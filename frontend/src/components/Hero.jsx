import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { byTopic } from '../lib/media';

const SHOTS = byTopic('hero');
const DWELL = 6400;

export default function Hero({ stats }) {
  const [i, setI] = useState(0);

  useEffect(() => {
    if (SHOTS.length < 2) return;
    const t = setInterval(() => setI((v) => (v + 1) % SHOTS.length), DWELL);
    return () => clearInterval(t);
  }, []);

  return (
    <section className="relative min-h-[100svh] overflow-hidden">
      {/* Frame stack: each shot cross-dissolves while slowly pushing in. */}
      <div className="absolute inset-0">
        {SHOTS.length === 0 && <div className="absolute inset-0 bg-ink-800" />}
        {SHOTS.map((shot, idx) => (
          <div
            key={shot.file}
            className={`absolute inset-0 transition-opacity duration-[2600ms] ease-in-out ${
              idx === i ? 'opacity-100' : 'opacity-0'
            }`}
          >
            <img
              // Remount so the push-in restarts on the frame that becomes visible.
              key={idx === i ? `${shot.file}-${i}` : shot.file}
              src={shot.file}
              alt=""
              aria-hidden={idx !== i}
              className={`h-full w-full object-cover ${idx === i ? 'animate-kenburns' : ''}`}
            />
          </div>
        ))}
        <div className="vignette grain absolute inset-0" />
      </div>

      <div className="shell relative flex min-h-[100svh] flex-col justify-center pb-28 pt-36">
        <p className="eyebrow animate-fadeIn">École de Sciences de l'Information · Rabat</p>

        <h1 className="mt-6 max-w-4xl font-display text-[clamp(2.9rem,8.2vw,6.6rem)] font-light leading-[0.94]">
          <span className="block overflow-hidden">
            <span className="block animate-fadeUp">Le savoir de</span>
          </span>
          <span className="block overflow-hidden">
            <span className="block animate-fadeUp shimmer-text" style={{ animationDelay: '160ms' }}>
              l'ESI, complet
            </span>
          </span>
        </h1>

        <p
          className="mt-8 max-w-xl animate-fadeUp text-[17px] leading-relaxed text-ivory/75"
          style={{ animationDelay: '320ms' }}
        >
          Six semestres de cycle ingénieur, {stats?.modules ?? '—'} modules et{' '}
          {stats?.resources ?? '—'} supports déjà classés ici — polycopiés, fiches de TP, TD et
          annales — avec un assistant qui connaît le règlement.
        </p>

        <div
          className="mt-11 flex flex-wrap items-center gap-4 animate-fadeUp"
          style={{ animationDelay: '460ms' }}
        >
          <Link to="/programmes" className="btn-gold">
            Explorer les modules
          </Link>
          <Link to="/assistant" className="btn-ghost">
            Poser une question
          </Link>
        </div>

        {stats && (
          <dl
            className="mt-20 grid max-w-3xl grid-cols-2 gap-x-8 gap-y-9 animate-fadeUp sm:grid-cols-4"
            style={{ animationDelay: '620ms' }}
          >
            {[
              ['Modules', stats.modules],
              ['Documents', stats.resources],
              ['Filières', 4],
              [
                'Semestres couverts',
                `${stats.semesters_indexed} + PFE`,
                `S1 à S${stats.semesters_indexed} ont leurs modules et leurs documents dans ce wiki ` +
                  `(le dépôt porte S1-S2, le corpus miroir d'EsiHub couvre S3 à S5) sur ${stats.cycle_semesters} ` +
                  `semestres de cycle ; S6 est l'année du PFE (${stats.pfe_reports} rapports), sans modules.`,
              ],
            ].map(([label, value, hint]) => (
              <div key={label} title={hint}>
                <dt className="text-[10px] uppercase tracking-[0.28em] text-muted">{label}</dt>
                <dd className="mt-2 font-display text-4xl text-gold-500">{value}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-8 flex justify-center">
        <span className="flex h-14 w-8 items-start justify-center rounded-full border border-white/20 p-2">
          <span className="h-2.5 w-px animate-drift bg-gold-500" />
        </span>
      </div>
    </section>
  );
}
