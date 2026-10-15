import { byTopic } from '../lib/media';

const SHOT = byTopic('campus')[0] || byTopic('library')[0];

export default function PageHeader({ eyebrow, title, lead, image }) {
  const src = image || SHOT?.file;
  return (
    <header className="relative overflow-hidden border-b border-white/8">
      {src && (
        <div className="absolute inset-0">
          <img src={src} alt="" className="h-full w-full object-cover opacity-30 animate-kenburns" />
          <div className="absolute inset-0 bg-gradient-to-b from-ink-950/70 via-ink-950/85 to-ink-950" />
        </div>
      )}
      <div className="shell relative pb-20 pt-40">
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="mt-5 max-w-3xl font-display text-[clamp(2.4rem,6vw,4.6rem)] font-light leading-[1.02]">
          {title}
        </h1>
        {lead && <p className="mt-6 max-w-2xl text-[16px] leading-relaxed text-muted">{lead}</p>}
      </div>
    </header>
  );
}
