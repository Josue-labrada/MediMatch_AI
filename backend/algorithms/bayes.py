"""
Regla de Bayes para estimar el NIVEL DE RIESGO de salud de una persona a partir de un cuestionario.

Python puro (sin FastAPI ni base de datos), igual que csp.py y ranking.py: se puede probar con
pytest y explicar sin mezclar infraestructura.

Idea (Fundamentos de IA): empiezo con una creencia (prior), veo evidencia y la ACTUALIZO (posterior).

                 P(evidencia | hipótesis) · P(hipótesis)
P(hipótesis | evidencia) = ---------------------------------
                                  P(evidencia)

Cómo se aplica aquí
  hipótesis  = nivel de riesgo de la persona: "bajo", "medio" o "alto"
  prior      = P(nivel) según el GRUPO DE EDAD (lo que creemos antes de preguntar nada más)
  evidencia  = cada respuesta del cuestionario (fuma, actividad física, peso, ...)
  verosimilitud = P(respuesta | nivel): ¿qué tan común es esa respuesta entre personas de ese nivel?
  posterior  = P(nivel | respuestas); el posterior de cada respuesta es el prior de la siguiente.

Supuesto (Bayes ingenuo): dado el nivel de riesgo, las respuestas son independientes entre sí.
Es una simplificación; permite multiplicar las verosimilitudes una por una.

IMPORTANTE: todas las probabilidades de este archivo son ILUSTRATIVAS (prototipo académico).
No provienen de estudios actuariales ni médicos y no sustituyen una evaluación real.

Contenido
  1) ReglaDeBayes       varias hipótesis (clase del profesor).
  2) PruebaDiagnostica  dos hipótesis: enfermo / sano (clase del profesor).
  3) Modelo de riesgo   priors, verosimilitudes y cuestionario.
  4) analizar()         aplica Bayes respuesta por respuesta.
  5) derivar_criterios  traduce el riesgo a restricciones y pesos para el CSP existente.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple


# ===========================================================================
# 1) REGLA DE BAYES CON VARIAS HIPÓTESIS
# ===========================================================================
class ReglaDeBayes:
    def __init__(self, probabilidades_previas: Mapping[str, float]):
        # {hipótesis: prior}. Las probabilidades deben sumar 1.
        self.previas: Dict[str, float] = dict(probabilidades_previas)

    def probabilidad_evidencia(self, verosimilitudes: Mapping[str, float]) -> float:
        # Probabilidad total: P(E) = suma de P(E | H) * P(H)
        total = 0.0
        for hipotesis in self.previas:
            total = total + verosimilitudes[hipotesis] * self.previas[hipotesis]
        return total

    def posteriores(self, verosimilitudes: Mapping[str, float]) -> Dict[str, float]:
        # verosimilitudes: {hipótesis: P(evidencia | hipótesis)}
        evidencia = self.probabilidad_evidencia(verosimilitudes)
        resultado = {}
        for hipotesis in self.previas:
            numerador = verosimilitudes[hipotesis] * self.previas[hipotesis]
            resultado[hipotesis] = numerador / evidencia
        return resultado

    def actualizar(self, verosimilitudes: Mapping[str, float]) -> None:
        # El posterior de hoy se convierte en el prior de mañana.
        self.previas = self.posteriores(verosimilitudes)


# ===========================================================================
# 2) PRUEBA DIAGNÓSTICA (dos hipótesis)
# ===========================================================================
class PruebaDiagnostica:
    def __init__(self, nombre: str, prior: float, sensibilidad: float, especificidad: float):
        self.nombre = nombre
        self.prior = prior  # P(enfermo) antes de la prueba
        self.sensibilidad = sensibilidad  # P(positivo | enfermo)
        self.especificidad = especificidad  # P(negativo | sano)

    def falsos_positivos(self) -> float:
        return 1 - self.especificidad  # P(positivo | sano)

    def probabilidad_positivo(self) -> float:
        con_enfermedad = self.sensibilidad * self.prior
        sin_enfermedad = self.falsos_positivos() * (1 - self.prior)
        return con_enfermedad + sin_enfermedad

    def posterior_si_positivo(self) -> float:
        return self.sensibilidad * self.prior / self.probabilidad_positivo()

    def posterior_si_negativo(self) -> float:
        probabilidad_negativo = 1 - self.probabilidad_positivo()
        return (1 - self.sensibilidad) * self.prior / probabilidad_negativo

    def frecuencias_naturales(self, poblacion: float) -> Dict[str, float]:
        # Misma cuenta, pero con personas en lugar de probabilidades.
        enfermos = poblacion * self.prior
        sanos = poblacion - enfermos
        return {
            "enfermos": enfermos,
            "verdaderos positivos": enfermos * self.sensibilidad,
            "falsos negativos": enfermos * (1 - self.sensibilidad),
            "sanos": sanos,
            "falsos positivos": sanos * self.falsos_positivos(),
            "verdaderos negativos": sanos * self.especificidad,
        }

    def posteriores_con_repeticion(self, repeticiones: int) -> List[float]:
        # Si la prueba da positivo varias veces (independientes), el posterior es el prior de la siguiente.
        prior_actual = self.prior
        lista = []
        for _ in range(repeticiones):
            prueba = PruebaDiagnostica(self.nombre, prior_actual, self.sensibilidad, self.especificidad)
            prior_actual = prueba.posterior_si_positivo()
            lista.append(prior_actual)
        return lista


# ===========================================================================
# 3) MODELO DE RIESGO (datos ilustrativos)
# ===========================================================================
NIVELES: Tuple[str, ...] = ("bajo", "medio", "alto")
ETIQUETA_NIVEL: Dict[str, str] = {"bajo": "Riesgo bajo", "medio": "Riesgo medio", "alto": "Riesgo alto"}


@dataclass(frozen=True)
class OpcionPregunta:
    valor: str
    etiqueta: str
    # P(respuesta | nivel). Para cada nivel, las verosimilitudes de TODAS las opciones suman 1.
    verosimilitud: Mapping[str, float] = field(default_factory=dict)
    # Solo para la edad: prior P(nivel) del grupo de edad.
    prior: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Pregunta:
    id: str
    texto: str
    ayuda: str
    grupo: str  # "prior" (edad) | "evidencia" (Bayes) | "necesidad" (sí/no que NO entra a Bayes)
    opciones: Tuple[OpcionPregunta, ...]

    def opcion(self, valor: str) -> OpcionPregunta:
        for o in self.opciones:
            if o.valor == valor:
                return o
        raise ValueError(f"Respuesta inválida para '{self.id}': {valor!r}")


def _v(bajo: float, medio: float, alto: float) -> Dict[str, float]:
    return {"bajo": bajo, "medio": medio, "alto": alto}


# Edad → prior. Mientras mayor la edad, más masa de probabilidad en riesgo medio/alto.
EDAD = Pregunta(
    "edad",
    "¿En qué rango de edad estás?",
    "Define la creencia inicial (prior) antes de ver el resto de tus respuestas.",
    "prior",
    (
        OpcionPregunta("18-29", "18 a 29 años", prior=_v(0.70, 0.25, 0.05)),
        OpcionPregunta("30-44", "30 a 44 años", prior=_v(0.55, 0.33, 0.12)),
        OpcionPregunta("45-59", "45 a 59 años", prior=_v(0.35, 0.40, 0.25)),
        OpcionPregunta("60+", "60 años o más", prior=_v(0.15, 0.40, 0.45)),
    ),
)

# Cada respuesta es evidencia: verosimilitud = P(respuesta | nivel de riesgo).
EVIDENCIA: Tuple[Pregunta, ...] = (
    Pregunta(
        "fuma", "¿Fumas?", "Tabaco o vapeo.", "evidencia",
        (
            OpcionPregunta("no", "No", _v(0.80, 0.60, 0.40)),
            OpcionPregunta("ocasional", "Ocasionalmente", _v(0.15, 0.25, 0.25)),
            OpcionPregunta("si", "Sí, con frecuencia", _v(0.05, 0.15, 0.35)),
        ),
    ),
    Pregunta(
        "actividad", "¿Cuánta actividad física haces?", "Ejercicio o deporte en una semana normal.", "evidencia",
        (
            OpcionPregunta("alta", "Alta (4+ veces por semana)", _v(0.45, 0.25, 0.10)),
            OpcionPregunta("media", "Media (1 a 3 veces)", _v(0.40, 0.45, 0.35)),
            OpcionPregunta("baja", "Baja (casi nunca)", _v(0.15, 0.30, 0.55)),
        ),
    ),
    Pregunta(
        "peso", "¿Cómo describirías tu peso?", "Según tu índice de masa corporal (IMC).", "evidencia",
        (
            OpcionPregunta("normal", "Normal", _v(0.75, 0.50, 0.25)),
            OpcionPregunta("sobrepeso", "Sobrepeso", _v(0.20, 0.35, 0.35)),
            OpcionPregunta("obesidad", "Obesidad", _v(0.05, 0.15, 0.40)),
        ),
    ),
    Pregunta(
        "cronicas", "¿Tienes enfermedades crónicas diagnosticadas?", "Por ejemplo diabetes o hipertensión.", "evidencia",
        (
            OpcionPregunta("ninguna", "Ninguna", _v(0.90, 0.55, 0.15)),
            OpcionPregunta("una", "Una", _v(0.09, 0.35, 0.40)),
            OpcionPregunta("varias", "Dos o más", _v(0.01, 0.10, 0.45)),
        ),
    ),
    Pregunta(
        "hospitalizaciones", "¿Cuántas hospitalizaciones has tenido en los últimos 5 años?", "No cuentan partos.", "evidencia",
        (
            OpcionPregunta("ninguna", "Ninguna", _v(0.90, 0.65, 0.35)),
            OpcionPregunta("una", "Una", _v(0.08, 0.25, 0.35)),
            OpcionPregunta("varias", "Dos o más", _v(0.02, 0.10, 0.30)),
        ),
    ),
    Pregunta(
        "familiar", "¿Hay antecedentes familiares graves?", "Cáncer o enfermedades del corazón en padres o hermanos.", "evidencia",
        (
            OpcionPregunta("no", "No", _v(0.85, 0.65, 0.45)),
            OpcionPregunta("si", "Sí", _v(0.15, 0.35, 0.55)),
        ),
    ),
)

# Necesidades: NO son evidencia de riesgo; solo marcan coberturas deseadas.
NECESIDADES: Tuple[Pregunta, ...] = (
    Pregunta(
        "maternidad", "¿Planeas tener un bebé en los próximos 2 años?", "Se añadirá Maternidad a tus coberturas deseadas.", "necesidad",
        (OpcionPregunta("no", "No"), OpcionPregunta("si", "Sí")),
    ),
    Pregunta(
        "viajes", "¿Viajas con frecuencia al extranjero?", "Se añadirá Emergencia en el extranjero a tus coberturas deseadas.", "necesidad",
        (OpcionPregunta("no", "No"), OpcionPregunta("si", "Sí")),
    ),
)

PREGUNTAS: Tuple[Pregunta, ...] = (EDAD,) + EVIDENCIA + NECESIDADES

# P(hospitalización mayor en los próximos 12 meses | nivel de riesgo). Ilustrativo.
P_HOSPITALIZACION: Dict[str, float] = {"bajo": 0.03, "medio": 0.10, "alto": 0.28}


def validar_modelo() -> None:
    """Comprueba que el modelo sea una distribución de probabilidad válida (lo usan las pruebas)."""
    for opcion in EDAD.opciones:
        assert abs(sum(opcion.prior.values()) - 1) < 1e-9, f"prior de {opcion.valor} no suma 1"
    for pregunta in EVIDENCIA:
        for nivel in NIVELES:
            total = sum(o.verosimilitud[nivel] for o in pregunta.opciones)
            assert abs(total - 1) < 1e-9, f"'{pregunta.id}' / {nivel}: verosimilitudes suman {total}"


# ===========================================================================
# 4) ANÁLISIS: Bayes respuesta por respuesta
# ===========================================================================
@dataclass(frozen=True)
class PasoBayes:
    """Una actualización: cómo cambió la creencia al ver una respuesta."""

    pregunta_id: str
    pregunta: str
    respuesta: str
    verosimilitud: Dict[str, float]  # P(respuesta | nivel)
    probabilidad_evidencia: float  # P(respuesta) por probabilidad total
    antes: Dict[str, float]  # prior de este paso
    despues: Dict[str, float]  # posterior de este paso


@dataclass(frozen=True)
class AnalisisRiesgo:
    prior: Dict[str, float]
    posterior: Dict[str, float]
    pasos: Tuple[PasoBayes, ...]
    nivel_probable: str
    indice_riesgo: float  # 0..1 = P(medio)·0.5 + P(alto)
    prob_hospitalizacion: float  # probabilidad total sobre el posterior

    def frecuencias_naturales(self, poblacion: int = 1000) -> Dict[str, float]:
        """Misma idea en personas: de cada `poblacion` personas como tú, ¿cuántas hospitalizadas?"""
        return {
            "poblacion": float(poblacion),
            "hospitalizadas": poblacion * self.prob_hospitalizacion,
            **{f"nivel_{n}": poblacion * self.posterior[n] for n in NIVELES},
        }


def _indice(posterior: Mapping[str, float]) -> float:
    return posterior["medio"] * 0.5 + posterior["alto"]


def analizar(respuestas: Mapping[str, str]) -> AnalisisRiesgo:
    """
    respuestas: {id_pregunta: valor}. Requiere 'edad' y todas las preguntas de evidencia.
    Aplica Bayes en el orden del cuestionario y devuelve cada paso para poder explicarlo.
    """
    prior = EDAD.opcion(respuestas["edad"]).prior
    bayes = ReglaDeBayes(prior)
    pasos: List[PasoBayes] = []

    for pregunta in EVIDENCIA:
        respuesta = pregunta.opcion(respuestas[pregunta.id])
        antes = dict(bayes.previas)
        evidencia = bayes.probabilidad_evidencia(respuesta.verosimilitud)
        bayes.actualizar(respuesta.verosimilitud)  # posterior de hoy = prior de mañana
        pasos.append(
            PasoBayes(
                pregunta_id=pregunta.id,
                pregunta=pregunta.texto,
                respuesta=respuesta.etiqueta,
                verosimilitud=dict(respuesta.verosimilitud),
                probabilidad_evidencia=evidencia,
                antes=antes,
                despues=dict(bayes.previas),
            )
        )

    posterior = dict(bayes.previas)
    # Probabilidad total: P(hosp) = Σ P(hosp | nivel) · P(nivel | respuestas)
    prob_hosp = sum(P_HOSPITALIZACION[n] * posterior[n] for n in NIVELES)
    return AnalisisRiesgo(
        prior=dict(prior),
        posterior=posterior,
        pasos=tuple(pasos),
        nivel_probable=max(NIVELES, key=lambda n: posterior[n]),
        indice_riesgo=_indice(posterior),
        prob_hospitalizacion=prob_hosp,
    )


# ===========================================================================
# 5) DEL RIESGO A LAS PREFERENCIAS DEL CSP
# ===========================================================================
@dataclass(frozen=True)
class CriteriosDerivados:
    deducible_maximo: float
    coaseguro_maximo: Optional[float]
    suma_asegurada_minima: Optional[float]
    coberturas_obligatorias: Tuple[str, ...]
    coberturas_deseadas: Tuple[str, ...]
    pesos: Dict[str, float]
    razones: Tuple[str, ...]  # explicación legible de cada decisión


# Pesos en los extremos del índice de riesgo; entre ambos se interpola linealmente.
PESOS_RIESGO_BAJO = {"costo": 70, "deducible": 10, "coaseguro": 5, "suma_asegurada": 5, "coberturas": 10}
PESOS_RIESGO_ALTO = {"costo": 10, "deducible": 20, "coaseguro": 15, "suma_asegurada": 25, "coberturas": 30}


def _elegir(valores: Sequence[float], posicion: float) -> float:
    """Valor del catálogo (ordenado) en la posición relativa 0..1."""
    ordenados = sorted(valores)
    return ordenados[min(len(ordenados) - 1, int(posicion * len(ordenados)))]


def derivar_criterios(
    analisis: AnalisisRiesgo,
    respuestas: Mapping[str, str],
    deducibles: Sequence[float],
    coaseguros: Sequence[float],
    sumas: Sequence[float],
    codigos_catalogo: Sequence[str],
) -> CriteriosDerivados:
    """
    Regla simple y explicable: a mayor riesgo, más protección exigida (deducible bajo, mejor suma
    asegurada) y más peso a la protección que al ahorro. Las coberturas solo se piden si existen
    en el catálogo.
    """
    r = analisis.indice_riesgo
    razones: List[str] = [
        f"Índice de riesgo = P(medio)·0.5 + P(alto) = {r:.2f} (0 = sin riesgo, 1 = riesgo máximo)."
    ]

    if r < 0.25:
        deducible, coaseguro, suma = max(deducibles), None, None
        razones.append("Riesgo bajo: aceptas un deducible alto a cambio de una prima menor.")
    elif r < 0.55:
        deducible = _elegir(deducibles, 0.5)
        coaseguro, suma = None, _elegir(sumas, 0.2)
        razones.append("Riesgo medio: deducible intermedio y una suma asegurada mínima moderada.")
    else:
        deducible = _elegir(deducibles, 0.2)
        coaseguro, suma = _elegir(coaseguros, 0.5), _elegir(sumas, 0.45)
        razones.append("Riesgo alto: deducible bajo, coaseguro acotado y una suma asegurada amplia.")

    pesos = {k: PESOS_RIESGO_BAJO[k] + (PESOS_RIESGO_ALTO[k] - PESOS_RIESGO_BAJO[k]) * r for k in PESOS_RIESGO_BAJO}
    razones.append("Los pesos pasan de 'ahorrar' a 'protegerse' conforme sube el índice de riesgo.")

    deseadas: List[str] = []
    if respuestas.get("maternidad") == "si":
        deseadas.append("maternidad")
    if respuestas.get("viajes") == "si":
        deseadas.append("emergencia_extranjero")
    if respuestas.get("cronicas") in ("una", "varias") or r >= 0.55:
        deseadas += ["telemedicina", "checkup"]
    deseadas = [c for c in dict.fromkeys(deseadas) if c in codigos_catalogo and c != "hospitalizacion"]
    if deseadas:
        razones.append("Coberturas deseadas según tus necesidades y tu perfil: " + ", ".join(deseadas) + ".")

    obligatorias = ("hospitalizacion",) if "hospitalizacion" in codigos_catalogo else ()
    return CriteriosDerivados(
        deducible_maximo=deducible,
        coaseguro_maximo=coaseguro,
        suma_asegurada_minima=suma,
        coberturas_obligatorias=obligatorias,
        coberturas_deseadas=tuple(deseadas),
        pesos=pesos,
        razones=tuple(razones),
    )
