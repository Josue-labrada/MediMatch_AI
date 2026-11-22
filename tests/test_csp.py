"""
Pruebas unitarias del CSP con un catálogo mínimo escrito a mano, para que cada
resultado esperado se pueda verificar con lápiz y papel.
"""
import pytest

from backend.algorithms import csp
from backend.algorithms.modelos import INCLUIDA, OPCIONAL, OfertaCobertura, Plan, Preferencias, Regla, Variante


def plan(external_id, variantes, coberturas, reglas=(), suma=10_000_000):
    return Plan(
        id=hash(external_id) % 1000,
        external_id=external_id,
        nombre=external_id,
        aseguradora="Prueba (simulada)",
        nivel="Intermedio",
        suma_asegurada=suma,
        variantes=tuple(Variante(d, c, p) for d, c, p in variantes),
        coberturas=tuple(OfertaCobertura(cod, t, costo) for cod, t, costo in coberturas),
        reglas=tuple(reglas),
    )


HOSP = ("hosp", INCLUIDA, 0)

BARATO = plan("BARATO", [(50_000, 20, 900), (80_000, 20, 700)], [HOSP, ("dental", OPCIONAL, 150)])
MEDIO = plan(
    "MEDIO",
    [(20_000, 10, 2_000), (30_000, 10, 1_700)],
    [HOSP, ("mat", OPCIONAL, 500), ("checkup", OPCIONAL, 100), ("dental", OPCIONAL, 120), ("vision", OPCIONAL, 80)],
    reglas=[
        Regla("requiere", "mat", "checkup"),
        Regla("deducible_max", "mat", valor=20_000),
        Regla("excluye", "dental", "vision"),
    ],
)
CARO = plan("CARO", [(10_000, 10, 5_000)], [HOSP, ("mat", INCLUIDA, 0), ("intl", OPCIONAL, 900)], suma=50_000_000)
CATALOGO = [BARATO, MEDIO, CARO]


def claves(resultado):
    return {s.clave for s in resultado.soluciones}


@pytest.mark.parametrize("fc", [True, False])
def test_presupuesto_y_deducible_son_restricciones_duras(fc):
    prefs = Preferencias(presupuesto_mensual=1_000, deducible_maximo=80_000)
    r = csp.resolver(CATALOGO, prefs, forward_checking=fc)
    assert claves(r) == {"BARATO|50000|sin-extras", "BARATO|80000|sin-extras"}
    assert all(s.prima_total <= 1_000 for s in r.soluciones)


@pytest.mark.parametrize("fc", [True, False])
def test_cobertura_obligatoria_no_ofrecida_descarta_el_plan(fc):
    prefs = Preferencias(presupuesto_mensual=10_000, deducible_maximo=80_000, coberturas_obligatorias=("mat",))
    r = csp.resolver(CATALOGO, prefs, forward_checking=fc)
    assert "BARATO" in {d.plan.external_id for d in r.descartes}
    motivo = next(d for d in r.descartes if d.plan.external_id == "BARATO").motivos[0]
    assert motivo.restriccion == "cobertura_obligatoria"


@pytest.mark.parametrize("fc", [True, False])
def test_regla_requiere_arrastra_cobertura_y_su_costo(fc):
    """mat requiere checkup: la solución de MEDIO debe incluir ambos y pagar ambos extras."""
    prefs = Preferencias(presupuesto_mensual=10_000, deducible_maximo=80_000, coberturas_obligatorias=("mat",))
    r = csp.resolver([MEDIO], prefs, forward_checking=fc)
    assert claves(r) == {"MEDIO|20000|checkup+mat"}  # 30k violaría deducible_max de mat
    assert r.soluciones[0].prima_total == 2_000 + 500 + 100


@pytest.mark.parametrize("fc", [True, False])
def test_regla_excluye_impide_combinar(fc):
    prefs = Preferencias(presupuesto_mensual=10_000, deducible_maximo=80_000, coberturas_deseadas=("dental", "vision"))
    r = csp.resolver([MEDIO], prefs, forward_checking=fc)
    assert all(not {"dental", "vision"} <= s.opcionales for s in r.soluciones)
    assert r.estadisticas.podas.get("regla_excluye", 0) > 0


