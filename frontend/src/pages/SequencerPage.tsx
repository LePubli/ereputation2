import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface SequenceStep {
  delay_days: number;
  subject: string;
  body: string;
  type: 'email' | 'task';
}

interface Sequence {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'draft';
  steps: SequenceStep[];
  enrolled_count?: number;
  sent_count?: number;
  open_rate?: number;
  reply_rate?: number;
  created_at: string;
}

const STATUS_CONFIG = {
  active: { label: 'Actif', color: 'var(--accent-green)', bg: 'rgba(63,185,80,0.1)' },
  paused: { label: 'En pause', color: 'var(--accent-orange)', bg: 'rgba(210,153,34,0.1)' },
  draft: { label: 'Brouillon', color: 'var(--text-muted)', bg: 'var(--bg-tertiary)' },
};

const DEFAULT_STEPS: SequenceStep[] = [
  { delay_days: 0, type: 'email', subject: 'Découvrez comment {company} peut...', body: 'Bonjour,\n\nJe me permets de vous contacter...' },
  { delay_days: 3, type: 'email', subject: 'Suite à mon précédent message', body: 'Bonjour,\n\nJe souhaitais revenir sur...' },
  { delay_days: 7, type: 'task', subject: 'Appel de suivi', body: 'Tenter de joindre par téléphone' },
];

