import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import ModuleCard from '../components/ModuleCard';
import Reveal from '../components/Reveal';
import { useApi } from '../lib/api';

export default function Programmes() {
  const [params] = useSearchParams();
  const [semester, setSemester] = useState(params.get('semestre') || '');
  const [bloc, setBloc] = useState(params.get('bloc') || '');
  const [branch, setBranch] = useState(params.get('filiere') || '');
  const [term, setTerm] = useState('');
  const [query, setQuery] = useState('');

  useEffect(() => {
    const t = setTimeout(() => setQuery(term.trim()), 320);
    return () => clearTimeout(t);
  }, [term]);

  const { data: semesters } = useApi('/semesters/');
  const { data: stats } = useApi('/stats/');
  const path = useMemo(() => {
    const p = new URLSearchParams();
    if (semester) p.set('semester', semester);
    if (bloc !== '') p.set('block', bloc);
    if (branch) p.set('branch', branch);
    if (query) p.set('search', query);
    return `/modules/${p.toString() ? `?${p}` : ''}`;
  }, [semester, bloc, branch, query]);

  const { data: modules, loading } = useApi(path);
  const branches = stats?.branches || [];

  return (
    <>
      <PageHeader
        eyebrow="Catalogue"
        title="Programmes & documents"
        lead="Les cinq semestres du cycle ingénieur sont au catalogue : S1 et S2 viennent du dépôt de cours, S3 à S5 des polycopiés relevés sur EsiHub. Chaque document s'ouvre depuis ce site, ou depuis son Drive d'origine quand la copie locale n'est pas là. S6 est l'année du PFE, sans modules — les rapports de stage restent sur l'onglet EsiHub."
      />

      <div className="shell sticky top-[68px] z-30 -mt-10 pb-2">
        <div className="card flex flex-col gap-4 p-5 backdrop-blur-xl md:flex-row md:items-center">
          <div className="flex flex-1 flex-wrap gap-2">
            <Chip active={!semester} onClick={() => setSemester('')}>
              Tous
            </Chip>
            {(semesters || []).map((s) => (
              <Chip key={s.code} active={semester === s.code} onClick={() => setSemester(s.code)}>
                {s.title}
              </Chip>
            ))}
          </div>

          <div className="flex flex-wrap gap-2 md:border-l md:border-white/8 md:pl-4">
            {['', 1, 2, 3, 4, 5, 6, 7, 8, 0].map((b) => (
              <Chip key={b} active={String(bloc) === String(b)} onClick={() => setBloc(b)}>
                {b === '' ? 'Blocs' : b === 0 ? 'Divers' : b}
              </Chip>
            ))}
          </div>

          {branches.length > 0 && (
            <div className="flex flex-wrap gap-2 md:border-l md:border-white/8 md:pl-4">
              {branches.map((b) => (
                <Chip
                  key={b.code}
                  active={branch === b.code}
                  onClick={() => setBranch(branch === b.code ? '' : b.code)}
                >
                  {b.code}
                </Chip>
              ))}
            </div>
          )}

          <div className="relative md:w-64 md:border-l md:border-white/8 md:pl-4">
            <input
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              placeholder="Rechercher un module ou un document…"
              className="w-full rounded-full border border-white/12 bg-ink-900/80 px-5 py-2.5 text-sm text-ivory outline-none transition placeholder:text-muted/70 focus:border-gold-600/60"
            />
          </div>
        </div>
      </div>

      <section className="shell py-16">
        <p className="mb-8 text-[12px] uppercase tracking-[0.2em] text-muted">
          {loading ? 'Chargement…' : `${modules?.length ?? 0} module(s)`}
          {branch && !loading && ` · filière ${branch}`}
          {query && !loading && ` pour « ${query} »`}
        </p>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {(modules || []).map((m, i) => (
            <Reveal key={m.slug} delay={(i % 3) * 70}>
              <ModuleCard module={m} index={i} />
            </Reveal>
          ))}
        </div>

        {!loading && modules?.length === 0 && (
          <div className="card p-14 text-center">
            <p className="font-display text-3xl text-ivory/80">Aucun module ne correspond</p>
            <p className="mt-3 text-sm text-muted">
              Essayez un autre terme, ou retirez le filtre de bloc ou de filière.
            </p>
          </div>
        )}
      </section>
    </>
  );
}

function Chip({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full border px-4 py-2 text-[11px] uppercase tracking-[0.16em] transition ${
        active
          ? 'border-gold-600 bg-gold-600/12 text-gold-400'
          : 'border-white/12 text-ivory/65 hover:border-white/28 hover:text-ivory'
      }`}
    >
      {children}
    </button>
  );
}
