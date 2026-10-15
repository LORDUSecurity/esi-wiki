import { useEffect, useMemo, useState } from 'react';
import PageHeader from '../components/PageHeader';
import Reveal from '../components/Reveal';
import { useApi } from '../lib/api';

const KIND_LABELS = { cours: 'Polycopié', examen: 'Examen', resume: 'Résumé' };

export default function EsiHub() {
  const [tab, setTab] = useState('cours');
  return (
    <>
      <PageHeader
        eyebrow="Sources externes"
        title="Le dépôt EsiHub"
        lead="esihub.net recense les supports d'autres filières et promotions, ainsi que les rapports de PFE soutenus à l'ESI. Les modules sont indexés de S1 à S5 ; S6 est l'année du PFE, sans modules — d'où l'onglet des rapports de stage. Nous avons téléchargé les polycopiés de S3 à S5 : ils sont au catalogue, dans Programmes. Les originaux restent chez eux sur Google Drive, et l'index complet — autres promotions, liens Drive — se consulte ici."
      />

      <div className="shell -mt-10">
        <div className="flex gap-2">
          <TabButton active={tab === 'cours'} onClick={() => setTab('cours')}>
            Cours & annales
          </TabButton>
          <TabButton active={tab === 'pfe'} onClick={() => setTab('pfe')}>
            Rapports de PFE
          </TabButton>
        </div>
      </div>

      {tab === 'cours' ? <CoursesPanel /> : <ReportsPanel />}
    </>
  );
}

function CoursesPanel() {
  const { data: meta } = useApi('/hub/meta/');
  const [branch, setBranch] = useState('');
  const [semester, setSemester] = useState('');
  const [term, setTerm] = useState('');
  const [query, setQuery] = useState('');

  useEffect(() => {
    const t = setTimeout(() => setQuery(term.trim()), 320);
    return () => clearTimeout(t);
  }, [term]);

  const path = useMemo(() => {
    const p = new URLSearchParams();
    if (branch) p.set('branch', branch);
    if (semester) p.set('semester', semester);
    if (query) p.set('search', query);
    return `/hub/courses/${p.toString() ? `?${p}` : ''}`;
  }, [branch, semester, query]);

  const { data: courses, loading } = useApi(path);

  return (
    <>
      <div className="shell sticky top-[68px] z-30 -mt-6 pb-2 pt-6">
        <div className="card flex flex-col gap-4 p-5 backdrop-blur-xl xl:flex-row xl:items-center">
          <Chips
            options={(meta?.branches || []).map((b) => ({ value: b.code, label: b.code }))}
            active={branch}
            onSelect={setBranch}
            allLabel="Toutes filières"
          />
          <div className="flex flex-wrap gap-2 xl:border-l xl:border-white/8 xl:pl-4">
            <Chip active={!semester} onClick={() => setSemester('')}>
              S1–S5
            </Chip>
            {(meta?.semesters || []).map((s) => (
              <Chip key={s.code} active={semester === s.code} onClick={() => setSemester(s.code)}>
                {s.code}
              </Chip>
            ))}
            <span className="cursor-not-allowed rounded-full border border-dashed border-white/12 px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-muted/60">
              S6 · année PFE, sans modules
            </span>
          </div>
          <input
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="Rechercher un module…"
            className="w-full rounded-full border border-white/12 bg-ink-900/80 px-5 py-2.5 text-sm text-ivory outline-none transition placeholder:text-muted/70 focus:border-gold-600/60 xl:ml-auto xl:w-64"
          />
        </div>
      </div>

      <section className="shell py-14">
        <Counter loading={loading} count={courses?.length} query={query} />

        {/* One reveal for the whole grid: 374 cards would otherwise each carry an observer. */}
        <Reveal>
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {(courses || []).map((c) => (
              <CourseCard key={c.id} course={c} />
            ))}
          </div>
        </Reveal>

        {!loading && courses?.length === 0 && <Empty />}
      </section>
    </>
  );
}

