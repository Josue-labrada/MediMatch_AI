/**
 * Ilustración conceptual de un árbol de backtracking: nivel 1 = planes,
 * nivel 2 = variantes de deducible. Es didáctica (no representa datos
 * reales): muestra ramas podadas y asignaciones consistentes.
 */
type NodeState = 'explored' | 'solution' | 'pruned';

interface TreeNode {
  x: number;
  y: number;
  state: NodeState;
  parent?: number; // índice del nodo padre
}

const NODES: TreeNode[] = [
  { x: 160, y: 26, state: 'explored' }, // 0 raíz
  { x: 62, y: 96, state: 'explored', parent: 0 }, // 1 plan A
  { x: 160, y: 96, state: 'pruned', parent: 0 }, // 2 plan B (podado por forward checking)
  { x: 258, y: 96, state: 'explored', parent: 0 }, // 3 plan C
  { x: 30, y: 166, state: 'solution', parent: 1 },
  { x: 94, y: 166, state: 'pruned', parent: 1 },
  { x: 226, y: 166, state: 'pruned', parent: 3 },
  { x: 290, y: 166, state: 'solution', parent: 3 },
];

const LEVEL_LABELS = ['Inicio', 'Plan', 'Deducible'];

function Node({ x, y, state }: TreeNode) {
  if (state === 'solution') {
    return (
      <g>
        <circle cx={x} cy={y} r={14} fill="url(#solutionFill)" />
        <circle cx={x} cy={y} r={14} fill="none" stroke="rgba(255,255,255,0.7)" />
        <path d={`M${x - 5} ${y} l3.5 3.5 l6.5 -7`} fill="none" stroke="#fff" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" />
      </g>
    );
  }
  if (state === 'pruned') {
    return (
      <g>
        <circle cx={x} cy={y} r={12} fill="#fff1f2" stroke="#fda4af" strokeDasharray="3 3" />
        <path d={`M${x - 4} ${y - 4} l8 8 M${x + 4} ${y - 4} l-8 8`} stroke="#e11d48" strokeWidth={2} strokeLinecap="round" />
      </g>
    );
  }
  return <circle cx={x} cy={y} r={12} fill="#fff" stroke="#84bfff" strokeWidth={2} />;
}

export function SearchTreeIllustration() {
  return (
    <figure>
      <svg
        viewBox="0 0 320 196"
        className="h-auto w-full"
        role="img"
        aria-labelledby="arbol-titulo arbol-desc"
      >
        <title id="arbol-titulo">Árbol de búsqueda con backtracking</title>
        <desc id="arbol-desc">
          Ilustración conceptual: desde la raíz se prueban tres planes; uno se poda completo y en los otros
          dos se encuentra una asignación válida y se descarta otra.
        </desc>
        <defs>
          <linearGradient id="solutionFill" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#4d9bf2" />
            <stop offset="1" stopColor="#1a5aab" />
          </linearGradient>
        </defs>

        {NODES.map((node, index) => {
          if (node.parent === undefined) return null;
          const parent = NODES[node.parent];
          const pruned = node.state === 'pruned';
          return (
            <line
              key={`edge-${index}`}
              x1={parent.x}
              y1={parent.y}
              x2={node.x}
              y2={node.y}
              stroke={pruned ? '#fecdd3' : '#b5d9ff'}
              strokeWidth={2}
              strokeDasharray={pruned ? '4 4' : undefined}
            />
          );
        })}
        {NODES.map((node, index) => (
          <Node key={`node-${index}`} {...node} />
        ))}
      </svg>

      <figcaption className="mt-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-2 text-xs text-slate-500">
        <span className="flex flex-wrap gap-x-4 gap-y-1">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-ice-600" /> Asignación válida
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full border border-dashed border-rose-400 bg-rose-50" /> Rama podada
          </span>
        </span>
        <span className="hidden sm:inline" aria-hidden="true">
          Niveles: {LEVEL_LABELS.join(' → ')}
        </span>
      </figcaption>
    </figure>
  );
}
