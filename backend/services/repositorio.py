"""
Lectura del catálogo en PostgreSQL y conversión a los modelos de dominio.

Este módulo es el "puente" entre la base de datos y los algoritmos: convierte filas
ORM en dataclasses puras (backend/algorithms/modelos.py).
"""
from typing import Dict, List, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..algorithms.csp import mxn
from ..algorithms.modelos import OfertaCobertura, Plan, Regla, Variante
from ..models import Cobertura, PlanCobertura, PlanDB, ReglaDB, VarianteDB
from ..schemas import CoberturaOut, OfertaOut, OpcionesOut, PlanOut, ReglaOut, VarianteOut


def _consulta_planes(solo_activos: bool):
    consulta = (
        select(PlanDB)
        .options(
            selectinload(PlanDB.aseguradora),
            selectinload(PlanDB.variantes),
            selectinload(PlanDB.coberturas).selectinload(PlanCobertura.cobertura),
            selectinload(PlanDB.reglas).selectinload(ReglaDB.cobertura),
            selectinload(PlanDB.reglas).selectinload(ReglaDB.objetivo),
        )
        .order_by(PlanDB.external_id)
    )
    if solo_activos:
        consulta = consulta.where(PlanDB.activo.is_(True))
    return consulta


def nombres_coberturas(db: Session) -> Dict[str, str]:
    return {c.codigo: c.nombre for c in db.scalars(select(Cobertura))}


def cargar_planes_dominio(db: Session) -> Tuple[List[Plan], Dict[str, str]]:
    """Planes activos como dataclasses para el CSP, más el diccionario código → nombre."""
    planes = []
    for p in db.scalars(_consulta_planes(solo_activos=True)):
        planes.append(
            Plan(
                id=p.id,
                external_id=p.external_id,
                nombre=p.nombre,
                aseguradora=p.aseguradora.nombre,
                nivel=p.nivel,
                suma_asegurada=float(p.suma_asegurada),
                variantes=tuple(
                    Variante(float(v.deducible), float(v.coaseguro_porcentaje), float(v.prima_mensual))
                    for v in p.variantes
                ),
                coberturas=tuple(
                    OfertaCobertura(pc.cobertura.codigo, pc.tipo, float(pc.costo_extra)) for pc in p.coberturas
                ),
                reglas=tuple(
                    Regla(
                        r.tipo,
                        r.cobertura.codigo,
                        r.objetivo.codigo if r.objetivo else None,
                        float(r.valor) if r.valor is not None else None,
                    )
                    for r in p.reglas
                ),
            )
        )
    return planes, nombres_coberturas(db)


def describir_regla(r: ReglaDB) -> str:
    a = r.cobertura.nombre
    if r.tipo == "requiere":
        return f"«{a}» requiere contratar también «{r.objetivo.nombre}»."
    if r.tipo == "excluye":
        return f"«{a}» no puede contratarse junto con «{r.objetivo.nombre}»."
    return f"«{a}» solo está disponible con deducible de hasta {mxn(float(r.valor))}."


def listar_planes(db: Session, solo_activos: bool = False) -> List[PlanOut]:
    salida = []
    for p in db.scalars(_consulta_planes(solo_activos)):
        salida.append(
            PlanOut(
                id=p.id,
                external_id=p.external_id,
                nombre=p.nombre,
                aseguradora=p.aseguradora.nombre,
                nivel=p.nivel,
                suma_asegurada=float(p.suma_asegurada),
                moneda=p.moneda,
                activo=p.activo,
                variantes=[
                    VarianteOut(
                        deducible=float(v.deducible),
                        coaseguro_porcentaje=float(v.coaseguro_porcentaje),
                        prima_mensual=float(v.prima_mensual),
                    )
                    for v in p.variantes
                ],
                coberturas=[
                    OfertaOut(
                        codigo=pc.cobertura.codigo,
                        nombre=pc.cobertura.nombre,
                        tipo=pc.tipo,
                        costo_extra=float(pc.costo_extra),
                    )
                    for pc in sorted(p.coberturas, key=lambda x: (x.tipo != "incluida", x.cobertura.nombre))
                ],
                reglas=[
                    ReglaOut(
                        tipo=r.tipo,
                        cobertura=r.cobertura.codigo,
                        cobertura_objetivo=r.objetivo.codigo if r.objetivo else None,
                        valor=float(r.valor) if r.valor is not None else None,
                        descripcion=describir_regla(r),
                    )
                    for r in p.reglas
                ],
            )
        )
    return salida


def listar_coberturas(db: Session) -> List[CoberturaOut]:
    return [
        CoberturaOut(codigo=c.codigo, nombre=c.nombre, descripcion=c.descripcion)
        for c in db.scalars(select(Cobertura).order_by(Cobertura.id))
    ]


def opciones_formulario(db: Session) -> OpcionesOut:
    """Valores distintos presentes en planes activos: el formulario no inventa opciones."""
    activos = select(PlanDB.id).where(PlanDB.activo.is_(True))
    variantes = VarianteDB.plan_id.in_(activos)
    deducibles = db.scalars(select(VarianteDB.deducible).where(variantes).distinct().order_by(VarianteDB.deducible))
    coaseguros = db.scalars(
        select(VarianteDB.coaseguro_porcentaje).where(variantes).distinct().order_by(VarianteDB.coaseguro_porcentaje)
    )
    sumas = db.scalars(
        select(PlanDB.suma_asegurada).where(PlanDB.activo.is_(True)).distinct().order_by(PlanDB.suma_asegurada)
    )
    prima_min, prima_max = db.execute(
        select(func.min(VarianteDB.prima_mensual), func.max(VarianteDB.prima_mensual)).where(variantes)
    ).one()
    planes_activos = db.scalar(select(func.count()).select_from(PlanDB).where(PlanDB.activo.is_(True))) or 0
    return OpcionesOut(
        coberturas=listar_coberturas(db),
        deducibles=[float(d) for d in deducibles],
        coaseguros=[float(c) for c in coaseguros],
        sumas_aseguradas=[float(s) for s in sumas],
        prima_minima=float(prima_min) if prima_min is not None else None,
        prima_maxima=float(prima_max) if prima_max is not None else None,
        planes_activos=planes_activos,
    )
