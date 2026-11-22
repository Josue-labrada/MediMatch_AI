import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '../../lib/cn';

export interface SectionHeaderProps {
  /** Etiqueta pequeña sobre el título. */
  eyebrow?: string;
  eyebrowIcon?: LucideIcon;
  title: ReactNode;
  description?: ReactNode;
  align?: 'left' | 'center';
  /** h1 solo para el encabezado principal de cada página. */
  level?: 'h1' | 'h2';
  /** id del título, para enlazarlo con aria-labelledby de la sección. */
  id?: string;
  className?: string;
}

export function SectionHeader({
  eyebrow,
  eyebrowIcon: EyebrowIcon,
  title,
  description,
  align = 'center',
  level = 'h2',
  id,
  className,
}: SectionHeaderProps) {
  const Heading = level;
  const centered = align === 'center';

  return (
    <header className={cn('max-w-4xl', centered && 'mx-auto text-center', className)}>
      {eyebrow && (
        <p className="eyebrow glass glass-tint mb-5">
          {EyebrowIcon && <EyebrowIcon aria-hidden="true" size={14} strokeWidth={2.4} />}
          {eyebrow}
        </p>
      )}
      <Heading
        id={id}
        className={cn(
          'font-semibold tracking-tight text-slate-900',
          level === 'h1'
            ? 'text-[2.5rem] leading-[1.06] sm:text-6xl xl:text-7xl'
            : 'text-3xl leading-tight sm:text-4xl xl:text-5xl',
        )}
      >
        {title}
      </Heading>
      {description && (
        <p className={cn('mt-5 text-lg leading-relaxed text-slate-600 sm:text-xl', centered && 'mx-auto max-w-2xl')}>
          {description}
        </p>
      )}
    </header>
  );
}
