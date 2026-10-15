import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import Reveal from '../components/Reveal';
import { KindBadge } from '../components/ModuleCard';
import { useApi } from '../lib/api';

const KIND_LABEL = {
  '': 'Tout',
  cours: 'Cours',
  tp: 'TP',
  td: 'TD',
  exam: 'Examens',
  resume: 'Résumés',
  autre: 'Autres',
};

const HUB_KINDS = { cours: 'Polycopié', examen: 'Examen', resume: 'Résumé' };

export default function ModuleDetail() {
  const { slug } = useParams();
  const { data: mod, error, loading } = useApi(`/modules/${slug}/`);
  const [kind, setKind] = useState('');

  const groups = useMemo(() => {
    const all = mod?.resources || [];
    const filtered = kind ? all.filter((r) => r.kind === kind) : all;
    const byKind = {};
    for (const r of filtered) (byKind[r.kind] ||= []).push(r);
    return byKind;
  }, [mod, kind]);

  if (loading) {
    return (
      <PageHeader eyebrow="Module" title="Chargement…" />
    );
  }

  if (error || !mod) {
    return (
      <div className="shell grid min-h-[70vh] place-items-center py-32 text-center">
        <div>
          <p className="eyebrow">Introuvable</p>
          <h1 className="mt-4 font-display text-5xl">{error?.message || 'Module inconnu'}</h1>
          <Link to="/programmes" className="btn-gold mt-9">
            Retour au catalogue
          </Link>
        </div>
      </div>
    );
  }

  const counts = (mod.resources || []).reduce((a, r) => ((a[r.kind] = (a[r.kind] || 0) + 1), a), {});

  return (
    <>
      <PageHeader
        eyebrow={[
          mod.semester,
          mod.branch,
          mod.block ? `Bloc ${mod.block}` : null,
          mod.origin === 'esihub' ? 'Corpus EsiHub' : null,
        ]
          .filter(Boolean)
          .join(' · ')}
        title={`${mod.code} — ${mod.title}`}
        lead={mod.summary}
      />

      <section className="shell py-16">
        <div className="flex flex-wrap items-center gap-2">
          {Object.keys(KIND_LABEL).map((k) => (
            <button
              key={k}
              onClick={() => setKind(k)}
              disabled={k !== '' && !counts[k]}
              className={`rounded-full border px-4 py-2 text-[11px] uppercase tracking-[0.16em] transition disabled:cursor-not-allowed disabled:opacity-30 ${
                kind === k
                  ? 'border-gold-600 bg-gold-600/12 text-gold-400'
                  : 'border-white/12 text-ivory/65 hover:border-white/28'
              }`}
            >
              {KIND_LABEL[k]}
              {k && counts[k] ? ` (${counts[k]})` : ''}
            </button>
          ))}
        </div>

        {Object.entries(groups).map(([k, items]) => (
          <div key={k} className="mt-14">
            <h2 className="font-display text-3xl text-ivory/90">{KIND_LABEL[k] || k}</h2>
            <div className="mt-6 divide-y divide-white/7 border-y border-white/7">
              {items.map((r, i) => (
                <Reveal key={r.id} delay={Math.min(i, 8) * 40} as="div">
                  <a
                    href={encodeURI(r.url)}
                    target="_blank"
                    rel="noreferrer"
                    className="group flex items-center gap-5 py-5 transition hover:bg-white/3"
                  >
                    <span className="grid h-12 w-12 shrink-0 place-items-center rounded-md border border-white/10 bg-ink-800 text-[10px] font-semibold uppercase tracking-wider text-gold-500 transition group-hover:border-gold-600/60">
                      {r.file_type || 'doc'}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[15.5px] text-ivory/90 group-hover:text-gold-400">
                        {r.title}
                      </span>
                      <span className="mt-1 block text-[12px] text-muted">
                        {r.size_kb >= 1024
                          ? `${(r.size_kb / 1024).toFixed(1)} MB`
                          : `${r.size_kb} KB`}
                        {' · '}
                        {r.path
                          .split('/')
                          .slice(1)
                          .filter((seg) => seg !== 'module')
                          .join(' / ')}
                      </span>
                    </span>
                    <span className="shrink-0 text-[11px] uppercase tracking-[0.18em] text-muted transition group-hover:text-gold-500">
                      {r.is_local === false ? 'Drive ↗' : 'Ouvrir →'}
                    </span>
                  </a>
                </Reveal>
              ))}
            </div>
          </div>
        ))}

        {mod.hub_references?.length > 0 && (
          <div className="mt-14">
            <h2 className="font-display text-3xl text-ivory/90">Aussi sur EsiHub</h2>
            <p className="mt-2 text-sm text-muted">
              Le même code de module, tel qu'indexé par d'autres filières — les fichiers
              ouvrent sur le Google Drive d'EsiHub.
            </p>
            <div className="mt-6 space-y-3">
              {mod.hub_references.map((ref) => (
                <div key={ref.id} className="card flex flex-wrap items-center gap-x-4 gap-y-2 px-5 py-4">
                  <span className="rounded border border-gold-600/40 px-2 py-0.5 text-[10px] uppercase tracking-[0.2em] text-gold-400">
                    {ref.branch}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-[15px] text-ivory/85">{ref.title}</span>
                  {ref.year && <span className="text-[11px] uppercase tracking-[0.16em] text-muted">{ref.year}</span>}
                  <span className="flex flex-wrap gap-2">
                    {Object.entries(ref.links).map(([k, url]) => (
                      <a
                        key={k}
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-ghost !px-3 !py-1.5 !text-[10px]"
                      >
                        {HUB_KINDS[k] || k} <span aria-hidden>↗</span>
                      </a>
                    ))}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-16 flex flex-wrap gap-4">
          <Link to="/programmes" className="btn-ghost">
            ← Autres modules
          </Link>
          <Link to="/esihub" className="btn-ghost">
            Dépôt EsiHub
          </Link>
          <Link to={`/assistant?q=${encodeURIComponent(`${mod.code} ${mod.title}`)}`} className="btn-gold">
            Questionner l'assistant
          </Link>
        </div>
      </section>
    </>
  );
}
