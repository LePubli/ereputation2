import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface SyncJob {
  id: string;
  direction: 'push' | 'pull' | 'bidirectional';
  status: 'idle' | 'running' | 'completed' | 'failed';
  records_processed?: number;
  records_created?: number;
  records_updated?: number;
  records_skipped?: number;
  errors?: number;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
}

interface HubSpotContact {
  id: string;
  firstname?: string;
  lastname?: string;
  email?: string;
  company?: string;
  phone?: string;
  lifecyclestage?: string;
  hs_lead_status?: string;
  synced: boolean;
}

interface SyncConfig {
  hubspot_token: string;
  auto_sync: boolean;
  sync_interval_hours: number;
  push_fields: string[];
  pull_fields: string[];
  create_missing: boolean;
  update_existing: boolean;
  conflict_resolution: 'local_wins' | 'remote_wins' | 'newest_wins';
}

const FIELD_OPTIONS = [
  { key: 'company_name', label: 'Nom entreprise', hs: 'company' },
  { key: 'email', label: 'Email', hs: 'email' },
  { key: 'phone', label: 'Téléphone', hs: 'phone' },
  { key: 'website', label: 'Site web', hs: 'website' },
  { key: 'city', label: 'Ville', hs: 'city' },
  { key: 'region', label: 'Région', hs: 'state' },
  { key: 'employee_count', label: 'Effectif', hs: 'numberofemployees' },
  { key: 'pipeline_stage', label: 'Étape pipeline', hs: 'lifecyclestage' },
];

