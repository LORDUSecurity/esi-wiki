import { useMemo, useState } from 'react';
import PageHeader from '../components/PageHeader';
import Reveal from '../components/Reveal';
import { useApi } from '../lib/api';

export default function Faq() {
  const { data: groups, loading } = useApi('/faqs/');
  const [term, setTerm] = useState('');
  const [open, setOpen] = useState(null);

  const filtered = useMemo(() => {
    const t = term.trim().toLowerCase();
    if (!t) return groups || [];
    return (groups || [])
      .map((g) => ({
        ...g,
        items: g.items.filter(
          (i) => i.question.toLowerCase().includes(t) || i.answer.toLowerCase().includes(t)
        ),
      }))
      .filter((g) => g.items.length);
  }, [groups, term]);

  const total = (groups || []).reduce((n, g) => n + g.items.length, 0);

  return (
    <>
      <PageHeader
        eyebrow="Règlement pédagogique"
        title="Questions fréquentes"
        lead="Validation des modules, mentions, stages, absences, fraude : ce que le règlement dit réellement, sans interprétation."
        image={undefined}
      />

      <section className="shell py-16">
        <div className="relative max-w-xl">
          <input
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="Rechercher : mention, rattrapage, absence…"
            className="w-full rounded-full border border-white/12 bg-ink-800/70 px-6 py-4 text-sm text-ivory outline-none transition placeholder:text-muted/70 focus:border-gold-600/60 focus:shadow-[0_0_30px_-12px_rgba(212,175,103,.6)]"
          />
          <span className="pointer-events-none absolute right-6 top-1/2 -translate-y-1/2 text-gold-600">
            ⌕
          </span>
        </div>

        <p className="mt-6 text-[12px] uppercase tracking-[0.2em] text-muted">
          {loading ? 'Chargement…' : `${total} réponses`}
        </p>

        <div className="mt-12 space-y-14">
          {filtered.map((g) => (
            <div key={g.category}>
              <h2 className="border-b border-white/10 pb-4 font-display text-3xl text-gold-500">
                {g.label}
              </h2>
              <div className="mt-2 divide-y divide-white/7">
                {g.items.map((f) => {
                  const id = `${g.category}-${f.id}`;
                  const isOpen = open === id;
                  return (
                    <div key={f.id}>
                      <button
                        onClick={() => setOpen(isOpen ? null : id)}
                        aria-expanded={isOpen}
                        className="flex w-full items-center justify-between gap-6 py-6 text-left transition hover:text-gold-400"
                      >
                        <span className="text-[17px] leading-snug text-ivory/90">{f.question}</span>
                        <span
                          className={`shrink-0 text-xl text-gold-600 transition duration-300 ${
                            isOpen ? 'rotate-45' : ''
                          }`}
                        >
                          +
                        </span>
                      </button>
                      <div
                        className="grid transition-all duration-500 ease-out"
                        style={{ gridTemplateRows: isOpen ? '1fr' : '0fr' }}
                      >
                        <div className="overflow-hidden">
                          <Reveal className="pb-7 pr-10 text-[15px] leading-relaxed text-muted">
                            {f.answer}
                          </Reveal>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {!loading && filtered.length === 0 && (
            <p className="py-20 text-center font-display text-3xl text-muted">
              Rien ne correspond à « {term} ».
            </p>
          )}
        </div>
      </section>
    </>
  );
}
