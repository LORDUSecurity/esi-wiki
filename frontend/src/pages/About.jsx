import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import Reveal from '../components/Reveal';
import SectionHeading from '../components/SectionHeading';
import { byTopic } from '../lib/media';
import { useApi } from '../lib/api';

const ARGUMENTS = [
  ['Curriculum', 'Algorithmique, systèmes, réseaux, données, sécurité et développement web, dès le premier semestre.'],
  ['Méthode', 'Chaque module rassemble son polycopié, ses fiches de TP, ses TD et ses sujets d\'examen.'],
  ['Encadrement', 'Stages ouvrier, d\'études et de fin d\'études, soutenus par un jury et un tuteur.'],
  ['Ouverture', 'Ajman University, CNAM, Université de Montréal, Oracle Academy, Huawei ICT Academy.'],
];

const DIPLOMAS = ["Ingénieur d'État", 'Master', 'Master Spécialisé', 'Doctorat'];

export default function About() {
  const { data: majors } = useApi('/majors/');
  const { data: stats } = useApi('/stats/');
  const shot = byTopic('students')[0]?.file || byTopic('campus')[0]?.file;

  return (
    <>
      <PageHeader
        eyebrow="L'école"
        title="À propos de l'ESI"
        lead="L'École de Sciences de l'Information forme des ingénieurs : informatique, cybersécurité, intelligence artificielle et science des données."
        image={byTopic('lecture')[0]?.file}
      />

      <section className="shell grid items-center gap-16 py-24 lg:grid-cols-2">
        <Reveal>
          <p className="eyebrow">Mission</p>
          <h2 className="mt-5 font-display text-[clamp(2rem,4vw,3.2rem)] font-light leading-[1.08]">
            Former des ingénieurs, et faire circuler le savoir entre les promotions.
          </h2>
          <p className="mt-7 text-[15.5px] leading-relaxed text-muted">
            Ce wiki est tenu par et pour les étudiants. Il reprend les supports de cours des cinq
            semestres de cours du cycle ingénieur et le règlement pédagogique, pour qu'un polycopié
            ne disparaisse pas avec une promotion : S1 et S2 viennent du dépôt de cours du repo,
            S3 à S5 des polycopiés miroités depuis EsiHub. Les chiffres affichés ici viennent de la
            base du site :{' '}
            {stats ? `${stats.modules} modules et ${stats.resources} documents` : '—'}.
          </p>
          <div className="mt-9 flex flex-wrap gap-3">
            {DIPLOMAS.map((d) => (
              <span
                key={d}
                className="rounded-full border border-gold-600/35 bg-gold-600/8 px-4 py-2 text-[12px] uppercase tracking-[0.14em] text-gold-400"
              >
                {d}
              </span>
            ))}
          </div>
        </Reveal>

        <Reveal delay={140}>
          <div className="relative overflow-hidden rounded-xl border border-white/10">
            {shot && <img src={shot} alt="" className="h-[520px] w-full object-cover animate-kenburns" />}
            <div className="absolute inset-0 bg-gradient-to-t from-ink-950/85 to-transparent" />
            <div className="absolute bottom-8 left-8 right-8">
              <p className="font-display text-2xl text-ivory">Rabat</p>
              <p className="mt-1 text-xs uppercase tracking-[0.2em] text-gold-500">
                Campus et quartiers
              </p>
            </div>
          </div>
        </Reveal>
      </section>

      <section className="bg-ink-900 py-24">
        <div className="shell">
          <SectionHeading eyebrow="Repères" title="Ce qui structure la scolarité" />
          <div className="mt-14 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {ARGUMENTS.map(([title, body], i) => (
              <Reveal key={title} delay={i * 90}>
                <div className="card h-full p-8">
                  <span className="font-display text-2xl text-gold-600">0{i + 1}</span>
                  <h3 className="mt-4 text-[19px] text-ivory">{title}</h3>
                  <p className="mt-3 text-[13.5px] leading-relaxed text-muted">{body}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="shell py-24">
        <SectionHeading
          eyebrow="Filières"
          title="Quatre parcours après le socle commun"
          action={
            <Link to="/programmes" className="btn-ghost">
              Voir les modules
            </Link>
          }
        />
        <div className="mt-12 divide-y divide-white/8 border-y border-white/8">
          {(majors || []).map((m, i) => (
            <Reveal key={m.code} delay={i * 60}>
              <div className="grid gap-4 py-9 md:grid-cols-[160px_1fr_1fr] md:items-baseline">
                <p className="font-display text-3xl text-gold-500">{m.code}</p>
                <div>
                  <h3 className="text-[18px] text-ivory">{m.name}</h3>
                  <p className="mt-2 text-[14px] leading-relaxed text-muted">{m.tagline}</p>
                </div>
                <ul className="flex flex-wrap gap-2">
                  {(m.career_paths || []).map((c) => (
                    <li
                      key={c}
                      className="rounded-full border border-white/10 px-3 py-1.5 text-[12px] text-ivory/70"
                    >
                      {c}
                    </li>
                  ))}
                </ul>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="shell pb-24">
        <Reveal>
          <div className="card border-gold-600/25 p-9 md:p-12">
            <p className="eyebrow">Avertissement</p>
            <h2 className="mt-4 font-display text-3xl font-light">
              Ce site n'est pas le site officiel de l'ESI
            </h2>
            <p className="mt-5 max-w-3xl text-[15px] leading-relaxed text-muted">
              Il s'agit d'un dépôt étudiant : les supports viennent des promotions précédentes, et
              les règles citées sont recopiées du règlement pédagogique. Pour une inscription, une
              note ou une décision disciplinaire, seul compte ce que dit l'administration.
            </p>
            <Link to="/contact" className="btn-gold mt-9">
              Signaler une erreur
            </Link>
          </div>
        </Reveal>
      </section>
    </>
  );
}
