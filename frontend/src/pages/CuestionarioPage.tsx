import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, ClipboardList, Loader2, Lock, RotateCcw, Sigma, Users } from 'lucide-react';
import { SegmentedControl } from '../components/form/SegmentedControl';
import { OpcionCard } from '../components/resultados/OpcionCard';
import { Chip } from '../components/ui/Chip';
import { GlassButton } from '../components/ui/GlassButton';
import { GlassCard } from '../components/ui/GlassCard';
import { ProgressBar } from '../components/ui/ProgressBar';
import { SectionHeader } from '../components/ui/SectionHeader';
import { StateMessage } from '../components/ui/StateMessage';
import { useBusqueda } from '../context/BusquedaContext';
import { useApi } from '../hooks/useApi';
import { formatMXN, formatPct } from '../lib/format';
import { api } from '../services/api';
import type { CuestionarioResponse, Distribucion, NivelRiesgo, PreguntaCuestionario } from '../types/api';

const NIVELES: NivelRiesgo[] = ['bajo', 'medio', 'alto'];
const TONO: Record<NivelRiesgo, 'emerald' | 'ice' | 'slate'> = { bajo: 'emerald', medio: 'ice', alto: 'slate' };
const GRUPOS: Array<{ grupo: PreguntaCuestionario['grupo']; titulo: string; ayuda: string }> = [
  { grupo: 'prior', titulo: 'Punto de partida', ayuda: 'Tu edad fija la creencia inicial (prior).' },
  { grupo: 'evidencia', titulo: 'Tu historial', ayuda: 'Cada respuesta es evidencia que actualiza la probabilidad.' },
  { grupo: 'necesidad', titulo: 'Tus necesidades', ayuda: 'No cambian el riesgo: solo añaden coberturas deseadas.' },
];

export function CuestionarioPage() {
  const { data: preguntas, error, loading, reload } = useApi(api.preguntasCuestionario);

  return (
    <div className="mx-auto max-w-[1680px] py-12 sm:py-16">
      <SectionHeader
        level="h1"
        align="left"
        eyebrow="Regla de Bayes"
        eyebrowIcon={ClipboardList}
        title="Cuestionario de riesgo"
        description="Responde unas preguntas sencillas. Partimos de una probabilidad inicial según tu edad y la actualizamos con cada respuesta usando la regla de Bayes; con el resultado buscamos el seguro que mejor te protege."
      />
      <div className="mt-10">
        {loading && <StateMessage variant="loading" title="Cargando cuestionario…" />}
        {error && (
          <StateMessage
            variant="error"
            title="No se pudo cargar el cuestionario"
            action={
              <GlassButton variant="secondary" icon={RotateCcw} iconPosition="left" onClick={reload}>
                Reintentar
              </GlassButton>
            }
          >
            {error}
          </StateMessage>
        )}
        {preguntas && <Cuestionario preguntas={preguntas} />}
      </div>
    </div>
  );
}

function Cuestionario({ preguntas }: { preguntas: PreguntaCuestionario[] }) {
  const navigate = useNavigate();
  const { guardarResultado } = useBusqueda();
  const [respuestas, setRespuestas] = useState<Record<string, string>>(() =>
    Object.fromEntries(preguntas.map((p) => [p.id, p.opciones[0].valor])),
  );
  const [presupuesto, setPresupuesto] = useState(4000);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<CuestionarioResponse | null>(null);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      setResultado(await api.evaluarCuestionario({ ...respuestas, presupuesto_mensual: presupuesto }));
      setTimeout(() => document.getElementById('resultado-bayes')?.scrollIntoView({ behavior: 'smooth' }), 50);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  function verRankingCompleto() {
    if (!resultado) return;
    guardarResultado(resultado.preferencias_derivadas, resultado.recomendacion);
    navigate('/resultados');
  }

  return (
    <div className="grid gap-6">
      <form onSubmit={enviar} className="grid gap-6">
        {GRUPOS.map(({ grupo, titulo, ayuda }) => (
          <GlassCard key={grupo} tone="strong" padding="lg">
            <h2 className="text-lg font-semibold">{titulo}</h2>
            <p className="mb-6 text-sm text-slate-600">{ayuda}</p>
            <div className="grid gap-6 lg:grid-cols-2">
              {preguntas
                .filter((p) => p.grupo === grupo)
                .map((p) => (
                  <div key={p.id}>
                    <SegmentedControl
                      name={p.id}
                      legend={p.texto}
                      options={p.opciones.map((o) => ({ value: o.valor, label: o.etiqueta }))}
                      value={respuestas[p.id]}
                      onChange={(v) => setRespuestas((r) => ({ ...r, [p.id]: v }))}
                    />
                    <p className="mt-1.5 text-xs text-slate-500">{p.ayuda}</p>
                  </div>
                ))}
            </div>
          </GlassCard>
        ))}

        <GlassCard tone="strong" padding="lg">
          <h2 className="text-lg font-semibold">Tu presupuesto</h2>
          <label htmlFor="presupuesto-cuestionario" className="mt-4 mb-2.5 flex items-baseline justify-between text-sm font-semibold">
            Máximo mensual
            <span className="text-xl tabular-nums text-ice-700">{formatMXN(presupuesto)}</span>
          </label>
          <input
            id="presupuesto-cuestionario"
            type="range"
            min={500}
            max={12000}
            step={100}
            value={presupuesto}
            onChange={(e) => setPresupuesto(Number(e.target.value))}
            className="w-full accent-ice-600"
          />
        </GlassCard>

        <div className="flex flex-wrap items-center gap-4">
          <GlassButton type="submit" size="lg" icon={enviando ? Loader2 : Sigma} disabled={enviando}>
            {enviando ? 'Calculando…' : 'Calcular mi riesgo y recomendar'}
          </GlassButton>
          <p className="flex items-center gap-2 text-sm text-slate-600">
            <Lock aria-hidden="true" size={16} /> Tus respuestas no se guardan.
          </p>
        </div>
        {error && <StateMessage variant="error" title="No se pudo calcular">{error}</StateMessage>}
      </form>

      {resultado && <Resultado r={resultado} onVerRanking={verRankingCompleto} />}
    </div>
  );
}

