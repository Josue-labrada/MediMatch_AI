import { useMemo, useState, type FormEvent, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Cpu,
  Loader2,
  Lock,
  RotateCcw,
  Scale,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  type LucideIcon,
} from 'lucide-react';
import { SegmentedControl } from '../components/form/SegmentedControl';
import { GlassButton } from '../components/ui/GlassButton';
import { GlassCard } from '../components/ui/GlassCard';
import { SectionHeader } from '../components/ui/SectionHeader';
import { StateMessage } from '../components/ui/StateMessage';
import { useBusqueda } from '../context/BusquedaContext';
import { useApi } from '../hooks/useApi';
import { formatMXN, formatMillones } from '../lib/format';
import { api } from '../services/api';
import type { Algoritmo, Criterio, Importancia, Opciones, Pesos, PreferenciasRequest } from '../types/api';

const CRITERIOS: Array<{ clave: Criterio; etiqueta: string; ayuda: string }> = [
  { clave: 'costo', etiqueta: 'Costo mensual', ayuda: 'Pagar menos prima' },
  { clave: 'deducible', etiqueta: 'Deducible bajo', ayuda: 'Pagar menos antes de que el seguro responda' },
  { clave: 'coaseguro', etiqueta: 'Coaseguro bajo', ayuda: 'Menor porcentaje que pagas tú de cada siniestro' },
  { clave: 'suma_asegurada', etiqueta: 'Suma asegurada alta', ayuda: 'Mayor tope de cobertura' },
  { clave: 'coberturas', etiqueta: 'Coberturas deseadas', ayuda: 'Incluir las coberturas que marcaste como deseadas' },
];

const PRESETS: Array<{ nombre: string; icon: LucideIcon; pesos: Pesos }> = [
  { nombre: 'Equilibrado', icon: Scale, pesos: { costo: 35, deducible: 20, coaseguro: 10, suma_asegurada: 15, coberturas: 20 } },
  { nombre: 'Ahorro', icon: Sparkles, pesos: { costo: 70, deducible: 10, coaseguro: 5, suma_asegurada: 5, coberturas: 10 } },
  { nombre: 'Protección', icon: ShieldCheck, pesos: { costo: 10, deducible: 20, coaseguro: 15, suma_asegurada: 25, coberturas: 30 } },
];

interface FormState {
  presupuesto: number;
  deducibleMaximo: number;
  coaseguroMaximo: number | null;
  sumaMinima: number | null;
  coberturas: Record<string, Importancia>;
  pesos: Pesos;
  algoritmo: Algoritmo;
}

function estadoInicial(opciones: Opciones, previas: PreferenciasRequest | null): FormState {
  if (previas) {
    const coberturas: Record<string, Importancia> = {};
    previas.coberturas_obligatorias.forEach((c) => (coberturas[c] = 'obligatoria'));
    previas.coberturas_deseadas.forEach((c) => (coberturas[c] = 'deseada'));
    return {
      presupuesto: previas.presupuesto_mensual,
      deducibleMaximo: previas.deducible_maximo,
      coaseguroMaximo: previas.coaseguro_maximo,
      sumaMinima: previas.suma_asegurada_minima,
      coberturas,
      pesos: previas.pesos,
      algoritmo: previas.algoritmo,
    };
  }
  const medio = opciones.deducibles[Math.floor(opciones.deducibles.length / 2)] ?? 0;
  return {
    presupuesto: 3000,
    deducibleMaximo: medio,
    coaseguroMaximo: null,
    sumaMinima: null,
    coberturas: { hospitalizacion: 'obligatoria' },
    pesos: PRESETS[0].pesos,
    algoritmo: 'backtracking_fc',
  };
}

