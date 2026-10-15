import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import { useApi, useChat } from '../lib/api';

const SUGGESTIONS = [
  'Comment valider un module ?',
  'Quelle mention pour 17/20 ?',
  'Que contient le module Réseaux sans fils ?',
  'Combien de documents en Programmation Python ?',
  'Les règles d\'absence en cas d\'examen',
];

const MODE_LABEL = {
  corpus: 'polycopiés indexés du wiki',
  keyless: 'modèle sans clé',
  provider: 'modèle configuré côté serveur',
  local: 'base de données locale',
};

// Which lane answered is a claim the site has to be able to prove, so a named provider is
// credited by name — 'Gemini', 'NVIDIA', 'OpenRouter', 'OpenAI' — and never as a generic route.
// The tier is stated per provider because they are not all free: OpenAI bills per token, so a
// blanket "(gratuit)" would be a claim this site cannot make.
const PAID_PROVIDERS = new Set(['OpenAI']);
const tierLabel = (m) =>
  m?.mode === 'provider' && m.provider
    ? `modèle ${m.provider}${PAID_PROVIDERS.has(m.provider) ? ' (payant)' : ' (gratuit)'}`
    : MODE_LABEL[m?.mode] ?? 'prêt';

const lastAnswer = (messages) => [...messages].reverse().find((m) => m.role === 'assistant');

