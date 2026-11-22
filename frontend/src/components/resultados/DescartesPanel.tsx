import { ChevronDown, XCircle } from 'lucide-react';
import type { Descarte } from '../../types/api';
import { Chip } from '../ui/Chip';
import { GlassCard } from '../ui/GlassCard';

/** Planes que el CSP descartó por completo, con la restricción responsable. */
export function DescartesPanel({ descartes, abierto = false }: { descartes: Descarte[]; abierto?: boolean }) {
  if (descartes.length === 0) return null;
  return (
    <GlassCard tone="strong" padding="none">
      <details open={abierto} className="group">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 p-6 sm:px-7 [&::-webkit-details-marker]:hidden">
          <span className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-2xl bg-rose-50 text-rose-600">
              <XCircle aria-hidden="true" size={19} />
            </span>
            <span>
              <span className="block text-lg font-semibold text-slate-900">Planes descartados ({descartes.length})</span>
              <span className="block text-sm text-slate-500">Razones de descarte que reportó el CSP</span>
            </span>
          </span>
          <ChevronDown aria-hidden="true" size={20} className="text-ice-700 transition-transform group-open:rotate-180" />
        </summary>
        <ul className="grid gap-3 px-6 pb-6 sm:px-7 lg:grid-cols-2 2xl:grid-cols-3">
          {descartes.map((d) => (
            <li key={d.plan_external_id} className="rounded-2xl bg-white/60 p-4 ring-1 ring-inset ring-white/80">
              <p className="font-semibold text-slate-900">{d.plan}</p>
              <p className="text-xs text-slate-500">{d.aseguradora}</p>
              <ul className="mt-3 space-y-2">
                {d.motivos.map((m) => (
                  <li key={m.detalle} className="text-sm text-slate-600">
                    <Chip tone="rose" className="mb-1">
                      {m.etiqueta}
                    </Chip>
                    <p className="leading-snug">{m.detalle}</p>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </details>
    </GlassCard>
  );
}
