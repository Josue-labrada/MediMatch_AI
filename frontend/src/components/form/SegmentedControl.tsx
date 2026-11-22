import { cn } from '../../lib/cn';

export interface SegmentOption<T extends string | number> {
  value: T;
  label: string;
}

interface SegmentedControlProps<T extends string | number> {
  name: string;
  legend: string;
  /** Oculta la leyenda visualmente (sigue disponible para lectores de pantalla). */
  hideLegend?: boolean;
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  size?: 'sm' | 'md';
  className?: string;
}

/** Grupo de opciones exclusivas con radios nativos (accesible con teclado). */
export function SegmentedControl<T extends string | number>({
  name,
  legend,
  hideLegend = false,
  options,
  value,
  onChange,
  size = 'md',
  className,
}: SegmentedControlProps<T>) {
  return (
    <fieldset className={className}>
      <legend className={hideLegend ? 'sr-only' : 'mb-2.5 text-sm font-semibold text-slate-900'}>{legend}</legend>
      <div className="flex flex-wrap gap-1 rounded-2xl bg-ice-100/70 p-1 ring-1 ring-inset ring-ice-200/70">
        {options.map((opcion) => (
          <label key={String(opcion.value)} className="flex-1">
            <input
              type="radio"
              name={name}
              className="peer sr-only"
              checked={opcion.value === value}
              onChange={() => onChange(opcion.value)}
            />
            <span
              className={cn(
                'flex cursor-pointer items-center justify-center whitespace-nowrap rounded-xl font-medium text-slate-600 transition-all duration-200',
                'hover:text-slate-900 peer-checked:bg-white peer-checked:text-ice-800 peer-checked:shadow-[0_1px_3px_rgba(15,39,71,0.12),inset_0_0_0_1px_rgba(132,191,255,0.5)]',
                'peer-focus-visible:ring-2 peer-focus-visible:ring-ice-600',
                size === 'sm' ? 'px-2.5 py-1.5 text-xs' : 'px-3 py-2 text-sm',
              )}
            >
              {opcion.label}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
