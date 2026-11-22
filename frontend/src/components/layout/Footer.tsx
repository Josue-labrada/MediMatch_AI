import { FlaskConical } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';

export function Footer() {
  return (
    <footer className="px-4 sm:px-8 lg:px-12 pb-8 pt-16">
      <GlassCard
        tone="strong"
        padding="md"
        className="mx-auto flex max-w-[1680px] flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <p className="font-semibold text-slate-900">
            MediMatch <span className="text-gradient">IA</span>
          </p>
          <p className="mt-1 text-sm text-slate-500">
            Proyecto final · Fundamentos de Inteligencia Artificial · ITESO 2026
          </p>
        </div>
        <p className="flex max-w-md items-start gap-2 text-sm leading-relaxed text-slate-600">
          <FlaskConical aria-hidden="true" size={17} className="mt-0.5 shrink-0 text-ice-700" />
          Prototipo educativo. Planes, precios y aseguradoras son ficticios. No constituye cotización,
          oferta de venta ni asesoría profesional.
        </p>
      </GlassCard>
    </footer>
  );
}
