import Reveal from './Reveal';

export default function SectionHeading({ eyebrow, title, lead, align = 'left', action }) {
  return (
    <div
      className={`flex flex-col gap-6 md:flex-row md:items-end md:justify-between ${
        align === 'center' ? 'text-center md:flex-col md:items-center' : ''
      }`}
    >
      <Reveal className="max-w-2xl">
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h2 className="mt-4 font-display text-[clamp(2rem,4.4vw,3.4rem)] font-light leading-[1.06]">
          {title}
        </h2>
        {lead && <p className="mt-5 text-[15px] leading-relaxed text-muted">{lead}</p>}
      </Reveal>
      {action && (
        <Reveal delay={120} className="shrink-0">
          {action}
        </Reveal>
      )}
    </div>
  );
}
