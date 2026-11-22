import type { ReactNode } from 'react';
import { ArrowLeft, Check, Minus, Scale, X } from 'lucide-react';
import { GlassButton } from '../components/ui/GlassButton';
import { GlassCard } from '../components/ui/GlassCard';
import { SectionHeader } from '../components/ui/SectionHeader';
import { StateMessage } from '../components/ui/StateMessage';
import { useBusqueda } from '../context/BusquedaContext';
import { cn } from '../lib/cn';
import { formatMXN, formatMillones } from '../lib/format';
import type { Opcion } from '../types/api';

type Mejor = 'min' | 'max' | null;

interface FilaNumerica {
  etiqueta: string;
  valor: (o: Opcion) => number;
  formato: (v: number) => string;
  mejor: Mejor;
}

const FILAS: FilaNumerica[] = [
  { etiqueta: 'Puntaje', valor: (o) => o.puntaje, formato: (v) => `${v.toFixed(1)} / 100`, mejor: 'max' },
  { etiqueta: 'Prima mensual total', valor: (o) => o.prima_total, formato: formatMXN, mejor: 'min' },
  { etiqueta: 'Prima base', valor: (o) => o.prima_base, formato: formatMXN, mejor: null },
  { etiqueta: 'Coberturas opcionales', valor: (o) => o.costo_opcionales, formato: formatMXN, mejor: null },
  { etiqueta: 'Deducible', valor: (o) => o.deducible, formato: formatMXN, mejor: 'min' },
  { etiqueta: 'Coaseguro', valor: (o) => o.coaseguro_porcentaje, formato: (v) => `${v}%`, mejor: 'min' },
  { etiqueta: 'Suma asegurada', valor: (o) => o.suma_asegurada, formato: formatMillones, mejor: 'max' },
];

