import { ArrowRight, BrainCircuit, FlaskConical, Info, Sparkles } from 'lucide-react';
import { SearchTreeIllustration } from '../components/illustrations/SearchTreeIllustration';
import { GlassButton } from '../components/ui/GlassButton';
import { GlassCard } from '../components/ui/GlassCard';
import { SectionHeader } from '../components/ui/SectionHeader';
import { aiApproaches, heroHighlights, howItWorksSteps, principles } from '../content/landing';

export function HomePage() {
  return (
    <div className="mx-auto max-w-[1680px]">
      <HeroSection />
      <HowItWorksSection />
      <AiApproachesSection />
      <PrinciplesSection />
      <ClosingSection />
    </div>
  );
}

function HeroSection() {
  return (
    <section aria-labelledby="hero-titulo" className="grid items-center gap-12 pb-16 pt-12 sm:pt-16 lg:min-h-[calc(100svh-5.5rem)] lg:grid-cols-[1.1fr_0.9fr] lg:gap-16 lg:py-10 2xl:gap-24">
      <div className="animate-fade-up">
        <SectionHeader
          id="hero-titulo"
          level="h1"
          align="left"
          eyebrow="Prototipo académico · Datos simulados"
          eyebrowIcon={FlaskConical}
          title={
            <>
              Encuentra la cobertura médica que <span className="text-gradient">sí encaja contigo</span>
            </>
          }
          description="MediMatch IA compara planes simulados de gastos médicos mayores. Un solucionador de restricciones descarta lo que no cumple y una función objetivo transparente ordena las alternativas, explicando cada decisión."
        />

        <div className="mt-9 flex flex-col gap-3 sm:flex-row">
          <GlassButton to="/buscar" size="lg" icon={ArrowRight}>
            Comenzar búsqueda
          </GlassButton>
          <GlassButton to="/algoritmos" size="lg" variant="secondary" icon={BrainCircuit} iconPosition="left">
            Conocer los algoritmos
          </GlassButton>
        </div>

        <ul className="mt-12 grid gap-5 sm:grid-cols-3">
          {heroHighlights.map(({ icon: Icon, title, description }) => (
            <li key={title} className="flex items-start gap-3">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-white/80 text-ice-700 shadow-sm ring-1 ring-ice-200">
                <Icon aria-hidden="true" size={17} />
              </span>
              <span>
                <span className="block text-sm font-semibold text-slate-900">{title}</span>
                <span className="block text-sm leading-snug text-slate-500">{description}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="relative animate-fade-up [animation-delay:120ms]">
        {/* Halo detrás de la tarjeta para reforzar el efecto de vidrio. */}
        <div aria-hidden="true" className="absolute inset-0 -z-10 sm:-inset-6 rounded-[2.5rem] bg-gradient-to-br from-ice-300/60 via-cyan-200/40 to-transparent blur-2xl" />
        <GlassCard padding="lg" className="mx-auto max-w-2xl rounded-[2rem] lg:mr-0">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-slate-900">Cómo decide MediMatch</p>
            <span className="rounded-full bg-ice-100/80 px-2.5 py-1 text-[0.7rem] font-semibold uppercase tracking-wider text-ice-700">
              Ilustración conceptual
            </span>
          </div>
          <div className="mt-6">
            <SearchTreeIllustration />
          </div>
          <ol className="mt-7 space-y-2.5">
            {[
              ['Restricciones duras', 'CSP con backtracking'],
              ['Preferencias y pesos', 'Función objetivo'],
              ['Resultado', 'Explicación por criterio'],
            ].map(([input, method], index) => (
              <li
                key={input}
                className="flex items-center justify-between gap-3 rounded-2xl bg-white/60 px-4 py-3 text-sm ring-1 ring-white/80"
              >
                <span className="flex items-center gap-3">
                  <span className="grid h-6 w-6 place-items-center rounded-full bg-ice-600 text-[0.7rem] font-bold text-white">
                    {index + 1}
                  </span>
                  <span className="font-medium text-slate-800">{input}</span>
                </span>
                <span className="text-slate-500">{method}</span>
              </li>
            ))}
          </ol>
        </GlassCard>
      </div>
    </section>
  );
}

function HowItWorksSection() {
  return (
    <section id="como-funciona" aria-labelledby="como-funciona-titulo" className="scroll-mt-28 py-20 lg:py-28">
      <SectionHeader
        id="como-funciona-titulo"
        eyebrow="Cómo funciona"
        eyebrowIcon={Sparkles}
        title="De tus restricciones a una recomendación explicada"
        description="Cuatro pasos, sin cajas negras: cada etapa produce información que puedes revisar."
      />
      <ol className="mt-14 grid gap-5 sm:grid-cols-2 xl:grid-cols-4 2xl:gap-6">
        {howItWorksSteps.map(({ icon: Icon, title, description }, index) => (
          <GlassCard as="li" key={title} interactive className="flex flex-col">
            <div className="flex items-center justify-between">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-ice-100 to-white text-ice-700 ring-1 ring-ice-200/70">
                <Icon aria-hidden="true" size={21} />
              </span>
              <span className="text-sm font-semibold tabular-nums text-ice-300" aria-hidden="true">
                0{index + 1}
              </span>
            </div>
            <h3 className="mt-6 text-lg font-semibold leading-snug">{title}</h3>
            <p className="mt-2 text-[0.95rem] leading-relaxed text-slate-600">{description}</p>
          </GlassCard>
        ))}
      </ol>
    </section>
  );
}

function AiApproachesSection() {
  return (
    <section aria-labelledby="enfoques-titulo" className="py-20 lg:py-28">
      <SectionHeader
        id="enfoques-titulo"
        eyebrow="Enfoques de IA"
        eyebrowIcon={BrainCircuit}
        title="Dos técnicas del curso, trabajando en conjunto"
        description="El CSP garantiza que solo se consideren opciones válidas; la optimización decide cuál conviene más según tus prioridades."
      />
      <div className="mt-14 grid gap-6 lg:grid-cols-2">
        {aiApproaches.map(({ icon: Icon, tag, title, summary, elements }) => (
          <GlassCard as="article" key={title} tone="strong" padding="lg" interactive>
            <div className="flex items-center gap-3">
              <span className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-ice-500 to-ice-700 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.4)]">
                <Icon aria-hidden="true" size={22} />
              </span>
              <span className="text-xs font-semibold uppercase tracking-[0.12em] text-ice-700">{tag}</span>
            </div>
            <h3 className="mt-6 text-2xl font-semibold leading-snug">{title}</h3>
            <p className="mt-3 leading-relaxed text-slate-600">{summary}</p>
            <dl className="mt-7 divide-y divide-ice-100 rounded-2xl bg-white/55 ring-1 ring-white/80">
              {elements.map(({ term, detail }) => (
                <div key={term} className="grid gap-1 px-4 py-3.5 sm:grid-cols-[8.5rem_1fr] sm:gap-4">
                  <dt className="text-sm font-semibold text-slate-900">{term}</dt>
                  <dd className="text-sm leading-relaxed text-slate-600">{detail}</dd>
                </div>
              ))}
            </dl>
          </GlassCard>
        ))}
      </div>

      <GlassCard tone="tint" padding="md" className="mt-6 flex items-start gap-4">
        <Info aria-hidden="true" size={20} className="mt-0.5 shrink-0 text-ice-700" />
        <p className="text-sm leading-relaxed text-slate-700">
          <strong className="font-semibold text-slate-900">Nota de transparencia:</strong> la puntuación de
          ranking es una función objetivo diseñada y documentada por el equipo. No es un modelo de machine
          learning entrenado ni una probabilidad actuarial.
        </p>
      </GlassCard>
    </section>
  );
}

function PrinciplesSection() {
  return (
    <section aria-labelledby="principios-titulo" className="py-20 lg:py-28">
      <SectionHeader
        id="principios-titulo"
        eyebrow="Principios"
        title="Diseñado con responsabilidad"
        description="Un prototipo académico debe ser claro sobre lo que hace y lo que no hace."
      />
      <ul className="mt-14 grid gap-5 sm:grid-cols-2 xl:grid-cols-4 2xl:gap-6">
        {principles.map(({ icon: Icon, title, description }) => (
          <GlassCard as="li" key={title} interactive>
            <Icon aria-hidden="true" size={22} className="text-ice-700" />
            <h3 className="mt-4 font-semibold">{title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">{description}</p>
          </GlassCard>
        ))}
      </ul>
    </section>
  );
}

function ClosingSection() {
  return (
    <section aria-labelledby="cierre-titulo" className="py-16">
      <GlassCard padding="lg" className="relative overflow-hidden rounded-[2rem] text-center lg:py-20">
        <div aria-hidden="true" className="absolute -right-24 -top-24 -z-10 h-72 w-72 rounded-full bg-ice-300/50 blur-3xl" />
        <div aria-hidden="true" className="absolute -bottom-28 -left-20 -z-10 h-72 w-72 rounded-full bg-cyan-200/40 blur-3xl" />
        <h2 id="cierre-titulo" className="text-3xl font-semibold sm:text-4xl xl:text-5xl">
          Explora qué configuraciones <span className="text-gradient">cumplen tus condiciones</span>
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-lg leading-relaxed text-slate-600">
          Ajusta restricciones y pesos, y observa cómo cambian los resultados por efecto del algoritmo.
        </p>
        <GlassButton to="/buscar" size="lg" icon={ArrowRight} className="mt-8">
          Comenzar búsqueda
        </GlassButton>
      </GlassCard>
    </section>
  );
}
