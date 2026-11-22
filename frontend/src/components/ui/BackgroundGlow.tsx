/**
 * Fondo decorativo fijo: gradiente blanco → azul hielo con halos difusos.
 * Los halos tienen opacidad baja para no competir con el texto, y su
 * desplazamiento lento se desactiva con prefers-reduced-motion (index.css).
 */
export function BackgroundGlow() {
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-white via-ice-50 to-ice-100" />

      <div className="absolute -left-40 -top-48 h-[34rem] w-[34rem] animate-drift rounded-full bg-ice-300/45 blur-3xl" />
      <div className="absolute -right-48 top-1/4 h-[38rem] w-[38rem] animate-drift rounded-full bg-cyan-200/35 blur-3xl [animation-delay:-9s]" />
      <div className="absolute -bottom-56 left-1/4 h-[30rem] w-[30rem] animate-drift rounded-full bg-indigo-200/30 blur-3xl [animation-delay:-17s]" />

      {/* Retícula de puntos muy tenue, desvanecida hacia los bordes. */}
      <div
        className="absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage: 'radial-gradient(rgba(26, 90, 171, 0.18) 1px, transparent 1px)',
          backgroundSize: '28px 28px',
          maskImage: 'radial-gradient(ellipse 70% 55% at 50% 30%, #000 30%, transparent 75%)',
          WebkitMaskImage: 'radial-gradient(ellipse 70% 55% at 50% 30%, #000 30%, transparent 75%)',
        }}
      />
    </div>
  );
}