function Barras({ titulo, dist }: { titulo: string; dist: Distribucion }) {
  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold text-slate-900">{titulo}</h3>
      <div className="grid gap-3">
        {NIVELES.map((n) => (
          <div key={n}>
            <div className="mb-1 flex justify-between text-sm">
              <span className="capitalize">{n}</span>
              <span className="font-semibold tabular-nums">{formatPct(dist[n], 1)}</span>
            </div>
            <ProgressBar value={dist[n]} label={`${titulo}: riesgo ${n}`} tone={TONO[n]} />
          </div>
        ))}
      </div>
    </div>
  );
}

function Resultado({ r, onVerRanking }: { r: CuestionarioResponse; onVerRanking: () => void }) {
  const a = r.analisis;
  const mejor = r.recomendacion.ranking[0];
  const f = a.frecuencias_naturales;

  return (
    <section id="resultado-bayes" aria-labelledby="titulo-bayes" className="grid gap-6">
      <GlassCard tone="tint" padding="lg">
        <p className="text-sm font-semibold text-ice-800">Resultado de la regla de Bayes</p>
        <h2 id="titulo-bayes" className="mt-1 text-3xl font-semibold tracking-tight">
          {a.nivel_etiqueta}
          <span className="ml-3 text-lg font-medium text-slate-600">
            ({formatPct(a.posterior[a.nivel_probable], 1)} de probabilidad)
          </span>
        </h2>
        <div className="mt-6 grid gap-8 lg:grid-cols-2">
          <Barras titulo="Antes de tus respuestas (solo edad)" dist={a.prior} />
          <Barras titulo="Después de tus respuestas (posterior)" dist={a.posterior} />
        </div>
        <p className="mt-6 flex items-start gap-2 text-sm text-slate-700">
          <Users aria-hidden="true" size={18} className="mt-0.5 shrink-0" />
          Probabilidad de una hospitalización mayor en 12 meses: <strong>{formatPct(a.prob_hospitalizacion, 1)}</strong>.
          De cada {f.poblacion} personas con tu perfil, unas <strong>{Math.round(f.hospitalizadas)}</strong> se hospitalizarían.
        </p>
      </GlassCard>

      <GlassCard tone="strong" padding="lg">
        <h2 className="text-lg font-semibold">Cómo cambió la creencia, respuesta por respuesta</h2>
        <p className="mb-4 text-sm text-slate-600">
          P(nivel | respuesta) = P(respuesta | nivel) · P(nivel) / P(respuesta). El posterior de cada fila es el prior de la siguiente.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[40rem] text-left text-sm">
            <thead>
              <tr className="border-b border-ice-200 text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4">Respuesta</th>
                <th className="py-2 pr-4">P(resp.)</th>
                {NIVELES.map((n) => (
                  <th key={n} className="py-2 pr-4 capitalize">
                    {n} (ahora)
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {a.pasos.map((p) => (
                <tr key={p.pregunta_id} className="border-b border-ice-100">
                  <td className="py-2 pr-4">
                    <span className="block font-medium">{p.respuesta}</span>
                    <span className="text-xs text-slate-500">{p.pregunta}</span>
                  </td>
                  <td className="py-2 pr-4 tabular-nums">{formatPct(p.probabilidad_evidencia, 1)}</td>
                  {NIVELES.map((n) => (
                    <td key={n} className="py-2 pr-4 tabular-nums">
                      {formatPct(p.despues[n], 1)}
                      <span className="ml-1 text-xs text-slate-400">← {formatPct(p.antes[n], 0)}</span>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>

      <GlassCard tone="strong" padding="lg">
        <h2 className="text-lg font-semibold">Qué le pedimos al seguro y por qué</h2>
        <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-slate-700">
          {r.razones.map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ul>
        {r.ajustes.length > 0 && (
          <ul className="mt-4 space-y-1.5 text-sm text-amber-800">
            {r.ajustes.map((t) => (
              <li key={t}>
                <Chip tone="amber">Ajuste</Chip> {t}
              </li>
            ))}
          </ul>
        )}
      </GlassCard>

      {mejor ? (
        <div className="grid gap-4">
          <h2 className="text-xl font-semibold">Tu seguro recomendado</h2>
          <OpcionCard opcion={mejor} destacada seleccionada={false} puedeSeleccionar={false} onComparar={() => undefined} />
          <div>
            <GlassButton onClick={onVerRanking} icon={ArrowRight}>
              Ver el ranking completo ({r.recomendacion.candidatos_validos} opciones)
            </GlassButton>
          </div>
        </div>
      ) : (
        <StateMessage variant="empty" title="No encontramos un plan con ese presupuesto">
          Sube tu presupuesto mensual e inténtalo de nuevo.
        </StateMessage>
      )}
      <p className="text-xs text-slate-500">{r.aviso}</p>
    </section>
  );
}