function ReportsPanel() {
  const { data: meta } = useApi('/hub/meta/');
  const [promotion, setPromotion] = useState('');
  const [term, setTerm] = useState('');
  const [query, setQuery] = useState('');

  useEffect(() => {
    const t = setTimeout(() => setQuery(term.trim()), 320);
    return () => clearTimeout(t);
  }, [term]);

  const path = useMemo(() => {
    const p = new URLSearchParams();
    if (promotion) p.set('promotion', promotion);
    if (query) p.set('search', query);
    return `/hub/reports/${p.toString() ? `?${p}` : ''}`;
  }, [promotion, query]);

  const { data: reports, loading } = useApi(path);

  return (
    <>
      <div className="shell -mt-6 py-8">
        <div className="card flex flex-col gap-4 p-5 backdrop-blur-xl lg:flex-row lg:items-center">
          <Chips
            options={(meta?.promotions || []).map((p) => ({ value: p, label: p }))}
            active={promotion}
            onSelect={setPromotion}
            allLabel="Toutes promotions"
          />
          <input
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="Sujet, auteur, organisme…"
            className="w-full rounded-full border border-white/12 bg-ink-900/80 px-5 py-2.5 text-sm text-ivory outline-none transition placeholder:text-muted/70 focus:border-gold-600/60 lg:ml-auto lg:w-80"
          />
        </div>

        <Counter loading={loading} count={reports?.length} query={query} />

        <Reveal>
          <div className="grid gap-5 lg:grid-cols-2">
            {(reports || []).map((r) => (
              <ReportCard key={r.id} report={r} />
            ))}
          </div>
        </Reveal>

        {!loading && reports?.length === 0 && <Empty />}
      </div>
    </>
  );
}

function CourseCard({ course }) {
  return (
    <article className="card flex h-full flex-col p-6">
      <div className="mb-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-muted">
        <span className="rounded border border-gold-600/40 px-2 py-0.5 text-gold-400">{course.branch}</span>
        <span>{course.semester}</span>
        {course.year && <span>· {course.year}</span>}
      </div>

      <h3 className="font-display text-[22px] leading-snug text-ivory">{course.title}</h3>

      <div className="mt-4 flex flex-wrap gap-2 pt-3">
        {Object.entries(course.links).map(([kind, url]) => (
          <a
            key={kind}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-ghost !px-3.5 !py-2 !text-[11px]"
          >
            {KIND_LABELS[kind] || kind} <span aria-hidden>↗</span>
          </a>
        ))}
      </div>
    </article>
  );
}

function ReportCard({ report }) {
  return (
    <article className="card flex h-full flex-col p-7">
      <div className="mb-3 flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-muted">
        {report.promotion && <span className="rounded border border-gold-600/40 px-2 py-0.5 text-gold-400">PFE {report.promotion}</span>}
        {report.language && <span>· {report.language}</span>}
      </div>

      <h3 className="font-display text-[24px] leading-snug text-ivory">{report.title}</h3>

      <p className="mt-3 text-sm text-ivory/70">
        {report.engineer}
        {report.organisation && (
          <>
            <span className="text-muted"> — </span>
            {report.organisation}
          </>
        )}
      </p>

      {report.abstract && (
        <p className="mt-4 line-clamp-4 text-[13px] leading-relaxed text-muted">{report.abstract}</p>
      )}

      {report.tags?.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5">
          {report.tags.slice(0, 5).map((t) => (
            <span key={t} className="rounded-full border border-white/12 px-2.5 py-1 text-[10px] text-ivory/60">
              {t}
            </span>
          ))}
        </div>
      )}

      <div className="mt-auto flex flex-wrap gap-2 pt-5">
        {report.report_url ? (
          <a href={report.report_url} target="_blank" rel="noopener noreferrer" className="btn-gold !px-4 !py-2 !text-[11px]">
            Lire le rapport <span aria-hidden>↗</span>
          </a>
        ) : (
          <span className="text-[11px] uppercase tracking-[0.16em] text-muted">PDF non publié</span>
        )}
        {report.page && (
          <a href={report.page} target="_blank" rel="noopener noreferrer" className="btn-ghost !px-4 !py-2 !text-[11px]">
            Fiche EsiHub <span aria-hidden>↗</span>
          </a>
        )}
      </div>
    </article>
  );
}

function Chips({ options, active, onSelect, allLabel }) {
  return (
    <div className="flex flex-wrap gap-2">
      <Chip active={!active} onClick={() => onSelect('')}>
        {allLabel}
      </Chip>
      {options.map((o) => (
        <Chip key={o.value} active={active === o.value} onClick={() => onSelect(o.value)}>
          {o.label}
        </Chip>
      ))}
    </div>
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

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`border-b-2 px-5 py-3 text-[12px] uppercase tracking-[0.18em] transition ${
        active ? 'border-gold-500 text-gold-400' : 'border-white/8 text-ivory/60 hover:text-ivory'
      }`}
    >
      {children}
    </button>
  );
}

function Counter({ loading, count, query }) {
  return (
    <p className="mb-7 mt-7 text-[12px] uppercase tracking-[0.2em] text-muted">
      {loading ? 'Chargement…' : `${count ?? 0} résultat(s)`}
      {query && !loading && ` pour « ${query} »`}
    </p>
  );
}

function Empty() {
  return (
    <div className="card p-14 text-center">
      <p className="font-display text-3xl text-ivory/80">Aucun résultat</p>
      <p className="mt-3 text-sm text-muted">Changez de filière, de semestre ou de terme recherché.</p>
    </div>
  );
}
