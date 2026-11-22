import { Check, ChevronDown, CircleDollarSign, Minus, Plus, ShieldCheck } from 'lucide-react';
import { cn } from '../../lib/cn';
import { formatMXN, formatMillones, formatPct } from '../../lib/format';
import type { Opcion } from '../../types/api';
import { Chip } from '../ui/Chip';
import { GlassCard } from '../ui/GlassCard';
import { ProgressBar } from '../ui/ProgressBar';

interface OpcionCardProps {
  opcion: Opcion;
  seleccionada: boolean;
  puedeSeleccionar: boolean;
  onComparar: () => void;
  destacada?: boolean;
}

/** Una configuración del ranking con su explicación de puntaje y restricciones. */
export function OpcionCard({ opcion, seleccionada, puedeSeleccionar, onComparar, destacada = false }: OpcionCardProps) {
  const incluidas = opcion.coberturas.filter((c) => c.origen === 'incluida');
  const opcionales = opcion.coberturas.filter((c) => c.origen === 'opcional');

  return (
    <GlassCard
      as="article"
      tone="strong"
      padding="none"
      className={cn('overflow-hidden', destacada && 'ring-2 ring-ice-400/70')}
      aria-labelledby={`opcion-${opcion.posicion}`}
    >
      <div className="grid gap-6 p-6 sm:p-7 lg:grid-cols-[1fr_auto]">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={cn(
                'grid h-9 w-9 place-items-center rounded-full text-sm font-bold',
                destacada ? 'bg-gradient-to-br from-ice-500 to-ice-700 text-white' : 'bg-ice-100 text-ice-800',
              )}
            >
              {opcion.posicion}
            </span>
            <Chip tone="slate">{opcion.nivel}</Chip>
            {destacada && <Chip tone="ice">Mejor puntaje</Chip>}
            {opcion.es_menor_prima && <Chip tone="emerald">Menor prima</Chip>}
          </div>
          <h3 id={`opcion-${opcion.posicion}`} className="mt-3 text-xl font-semibold leading-tight sm:text-2xl">
            {opcion.plan}
          </h3>
          <p className="text-sm text-slate-500">{opcion.aseguradora}</p>

          <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-4">
            <Dato etiqueta="Prima mensual" valor={formatMXN(opcion.prima_total)} nota={opcion.costo_opcionales > 0 ? `${formatMXN(opcion.prima_base)} + ${formatMXN(opcion.costo_opcionales)} extras` : 'Sin extras'} fuerte />
            <Dato etiqueta="Deducible" valor={formatMXN(opcion.deducible)} />
            <Dato etiqueta="Coaseguro" valor={`${opcion.coaseguro_porcentaje}%`} />
            <Dato etiqueta="Suma asegurada" valor={formatMillones(opcion.suma_asegurada)} />
          </dl>

          <div className="mt-5 flex flex-wrap gap-1.5">
            {incluidas.map((c) => (
              <Chip key={c.codigo} tone="slate">
                <Check aria-hidden="true" size={12} />
                {c.nombre}
              </Chip>
            ))}
            {opcionales.map((c) => (
              <Chip key={c.codigo} tone="ice">
                <Plus aria-hidden="true" size={12} />
                {c.nombre} · {formatMXN(c.costo_extra)}
              </Chip>
            ))}
            {opcion.coberturas_deseadas_faltantes.map((n) => (
              <Chip key={n} tone="amber">
                <Minus aria-hidden="true" size={12} />
                Sin {n}
              </Chip>
            ))}
          </div>
        </div>

        <div className="flex flex-row items-center justify-between gap-4 border-t border-ice-100 pt-5 lg:w-56 lg:flex-col lg:items-stretch lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Puntaje</p>
            <p className="text-4xl font-semibold tabular-nums tracking-tight text-slate-900">
              {opcion.puntaje.toFixed(1)}
              <span className="text-base font-medium text-slate-400"> /100</span>
            </p>
            <ProgressBar value={opcion.puntaje / 100} label={`Puntaje de ${opcion.plan}`} className="mt-2" />
          </div>
          <button
            type="button"
            onClick={onComparar}
            disabled={!seleccionada && !puedeSeleccionar}
            aria-pressed={seleccionada}
            className={cn(
              'inline-flex h-10 items-center justify-center gap-2 rounded-full px-4 text-sm font-semibold ring-1 transition disabled:cursor-not-allowed disabled:opacity-40',
              seleccionada ? 'bg-ice-700 text-white ring-ice-700' : 'bg-white/80 text-ice-800 ring-ice-200 hover:bg-white',
            )}
          >
            {seleccionada ? <Check aria-hidden="true" size={16} /> : <Plus aria-hidden="true" size={16} />}
            {seleccionada ? 'En comparación' : 'Comparar'}
          </button>
        </div>
      </div>

      <details className="group border-t border-ice-100/80 bg-white/40">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-6 py-4 text-sm font-semibold text-ice-800 hover:bg-white/50 sm:px-7 [&::-webkit-details-marker]:hidden">
          ¿Por qué este puntaje?
          <ChevronDown aria-hidden="true" size={18} className="transition-transform group-open:rotate-180" />
        </summary>
        <div className="grid gap-8 px-6 pb-7 sm:px-7 xl:grid-cols-[1.4fr_1fr]">
          <div>
            <h4 className="flex items-center gap-2 text-sm font-semibold">
              <CircleDollarSign aria-hidden="true" size={16} className="text-ice-700" />
              Desglose de la función objetivo
            </h4>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full min-w-[30rem] text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wider text-slate-500">
                    <th className="py-2 pr-3 font-semibold">Criterio</th>
                    <th className="py-2 pr-3 font-semibold">Valor</th>
                    <th className="py-2 pr-3 font-semibold">Normalizado</th>
                    <th className="py-2 pr-3 text-right font-semibold">Peso</th>
                    <th className="py-2 text-right font-semibold">Aporte</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ice-100">
                  {opcion.componentes.map((c) => (
                    <tr key={c.criterio}>
                      <td className="py-2.5 pr-3 font-medium text-slate-800">{c.etiqueta}</td>
                      <td className="py-2.5 pr-3 tabular-nums text-slate-600">{c.valor_texto}</td>
                      <td className="py-2.5 pr-3">
                        <div className="flex items-center gap-2">
                          <ProgressBar value={c.normalizado} label={`${c.etiqueta} normalizado`} className="w-20" />
                          <span className="tabular-nums text-slate-600">{c.normalizado.toFixed(2)}</span>
                        </div>
                      </td>
                      <td className="py-2.5 pr-3 text-right tabular-nums text-slate-600">{formatPct(c.peso)}</td>
                      <td className="py-2.5 text-right font-semibold tabular-nums text-slate-900">
                        {(c.contribucion * 100).toFixed(1)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan={4} className="pt-3 text-right text-xs text-slate-500">
                      Puntaje = Σ peso × normalizado
                    </td>
                    <td className="pt-3 text-right font-semibold tabular-nums text-ice-800">{opcion.puntaje.toFixed(1)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
          <div>
            <h4 className="flex items-center gap-2 text-sm font-semibold">
              <ShieldCheck aria-hidden="true" size={16} className="text-emerald-600" />
              Restricciones que cumple
            </h4>
            <ul className="mt-3 space-y-2">
              {opcion.restricciones_cumplidas.map((r) => (
                <li key={r} className="flex gap-2 text-sm text-slate-600">
                  <Check aria-hidden="true" size={16} className="mt-0.5 shrink-0 text-emerald-600" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </details>
    </GlassCard>
  );
}

function Dato({ etiqueta, valor, nota, fuerte }: { etiqueta: string; valor: string; nota?: string; fuerte?: boolean }) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-500">{etiqueta}</dt>
      <dd className={cn('tabular-nums text-slate-900', fuerte ? 'text-lg font-semibold' : 'font-semibold')}>{valor}</dd>
      {nota && <dd className="text-xs text-slate-500">{nota}</dd>}
    </div>
  );
}
