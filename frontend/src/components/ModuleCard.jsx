import { Link } from 'react-router-dom';

const KIND_DOT = {
  cours: 'bg-sky-400/80',
  tp: 'bg-emerald-400/80',
  td: 'bg-amber-400/80',
  exam: 'bg-rose-400/80',
  resume: 'bg-violet-400/80',
  autre: 'bg-slate-400/70',
};

export function KindBadge({ kind }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-ivory/70">
      <span className={`h-1.5 w-1.5 rounded-full ${KIND_DOT[kind] || KIND.autre}`} />
      {kind}
    </span>
  );
}

export default function ModuleCard({ module, index = 0 }) {
  return (
    <Link
      to={`/programmes/${module.slug}`}
      className="card group flex h-full flex-col p-7 transition duration-500 hover:-translate-y-1.5 hover:border-gold-600/45 hover:shadow-glow"
    >
      <div className="flex items-start justify-between gap-4">
        <span className="font-display text-[42px] leading-none text-gold-600/85 transition group-hover:text-gold-400">
          {module.code}
        </span>
        <span className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] uppercase tracking-[0.16em] text-muted">
          {module.branch ? `${module.branch} · ${module.semester_code}` : module.semester_code}
        </span>
      </div>

      <h3 className="mt-5 font-display text-[26px] font-light leading-tight text-ivory">
        {module.title}
      </h3>

      <p className="mt-3 flex-1 text-[13.5px] leading-relaxed text-muted line-clamp-3">
        {module.summary || `Bloc ${module.block} — ${module.resource_count} documents.`}
      </p>

      <div className="mt-6 flex items-center justify-between border-t border-white/7 pt-4 text-[11px] uppercase tracking-[0.16em]">
        <span className="text-ivory/60">{module.resource_count} documents</span>
        <span className="text-gold-500 transition group-hover:translate-x-1">Ouvrir →</span>
      </div>
    </Link>
  );
}

export { KIND_DOT };
