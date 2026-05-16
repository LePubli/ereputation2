import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface Signal {
  id: string;
  prospect_id: string;
  prospect_name: string;
  type: string;
  title: string;
  description?: string;
  source: string;
  severity: string;
  is_read: boolean;
  signal_date: string | null;
  created_at: string;
}

const SIGNAL_CONFIG: Record<string, { icon: string; label: string; color: string; bg: string }> = {
  bodacc: { icon: '📋', label: 'BODACC', color: 'var(--accent-orange)', bg: 'rgba(210,153,34,0.1)' },
  bodacc_capital_change: { icon: '💰', label: 'Capital', color: 'var(--accent-orange)', bg: 'rgba(210,153,34,0.1)' },
  job_posting_detected: { icon: '👥', label: 'Recrutement', color: 'var(--accent-green)', bg: 'rgba(63,185,80,0.1)' },
  news_mention: { icon: '📰', label: 'Presse', color: 'var(--accent-blue)', bg: 'rgba(47,129,247,0.1)' },
  website_change: { icon: '🌐', label: 'Site web', color: 'var(--accent-purple)', bg: 'rgba(139,92,246,0.1)' },
  inbound_form: { icon: '📩', label: 'Formulaire', color: 'var(--accent-green)', bg: 'rgba(63,185,80,0.1)' },
  no_contact: { icon: '📵', label: 'Sans contact', color: 'var(--accent-red)', bg: 'rgba(248,81,73,0.1)' },
  hot_lead: { icon: '🔥', label: 'Lead chaud', color: 'var(--accent-green)', bg: 'rgba(63,185,80,0.1)' },
  growth: { icon: '📈', label: 'Croissance', color: 'var(--accent-blue)', bg: 'rgba(47,129,247,0.1)' },
  new_company: { icon: '🆕', label: 'Nouvelle société', color: 'var(--accent-purple)', bg: 'rgba(139,92,246,0.1)' },
};

const SEVERITY_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  critical: { label: 'Critique', color: 'var(--accent-red)', bg: 'rgba(248,81,73,0.1)' },
  high: { label: 'Haute', color: 'var(--accent-orange)', bg: 'rgba(210,153,34,0.1)' },
  medium: { label: 'Moyenne', color: 'var(--accent-blue)', bg: 'rgba(47,129,247,0.1)' },
  low: { label: 'Basse', color: '#8b949e', bg: 'rgba(139,148,158,0.1)' },
  opportunity: { label: 'Opportunité', color: 'var(--accent-green)', bg: 'rgba(63,185,80,0.1)' },
  warning: { label: 'Attention', color: 'var(--accent-orange)', bg: 'rgba(210,153,34,0.1)' },
  info: { label: 'Info', color: 'var(--accent-blue)', bg: 'rgba(47,129,247,0.1)' },
};

