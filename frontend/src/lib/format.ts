const mxn = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 });
const entero = new Intl.NumberFormat('es-MX');

export const formatMXN = (valor: number) => mxn.format(valor);
export const formatNumero = (valor: number) => entero.format(valor);
export const formatPct = (fraccion: number, decimales = 0) => `${(fraccion * 100).toFixed(decimales)}%`;

/** 5,000,000 → "$5 M" para sumas aseguradas. */
export function formatMillones(valor: number): string {
  return valor >= 1_000_000 ? `$${formatNumero(valor / 1_000_000)} M` : formatMXN(valor);
}

export function formatFecha(iso: string): string {
  return new Date(iso).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' });
}

export const ETIQUETA_ALGORITMO: Record<string, string> = {
  backtracking_fc: 'Backtracking + forward checking',
  backtracking: 'Backtracking simple',
};
