import { useState } from 'react';
import PageHeader from '../components/PageHeader';
import Reveal from '../components/Reveal';
import { request, useApi } from '../lib/api';
import { byTopic } from '../lib/media';

const PROFILES = [
  ['prospective', 'Étudiant pressenti'],
  ['student', 'Étudiant actuel'],
  ['partner', 'Partenaire / entreprise'],
  ['other', 'Autre'],
];

const EMPTY = { name: '', email: '', phone: '', profile: 'prospective', subject: '', message: '' };

export default function Contact() {
  const { data: contact } = useApi('/contact-info/');
  const [form, setForm] = useState(EMPTY);
  const [state, setState] = useState({ status: 'idle', errors: null });

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setState({ status: 'sending', errors: null });
    try {
      await request('/contact/', { method: 'POST', body: JSON.stringify(form) });
      setState({ status: 'sent', errors: null });
      setForm(EMPTY);
    } catch (err) {
      setState({ status: 'error', errors: err.fields || { detail: err.message } });
    }
  }

  const fieldError = (name) => state.errors?.[name]?.[0] || null;

  return (
    <>
      <PageHeader
        eyebrow="Contact"
        title="Écrire à l'équipe du wiki"
        lead="Une ressource manquante, un doublon, une règle mal retranscrite ? Les messages alimentent l'administration du site."
        image={byTopic('life')[0]?.file}
      />

      <section className="shell grid gap-16 py-20 lg:grid-cols-[1.4fr_1fr]">
        <Reveal>
          {state.status === 'sent' ? (
            <div className="card border-gold-600/35 p-12 text-center">
              <p className="font-display text-4xl text-gold-400">Message enregistré</p>
              <p className="mt-4 text-sm text-muted">
                Il est visible dans l'administration Django, rubrique Messages de contact.
              </p>
              <button onClick={() => setState({ status: 'idle', errors: null })} className="btn-ghost mt-9">
                Écrire encore
              </button>
            </div>
          ) : (
            <form onSubmit={submit} className="card space-y-6 p-8 md:p-10" noValidate>
              {state.errors?.detail && (
                <p className="rounded-lg border border-rose-500/35 bg-rose-500/8 px-4 py-3 text-sm text-rose-200">
                  {state.errors.detail}
                </p>
              )}

              <div className="grid gap-6 sm:grid-cols-2">
                <Field label="Nom" error={fieldError('name')}>
                  <input required value={form.name} onChange={set('name')} className={inputCls} placeholder="Votre nom" />
                </Field>
                <Field label="E-mail" error={fieldError('email')}>
                  <input required type="email" value={form.email} onChange={set('email')} className={inputCls} placeholder="prenom.nom@esi.ac.ma" />
                </Field>
                <Field label="Téléphone" error={fieldError('phone')}>
                  <input value={form.phone} onChange={set('phone')} className={inputCls} placeholder="optionnel" />
                </Field>
                <Field label="Vous êtes" error={fieldError('profile')}>
                  <select value={form.profile} onChange={set('profile')} className={inputCls}>
                    {PROFILES.map(([v, l]) => (
                      <option key={v} value={v} className="bg-ink-800">
                        {l}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <Field label="Sujet" error={fieldError('subject')}>
                <input required value={form.subject} onChange={set('subject')} className={inputCls} placeholder="Ajouter des annales de 5.1" />
              </Field>

              <Field label="Message" error={fieldError('message')}>
                <textarea required rows={6} value={form.message} onChange={set('message')} className={`${inputCls} resize-y`} placeholder="Décrivez votre demande…" />
              </Field>

              <div className="flex items-center gap-5 pt-2">
                <button type="submit" disabled={state.status === 'sending'} className="btn-gold disabled:opacity-50">
                  {state.status === 'sending' ? 'Envoi…' : 'Envoyer'}
                </button>
                <p className="text-xs text-muted">Conservé dans la base locale du projet.</p>
              </div>
            </form>
          )}
        </Reveal>

        <Reveal delay={120}>
          <aside className="space-y-10">
            <div>
              <h3 className="eyebrow">Direct</h3>
              <a
                href={`mailto:${contact?.email || ''}`}
                className="mt-4 block font-display text-2xl text-ivory transition hover:text-gold-400"
              >
                {contact?.email || '—'}
              </a>
              {contact?.phone && (
                <a
                  href={`tel:${contact.phone.replace(/\s+/g, '')}`}
                  className="mt-2 block text-sm text-muted transition hover:text-ivory"
                >
                  {contact.phone}
                </a>
              )}
              <p className="mt-2 text-xs text-muted">
                Adresse et numéro viennent du serveur&nbsp;: le dépôt public ne porte pas de
                téléphone.
              </p>
            </div>
            <div className="rule" />
            <div>
              <h3 className="eyebrow">Administration</h3>
              <p className="mt-4 text-[14px] leading-relaxed text-muted">
                Pour une question de scolarité — note, inscription, convention de stage — adressez-vous
                directement à l'administration de l'ESI. Ce wiki n'a aucun accès aux dossiers
                étudiants.
              </p>
            </div>
            <div className="rule" />
            <div>
              <h3 className="eyebrow">Backend</h3>
              <p className="mt-4 text-[14px] leading-relaxed text-muted">
                Les messages sont stockés par Django et consultables dans{' '}
                <a href="/admin/" className="text-gold-500 underline underline-offset-4 hover:text-gold-400">
                  /admin/
                </a>
                .
              </p>
            </div>
          </aside>
        </Reveal>
      </section>
    </>
  );
}

const inputCls =
  'w-full rounded-lg border border-white/12 bg-ink-900/70 px-4 py-3 text-sm text-ivory outline-none transition placeholder:text-muted/60 focus:border-gold-600/60';

function Field({ label, error, children }) {
  return (
    <label className="block">
      <span className="mb-2 block text-[11px] uppercase tracking-[0.18em] text-muted">{label}</span>
      {children}
      {error && <span className="mt-2 block text-xs text-rose-300">{error}</span>}
    </label>
  );
}
