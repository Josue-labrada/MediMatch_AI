"""
Búsqueda / optimización multicriterio sobre las soluciones del CSP.

El CSP devuelve el conjunto factible F (todas las configuraciones válidas). Aquí se
busca en F la configuración que maximiza una FUNCIÓN OBJETIVO explícita:

    puntaje(x) = Σ_i  w_i · n_i(x)          con  Σ_i w_i = 1,   0 ≤ n_i(x) ≤ 1

Criterios n_i (normalización min-max dentro de F, 1 = lo mejor de F):
    costo           prima total mensual     menor es mejor   n = (max − x) / (max − min)
    deducible       deducible               menor es mejor   n = (max − x) / (max − min)
    coaseguro       % de coaseguro          menor es mejor   n = (max − x) / (max − min)
    suma_asegurada  suma asegurada          mayor es mejor   n = (x − min) / (max − min)
    coberturas      fracción de coberturas deseadas que incluye la configuración (ya en 0..1)

Casos especiales (decisiones documentadas):
    • max == min: el criterio no distingue entre opciones → n = 1 para todas.
    • El usuario no marcó coberturas deseadas: el criterio "coberturas" no aplica y su
      peso se reparte proporcionalmente entre los demás.
    • Todos los pesos en 0: se usan pesos iguales.

Desempate determinista: puntaje ↓, prima total ↑, deducible ↑, external_id ↑, clave ↑.

Como F es pequeño (decenas o cientos de elementos) se evalúa exhaustivamente: el
óptimo encontrado es el óptimo global. Esto NO es machine learning: los pesos los
define el usuario y la fórmula la diseñó el equipo.
"""
from typing import Dict, List, Optional, Sequence

from .modelos import CRITERIOS, Componente, Configuracion, Preferencias, Recomendacion

MENOR_ES_MEJOR = {"costo", "deducible", "coaseguro"}
MAYOR_ES_MEJOR = {"suma_asegurada"}


def pesos_aplicados(prefs: Preferencias) -> Dict[str, float]:
    """Pesos finales: sin criterios que no aplican y normalizados para sumar 1."""
    pesos = {c: max(0.0, w) for c, w in prefs.pesos.como_dict().items()}
    if not prefs.coberturas_deseadas:
        pesos.pop("coberturas")
    total = sum(pesos.values())
    if total == 0:
        return {c: 1 / len(pesos) for c in pesos}
    return {c: w / total for c, w in pesos.items()}


def valores_crudos(config: Configuracion, prefs: Preferencias) -> Dict[str, float]:
    """Valor original de cada criterio para una configuración."""
    deseadas = set(prefs.coberturas_deseadas)
    cubiertas = len(deseadas & config.coberturas_totales) / len(deseadas) if deseadas else 0.0
    return {
        "costo": config.prima_total,
        "deducible": config.variante.deducible,
        "coaseguro": config.variante.coaseguro_porcentaje,
        "suma_asegurada": config.plan.suma_asegurada,
        "coberturas": cubiertas,
    }


def _normalizar(criterio: str, x: float, minimo: float, maximo: float) -> float:
    if criterio == "coberturas":
        return x
    if maximo == minimo:
        return 1.0
    if criterio in MENOR_ES_MEJOR:
        return (maximo - x) / (maximo - minimo)
    return (x - minimo) / (maximo - minimo)


def rankear(soluciones: Sequence[Configuracion], prefs: Preferencias) -> List[Recomendacion]:
    """Ordena todas las soluciones del CSP de mayor a menor puntaje."""
    if not soluciones:
        return []

    pesos = pesos_aplicados(prefs)
    crudos = [valores_crudos(s, prefs) for s in soluciones]
    rangos = {c: (min(v[c] for v in crudos), max(v[c] for v in crudos)) for c in pesos}

    evaluadas = []
    for config, valores in zip(soluciones, crudos):
        componentes = []
        for criterio in CRITERIOS:
            if criterio not in pesos:
                continue
            n = _normalizar(criterio, valores[criterio], *rangos[criterio])
            componentes.append(
                Componente(
                    criterio=criterio,
                    valor=valores[criterio],
                    normalizado=round(n, 6),
                    peso=round(pesos[criterio], 6),
                    contribucion=round(pesos[criterio] * n, 6),
                )
            )
        puntaje = sum(c.peso * c.normalizado for c in componentes)
        evaluadas.append((config, round(puntaje, 6), tuple(componentes)))

    evaluadas.sort(
        key=lambda e: (
            -e[1],
            e[0].prima_total,
            e[0].variante.deducible,
            e[0].plan.external_id,
            e[0].clave,
        )
    )
    return [
        Recomendacion(posicion=i + 1, configuracion=c, puntaje=p, componentes=comp)
        for i, (c, p, comp) in enumerate(evaluadas)
    ]


def menor_prima(soluciones: Sequence[Configuracion]) -> Optional[Configuracion]:
    """Línea base de comparación: la solución válida más barata (criterio único)."""
    if not soluciones:
        return None
    return min(soluciones, key=lambda s: (s.prima_total, s.variante.deducible, s.plan.external_id, s.clave))
