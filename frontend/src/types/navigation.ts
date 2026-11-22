import type { LucideIcon } from 'lucide-react';

/** Pantalla de la aplicación registrada en el router y en la navegación. */
export interface AppRoute {
  /** Ruta absoluta, p. ej. "/buscar". */
  path: string;
  /** Texto corto para la barra de navegación. */
  label: string;
  /** Título completo de la pantalla (también se usa en <title>). */
  title: string;
  /** Resumen de la pantalla (se muestra en el menú móvil). */
  description: string;
  icon: LucideIcon;
}
