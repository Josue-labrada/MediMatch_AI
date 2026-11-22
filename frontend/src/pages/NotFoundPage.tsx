import { ArrowLeft, Compass } from 'lucide-react';
import { GlassButton } from '../components/ui/GlassButton';
import { GlassCard } from '../components/ui/GlassCard';

export function NotFoundPage() {
  return (
    <section className="mx-auto max-w-xl py-24">
      <GlassCard tone="strong" padding="lg" className="text-center">
        <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-ice-100 text-ice-700">
          <Compass aria-hidden="true" size={26} />
        </span>
        <h1 className="mt-5 text-2xl font-semibold">Página no encontrada</h1>
        <p className="mt-3 text-slate-600">La dirección que buscas no existe en MediMatch IA.</p>
        <GlassButton to="/" variant="secondary" icon={ArrowLeft} iconPosition="left" className="mt-8">
          Volver al inicio
        </GlassButton>
      </GlassCard>
    </section>
  );
}
