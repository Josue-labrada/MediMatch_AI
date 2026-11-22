"""
Modelos de dominio para los algoritmos de IA.

Son dataclasses de Python puro: NO dependen de la base de datos ni de FastAPI.
Así el CSP y el ranking se pueden probar con pytest usando datos pequeños
escritos a mano, y explicar sin mezclar detalles de infraestructura.
"""
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Tuple

INCLUIDA = "incluida"
OPCIONAL = "opcional"

# Criterios de la función objetivo, en el orden en que se muestran.
CRITERIOS: Tuple[str, ...] = ("costo", "deducible", "coaseguro", "suma_asegurada", "coberturas")


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Variante:
    """Un valor del dominio de la variable D (variante de deducible)."""

    deducible: float
    coaseguro_porcentaje: float
    prima_mensual: float


@dataclass(frozen=True)
class OfertaCobertura:
    """Cómo ofrece un plan una cobertura: incluida (costo 0) u opcional (costo extra)."""

    codigo: str
    tipo: str  # INCLUIDA | OPCIONAL
    costo_extra: float = 0.0


@dataclass(frozen=True)
class Regla:
    """
    Restricción de compatibilidad del plan.
      requiere      : si `cobertura` se incluye, `objetivo` también debe incluirse.
      excluye       : `cobertura` y `objetivo` no pueden incluirse juntas.
      deducible_max : `cobertura` solo puede incluirse si deducible <= `valor`.
    """

    tipo: str
    cobertura: str
    objetivo: Optional[str] = None
    valor: Optional[float] = None


@dataclass(frozen=True)
class Plan:
    id: int
    external_id: str
    nombre: str
    aseguradora: str
    nivel: str
    suma_asegurada: float
    variantes: Tuple[Variante, ...]
    coberturas: Tuple[OfertaCobertura, ...]
    reglas: Tuple[Regla, ...] = ()

    def oferta(self, codigo: str) -> Optional[OfertaCobertura]:
        for o in self.coberturas:
            if o.codigo == codigo:
                return o
        return None


# ---------------------------------------------------------------------------
# Preferencias del usuario (sin datos personales ni médicos)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Pesos:
    """Importancia relativa de cada criterio. Se normalizan para sumar 1."""

    costo: float = 0.35
    deducible: float = 0.2
    coaseguro: float = 0.1
    suma_asegurada: float = 0.15
    coberturas: float = 0.2

    def como_dict(self) -> Dict[str, float]:
        return {c: float(getattr(self, c)) for c in CRITERIOS}


@dataclass(frozen=True)
class Preferencias:
    # Restricciones DURAS (el CSP las garantiza).
    presupuesto_mensual: float
    deducible_maximo: float
    coaseguro_maximo: Optional[float] = None
    suma_asegurada_minima: Optional[float] = None
    coberturas_obligatorias: Tuple[str, ...] = ()
    # Preferencias SUAVES (solo afectan la puntuación).
    coberturas_deseadas: Tuple[str, ...] = ()
    pesos: Pesos = field(default_factory=Pesos)


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Configuracion:
    """Asignación completa y consistente del CSP: plan + variante + coberturas opcionales elegidas."""

    plan: Plan
    variante: Variante
    opcionales: FrozenSet[str]

    @property
    def costo_opcionales(self) -> float:
        return sum(o.costo_extra for o in self.plan.coberturas if o.codigo in self.opcionales)

    @property
    def prima_total(self) -> float:
        return self.variante.prima_mensual + self.costo_opcionales

    @property
    def coberturas_totales(self) -> FrozenSet[str]:
        """Coberturas que tendría el usuario: las incluidas en el plan + las opcionales elegidas."""
        incluidas = {o.codigo for o in self.plan.coberturas if o.tipo == INCLUIDA}
        return frozenset(incluidas | set(self.opcionales))

    @property
    def clave(self) -> str:
        """Identificador estable de la configuración."""
        extras = "+".join(sorted(self.opcionales)) or "sin-extras"
        return f"{self.plan.external_id}|{int(self.variante.deducible)}|{extras}"


@dataclass(frozen=True)
class Motivo:
    """Restricción que provocó una poda, con un texto entendible para el usuario."""

    restriccion: str
    detalle: str
    # False para podas que nunca son la causa de fondo de un descarte (p. ej. quitar el
    # valor 0 de una cobertura obligatoria): cuentan en estadísticas, no en explicaciones.
    explicativo: bool = True


@dataclass
class Descarte:
    """Plan que no produjo ninguna configuración válida y por qué."""

    plan: Plan
    motivos: List[Motivo]


@dataclass
class EstadisticasCSP:
    algoritmo: str = ""
    espacio_busqueda: int = 0  # tamaño del producto cartesiano sin podar
    nodos_explorados: int = 0  # asignaciones parciales intentadas
    backtracks: int = 0  # veces que una variable agotó su dominio y se regresó
    podas: Dict[str, int] = field(default_factory=dict)  # restricción → nº de podas
    tiempo_ms: float = 0.0

    def registrar_poda(self, restriccion: str) -> None:
        self.podas[restriccion] = self.podas.get(restriccion, 0) + 1

    @property
    def total_podas(self) -> int:
        return sum(self.podas.values())


@dataclass
class ResultadoCSP:
    soluciones: List[Configuracion]
    descartes: List[Descarte]
    estadisticas: EstadisticasCSP


@dataclass(frozen=True)
class Componente:
    """Aporte de un criterio a la puntuación de una configuración."""

    criterio: str
    valor: float  # valor original (MXN, %, fracción)
    normalizado: float  # 0..1, donde 1 es lo mejor dentro del conjunto factible
    peso: float  # peso aplicado (ya normalizado)
    contribucion: float  # peso × normalizado


@dataclass(frozen=True)
class Recomendacion:
    posicion: int
    configuracion: Configuracion
    puntaje: float  # 0..1
    componentes: Tuple[Componente, ...]
