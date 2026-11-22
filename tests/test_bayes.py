"""Pruebas de la regla de Bayes y del cuestionario de riesgo (sin base de datos)."""
import pytest

from conftest import cargar_catalogo_json  # noqa: F401  (también fija sys.path)
from backend.algorithms import bayes

BAJO = dict(edad="18-29", fuma="no", actividad="alta", peso="normal", cronicas="ninguna",
            hospitalizaciones="ninguna", familiar="no")
ALTO = dict(edad="60+", fuma="si", actividad="baja", peso="obesidad", cronicas="varias",
            hospitalizaciones="varias", familiar="si")
CODIGOS = ["hospitalizacion", "maternidad", "emergencia_extranjero", "telemedicina", "checkup"]


def test_modelo_es_distribucion_valida():
    bayes.validar_modelo()


def test_ejemplos_del_profesor():
    bacteria = bayes.PruebaDiagnostica("bacteria", 0.001, 0.99, 0.98)
    assert bacteria.posterior_si_positivo() == pytest.approx(0.0472, abs=1e-4)
    cancer = bayes.PruebaDiagnostica("cancer", 0.01, 0.90, 0.90)
    assert cancer.posterior_si_positivo() == pytest.approx(9 / 108)
    fabrica = bayes.ReglaDeBayes({"M1": 0.40, "M2": 0.60})
    post = fabrica.posteriores({"M1": 0.02, "M2": 0.03})
    assert post["M1"] == pytest.approx(0.008 / 0.026)
    assert sum(post.values()) == pytest.approx(1)


def test_posterior_suma_uno_y_actualiza_paso_a_paso():
    a = bayes.analizar(ALTO)
    assert sum(a.posterior.values()) == pytest.approx(1)
    assert len(a.pasos) == len(bayes.EVIDENCIA)
    assert a.pasos[0].antes == pytest.approx(a.prior)
    for anterior, siguiente in zip(a.pasos, a.pasos[1:]):
        assert siguiente.antes == pytest.approx(anterior.despues)  # posterior de hoy = prior de mañana
    assert a.pasos[-1].despues == pytest.approx(a.posterior)


def test_perfil_sano_vs_perfil_riesgoso():
    bajo, alto = bayes.analizar(BAJO), bayes.analizar(ALTO)
    assert bajo.nivel_probable == "bajo" and alto.nivel_probable == "alto"
    assert alto.indice_riesgo > bajo.indice_riesgo
    assert alto.prob_hospitalizacion > bajo.prob_hospitalizacion
    assert bayes.P_HOSPITALIZACION["bajo"] < bajo.prob_hospitalizacion + 1e-9


def test_mas_evidencia_de_riesgo_sube_el_indice():
    base = bayes.analizar(BAJO).indice_riesgo
    peor = bayes.analizar({**BAJO, "fuma": "si"}).indice_riesgo
    assert peor > base


def test_respuesta_invalida_falla():
    with pytest.raises(ValueError):
        bayes.analizar({**BAJO, "fuma": "mucho"})


def _criterios(resp):
    return bayes.derivar_criterios(
        bayes.analizar(resp), resp, [10000, 20000, 30000, 50000, 80000], [10, 15, 20, 25],
        [3_000_000, 5_000_000, 12_000_000, 20_000_000], CODIGOS,
    )


def test_mayor_riesgo_exige_mas_proteccion():
    bajo, alto = _criterios(BAJO), _criterios(ALTO)
    assert alto.deducible_maximo < bajo.deducible_maximo
    assert alto.pesos["costo"] < bajo.pesos["costo"]
    assert alto.pesos["coberturas"] > bajo.pesos["coberturas"]
    assert bajo.coaseguro_maximo is None and alto.coaseguro_maximo is not None
    assert bajo.coberturas_obligatorias == ("hospitalizacion",)


def test_necesidades_agregan_coberturas_deseadas():
    c = _criterios({**BAJO, "maternidad": "si", "viajes": "si"})
    assert {"maternidad", "emergencia_extranjero"} <= set(c.coberturas_deseadas)
