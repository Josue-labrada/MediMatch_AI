import { cn } from '../../lib/cn';

interface ProgressBarProps {
  /** Fracción entre 0 y 1. */
  value: number;
  label: string;
  tone?: 'ice' | 'emerald' | 'slate';
  className?: string;
}

const tones = {
  ice: 'from-ice-400 to-ice-600',
  emerald: 'from-emerald-400 to-emerald-600',
  slate: 'from-slate-300 to-slate-400',
};

export function ProgressBar({ value, label, tone = 'ice', className }: ProgressBarProps) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(pct)}
      className={cn('h-2 overflow-hidden rounded-full bg-ice-100/80 ring-1 ring-inset ring-ice-200/60', className)}
    >
      <div
        className={cn('h-full rounded-full bg-gradient-to-r transition-[width] duration-500', tones[tone])}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
