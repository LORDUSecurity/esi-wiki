import PageHeader from '../components/PageHeader';
import Gallery from '../components/Gallery';
import Reveal from '../components/Reveal';
import SectionHeading from '../components/SectionHeading';
import { ASSETS, byTopic } from '../lib/media';

const SECTIONS = [
  { key: 'library', title: 'Bibliothèques et salles de lecture', lead: "Les lieux où l'on révise vraiment." },
  { key: 'lecture', title: 'Amphithéâtres et salles', lead: 'Supports de cours, travail dirigé, examens.' },
  { key: 'lab', title: 'Laboratoires', lead: 'Manipulation, instrumentation, calcul.' },
  { key: 'students', title: 'Vie étudiante', lead: 'Les visages et les moments d\'après-cours.' },
  { key: 'graduation', title: 'Soutenances et promotions', lead: 'Le bout du chemin, en toge.' },
  { key: 'rabat', title: 'Rabat', lead: 'La ville autour du campus.' },
];

export default function CampusLife() {
  const shown = SECTIONS.flatMap((s) => byTopic(s.key));

  return (
    <>
      <PageHeader
        eyebrow="Galerie"
        title="Vie de campus"
        lead="Photographies sous licence libre, choisies pour l'ambiance de travail qu'elles rendent. Elles illustrent le site et ne prétendent pas montrer l'ESI."
        image={byTopic('library')[0]?.file}
      />

      <section className="shell space-y-24 py-20">
        {SECTIONS.map((s) => {
          const items = byTopic(s.key);
          if (!items.length) return null;
          return (
            <div key={s.key}>
              <SectionHeading eyebrow={s.key} title={s.title} lead={s.lead} />
              <div className="mt-10">
                <Gallery items={items} columns="lg:grid-cols-3" />
              </div>
            </div>
          );
        })}
      </section>

      <section className="bg-ink-900 py-24">
        <div className="shell">
          <Reveal>
            <p className="eyebrow">Attributions</p>
            <h2 className="mt-4 font-display text-4xl font-light">Crédits photographiques</h2>
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-muted">
              {shown.length} images utilisées sur cette page, toutes issues de Wikimedia Commons.
              Les licences CC BY et CC BY-SA exigent que l'auteur et la licence apparaissent — les
              voici, avec le lien vers le fichier d'origine.
            </p>
          </Reveal>

          <div className="mt-10 overflow-x-auto">
            <table className="w-full min-w-[680px] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-white/12 text-[11px] uppercase tracking-[0.16em] text-muted">
                  <th className="py-3 pr-4 font-medium">Fichier</th>
                  <th className="py-3 pr-4 font-medium">Auteur</th>
                  <th className="py-3 pr-4 font-medium">Licence</th>
                  <th className="py-3 font-medium">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/7">
                {ASSETS.map((a) => (
                  <tr key={a.file} className="text-ivory/75">
                    <td className="py-3 pr-4">
                      <span className="flex items-center gap-3">
                        <img src={a.file} alt="" className="h-9 w-14 rounded object-cover" loading="lazy" />
                        <span className="max-w-[220px] truncate text-xs">{a.title.replace('File:', '')}</span>
                      </span>
                    </td>
                    <td className="py-3 pr-4 text-xs">{a.artist}</td>
                    <td className="py-3 pr-4 text-xs text-gold-500">{a.license}</td>
                    <td className="py-3 text-xs">
                      <a href={a.page} target="_blank" rel="noreferrer" className="underline decoration-white/25 underline-offset-4 hover:text-gold-400">
                        Commons
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </>
  );
}
