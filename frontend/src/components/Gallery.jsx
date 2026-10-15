import { useCallback, useEffect, useState } from 'react';

export default function Gallery({ items, columns = 'md:grid-cols-3' }) {
  const [open, setOpen] = useState(-1);

  const close = useCallback(() => setOpen(-1), []);
  const step = useCallback(
    (d) => setOpen((v) => (v < 0 ? v : (v + d + items.length) % items.length)),
    [items.length]
  );

  useEffect(() => {
    if (open < 0) return;
    const onKey = (e) => {
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowRight') step(1);
      if (e.key === 'ArrowLeft') step(-1);
    };
    window.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [open, close, step]);

  const active = open >= 0 ? items[open] : null;

  return (
    <>
      <div className={`grid gap-4 sm:grid-cols-2 ${columns}`}>
        {items.map((it, idx) => (
          <button
            key={it.file}
            onClick={() => setOpen(idx)}
            className={`group relative overflow-hidden rounded-xl border border-white/8 bg-ink-800 text-left transition duration-500 hover:border-gold-600/40 ${
              idx % 5 === 0 ? 'sm:col-span-2' : ''
            }`}
          >
            <img
              src={it.file}
              alt={it.title.replace('File:', '').replace(/\.[a-z]+$/i, '')}
              loading="lazy"
              className="h-full w-full object-cover transition duration-[1400ms] ease-out group-hover:scale-[1.06]"
              style={{ aspectRatio: idx % 5 === 0 ? '16/9' : '4/3' }}
            />
            <span className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-ink-950 via-ink-950/70 to-transparent p-5 opacity-0 transition duration-500 group-hover:opacity-100">
              <span className="block text-[11px] uppercase tracking-[0.2em] text-gold-500">
                {it.license}
              </span>
              <span className="mt-1.5 block truncate text-sm text-ivory/85">{it.artist}</span>
            </span>
          </button>
        ))}
      </div>

      {active && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-ink-950/95 p-5 backdrop-blur-sm animate-fadeIn"
          onClick={close}
          role="dialog"
          aria-modal="true"
        >
          <img
            src={active.file}
            alt=""
            className="max-h-[82vh] w-auto max-w-full rounded-lg border border-white/10 shadow-glow"
            onClick={(e) => e.stopPropagation()}
          />
          <div className="absolute inset-x-0 bottom-6 mx-auto max-w-2xl px-6 text-center">
            <p className="text-xs uppercase tracking-[0.2em] text-gold-500">{active.license}</p>
            <p className="mt-2 text-sm text-ivory/80">
              Photo : {active.artist} —{' '}
              <a
                href={active.page}
                target="_blank"
                rel="noreferrer noopener"
                className="underline decoration-gold-600/50 underline-offset-4 hover:text-gold-400"
                onClick={(e) => e.stopPropagation()}
              >
                source Wikimedia Commons
              </a>
            </p>
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); step(1); }}
            className="absolute right-5 grid h-12 w-12 place-items-center rounded-full border border-white/15 text-ivory/80 hover:border-gold-600 hover:text-gold-400"
            aria-label="Image suivante"
          >
            →
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); step(-1); }}
            className="absolute left-5 grid h-12 w-12 place-items-center rounded-full border border-white/15 text-ivory/80 hover:border-gold-600 hover:text-gold-400"
            aria-label="Image précédente"
          >
            ←
          </button>
          <button
            onClick={close}
            className="absolute right-5 top-5 grid h-11 w-11 place-items-center rounded-full border border-white/15 text-ivory/70 hover:border-gold-600 hover:text-gold-400"
            aria-label="Fermer"
          >
            ✕
          </button>
        </div>
      )}
    </>
  );
}