export default function Assistant() {
  const [params] = useSearchParams();
  const { messages, send, busy, error, reset } = useChat();
  const [text, setText] = useState('');
  const endRef = useRef(null);
  const asked = useRef(false);

  useEffect(() => {
    const q = params.get('q');
    if (q && !asked.current) {
      asked.current = true;
      send(`Donne un aperçu du module ${q}.`);
    }
  }, [params, send]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, busy]);

  function submit(e) {
    e.preventDefault();
    if (!text.trim()) return;
    send(text);
    setText('');
  }

  const { data: stats } = useApi('/stats/');

  return (
    <>
      <PageHeader
        eyebrow="Assistant"
        title="Posez une question au wiki"
        lead={
          stats?.corpus_documents
            ? `Réponses ancrées dans le catalogue, le règlement et ${stats.corpus_documents} polycopiés indexés sur cette machine, du dépôt et d'EsiHub (${stats.corpus_chunks} extraits). Les chiffres viennent des tables, les définitions des documents — un modèle ne fait que rédiger.`
            : "Réponses construites à partir du catalogue de modules, des documents et du règlement chargés dans la base. Sans clé API, l'assistant répond directement depuis la base : les chiffres viennent des tables, jamais d'un modèle."
        }
      />

      <section className="shell py-16">
        <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
          <div className="card flex h-[68vh] min-h-[520px] flex-col">
            <div className="flex items-center justify-between border-b border-white/8 px-6 py-4">
              <div className="flex items-center gap-3">
                <span className="relative grid h-9 w-9 place-items-center rounded-full border border-gold-600/45 text-gold-500">
                  ✦
                  <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-emerald-400" />
                </span>
                <div>
                  <p className="text-sm text-ivory">Assistant ESI</p>
                  <p className="text-[11px] uppercase tracking-[0.16em] text-muted">
                    {busy
                      ? 'en train de répondre…'
                      : tierLabel(lastAnswer(messages))}
                  </p>
                </div>
              </div>
              {messages.length > 0 && (
                <button onClick={reset} className="text-[11px] uppercase tracking-[0.16em] text-muted transition hover:text-gold-400">
                  Nouvelle conversation
                </button>
              )}
            </div>

            <div className="flex-1 space-y-5 overflow-y-auto px-6 py-6">
              {messages.length === 0 && (
                <div className="grid h-full place-items-center text-center">
                  <div>
                    <p className="font-display text-3xl text-ivory/80">Par quoi on commence ?</p>
                    <div className="mt-8 flex flex-wrap justify-center gap-2">
                      {SUGGESTIONS.map((s) => (
                        <button
                          key={s}
                          onClick={() => send(s)}
                          className="rounded-full border border-white/12 px-4 py-2 text-[12.5px] text-ivory/70 transition hover:border-gold-600/60 hover:text-gold-400"
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[78%] whitespace-pre-wrap rounded-2xl px-5 py-3.5 text-[14.5px] leading-relaxed animate-fadeUp ${
                      m.role === 'user'
                        ? 'rounded-br-md bg-gold-600 text-ink-950'
                        : 'rounded-bl-md border border-white/10 bg-ink-700/80 text-ivory/90'
                    }`}
                  >
                    {m.content}
                    {m.role === 'assistant' && (m.note || m.sources?.length) && (
                      <span className="mt-3 block space-y-1 border-t border-white/8 pt-2 text-[11.5px] text-muted">
                        {m.note && <span className="block">⚠ {m.note}</span>}
                        {m.sources?.length > 0 && (
                          <span className="block">
                            {m.mode === 'corpus' || m.mode === 'local' ? 'Sources : ' : 'Polycopiés les plus proches : '}
                            {m.sources.join(' · ')}
                          </span>
                        )}
                      </span>
                    )}
                  </div>
                </div>
              ))}

              {busy && (
                <div className="flex justify-start">
                  <div className="flex gap-1.5 rounded-2xl rounded-bl-md border border-white/10 bg-ink-700/80 px-5 py-4">
                    {[0, 150, 300].map((d) => (
                      <span
                        key={d}
                        className="h-1.5 w-1.5 animate-drift rounded-full bg-gold-500"
                        style={{ animationDelay: `${d}ms` }}
                      />
                    ))}
                  </div>
                </div>
              )}

              <div ref={endRef} />
            </div>

            {error && (
              <p className="border-t border-rose-500/25 bg-rose-500/8 px-6 py-3 text-[13px] text-rose-200">
                {error}
              </p>
            )}

            <form onSubmit={submit} className="flex items-center gap-3 border-t border-white/8 px-6 py-5">
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Votre question…"
                className="flex-1 rounded-full border border-white/12 bg-ink-900/80 px-5 py-3 text-sm text-ivory outline-none transition placeholder:text-muted/60 focus:border-gold-600/60"
              />
              <button
                type="submit"
                disabled={busy || !text.trim()}
                className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-gold-600 text-ink-950 transition hover:bg-gold-400 disabled:opacity-40"
                aria-label="Envoyer"
              >
                →
              </button>
            </form>
          </div>

          <aside className="space-y-6">
            <div className="card p-6">
              <h3 className="eyebrow">Fonctionnement</h3>
              <p className="mt-4 text-[13.5px] leading-relaxed text-muted">
                Quatre niveaux, dans l'ordre : la base de données pour les chiffres et le
                règlement, les polycopiés EsiHub indexés sur la machine pour les définitions, puis
                un modèle qui ne fait que rédiger — Gemini, NVIDIA, OpenRouter ou OpenAI selon
                les clés posées côté serveur, chacun avec ses propres modèles, les trois premiers
                sur leur niveau gratuit et OpenAI en dernier car il facture à l'usage, et un
                endpoint public sans clé quand aucune clé n'est là. Aucun chiffre ne sort
                d'un modèle : nombre de modules, de documents, note ou seuil viennent des tables.
                Chaque réponse indique qui a parlé et les fichiers cités.
              </p>
            </div>
            <div className="card p-6">
              <h3 className="eyebrow">Limite assumée</h3>
              <p className="mt-4 text-[13.5px] leading-relaxed text-muted">
                Si la base ne couvre pas la question, l'assistant est censé le dire. Un chiffre
                important — note, date, règle — doit être vérifié dans le document d'origine.
              </p>
            </div>
            <div className="card p-6">
              <h3 className="eyebrow">Raccourcis</h3>
              <ul className="mt-4 space-y-2 text-[13.5px]">
                {SUGGESTIONS.slice(0, 3).map((s) => (
                  <li key={s}>
                    <button onClick={() => send(s)} className="text-left text-ivory/70 transition hover:text-gold-400">
                      — {s}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </section>
    </>
  );
}
