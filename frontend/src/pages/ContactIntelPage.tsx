import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Search, CheckCircle2, XCircle, Loader2, Zap, Globe, Mail, Phone, Linkedin, ExternalLink, Settings } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '../api/client';
import { PageHeader } from '../components/ui/PageHeader';

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
    queryFn: async () => { const { data } = await apiClient.get('/contacts/providers'); return data; },
  });

  const findMutation = useMutation({
    mutationFn: async (body: typeof form) => {
      const { data } = await apiClient.post('/contacts/find', body);
      return data as ContactResult;
    },
    onSuccess: (data) => {
      setResult(data);
      if (data.contact.email_verified) toast.success('Email SMTP vérifié ✓');
      else if (data.contact.email) toast.success('Email trouvé (non vérifié)');
      else toast.info('Aucun email trouvé — essayez d\'activer un provider payant');
    },
  });

  const domainMutation = useMutation({
    mutationFn: async (domain: string) => {
      const { data } = await apiClient.post('/contacts/domain-search', { domain });
      return data;
    },
  });

  const verifyMutation = useMutation({
    mutationFn: async (email: string) => {
      const { data } = await apiClient.post('/contacts/verify-email', { email });
      return data;
    },
    onSuccess: (data) => {
      if (data.valid) toast.success(`✓ ${data.email} — Email valide`);
      else toast.error(`✗ ${data.email} — Email invalide`);
    },
  });

  return (
    <>
      <PageHeader
        title="Contact Intelligence"
        description="Trouvez emails et téléphones — Apollo-style, gratuit par défaut"
      />
      <div className="p-6">
        {/* Tabs */}
        <div className="flex border-b mb-6">
          {[
            { id: 'search', label: '🔍 Recherche contact' },
            { id: 'domain', label: '🌐 Domain search' },
            { id: 'verify', label: '✉️ Vérifier email' },
            { id: 'providers', label: `⚡ Providers (${providers?.active_count ?? '...'}  actifs)` },
          ].map((t) => (
            <button key={t.id} onClick={() => setTab(t.id as typeof tab)}
              className={`px-5 py-3 text-sm font-medium border-b-2 transition ${
                tab === t.id ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab: Recherche contact */}
        {tab === 'search' && (
          <div className="grid grid-cols-2 gap-6">
            {/* Formulaire */}
            <div className="bg-white rounded-xl border p-5 space-y-4">
              <h3 className="font-semibold">Trouver un contact</h3>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Prénom">
                  <input value={form.first_name} onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))}
                    placeholder="Jean" className="input" />
                </Field>
                <Field label="Nom">
                  <input value={form.last_name} onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))}
                    placeholder="Dupont" className="input" />
                </Field>
              </div>
              <Field label="Entreprise *">
                <input value={form.company_name} onChange={e => setForm(f => ({ ...f, company_name: e.target.value }))}
                  placeholder="Acme SAS" className="input" required />
              </Field>
              <Field label="Site web">
                <input value={form.website} onChange={e => setForm(f => ({ ...f, website: e.target.value }))}
                  placeholder="https://acme.fr" className="input" />
              </Field>
              <Field label="Poste recherché">
                <select value={form.job_title} onChange={e => setForm(f => ({ ...f, job_title: e.target.value }))}
                  className="input">
                  <option>Dirigeant</option>
                  <option>Gérant</option>
                  <option>CEO</option>
                  <option>DG</option>
                  <option>Responsable marketing</option>
                  <option>Directeur commercial</option>
                  <option>DSI</option>
                  <option>DAF</option>
                </select>
              </Field>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={form.stop_on_verified}
                  onChange={e => setForm(f => ({ ...f, stop_on_verified: e.target.checked }))}
                  className="accent-blue-600" />
                Arrêter dès le premier email SMTP vérifié
              </label>
              <button
                onClick={() => findMutation.mutate(form)}
                disabled={!form.company_name || findMutation.isPending}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {findMutation.isPending
                  ? <><Loader2 className="w-4 h-4 animate-spin" /> Recherche en cours…</>
                  : <><Search className="w-4 h-4" /> Trouver le contact</>
                }
              </button>
              {providers && (
                <p className="text-xs text-center text-gray-400">
                  {providers.active_count} provider(s) actif(s) ·
                  Sources : {providers.providers.filter(p => p.active).map(p => p.name.split(' ')[0]).join(', ')}
                </p>
              )}
            </div>

            {/* Résultat */}
            <div className="bg-white rounded-xl border p-5">
              {!result && !findMutation.isPending && (
                <div className="flex flex-col items-center justify-center h-full text-center py-12">
                  <Search className="w-12 h-12 text-gray-200 mb-3" />
                  <p className="text-gray-400 text-sm">Le résultat apparaîtra ici</p>
                </div>
              )}
              {findMutation.isPending && (
                <div className="flex flex-col items-center justify-center h-full py-12">
                  <Loader2 className="w-10 h-10 animate-spin text-blue-600 mb-3" />
                  <p className="text-sm text-gray-500">Scan waterfall en cours…</p>
                  <p className="text-xs text-gray-400 mt-1">Site web → Pattern → SMTP → APIs</p>
                </div>
              )}
              {result && (
                <div className="space-y-4">
                  {/* Email principal */}
                  <div className={`p-4 rounded-lg border-2 ${result.contact.email_verified ? 'border-green-300 bg-green-50' : result.contact.email ? 'border-orange-200 bg-orange-50' : 'border-gray-200 bg-gray-50'}`}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-gray-500 uppercase">Email principal</span>
                      {result.contact.email_verified
                        ? <span className="flex items-center gap-1 text-xs text-green-700 font-medium"><CheckCircle2 className="w-3.5 h-3.5" /> SMTP vérifié</span>
                        : result.contact.email
                        ? <span className="text-xs text-orange-600">Non vérifié ({Math.round(result.contact.email_confidence * 100)}%)</span>
                        : <span className="text-xs text-gray-400">Non trouvé</span>
                      }
                    </div>
                    {result.contact.email
                      ? <div className="font-mono text-sm font-medium">{result.contact.email}</div>
                      : <div className="text-gray-400 text-sm">—</div>
                    }
                  </div>

                  {/* Autres données */}
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <ContactField icon={<Phone className="w-3.5 h-3.5" />} label="Téléphone" value={result.contact.phone || result.company_data.all_phones[0]} />
                    <ContactField icon={<Phone className="w-3.5 h-3.5" />} label="Mobile" value={result.contact.mobile} />
                    <ContactField icon={<Linkedin className="w-3.5 h-3.5" />} label="LinkedIn" value={result.contact.linkedin_url} isLink />
                    <ContactField icon={<Globe className="w-3.5 h-3.5" />} label="Domaine" value={result.domain} />
                  </div>

                  {/* Tous les emails trouvés */}
                  {result.company_data.all_emails.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 mb-2">Tous les emails trouvés ({result.company_data.all_emails.length})</p>
                      <div className="space-y-1">
                        {result.company_data.all_emails.slice(0, 8).map(e => (
                          <div key={e} className="flex items-center justify-between py-1 px-2 bg-gray-50 rounded text-xs font-mono">
                            <span>{e}</span>
                            <button onClick={() => { navigator.clipboard.writeText(e); toast.success('Copié'); }}
                              className="text-gray-400 hover:text-blue-600">⎘</button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Sources */}
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-1">Sources utilisées</p>
                    <div className="flex flex-wrap gap-1">
                      {result.meta.sources_used.map(s => (
                        <span key={s} className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded">{s}</span>
                      ))}
                      {result.meta.sources_used.length === 0 && <span className="text-xs text-gray-400">Aucune source n'a trouvé de résultat</span>}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab: Domain search */}
        {tab === 'domain' && (
          <div className="max-w-2xl space-y-4">
            <div className="bg-white rounded-xl border p-5">
              <h3 className="font-semibold mb-3">Domain Search</h3>
              <p className="text-sm text-gray-500 mb-4">Trouve tous les emails connus pour un domaine.</p>
              <div className="flex gap-2">
                <input value={domainQuery} onChange={e => setDomainQuery(e.target.value)}
                  placeholder="acme.fr" className="flex-1 px-3 py-2 border rounded text-sm" />
                <button onClick={() => domainMutation.mutate(domainQuery)} disabled={!domainQuery || domainMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded text-sm disabled:opacity-50">
                  {domainMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Rechercher'}
                </button>
              </div>
            </div>
            {domainMutation.data && (
              <div className="bg-white rounded-xl border p-5">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium">{domainMutation.data.emails_found} email(s) trouvé(s)</h4>
                  <div className="flex gap-1">
                    {domainMutation.data.sources_used.map((s: string) => (
                      <span key={s} className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded">{s}</span>
                    ))}
                  </div>
                </div>
                <div className="space-y-1">
                  {domainMutation.data.results.map((r: any, i: number) => (
                    <div key={i} className="flex items-center justify-between py-1.5 px-3 bg-gray-50 rounded text-sm">
                      <div>
                        <span className="font-mono">{r.email}</span>
                        {r.first_name && <span className="text-gray-500 ml-2 text-xs">{r.first_name} {r.last_name}</span>}
                        {r.job_title && <span className="text-gray-400 ml-1 text-xs">· {r.job_title}</span>}
                      </div>
                      <div className="flex items-center gap-1">
                        {r.verified ? <CheckCircle2 className="w-3.5 h-3.5 text-green-500" /> : <XCircle className="w-3.5 h-3.5 text-gray-300" />}
                        <button onClick={() => { navigator.clipboard.writeText(r.email); toast.success('Copié'); }}
                          className="text-gray-400 hover:text-blue-600 ml-1">⎘</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab: Verify */}
        {tab === 'verify' && (
          <div className="max-w-xl">
            <div className="bg-white rounded-xl border p-5">
              <h3 className="font-semibold mb-3">Vérification email SMTP</h3>
              <p className="text-sm text-gray-500 mb-4">Vérifie si un email existe via handshake SMTP (sans envoyer d'email).</p>
              <div className="flex gap-2">
                <input value={verifyEmail} onChange={e => setVerifyEmail(e.target.value)}
                  placeholder="jean.dupont@acme.fr" type="email" className="flex-1 px-3 py-2 border rounded text-sm" />
                <button onClick={() => verifyMutation.mutate(verifyEmail)} disabled={!verifyEmail || verifyMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded text-sm disabled:opacity-50">
                  {verifyMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Vérifier'}
                </button>
              </div>
              {verifyMutation.data && (
                <div className={`mt-4 p-3 rounded-lg flex items-center gap-3 ${verifyMutation.data.valid ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  {verifyMutation.data.valid
                    ? <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
                    : <XCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                  }
                  <div>
                    <p className={`font-medium text-sm ${verifyMutation.data.valid ? 'text-green-800' : 'text-red-800'}`}>
                      {verifyMutation.data.valid ? '✓ Email valide' : '✗ Email invalide'}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">{verifyMutation.data.email} · méthode: {verifyMutation.data.method}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab: Providers */}
        {tab === 'providers' && (
          <div className="space-y-3 max-w-2xl">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
              <strong>Pour activer un provider payant</strong> : ajouter la clé API dans Coolify → Variables d'environnement, puis redéployer.
            </div>
            {providers?.providers.map((p) => (
              <div key={p.name} className={`bg-white rounded-lg border p-4 ${p.active ? '' : 'opacity-60'}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-2.5 h-2.5 rounded-full ${p.active ? 'bg-green-500' : 'bg-gray-300'}`} />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{p.name}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${p.type === 'free' ? 'bg-green-100 text-green-700' : 'bg-purple-100 text-purple-700'}`}>
                          {p.type === 'free' ? '🆓 Gratuit' : '💳 Payant'}
                        </span>
                        {p.active ? <span className="text-xs text-green-600 font-medium">● Actif</span>
                          : <span className="text-xs text-gray-400">○ Inactif</span>}
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5">{p.description}</p>
                    </div>
                  </div>
                  {p.url && (
                    <a href={p.url} target="_blank" rel="noreferrer" className="text-blue-500 hover:text-blue-700">
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
                {p.config_key && !p.active && (
                  <div className="mt-3 flex items-center gap-2 bg-gray-50 px-3 py-2 rounded text-xs">
                    <Settings className="w-3.5 h-3.5 text-gray-400" />
                    <span>Variable à ajouter : <code className="font-mono bg-gray-200 px-1 rounded">{p.config_key}</code></span>
                    {p.pricing && <span className="text-gray-400 ml-auto">{p.pricing}</span>}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {children}
    </div>
  );
}

function ContactField({ icon, label, value, isLink }: { icon: React.ReactNode; label: string; value: string | null | undefined; isLink?: boolean }) {
  if (!value) return (
    <div className="flex items-center gap-1.5 px-2 py-1.5 bg-gray-50 rounded">
      <span className="text-gray-300">{icon}</span>
      <span className="text-gray-400 text-xs">{label} : —</span>
    </div>
  );
  return (
    <div className="flex items-center gap-1.5 px-2 py-1.5 bg-gray-50 rounded">
      <span className="text-gray-500">{icon}</span>
      {isLink
        ? <a href={value.startsWith('http') ? value : `https://${value}`} target="_blank" rel="noreferrer"
            className="text-xs text-blue-600 hover:underline truncate">{label} ↗</a>
        : <span className="text-xs text-gray-800 truncate">{value}</span>
      }
    </div>
  );
}
