import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface InboundLead {
  id: string;
  source: 'typeform' | 'hubspot' | 'webhook' | 'form' | 'other';
  company_name?: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  message?: string;
  score?: number;
  status: 'new' | 'processing' | 'enriched' | 'converted' | 'rejected';
  received_at: string;
  raw_data?: Record<string, unknown>;
}

const SOURCE_CONFIG = {
  typeform: { icon: '📝', label: 'Typeform', color: '#2f81f7' },
  hubspot: { icon: '🟠', label: 'HubSpot', color: '#f97316' },
  webhook: { icon: '🔗', label: 'Webhook', color: '#8b5cf6' },
  form: { icon: '📋', label: 'Formulaire', color: '#3fb950' },
  other: { icon: '📥', label: 'Autre', color: '#8b949e' },
};

const STATUS_CONFIG = {
  new: { label: 'Nouveau', color: '#2f81f7', bg: 'rgba(47,129,247,0.1)' },
  processing: { label: 'En cours', color: '#d29922', bg: 'rgba(210,153,34,0.1)' },
  enriched: { label: 'Enrichi', color: '#8b5cf6', bg: 'rgba(139,92,246,0.1)' },
  converted: { label: 'Converti', color: '#3fb950', bg: 'rgba(63,185,80,0.1)' },
  rejected: { label: 'Rejeté', color: '#f85149', bg: 'rgba(248,81,73,0.1)' },
};

