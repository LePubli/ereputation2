import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface SourcingJob {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  source: string;
  config: {
    region?: string;
    naf_code?: string;
    city?: string;
    query?: string;
    limit?: number;
  };
  progress?: number;
  found_count?: number;
  new_count?: number;
  error?: string;
  created_at: string;
  completed_at?: string;
}

const SCRAPER_SOURCES = [
  { id: 'insee', label: 'INSEE', icon: '🇫🇷', description: 'Base SIRENE officielle — 12M+ entreprises', free: true },
  { id: 'pages_jaunes', label: 'Pages Jaunes', icon: '📒', description: 'Annuaire avec coordonnées', free: true },
  { id: 'google_maps', label: 'Google Maps', icon: '🗺️', description: 'Entreprises locales avec avis', free: true },
  { id: 'societe', label: 'Société.com', icon: '📊', description: 'Données financières et dirigeants', free: true },
  { id: 'pappers', label: 'Pappers', icon: '📋', description: 'RCS, statuts, dirigeants', free: true },
  { id: 'bodacc', label: 'BODACC', icon: '⚖️', description: 'Annonces légales et cessations', free: true },
  { id: 'trustpilot', label: 'Trustpilot', icon: '⭐', description: 'Notes et avis clients', free: true },
];

const NAF_CODES = [
  { code: '', label: 'Tous les secteurs' },
  { code: '47', label: '47 — Commerce de détail' },
  { code: '62', label: '62 — Activités informatiques' },
  { code: '56', label: '56 — Restauration' },
  { code: '41', label: '41 — Construction' },
  { code: '69', label: '69 — Droit et comptabilité' },
  { code: '70', label: '70 — Conseil aux entreprises' },
  { code: '74', label: '74 — Activités créatives' },
  { code: '73', label: '73 — Publicité et études de marché' },
  { code: '85', label: '85 — Enseignement' },
  { code: '86', label: '86 — Santé' },
  { code: '96', label: '96 — Autres services' },
];

const REGIONS = [
  '', 'Hauts-de-France', 'Île-de-France', 'Auvergne-Rhône-Alpes',
  'Bretagne', 'Occitanie', 'Normandie', 'Grand Est',
  'Nouvelle-Aquitaine', 'Pays de la Loire', "Provence-Alpes-Côte d'Azur",
];

const STATUS_CONFIG = {
  pending: { label: 'En attente', color: '#8b949e', icon: '⏳' },
  running: { label: 'En cours', color: '#d29922', icon: '⚙️' },
  completed: { label: 'Terminé', color: '#3fb950', icon: '✅' },
  failed: { label: 'Échoué', color: '#f85149', icon: '❌' },
};

