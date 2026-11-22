"""
Sincronización Mock Insurance API → PostgreSQL.

1. Pide el catálogo por HTTP (httpx) y lo valida con Pydantic (CatalogoMock).
2. Hace "upsert" por claves naturales para no duplicar:
     aseguradoras.external_id · coberturas.codigo · planes(aseguradora_id, external_id)
3. Los hijos de cada plan (variantes, coberturas ofrecidas, reglas) se reemplazan
   completos solo si el plan cambió.
4. Los planes que ya no vienen en la API se marcan activo = FALSE (no se borran).
5. Registra el resultado en la tabla sincronizaciones.

Una segunda sincronización sin cambios en la API produce 0 creados / 0 actualizados.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Tuple

import httpx
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..config import MOCK_API_URL
from ..models import Aseguradora, Cobertura, PlanCobertura, PlanDB, ReglaDB, Sincronizacion, VarianteDB
from ..schemas import CatalogoMock, PlanMock


class ErrorSincronizacion(Exception):
    pass


def obtener_catalogo(incluir_novedades: bool) -> Tuple[CatalogoMock, str]:
    url = f"{MOCK_API_URL}/api/v1/planes"
    params = {"incluir_novedades": str(incluir_novedades).lower()}
    try:
        respuesta = httpx.get(url, params=params, timeout=10)
        respuesta.raise_for_status()
        catalogo = CatalogoMock.model_validate(respuesta.json())
    except httpx.HTTPError as exc:
        raise ErrorSincronizacion(f"No se pudo contactar la API mock ({url}): {exc}") from exc
    except ValidationError as exc:
        raise ErrorSincronizacion(f"La API mock devolvió datos inválidos: {exc.error_count()} errores") from exc
    if not catalogo.simulado:
        raise ErrorSincronizacion("Solo se aceptan catálogos marcados como simulados.")
    return catalogo, f"{url}?incluir_novedades={params['incluir_novedades']}"


def _n(valor) -> float:
    return float(valor) if isinstance(valor, Decimal) else float(valor)


def _firma_db(plan: PlanDB, codigos: Dict[int, str]) -> tuple:
    """Representación comparable de un plan guardado (para detectar cambios)."""
    return (
        plan.nombre,
        plan.nivel,
        _n(plan.suma_asegurada),
        plan.moneda,
        tuple(sorted((_n(v.deducible), _n(v.coaseguro_porcentaje), _n(v.prima_mensual)) for v in plan.variantes)),
        tuple(sorted((codigos[c.cobertura_id], c.tipo, _n(c.costo_extra)) for c in plan.coberturas)),
        tuple(
            sorted(
                (
                    r.tipo,
                    codigos[r.cobertura_id],
                    codigos.get(r.cobertura_objetivo_id) if r.cobertura_objetivo_id else None,
                    _n(r.valor) if r.valor is not None else None,
                )
                for r in plan.reglas
            )
        ),
    )


def _firma_mock(p: PlanMock) -> tuple:
    return (
        p.nombre,
        p.nivel,
        float(p.suma_asegurada),
        p.moneda,
        tuple(sorted((v.deducible, v.coaseguro_porcentaje, v.prima_mensual) for v in p.variantes)),
        tuple(sorted((c.codigo, c.tipo, c.costo_extra) for c in p.coberturas)),
        tuple(sorted((r.tipo, r.cobertura, r.cobertura_objetivo, r.valor) for r in p.reglas)),
    )


def _cargar_hijos(plan: PlanDB, datos: PlanMock, cobertura_id: Dict[str, int]) -> None:
    plan.variantes = [
        VarianteDB(deducible=v.deducible, coaseguro_porcentaje=v.coaseguro_porcentaje, prima_mensual=v.prima_mensual)
        for v in datos.variantes
    ]
    plan.coberturas = [
        PlanCobertura(cobertura_id=cobertura_id[c.codigo], tipo=c.tipo, costo_extra=c.costo_extra)
        for c in datos.coberturas
    ]
    plan.reglas = [
        ReglaDB(
            tipo=r.tipo,
            cobertura_id=cobertura_id[r.cobertura],
            cobertura_objetivo_id=cobertura_id[r.cobertura_objetivo] if r.cobertura_objetivo else None,
            valor=r.valor,
        )
        for r in datos.reglas
    ]


def sincronizar(db: Session, incluir_novedades: bool = False) -> Sincronizacion:
    try:
        catalogo, origen = obtener_catalogo(incluir_novedades)
    except ErrorSincronizacion as exc:
        registro = Sincronizacion(origen=MOCK_API_URL, resultado="error", mensaje=str(exc))
        db.add(registro)
        db.commit()
        raise

    creados = actualizados = sin_cambios = desactivados = 0
    try:
        # Aseguradoras y coberturas: upsert por clave natural.
        aseguradoras = {a.external_id: a for a in db.scalars(select(Aseguradora))}
        for a in catalogo.aseguradoras:
            if a.external_id in aseguradoras:
                aseguradoras[a.external_id].nombre = a.nombre
            else:
                nueva = Aseguradora(external_id=a.external_id, nombre=a.nombre, es_simulada=True)
                db.add(nueva)
                aseguradoras[a.external_id] = nueva

        coberturas = {c.codigo: c for c in db.scalars(select(Cobertura))}
        for c in catalogo.coberturas:
            if c.codigo in coberturas:
                coberturas[c.codigo].nombre = c.nombre
                coberturas[c.codigo].descripcion = c.descripcion
            else:
                nueva = Cobertura(codigo=c.codigo, nombre=c.nombre, descripcion=c.descripcion)
                db.add(nueva)
                coberturas[c.codigo] = nueva
        db.flush()  # asigna ids

        cobertura_id = {codigo: c.id for codigo, c in coberturas.items()}
        codigo_por_id = {c.id: codigo for codigo, c in coberturas.items()}

        existentes = {
            (p.aseguradora_id, p.external_id): p
            for p in db.scalars(
                select(PlanDB).options(
                    selectinload(PlanDB.variantes), selectinload(PlanDB.coberturas), selectinload(PlanDB.reglas)
                )
            )
        }
        vistos = set()
        ahora = datetime.now(timezone.utc)

        for datos in catalogo.planes:
            aseg = aseguradoras.get(datos.aseguradora_external_id)
            if aseg is None:
                raise ErrorSincronizacion(f"Plan {datos.external_id}: aseguradora desconocida.")
            faltantes = {c.codigo for c in datos.coberturas} - set(cobertura_id)
            if faltantes:
                raise ErrorSincronizacion(f"Plan {datos.external_id}: coberturas desconocidas {faltantes}.")

            clave = (aseg.id, datos.external_id)
            vistos.add(clave)
            plan = existentes.get(clave)

            if plan is None:
                plan = PlanDB(aseguradora_id=aseg.id, external_id=datos.external_id)
                db.add(plan)
                creados += 1
            elif plan.activo and _firma_db(plan, codigo_por_id) == _firma_mock(datos):
                sin_cambios += 1
                continue
            else:
                actualizados += 1

            plan.nombre = datos.nombre
            plan.nivel = datos.nivel
            plan.suma_asegurada = datos.suma_asegurada
            plan.moneda = datos.moneda
            plan.activo = True
            plan.updated_at = ahora
            _cargar_hijos(plan, datos, cobertura_id)

        for clave, plan in existentes.items():
            if clave not in vistos and plan.activo:
                plan.activo = False
                plan.updated_at = ahora
                desactivados += 1

        registro = Sincronizacion(
            origen=origen,
            creados=creados,
            actualizados=actualizados,
            desactivados=desactivados,
            sin_cambios=sin_cambios,
            resultado="ok",
            mensaje=f"{len(catalogo.planes)} planes recibidos de la API mock (datos simulados).",
        )
        db.add(registro)
        db.commit()
        return registro
    except Exception as exc:
        db.rollback()
        db.add(Sincronizacion(origen=origen, resultado="error", mensaje=str(exc)[:500]))
        db.commit()
        raise ErrorSincronizacion(str(exc)) from exc