export function BuscarPage() {
  const { data: opciones, error, loading, reload } = useApi(api.opciones);

  return (
    <div className="mx-auto max-w-[1680px] py-12 sm:py-16">
      <SectionHeader
        level="h1"
        align="left"
        eyebrow="Formulario inteligente"
        eyebrowIcon={SlidersHorizontal}
        title="Define qué necesitas"
        description="Las restricciones son innegociables: el CSP descarta cualquier configuración que no las cumpla. Las prioridades solo cambian el orden de las opciones válidas."
      />
      <div className="mt-10">
        {loading && <StateMessage variant="loading" title="Cargando opciones del catálogo…" />}
        {error && (
          <StateMessage
            variant="error"
            title="No se pudo cargar el catálogo"
            action={
              <GlassButton variant="secondary" icon={RotateCcw} iconPosition="left" onClick={reload}>
                Reintentar
              </GlassButton>
            }
          >
            {error}
          </StateMessage>
        )}
        {opciones && opciones.planes_activos === 0 && (
          <StateMessage
            variant="empty"
            title="El catálogo está vacío"
            action={<GlassButton to="/admin">Ir al panel administrativo</GlassButton>}
          >
            Sincroniza la API mock desde el panel administrativo para cargar los planes simulados.
          </StateMessage>
        )}
        {opciones && opciones.planes_activos > 0 && <Formulario opciones={opciones} />}
      </div>
    </div>
  );
}

