"""Pruebas de la función objetivo: normalización, pesos, casos límite y desempates."""
import pytest

from backend.algorithms import ranking
from backend.algorithms.modelos import INCLUIDA, OPCIONAL, Configuracion, OfertaCobertura, Pesos, Plan, Preferencias, Variante


def config(external_id, prima, deducible=30_000, coaseguro=10, suma=10_000_000, incluidas=(), opcionales=()):
    ofertas = [OfertaCobertura(c, INCLUIDA, 0) for c in incluidas] + [
        OfertaCobertura(c, OPCIONAL, costo) for c, costo in opcionales
    ]
    plan = Plan(1, external_id, external_id, "Prueba (simulada)", "Intermedio", suma,
                (Variante(deducible, coaseguro, prima),), tuple(ofertas))
    return Configuracion(plan, plan.variantes[0], frozenset(c for c, _ in opcionales))


def prefs(pesos=None, deseadas=()):
    return Preferencias(presupuesto_mensual=10_000, deducible_maximo=100_000,
                        coberturas_deseadas=tuple(deseadas), pesos=pesos or Pesos())


def test_pesos_se_normalizan_y_sin_deseadas_se_redistribuye_coberturas():
    p = ranking.pesos_aplicados(prefs(Pesos(costo=50, deducible=50, coaseguro=0, suma_asegurada=0, coberturas=100)))
    assert "coberturas" not in p
    assert p == pytest.approx({"costo": 0.5, "deducible": 0.5, "coaseguro": 0.0, "suma_asegurada": 0.0})


def test_pesos_en_cero_usan_pesos_iguales():
    p = ranking.pesos_aplicados(prefs(Pesos(0, 0, 0, 0, 0), deseadas=("dental",)))
    assert sum(p.values()) == pytest.approx(1)
    assert len(set(p.values())) == 1


def test_puntaje_esta_entre_0_y_1_y_suma_contribuciones():
    soluciones = [config("A", 1_000), config("B", 2_000, deducible=10_000), config("C", 3_000, suma=50_000_000)]
    for r in ranking.rankear(soluciones, prefs()):
        assert 0 <= r.puntaje <= 1
        assert r.puntaje == pytest.approx(sum(c.contribucion for c in r.componentes), abs=1e-5)


def test_criterio_sin_variacion_vale_1():
    soluciones = [config("A", 1_000), config("B", 2_000)]  # mismo deducible, coaseguro y suma
    r = ranking.rankear(soluciones, prefs())
    for rec in r:
        comp = {c.criterio: c for c in rec.componentes}
        assert comp["deducible"].normalizado == 1.0
        assert comp["suma_asegurada"].normalizado == 1.0


def test_cambiar_pesos_cambia_el_ranking():
    barata = config("BARATA", 1_000, incluidas=("hosp",))
    completa = config("COMPLETA", 2_500, incluidas=("hosp", "dental", "mat"))
    soluciones = [barata, completa]
    deseadas = ("dental", "mat")
    ahorro = ranking.rankear(soluciones, prefs(Pesos(costo=90, deducible=0, coaseguro=0, suma_asegurada=0, coberturas=10), deseadas))
    proteccion = ranking.rankear(soluciones, prefs(Pesos(costo=10, deducible=0, coaseguro=0, suma_asegurada=0, coberturas=90), deseadas))
    assert ahorro[0].configuracion.plan.external_id == "BARATA"
    assert proteccion[0].configuracion.plan.external_id == "COMPLETA"


def test_desempate_determinista_por_prima_y_luego_id():
    a = config("ZETA", 1_000)
    b = config("ALFA", 1_000)
    c = config("MEDIO", 1_000)
    # Todas idénticas en criterios → mismo puntaje; el orden lo fija external_id.
    orden = [r.configuracion.plan.external_id for r in ranking.rankear([a, b, c], prefs())]
    assert orden == ["ALFA", "MEDIO", "ZETA"]
    assert orden == [r.configuracion.plan.external_id for r in ranking.rankear([c, a, b], prefs())]


def test_menor_prima_es_linea_base():
    soluciones = [config("A", 1_500), config("B", 900), config("C", 2_000)]
    assert ranking.menor_prima(soluciones).plan.external_id == "B"
    assert ranking.menor_prima([]) is None


def test_ranking_vacio():
    assert ranking.rankear([], prefs()) == []
