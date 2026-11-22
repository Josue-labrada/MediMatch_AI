import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { ArrowRight, HeartPulse, Menu, X } from 'lucide-react';
import { APP_ROUTES } from '../../config/routes';
import { cn } from '../../lib/cn';
import { GlassButton } from '../ui/GlassButton';

const MOBILE_MENU_ID = 'menu-movil';

export function Navbar() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();

  // Cierra el menú móvil al navegar.
  useEffect(() => setOpen(false), [pathname]);

  // Cierra el menú móvil con la tecla Escape.
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open]);

  return (
    <header className="sticky top-0 z-50 px-4 sm:px-8 lg:px-12 pt-4">
      {/* La barra y el menú móvil son hermanos (no anidados) porque
          backdrop-filter no se compone bien entre vidrios anidados. */}
      <nav
        aria-label="Principal"
        className="glass glass-strong mx-auto flex max-w-[1680px] items-center justify-between gap-4 rounded-full py-2 pl-3 pr-2"
      >
        <Link to="/" className="flex shrink-0 items-center gap-2.5 rounded-full pr-2">
          <span className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-ice-400 to-ice-700 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.45)]">
            <HeartPulse aria-hidden="true" size={19} strokeWidth={2.3} />
          </span>
          <span className="text-[1.05rem] font-semibold tracking-tight text-slate-900">
            MediMatch <span className="text-gradient">IA</span>
          </span>
        </Link>

        <ul className="hidden items-center gap-1 lg:flex">
          {APP_ROUTES.map((route) => (
            <li key={route.path}>
              <NavLink
                to={route.path}
                end
                className={({ isActive }) =>
                  cn(
                    'rounded-full px-3.5 py-2 text-sm font-medium transition-colors duration-200',
                    isActive
                      ? 'bg-white text-ice-800 shadow-[0_1px_2px_rgba(15,39,71,0.08),inset_0_0_0_1px_rgba(132,191,255,0.45)]'
                      : 'text-slate-600 hover:bg-white/60 hover:text-slate-900',
                  )
                }
              >
                {route.label}
              </NavLink>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-1.5">
          <GlassButton to="/buscar" size="sm" icon={ArrowRight} className="hidden sm:inline-flex">
            Comenzar
          </GlassButton>
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            aria-expanded={open}
            aria-controls={MOBILE_MENU_ID}
            aria-label={open ? 'Cerrar menú' : 'Abrir menú'}
            className="grid h-10 w-10 place-items-center rounded-full text-slate-700 transition-colors hover:bg-white/70 lg:hidden"
          >
            {open ? <X aria-hidden="true" size={20} /> : <Menu aria-hidden="true" size={20} />}
          </button>
        </div>
      </nav>

      {open && (
        <div
          id={MOBILE_MENU_ID}
          className="glass glass-strong mx-auto mt-2 max-w-[1680px] animate-fade-up rounded-3xl p-2 lg:hidden"
        >
          <ul className="grid gap-1 sm:grid-cols-2">
            {APP_ROUTES.map(({ path, label, description, icon: Icon }) => (
              <li key={path}>
                <NavLink
                  to={path}
                  end
                  className={({ isActive }) =>
                    cn(
                      'flex items-start gap-3 rounded-2xl p-3 transition-colors',
                      isActive ? 'bg-white text-ice-800' : 'hover:bg-white/70',
                    )
                  }
                >
                  <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-ice-100 text-ice-700">
                    <Icon aria-hidden="true" size={17} />
                  </span>
                  <span>
                    <span className="block text-sm font-semibold text-slate-900">{label}</span>
                    <span className="line-clamp-2 block text-xs leading-snug text-slate-500">{description}</span>
                  </span>
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      )}
    </header>
  );
}
