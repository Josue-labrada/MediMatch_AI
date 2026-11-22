import type { LucideIcon } from 'lucide-react';
import { cn } from '../../lib/cn';
import { GlassCard } from './GlassCard';

interface StatTileProps {
  label: string;
  value: string;
  hint?: string;
  icon?: LucideIcon;
  className?: string;
}

/** Métrica destacada: valor grande con etiqueta y nota opcional. */
export function StatTile({ label, value, hint, icon: Icon, className }: StatTileProps) {
  return (
    <GlassCard padding="sm" tone="strong" className={cn('flex flex-col gap-1', className)}>
      <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
        {Icon && <Icon aria-hidden="true" size={14} className="text-ice-700" />}
        {label}
      </span>
      <span className="text-2xl font-semibold tabular-nums tracking-tight text-slate-900">{value}</span>
      {hint && <span className="text-xs leading-snug text-slate-500">{hint}</span>}
    </GlassCard>
  );
}