function Formulario({ opciones }: { opciones: Opciones }) {
  const navigate = useNavigate();
  const { preferencias, guardarResultado } = useBusqueda();
  const [form, setForm] = useState<FormState>(() => estadoInicial(opciones, preferencias));
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof FormState>(clave: K, valor: FormState[K]) => setForm((f) => ({ ...f, [clave]: valor }));

  const obligatorias = Object.entries(form.coberturas).filter(([, v]) => v === 'obligatoria').map(([c]) => c);
  const deseadas = Object.entries(form.coberturas).filter(([, v]) => v === 'deseada').map(([c]) => c);
  const totalPesos = CRITERIOS.reduce(
    (acc, c) => acc + (c.clave === 'coberturas' && deseadas.length === 0 ? 0 : form.pesos[c.clave]),
    0,
  );
  const nombre = useMemo(() => Object.fromEntries(opciones.coberturas.map((c) => [c.codigo, c.nombre])), [opciones]);
  const maxPresupuesto = Math.ceil(((opciones.prima_maxima ?? 10_000) + 2_000) / 1000) * 1000;

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    const solicitud: PreferenciasRequest = {
      presupuesto_mensual: form.presupuesto,
      deducible_maximo: form.deducibleMaximo,
      coaseguro_maximo: form.coaseguroMaximo,
      suma_asegurada_minima: form.sumaMinima,
      coberturas_obligatorias: obligatorias,
      coberturas_deseadas: deseadas,
      pesos: form.pesos,
      algoritmo: form.algoritmo,
    };
    setEnviando(true);
    setError(null);
    try {
      const resultado = await api.recomendar(solicitud);
      guardarResultado(solicitud, resultado);
      navigate('/resultados');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} className="grid items-start gap-6 xl:grid-cols-[1fr_22rem] 2xl:grid-cols-[1fr_24rem]">
      <div className="grid gap-6">
        {/* ---------------------------------------------------- restricciones */}
        <Bloque
          icon={Lock}
          titulo="Restricciones duras"
          subtitulo="Variables y dominios del CSP: si una configuración no cumple, se descarta."
        >
          <div className="grid gap-8 lg:grid-cols-2">
            <div>
              <label htmlFor="presupuesto" className="mb-2.5 flex items-baseline justify-between text-sm font-semibold text-slate-900">
                Presupuesto mensual máximo
                <span className="text-xl font-semibold tabular-nums text-ice-700">{formatMXN(form.presupuesto)}</span>
              </label>
              <input
                id="presupuesto"
                type="range"
                min={500}
                max={maxPresupuesto}
                step={100}
                value={form.presupuesto}
                onChange={(e) => set('presupuesto', Number(e.target.value))}
                className="w-full accent-ice-600"
              />
              <div className="mt-1 flex justify-between text-xs text-slate-500">
                <span>{formatMXN(500)}</span>
                <span>
                  Primas del catálogo: {formatMXN(opciones.prima_minima ?? 0)} – {formatMXN(opciones.prima_maxima ?? 0)}
                </span>
                <span>{formatMXN(maxPresupuesto)}</span>
              </div>
            </div>

            <SegmentedControl
              name="deducible"
              legend="Deducible máximo que aceptas"
              options={opciones.deducibles.map((d) => ({ value: d, label: formatMXN(d) }))}
              value={form.deducibleMaximo}
              onChange={(v) => set('deducibleMaximo', v)}
            />

            <SegmentedControl
              name="coaseguro"
              legend="Coaseguro máximo"
              options={[
                { value: -1, label: 'Sin límite' },
                ...opciones.coaseguros.map((c) => ({ value: c, label: `${c}%` })),
              ]}
              value={form.coaseguroMaximo ?? -1}
              onChange={(v) => set('coaseguroMaximo', v === -1 ? null : v)}
            />

            <div>
              <label htmlFor="suma" className="mb-2.5 block text-sm font-semibold text-slate-900">
                Suma asegurada mínima
              </label>
              <select
                id="suma"
                value={form.sumaMinima ?? ''}
                onChange={(e) => set('sumaMinima', e.target.value === '' ? null : Number(e.target.value))}
                className="h-11 w-full rounded-2xl border-0 bg-white/80 px-4 text-sm font-medium text-slate-800 ring-1 ring-inset ring-ice-200 focus:ring-2 focus:ring-ice-600"
              >
                <option value="">Sin mínimo</option>
                {opciones.sumas_aseguradas.map((s) => (
                  <option key={s} value={s}>
                    Al menos {formatMillones(s)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </Bloque>

        {/* ---------------------------------------------------- coberturas */}
        <Bloque
          icon={ShieldCheck}
          titulo="Coberturas"
          subtitulo="Obligatoria = restricción dura del CSP. Deseada = suma puntos en el ranking. No importa = se ignora."
        >
          <ul className="grid gap-3 lg:grid-cols-2">
            {opciones.coberturas.map((c) => (
              <li
                key={c.codigo}
                className="flex flex-col gap-3 rounded-2xl bg-white/60 p-4 ring-1 ring-inset ring-white/80 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0">
                  <p className="font-medium text-slate-900">{c.nombre}</p>
                  {c.descripcion && <p className="text-xs leading-snug text-slate-500">{c.descripcion}</p>}
                </div>
                <SegmentedControl
                  name={`cob-${c.codigo}`}
                  legend={`Importancia de ${c.nombre}`}
                  hideLegend
                  size="sm"
                  className="shrink-0"
                  options={[
                    { value: 'ninguna', label: 'No importa' },
                    { value: 'deseada', label: 'Deseada' },
                    { value: 'obligatoria', label: 'Obligatoria' },
                  ]}
                  value={form.coberturas[c.codigo] ?? 'ninguna'}
                  onChange={(v) => set('coberturas', { ...form.coberturas, [c.codigo]: v as Importancia })}
                />
              </li>
            ))}
          </ul>
        </Bloque>

        {/* ---------------------------------------------------- pesos */}
        <Bloque
          icon={Scale}
          titulo="Prioridades"
          subtitulo="Pesos de la función objetivo. Se normalizan para sumar 100%."
          accion={
            <div className="flex flex-wrap gap-2">
              {PRESETS.map((p) => (
                <button
                  key={p.nombre}
                  type="button"
                  onClick={() => set('pesos', p.pesos)}
                  className="inline-flex items-center gap-1.5 rounded-full bg-white/80 px-3 py-1.5 text-xs font-semibold text-ice-800 ring-1 ring-ice-200 transition hover:bg-white"
                >
                  <p.icon aria-hidden="true" size={13} />
                  {p.nombre}
                </button>
              ))}
            </div>
          }
        >
          <div className="grid gap-x-10 gap-y-6 lg:grid-cols-2">
            {CRITERIOS.map((c) => {
              const inactivo = c.clave === 'coberturas' && deseadas.length === 0;
              const pct = !inactivo && totalPesos > 0 ? (form.pesos[c.clave] / totalPesos) * 100 : 0;
              return (
                <div key={c.clave} className={inactivo ? 'opacity-50' : undefined}>
                  <label htmlFor={`peso-${c.clave}`} className="flex items-baseline justify-between gap-3 text-sm">
                    <span className="font-semibold text-slate-900">{c.etiqueta}</span>
                    <span className="tabular-nums font-semibold text-ice-700">{pct.toFixed(0)}%</span>
                  </label>
                  <p className="mb-2 text-xs text-slate-500">
                    {inactivo ? 'No aplica: no marcaste coberturas deseadas (su peso se reparte).' : c.ayuda}
                  </p>
                  <input
                    id={`peso-${c.clave}`}
                    type="range"
                    min={0}
                    max={100}
                    step={5}
                    value={form.pesos[c.clave]}
                    disabled={inactivo}
                    onChange={(e) => set('pesos', { ...form.pesos, [c.clave]: Number(e.target.value) })}
                    className="w-full accent-ice-600"
                  />
                </div>
              );
            })}
          </div>
        </Bloque>

        <Bloque icon={Cpu} titulo="Algoritmo de búsqueda" subtitulo="Ambos encuentran las mismas soluciones; cambia cuántos nodos exploran.">
          <SegmentedControl
            name="algoritmo"
            legend="Algoritmo CSP"
            hideLegend
            options={[
              { value: 'backtracking_fc', label: 'Backtracking + forward checking' },
              { value: 'backtracking', label: 'Backtracking simple' },
            ]}
            value={form.algoritmo}
            onChange={(v) => set('algoritmo', v)}
          />
        </Bloque>
      </div>

      {/* ---------------------------------------------------- resumen */}
      <aside className="xl:sticky xl:top-28">
        <GlassCard tone="strong" padding="md" className="rounded-[1.75rem]">
          <h2 className="text-lg font-semibold">Resumen</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <Fila etiqueta="Presupuesto" valor={formatMXN(form.presupuesto)} />
            <Fila etiqueta="Deducible máx." valor={formatMXN(form.deducibleMaximo)} />
            <Fila etiqueta="Coaseguro máx." valor={form.coaseguroMaximo === null ? 'Sin límite' : `${form.coaseguroMaximo}%`} />
            <Fila etiqueta="Suma mínima" valor={form.sumaMinima === null ? 'Sin mínimo' : formatMillones(form.sumaMinima)} />
            <Fila etiqueta="Obligatorias" valor={obligatorias.length ? obligatorias.map((c) => nombre[c]).join(', ') : '—'} />
            <Fila etiqueta="Deseadas" valor={deseadas.length ? deseadas.map((c) => nombre[c]).join(', ') : '—'} />
          </dl>
          {error && (
            <p role="alert" className="mt-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-700 ring-1 ring-rose-200">
              {error}
            </p>
          )}
          <GlassButton type="submit" size="lg" className="mt-6 w-full" icon={enviando ? Loader2 : ArrowRight} disabled={enviando}>
            {enviando ? 'Calculando…' : 'Buscar configuraciones'}
          </GlassButton>
          <p className="mt-4 flex gap-2 text-xs leading-relaxed text-slate-500">
            <Lock aria-hidden="true" size={14} className="mt-0.5 shrink-0" />
            No pedimos nombre, edad ni datos de salud. Catálogo de {opciones.planes_activos} planes simulados.
          </p>
        </GlassCard>
      </aside>
    </form>
  );
}

function Bloque({
  icon: Icon,
  titulo,
  subtitulo,
  accion,
  children,
}: {
  icon: LucideIcon;
  titulo: string;
  subtitulo: string;
  accion?: ReactNode;
  children: ReactNode;
}) {
  return (
    <GlassCard tone="strong" padding="md" className="sm:p-8">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-ice-100 to-white text-ice-700 ring-1 ring-ice-200/70">
            <Icon aria-hidden="true" size={19} />
          </span>
          <div>
            <h2 className="text-lg font-semibold leading-tight">{titulo}</h2>
            <p className="mt-0.5 text-sm text-slate-500">{subtitulo}</p>
          </div>
        </div>
        {accion}
      </div>
      {children}
    </GlassCard>
  );
}

function Fila({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="shrink-0 text-slate-500">{etiqueta}</dt>
      <dd className="text-right font-medium text-slate-900">{valor}</dd>
    </div>
  );
}
