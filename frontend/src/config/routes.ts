import { BrainCircuit, ClipboardList, Database, House, ListChecks, Scale, SlidersHorizontal } from 'lucide-react';
import type { AppRoute } from '../types/navigation';

/**
 * Fuente única de las pantallas: el router, la navbar y los títulos de
 * página se generan a partir de esta lista.
 */
export const APP_ROUTES: AppRoute[] = [
  {
    path: '/',
    label: 'Inicio',
    title: 'Inicio',
    description: 'Presentación del prototipo y de los enfoques de IA.',
    icon: House,
  },
  {
    path: '/buscar',
    label: 'Buscar',
    title: 'Encontrar un seguro',
    description:
      'Formulario para definir restricciones (presupuesto, deducible, coberturas indispensables) y pesos de preferencia.',
    icon: SlidersHorizontal,
  },
  {
    path: '/cuestionario',
    label: 'Cuestionario',
    title: 'Cuestionario de riesgo (Bayes)',
    description:
      'Responde unas preguntas: la regla de Bayes estima tu nivel de riesgo y el sistema te recomienda un seguro.',
    icon: ClipboardList,
  },
  {
    path: '/resultados',
    label: 'Resultados',
    title: 'Resultados y recomendaciones',
    description:
      'Configuraciones válidas encontradas por el CSP, ordenadas por la función objetivo y con su explicación.',
    icon: ListChecks,
  },
  {
    path: '/comparar',
    label: 'Comparar',
    title: 'Comparación de seguros',
    description: 'Comparación lado a lado de las alternativas seleccionadas.',
    icon: Scale,
  },
  {
    path: '/algoritmos',
    label: 'Algoritmos',
    title: 'Cómo funcionan los algoritmos',
    description:
      'Explicación del modelado CSP, backtracking, forward checking y la función objetivo del ranking.',
    icon: BrainCircuit,
  },
  {
    path: '/admin',
    label: 'Admin',
    title: 'Panel administrativo',
    description: 'Sincronización del catálogo simulado desde la API mock y estado de los servicios.',
    icon: Database,
  },
];

export function findRoute(pathname: string): AppRoute | undefined {
  return APP_ROUTES.find((route) => route.path === pathname);
}
