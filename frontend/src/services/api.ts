/**
 * Capa de datos: única parte del frontend que habla con el backend.
 * Las rutas son relativas (/api/...); en desarrollo Vite las reenvía a FastAPI.
 */
import type {
  CuestionarioRequest,
  CuestionarioResponse,
  EstadoSistema,
  Opciones,
  PlanCatalogo,
  PreferenciasRequest,
  PreguntaCuestionario,
  RecomendacionResponse,
  Sincronizacion,
} from '../types/api';

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

/** Convierte el "detail" de FastAPI (texto o lista de errores de validación) en un mensaje legible. */
function mensajeDeError(detail: unknown, status: number): string {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e: { loc?: unknown[]; msg?: string }) => `${(e.loc ?? []).slice(1).join('.')}: ${e.msg ?? ''}`)
      .join(' · ');
  }
  return `Error ${status} del servidor`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError('No se pudo conectar con el backend. ¿Están corriendo los contenedores?', 0);
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(mensajeDeError(body?.detail, response.status), response.status);
  }
  return body as T;
}

export const api = {
  opciones: () => request<Opciones>('/api/opciones'),
  planes: () => request<PlanCatalogo[]>('/api/planes'),
  estado: () => request<EstadoSistema>('/api/estado'),
  historialSync: () => request<Sincronizacion[]>('/api/sync/historial'),
  sincronizar: (incluirNovedades: boolean) =>
    request<Sincronizacion>('/api/sync', {
      method: 'POST',
      body: JSON.stringify({ incluir_novedades: incluirNovedades }),
    }),
  preguntasCuestionario: () => request<PreguntaCuestionario[]>('/api/cuestionario/preguntas'),
  evaluarCuestionario: (respuestas: CuestionarioRequest) =>
    request<CuestionarioResponse>('/api/cuestionario', {
      method: 'POST',
      body: JSON.stringify(respuestas),
    }),
  recomendar: (preferencias: PreferenciasRequest) =>
    request<RecomendacionResponse>('/api/recomendaciones', {
      method: 'POST',
      body: JSON.stringify(preferencias),
    }),
};
