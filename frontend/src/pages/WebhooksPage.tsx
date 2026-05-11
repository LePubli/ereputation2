import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface Webhook {
  id: string;
  name: string;
  url: string;
  events: string[];
  enabled: boolean;
  secret?: string;
  last_triggered?: string;
  success_count?: number;
  error_count?: number;
  created_at: string;
}

interface WebhookLog {
  id: string;
  webhook_id: string;
  event: string;
  status: 'success' | 'error' | 'pending';
  response_code?: number;
  triggered_at: string;
  payload_preview?: string;
}

const AVAILABLE_EVENTS = [
  'prospect.created', 'prospect.updated', 'prospect.enriched',
  'prospect.stage_changed', 'signal.detected', 'sequence.sent',
  'inbound.lead_received', 'contact.found',
];

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [logs, setLogs] = useState<WebhookLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'list' | 'logs'>('list');
  const [testing, setTesting] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: '',
    url: '',
    events: [] as string[],
    enabled: true,
  });

  useEffect(() => {
    loadWebhooks();
    if (activeTab === 'logs') loadLogs();
  }, [activeTab]);

  const loadWebhooks = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/webhooks/?limit=50');
      setWebhooks(data.items || []);
    } catch { setWebhooks([]); } finally { setLoading(false); }
  };

  const loadLogs = async () => {
    try {
      const data = await apiClient.get('/webhooks/logs?limit=100');
      setLogs(data.items || []);
    } catch { setLogs([]); }
  };

  const createWebhook = async () => {
    if (!form.name || !form.url) return;
    try {
      await apiClient.post('/webhooks/', form);
      setShowCreate(false);
      setForm({ name: '', url: '', events: [], enabled: true });
      loadWebhooks();
    } catch { }
  };

  const toggleWebhook = async (wh: Webhook) => {
    await apiClient.patch(`/webhooks/${wh.id}`, { enabled: !wh.enabled });
    setWebhooks(prev => prev.map(w => w.id === wh.id ? { ...w, enabled: !wh.enabled } : w));
  };

  const deleteWebhook = async (id: string) => {
    if (!confirm('Supprimer ce webhook ?')) return;
    await apiClient.delete(`/webhooks/${id}`);
    setWebhooks(prev => prev.filter(w => w.id !== id));
    if (selectedId === id) setSelectedId(null);
  };

  const testWebhook = async (id: string) => {
    setTesting(id);
    try {
      await apiClient.post(`/webhooks/${id}/test`, {});
      alert('✅ Webhook testé avec succès !');
      loadLogs();
    } catch {
      alert('❌ Échec du test webhook');
    } finally { setTesting(null); }
  };

  const toggleEvent = (event: string) => {
    setForm(prev => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter(e => e !== event)
        : [...prev.events, event],
    }));
  };

  const selected = webhooks.find(w => w.id === selectedId);

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%', boxSizing: 'border-box', overflow: 'hidden' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Webhooks Sortants
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
            Notifications temps réel vers vos outils externes · {webhooks.filter(w => w.enabled).length} actifs
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          style={{
            padding: '0.5rem 1rem', borderRadius: '8px',
            background: 'var(--accent-blue)', border: 'none',
            color: '#fff', cursor: 'pointer', fontSize: '0.875rem',
          }}
        >+ Nouveau webhook</button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border-color)' }}>
        {[
          { id: 'list' as const, label: `🔗 Webhooks (${webhooks.length})` },
          { id: 'logs' as const, label: `📋 Logs (${logs.length})` },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '0.75rem 1.25rem', border: 'none',
              borderBottom: `2px solid ${activeTab === tab.id ? 'var(--accent-blue)' : 'transparent'}`,
              background: 'none',
              color: activeTab === tab.id ? 'var(--accent-blue)' : 'var(--text-secondary)',
              cursor: 'pointer', fontSize: '0.875rem',
              fontWeight: activeTab === tab.id ? 600 : 400,
            }}
          >{tab.label}</button>
        ))}
      </div>

      {/* LIST TAB */}
      {activeTab === 'list' && (
        <div style={{ flex: 1, display: 'flex', gap: '1rem', overflow: 'hidden' }}>
          {/* Webhook list */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.625rem', overflow: 'auto' }}>
            {loading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} style={{ height: '90px', background: 'var(--bg-card)', borderRadius: '8px', animation: 'pulse 1.5s ease infinite' }} />
              ))
            ) : webhooks.length === 0 ? (
              <div style={{
                textAlign: 'center', padding: '4rem',
                border: '1px dashed var(--border-color)', borderRadius: '10px', color: 'var(--text-muted)',
              }}>
                <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>🔗</div>
                <p>Aucun webhook configuré</p>
                <p style={{ fontSize: '0.8125rem' }}>Connectez vos outils : Zapier, Make, n8n, Slack...</p>
              </div>
            ) : (
              webhooks.map(wh => (
                <div
                  key={wh.id}
                  onClick={() => setSelectedId(selectedId === wh.id ? null : wh.id)}
                  style={{
                    background: selectedId === wh.id ? 'rgba(47,129,247,0.06)' : 'var(--bg-card)',
                    border: `1px solid ${selectedId === wh.id ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
                    borderLeft: `4px solid ${wh.enabled ? 'var(--accent-blue)' : 'var(--border-color)'}`,
                    borderRadius: '8px', padding: '1rem', cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem' }}>
                        {wh.name}
                      </span>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '0.125rem', fontFamily: 'monospace' }}>
                        {wh.url.length > 50 ? wh.url.slice(0, 50) + '...' : wh.url}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.375rem', alignItems: 'center' }}>
                      <button
                        onClick={e => { e.stopPropagation(); testWebhook(wh.id); }}
                        disabled={testing === wh.id}
                        style={{
                          padding: '0.25rem 0.625rem', borderRadius: '6px',
                          background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                          color: 'var(--text-secondary)', fontSize: '0.75rem', cursor: 'pointer',
                        }}
                      >{testing === wh.id ? '...' : '▶ Test'}</button>
                      <button
                        onClick={e => { e.stopPropagation(); toggleWebhook(wh); }}
                        style={{
                          width: '40px', height: '22px', borderRadius: '11px', border: 'none',
                          background: wh.enabled ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
                          cursor: 'pointer', position: 'relative', transition: 'background 0.2s',
                        }}
                      >
                        <div style={{
                          position: 'absolute', top: '3px', left: wh.enabled ? '20px' : '3px',
                          width: '16px', height: '16px', borderRadius: '50%', background: '#fff',
                          transition: 'left 0.2s',
                        }} />
                      </button>
                      <button
                        onClick={e => { e.stopPropagation(); deleteWebhook(wh.id); }}
                        style={{
                          padding: '0.25rem 0.5rem', borderRadius: '6px',
                          background: 'rgba(248,81,73,0.1)', border: '1px solid rgba(248,81,73,0.3)',
                          color: 'var(--accent-red)', fontSize: '0.75rem', cursor: 'pointer',
                        }}
                      >🗑️</button>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                    {wh.events.map(ev => (
                      <span key={ev} style={{
                        padding: '1px 7px', borderRadius: '4px', fontSize: '0.7rem',
                        background: 'rgba(47,129,247,0.1)', color: 'var(--accent-blue)',
                        border: '1px solid rgba(47,129,247,0.2)',
                      }}>{ev}</span>
                    ))}
                  </div>

                  <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                    <span style={{ color: 'var(--accent-green)' }}>✅ {wh.success_count || 0}</span>
                    <span style={{ color: 'var(--accent-red)' }}>❌ {wh.error_count || 0}</span>
                    {wh.last_triggered && <span>Dernier : {new Date(wh.last_triggered).toLocaleDateString('fr-FR')}</span>}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Detail - secret */}
          {selected && (
            <div style={{
              width: '280px', minWidth: '280px',
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '10px', padding: '1.25rem',
            }}>
              <h3 style={{ color: 'var(--text-primary)', margin: '0 0 1rem', fontSize: '0.9375rem' }}>🔐 Sécurité</h3>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>
                  Secret HMAC-SHA256
                </label>
                <div
                  style={{
                    background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                    borderRadius: '6px', padding: '0.5rem', fontFamily: 'monospace',
                    fontSize: '0.7rem', color: 'var(--text-secondary)', wordBreak: 'break-all',
                    cursor: 'pointer',
                  }}
                  onClick={() => selected.secret && navigator.clipboard.writeText(selected.secret)}
                  title="Cliquer pour copier"
                >
                  {selected.secret || 'Auto-généré à la création'}
                </div>
              </div>
              <div style={{
                background: 'rgba(47,129,247,0.08)', border: '1px solid rgba(47,129,247,0.2)',
                borderRadius: '8px', padding: '0.75rem',
                color: 'var(--text-secondary)', fontSize: '0.75rem', lineHeight: 1.5,
              }}>
                Vérifiez la signature <code style={{ color: 'var(--accent-blue)' }}>X-Webhook-Signature</code> dans les headers pour authentifier les requêtes.
              </div>
            </div>
          )}
        </div>
      )}

      {/* LOGS TAB */}
      {activeTab === 'logs' && (
        <div style={{ flex: 1, overflow: 'auto' }}>
          {logs.length === 0 ? (
            <div style={{
              textAlign: 'center', padding: '4rem',
              border: '1px dashed var(--border-color)', borderRadius: '10px', color: 'var(--text-muted)',
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>📋</div>
              Aucun log disponible
            </div>
          ) : (
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '10px', overflow: 'hidden',
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary)' }}>
                    {['Statut', 'Événement', 'Webhook', 'Code HTTP', 'Date'].map(h => (
                      <th key={h} style={{
                        padding: '0.625rem 0.875rem', textAlign: 'left',
                        color: 'var(--text-muted)', fontSize: '0.75rem',
                        fontWeight: 600, textTransform: 'uppercase',
                        borderBottom: '1px solid var(--border-color)',
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {logs.map(log => {
                    const wh = webhooks.find(w => w.id === log.webhook_id);
                    const statusColor = log.status === 'success' ? 'var(--accent-green)' : log.status === 'error' ? 'var(--accent-red)' : 'var(--accent-orange)';
                    return (
                      <tr key={log.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '0.625rem 0.875rem' }}>
                          <span style={{ color: statusColor, fontSize: '0.8125rem' }}>
                            {log.status === 'success' ? '✅' : log.status === 'error' ? '❌' : '⏳'}
                          </span>
                        </td>
                        <td style={{ padding: '0.625rem 0.875rem' }}>
                          <span style={{
                            padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem',
                            background: 'rgba(47,129,247,0.1)', color: 'var(--accent-blue)',
                          }}>{log.event}</span>
                        </td>
                        <td style={{ padding: '0.625rem 0.875rem', color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>
                          {wh?.name || log.webhook_id.slice(0, 8)}
                        </td>
                        <td style={{ padding: '0.625rem 0.875rem', color: log.response_code && log.response_code < 300 ? 'var(--accent-green)' : 'var(--accent-red)', fontSize: '0.8125rem' }}>
                          {log.response_code || '—'}
                        </td>
                        <td style={{ padding: '0.625rem 0.875rem', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                          {new Date(log.triggered_at).toLocaleString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div
          style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={e => e.target === e.currentTarget && setShowCreate(false)}
        >
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-color)',
            borderRadius: '12px', padding: '1.5rem', width: '560px', maxWidth: '95vw',
            boxShadow: '0 24px 64px rgba(0,0,0,0.5)', maxHeight: '85vh', overflow: 'auto',
          }}>
            <h2 style={{ color: 'var(--text-primary)', margin: '0 0 1.25rem', fontSize: '1rem' }}>+ Nouveau webhook</h2>

            {[
              { label: 'Nom', key: 'name' as const, placeholder: 'Ex: Notification Slack' },
              { label: 'URL cible', key: 'url' as const, placeholder: 'https://hooks.slack.com/...' },
            ].map(f => (
              <div key={f.key} style={{ marginBottom: '0.875rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>{f.label}</label>
                <input
                  type="text" placeholder={f.placeholder}
                  value={form[f.key]}
                  onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                  style={{
                    width: '100%', padding: '0.5rem 0.75rem',
                    background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                    borderRadius: '6px', color: 'var(--text-primary)', fontSize: '0.875rem',
                    outline: 'none', boxSizing: 'border-box',
                  }}
                />
              </div>
            ))}

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                Événements déclencheurs
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
                {AVAILABLE_EVENTS.map(ev => (
                  <button
                    key={ev}
                    onClick={() => toggleEvent(ev)}
                    style={{
                      padding: '0.25rem 0.75rem', borderRadius: '20px', cursor: 'pointer',
                      background: form.events.includes(ev) ? 'rgba(47,129,247,0.15)' : 'var(--bg-tertiary)',
                      border: `1px solid ${form.events.includes(ev) ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
                      color: form.events.includes(ev) ? 'var(--accent-blue)' : 'var(--text-secondary)',
                      fontSize: '0.75rem', transition: 'all 0.1s',
                    }}
                  >{ev}</button>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
              <button onClick={() => setShowCreate(false)} style={{ padding: '0.5rem 1rem', borderRadius: '8px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.875rem' }}>Annuler</button>
              <button onClick={createWebhook} disabled={!form.name || !form.url} style={{ padding: '0.5rem 1rem', borderRadius: '8px', background: 'var(--accent-blue)', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '0.875rem', opacity: !form.name || !form.url ? 0.6 : 1 }}>Créer</button>
            </div>
          </div>
        </div>
      )}

      <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
}