export default function InboundPage() {
  const [leads, setLeads] = useState<InboundLead[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<InboundLead | null>(null);
  const [statusFilter, setStatusFilter] = useState<'all' | InboundLead['status']>('all');
  const [enrichingId, setEnrichingId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'leads' | 'config'>('leads');

  // Config state
  const [webhookUrl, setWebhookUrl] = useState('');
  const [typeformKey, setTypeformKey] = useState('');
  const [hubspotToken, setHubspotToken] = useState('');

  useEffect(() => {
    loadLeads();
    loadWebhookConfig();
  }, []);

  const loadLeads = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/inbound/leads/?limit=100');
      setLeads(data.items || []);
    } catch { setLeads([]); } finally { setLoading(false); }
  };

  const loadWebhookConfig = async () => {
    try {
      const data = await apiClient.get('/inbound/config');
      setWebhookUrl(data.webhook_url || '');
      setTypeformKey(data.typeform_key || '');
      setHubspotToken(data.hubspot_token || '');
    } catch { }
  };

  const enrichLead = async (lead: InboundLead) => {
    setEnrichingId(lead.id);
    try {
      await apiClient.post(`/inbound/leads/${lead.id}/enrich`, {});
      loadLeads();
    } finally { setEnrichingId(null); }
  };

  const convertToProspect = async (lead: InboundLead) => {
    await apiClient.post(`/inbound/leads/${lead.id}/convert`, {});
    setLeads(prev => prev.map(l => l.id === lead.id ? { ...l, status: 'converted' } : l));
    setSelected(null);
  };

  const rejectLead = async (id: string) => {
    await apiClient.patch(`/inbound/leads/${id}`, { status: 'rejected' });
    setLeads(prev => prev.map(l => l.id === id ? { ...l, status: 'rejected' } : l));
  };

  const filtered = leads.filter(l => statusFilter === 'all' || l.status === statusFilter);

  const counts = {
    new: leads.filter(l => l.status === 'new').length,
    enriched: leads.filter(l => l.status === 'enriched').length,
    converted: leads.filter(l => l.status === 'converted').length,
  };

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%', boxSizing: 'border-box', overflow: 'hidden' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Inbound Enrichment
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
            Capture et enrichissement automatique des leads entrants
          </p>
        </div>
        <button onClick={loadLeads} style={{
          padding: '0.5rem 0.875rem', borderRadius: '8px',
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.8125rem',
        }}>↻ Actualiser</button>
      </div>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.875rem' }}>
        {[
          { label: 'Nouveaux leads', value: counts.new, color: '#2f81f7', icon: '📥' },
          { label: 'Leads enrichis', value: counts.enriched, color: '#8b5cf6', icon: '⚡' },
          { label: 'Convertis en prospects', value: counts.converted, color: '#3fb950', icon: '✅' },
        ].map(kpi => (
          <div key={kpi.label} style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-color)',
            borderRadius: '10px', padding: '1rem 1.25rem',
            display: 'flex', alignItems: 'center', gap: '1rem',
          }}>
            <div style={{
              width: '44px', height: '44px', borderRadius: '10px',
              background: `${kpi.color}22`, display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontSize: '1.25rem',
            }}>
              {kpi.icon}
            </div>
            <div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: kpi.color }}>{kpi.value}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{kpi.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0', borderBottom: '1px solid var(--border-color)' }}>
        {[
          { id: 'leads' as const, label: '📥 Leads entrants' },
          { id: 'config' as const, label: '⚙️ Configuration sources' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '0.75rem 1.25rem', border: 'none',
              borderBottom: '2px solid',
              borderBottomColor: activeTab === tab.id ? 'var(--accent-blue)' : 'transparent',
              background: 'none',
              color: activeTab === tab.id ? 'var(--accent-blue)' : 'var(--text-secondary)',
              cursor: 'pointer', fontSize: '0.875rem',
              fontWeight: activeTab === tab.id ? 600 : 400,
            }}
          >{tab.label}</button>
        ))}
      </div>

      {/* LEADS TAB */}
      {activeTab === 'leads' && (
        <div style={{ flex: 1, display: 'flex', gap: '1rem', overflow: 'hidden' }}>
          {/* List */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.75rem', overflow: 'auto' }}>
            {/* Status filters */}
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {(['all', 'new', 'processing', 'enriched', 'converted', 'rejected'] as const).map(s => {
                const cfg = s === 'all' ? { label: 'Tous', color: 'var(--accent-blue)', bg: 'rgba(47,129,247,0.1)' } : STATUS_CONFIG[s];
                const count = s === 'all' ? leads.length : leads.filter(l => l.status === s).length;
                return (
                  <button
                    key={s}
                    onClick={() => setStatusFilter(s)}
                    style={{
                      padding: '0.3rem 0.75rem', borderRadius: '20px', border: '1px solid',
                      borderColor: statusFilter === s ? cfg.color : 'var(--border-color)',
                      background: statusFilter === s ? cfg.bg : 'var(--bg-card)',
                      color: statusFilter === s ? cfg.color : 'var(--text-secondary)',
                      cursor: 'pointer', fontSize: '0.8125rem', transition: 'all 0.15s',
                    }}
                  >
                    {cfg.label} <span style={{ opacity: 0.7 }}>({count})</span>
                  </button>
                );
              })}
            </div>

            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} style={{ height: '72px', background: 'var(--bg-card)', borderRadius: '8px', animation: 'pulse 1.5s ease infinite' }} />
              ))
            ) : filtered.length === 0 ? (
              <div style={{
                textAlign: 'center', padding: '4rem',
                border: '1px dashed var(--border-color)', borderRadius: '10px', color: 'var(--text-muted)',
              }}>
                <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>📥</div>
                <p>Aucun lead {statusFilter !== 'all' ? `"${STATUS_CONFIG[statusFilter]?.label}"` : ''}</p>
              </div>
            ) : (
              filtered.map(lead => {
                const srcCfg = SOURCE_CONFIG[lead.source] || SOURCE_CONFIG.other;
                const staCfg = STATUS_CONFIG[lead.status];
                const isSelected = selected?.id === lead.id;
                return (
                  <div
                    key={lead.id}
                    onClick={() => setSelected(isSelected ? null : lead)}
                    style={{
                      background: isSelected ? 'rgba(47,129,247,0.06)' : 'var(--bg-card)',
                      border: `1px solid ${isSelected ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
                      borderLeft: `4px solid ${srcCfg.color}`,
                      borderRadius: '8px', padding: '0.875rem',
                      cursor: 'pointer', transition: 'all 0.15s',
                      display: 'flex', alignItems: 'center', gap: '0.875rem',
                    }}
                  >
                    <div style={{ fontSize: '1.25rem', flexShrink: 0 }}>{srcCfg.icon}</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem' }}>
                          {lead.company_name || lead.contact_name || lead.email || 'Lead anonyme'}
                        </span>
                        <span style={{
                          padding: '1px 8px', borderRadius: '20px', fontSize: '0.7rem',
                          background: staCfg.bg, color: staCfg.color,
                        }}>{staCfg.label}</span>
                      </div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'flex', gap: '0.75rem' }}>
                        <span>{srcCfg.label}</span>
                        {lead.email && <span>📧 {lead.email}</span>}
                        {lead.phone && <span>📞 {lead.phone}</span>}
                        <span>{new Date(lead.received_at).toLocaleDateString('fr-FR')}</span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.375rem', flexShrink: 0 }}>
                      {lead.status === 'new' && (
                        <button
                          onClick={e => { e.stopPropagation(); enrichLead(lead); }}
                          disabled={enrichingId === lead.id}
                          style={{
                            padding: '0.25rem 0.625rem', borderRadius: '6px',
                            background: 'rgba(47,129,247,0.1)', border: '1px solid rgba(47,129,247,0.3)',
                            color: 'var(--accent-blue)', fontSize: '0.75rem', cursor: 'pointer',
                          }}
                        >
                          {enrichingId === lead.id ? '...' : '⚡ Enrichir'}
                        </button>
                      )}
                      {lead.status === 'enriched' && (
                        <button
                          onClick={e => { e.stopPropagation(); convertToProspect(lead); }}
                          style={{
                            padding: '0.25rem 0.625rem', borderRadius: '6px',
                            background: 'rgba(63,185,80,0.1)', border: '1px solid rgba(63,185,80,0.3)',
                            color: 'var(--accent-green)', fontSize: '0.75rem', cursor: 'pointer',
                          }}
                        >✅ Convertir</button>
                      )}
                      {!['converted', 'rejected'].includes(lead.status) && (
                        <button
                          onClick={e => { e.stopPropagation(); rejectLead(lead.id); }}
                          style={{
                            padding: '0.25rem 0.625rem', borderRadius: '6px',
                            background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                            color: 'var(--text-muted)', fontSize: '0.75rem', cursor: 'pointer',
                          }}
                        >✕</button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Detail panel */}
          {selected && (
            <div style={{
              width: '320px', minWidth: '320px',
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '10px', padding: '1.25rem', overflow: 'auto',
            }}>
              <h3 style={{ color: 'var(--text-primary)', margin: '0 0 1rem', fontSize: '0.9375rem' }}>
                Détail du lead
              </h3>
              {Object.entries(selected).filter(([k]) => !['id', 'raw_data'].includes(k)).map(([key, value]) => (
                <div key={key} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                  padding: '0.375rem 0', borderBottom: '1px solid var(--border-color)',
                }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{key}</span>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', maxWidth: '60%', textAlign: 'right', wordBreak: 'break-all' }}>
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
              {selected.raw_data && (
                <div style={{ marginTop: '1rem' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '0.5rem' }}>Raw data</div>
                  <pre style={{ color: 'var(--text-secondary)', fontSize: '0.7rem', background: 'var(--bg-secondary)', borderRadius: '6px', padding: '0.75rem', overflow: 'auto', margin: 0 }}>
                    {JSON.stringify(selected.raw_data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* CONFIG TAB */}
      {activeTab === 'config' && (
        <div style={{ flex: 1, overflow: 'auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', maxWidth: '800px' }}>
            {[
              {
                title: '📝 Typeform', description: 'Capture automatique des formulaires Typeform',
                field: typeformKey, setField: setTypeformKey,
                label: 'Clé API Typeform', placeholder: 'tfp_xxxxxxxxx',
                webhook: `${webhookUrl}/api/v1/inbound/typeform`,
              },
              {
                title: '🟠 HubSpot', description: 'Synchronisation des contacts HubSpot',
                field: hubspotToken, setField: setHubspotToken,
                label: 'Token HubSpot', placeholder: 'pat-eu1-xxxxxxxx',
                webhook: `${webhookUrl}/api/v1/inbound/hubspot`,
              },
            ].map(src => (
              <div key={src.title} style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: '10px', padding: '1.25rem',
              }}>
                <h3 style={{ color: 'var(--text-primary)', margin: '0 0 0.375rem', fontSize: '0.9375rem' }}>{src.title}</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0 0 1rem' }}>{src.description}</p>

                <div style={{ marginBottom: '0.75rem' }}>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>{src.label}</label>
                  <input
                    type="password" value={src.field} onChange={e => src.setField(e.target.value)}
                    placeholder={src.placeholder}
                    style={{ width: '100%', padding: '0.5rem 0.75rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)', fontSize: '0.8125rem', outline: 'none', boxSizing: 'border-box' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>URL Webhook entrant</label>
                  <div style={{
                    background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                    borderRadius: '6px', padding: '0.5rem 0.75rem',
                    color: 'var(--text-secondary)', fontSize: '0.75rem', fontFamily: 'monospace',
                    wordBreak: 'break-all', cursor: 'pointer',
                  }}
                    onClick={() => navigator.clipboard.writeText(src.webhook)}
                    title="Cliquer pour copier"
                  >
                    📋 {src.webhook}
                  </div>
                </div>
              </div>
            ))}

            {/* Generic Webhook */}
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '10px', padding: '1.25rem', gridColumn: 'span 2',
            }}>
              <h3 style={{ color: 'var(--text-primary)', margin: '0 0 0.375rem', fontSize: '0.9375rem' }}>🔗 Webhook universel</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0 0 1rem' }}>
                Envoyez n'importe quel payload JSON vers cet endpoint. Les champs company, email, phone, name sont détectés automatiquement.
              </p>
              <div style={{
                background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                borderRadius: '8px', padding: '0.875rem',
                fontFamily: 'monospace', fontSize: '0.8125rem', color: 'var(--text-secondary)',
              }}>
                <div style={{ color: 'var(--accent-blue)', marginBottom: '0.25rem' }}>POST /api/v1/inbound/webhook</div>
                <div style={{ color: 'var(--text-muted)' }}>Authorization: Bearer {'<webhook_secret>'}</div>
                <div style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                  {`{ "company": "ACME", "email": "contact@acme.fr", "phone": "01 23 45 67 89" }`}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
}
