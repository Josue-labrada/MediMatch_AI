import { Link } from 'react-router-dom';
import {
  ArrowRight,
  BadgeDollarSign,
  Clock,
  FlaskConical,
  GitBranch,
  Layers,
  ListChecks,
  Scale,
  Scissors,
  SlidersHorizontal,
  Trophy,
} from 'lucide-react';
import { DescartesPanel } from '../components/resultados/DescartesPanel';
import { OpcionCard } from '../components/resultados/OpcionCard';
import { Chip } from '../components/ui/Chip';
import { GlassButton } from '../components/ui/GlassButton';
import { GlassCard } from '../components/ui/GlassCard';
import { SectionHeader } from '../components/ui/SectionHeader';
import { StatTile } from '../components/ui/StatTile';
import { StateMessage } from '../components/ui/StateMessage';
import { MAX_COMPARAR, useBusqueda } from '../context/BusquedaContext';
import { ETIQUETA_ALGORITMO, formatMXN, formatNumero } from '../lib/format';
import type { RecomendacionResponse } from '../types/api';

export function ResultadosPage() {
  const { resultado, comparar, alternarComparar } = useBusqueda();

  if (!resultado) {
    return (
      <div className="mx-auto max-w-3xl py-20">
        <StateMessage
          variant="empty"
          title="Aún no hay resultados"
          action={
            <GlassButton to="/buscar" icon={ArrowRight}>
              Ir al formulario
            </GlassButton>
          }
        >
          Define tus restricciones y prioridades para que el CSP busque configuraciones válidas.
        </StateMessage>
      </div>
    );
  }

  const r = resultado;
  const s = r.estadisticas;

  return (
    <div className="mx-auto max-w-[1680px] py-12 sm:py-16">
      <div className="flex flex-wrap items-end justify-between gap-6">
        <SectionHeader
          level="h1"
          align="left"
          eyebrow="Resultados"
          eyebrowIcon={ListChecks}
          title={
            r.candidatos_validos > 0 ? (
              <>
                {formatNumero(r.candidatos_validos)} configuraciones <span className="text-gradient">cumplen</span>
              </>
            ) : (
              'Ninguna configuración cumple'
            )
          }
          description={r.algoritmo_utilizado}
        />
        <GlassButton to="/buscar" variant="secondary" icon={SlidersHorizontal} iconPosition="left">
          Ajustar búsqueda
        </GlassButton>
      </div>

      <p className="mt-6 flex items-start gap-2 rounded-2xl bg-amber-50/80 px-4 py-3 text-sm text-amber-900 ring-1 ring-amber-200">
        <FlaskConical aria-hidden="true" size={17} className="mt-0.5 shrink-0" />
        {r.aviso}
      </p>

      <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <StatTile icon={Layers} label="Planes evaluados" value={formatNumero(r.planes_evaluados)} hint="Dominio de la variable P" />
        <StatTile icon={ListChecks} label="Válidas" value={formatNumero(r.candidatos_validos)} hint="Soluciones del CSP" />
        <StatTile icon={GitBranch} label="Nodos" value={formatNumero(s.nodos_explorados)} hint={`de ${formatNumero(s.espacio_busqueda)} combinaciones posibles`} />
        <StatTile icon={Scissors} label="Podas" value={formatNumero(s.total_podas)} hint="Valores descartados" />
        <StatTile icon={Clock} label="Tiempo" value={`${s.tiempo_ms.toFixed(1)} ms`} hint={ETIQUETA_ALGORITMO[s.algoritmo]} />
        <StatTile icon={Scale} label="Descartados" value={formatNumero(r.descartes.length)} hint="Planes sin solución" />
      </div>

      {r.candidatos_validos === 0 ? (
        <div className="mt-8 grid gap-6">
          <StateMessage
            variant="empty"
            title="Tus restricciones no son compatibles con ningún plan del catálogo"
            action={
              <GlassButton to="/buscar" icon={SlidersHorizontal} iconPosition="left">
                Relajar restricciones
              </GlassButton>
            }
          >
            El CSP exploró {formatNumero(s.nodos_explorados)} nodos y ninguno llegó a una asignación completa y consistente.
            Revisa abajo qué restricción descartó cada plan.
          </StateMessage>
          <DescartesPanel descartes={r.descartes} abierto />
        </div>
      ) : (
        <>
          <ComparacionBaseline resultado={r} />

          <section aria-labelledby="ranking-titulo" className="mt-10">
            <div className="mb-5 flex flex-wrap items-baseline justify-between gap-3">
              <h2 id="ranking-titulo" className="text-2xl font-semibold">
                Ranking por función objetivo
              </h2>
              <p className="text-sm text-slate-500">
                Mostrando {r.ranking.length} de {formatNumero(r.candidatos_validos)} · Pesos:{' '}
                {Object.entries(r.pesos_aplicados)
                  .map(([k, v]) => `${k.replace('_', ' ')} ${Math.round((v ?? 0) * 100)}%`)
                  .join(' · ')}
              </p>
            </div>
            <div className="grid gap-5">
              {r.ranking.map((o) => (
                <OpcionCard
                  key={o.id}
                  opcion={o}
                  destacada={o.posicion === 1}
                  seleccionada={comparar.includes(o.id)}
                  puedeSeleccionar={comparar.length < MAX_COMPARAR}
                  onComparar={() => alternarComparar(o.id)}
                />
              ))}
            </div>
          </section>

          <div className="mt-10">
            <DescartesPanel descartes={r.descartes} />
          </div>
        </>
      )}

      {comparar.length > 0 && (
        <div className="pointer-events-none sticky bottom-4 z-40 mt-10 flex justify-center">
          <GlassCard tone="strong" padding="sm" className="pointer-events-auto flex items-center gap-4 rounded-full !py-2 !pl-5 !pr-2">
            <span className="text-sm font-medium text-slate-700">
              {comparar.length} de {MAX_COMPARAR} para comparar
            </span>
            <GlassButton to="/comparar" size="sm" icon={ArrowRight}>
              Comparar
            </GlassButton>
          </GlassCard>
        </div>
      )}
    </div>
  );
}

