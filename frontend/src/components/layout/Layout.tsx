import { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { findRoute } from '../../config/routes';
import { BackgroundGlow } from '../ui/BackgroundGlow';
import { Footer } from './Footer';
import { Navbar } from './Navbar';

/** Estructura común: fondo, navegación, contenido de la ruta y pie. */
export function Layout() {
  const { pathname } = useLocation();

  // Título de pestaña por pantalla y regreso al inicio de la página al navegar.
  useEffect(() => {
    const route = findRoute(pathname);
    document.title = route && route.path !== '/' ? `${route.title} · MediMatch IA` : 'MediMatch IA';
    window.scrollTo({ top: 0 });
  }, [pathname]);

  return (
    <>
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[60] focus:rounded-full focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-ice-800 focus:shadow-lg"
      >
        Saltar al contenido
      </a>
      <BackgroundGlow />
      <Navbar />
      <main id="contenido" className="overflow-x-clip px-4 sm:px-8 lg:px-12">
        <Outlet />
      </main>
      <Footer />
    </>
  );
}
