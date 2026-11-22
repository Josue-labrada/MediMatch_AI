import { ArrowDown, BrainCircuit, Database, Filter, GitBranch, Info, ListOrdered, MessageSquareText, Server } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { SectionHeader } from '../components/ui/SectionHeader';
import { useBusqueda } from '../context/BusquedaContext';
import { ETIQUETA_ALGORITMO, formatNumero } from '../lib/format';

const FLUJO = [
  { icon: MessageSquareText, titulo: 'Formulario', texto: 'Restricciones duras y pesos. Sin datos personales.' },
  { icon: Server, titulo: 'FastAPI', texto: 'Valida con Pydantic y rechaza campos no previstos.' },
  { icon: Database, titulo: 'PostgreSQL', texto: 'Catálogo simulado sincronizado desde la API mock.' },
  { icon: GitBranch, titulo: 'CSP', texto: 'Backtracking + forward checking: todas las configuraciones válidas.' },
  { icon: ListOrdered, titulo: 'Optimización', texto: 'Función objetivo ponderada sobre el conjunto factible.' },
  { icon: Filter, titulo: 'Explicación', texto: 'Desglose del puntaje, restricciones cumplidas y descartes.' },
];

const VARIABLES = [
  { v: 'P', nombre: 'Plan', dominio: 'Planes activos en PostgreSQL' },
  { v: 'D', nombre: 'Variante de deducible', dominio: 'Variantes del plan asignado a P (dominio condicionado)' },
  { v: 'Cₖ', nombre: '¿Incluir la cobertura k?', dominio: 'incluida → {1} · opcional → {1, 0} · no ofrecida → {0}' },
];

const RESTRICCIONES = [
  { nombre: 'Suma asegurada mínima', tipo: 'Unaria (P)', formula: 'suma(P) ≥ mínimo' },
  { nombre: 'Deducible máximo', tipo: 'Unaria (D)', formula: 'deducible(D) ≤ máximo' },
  { nombre: 'Coaseguro máximo', tipo: 'Unaria (D)', formula: 'coaseguro(D) ≤ máximo' },
  { nombre: 'Cobertura obligatoria', tipo: 'Unaria (Cₖ)', formula: 'Cₖ = 1' },
  { nombre: 'Presupuesto', tipo: 'Global', formula: 'prima(D) + Σ costo(Cₖ = 1) ≤ presupuesto' },
  { nombre: 'Regla «requiere»', tipo: 'Binaria (Cₐ, C_b)', formula: 'Cₐ = 1 ⇒ C_b = 1' },
  { nombre: 'Regla «excluye»', tipo: 'Binaria (Cₐ, C_b)', formula: '¬(Cₐ = 1 ∧ C_b = 1)' },
  { nombre: 'Regla «deducible máx.»', tipo: 'Binaria (D, Cₐ)', formula: 'Cₐ = 1 ⇒ deducible(D) ≤ valor' },
];

const PSEUDOCODIGO = `función BACKTRACK(asignación, dominios):
    si todas las variables están asignadas:
        guardar solución;  regresar
    X ← siguiente variable sin asignar         # orden: P, D, C₁ … Cₙ
    para cada valor v en dominios[X]:
        asignación[X] ← v
        si CONSISTENTE(X, asignación):         # restricciones ya evaluables
            nuevos ← FORWARD_CHECK(asignación, dominios)
            si ningún dominio quedó vacío:
                BACKTRACK(asignación, nuevos)
            si no: registrar poda             # se evita toda la rama
        si no: registrar poda
        quitar X de la asignación              # backtrack`;

