import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '../../lib/cn';

type CardPadding = 'none' | 'sm' | 'md' | 'lg';
type CardTone = 'default' | 'strong' | 'tint';

export interface GlassCardProps extends HTMLAttributes<HTMLElement> {
  /** Etiqueta semántica del contenedor. */
  as?: 'div' | 'article' | 'section' | 'aside' | 'li';
  padding?: CardPadding;
  /** strong = más opaca (texto denso); tint = azul hielo. */
  tone?: CardTone;
  /** Eleva la tarjeta al pasar el cursor. */
  interactive?: boolean;
  children: ReactNode;
}

const paddingClasses: Record<CardPadding, string> = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-7 sm:p-10',
};

const toneClasses: Record<CardTone, string> = {
  default: '',
  strong: 'glass-strong',
  tint: 'glass-tint',
};

/** Superficie translúcida base del sistema Liquid Glass. */
export function GlassCard({
  as: Tag = 'div',
  padding = 'md',
  tone = 'default',
  interactive = false,
  className,
  children,
  ...rest
}: GlassCardProps) {
  return (
    <Tag
      className={cn(
        'glass rounded-3xl',
        toneClasses[tone],
        paddingClasses[padding],
        interactive && 'glass-interactive',
        className,
      )}
      {...rest}
    >
      {children}
    </Tag>
  );
}
