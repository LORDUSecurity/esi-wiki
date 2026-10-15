import { Link } from 'react-router-dom';
import { ASSETS } from '../lib/media';
import { useApi } from '../lib/api';

const NAV = [
  { to: '/programmes', label: 'Programmes' },
  { to: '/campus', label: 'Vie de campus' },
  { to: '/faq', label: 'Questions fréquentes' },
  { to: '/a-propos', label: 'À propos' },
  { to: '/assistant', label: 'Assistant IA' },
  { to: '/contact', label: 'Contact' },
];

export default function Footer() {
  const { data: contact } = useApi('/contact-info/');
  return (
    <footer className="relative mt-28 border-t border-white/8 bg-ink-900">
      <div className="shell grid gap-12 py-16 md:grid-cols-2 lg:grid-cols-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-md border border-gold-600/45 bg-ink-800 font-display text-lg text-gold-500">
              E
            </span>
            <span className="font-display text-xl">ESI Wiki</span>
          </div>
          <p className="mt-5 max-w-xs text-sm leading-relaxed text-muted">
            Mémoire documentaire des étudiants de l'École de Sciences de l'Information — cours, TP, TD,
            annales et règlement, réunis au même endroit.
          </p>
        </div>

        <div>
          <h4 className="eyebrow">Navigation</h4>
          <ul className="mt-5 space-y-2.5 text-sm">
            {NAV.map((l) => (
              <li key={l.to}>
                <Link to={l.to} className="text-ivory/70 transition hover:text-gold-400">
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="eyebrow">Contact</h4>
          <ul className="mt-5 space-y-2.5 text-sm text-ivory/70">
            <li>
              <a
                href={`mailto:${contact?.email || ''}`}
                className="link-underline hover:text-gold-400"
              >
                {contact?.email || '—'}
              </a>
            </li>
            {contact?.phone && (
              <li>
                <a
                  href={`tel:${contact.phone.replace(/\s+/g, '')}`}
                  className="link-underline hover:text-gold-400"
                >
                  {contact.phone}
                </a>
              </li>
            )}
            <li className="text-muted">Rabat, Maroc</li>
          </ul>
        </div>

        <div>
          <h4 className="eyebrow">Iconographie</h4>
          <p className="mt-5 text-xs leading-relaxed text-muted">
            {ASSETS.length} photographies proviennent de Wikimedia Commons sous licence libre
            (CC BY / CC BY-SA / domaine public). Ce sont des illustrations : elles ne représentent pas
            le campus de l'ESI. Chaque auteur est crédité sur la page{' '}
            <Link to="/campus" className="text-gold-500 hover:text-gold-400">Vie de campus</Link>.
          </p>
        </div>
      </div>

      <div className="border-t border-white/6">
        <div className="shell flex flex-col items-center justify-between gap-3 py-6 text-xs text-muted md:flex-row">
          <p>© {new Date().getFullYear()} ESI Wiki — projet étudiant, sans valeur officielle.</p>
          <p>
            Règles et chiffres repris du règlement pédagogique ; vérifiez toujours auprès de
            l'administration.
          </p>
        </div>
      </div>
    </footer>
  );
}
