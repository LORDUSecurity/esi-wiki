import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';

const LINKS = [
  { to: '/', label: 'Accueil' },
  { to: '/programmes', label: 'Programmes' },
  { to: '/esihub', label: 'EsiHub' },
  { to: '/campus', label: 'Vie de campus' },
  { to: '/faq', label: 'Q&R' },
  { to: '/a-propos', label: 'À propos' },
  { to: '/contact', label: 'Contact' },
];

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => setOpen(false), [pathname]);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'border-b border-white/8 bg-ink-950/85 backdrop-blur-xl py-3'
          : 'border-b border-transparent bg-transparent py-6'
      }`}
    >
      <div className="shell flex items-center justify-between gap-6">
        <Link to="/" className="group flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-md border border-gold-600/45 bg-ink-800 font-display text-lg text-gold-500 transition group-hover:bg-gold-600 group-hover:text-ink-950">
            E
          </span>
          <span className="leading-none">
            <span className="block font-display text-[19px] tracking-wide text-ivory">ESI Wiki</span>
            <span className="block text-[9px] uppercase tracking-[0.3em] text-muted">Rabat</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-6 lg:flex">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) =>
                `link-underline text-[13px] uppercase tracking-[0.15em] transition-colors ${
                  isActive ? 'text-gold-400' : 'text-ivory/70 hover:text-ivory'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
          <Link to="/assistant" className="btn-gold !px-5 !py-2.5 !text-[11px]">
            Assistant IA
          </Link>
        </nav>

        <button
          onClick={() => setOpen((v) => !v)}
          aria-label="Menu"
          aria-expanded={open}
          className="grid h-10 w-10 place-items-center rounded-md border border-white/12 text-ivory/80 lg:hidden"
        >
          <span className="relative block h-3 w-5">
            <span className={`absolute inset-x-0 top-0 h-px bg-current transition ${open ? 'translate-y-1.5 rotate-45' : ''}`} />
            <span className={`absolute inset-x-0 top-1.5 h-px bg-current transition ${open ? 'opacity-0' : ''}`} />
            <span className={`absolute inset-x-0 top-3 h-px bg-current transition ${open ? '-translate-y-1.5 -rotate-45' : ''}`} />
          </span>
        </button>
      </div>

      {open && (
        <div className="border-t border-white/8 bg-ink-950/97 lg:hidden">
          <nav className="shell flex flex-col py-4">
            {[...LINKS, { to: '/assistant', label: 'Assistant IA' }].map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === '/'}
                className={({ isActive }) =>
                  `border-b border-white/5 py-3 text-sm uppercase tracking-[0.16em] ${
                    isActive ? 'text-gold-400' : 'text-ivory/80'
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
          </nav>
        </div>
      )}
    </header>
  );
}
