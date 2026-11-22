"""
Esquemas Pydantic: contratos de entrada/salida de la API y del catálogo mock.

Privacidad: PreferenciasIn usa extra="forbid", así que la API RECHAZA cualquier campo
no previsto (edad, padecimientos, nombre…). Solo se aceptan restricciones y pesos.
"""
from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------- catálogo mock
class AseguradoraMock(BaseModel):
    external_id: str
    nombre: str


class CoberturaMock(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None


class VarianteMock(BaseModel):
    deducible: float = Field(ge=0)
    coaseguro_porcentaje: float = Field(ge=0, le=100)
    prima_mensual: float = Field(gt=0)


class OfertaMock(BaseModel):
    codigo: str
    tipo: Literal["incluida", "opcional"]
    costo_extra: float = Field(ge=0)


class ReglaMock(BaseModel):
    tipo: Literal["requiere", "excluye", "deducible_max"]
    cobertura: str
    cobertura_objetivo: Optional[str] = None
    valor: Optional[float] = None


class PlanMock(BaseModel):
    external_id: str
    aseguradora_external_id: str
    nombre: str
    nivel: Literal["Básico", "Intermedio", "Premium"]
    suma_asegurada: float = Field(gt=0)
    moneda: str = "MXN"
    variantes: List[VarianteMock] = Field(min_length=1)
    coberturas: List[OfertaMock]
    reglas: List[ReglaMock] = []


class CatalogoMock(BaseModel):
    simulado: bool
    aseguradoras: List[AseguradoraMock]
    coberturas: List[CoberturaMock]
    planes: List[PlanMock]


# ---------------------------------------------------------------- entrada usuario
class PesosIn(BaseModel):
    """Importancia de 0 a 100 por criterio; el backend los normaliza para que sumen 1."""

    model_config = ConfigDict(extra="forbid")
    costo: float = Field(35, ge=0, le=100)
    deducible: float = Field(20, ge=0, le=100)
    coaseguro: float = Field(10, ge=0, le=100)
    suma_asegurada: float = Field(15, ge=0, le=100)
    coberturas: float = Field(20, ge=0, le=100)


class PreferenciasIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    presupuesto_mensual: float = Field(gt=0, le=200_000, description="MXN por mes")
    deducible_maximo: float = Field(ge=0, le=1_000_000)
    coaseguro_maximo: Optional[float] = Field(None, ge=0, le=100)
    suma_asegurada_minima: Optional[float] = Field(None, ge=0)
    coberturas_obligatorias: List[str] = []
    coberturas_deseadas: List[str] = []
    pesos: PesosIn = PesosIn()
    algoritmo: Literal["backtracking_fc", "backtracking"] = "backtracking_fc"

    @model_validator(mode="after")
    def _sin_duplicados(self) -> "PreferenciasIn":
        # Una cobertura obligatoria ya está garantizada: no se cuenta también como deseada.
        self.coberturas_obligatorias = list(dict.fromkeys(self.coberturas_obligatorias))
        self.coberturas_deseadas = [
            c for c in dict.fromkeys(self.coberturas_deseadas) if c not in self.coberturas_obligatorias
        ]
        return self


class SyncIn(BaseModel):
    incluir_novedades: bool = False


# ---------------------------------------------------------------- salida catálogo
class CoberturaOut(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None


class VarianteOut(BaseModel):
    deducible: float
    coaseguro_porcentaje: float
    prima_mensual: float


class OfertaOut(BaseModel):
    codigo: str
    nombre: str
    tipo: str
    costo_extra: float


class ReglaOut(BaseModel):
    tipo: str
    cobertura: str
    cobertura_objetivo: Optional[str] = None
    valor: Optional[float] = None
    descripcion: str


class PlanOut(BaseModel):
    id: int
    external_id: str
    nombre: str
    aseguradora: str
    nivel: str
    suma_asegurada: float
    moneda: str
    activo: bool
    simulado: bool = True
    variantes: List[VarianteOut]
    coberturas: List[OfertaOut]
    reglas: List[ReglaOut]


class OpcionesOut(BaseModel):
    """Valores reales del catálogo para construir el formulario."""

    coberturas: List[CoberturaOut]
    deducibles: List[float]
    coaseguros: List[float]
    sumas_aseguradas: List[float]
    prima_minima: Optional[float]
    prima_maxima: Optional[float]
    planes_activos: int


class SyncOut(BaseModel):
    id: int
    fecha: datetime
    origen: str
    creados: int
    actualizados: int
    desactivados: int
    sin_cambios: int
    resultado: str
    mensaje: Optional[str] = None


class EstadoServicio(BaseModel):
    ok: bool
    detalle: str


class EstadoOut(BaseModel):
    backend: EstadoServicio
    base_datos: EstadoServicio
    mock_api: EstadoServicio
    catalogo: Dict[str, int]
    ultima_sincronizacion: Optional[SyncOut]


# ---------------------------------------------------------------- recomendación
class ComponenteOut(BaseModel):
    criterio: str
    etiqueta: str
    valor: float
    valor_texto: str
    normalizado: float
    peso: float
    contribucion: float


class CoberturaIncluidaOut(BaseModel):
    codigo: str
    nombre: str
    origen: Literal["incluida", "opcional"]
    costo_extra: float


class OpcionOut(BaseModel):
    id: str
    posicion: int
    puntaje: float = Field(description="0 a 100")
    plan_external_id: str
    plan: str
    aseguradora: str
    nivel: str
    suma_asegurada: float
    deducible: float
    coaseguro_porcentaje: float
    prima_base: float
    costo_opcionales: float
    prima_total: float
    coberturas: List[CoberturaIncluidaOut]
    coberturas_deseadas_cubiertas: List[str]
    coberturas_deseadas_faltantes: List[str]
    componentes: List[ComponenteOut]
    restricciones_cumplidas: List[str]
    es_menor_prima: bool


class MotivoOut(BaseModel):
    restriccion: str
    etiqueta: str
    detalle: str


class DescarteOut(BaseModel):
    plan_external_id: str
    plan: str
    aseguradora: str
    motivos: List[MotivoOut]


class EstadisticasOut(BaseModel):
    algoritmo: str
    espacio_busqueda: int
    nodos_explorados: int
    backtracks: int
    podas: Dict[str, int]
    total_podas: int
    soluciones: int
    tiempo_ms: float


class ComparacionBaselineOut(BaseModel):
    """Contraste entre el mejor multicriterio y la opción de menor prima."""

    misma_opcion: bool
    posicion_menor_prima: Optional[int]
    diferencia_prima: float
    diferencia_puntaje: float


class RecomendacionOut(BaseModel):
    consulta_id: int
    simulado: bool = True
    aviso: str
    algoritmo_utilizado: str
    planes_evaluados: int
    candidatos_validos: int
    pesos_aplicados: Dict[str, float]
    estadisticas: EstadisticasOut
    comparacion_algoritmos: List[EstadisticasOut]
    ranking: List[OpcionOut]
    menor_prima: Optional[OpcionOut]
    comparacion_baseline: Optional[ComparacionBaselineOut]
    descartes: List[DescarteOut]


# ---------------------------------------------------------------- cuestionario (Bayes)
class CuestionarioIn(BaseModel):
    """
    Respuestas del cuestionario de riesgo. Son datos de salud SENSIBLES: se usan solo para esta
    petición y NO se guardan (ni en la base de datos ni en logs). extra="forbid" rechaza cualquier
    otro campo (nombre, correo, diagnósticos en texto libre...).
    """

    model_config = ConfigDict(extra="forbid")

    edad: Literal["18-29", "30-44", "45-59", "60+"]
    fuma: Literal["no", "ocasional", "si"]
    actividad: Literal["alta", "media", "baja"]
    peso: Literal["normal", "sobrepeso", "obesidad"]
    cronicas: Literal["ninguna", "una", "varias"]
    hospitalizaciones: Literal["ninguna", "una", "varias"]
    familiar: Literal["no", "si"]
    maternidad: Literal["no", "si"] = "no"
    viajes: Literal["no", "si"] = "no"
    presupuesto_mensual: float = Field(gt=0, le=200_000, description="MXN por mes")


class OpcionPreguntaOut(BaseModel):
    valor: str
    etiqueta: str


class PreguntaOut(BaseModel):
    id: str
    texto: str
    ayuda: str
    grupo: Literal["prior", "evidencia", "necesidad"]
    opciones: List[OpcionPreguntaOut]


class PasoBayesOut(BaseModel):
    pregunta_id: str
    pregunta: str
    respuesta: str
    verosimilitud: Dict[str, float]
    probabilidad_evidencia: float
    antes: Dict[str, float]
    despues: Dict[str, float]


class AnalisisRiesgoOut(BaseModel):
    prior: Dict[str, float]
    posterior: Dict[str, float]
    pasos: List[PasoBayesOut]
    nivel_probable: str
    nivel_etiqueta: str
    indice_riesgo: float
    prob_hospitalizacion: float
    frecuencias_naturales: Dict[str, float]


class CuestionarioOut(BaseModel):
    aviso: str
    analisis: AnalisisRiesgoOut
    razones: List[str]
    ajustes: List[str]
    preferencias_derivadas: PreferenciasIn
    recomendacion: RecomendacionOut