export default function SourcingPage() {
  const [jobs, setJobs] = useState<SourcingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const [form, setForm] = useState({
    name: '',
    source: 'insee',
    region: '',
    naf_code: '',
    city: '',
    query: '',
    limit: 100,
  });

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadJobs = async () => {
    try {
      const data = await apiClient.get('/sourcing/jobs?limit=20');
      setJobs(data.items || []);
    } catch { } finally { setLoading(false); }
  };

  const launchJob = async () => {
    if (!form.name || !form.source) return;
    setLaunching(true);
    try {
      await apiClient.post('/sourcing/jobs', {
        name: form.name,
        source: form.source,
        config: {
          region: form.region || undefined,
          naf_code: form.naf_code || undefined,
          city: form.city || undefined,
          query: form.query || undefined,
          limit: form.limit,
        },
      });
      setShowForm(false);
      setForm({ name: '', source: 'insee', region: '', naf_code: '', city: '', query: '', limit: 100 });
      loadJobs();
    } finally { setLaunching(false); }
  };

  const cancelJob = async (id: string) => {
    await apiClient.post(`/sourcing/jobs/${id}/cancel`, {});
    loadJobs();
  };

  const runningJobs = jobs.filter(j => j.status === 'running');
  const completedToday = jobs.filter(j => j.status === 'completed' && j.completed_at && new Date(j.completed_at).toDateString() === new Date().toDateString());
  const totalFound = jobs.filter(j => j.status === 'completed').reduce((a, j) => a + (j.found_count || 0), 0);

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%', boxSizing: 'border-box', overflow: 'hidden' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Sourcing — Scraping en masse
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
            Alimentez votre base prospects via {SCRAPER_SOURCES.length} sources gratuites
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          style={{
            padding: '0.5rem 1rem', borderRadius: '8px',
            background: 'var(--accent-blue)', border: 'none',
            color: '#fff', cursor: 'pointer', fontSize: '0.875rem',
            display: 'flex', alignItems: 'center', gap: '0.5rem',
          }}
        >⚡ Lancer un scraping</button>
      </div>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.875rem' }}>
        {[
          { label: 'Jobs en cours', value: runningJobs.length, color: '#d29922', icon: '⚙️' },
          { label: 'Terminés aujourd\'hui', value: completedToday.length, color: '#3fb950', icon: '✅' },
          { label: 'Total prospects trouvés', value: totalFound.toLocaleString('fr-FR'), color: '#2f81f7', icon: '🏢' },
        ].map(kpi => (
          <div key={kpi.label} style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-color)',
            borderRadius: '10px', padding: '1rem 1.25rem',
            display: 'flex', alignItems: 'center', gap: '0.875rem',
          }}>
            <div style={{
              width: '44px', height: '44px', borderRadius: '10px',
              background: `${kpi.color}22`, display: 'flex',
              alignItems: 'center', justifyContent: 'center', fontSize: '1.25rem', flexShrink: 0,
            }}>{kpi.icon}</div>
            <div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: kpi.color, lineHeight: 1 }}>{kpi.value}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{kpi.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Jobs list */}
      <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} style={{ height: '80px', background: 'var(--bg-card)', borderRadius: '8px', animation: 'pulse 1.5s ease infinite' }} />
          ))
        ) : jobs.length === 0 ? (
          <div style={{
            textAlign: 'center', padding: '4rem',
            border: '1px dashed var(--border-color)', borderRadius: '10px', color: 'var(--text-muted)',
          }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🔍</div>
            <p style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Aucun job de scraping</p>
            <p style={{ fontSize: '0.875rem' }}>Lancez votre premier scraping pour alimenter votre base prospects</p>
          </div>
        ) : (
          jobs.map(job => {
            const statusCfg = STATUS_CONFIG[job.status];
            const src = SCRAPER_SOURCES.find(s => s.id === job.source);
            return (
              <div key={job.id} style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderLeft: `4px solid ${statusCfg.color}`,
                borderRadius: '8px', padding: '1rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.625rem' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem' }}>{job.name}</span>
                      <span style={{
                        padding: '1px 8px', borderRadius: '20px', fontSize: '0.7rem',
                        background: `${statusCfg.color}22`, color: statusCfg.color,
                      }}>
                        {statusCfg.icon} {statusCfg.label}
                      </span>
                      {src && (
                        <span style={{
                          padding: '1px 8px', borderRadius: '4px', fontSize: '0.7rem',
                          background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
                        }}>
                          {src.icon} {src.label}
                        </span>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      {job.config.region && <span>📍 {job.config.region}</span>}
                      {job.config.naf_code && <span>🏭 NAF {job.config.naf_code}</span>}
                      {job.config.city && <span>🏙️ {job.config.city}</span>}
                      <span>🎯 Limite: {job.config.limit}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexShrink: 0 }}>
                    {(job.found_count !== undefined) && (
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#3fb950' }}>{job.found_count}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          +{job.new_count || 0} nouveaux
                        </div>
                      </div>
                    )}
                    {job.status === 'running' && (
                      <button
                        onClick={() => cancelJob(job.id)}
                        style={{
                          padding: '0.25rem 0.625rem', borderRadius: '6px',
                          background: 'rgba(248,81,73,0.1)', border: '1px solid rgba(248,81,73,0.3)',
                          color: 'var(--accent-red)', fontSize: '0.75rem', cursor: 'pointer',
                        }}
                      >✕ Annuler</button>
                    )}
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                      {new Date(job.created_at).toLocaleString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>

                {/* Progress bar */}
                {job.status === 'running' && (
                  <div>
                    <div style={{ height: '4px', background: 'var(--bg-tertiary)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', borderRadius: '2px',
                        background: 'linear-gradient(90deg, var(--accent-blue), #8b5cf6)',
                        width: job.progress !== undefined ? `${job.progress}%` : '100%',
                        animation: job.progress === undefined ? 'shimmer 1.5s infinite' : 'none',
                        transition: 'width 0.3s ease',
                      }} />
                    </div>
                    {job.progress !== undefined && (
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginTop: '0.25rem', textAlign: 'right' }}>
                        {job.progress}%
                      </div>
                    )}
                  </div>
                )}

                {job.status === 'failed' && job.error && (
                  <div style={{
                    marginTop: '0.5rem', padding: '0.5rem 0.75rem',
                    background: 'rgba(248,81,73,0.08)', borderRadius: '6px',
                    color: 'var(--accent-red)', fontSize: '0.75rem',
                  }}>
                    ⚠️ {job.error}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Create job modal */}
      {showForm && (
        <div
          style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}
          onClick={e => e.target === e.currentTarget && setShowForm(false)}
        >
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-color)',
            borderRadius: '12px', padding: '1.5rem', width: '640px', maxWidth: '95vw',
            boxShadow: '0 24px 64px rgba(0,0,0,0.5)', maxHeight: '90vh', overflow: 'auto',
          }}>
            <h2 style={{ color: 'var(--text-primary)', margin: '0 0 1.5rem', fontSize: '1.0625rem' }}>
              ⚡ Nouveau job de scraping
            </h2>

            {/* Job name */}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>Nom du job *</label>
              <input
                type="text" placeholder="Ex: PME Nord-Pas-de-Calais — Informatique"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                style={{ width: '100%', padding: '0.5rem 0.75rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)', fontSize: '0.875rem', outline: 'none', boxSizing: 'border-box' }}
              />
            </div>

            {/* Source selection */}
            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Source *</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
                {SCRAPER_SOURCES.map(src => (
                  <button
                    key={src.id}
                    onClick={() => setForm(f => ({ ...f, source: src.id }))}
                    style={{
                      padding: '0.75rem', borderRadius: '8px', cursor: 'pointer', textAlign: 'left',
                      background: form.source === src.id ? 'rgba(47,129,247,0.1)' : 'var(--bg-secondary)',
                      border: `1px solid ${form.source === src.id ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
                      transition: 'all 0.1s',
                    }}
                  >
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem', marginBottom: '0.125rem' }}>
                      {src.icon} {src.label}
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{src.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Filters */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>Région</label>
                <select value={form.region} onChange={e => setForm(f => ({ ...f, region: e.target.value }))}
                  style={{ width: '100%', padding: '0.5rem 0.75rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: form.region ? 'var(--text-primary)' : 'var(--text-muted)', fontSize: '0.875rem', outline: 'none' }}>
                  {REGIONS.map(r => <option key={r} value={r}>{r || 'Toutes les régions'}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>Secteur NAF</label>
                <select value={form.naf_code} onChange={e => setForm(f => ({ ...f, naf_code: e.target.value }))}
                  style={{ width: '100%', padding: '0.5rem 0.75rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: form.naf_code ? 'var(--text-primary)' : 'var(--text-muted)', fontSize: '0.875rem', outline: 'none' }}>
                  {NAF_CODES.map(n => <option key={n.code} value={n.code}>{n.label}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>Ville / Code postal</label>
                <input type="text" placeholder="Ex: Lille, 59000" value={form.city}
                  onChange={e => setForm(f => ({ ...f, city: e.target.value }))}
                  style={{ width: '100%', padding: '0.5rem 0.75rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)', fontSize: '0.875rem', outline: 'none', boxSizing: 'border-box' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>Limite de résultats</label>
                <select value={form.limit} onChange={e => setForm(f => ({ ...f, limit: parseInt(e.target.value) }))}
                  style={{ width: '100%', padding: '0.5rem 0.75rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)', fontSize: '0.875rem', outline: 'none' }}>
                  {[50, 100, 250, 500, 1000, 5000].map(n => <option key={n} value={n}>{n.toLocaleString('fr-FR')} résultats</option>)}
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
              <button onClick={() => setShowForm(false)}
                style={{ padding: '0.5rem 1rem', borderRadius: '8px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.875rem' }}>
                Annuler
              </button>
              <button onClick={launchJob} disabled={launching || !form.name}
                style={{ padding: '0.5rem 1.25rem', borderRadius: '8px', background: 'var(--accent-blue)', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '0.875rem', opacity: launching || !form.name ? 0.7 : 1 }}>
                {launching ? 'Lancement...' : '⚡ Lancer le scraping'}
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes shimmer { 0% { width: 0%; } 50% { width: 80%; } 100% { width: 100%; } }
      `}</style>
    </div>
  );
}
