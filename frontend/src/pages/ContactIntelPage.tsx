import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Search, CheckCircle2, XCircle, Loader2, Zap, Globe, Mail, Phone, Linkedin, Settings } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '../api/client';

interface ContactResult {
  contact: {
    first_name: string | null; last_name: string | null; job_title: string | null;
    email: string | null; email_confidence: number; email_verified: boolean;
    phone: string | null; mobile: string | null; linkedin_url: string | null;
  };
  company_data: { all_emails: string[]; all_phones: string[]; linkedin_company: string | null; };
  meta: { sources_used: string[]; providers_tried: string[]; enriched_at: string; };
  domain: string | null;
}

interface Provider {
  name: string; type: string; active: boolean; description: string;
  config_key: string | null; pricing?: string; url?: string;
}

export default function ContactIntelPage() {
  const [form, setForm] = useState({
    company_name: '', website: '', first_name: '', last_name: '',
    job_title: 'Dirigeant', stop_on_verified: true,
  });
  const [result, setResult] = useState<ContactResult | null>(null);
  const [tab, setTab] = useState<'search' | 'domain' | 'verify' | 'providers'>('search');
  const [domainQuery, setDomainQuery] = useState('');
  const [verifyEmail, setVerifyEmail] = useState('');

  const { data: providers } = useQuery<{ providers: Provider[]; active_count: number }>({
    queryKey: ['contact-providers'],
    queryFn: async () => { try { const data = await apiClient.get('/contacts/providers'); return data; } catch { return { providers: [], active_count: 0 }; } },
  });

  const findMutation = useMutation({
    mutationFn: async (body: typeof form) => {
      const data = await apiClient.post('/contacts/find', body);
      return data as ContactResult;
    },
    onSuccess: (data) => {
      setResult(data);
      if (data.contact.email_verified) toast.success('Email SMTP vérifié ✓');
      else if (data.contact.email) toast.success('Email trouvé (non vérifié)');
      else toast.info("Aucun email trouvé");
    },
  });

  const domainMutation = useMutation({
    mutationFn: async (domain: string) => apiClient.post('/contacts/domain-search', { domain }),
  });

  const verifyMutation = useMutation({
    mutationFn: async (email: string) => apiClient.post('/contacts/verify-email', { email }),
    onSuccess: (data: any) => {
      if (data.valid) toast.success(`✓ ${data.email} — Email valide`);
      else toast.error(`✗ ${data.email} — Email invalide`);
    },
  });

  const TABS = [
    { id: 'search', label: 'Recherche contact', icon: '🔍' },
    { id: 'domain', label: 'Domain search', icon: '🌐' },
    { id: 'verify', label: 'Vérifier email', icon: '✉️' },
    { id: 'providers', label: `Providers (${providers?.active_count ?? '…'} actifs)`, icon: '⚡' },
  ];

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%', boxSizing: 'border-box', overflowY: 'auto' }}>

      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 0.25rem' }}>
          Contact Intelligence
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: 0 }}>
          Trouvez emails et téléphones — Apollo-style, gratuit par défaut
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.25rem', background: 'var(--bg-tertiary)', padding: '4px', borderRadius: '10px', width: 'fit-content' }}>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id as typeof tab)}
            style={{
              padding: '0.4375rem 1rem', borderRadius: '7px', fontSize: '0.8125rem',
              fontWeight: tab === t.id ? 600 : 500,
              background: tab === t.id ? '#fff' : 'transparent',
              border: 'none', color: tab === t.id ? 'var(--accent-blue)' : 'var(--text-secondary)',
              cursor: 'pointer', transition: 'all 0.15s',
              boxShadow: tab === t.id ? '0 1px 4px rgba(30,42,59,0.1)' : 'none',
              whiteSpace: 'nowrap',
            }}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Search tab */}
      {tab === 'search' && (
        <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '1.25rem', flex: 1 }}>

          {/* Form card */}
          <div style={{ background: '#fff', border: '1px solid var(--border-color)', borderRadius: '12px', boxShadow: 'var(--shadow-card)', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', height: 'fit-content' }}>
            <h3 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              🔍 Trouver un contact
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <FormField label="Prénom">
                <CRMInput value={form.first_name} onChange={v => setForm(f => ({ ...f, first_name: v }))} placeholder="Jean" />
              </FormField>
              <FormField label="Nom">
                <CRMInput value={form.last_name} onChange={v => setForm(f => ({ ...f, last_name: v }))} placeholder="Dupont" />
              </FormField>
            </div>

            <FormField label="Entreprise *">
              <CRMInput value={form.company_name} onChange={v => setForm(f => ({ ...f, company_name: v }))} placeholder="Acme SAS" />
            </FormField>

            <FormField label="Site web">
              <CRMInput value={form.website} onChange={v => setForm(f => ({ ...f, website: v }))} placeholder="https://acme.fr" />
            </FormField>

            <FormField label="Poste recherché">
              <select
                value={form.job_title}
                onChange={e => setForm(f => ({ ...f, job_title: e.target.value }))}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: '#fff', color: 'var(--text-primary)', fontSize: '0.875rem', outline: 'none' }}
              >
                {['Dirigeant', 'Gérant', 'CEO', 'DG', 'Responsable marketing', 'Directeur commercial', 'DSI', 'DAF'].map(o => (
                  <option key={o}>{o}</option>
                ))}
              </select>
            </FormField>

            <label style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', cursor: 'pointer', padding: '0.625rem', background: 'var(--bg-tertiary)', borderRadius: '8px' }}>
              <input type="checkbox" checked={form.stop_on_verified}
                onChange={e => setForm(f => ({ ...f, stop_on_verified: e.target.checked }))}
                style={{ accentColor: 'var(--accent-blue)', width: '14px', height: '14px' }} />
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                Arrêter dès le premier email SMTP vérifié
              </span>
            </label>

            <button
              onClick={() => findMutation.mutate(form)}
              disabled={!form.company_name || findMutation.isPending}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                padding: '0.6875rem', borderRadius: '10px',
                background: 'var(--accent-blue)', border: 'none', color: '#fff',
                fontWeight: 600, fontSize: '0.9375rem', cursor: 'pointer',
                opacity: (!form.company_name || findMutation.isPending) ? 0.6 : 1,
                boxShadow: '0 4px 12px rgba(52,104,246,0.3)',
                transition: 'all 0.2s',
              }}
            >
              {findMutation.isPending
                ? <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Recherche en cours…</>
                : <><Search size={16} /> Trouver le contact</>
              }
            </button>

            {providers && (
              <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                {providers.active_count} provider(s) · {providers.providers.filter(p => p.active).map(p => p.name.split(' ')[0]).join(', ')}
              </p>
            )}
          </div>

          {/* Result card */}
          <div style={{ background: '#fff', border: '1px solid var(--border-color)', borderRadius: '12px', boxShadow: 'var(--shadow-card)', padding: '1.5rem' }}>
            {!result && !findMutation.isPending && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '300px', color: 'var(--text-muted)' }}>
                <div style={{ width: '64px', height: '64px', borderRadius: '16px', background: 'var(--bg-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.75rem', marginBottom: '1rem' }}>🔍</div>
                <p style={{ margin: 0, fontWeight: 600, color: 'var(--text-secondary)' }}>Lancez une recherche</p>
                <p style={{ margin: '0.25rem 0 0', fontSize: '0.8125rem' }}>Le résultat apparaîtra ici</p>
              </div>
            )}

            {findMutation.isPending && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '300px' }}>
                <div style={{ width: '56px', height: '56px', borderRadius: '50%', border: '3px solid var(--border-color)', borderTopColor: 'var(--accent-blue)', animation: 'spin 0.8s linear infinite', marginBottom: '1.25rem' }} />
                <p style={{ margin: 0, fontWeight: 600, color: 'var(--text-primary)' }}>Scan waterfall en cours…</p>
                <p style={{ margin: '0.25rem 0 0', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Site web → Pattern → SMTP → APIs</p>
              </div>
            )}

            {result && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <h3 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Résultats pour {result.contact.first_name || ''} {result.contact.last_name || form.company_name}
                </h3>

                {/* Email principal */}
                <div style={{
                  padding: '1.25rem', borderRadius: '10px',
                  background: result.contact.email_verified ? 'rgba(27,193,94,0.06)' : result.contact.email ? 'rgba(245,166,35,0.06)' : 'var(--bg-tertiary)',
                  border: `2px solid ${result.contact.email_verified ? 'rgba(27,193,94,0.3)' : result.contact.email ? 'rgba(245,166,35,0.3)' : 'var(--border-color)'}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      Email principal
                    </span>
                    {result.contact.email_verified
                      ? <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--accent-green)', fontWeight: 600 }}>
                          <CheckCircle2 size={13} /> SMTP vérifié
                        </span>
                      : result.contact.email
                      ? <span style={{ fontSize: '0.75rem', color: 'var(--accent-orange)', fontWeight: 500 }}>
                          Non vérifié ({Math.round(result.contact.email_confidence * 100)}%)
                        </span>
                      : <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Non trouvé</span>
                    }
                  </div>
                  {result.contact.email
                    ? <div style={{ fontFamily: 'monospace', fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0.01em' }}>
                        {result.contact.email}
                      </div>
                    : <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Aucun email trouvé</div>
                  }
                  {result.contact.email && (
                    <div style={{ marginTop: '0.75rem' }}>
                      <div style={{ height: '4px', borderRadius: '2px', background: 'var(--border-color)', overflow: 'hidden' }}>
                        <div style={{
                          height: '100%', borderRadius: '2px',
                          width: `${result.contact.email_confidence * 100}%`,
                          background: result.contact.email_verified ? 'var(--accent-green)' : 'var(--accent-orange)',
                          transition: 'width 0.5s ease',
                        }} />
                      </div>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        Confiance : {Math.round(result.contact.email_confidence * 100)}%
                      </span>
                    </div>
                  )}
                </div>

                {/* Autres champs */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <ResultField icon={<Phone size={13} />} label="Téléphone" value={result.contact.phone || result.company_data.all_phones[0]} />
                  <ResultField icon={<Phone size={13} />} label="Mobile" value={result.contact.mobile} />
                  <ResultField icon={<Linkedin size={13} />} label="LinkedIn" value={result.contact.linkedin_url} isLink />
                  <ResultField icon={<Globe size={13} />} label="Domaine" value={result.domain} />
                </div>

                {/* Autres emails */}
                {result.company_data.all_emails.length > 0 && (
                  <div>
                    <p style={{ margin: '0 0 0.625rem', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      Tous les emails ({result.company_data.all_emails.length})
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                      {result.company_data.all_emails.slice(0, 5).map((email, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', background: 'var(--bg-tertiary)', borderRadius: '6px', fontSize: '0.8125rem' }}>
                          <Mail size={12} color="var(--text-muted)" />
                          <span style={{ fontFamily: 'monospace', color: 'var(--text-primary)' }}>{email}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Sources */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Sources :</span>
                  {result.meta.sources_used.map(s => (
                    <span key={s} style={{ padding: '2px 10px', borderRadius: '20px', fontSize: '0.7rem', fontWeight: 600, background: 'rgba(52,104,246,0.1)', color: 'var(--accent-blue)', border: '1px solid rgba(52,104,246,0.2)' }}>
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Domain search tab */}
      {tab === 'domain' && (
        <div style={{ background: '#fff', border: '1px solid var(--border-color)', borderRadius: '12px', boxShadow: 'var(--shadow-card)', padding: '1.5rem', maxWidth: '560px' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>🌐 Recherche par domaine</h3>
          <div style={{ display: 'flex', gap: '0.625rem' }}>
            <CRMInput value={domainQuery} onChange={setDomainQuery} placeholder="acme.fr" />
            <button
              onClick={() => domainMutation.mutate(domainQuery)}
              disabled={!domainQuery || domainMutation.isPending}
              style={{ padding: '0.5rem 1.25rem', borderRadius: '8px', background: 'var(--accent-blue)', border: 'none', color: '#fff', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem', whiteSpace: 'nowrap', opacity: (!domainQuery || domainMutation.isPending) ? 0.6 : 1 }}
            >
              {domainMutation.isPending ? 'Recherche…' : 'Rechercher'}
            </button>
          </div>
        </div>
      )}

      {/* Verify tab */}
      {tab === 'verify' && (
        <div style={{ background: '#fff', border: '1px solid var(--border-color)', borderRadius: '12px', boxShadow: 'var(--shadow-card)', padding: '1.5rem', maxWidth: '560px' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>✉️ Vérifier un email</h3>
          <div style={{ display: 'flex', gap: '0.625rem' }}>
            <CRMInput value={verifyEmail} onChange={setVerifyEmail} placeholder="contact@acme.fr" />
            <button
              onClick={() => verifyMutation.mutate(verifyEmail)}
              disabled={!verifyEmail || verifyMutation.isPending}
              style={{ padding: '0.5rem 1.25rem', borderRadius: '8px', background: 'var(--accent-blue)', border: 'none', color: '#fff', cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem', whiteSpace: 'nowrap', opacity: (!verifyEmail || verifyMutation.isPending) ? 0.6 : 1 }}
            >
              {verifyMutation.isPending ? 'Vérification…' : 'Vérifier'}
            </button>
          </div>
        </div>
      )}

      {/* Providers tab */}
      {tab === 'providers' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
          {providers?.providers.map(p => (
            <div key={p.name} style={{
              background: '#fff', border: `1px solid ${p.active ? 'rgba(27,193,94,0.3)' : 'var(--border-color)'}`,
              borderRadius: '12px', boxShadow: 'var(--shadow-card)', padding: '1.25rem',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>{p.name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>{p.type}</div>
                </div>
                <span style={{
                  padding: '3px 10px', borderRadius: '20px', fontSize: '0.7rem', fontWeight: 700,
                  background: p.active ? 'rgba(27,193,94,0.1)' : 'var(--bg-tertiary)',
                  color: p.active ? 'var(--accent-green)' : 'var(--text-muted)',
                  border: `1px solid ${p.active ? 'rgba(27,193,94,0.2)' : 'var(--border-color)'}`,
                }}>
                  {p.active ? '● Actif' : '○ Inactif'}
                </span>
              </div>
              <p style={{ margin: '0 0 0.75rem', fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{p.description}</p>
              {p.pricing && <span style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', fontWeight: 500 }}>{p.pricing}</span>}
            </div>
          ))}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

// ── Sub-components
function FormField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.375rem' }}>
        {label}
      </label>
      {children}
    </div>
  );
}

function CRMInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width: '100%', padding: '0.5rem 0.75rem',
        borderRadius: '8px', border: '1px solid var(--border-color)',
        background: '#fff', color: 'var(--text-primary)', fontSize: '0.875rem',
        outline: 'none', boxSizing: 'border-box' as const,
        transition: 'border-color 0.15s, box-shadow 0.15s',
      }}
      onFocus={e => { e.target.style.borderColor = 'var(--accent-blue)'; e.target.style.boxShadow = '0 0 0 3px rgba(52,104,246,0.12)'; }}
      onBlur={e => { e.target.style.borderColor = 'var(--border-color)'; e.target.style.boxShadow = 'none'; }}
    />
  );
}

function ResultField({ icon, label, value, isLink }: { icon: React.ReactNode; label: string; value?: string | null; isLink?: boolean }) {
  if (!value) return (
    <div style={{ padding: '0.75rem', background: 'var(--bg-tertiary)', borderRadius: '8px', opacity: 0.5 }}>
      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '4px' }}>{icon} {label}</div>
      <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>—</div>
    </div>
  );
  return (
    <div style={{ padding: '0.75rem', background: 'var(--bg-tertiary)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '4px' }}>{icon} {label}</div>
      {isLink
        ? <a href={value} target="_blank" rel="noreferrer" style={{ fontSize: '0.8125rem', color: 'var(--accent-blue)', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }}>{value}</a>
        : <div style={{ fontSize: '0.8125rem', color: 'var(--text-primary)', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{value}</div>
      }
    </div>
  );
}
