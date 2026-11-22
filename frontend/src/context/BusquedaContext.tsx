/**
 * Estado compartido de la búsqueda: últimas preferencias, último resultado del backend
 * y opciones marcadas para comparar. Se guarda en sessionStorage para sobrevivir a
 * recargas de la página (solo en este navegador; no contiene datos personales).
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { PreferenciasRequest, RecomendacionResponse } from '../types/api';

const CLAVE = 'medimatch.busqueda.v1';
export const MAX_COMPARAR = 3;

interface EstadoBusqueda {
  preferencias: PreferenciasRequest | null;
  resultado: RecomendacionResponse | null;
  comparar: string[];
}

interface BusquedaContextValue extends EstadoBusqueda {
  guardarResultado: (preferencias: PreferenciasRequest, resultado: RecomendacionResponse) => void;
  alternarComparar: (id: string) => void;
  limpiarComparar: () => void;
}

const vacio: EstadoBusqueda = { preferencias: null, resultado: null, comparar: [] };

function leer(): EstadoBusqueda {
  try {
    const crudo = sessionStorage.getItem(CLAVE);
    return crudo ? { ...vacio, ...JSON.parse(crudo) } : vacio;
  } catch {
    return vacio;
  }
}

const BusquedaContext = createContext<BusquedaContextValue | null>(null);

export function BusquedaProvider({ children }: { children: ReactNode }) {
  const [estado, setEstado] = useState<EstadoBusqueda>(leer);

  useEffect(() => {
    try {
      sessionStorage.setItem(CLAVE, JSON.stringify(estado));
    } catch {
      /* almacenamiento no disponible: la app sigue funcionando en memoria */
    }
  }, [estado]);

  const guardarResultado = useCallback((preferencias: PreferenciasRequest, resultado: RecomendacionResponse) => {
    setEstado({ preferencias, resultado, comparar: resultado.ranking.slice(0, 2).map((o) => o.id) });
  }, []);

  const alternarComparar = useCallback((id: string) => {
    setEstado((prev) => {
      if (prev.comparar.includes(id)) return { ...prev, comparar: prev.comparar.filter((x) => x !== id) };
      if (prev.comparar.length >= MAX_COMPARAR) return prev;
      return { ...prev, comparar: [...prev.comparar, id] };
    });
  }, []);

  const limpiarComparar = useCallback(() => setEstado((prev) => ({ ...prev, comparar: [] })), []);

  const value = useMemo(
    () => ({ ...estado, guardarResultado, alternarComparar, limpiarComparar }),
    [estado, guardarResultado, alternarComparar, limpiarComparar],
  );
  return <BusquedaContext.Provider value={value}>{children}</BusquedaContext.Provider>;
}

export function useBusqueda(): BusquedaContextValue {
  const ctx = useContext(BusquedaContext);
  if (!ctx) throw new Error('useBusqueda debe usarse dentro de <BusquedaProvider>');
  return ctx;
}
