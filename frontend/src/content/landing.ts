/**
 * Textos de la landing page. Es contenido informativo del producto, no
 * datos de seguros: ningún plan, precio ni recomendación vive en el frontend.
 */
import {
  BadgeX,
  Eye,
  FlaskConical,
  GitBranch,
  ListOrdered,
  Lock,
  MessageSquareText,
  SlidersHorizontal,
  Target,
} from 'lucide-react';
import type { AiApproach, FeatureItem } from '../types/content';

export const heroHighlights: FeatureItem[] = [
  { icon: Lock, title: 'Sin datos médicos', description: 'Solo pedimos restricciones y preferencias.' },
  { icon: Eye, title: 'Decisiones explicables', description: 'Cada resultado muestra su porqué.' },
  { icon: FlaskConical, title: 'Catálogo simulado', description: 'Aseguradoras y precios ficticios.' },
];

export const howItWorksSteps: FeatureItem[] = [
  {
    icon: SlidersHorizontal,
    title: 'Define tus límites',
    description:
      'Presupuesto mensual, deducible máximo, coberturas indispensables y qué tanto te importa cada criterio.',
  },
  {
    icon: GitBranch,
    title: 'El CSP busca combinaciones válidas',
    description:
      'Plan, deducible y coberturas se modelan como variables. El backtracking explora asignaciones y el forward checking poda ramas imposibles.',
  },
  {
    icon: ListOrdered,
    title: 'Se ordenan con una función objetivo',
    description:
      'Cada combinación válida recibe una puntuación ponderada con tus pesos. Los empates se resuelven con reglas fijas y públicas.',
  },
  {
    icon: MessageSquareText,
    title: 'Ves la explicación',
    description:
      'Qué restricciones se cumplieron, por qué se descartó cada opción y cuánto aportó cada criterio a la puntuación.',
  },
];

export const aiApproaches: AiApproach[] = [
  {
    icon: GitBranch,
    tag: 'Módulo 04 · CSP',
    title: 'Problema de satisfacción de restricciones',
    summary:
      'Encuentra todas las configuraciones que cumplen tus restricciones duras, sin depender de reglas fijas por presupuesto.',
    elements: [
      { term: 'Variables', detail: 'Plan, variante de deducible y coberturas a incluir.' },
      { term: 'Dominios', detail: 'Opciones disponibles en el catálogo sincronizado.' },
      { term: 'Restricciones', detail: 'Presupuesto, deducible máximo, coberturas obligatorias y compatibilidades.' },
      { term: 'Algoritmo', detail: 'Backtracking con forward checking y conteo de podas.' },
    ],
  },
  {
    icon: Target,
    tag: 'Módulo 03 · Búsqueda',
    title: 'Búsqueda y optimización multicriterio',
    summary:
      'Recorre el conjunto de soluciones válidas y elige la de mayor puntuación según una función objetivo explícita.',
    elements: [
      { term: 'Espacio', detail: 'Soluciones factibles que entrega el CSP.' },
      { term: 'Función objetivo', detail: 'Suma ponderada de criterios normalizados entre 0 y 1.' },
      { term: 'Pesos', detail: 'Ajustables por el usuario; siempre suman 1.' },
      { term: 'Comparación', detail: 'Contraste contra la alternativa de menor prima.' },
    ],
  },
];

export const principles: FeatureItem[] = [
  {
    icon: FlaskConical,
    title: 'Datos simulados',
    description: 'Todas las aseguradoras, planes y precios son ficticios y están etiquetados como tales.',
  },
  {
    icon: Lock,
    title: 'Privacidad primero',
    description: 'No solicitamos diagnósticos, historial clínico ni datos personales sensibles.',
  },
  {
    icon: Eye,
    title: 'Transparencia',
    description: 'La puntuación es una función diseñada por el equipo, no un modelo entrenado ni una predicción actuarial.',
  },
  {
    icon: BadgeX,
    title: 'Sin venta de pólizas',
    description: 'No cotizamos oficialmente, no emitimos pólizas y no procesamos pagos.',
  },
];
