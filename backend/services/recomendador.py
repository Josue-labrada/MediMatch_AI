"""
Orquestación de una recomendación (el flujo completo que se expone en la presentación):

    PreferenciasIn (JSON del formulario)
        │  validación Pydantic (rechaza campos no previstos → privacidad)
        ▼
    repositorio.cargar_planes_dominio   PostgreSQL → dataclasses Plan
        ▼
    csp.resolver                        todas las configuraciones válidas + descartes + estadísticas
        ▼
    ranking.rankear / menor_prima       función objetivo multicriterio + línea base
        ▼
    RecomendacionOut                    ranking explicado, guardado en la tabla consultas
"""
from typing import Dict, List, Mapping, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..algorithms import csp, ranking
from ..algorithms.modelos import (
    INCLUIDA,
    Configuracion,
    EstadisticasCSP,
    Pesos,
    Preferencias,
    Recomendacion,
)
from ..models import Consulta
from ..schemas import (
    ComparacionBaselineOut,
    CoberturaIncluidaOut,
    ComponenteOut,
    DescarteOut,
    EstadisticasOut,
    MotivoOut,
    OpcionOut,
    PreferenciasIn,
    RecomendacionOut,
)
from .repositorio import cargar_planes_dominio

MAX_RANKING = 15
AVISO = (
    "Resultados calculados sobre un catálogo SIMULADO con fines académicos. "
    "No es una cotización ni una oferta de venta."
)
ETIQUETAS_CRITERIO = {
    "costo": "Costo mensual",
    "deducible": "Deducible",
    "coaseguro": "Coaseguro",
    "suma_asegurada": "Suma asegurada",
    "coberturas": "Coberturas deseadas",
}
NOMBRE_ALGORITMO = {
    csp.ALGORITMO_FC: "CSP con backtracking + forward checking; ranking por función objetivo ponderada",
    csp.ALGORITMO_BT: "CSP con backtracking simple; ranking por función objetivo ponderada",
}


def a_preferencias(entrada: PreferenciasIn) -> Preferencias:
    return Preferencias(
        presupuesto_mensual=entrada.presupuesto_mensual,
        deducible_maximo=entrada.deducible_maximo,
        coaseguro_maximo=entrada.coaseguro_maximo,
        suma_asegurada_minima=entrada.suma_asegurada_minima,
        coberturas_obligatorias=tuple(entrada.coberturas_obligatorias),
        coberturas_deseadas=tuple(entrada.coberturas_deseadas),
        pesos=Pesos(**entrada.pesos.model_dump()),
    )


def _texto_valor(criterio: str, valor: float) -> str:
    if criterio in ("costo", "deducible", "suma_asegurada"):
        return csp.mxn(valor)
    if criterio == "coaseguro":
        return f"{valor:g}%"
    return f"{valor * 100:.0f}% de las deseadas"


def _estadisticas(stats: EstadisticasCSP, soluciones: int) -> EstadisticasOut:
    return EstadisticasOut(
        algoritmo=stats.algoritmo,
        espacio_busqueda=stats.espacio_busqueda,
        nodos_explorados=stats.nodos_explorados,
        backtracks=stats.backtracks,
        podas=dict(sorted(stats.podas.items(), key=lambda kv: -kv[1])),
        total_podas=stats.total_podas,
        soluciones=soluciones,
        tiempo_ms=stats.tiempo_ms,
    )


def _opcion(
    config: Configuracion,
    posicion: int,
    recomendacion: Optional[Recomendacion],
    prefs: Preferencias,
    nombres: Mapping[str, str],
    clave_menor: Optional[str],
) -> OpcionOut:
    plan = config.plan
    coberturas = [
        CoberturaIncluidaOut(
            codigo=o.codigo,
            nombre=nombres.get(o.codigo, o.codigo),
            origen="incluida" if o.tipo == INCLUIDA else "opcional",
            costo_extra=o.costo_extra,
        )
        for o in plan.coberturas
        if o.tipo == INCLUIDA or o.codigo in config.opcionales
    ]
    tiene = config.coberturas_totales
    componentes = []
    if recomendacion:
        componentes = [
            ComponenteOut(
                criterio=c.criterio,
                etiqueta=ETIQUETAS_CRITERIO[c.criterio],
                valor=c.valor,
                valor_texto=_texto_valor(c.criterio, c.valor),
                normalizado=c.normalizado,
                peso=c.peso,
                contribucion=c.contribucion,
            )
            for c in recomendacion.componentes
        ]
    return OpcionOut(
        id=config.clave,
        posicion=posicion,
        puntaje=round((recomendacion.puntaje if recomendacion else 0) * 100, 2),
        plan_external_id=plan.external_id,
        plan=plan.nombre,
        aseguradora=plan.aseguradora,
        nivel=plan.nivel,
        suma_asegurada=plan.suma_asegurada,
        deducible=config.variante.deducible,
        coaseguro_porcentaje=config.variante.coaseguro_porcentaje,
        prima_base=config.variante.prima_mensual,
        costo_opcionales=config.costo_opcionales,
        prima_total=config.prima_total,
        coberturas=coberturas,
        coberturas_deseadas_cubiertas=[nombres.get(c, c) for c in prefs.coberturas_deseadas if c in tiene],
        coberturas_deseadas_faltantes=[nombres.get(c, c) for c in prefs.coberturas_deseadas if c not in tiene],
        componentes=componentes,
        restricciones_cumplidas=csp.explicar_cumplimiento(config, prefs, nombres),
        es_menor_prima=config.clave == clave_menor,
    )


