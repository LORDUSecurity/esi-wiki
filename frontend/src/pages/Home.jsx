import { Link } from 'react-router-dom';
import Hero from '../components/Hero';
import Reveal from '../components/Reveal';
import SectionHeading from '../components/SectionHeading';
import ModuleCard from '../components/ModuleCard';
import { useApi } from '../lib/api';
import { byTopic } from '../lib/media';

const BLOCKS = [
  [1, 'Fondamentaux informatiques'],
  [2, 'Mathématiques'],
  [3, 'Programmation'],
  [4, 'Documentation & GED'],
  [5, 'Réseaux & web'],
  [6, 'Savoir & optimisation'],
  [7, 'Économie & gestion'],
  [8, 'Communication & langues'],
];

const CAMPUS = [...byTopic('library').slice(0, 2), ...byTopic('students').slice(0, 1), ...byTopic('campus').slice(0, 1)];

export default function Home() {
  const { data: stats } = useApi('/stats/');
  const { data: majors } = useApi('/majors/');
  const { data: modules } = useApi('/modules/');
  const { data: faqs } = useApi('/faqs/');
  const { data: hub } = useApi('/hub/meta/');

  const featured = (modules || []).filter((m) => ['3.2', '5.1', '1.2', '3.1', '4.2', '6.1'].includes(m.code) || m.code === '1.1').slice(0, 6);
  const marquee = (modules || []).map((m) => `${m.code} ${m.title}`);

  return (
    <>
      <Hero stats={stats} />

      {marquee.length > 0 && (
        <div className="relative overflow-hidden border-y border-white/8 bg-ink-900 py-4">
          {/* One entry per 2.5 seconds, whatever the catalogue holds: a fixed 38s over 104 module
              names read as a blur (1.2s per name on a laptop), and the strip is here to be read. */}
          <div
            className="flex w-max animate-marquee gap-10 whitespace-nowrap hover:[animation-play-state:paused]"
            style={{ animationDuration: `${Math.max(marquee.length * 2.5, 60)}s` }}
          >
            {[...marquee, ...marquee].map((t, i) => (
              <span key={i} className="text-[12px] uppercase tracking-[0.22em] text-muted">
                {t} <span className="text-gold-700">◆</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Filières */}
      <section className="shell py-28">
        <SectionHeading
          eyebrow="Quatre filières"
          title="Choisir sa spécialité, sans paraphrase"
          lead="Chaque filière structure les six semestres du cycle ingénieur : les mêmes socles, des prolongements très différents vers le métier."
          action={
            <Link to="/programmes" className="btn-ghost">
              Tous les modules
            </Link>
          }
        />
        <div className="mt-14 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {(majors || []).map((m, i) => (
            <Reveal key={m.code} delay={i * 90}>
              <article className="card group h-full p-8 transition duration-500 hover:-translate-y-1.5 hover:border-gold-600/45">
                <p className="font-display text-[34px] text-gold-600 transition group-hover:text-gold-400">
                  {m.code}
                </p>
                <h3 className="mt-4 text-[19px] font-normal leading-snug text-ivory">{m.name}</h3>
                <p className="mt-3 text-[13.5px] leading-relaxed text-muted">{m.tagline}</p>
                <ul className="mt-6 space-y-1.5 border-t border-white/7 pt-5 text-[12.5px] text-ivory/65">
                  {(m.career_paths || []).slice(0, 3).map((c) => (
                    <li key={c} className="flex gap-2">
                      <span className="text-gold-700">—</span>
                      {c}
                    </li>
                  ))}
                </ul>
              </article>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Blocs */}
      <section className="relative overflow-hidden bg-ink-900 py-28">
        <div className="shell">
          <SectionHeading
            eyebrow="Organisation"
            title="Huit blocs, six semestres"
            lead="Le cycle ingénieur court de S1 à S6. Les cinq semestres de cours sont ici, documents à l'appui : le dépôt porte S1 et S2, le corpus miroir d'EsiHub couvre S3 à S5 pour les filières ICSD, IDC, IIN, ISITD et ISSIC. Filtrez par semestre, par bloc ou par filière."
          />
          <div className="mt-14 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {BLOCKS.map(([n, label], i) => (
              <Reveal key={n} delay={i * 60}>
                <Link
                  to={`/programmes?bloc=${n}`}
                  className="group flex items-center gap-4 rounded-lg border border-white/8 bg-ink-800/50 px-5 py-5 transition hover:border-gold-600/45 hover:bg-ink-700/60"
                >
                  <span className="font-display text-3xl text-gold-600/80 group-hover:text-gold-400">
                    {n}
                  </span>
                  <span className="text-[13px] uppercase tracking-[0.13em] text-ivory/75">
                    {label}
                  </span>
                </Link>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Modules phares */}
      <section className="shell py-28">
        <SectionHeading
          eyebrow="Ressources"
          title="Les modules les plus consultés"
          lead="Polycopiés, fiches de TP, TD et sujets d'examen rattachés à chaque module."
          action={
            <Link to="/programmes" className="btn-ghost">
              Voir les {modules?.length ?? '—'} modules
            </Link>
          }
        />
        <div className="mt-14 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {featured.map((m, i) => (
            <Reveal key={m.slug} delay={(i % 3) * 90}>
              <ModuleCard module={m} />
            </Reveal>
          ))}
        </div>
      </section>

      {/* EsiHub */}
      {hub && (
        <section className="relative overflow-hidden bg-ink-900 py-28">
          <div className="shell grid gap-14 lg:grid-cols-[1.15fr_1fr] lg:items-center">
            <Reveal>
              <p className="eyebrow">Dépôt communautaire</p>
              <h2 className="mt-5 font-display text-[clamp(2rem,4.2vw,3.2rem)] font-light leading-[1.08] text-ivory">
                {hub.courses} modules indexés chez EsiHub, {stats?.mirrored_documents ?? 0}{' '}
                documents déjà copiés ici
              </h2>
              <p className="mt-6 max-w-xl text-[15px] leading-relaxed text-muted">
                EsiHub rassemble les polycopiés, examens et résumés des six filières sur cinq des
                six semestres du cycle, ainsi que les rapports de PFE soutenus depuis 2016. Nous
                avons téléchargé ceux de S3 à S5 : ils s'ouvrent maintenant depuis le catalogue du
                wiki. Le reste de l'index — autres promotions, rapports de PFE — reste sur son
                Google Drive et nous vous y menons.
              </p>
              <div className="mt-9 flex flex-wrap gap-4">
                <Link to="/esihub" className="btn-gold">
                  Explorer EsiHub
                </Link>
                <Link to="/esihub" className="btn-ghost">
                  Rapports de PFE
                </Link>
              </div>
            </Reveal>

            <Reveal delay={120}>
              <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-white/8 bg-white/8">
                {[
                  [hub.courses, 'modules'],
                  [hub.drive_links, 'liens Drive'],
                  [hub.branches?.length ?? 0, 'filières'],
                  [hub.reports, 'rapports de PFE'],
                ].map(([n, label]) => (
                  <div key={label} className="bg-ink-900 px-7 py-9">
                    <dt className="font-display text-[40px] leading-none text-gold-500">{n}</dt>
                    <dd className="mt-3 text-[11px] uppercase tracking-[0.2em] text-muted">{label}</dd>
                  </div>
                ))}
              </dl>
            </Reveal>
          </div>
        </section>
      )}

      {/* Campus strip */}
      <section className="relative overflow-hidden">
        <div className="grid gap-1 sm:grid-cols-2 lg:grid-cols-4">
          {CAMPUS.map((shot, i) => (
            <Link to="/campus" key={shot.file} className="group relative h-[300px] overflow-hidden lg:h-[420px]">
              <img
                src={shot.file}
                alt=""
                loading="lazy"
                className="h-full w-full object-cover transition duration-[1600ms] ease-out group-hover:scale-110"
              />
              <span className="absolute inset-0 bg-gradient-to-t from-ink-950/90 via-ink-950/25 to-transparent" />
              <span className="absolute bottom-6 left-6 right-6 translate-y-3 opacity-0 transition duration-500 group-hover:translate-y-0 group-hover:opacity-100">
                <span className="block text-[10px] uppercase tracking-[0.24em] text-gold-500">
                  Voir la galerie
                </span>
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* Assistant CTA */}
      <section className="shell py-28">
        <Reveal>
          <div className="card grain relative overflow-hidden px-8 py-16 text-center md:px-20">
            <div className="absolute inset-0 bg-gradient-to-br from-gold-700/12 via-transparent to-sky-900/12" />
            <div className="relative">
              <p className="eyebrow">Assistant</p>
              <h2 className="mx-auto mt-5 max-w-2xl font-display text-[clamp(2rem,4.6vw,3.5rem)] font-light leading-[1.05]">
                « Quelle mention pour 17 de moyenne ? »
              </h2>
              <p className="mx-auto mt-6 max-w-xl text-[15px] leading-relaxed text-muted">
                L'assistant répond à partir des modules, du catalogue de documents et du règlement
                chargés dans la base — pas à partir d'à peu près.
              </p>
              <Link to="/assistant" className="btn-gold mt-10">
                Ouvrir l'assistant
              </Link>
            </div>
          </div>
        </Reveal>
      </section>

      {/* FAQ teaser */}
      {faqs && (
        <section className="shell pb-28">
          <SectionHeading eyebrow="Règlement" title="Les questions qui reviennent" />
          <div className="mt-12 divide-y divide-white/8 border-y border-white/8">
            {faqs
              .flatMap((g) => g.items)
              .slice(0, 5)
              .map((f, i) => (
                <Reveal key={f.id} delay={i * 60}>
                  <details className="group py-6" open={i === 0}>
                    <summary className="flex cursor-pointer list-none items-center justify-between gap-6 text-[17px] text-ivory/90 transition group-hover:text-gold-400">
                      {f.question}
                      <span className="text-gold-600 transition group-open:rotate-45">+</span>
                    </summary>
                    <p className="mt-4 max-w-3xl text-[14.5px] leading-relaxed text-muted">
                      {f.answer}
                    </p>
                  </details>
                </Reveal>
              ))}
          </div>
          <div className="mt-10">
            <Link to="/faq" className="btn-ghost">
              Toutes les questions
            </Link>
          </div>
        </section>
      )}
    </>
  );
}
