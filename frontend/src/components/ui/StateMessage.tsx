import type { ReactNode } from 'react';
import { AlertTriangle, Inbox, Loader2, type LucideIcon } from 'lucide-react';
import { GlassCard } from './GlassCard';

type Variant = 'loading' | 'error' | 'empty';

const iconos: Record<Variant, LucideIcon> = { loading: Loader2, error: AlertTriangle, empty: Inbox };
const colores: Record<Variant, string> = {
  loading: 'bg-ice-100 text-ice-700',
  error: 'bg-rose-50 text-rose-600',
  empty: 'bg-ice-100 text-ice-700',
};

interface StateMessageProps {
  variant: Variant;
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}

/** Mensaje de estado (cargando, error o vacío) con el estilo de vidrio. */
export function StateMessage({ variant, title, children, action }: StateMessageProps) {
  const Icon = iconos[variant];
  return (
    <GlassCard
      tone="strong"
      padding="lg"
      className="text-center"
      role={variant === 'error' ? 'alert' : 'status'}
      aria-live="polite"
    >
      <span className={`mx-auto grid h-12 w-12 place-items-center rounded-2xl ${colores[variant]}`}>
        <Icon aria-hidden="true" size={22} className={variant === 'loading' ? 'animate-spin' : undefined} />
      </span>
      <h2 className="mt-4 text-lg font-semibold">{title}</h2>
      {children && <div className="mx-auto mt-2 max-w-xl text-sm leading-relaxed text-slate-600">{children}</div>}
      {action && <div className="mt-6 flex justify-center">{action}</div>}
    </GlassCard>
  );
}