export function CompararPage() {
  const { resultado, comparar, alternarComparar } = useBusqueda();
  const opciones = (resultado?.ranking ?? []).filter((o) => comparar.includes(o.id));

  const encabezado = (
    <SectionHeader
      level="h1"
      align="left"
      eyebrow="Comparación"
      eyebrowIcon={Scale}
      title="Compara lado a lado"
      description="Hasta tres configuraciones del último resultado. En verde, el mejor valor de cada fila."
    />
  );

  if (opciones.length < 2) {
    return (
      <div className="mx-auto max-w-[1680px] py-12 sm:py-16">
        {encabezado}
        <div className="mx-auto mt-10 max-w-3xl">
          <StateMessage
            variant="empty"
            title="Selecciona al menos dos opciones"
            action={
              <GlassButton to={resultado ? '/resultados' : '/buscar'} icon={ArrowLeft} iconPosition="left">
                {resultado ? 'Volver a resultados' : 'Hacer una búsqueda'}
              </GlassButton>
            }
          >
            En la pantalla de resultados, usa el botón «Comparar» de cada configuración.
          </StateMessage>
        </div>
      </div>
    );
  }

  // Todas las coberturas presentes en alguna opción, en orden alfabético.
  const coberturas = Array.from(new Set(opciones.flatMap((o) => o.coberturas.map((c) => c.nombre)))).sort();
  const deseadas = new Set(opciones.flatMap((o) => [...o.coberturas_deseadas_cubiertas, ...o.coberturas_deseadas_faltantes]));

  return (
    <div className="mx-auto max-w-[1680px] py-12 sm:py-16">
      <div className="flex flex-wrap items-end justify-between gap-6">
        {encabezado}
        <GlassButton to="/resultados" variant="secondary" icon={ArrowLeft} iconPosition="left">
          Volver a resultados
        </GlassButton>
      </div>

      <GlassCard tone="strong" padding="none" className="mt-10 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[44rem] border-collapse text-sm">
            <caption className="sr-only">Comparación de configuraciones seleccionadas</caption>
            <thead>
              <tr>
                <th scope="col" className="sticky left-0 z-10 w-56 bg-white/95 p-5 text-left align-bottom text-xs font-semibold uppercase tracking-wider text-slate-500 backdrop-blur">
                  Configuración
                </th>
                {opciones.map((o) => (
                  <th key={o.id} scope="col" className="p-5 text-left align-top">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <span className="text-xs font-semibold text-ice-700">#{o.posicion} del ranking</span>
                        <p className="text-lg font-semibold leading-tight text-slate-900">{o.plan}</p>
                        <p className="text-xs font-normal text-slate-500">
                          {o.aseguradora} · {o.nivel}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => alternarComparar(o.id)}
                        aria-label={`Quitar ${o.plan} de la comparación`}
                        className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-slate-400 transition hover:bg-white hover:text-slate-700"
                      >
                        <X aria-hidden="true" size={16} />
                      </button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-ice-100">
              {FILAS.map((fila) => {
                const valores = opciones.map(fila.valor);
                const objetivo = fila.mejor === 'min' ? Math.min(...valores) : fila.mejor === 'max' ? Math.max(...valores) : null;
                const hayDiferencia = new Set(valores).size > 1;
                return (
                  <Fila key={fila.etiqueta} etiqueta={fila.etiqueta}>
                    {opciones.map((o, i) => {
                      const esMejor = objetivo !== null && hayDiferencia && valores[i] === objetivo;
                      return (
                        <td key={o.id} className={cn('p-5 tabular-nums', esMejor ? 'font-semibold text-emerald-700' : 'text-slate-700')}>
                          {fila.formato(valores[i])}
                        </td>
                      );
                    })}
                  </Fila>
                );
              })}
              <tr>
                <td colSpan={opciones.length + 1} className="bg-ice-50/70 px-5 py-3 text-xs font-semibold uppercase tracking-wider text-ice-800">
                  Coberturas
                </td>
              </tr>
              {coberturas.map((nombre) => (
                <Fila key={nombre} etiqueta={nombre} nota={deseadas.has(nombre) ? 'Deseada' : undefined}>
                  {opciones.map((o) => {
                    const c = o.coberturas.find((x) => x.nombre === nombre);
                    return (
                      <td key={o.id} className="p-5">
                        {c ? (
                          <span className="inline-flex items-center gap-1.5 text-slate-700">
                            <Check aria-hidden="true" size={16} className="text-emerald-600" />
                            {c.origen === 'incluida' ? 'Incluida' : `Opcional · ${formatMXN(c.costo_extra)}`}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 text-slate-400">
                            <Minus aria-hidden="true" size={16} />
                            No incluida
                          </span>
                        )}
                      </td>
                    );
                  })}
                </Fila>
              ))}
              <tr>
                <td colSpan={opciones.length + 1} className="bg-ice-50/70 px-5 py-3 text-xs font-semibold uppercase tracking-wider text-ice-800">
                  Aporte de cada criterio al puntaje
                </td>
              </tr>
              {opciones[0].componentes.map((comp) => (
                <Fila key={comp.criterio} etiqueta={comp.etiqueta}>
                  {opciones.map((o) => {
                    const c = o.componentes.find((x) => x.criterio === comp.criterio);
                    return (
                      <td key={o.id} className="p-5 tabular-nums text-slate-700">
                        {c ? `${(c.contribucion * 100).toFixed(1)} pts` : '—'}
                        {c && <span className="ml-2 text-xs text-slate-400">({c.valor_texto})</span>}
                      </td>
                    );
                  })}
                </Fila>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
      <p className="mt-4 text-xs text-slate-500">
        Datos simulados con fines académicos. No constituye una cotización ni una oferta de venta.
      </p>
    </div>
  );
}

function Fila({ etiqueta, nota, children }: { etiqueta: string; nota?: string; children: ReactNode }) {
  return (
    <tr className="hover:bg-white/40">
      <th scope="row" className="sticky left-0 z-10 bg-white/95 p-5 text-left font-medium text-slate-800 backdrop-blur">
        {etiqueta}
        {nota && <span className="ml-2 rounded-full bg-ice-100 px-2 py-0.5 text-[0.7rem] font-semibold text-ice-800">{nota}</span>}
      </th>
      {children}
    </tr>
  );
}