export default function SequencerPage() {
  const [sequences, setSequences] = useState<Sequence[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [selected, setSelected] = useState<Sequence | null>(null);
  const [creating, setCreating] = useState(false);

  const [form, setForm] = useState({
    name: '',
    steps: DEFAULT_STEPS,
    use_ai: true,
  });

  useEffect(() => { loadSequences(); }, []);

  const loadSequences = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/sequencer/sequences/?limit=50');
      setSequences(data.items || []);
    } catch { setSequences([]); } finally { setLoading(false); }
  };

  const createSequence = async () => {
    if (!form.name.trim()) return;
    setCreating(true);
    try {
      await apiClient.post('/sequencer/sequences/', { ...form });
      setShowCreate(false);
      setForm({ name: '', steps: DEFAULT_STEPS, use_ai: true });
      loadSequences();
    } finally { setCreating(false); }
  };

  const toggleStatus = async (seq: Sequence) => {
    const newStatus = seq.status === 'active' ? 'paused' : 'active';
    await apiClient.patch(`/sequencer/sequences/${seq.id}`, { status: newStatus });
    setSequences(prev => prev.map(s => s.id === seq.id ? { ...s, status: newStatus } : s));
  };

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%', boxSizing: 'border-box' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Séquences Email
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
            Automatisation des relances multi-étapes avec IA
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          style={{
            padding: '0.5rem 1rem', borderRadius: '8px',
            background: 'var(--accent-blue)', border: 'none',
            color: '#fff', cursor: 'pointer', fontSize: '0.875rem',
          }}
        >+ Nouvelle séquence</button>
      </div>

      {/* Stats overview */}
      {sequences.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
          {[
            { label: 'Séquences actives', value: sequences.filter(s => s.status === 'active').length, color: 'var(--accent-green)' },
            { label: 'Prospects inscrits', value: sequences.reduce((a, s) => a + (s.enrolled_count || 0), 0), color: 'var(--accent-blue)' },
            { label: 'Emails envoyés', value: sequences.reduce((a, s) => a + (s.sent_count || 0), 0), color: 'var(--accent-orange)' },
            { label: 'Taux moyen d\'ouverture', value: sequences.length > 0 ? Math.round(sequences.reduce((a, s) => a + (s.open_rate || 0), 0) / sequences.length) + '%' : '—', color: 'var(--accent-purple)' },
          ].map(stat => (
            <div key={stat.label} style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: '10px', padding: '1rem',
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: stat.color }}>{stat.value}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '0.25rem' }}>{stat.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Sequences list */}
      <div style={{ flex: 1, overflow: 'auto', display: 'flex', gap: '1rem' }}>
        {/* List panel */}
        <div style={{ width: '340px', minWidth: '340px', display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} style={{ height: '90px', background: 'var(--bg-card)', borderRadius: '8px', animation: 'pulse 1.5s ease infinite' }} />
            ))
          ) : sequences.length === 0 ? (
            <div style={{
              textAlign: 'center', padding: '3rem 1rem',
              border: '1px dashed var(--border-color)', borderRadius: '10px', color: 'var(--text-muted)',
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>📧</div>
              <p>Aucune séquence créée</p>
              <p style={{ fontSize: '0.8125rem' }}>Créez votre première séquence de relance</p>
            </div>
          ) : (
            sequences.map(seq => {
              const statusCfg = STATUS_CONFIG[seq.status];
              const isSelected = selected?.id === seq.id;
              return (
                <div
                  key={seq.id}
                  onClick={() => setSelected(isSelected ? null : seq)}
                  style={{
                    background: isSelected ? 'rgba(47,129,247,0.08)' : 'var(--bg-card)',
                    border: `1px solid ${isSelected ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
                    borderRadius: '8px', padding: '0.875rem', cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem' }}>
                      {seq.name}
                    </span>
                    <span style={{
                      padding: '2px 8px', borderRadius: '20px', fontSize: '0.7rem',
                      background: statusCfg.bg, color: statusCfg.color,
                    }}>
                      {statusCfg.label}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    <span>📋 {seq.steps?.length || 0} étapes</span>
                    <span>👥 {seq.enrolled_count || 0} inscrits</span>
                    <span>📤 {seq.sent_count || 0} envois</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.625rem' }}>
                    <button
                      onClick={e => { e.stopPropagation(); toggleStatus(seq); }}
                      style={{
                        padding: '0.25rem 0.75rem', borderRadius: '6px', fontSize: '0.75rem',
                        background: seq.status === 'active' ? 'rgba(210,153,34,0.1)' : 'rgba(63,185,80,0.1)',
                        border: `1px solid ${seq.status === 'active' ? 'rgba(210,153,34,0.3)' : 'rgba(63,185,80,0.3)'}`,
                        color: seq.status === 'active' ? 'var(--accent-orange)' : 'var(--accent-green)',
                        cursor: 'pointer',
                      }}
                    >
                      {seq.status === 'active' ? '⏸ Pause' : '▶ Activer'}
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <div style={{
            flex: 1, background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '10px', padding: '1.25rem', overflow: 'auto',
          }}>
            <h3 style={{ color: 'var(--text-primary)', margin: '0 0 1.25rem', fontSize: '1rem' }}>
              📋 {selected.name} — Étapes
            </h3>
            <div style={{ position: 'relative' }}>
              <div style={{
                position: 'absolute', left: '19px', top: 0, bottom: 0,
                width: '2px', background: 'var(--border-color)',
              }} />
              {(selected.steps || []).map((step, i) => (
                <div key={i} style={{ display: 'flex', gap: '1rem', marginBottom: '1.25rem', position: 'relative' }}>
                  <div style={{
                    width: '40px', height: '40px', borderRadius: '50%', flexShrink: 0,
                    background: step.type === 'email' ? 'rgba(47,129,247,0.15)' : 'rgba(139,92,246,0.15)',
                    border: `2px solid ${step.type === 'email' ? 'rgba(47,129,247,0.4)' : 'rgba(139,92,246,0.4)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '1rem', zIndex: 1,
                  }}>
                    {step.type === 'email' ? '📧' : '📋'}
                  </div>
                  <div style={{
                    flex: 1, background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-color)', borderRadius: '8px', padding: '0.875rem',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem' }}>
                        {i === 0 ? 'Jour 0' : `J+${step.delay_days}`} · {step.subject}
                      </span>
                      <span style={{
                        padding: '1px 8px', borderRadius: '20px', fontSize: '0.7rem',
                        background: 'var(--bg-tertiary)', color: 'var(--text-muted)',
                      }}>{step.type}</span>
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', margin: 0, whiteSpace: 'pre-wrap' }}>
                      {step.body?.slice(0, 120)}{step.body?.length > 120 ? '...' : ''}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Create modal */}
      {showCreate && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 1000,
          background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }} onClick={e => e.target === e.currentTarget && setShowCreate(false)}>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-color)',
            borderRadius: '12px', padding: '1.5rem', width: '560px', maxWidth: '95vw',
            boxShadow: '0 24px 64px rgba(0,0,0,0.5)',
          }}>
            <h2 style={{ color: 'var(--text-primary)', margin: '0 0 1.25rem', fontSize: '1rem' }}>
              + Nouvelle séquence email
            </h2>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>Nom de la séquence</label>
              <input
                type="text"
                placeholder="Ex: Relance PME Hauts-de-France"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                style={{
                  width: '100%', padding: '0.625rem 0.875rem',
                  background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                  borderRadius: '8px', color: 'var(--text-primary)', fontSize: '0.875rem',
                  outline: 'none', boxSizing: 'border-box',
                }}
              />
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={form.use_ai} onChange={e => setForm(f => ({ ...f, use_ai: e.target.checked }))} />
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                  🤖 Personnalisation IA des emails
                </span>
              </label>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowCreate(false)}
                style={{ padding: '0.5rem 1rem', borderRadius: '8px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.875rem' }}
              >Annuler</button>
              <button
                onClick={createSequence}
                disabled={creating || !form.name.trim()}
                style={{ padding: '0.5rem 1rem', borderRadius: '8px', background: 'var(--accent-blue)', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '0.875rem', opacity: creating || !form.name.trim() ? 0.7 : 1 }}
              >{creating ? 'Création...' : 'Créer la séquence'}</button>
            </div>
          </div>
        </div>
      )}

      <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
}