export default function CRMSyncPage() {
  const [config, setConfig] = useState<SyncConfig>({
    hubspot_token: '',
    auto_sync: false,
    sync_interval_hours: 24,
    push_fields: ['company_name', 'email', 'phone', 'website', 'pipeline_stage'],
    pull_fields: ['email', 'phone', 'company_name'],
    create_missing: true,
    update_existing: true,
    conflict_resolution: 'newest_wins',
  });
  const [jobs, setJobs] = useState<SyncJob[]>([]);
  const [contacts, setContacts] = useState<HubSpotContact[]>([]);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'config' | 'contacts'>('dashboard');
  const [syncing, setSyncing] = useState<'push' | 'pull' | 'bidirectional' | null>(null);
  const [connected, setConnected] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadHistory();
    loadConfig();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await apiClient.get('/crm-sync/history?limit=20');
      setJobs(data.items || []);
    } catch { setJobs([]); }
  };

  const loadConfig = async () => {
    try {
      const data = await apiClient.get('/crm-sync/config');
      if (data.hubspot_token) {
        setConfig(data);
        setConnected(true);
      }
    } catch { }
  };

  const testConnection = async () => {
    setTesting(true);
    try {
      await apiClient.post('/crm-sync/test', { token: config.hubspot_token });
      setConnected(true);
      alert('✅ Connexion HubSpot réussie !');
    } catch {
      setConnected(false);
      alert('❌ Token HubSpot invalide');
    } finally { setTesting(false); }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      await apiClient.post('/crm-sync/config', config);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } finally { setSaving(false); }
  };

  const triggerSync = async (direction: 'push' | 'pull' | 'bidirectional') => {
    setSyncing(direction);
    try {
      const job = await apiClient.post('/crm-sync/sync', { direction });
      setJobs(prev => [job, ...prev]);
      // Poll for completion
      const poll = setInterval(async () => {
        try {
          const updated = await apiClient.get(`/crm-sync/jobs/${job.id}`);
          setJobs(prev => prev.map(j => j.id === job.id ? updated : j));
          if (updated.status !== 'running') {
            clearInterval(poll);
            setSyncing(null);
          }
        } catch { clearInterval(poll); setSyncing(null); }
      }, 2000);
    } catch { setSyncing(null); }
  };

  const loadHubSpotContacts = async () => {
    try {
      const data = await apiClient.get('/crm-sync/hubspot/contacts?limit=50');
      setContacts(data.contacts || []);
    } catch { setContacts([]); }
  };

  const lastJob = jobs[0];
  const totalSynced = jobs.filter(j => j.status === 'completed').reduce((a, j) => a + (j.records_processed || 0), 0);

  const togglePushField = (key: string) =>
    setConfig(prev => ({
      ...prev,
      push_fields: prev.push_fields.includes(key)
        ? prev.push_fields.filter(f => f !== key)
        : [...prev.push_fields, key],
    }));

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%', boxSizing: 'border-box', overflow: 'hidden' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            CRM Sync — HubSpot
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
            Synchronisation bidirectionnelle avec HubSpot CRM
          </p>
        </div>

        {/* Connection status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.375rem 0.875rem', borderRadius: '20px',
            background: connected ? 'rgba(63,185,80,0.1)' : 'rgba(248,81,73,0.1)',
            border: `1px solid ${connected ? 'rgba(63,185,80,0.3)' : 'rgba(248,81,73,0.3)'}`,
          }}>
            <div style={{
              width: '8px', height: '8px', borderRadius: '50%',
              background: connected ? 'var(--accent-green)' : 'var(--accent-red)',
              boxShadow: connected ? '0 0 6px var(--accent-green)' : 'none',
            }} />
            <span style={{ color: connected ? 'var(--accent-green)' : 'var(--accent-red)', fontSize: '0.8125rem', fontWeight: 600 }}>
              {connected ? 'Connecté' : 'Non connecté'}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)' }}>
        {[
          { id: 'dashboard' as const, label: '📊 Dashboard' },
          { id: 'config' as const, label: '⚙️ Configuration' },
          { id: 'contacts' as const, label: '👤 Contacts HubSpot' },
        ].map(tab => (
          <button key={tab.id} onClick={() => { setActiveTab(tab.id); if (tab.id === 'contacts' && connected) loadHubSpotContacts(); }} style={{
            padding: '0.75rem 1.25rem', border: 'none',
            borderBottom: `2px solid ${activeTab === tab.id ? 'var(--accent-blue)' : 'transparent'}`,
            background: 'none',
            color: activeTab === tab.id ? 'var(--accent-blue)' : 'var(--text-secondary)',
            cursor: 'pointer', fontSize: '0.875rem',
            fontWeight: activeTab === tab.id ? 600 : 400,
          }}>{tab.label}</button>
        ))}
      </div>

      {/* ── DASHBOARD ── */}
      {activeTab === 'dashboard' && (
        <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* KPIs */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.875rem' }}>
            {[
              { label: 'Total synchronisés', value: totalSynced.toLocaleString('fr-FR'), icon: '🔄', color: '#2f81f7' },
              { label: 'Dernière synchro', value: lastJob?.completed_at ? new Date(lastJob.completed_at).toLocaleDateString('fr-FR') : '—', icon: '🕐', color: '#d29922' },
              { label: 'Statut', value: lastJob?.status === 'completed' ? 'OK' : lastJob?.status || 'Aucune', icon: '✅', color: lastJob?.status === 'completed' ? '#3fb950' : '#8b949e' },
            ].map(kpi => (
              <div key={kpi.label} style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: '10px', padding: '1rem 1.25rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{kpi.label}</span>
                  <span>{kpi.icon}</span>
                </div>
                <div style={{ fontSize: '1.375rem', fontWeight: 700, color: kpi.color }}>{kpi.value}</div>
              </div>
            ))}
          </div>

          {/* Sync actions */}
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-color)',
            borderRadius: '10px', padding: '1.5rem',
          }}>
            <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600, margin: '0 0 1.25rem' }}>
              🔄 Synchronisation manuelle
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.875rem' }}>
              {[
                {
                  dir: 'push' as const, icon: '⬆️', label: 'Push vers HubSpot',
                  desc: 'Envoyer vos prospects dans HubSpot',
                  color: 'var(--accent-blue)',
                },
                {
                  dir: 'pull' as const, icon: '⬇️', label: 'Pull depuis HubSpot',
                  desc: 'Importer les contacts HubSpot',
                  color: 'var(--accent-green)',
                },
                {
                  dir: 'bidirectional' as const, icon: '↕️', label: 'Sync bidirectionnel',
                  desc: 'Push + Pull simultané avec résolution de conflits',
                  color: '#8b5cf6',
                },
              ].map(item => (
                <button
                  key={item.dir}
                  onClick={() => triggerSync(item.dir)}
                  disabled={!!syncing || !connected}
                  style={{
                    padding: '1.25rem', borderRadius: '10px', cursor: syncing || !connected ? 'not-allowed' : 'pointer',
                    background: syncing === item.dir ? `${item.color}18` : 'var(--bg-secondary)',
                    border: `1px solid ${syncing === item.dir ? item.color : 'var(--border-color)'}`,
                    textAlign: 'left', transition: 'all 0.15s',
                    opacity: !connected ? 0.5 : 1,
                  }}
                >
                  <div style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>
                    {syncing === item.dir ? (
                      <span style={{
                        display: 'inline-block', width: '28px', height: '28px',
                        border: `3px solid ${item.color}44`,
                        borderTopColor: item.color, borderRadius: '50%',
                        animation: 'spin 0.7s linear infinite',
                      }} />
                    ) : item.icon}
                  </div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9375rem', marginBottom: '0.25rem' }}>
                    {item.label}
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>{item.desc}</div>
                </button>
              ))}
            </div>
            {!connected && (
              <div style={{
                marginTop: '1rem', padding: '0.75rem 1rem',
                background: 'rgba(248,81,73,0.08)', border: '1px solid rgba(248,81,73,0.2)',
                borderRadius: '8px', color: 'var(--accent-red)', fontSize: '0.875rem',
              }}>
                ⚠️ Configurez votre token HubSpot dans l'onglet Configuration pour activer la synchronisation.
              </div>
            )}
          </div>

          {/* Sync history */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', overflow: 'hidden' }}>
            <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-color)' }}>
              <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600, margin: 0 }}>
                📋 Historique de synchronisation
              </h3>
            </div>
            {jobs.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                Aucune synchronisation effectuée
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary)' }}>
                    {['Direction', 'Statut', 'Traités', 'Créés', 'MÀJ', 'Erreurs', 'Durée', 'Date'].map(h => (
                      <th key={h} style={{ padding: '0.5rem 0.875rem', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', borderBottom: '1px solid var(--border-color)' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {jobs.map(job => {
                    const stColor = { completed: '#3fb950', running: '#d29922', failed: '#f85149', idle: '#8b949e' }[job.status];
                    return (
                      <tr key={job.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '0.625rem 0.875rem' }}>
                          <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                            {{ push: '⬆️ Push', pull: '⬇️ Pull', bidirectional: '↕️ Bidirectionnel' }[job.direction]}
                          </span>
                        </td>
                        <td style={{ padding: '0.625rem 0.875rem' }}>
                          <span style={{ color: stColor, fontSize: '0.8125rem', fontWeight: 600 }}>{job.status}</span>
                        </td>
                        <td style={{ padding: '0.625rem 0.875rem', color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>{job.records_processed ?? '—'}</td>
                        <td style={{ padding: '0.625rem 0.875rem', color: '#3fb950', fontSize: '0.8125rem' }}>{job.records_created ?? '—'}</td>
                        <td style={{ padding: '0.625rem 0.875rem', color: '#2f81f7', fontSize: '0.8125rem' }}>{job.records_updated ?? '—'}</td>
                        <td style={{ padding: '0.625rem 0.875rem', color: job.errors ? '#f85149' : 'var(--text-muted)', fontSize: '0.8125rem' }}>{job.errors ?? 0}</td>
                        <td style={{ padding: '0.625rem 0.875rem', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>{job.duration_seconds ? `${job.duration_seconds}s` : '—'}</td>
                        <td style={{ padding: '0.625rem 0.875rem', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                          {job.started_at ? new Date(job.started_at).toLocaleString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ── CONFIG ── */}
      {activeTab === 'config' && (
        <div style={{ flex: 1, overflow: 'auto' }}>
          <div style={{ maxWidth: '700px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>

            {/* Token */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1.25rem' }}>
              <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600, margin: '0 0 1rem' }}>🔑 Authentification HubSpot</h3>
              <div style={{ marginBottom: '0.875rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>
                  Token d'accès privé (Private App Token)
                </label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input
                    type="password"
                    placeholder="pat-eu1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                    value={config.hubspot_token}
                    onChange={e => setConfig(p => ({ ...p, hubspot_token: e.target.value }))}
                    style={{ flex: 1, padding: '0.5625rem 0.875rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)', fontSize: '0.875rem', outline: 'none' }}
                  />
                  <button onClick={testConnection} disabled={testing || !config.hubspot_token} style={{
                    padding: '0.5rem 1rem', borderRadius: '8px',
                    background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                    color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.875rem', whiteSpace: 'nowrap',
                    opacity: testing || !config.hubspot_token ? 0.6 : 1,
                  }}>
                    {testing ? '...' : '🔌 Tester'}
                  </button>
                </div>
              </div>
              <div style={{
                padding: '0.75rem', background: 'rgba(47,129,247,0.06)', borderRadius: '8px',
                color: 'var(--text-secondary)', fontSize: '0.8125rem', lineHeight: 1.5,
              }}>
                ℹ️ Créez une <strong>Private App</strong> dans HubSpot (Settings → Integrations → Private Apps) avec les scopes : <code style={{ color: 'var(--accent-blue)' }}>crm.objects.contacts.read/write</code>
              </div>
            </div>

            {/* Auto-sync */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1.25rem' }}>
              <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600, margin: '0 0 1rem' }}>⏱️ Synchronisation automatique</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                <SyncToggle label="Activer la synchro automatique" value={config.auto_sync} onChange={v => setConfig(p => ({ ...p, auto_sync: v }))} />
                {config.auto_sync && (
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>Fréquence</label>
                    <select value={config.sync_interval_hours} onChange={e => setConfig(p => ({ ...p, sync_interval_hours: parseInt(e.target.value) }))}
                      style={{ padding: '0.5rem 0.75rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)', fontSize: '0.875rem', outline: 'none' }}>
                      <option value={1}>Chaque heure</option>
                      <option value={6}>Toutes les 6 heures</option>
                      <option value={12}>Toutes les 12 heures</option>
                      <option value={24}>Une fois par jour</option>
                      <option value={168}>Une fois par semaine</option>
                    </select>
                  </div>
                )}
              </div>
            </div>

            {/* Field mapping */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1.25rem' }}>
              <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600, margin: '0 0 1rem' }}>🗺️ Mapping des champs (Push → HubSpot)</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                {FIELD_OPTIONS.map(f => (
                  <label key={f.key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', padding: '0.375rem' }}>
                    <input
                      type="checkbox"
                      checked={config.push_fields.includes(f.key)}
                      onChange={() => togglePushField(f.key)}
                      style={{ accentColor: 'var(--accent-blue)', cursor: 'pointer' }}
                    />
                    <div>
                      <div style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>{f.label}</div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontFamily: 'monospace' }}>→ {f.hs}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Conflict resolution */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1.25rem' }}>
              <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600, margin: '0 0 1rem' }}>⚔️ Résolution de conflits</h3>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {[
                  { value: 'local_wins', label: '🏠 Local prioritaire', desc: 'Vos données écrasent HubSpot' },
                  { value: 'remote_wins', label: '☁️ HubSpot prioritaire', desc: 'HubSpot écrase vos données' },
                  { value: 'newest_wins', label: '🕐 Le plus récent', desc: 'La donnée la plus récente gagne' },
                ].map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => setConfig(p => ({ ...p, conflict_resolution: opt.value as SyncConfig['conflict_resolution'] }))}
                    style={{
                      flex: 1, padding: '0.875rem', borderRadius: '8px', cursor: 'pointer', textAlign: 'left',
                      background: config.conflict_resolution === opt.value ? 'rgba(47,129,247,0.1)' : 'var(--bg-secondary)',
                      border: `1px solid ${config.conflict_resolution === opt.value ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
                    }}
                  >
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem' }}>{opt.label}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '0.125rem' }}>{opt.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Save */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', alignItems: 'center' }}>
              {saved && <span style={{ color: 'var(--accent-green)', fontSize: '0.875rem' }}>✅ Enregistré</span>}
              <button onClick={saveConfig} disabled={saving} style={{ padding: '0.625rem 1.5rem', borderRadius: '8px', background: 'var(--accent-blue)', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '0.875rem', fontWeight: 600 }}>
                {saving ? 'Enregistrement...' : 'Enregistrer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── CONTACTS ── */}
      {activeTab === 'contacts' && (
        <div style={{ flex: 1, overflow: 'auto' }}>
          {!connected ? (
            <div style={{ textAlign: 'center', padding: '4rem', border: '1px dashed var(--border-color)', borderRadius: '10px', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>🔌</div>
              <p>Configurez votre token HubSpot pour voir les contacts</p>
            </div>
          ) : contacts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '4rem', border: '1px dashed var(--border-color)', borderRadius: '10px', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>👤</div>
              <p>Chargement des contacts HubSpot...</p>
            </div>
          ) : (
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary)' }}>
                    {['Nom', 'Email', 'Entreprise', 'Téléphone', 'Lifecycle Stage', 'Synchronisé'].map(h => (
                      <th key={h} style={{ padding: '0.625rem 0.875rem', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', borderBottom: '1px solid var(--border-color)' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {contacts.map(c => (
                    <tr key={c.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '0.625rem 0.875rem', color: 'var(--text-primary)', fontSize: '0.875rem', fontWeight: 500 }}>
                        {[c.firstname, c.lastname].filter(Boolean).join(' ') || '—'}
                      </td>
                      <td style={{ padding: '0.625rem 0.875rem', color: 'var(--accent-blue)', fontSize: '0.8125rem' }}>{c.email || '—'}</td>
                      <td style={{ padding: '0.625rem 0.875rem', color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>{c.company || '—'}</td>
                      <td style={{ padding: '0.625rem 0.875rem', color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>{c.phone || '—'}</td>
                      <td style={{ padding: '0.625rem 0.875rem' }}>
                        {c.lifecyclestage && (
                          <span style={{ padding: '2px 8px', borderRadius: '20px', fontSize: '0.7rem', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)', border: '1px solid var(--border-color)' }}>
                            {c.lifecyclestage}
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '0.625rem 0.875rem' }}>
                        <span style={{ color: c.synced ? 'var(--accent-green)' : 'var(--text-muted)', fontSize: '0.8125rem' }}>
                          {c.synced ? '✅ Oui' : '⭕ Non'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

function SyncToggle({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{label}</span>
      <button onClick={() => onChange(!value)} style={{
        width: '44px', height: '24px', borderRadius: '12px', border: 'none',
        background: value ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
        cursor: 'pointer', position: 'relative', transition: 'background 0.2s',
      }}>
        <div style={{
          position: 'absolute', top: '3px', left: value ? '22px' : '3px',
          width: '18px', height: '18px', borderRadius: '50%', background: '#fff',
          transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
        }} />
      </button>
    </div>
  );
}