@pytest.mark.parametrize("fc", [True, False])
def test_regla_requiere_sin_presupuesto_suficiente(fc):
    """Con 2,500 MXN: 2,000 + mat 500 = 2,500, pero checkup (100) es obligatorio por regla → no cabe."""
    prefs = Preferencias(presupuesto_mensual=2_500, deducible_maximo=80_000, coberturas_obligatorias=("mat",))
    r = csp.resolver([MEDIO], prefs, forward_checking=fc)
    assert r.soluciones == []
    assert r.descartes[0].plan.external_id == "MEDIO"


def test_no_genera_soluciones_dominadas_con_coberturas_arrastradas():
    """checkup solo entra porque mat lo requiere; sin mat, no debe aparecer pagado."""
    prefs = Preferencias(presupuesto_mensual=10_000, deducible_maximo=80_000, coberturas_deseadas=("mat",))
    r = csp.resolver([MEDIO], prefs)
    for s in r.soluciones:
        assert ("checkup" in s.opcionales) == ("mat" in s.opcionales)


def test_suma_asegurada_minima():
    prefs = Preferencias(presupuesto_mensual=10_000, deducible_maximo=80_000, suma_asegurada_minima=20_000_000)
    r = csp.resolver(CATALOGO, prefs)
    assert {s.plan.external_id for s in r.soluciones} == {"CARO"}


def test_sin_soluciones_explica_todos_los_planes():
    prefs = Preferencias(presupuesto_mensual=500, deducible_maximo=10_000)
    r = csp.resolver(CATALOGO, prefs)
    assert r.soluciones == []
    assert {d.plan.external_id for d in r.descartes} == {"BARATO", "MEDIO", "CARO"}
    assert all(d.motivos for d in r.descartes)


def test_forward_checking_mismas_soluciones_menos_nodos():
    prefs = Preferencias(
        presupuesto_mensual=3_000,
        deducible_maximo=30_000,
        coberturas_obligatorias=("mat",),
        coberturas_deseadas=("dental", "vision"),
    )
    bt = csp.resolver(CATALOGO, prefs, forward_checking=False)
    fc = csp.resolver(CATALOGO, prefs, forward_checking=True)
    assert claves(bt) == claves(fc)
    assert fc.estadisticas.nodos_explorados < bt.estadisticas.nodos_explorados
    assert bt.estadisticas.algoritmo == csp.ALGORITMO_BT
    assert fc.estadisticas.algoritmo == csp.ALGORITMO_FC


def test_todas_las_soluciones_cumplen_todas_las_restricciones(catalogo_base):
    """Verificación independiente: cada solución se revisa contra las restricciones originales."""
    planes, _ = catalogo_base
    prefs = Preferencias(
        presupuesto_mensual=4_500,
        deducible_maximo=50_000,
        coaseguro_maximo=15,
        coberturas_obligatorias=("hospitalizacion",),
        coberturas_deseadas=("maternidad", "dental", "vision", "cobertura_internacional"),
    )
    r = csp.resolver(planes, prefs)
    assert r.soluciones
    for s in r.soluciones:
        tiene = s.coberturas_totales
        assert s.prima_total <= prefs.presupuesto_mensual
        assert s.variante.deducible <= prefs.deducible_maximo
        assert s.variante.coaseguro_porcentaje <= prefs.coaseguro_maximo
        assert "hospitalizacion" in tiene
        for regla in s.plan.reglas:
            if regla.tipo == "requiere" and regla.cobertura in tiene:
                assert regla.objetivo in tiene
            if regla.tipo == "excluye":
                assert not (regla.cobertura in tiene and regla.objetivo in tiene)
            if regla.tipo == "deducible_max" and regla.cobertura in tiene:
                assert s.variante.deducible <= regla.valor


def test_completitud_contra_fuerza_bruta(catalogo_base):
    """El CSP encuentra exactamente las mismas soluciones que enumerar todo el espacio."""
    from itertools import product

    planes, _ = catalogo_base
    prefs = Preferencias(
        presupuesto_mensual=4_000,
        deducible_maximo=50_000,
        coberturas_obligatorias=("maternidad",),
        coberturas_deseadas=("dental", "vision"),
    )
    esperadas = set()
    for p in planes:
        sub = csp._SubproblemaPlan(p, prefs, csp.EstadisticasCSP(), True, {})
        for v in p.variantes:
            for valores in product(*[sub._dominio_cobertura(c) for c in sub.coberturas]):
                a = dict(zip(sub.coberturas, valores))
                a[csp.VAR_DEDUCIBLE] = v
                if all(sub._consistente(var, a) is None for var in sub.orden):
                    esperadas.add(sub._configuracion(a).clave)
    assert claves(csp.resolver(planes, prefs)) == esperadas
