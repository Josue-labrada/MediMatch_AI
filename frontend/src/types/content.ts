import type { LucideIcon } from 'lucide-react';

/** Bloque de texto con ícono (pasos, principios, rasgos). */
export interface FeatureItem {
  icon: LucideIcon;
  title: string;
  description: string;
}

/** Tarjeta que describe un enfoque de IA con sus elementos formales. */
export interface AiApproach {
  icon: LucideIcon;
  tag: string;
  title: string;
  summary: string;
  elements: Array<{ term: string; detail: string }>;
}