const DEFAULT_TYPE_CFG = { icon: '⚡', label: 'Signal', color: 'var(--accent-blue)', bg: 'rgba(47,129,247,0.1)' };
const DEFAULT_SEV_CFG = { label: 'Info', color: 'var(--accent-blue)', bg: 'rgba(47,129,247,0.1)' };

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [severityFilter, setSeverityFilter] = useState<string>('all');

  useEffect(() => { loadSignals(); }, []);

  const loadSignals = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/signals/?limit=200');
      setSignals(data.items || []);
    } catch { setSignals([]); } finally { setLoading(false); }
  };

  const runDetection = async () => {
    setRunning(true);
    try {
      await apiClient.post('/signals/detect', {});
      await loadSignals();
    } finally { setRunning(false); }
  };

  const dismissSignal = async (id: string) => {
    await apiClient.patch(`/signals/${id}`, { dismissed: true });
    setSignals(prev => prev.filter(s => s.id !== id));
  };

  const filtered = signals.filter(s => {
    if (severityFilter !== 'all' && s.severity !== severityFilter) return false;
    return true;
  });

  const counts = {
    high: signals.filter(s => s.severity === 'high' || s.severity === 'critical').length,
    medium: signals.filter(s => s.severity === 'medium').length,
    low: signals.filter(s => s.severity === 'low').length,
  };

  const sevEntries = [
    { key: 'high', label: 'Haute priorité', color: 'var(--accent-orange)', bg: 'rgba(210,153,34,0.1)' },
    { key: 'medium', label: 'Moyenne', color: 'var(--accent-blue)', bg: 'rgba(47,129,247,0.1)' },
    { key: 'low', label: 'Basse', color: '#8b949e', bg: 'rgba(139,148,158,0.1)' },
  ];

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%', boxSizing: 'border-box' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Signaux d'Affaires
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
            Détection automatique d'opportunités · {signals.length} signaux actifs
          </p>
        </div>
        <button
          onClick={runDetection}
          disabled={running}
          style={{
            padding: '0.5rem 1rem', borderRadius: '8px',
            background: running ? 'var(--bg-tertiary)' : 'var(--accent-blue)',
            border: 'none', color: '#fff', cursor: running ? 'not-allowed' : 'pointer',
            fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem',
          }}
        >
          {running ? (
            <><span style={{ display: 'inline-block', width: '14px', height: '14px', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} /> Détection...</>
          ) : '⚡ Détecter maintenant'}
        </button>
      </div>

      {/* KPI cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.875rem' }}>
        {sevEntries.map(({ key, label, color, bg }) => (
          <div
            key={key}
            onClick={() => setSeverityFilter(severityFilter === key ? 'all' : key)}
            style={{
              background: severityFilter === key ? bg : 'var(--bg-card)',
              border: `1px solid ${severityFilter === key ? color : 'var(--border-color)'}`,
              borderRadius: '10px', padding: '1rem 1.25rem',
              cursor: 'pointer', transition: 'all 0.15s',
            }}
          >
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color }}>{counts[key as keyof typeof counts]}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', marginTop: '0.25rem' }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Severity filter pills */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <FilterPill label="Tous" active={severityFilter === 'all'} onClick={() => setSeverityFilter('all')} count={signals.length} />
        {sevEntries.map(({ key, label, color }) => {
          const count = signals.filter(s => s.severity === key || (key === 'high' && s.severity === 'critical')).length;
          if (count === 0) return null;
          return (
            <FilterPill key={key} label={label} active={severityFilter === key}
              onClick={() => setSeverityFilter(severityFilter === key ? 'all' : key)}
              count={count} color={color} />
          );
        })}
      </div>

      {/* Signals list */}
      <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} style={{ height: '80px', borderRadius: '8px', background: 'var(--bg-card)', border: '1px solid var(--border-color)', animation: 'pulse 1.5s ease infinite' }} />
          ))
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '4rem', border: '1px dashed var(--border-color)', borderRadius: '10px', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>⚡</div>
            <p style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Aucun signal détecté</p>
            <p style={{ fontSize: '0.875rem' }}>Cliquez sur "Détecter maintenant" pour analyser votre base</p>
          </div>
        ) : (
          filtered.map(signal => {
            const typeCfg = SIGNAL_CONFIG[signal.type] || DEFAULT_TYPE_CFG;
            const sevCfg = SEVERITY_CONFIG[signal.severity] || DEFAULT_SEV_CFG;
            return (
              <div
                key={signal.id}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderLeft: `4px solid ${typeCfg.color}`,
                  borderRadius: '8px', padding: '1rem',
                  display: 'flex', gap: '1rem', alignItems: 'flex-start',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-secondary)'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-card)'; }}
              >
                <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: typeCfg.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.25rem', flexShrink: 0 }}>
                  {typeCfg.icon}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem' }}>
                      {signal.prospect_name}
                    </span>
                    <span style={{ padding: '1px 8px', borderRadius: '20px', fontSize: '0.7rem', background: sevCfg.bg, color: sevCfg.color, border: `1px solid ${sevCfg.color}33` }}>
                      {sevCfg.label}
                    </span>
                    <span style={{ padding: '1px 8px', borderRadius: '20px', fontSize: '0.7rem', background: 'var(--bg-tertiary)', color: 'var(--text-muted)', border: '1px solid var(--border-color)' }}>
                      {typeCfg.label}
                    </span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', margin: '0 0 0.375rem' }}>
                    {signal.title}
                  </p>
                  {signal.description && (
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', margin: 0 }}>
                      {signal.description}
                    </p>
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', flexShrink: 0 }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textAlign: 'right', whiteSpace: 'nowrap' }}>
                    {signal.created_at ? new Date(signal.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }) : '—'}
                  </span>
                  <button
                    onClick={() => dismissSignal(signal.id)}
                    style={{ padding: '0.25rem 0.625rem', borderRadius: '6px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.75rem' }}
                  >Ignorer</button>
                </div>
              </div>
            );
          })
        )}
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
      `}</style>
    </div>
  );
}

function FilterPill({ label, active, onClick, count, color }: {
  label: string; active: boolean; onClick: () => void; count: number; color?: string;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '0.375rem 0.875rem', borderRadius: '20px',
        background: active ? (color ? `${color}22` : 'rgba(47,129,247,0.15)') : 'var(--bg-card)',
        border: `1px solid ${active ? (color || 'var(--accent-blue)') : 'var(--border-color)'}`,
        color: active ? (color || 'var(--accent-blue)') : 'var(--text-secondary)',
        cursor: 'pointer', fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: '0.375rem',
        transition: 'all 0.15s',
      }}
    >
      {label}
      <span style={{ background: 'var(--bg-tertiary)', borderRadius: '10px', padding: '0 5px', fontSize: '0.7rem', color: 'var(--text-muted)' }}>{count}</span>
    </button>
  );
}