function ComparacionBaseline({ resultado }: { resultado: RecomendacionResponse }) {
  const mejor = resultado.ranking[0];
  const base = resultado.menor_prima;
  const comp = resultado.comparacion_baseline;
  if (!mejor || !base || !comp) return null;

  return (
    <GlassCard tone="tint" padding="md" className="mt-8 sm:p-8">
      <h2 className="text-lg font-semibold">Multicriterio vs. menor prima</h2>
      <p className="mt-1 text-sm text-slate-600">
        {comp.misma_opcion
          ? 'La opción más barata también es la mejor según tus prioridades: aquí los dos criterios coinciden.'
          : `Con tus pesos, la mejor opción cuesta ${formatMXN(comp.diferencia_prima)} más al mes que la más barata, y obtiene ${comp.diferencia_puntaje.toFixed(1)} puntos más. La más barata queda en el lugar #${comp.posicion_menor_prima}.`}
      </p>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <MiniOpcion icon={Trophy} titulo="Mejor puntaje" plan={mejor.plan} aseguradora={mejor.aseguradora} prima={mejor.prima_total} puntaje={mejor.puntaje} />
        <MiniOpcion icon={BadgeDollarSign} titulo="Menor prima (línea base)" plan={base.plan} aseguradora={base.aseguradora} prima={base.prima_total} puntaje={base.puntaje} />
      </div>
      <p className="mt-4 text-xs text-slate-500">
        La línea base usa un solo criterio (prima). Ver <Link to="/algoritmos" className="font-semibold text-ice-700 underline-offset-2 hover:underline">cómo funciona la función objetivo</Link>.
      </p>
    </GlassCard>
  );
}

function MiniOpcion({
  icon: Icon,
  titulo,
  plan,
  aseguradora,
  prima,
  puntaje,
}: {
  icon: typeof Trophy;
  titulo: string;
  plan: string;
  aseguradora: string;
  prima: number;
  puntaje: number;
}) {
  return (
    <div className="flex items-center gap-4 rounded-2xl bg-white/70 p-4 ring-1 ring-inset ring-white">
      <span className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-ice-100 text-ice-700">
        <Icon aria-hidden="true" size={20} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{titulo}</p>
        <p className="truncate font-semibold text-slate-900">{plan}</p>
        <p className="truncate text-xs text-slate-500">{aseguradora}</p>
      </div>
      <div className="text-right">
        <p className="font-semibold tabular-nums text-slate-900">{formatMXN(prima)}</p>
        <Chip tone="ice">{puntaje.toFixed(1)} pts</Chip>
      </div>
    </div>
  );
}
