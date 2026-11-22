"""
Cuestionario de riesgo → Bayes → preferencias → CSP + ranking.

    CuestionarioIn ──► bayes.analizar            nivel de riesgo (posterior)
                  ──► bayes.derivar_criterios    restricciones y pesos
                  ──► recomendador.recomendar    CSP + función objetivo (ya existentes)

Privacidad: las respuestas de salud viven solo dentro de esta función. No se guardan; lo único
que llega a la tabla `consultas` son las preferencias derivadas (como en cualquier búsqueda).
"""
from typing import List

from sqlalchemy.orm import Session

from ..algorithms import bayes
from ..schemas import (
    AnalisisRiesgoOut,
    CuestionarioIn,
    CuestionarioOut,
    OpcionPreguntaOut,
    PasoBayesOut,
    PesosIn,
    PreferenciasIn,
    PreguntaOut,
)
from . import repositorio
from .recomendador import recomendar

AVISO = (
    "Estimación ilustrativa con probabilidades inventadas para un prototipo académico. "
    "No es un diagnóstico, una evaluación médica ni una cotización. Tus respuestas no se guardan."
)


def preguntas() -> List[PreguntaOut]:
    return [
        PreguntaOut(
            id=p.id,
            texto=p.texto,
            ayuda=p.ayuda,
            grupo=p.grupo,  # type: ignore[arg-type]
            opciones=[OpcionPreguntaOut(valor=o.valor, etiqueta=o.etiqueta) for o in p.opciones],
        )
        for p in bayes.PREGUNTAS
    ]


def _analisis_out(analisis: bayes.AnalisisRiesgo) -> AnalisisRiesgoOut:
    return AnalisisRiesgoOut(
        prior=analisis.prior,
        posterior=analisis.posterior,
        pasos=[PasoBayesOut(**paso.__dict__) for paso in analisis.pasos],
        nivel_probable=analisis.nivel_probable,
        nivel_etiqueta=bayes.ETIQUETA_NIVEL[analisis.nivel_probable],
        indice_riesgo=analisis.indice_riesgo,
        prob_hospitalizacion=analisis.prob_hospitalizacion,
        frecuencias_naturales=analisis.frecuencias_naturales(1000),
    )


def evaluar(db: Session, entrada: CuestionarioIn) -> CuestionarioOut:
    respuestas = entrada.model_dump(exclude={"presupuesto_mensual"})
    analisis = bayes.analizar(respuestas)

    catalogo = repositorio.opciones_formulario(db)
    criterios = bayes.derivar_criterios(
        analisis,
        respuestas,
        deducibles=catalogo.deducibles,
        coaseguros=catalogo.coaseguros,
        sumas=catalogo.sumas_aseguradas,
        codigos_catalogo=[c.codigo for c in catalogo.coberturas],
    )

    def preferencias(**cambios) -> PreferenciasIn:
        datos = dict(
            presupuesto_mensual=entrada.presupuesto_mensual,
            deducible_maximo=criterios.deducible_maximo,
            coaseguro_maximo=criterios.coaseguro_maximo,
            suma_asegurada_minima=criterios.suma_asegurada_minima,
            coberturas_obligatorias=list(criterios.coberturas_obligatorias),
            coberturas_deseadas=list(criterios.coberturas_deseadas),
            pesos=PesosIn(**criterios.pesos),
        )
        datos.update(cambios)
        return PreferenciasIn(**datos)

    # Si las exigencias derivadas del riesgo no caben en el presupuesto, se relajan por pasos
    # (las "preferencias" cambian, las coberturas obligatorias nunca).
    intentos = [
        (preferencias(), None),
        (
            preferencias(coaseguro_maximo=None, suma_asegurada_minima=None),
            "Sin planes con tu presupuesto: se quitaron el tope de coaseguro y la suma asegurada mínima.",
        ),
        (
            preferencias(
                coaseguro_maximo=None,
                suma_asegurada_minima=None,
                deducible_maximo=max(catalogo.deducibles),
            ),
            "Además se aceptó el deducible más alto del catálogo.",
        ),
    ]
    ajustes: List[str] = []
    for prefs, ajuste in intentos:
        if ajuste:
            ajustes.append(ajuste)
        recomendacion = recomendar(db, prefs)
        if recomendacion.candidatos_validos:
            break
    else:
        ajustes.append("Ningún plan cabe en ese presupuesto: sube el presupuesto mensual e inténtalo de nuevo.")

    return CuestionarioOut(
        aviso=AVISO,
        analisis=_analisis_out(analisis),
        razones=list(criterios.razones),
        ajustes=ajustes,
        preferencias_derivadas=prefs,
        recomendacion=recomendacion,
    )
