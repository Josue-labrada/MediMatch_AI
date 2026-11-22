import type { ButtonHTMLAttributes, ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '../../lib/cn';

type ButtonVariant = 'primary' | 'secondary' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface CommonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: LucideIcon;
  iconPosition?: 'left' | 'right';
  className?: string;
  children: ReactNode;
}

/** Con `to` se renderiza como enlace interno del router. */
interface LinkButtonProps extends CommonProps {
  to: string;
  'aria-label'?: string;
}

/** Sin `to` se renderiza como <button> nativo. */
interface NativeButtonProps
  extends CommonProps,
    Omit<ButtonHTMLAttributes<HTMLButtonElement>, keyof CommonProps> {
  to?: undefined;
}

export type GlassButtonProps = LinkButtonProps | NativeButtonProps;

const variantClasses: Record<ButtonVariant, string> = {
  // Vidrio azul: gradiente + brillo interior. Texto blanco sobre ice-600/700 (contraste AA).
  primary:
    'bg-gradient-to-b from-ice-500 to-ice-700 text-white ' +
    '[box-shadow:inset_0_1px_0_rgba(255,255,255,0.4),inset_0_0_0_1px_rgba(255,255,255,0.18),0_10px_30px_-10px_rgba(31,111,209,0.6)] ' +
    'hover:from-ice-600 hover:to-ice-800',
  secondary:
    'glass glass-strong text-ice-800 hover:text-ice-950 hover:bg-white/90',
  ghost: 'text-ice-800 hover:bg-white/60',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'h-9 px-4 text-sm gap-1.5',
  md: 'h-11 px-5 text-[0.95rem] gap-2',
  lg: 'h-12 px-6 text-base gap-2.5',
};

const iconSize: Record<ButtonSize, number> = { sm: 16, md: 18, lg: 19 };

export function GlassButton(props: GlassButtonProps) {
  const {
    variant = 'primary',
    size = 'md',
    icon: Icon,
    iconPosition = 'right',
    className,
    children,
  } = props;

  const classes = cn(
    'inline-flex select-none items-center justify-center rounded-full font-semibold',
    'transition-all duration-300 ease-out active:scale-[0.98]',
    'disabled:pointer-events-none disabled:opacity-50',
    variantClasses[variant],
    sizeClasses[size],
    className,
  );

  const iconEl = Icon ? <Icon aria-hidden="true" size={iconSize[size]} strokeWidth={2.2} /> : null;
  const content = (
    <>
      {iconPosition === 'left' && iconEl}
      <span>{children}</span>
      {iconPosition === 'right' && iconEl}
    </>
  );

  if (props.to !== undefined) {
    return (
      <Link to={props.to} className={classes} aria-label={props['aria-label']}>
        {content}
      </Link>
    );
  }

  // Quita las props propias del componente antes de pasarlas al <button>.
  const {
    variant: _variant,
    size: _size,
    icon: _icon,
    iconPosition: _iconPosition,
    className: _className,
    children: _children,
    to: _to,
    type = 'button',
    ...buttonProps
  } = props;

  return (
    <button type={type} className={classes} {...buttonProps}>
      {content}
    </button>
  );
}
