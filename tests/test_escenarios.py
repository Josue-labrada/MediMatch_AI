"""
Escenarios de demostración A–E (PROJECT_CONTEXT.md §9) sobre el catálogo simulado real.
Se ejecutan sin BD: leen los mismos JSON que sirve la API mock.
"""
from backend.algorithms import csp, ranking
from backend.algorithms.modelos import Pesos, Preferencias


def test_escenario_A_presupuesto_reducido_pocos_planes(catalogo_base):
    planes, nombres = catalogo_base
    prefs = Preferencias(presupuesto_mensual=1_300, deducible_maximo=80_000, coberturas_obligatorias=("hospitalizacion",))
    r = csp.resolver(planes, prefs, nombres=nombres)
    compatibles = {s.plan.external_id for s in r.soluciones}
    assert 0 < len(compatibles) <= 4
    assert len(r.descartes) >= len(planes) - 4


def test_escenario_B_cambian_pesos_cambia_ranking(catalogo_base):
    planes, nombres = catalogo_base
    base = dict(
        presupuesto_mensual=5_000,
        deducible_maximo=30_000,
        coberturas_obligatorias=("hospitalizacion",),
        coberturas_deseadas=("maternidad", "dental", "salud_mental"),
    )
    ahorro = Preferencias(**base, pesos=Pesos(costo=60, deducible=10, coaseguro=10, suma_asegurada=10, coberturas=10))
    proteccion = Preferencias(**base, pesos=Pesos(costo=10, deducible=10, coaseguro=10, suma_asegurada=20, coberturas=50))
    sol = csp.resolver(planes, ahorro, nombres=nombres).soluciones
    assert len(sol) > 10
    top_ahorro = ranking.rankear(sol, ahorro)[0].configuracion
    top_proteccion = ranking.rankear(sol, proteccion)[0].configuracion
    assert top_ahorro.clave != top_proteccion.clave
    assert top_ahorro.prima_total < top_proteccion.prima_total


def test_escenario_C_restricciones_incompatibles_cero_resultados(catalogo_base):
    planes, nombres = catalogo_base
    prefs = Preferencias(
        presupuesto_mensual=2_000,
        deducible_maximo=30_000,
        coberturas_obligatorias=("cobertura_internacional", "maternidad"),
    )
    r = csp.resolver(planes, prefs, nombres=nombres)
    assert r.soluciones == []
    assert len(r.descartes) == len(planes)
    assert all(d.motivos for d in r.descartes)


def test_escenario_D_producto_nuevo_cambia_resultado(catalogo_base, catalogo_con_novedades):
    prefs = Preferencias(presupuesto_mensual=2_700, deducible_maximo=30_000, coberturas_obligatorias=("maternidad",))
    antes = ranking.rankear(csp.resolver(catalogo_base[0], prefs).soluciones, prefs)
    despues = ranking.rankear(csp.resolver(catalogo_con_novedades[0], prefs).soluciones, prefs)
    assert antes[0].configuracion.plan.external_id != "FARO-MATERNA"
    assert despues[0].configuracion.plan.external_id == "FARO-MATERNA"
    assert len(despues) > len(antes)


def test_escenario_E_reglas_de_compatibilidad_y_podas(catalogo_base):
    planes, nombres = catalogo_base
    prefs = Preferencias(
        presupuesto_mensual=6_000,
        deducible_maximo=50_000,
        coberturas_obligatorias=("cobertura_internacional",),
        coberturas_deseadas=("dental",),
    )
    bt = csp.resolver(planes, prefs, forward_checking=False, nombres=nombres)
    fc = csp.resolver(planes, prefs, forward_checking=True, nombres=nombres)
    # Delta Viajero: internacional requiere ambulancia aérea y deducible <= 30,000.
    viajero = [s for s in fc.soluciones if s.plan.external_id == "DELTA-VIAJERO"]
    assert viajero and all("ambulancia_aerea" in s.opcionales and s.variante.deducible <= 30_000 for s in viajero)
    assert fc.estadisticas.podas.get("regla_deducible_max", 0) > 0
    assert {s.clave for s in bt.soluciones} == {s.clave for s in fc.soluciones}
    assert fc.estadisticas.nodos_explorados < bt.estadisticas.nodos_explorados
