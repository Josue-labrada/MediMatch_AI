import { useCallback, useEffect, useState } from 'react';

interface ApiState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
}

/** Ejecuta una petición al montar el componente y expone datos, error y recarga. */
export function useApi<T>(fetcher: () => Promise<T>): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let vigente = true;
    setLoading(true);
    fetcher()
      .then((d) => {
        if (vigente) {
          setData(d);
          setError(null);
        }
      })
      .catch((e: Error) => vigente && setError(e.message))
      .finally(() => vigente && setLoading(false));
    return () => {
      vigente = false;
    };
    // fetcher se pasa como referencia estable (funciones del objeto api).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);
  return { data, error, loading, reload };
}
