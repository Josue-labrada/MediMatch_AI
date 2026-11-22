import { useState } from 'react';
import { CheckCircle2, ChevronDown, Database, Loader2, RefreshCw, Server, Settings2, XCircle } from 'lucide-react';
import { Chip } from '../components/ui/Chip';
import { GlassButton } from '../components/ui/GlassButton';
import { GlassCard } from '../components/ui/GlassCard';
import { SectionHeader } from '../components/ui/SectionHeader';
import { StatTile } from '../components/ui/StatTile';
import { StateMessage } from '../components/ui/StateMessage';
import { useApi } from '../hooks/useApi';
import { cn } from '../lib/cn';
import { formatFecha, formatMXN, formatMillones, formatNumero } from '../lib/format';
import { api } from '../services/api';
import type { EstadoServicio, Sincronizacion } from '../types/api';

export function AdminPage() {
  const estado = useApi(api.estado);
  const historial = useApi(api.historialSync);
  const planes = useApi(api.planes);
  const [novedades, setNovedades] = useState(false);
  const [sincronizando, setSincronizando] = useState(false);
  const [ultimo, setUltimo] = useState<Sincronizacion | null>(null);
  const [errorSync, setErrorSync] = useState<string | null>(null);

  async function sincronizar() {
    setSincronizando(true);
    setErrorSync(null);
    try {
      setUltimo(await api.sincronizar(novedades));
    } catch (e) {
      setErrorSync((e as Error).message);
    } finally {
      setSincronizando(false);
      estado.reload();
      historial.reload();
      planes.reload();
    }
  }

  const cat = estado.data?.catalogo ?? {};

  return (
    <div className="mx-auto max-w-[1680px] py-12 sm:py-16">
      <SectionHeader
        level="h1"
        align="left"
        eyebrow="Administración"
        eyebrowIcon={Settings2}
        title="Panel administrativo"
        description="Estado de los servicios y sincronización del catálogo simulado desde la Mock Insurance API hacia PostgreSQL."
      />

      {/* Servicios */}
      <section aria-labelledby="servicios" className="mt-10">
        <h2 id="servicios" className="sr-only">Servicios</h2>
        {estado.error && <StateMessage variant="error" title="El backend no responde">{estado.error}</StateMessage>}
        {estado.data && (
          <div className="grid gap-4 md:grid-cols-3">
            <Servicio nombre="Backend FastAPI" puerto=":8000" icon={Server} estado={estado.data.backend} />
            <Servicio nombre="PostgreSQL" puerto=":5433" icon={Database} estado={estado.data.base_datos} />
            <Servicio nombre="Mock Insurance API" puerto=":8001" icon={Server} estado={estado.data.mock_api} />
          </div>
        )}
        {estado.data && (
          <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
            <StatTile label="Aseguradoras" value={formatNumero(cat.aseguradoras ?? 0)} hint="Todas simuladas" />
            <StatTile label="Planes activos" value={formatNumero(cat.planes_activos ?? 0)} />
            <StatTile label="Planes inactivos" value={formatNumero(cat.planes_inactivos ?? 0)} hint="Ya no vienen en la API" />
            <StatTile label="Variantes" value={formatNumero(cat.variantes ?? 0)} hint="Opciones de deducible" />
            <StatTile label="Coberturas" value={formatNumero(cat.coberturas ?? 0)} />
            <StatTile label="Consultas" value={formatNumero(cat.consultas ?? 0)} hint="Sin datos personales" />
          </div>
        )}
      </section>

      {/* Sincronización */}
      <section aria-labelledby="sync" className="mt-8 grid gap-6 xl:grid-cols-[26rem_1fr]">
        <GlassCard tone="strong" padding="lg">
          <h2 id="sync" className="text-xl font-semibold">Sincronizar catálogo</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            Pide el catálogo a la API mock por HTTP, lo valida y hace «upsert» en PostgreSQL. Repetirlo no duplica registros;
            los planes que desaparecen se marcan como inactivos.
          </p>
          <label className="mt-5 flex cursor-pointer items-start gap-3 rounded-2xl bg-white/60 p-4 ring-1 ring-inset ring-white/80">
            <input
              type="checkbox"
              checked={novedades}
              onChange={(e) => setNovedades(e.target.checked)}
              className="mt-0.5 h-4 w-4 accent-ice-600"
            />
            <span>
              <span className="block text-sm font-semibold text-slate-900">Incluir productos nuevos</span>
              <span className="block text-xs leading-snug text-slate-500">
                Escenario D: agrega «Faro Materna» y observa cómo cambian las recomendaciones sin tocar el algoritmo.
              </span>
            </span>
          </label>
          <GlassButton
            className="mt-5 w-full"
            size="lg"
            icon={sincronizando ? Loader2 : RefreshCw}
            iconPosition="left"
            onClick={sincronizar}
            disabled={sincronizando}
          >
            {sincronizando ? 'Sincronizando…' : 'Sincronizar ahora'}
          </GlassButton>
          {ultimo && (
            <p role="status" className="mt-4 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800 ring-1 ring-emerald-200">
              Listo: {ultimo.creados} creados · {ultimo.actualizados} actualizados · {ultimo.sin_cambios} sin cambios ·{' '}
              {ultimo.desactivados} desactivados.
            </p>
          )}
          {errorSync && (
            <p role="alert" className="mt-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-700 ring-1 ring-rose-200">
              {errorSync}
            </p>
          )}
        </GlassCard>

        <GlassCard tone="strong" padding="none" className="overflow-hidden">
          <h2 className="px-6 pt-6 text-xl font-semibold sm:px-8">Historial de sincronizaciones</h2>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[40rem] text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wider text-slate-500">
                  <th className="px-6 py-2 font-semibold sm:pl-8">Fecha</th>
                  <th className="px-3 py-2 font-semibold">Resultado</th>
                  <th className="px-3 py-2 text-right font-semibold">Creados</th>
                  <th className="px-3 py-2 text-right font-semibold">Actualizados</th>
                  <th className="px-3 py-2 text-right font-semibold">Sin cambios</th>
                  <th className="px-6 py-2 text-right font-semibold sm:pr-8">Desactivados</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ice-100">
                {(historial.data ?? []).map((h) => (
                  <tr key={h.id} title={h.mensaje ?? undefined}>
                    <td className="px-6 py-3 text-slate-700 sm:pl-8">{formatFecha(h.fecha)}</td>
                    <td className="px-3 py-3">
                      <Chip tone={h.resultado === 'ok' ? 'emerald' : 'rose'}>{h.resultado === 'ok' ? 'Correcta' : 'Error'}</Chip>
                    </td>
                    <td className="px-3 py-3 text-right tabular-nums">{h.creados}</td>
                    <td className="px-3 py-3 text-right tabular-nums">{h.actualizados}</td>
                    <td className="px-3 py-3 text-right tabular-nums">{h.sin_cambios}</td>
                    <td className="px-6 py-3 text-right tabular-nums sm:pr-8">{h.desactivados}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {historial.data?.length === 0 && <p className="px-8 pb-6 text-sm text-slate-500">Sin sincronizaciones todavía.</p>}
          </div>
        </GlassCard>
      </section>

      {/* Catálogo */}
      <section aria-labelledby="catalogo" className="mt-8">
        <div className="mb-4 flex flex-wrap items-baseline justify-between gap-3">
          <h2 id="catalogo" className="text-2xl font-semibold">Catálogo en PostgreSQL</h2>
          <Chip tone="amber">Datos simulados</Chip>
        </div>
        {planes.loading && <StateMessage variant="loading" title="Cargando catálogo…" />}
        <div className="grid gap-3">
          {(planes.data ?? []).map((p) => (
            <GlassCard key={p.id} tone="strong" padding="none" className={cn(!p.activo && 'opacity-60')}>
              <details className="group">
                <summary className="grid cursor-pointer list-none grid-cols-2 items-center gap-4 p-5 sm:grid-cols-[1.5fr_1fr_1fr_1fr_auto] sm:px-7 [&::-webkit-details-marker]:hidden">
                  <span className="col-span-2 sm:col-span-1">
                    <span className="block font-semibold text-slate-900">
                      {p.nombre} {!p.activo && <Chip tone="slate">Inactivo</Chip>}
                    </span>
                    <span className="block text-xs text-slate-500">
                      {p.aseguradora} · {p.external_id}
                    </span>
                  </span>
                  <span className="text-sm text-slate-600">{p.nivel}</span>
                  <span className="text-sm tabular-nums text-slate-600">{formatMillones(p.suma_asegurada)}</span>
                  <span className="text-sm tabular-nums text-slate-600">
                    {formatMXN(Math.min(...p.variantes.map((v) => v.prima_mensual)))} – {formatMXN(Math.max(...p.variantes.map((v) => v.prima_mensual)))}
                  </span>
                  <ChevronDown aria-hidden="true" size={18} className="hidden text-ice-700 transition-transform group-open:rotate-180 sm:block" />
                </summary>
                <div className="grid gap-6 border-t border-ice-100 px-5 py-5 sm:px-7 lg:grid-cols-3">
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Variantes (dominio de D)</h3>
                    <ul className="mt-2 space-y-1 text-sm tabular-nums text-slate-700">
                      {p.variantes.map((v) => (
                        <li key={v.deducible}>
                          Deducible {formatMXN(v.deducible)} · coaseguro {v.coaseguro_porcentaje}% · {formatMXN(v.prima_mensual)}/mes
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Coberturas</h3>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {p.coberturas.map((c) => (
                        <Chip key={c.codigo} tone={c.tipo === 'incluida' ? 'slate' : 'ice'}>
                          {c.nombre}
                          {c.tipo === 'opcional' && ` · +${formatMXN(c.costo_extra)}`}
                        </Chip>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Reglas de compatibilidad</h3>
                    {p.reglas.length === 0 ? (
                      <p className="mt-2 text-sm text-slate-500">Sin reglas.</p>
                    ) : (
                      <ul className="mt-2 space-y-1 text-sm text-slate-700">
                        {p.reglas.map((r) => (
                          <li key={r.descripcion}>{r.descripcion}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </details>
            </GlassCard>
          ))}
        </div>
      </section>
    </div>
  );
}

function Servicio({ nombre, puerto, icon: Icon, estado }: { nombre: string; puerto: string; icon: typeof Server; estado: EstadoServicio }) {
  return (
    <GlassCard tone="strong" padding="md" className="flex items-start gap-4">
      <span className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-ice-100 text-ice-700">
        <Icon aria-hidden="true" size={20} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="flex items-center gap-2 font-semibold text-slate-900">
          {nombre} <span className="text-xs font-normal text-slate-400">{puerto}</span>
        </p>
        <p className="truncate text-xs text-slate-500" title={estado.detalle}>
          {estado.detalle}
        </p>
      </div>
      {estado.ok ? (
        <CheckCircle2 aria-label="En línea" size={22} className="shrink-0 text-emerald-600" />
      ) : (
        <XCircle aria-label="Sin conexión" size={22} className="shrink-0 text-rose-600" />
      )}
    </GlassCard>
  );
}