def recomendar(db: Session, entrada: PreferenciasIn) -> RecomendacionOut:
    planes, nombres = cargar_planes_dominio(db)
    if not planes:
        raise HTTPException(503, "El catálogo está vacío. Sincroniza la API mock desde el panel administrativo.")

    desconocidas = set(entrada.coberturas_obligatorias + entrada.coberturas_deseadas) - set(nombres)
    if desconocidas:
        raise HTTPException(422, f"Coberturas desconocidas: {sorted(desconocidas)}")

    prefs = a_preferencias(entrada)
    usar_fc = entrada.algoritmo == csp.ALGORITMO_FC

    # Algoritmo elegido (produce el resultado) y el alternativo (solo para comparar eficiencia).
    resultado = csp.resolver(planes, prefs, forward_checking=usar_fc, nombres=nombres)
    alterno = csp.resolver(planes, prefs, forward_checking=not usar_fc, nombres=nombres)
    assert {s.clave for s in resultado.soluciones} == {s.clave for s in alterno.soluciones}

    ordenadas = ranking.rankear(resultado.soluciones, prefs)
    base = ranking.menor_prima(resultado.soluciones)
    clave_menor = base.clave if base else None
    por_clave: Dict[str, Recomendacion] = {r.configuracion.clave: r for r in ordenadas}

    top = [_opcion(r.configuracion, r.posicion, r, prefs, nombres, clave_menor) for r in ordenadas[:MAX_RANKING]]
    menor_out = None
    comparacion = None
    if base is not None:
        rec_base = por_clave[base.clave]
        menor_out = _opcion(base, rec_base.posicion, rec_base, prefs, nombres, clave_menor)
        mejor = ordenadas[0]
        comparacion = ComparacionBaselineOut(
            misma_opcion=mejor.configuracion.clave == base.clave,
            posicion_menor_prima=rec_base.posicion,
            diferencia_prima=round(mejor.configuracion.prima_total - base.prima_total, 2),
            diferencia_puntaje=round((mejor.puntaje - rec_base.puntaje) * 100, 2),
        )

    descartes: List[DescarteOut] = [
        DescarteOut(
            plan_external_id=d.plan.external_id,
            plan=d.plan.nombre,
            aseguradora=d.plan.aseguradora,
            motivos=[
                MotivoOut(restriccion=m.restriccion, etiqueta=csp.RESTRICCIONES[m.restriccion], detalle=m.detalle)
                for m in d.motivos
            ],
        )
        for d in resultado.descartes
    ]

    stats = _estadisticas(resultado.estadisticas, len(resultado.soluciones))
    stats_alt = _estadisticas(alterno.estadisticas, len(alterno.soluciones))
    comparacion_algoritmos = sorted([stats, stats_alt], key=lambda s: s.algoritmo)

    # Persistencia: solo preferencias y un resumen (sin datos personales).
    consulta = Consulta(
        preferencias_json=entrada.model_dump(),
        resultado_json={
            "algoritmo": stats.algoritmo,
            "candidatos_validos": len(resultado.soluciones),
            "nodos_explorados": stats.nodos_explorados,
            "top": [{"id": o.id, "puntaje": o.puntaje, "prima_total": o.prima_total} for o in top[:5]],
            "menor_prima": clave_menor,
        },
    )
    db.add(consulta)
    db.commit()

    return RecomendacionOut(
        consulta_id=consulta.id,
        aviso=AVISO,
        algoritmo_utilizado=NOMBRE_ALGORITMO[stats.algoritmo],
        planes_evaluados=len(planes),
        candidatos_validos=len(resultado.soluciones),
        pesos_aplicados={k: round(v, 4) for k, v in ranking.pesos_aplicados(prefs).items()},
        estadisticas=stats,
        comparacion_algoritmos=comparacion_algoritmos,
        ranking=top,
        menor_prima=menor_out,
        comparacion_baseline=comparacion,
        descartes=descartes,
    )
