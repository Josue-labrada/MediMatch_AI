import type { ReactNode } from 'react';
import { cn } from '../../lib/cn';

type ChipTone = 'ice' | 'emerald' | 'amber' | 'rose' | 'slate';

const tones: Record<ChipTone, string> = {
  ice: 'bg-ice-100 text-ice-800 ring-ice-200',
  emerald: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
  amber: 'bg-amber-50 text-amber-800 ring-amber-200',
  rose: 'bg-rose-50 text-rose-800 ring-rose-200',
  slate: 'bg-slate-100 text-slate-700 ring-slate-200',
};

export function Chip({ children, tone = 'ice', className }: { children: ReactNode; tone?: ChipTone; className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
