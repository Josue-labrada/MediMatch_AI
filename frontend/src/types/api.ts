/**
 * Contratos de la API del backend (espejo de backend/schemas.py).
 * El frontend solo muestra lo que calcula el backend: no contiene planes ni reglas.
 */

export type Criterio = 'costo' | 'deducible' | 'coaseguro' | 'suma_asegurada' | 'coberturas';
export type Algoritmo = 'backtracking_fc' | 'backtracking';
export type Importancia = 'ninguna' | 'deseada' | 'obligatoria';

export interface Cobertura {
  codigo: string;
  nombre: string;
  descripcion: string | null;
}

export interface Opciones {
  coberturas: Cobertura[];
  deducibles: number[];
  coaseguros: number[];
  sumas_aseguradas: number[];
  prima_minima: number | null;
  prima_maxima: number | null;
  planes_activos: number;
}

export type Pesos = Record<Criterio, number>;

export interface PreferenciasRequest {
  presupuesto_mensual: number;
  deducible_maximo: number;
  coaseguro_maximo: number | null;
  suma_asegurada_minima: number | null;
  coberturas_obligatorias: string[];
  coberturas_deseadas: string[];
  pesos: Pesos;
  algoritmo: Algoritmo;
}

export interface Componente {
  criterio: Criterio;
  etiqueta: string;
  valor: number;
  valor_texto: string;
  normalizado: number;
  peso: number;
  contribucion: number;
}

export interface CoberturaIncluida {
  codigo: string;
  nombre: string;
  origen: 'incluida' | 'opcional';
  costo_extra: number;
}

export interface Opcion {
  id: string;
  posicion: number;
  puntaje: number;
  plan_external_id: string;
  plan: string;
  aseguradora: string;
  nivel: string;
  suma_asegurada: number;
  deducible: number;
  coaseguro_porcentaje: number;
  prima_base: number;
  costo_opcionales: number;
  prima_total: number;
  coberturas: CoberturaIncluida[];
  coberturas_deseadas_cubiertas: string[];
  coberturas_deseadas_faltantes: string[];
  componentes: Componente[];
  restricciones_cumplidas: string[];
  es_menor_prima: boolean;
}

export interface Motivo {
  restriccion: string;
  etiqueta: string;
  detalle: string;
}

export interface Descarte {
  plan_external_id: string;
  plan: string;
  aseguradora: string;
  motivos: Motivo[];
}

export interface Estadisticas {
  algoritmo: Algoritmo;
  espacio_busqueda: number;
  nodos_explorados: number;
  backtracks: number;
  podas: Record<string, number>;
  total_podas: number;
  soluciones: number;
  tiempo_ms: number;
}

export interface ComparacionBaseline {
  misma_opcion: boolean;
  posicion_menor_prima: number | null;
  diferencia_prima: number;
  diferencia_puntaje: number;
}

export interface RecomendacionResponse {
  consulta_id: number;
  simulado: boolean;
  aviso: string;
  algoritmo_utilizado: string;
  planes_evaluados: number;
  candidatos_validos: number;
  pesos_aplicados: Partial<Record<Criterio, number>>;
  estadisticas: Estadisticas;
  comparacion_algoritmos: Estadisticas[];
  ranking: Opcion[];
  menor_prima: Opcion | null;
  comparacion_baseline: ComparacionBaseline | null;
  descartes: Descarte[];
}

export interface Variante {
  deducible: number;
  coaseguro_porcentaje: number;
  prima_mensual: number;
}

export interface Oferta {
  codigo: string;
  nombre: string;
  tipo: 'incluida' | 'opcional';
  costo_extra: number;
}

export interface Regla {
  tipo: string;
  cobertura: string;
  cobertura_objetivo: string | null;
  valor: number | null;
  descripcion: string;
}

export interface PlanCatalogo {
  id: number;
  external_id: string;
  nombre: string;
  aseguradora: string;
  nivel: string;
  suma_asegurada: number;
  moneda: string;
  activo: boolean;
  simulado: boolean;
  variantes: Variante[];
  coberturas: Oferta[];
  reglas: Regla[];
}

export interface Sincronizacion {
  id: number;
  fecha: string;
  origen: string;
  creados: number;
  actualizados: number;
  desactivados: number;
  sin_cambios: number;
  resultado: 'ok' | 'error';
  mensaje: string | null;
}

export interface EstadoServicio {
  ok: boolean;
  detalle: string;
}

export interface EstadoSistema {
  backend: EstadoServicio;
  base_datos: EstadoServicio;
  mock_api: EstadoServicio;
  catalogo: Record<string, number>;
  ultima_sincronizacion: Sincronizacion | null;
}

// ---------------------------------------------------------------- cuestionario (Bayes)
export type NivelRiesgo = 'bajo' | 'medio' | 'alto';
export type Distribucion = Record<NivelRiesgo, number>;

export interface PreguntaCuestionario {
  id: string;
  texto: string;
  ayuda: string;
  grupo: 'prior' | 'evidencia' | 'necesidad';
  opciones: Array<{ valor: string; etiqueta: string }>;
}

export interface PasoBayes {
  pregunta_id: string;
  pregunta: string;
  respuesta: string;
  verosimilitud: Distribucion;
  probabilidad_evidencia: number;
  antes: Distribucion;
  despues: Distribucion;
}

export interface AnalisisRiesgo {
  prior: Distribucion;
  posterior: Distribucion;
  pasos: PasoBayes[];
  nivel_probable: NivelRiesgo;
  nivel_etiqueta: string;
  indice_riesgo: number;
  prob_hospitalizacion: number;
  frecuencias_naturales: Record<string, number>;
}

/** Respuestas por id de pregunta (texto) más `presupuesto_mensual` (número). */
export type CuestionarioRequest = Record<string, string | number>;

export interface CuestionarioResponse {
  aviso: string;
  analisis: AnalisisRiesgo;
  razones: string[];
  ajustes: string[];
  preferencias_derivadas: PreferenciasRequest;
  recomendacion: RecomendacionResponse;
}