export function AlgoritmosPage() {
  const { resultado } = useBusqueda();
  const comparacion = resultado?.comparacion_algoritmos ?? [];

  return (
    <div className="mx-auto max-w-[1680px] py-12 sm:py-16">
      <SectionHeader
        level="h1"
        align="left"
        eyebrow="Cómo funciona"
        eyebrowIcon={BrainCircuit}
        title="Los algoritmos, paso a paso"
        description="MediMatch combina un problema de satisfacción de restricciones (módulo 04) con búsqueda/optimización exhaustiva sobre sus soluciones (módulo 03)."
      />

      {/* Flujo */}
      <section aria-labelledby="flujo" className="mt-12">
        <h2 id="flujo" className="text-2xl font-semibold">Flujo de una consulta</h2>
        <ol className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-6">
          {FLUJO.map(({ icon: Icon, titulo, texto }, i) => (
            <GlassCard as="li" key={titulo} tone="strong" padding="md" className="relative">
              <span className="text-xs font-semibold tabular-nums text-ice-400">0{i + 1}</span>
              <Icon aria-hidden="true" size={22} className="mt-2 text-ice-700" />
              <h3 className="mt-3 font-semibold">{titulo}</h3>
              <p className="mt-1 text-sm leading-relaxed text-slate-600">{texto}</p>
            </GlassCard>
          ))}
        </ol>
      </section>

      {/* CSP */}
      <section aria-labelledby="csp" className="mt-16 grid gap-6 xl:grid-cols-2">
        <GlassCard tone="strong" padding="lg">
          <h2 id="csp" className="text-2xl font-semibold">1 · Modelado como CSP</h2>
          <p className="mt-3 leading-relaxed text-slate-600">
            Un filtro revisa cada plan por separado. Un CSP define <strong>variables</strong>, <strong>dominios</strong> y{' '}
            <strong>restricciones</strong> que relacionan variables entre sí (por ejemplo, una cobertura que solo existe con
            cierto deducible) y busca asignaciones completas que las cumplan todas.
          </p>
          <h3 className="mt-6 text-sm font-semibold uppercase tracking-wider text-slate-500">Variables y dominios</h3>
          <dl className="mt-3 divide-y divide-ice-100 rounded-2xl bg-white/60 ring-1 ring-white">
            {VARIABLES.map((x) => (
              <div key={x.v} className="grid gap-1 px-4 py-3 sm:grid-cols-[3rem_1fr]">
                <dt className="font-mono text-lg font-semibold text-ice-700">{x.v}</dt>
                <dd>
                  <p className="font-medium text-slate-900">{x.nombre}</p>
                  <p className="text-sm text-slate-600">{x.dominio}</p>
                </dd>
              </div>
            ))}
          </dl>
          <p className="mt-4 text-sm leading-relaxed text-slate-600">
            Las coberturas variables son las obligatorias y deseadas del usuario, más las que éstas arrastran por reglas
            «requiere». Así el espacio se mantiene pequeño y sin soluciones dominadas.
          </p>
        </GlassCard>

        <GlassCard tone="strong" padding="lg">
          <h2 className="text-2xl font-semibold">Restricciones</h2>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-[28rem] text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wider text-slate-500">
                  <th className="py-2 pr-4 font-semibold">Restricción</th>
                  <th className="py-2 pr-4 font-semibold">Tipo</th>
                  <th className="py-2 font-semibold">Condición</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ice-100">
                {RESTRICCIONES.map((r) => (
                  <tr key={r.nombre}>
                    <td className="py-3 pr-4 font-medium text-slate-900">{r.nombre}</td>
                    <td className="py-3 pr-4 text-slate-600">{r.tipo}</td>
                    <td className="py-3 font-mono text-xs text-ice-800">{r.formula}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      </section>

      {/* Backtracking */}
      <section aria-labelledby="bt" className="mt-6 grid gap-6 xl:grid-cols-[1.2fr_1fr]">
        <GlassCard tone="strong" padding="lg">
          <h2 id="bt" className="text-2xl font-semibold">2 · Backtracking con forward checking</h2>
          <p className="mt-3 leading-relaxed text-slate-600">
            El <strong>backtracking</strong> asigna una variable a la vez y retrocede en cuanto una restricción falla.
            El <strong>forward checking</strong> además elimina, después de cada asignación, los valores incompatibles de
            las variables pendientes: si un dominio queda vacío, la rama se poda sin explorarla.
          </p>
          <pre className="mt-6 overflow-x-auto rounded-2xl bg-ice-950 p-5 text-[0.8rem] leading-relaxed text-ice-100">
            <code>{PSEUDOCODIGO}</code>
          </pre>
        </GlassCard>

        <GlassCard tone="tint" padding="lg">
          <h3 className="text-lg font-semibold">Ejemplo de poda</h3>
          <ol className="mt-4 space-y-3 text-sm leading-relaxed text-slate-700">
            <li>
              <strong>P = Delta Viajero</strong>, el usuario exige «Cobertura internacional».
            </li>
            <li className="flex items-center gap-2 text-ice-700">
              <ArrowDown aria-hidden="true" size={16} /> asignar D
            </li>
            <li>
              <strong>D = $50,000</strong>. Forward checking revisa C<sub>internacional</sub>: la regla exige deducible ≤
              $30,000 → se elimina el valor 1. Como es obligatoria, el 0 ya estaba eliminado → <strong>dominio vacío</strong>.
            </li>
            <li className="rounded-xl bg-white/70 p-3 ring-1 ring-white">
              Se poda la rama sin probar ninguna combinación de coberturas. El backtracking simple las habría intentado
              una por una.
            </li>
          </ol>
          {comparacion.length === 2 && (
            <div className="mt-6">
              <h4 className="text-sm font-semibold">En tu última búsqueda</h4>
              <table className="mt-2 w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wider text-slate-500">
                    <th className="py-1.5 font-semibold">Algoritmo</th>
                    <th className="py-1.5 text-right font-semibold">Nodos</th>
                    <th className="py-1.5 text-right font-semibold">Podas</th>
                    <th className="py-1.5 text-right font-semibold">Soluciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ice-200/60">
                  {comparacion.map((c) => (
                    <tr key={c.algoritmo}>
                      <td className="py-2 font-medium text-slate-800">{ETIQUETA_ALGORITMO[c.algoritmo]}</td>
                      <td className="py-2 text-right tabular-nums">{formatNumero(c.nodos_explorados)}</td>
                      <td className="py-2 text-right tabular-nums">{formatNumero(c.total_podas)}</td>
                      <td className="py-2 text-right tabular-nums">{formatNumero(c.soluciones)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </GlassCard>
      </section>

      {/* Función objetivo */}
      <section aria-labelledby="fo" className="mt-6 grid gap-6 xl:grid-cols-2">
        <GlassCard tone="strong" padding="lg">
          <h2 id="fo" className="text-2xl font-semibold">3 · Función objetivo del ranking</h2>
          <p className="mt-3 leading-relaxed text-slate-600">
            Sobre el conjunto factible F que entrega el CSP se busca la configuración con mayor puntaje. Como F es pequeño,
            se evalúa completo: el óptimo encontrado es el óptimo global.
          </p>
          <div className="mt-5 rounded-2xl bg-white/70 p-5 text-center font-mono text-sm text-ice-900 ring-1 ring-white sm:text-base">
            puntaje(x) = Σ wᵢ · nᵢ(x), con Σ wᵢ = 1 y 0 ≤ nᵢ ≤ 1
          </div>
          <ul className="mt-5 space-y-2 text-sm leading-relaxed text-slate-600">
            <li>
              <strong>Costo, deducible y coaseguro</strong> (menor es mejor): n = (max − x) / (max − min)
            </li>
            <li>
              <strong>Suma asegurada</strong> (mayor es mejor): n = (x − min) / (max − min)
            </li>
            <li>
              <strong>Coberturas deseadas</strong>: fracción de las deseadas que incluye la configuración
            </li>
          </ul>
        </GlassCard>
        <GlassCard tone="strong" padding="lg">
          <h3 className="text-lg font-semibold">Decisiones documentadas</h3>
          <ul className="mt-4 space-y-3 text-sm leading-relaxed text-slate-600">
            <li>• Si un criterio no varía dentro de F (max = min), vale 1 para todas: no altera el orden.</li>
            <li>• Sin coberturas deseadas, ese criterio no aplica y su peso se reparte proporcionalmente.</li>
            <li>• Si todos los pesos son 0, se usan pesos iguales.</li>
            <li>• Desempate determinista: puntaje ↓, prima ↑, deducible ↑, identificador del plan ↑.</li>
            <li>• Línea base para comparar: la configuración válida de menor prima (criterio único).</li>
            <li>• La normalización es relativa a F: agregar un plan al catálogo puede cambiar los puntajes de los demás.</li>
          </ul>
          <p className="mt-6 flex gap-3 rounded-2xl bg-ice-100/70 p-4 text-sm leading-relaxed text-slate-700 ring-1 ring-ice-200/70">
            <Info aria-hidden="true" size={18} className="mt-0.5 shrink-0 text-ice-700" />
            No es machine learning: no hay entrenamiento ni datos históricos. Es una función objetivo diseñada por el equipo,
            con pesos que define el usuario.
          </p>
        </GlassCard>
      </section>
    </div>
  );
}
