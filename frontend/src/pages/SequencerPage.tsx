import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface SequenceStep {
  step_number: number;
  wait_days: number;
  subject_template: string;
  body_template: string;
  use_ai_personalization?: boolean;
}

interface Sequence {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'draft';
  steps: number;
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
  { step_number: 1, wait_days: 0, subject_template: 'Découvrez comment {{company_name}} peut optimiser sa croissance', body_template: 'Bonjour,\n\nJe me permets de vous contacter au sujet de {{company_name}}...\n\nCordialement,' },
  { step_number: 2, wait_days: 3, subject_template: 'Suite à mon précédent message', body_template: 'Bonjour,\n\nJe souhaitais revenir sur mon précédent message...\n\nCordialement,' },
  { step_number: 3, wait_days: 7, subject_template: 'Dernière tentative de contact', body_template: 'Bonjour,\n\nJe me permets de vous recontacter une dernière fois...\n\nCordialement,' },
];

export default function SequencerPage() {
  const [sequences, setSequences] = useState<Sequence[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [selected, setSelected] = useState<Sequence | null>(null);
  const [creating, setCreating] = useState(false);

  const [form, setForm] = useState<{
    name: string;
    steps: SequenceStep[];
    use_ai: boolean;
  }>({
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
      await apiClient.post('/sequencer/sequences/', {
        name: form.name,
        description: '',
        steps: form.steps,
      });
      setShowCreate(false);
      setForm({ name: '', steps: DEFAULT_STEPS, use_ai: true });
      loadSequences();
    } finally { setCreating(false); }
  };

  const toggleStatus = async (seq: Sequence) => {
    const endpoint = seq.status === 'active' ? 'pause' : 'resume';
    await apiClient.post(`/sequencer/sequences/${seq.id}/${endpoint}`, {});
    setSequences(prev => prev.map(s =>
      s.id === seq.id ? { ...s, status: seq.status === 'active' ? 'paused' : 'active' } : s
    ));
  };

  const deleteSequence = async (id: string) => {
    if (!confirm('Supprimer cette séquence ?')) return;
    await apiClient.delete(`/sequencer/sequences/${id}`);
    setSequences(prev => prev.filter(s => s.id !== id));
    if (selected?.id === id) setSelected(null);
  };

  const addStep = () => {
    const next = form.steps.length + 1;
    setForm(f => ({
      ...f,
      steps: [...f.steps, {
        step_number: next,
        wait_days: next === 1 ? 0 : 3,
        subject_template: '',
        body_template: '',
      }],
    }));
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
          style={{ padding: '0.5rem 1rem', borderRadius: '8px', background: 'var(--accent-blue)', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '0.875rem' }}
        >+ Nouvelle séquence</button>
      </div>

      {/* Stats */}
      {sequences.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
          {[
            { label: 'Séquences actives', value: sequences.filter(s => s.status === 'active').length, color: 'var(--accent-green)' },
            { label: 'Prospects inscrits', value: sequences.reduce((a, s) => a + (s.enrolled_count || 0), 0), color: 'var(--accent-blue)' },
            { label: 'Emails envoyés', value: sequences.reduce((a, s) => a + (s.sent_count || 0), 0), color: 'var(--accent-orange)' },
            {
              label: "Taux d'ouverture moyen",
              value: sequences.length > 0
                ? Math.round(sequences.reduce((a, s) => a + (s.open_rate || 0), 0) / sequences.length) + '%'
                : '—',
              color: 'var(--accent-purple)',
            },
          ].map(stat => (
            <div key={stat.label} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1rem' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: stat.color }}>{stat.value}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '0.25rem' }}>{stat.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Main content */}
      <div style={{ flex: 1, overflow: 'auto', display: 'flex', gap: '1rem', minHeight: 0 }}>

        {/* Sequences list */}
        <div style={{ width: '340px', minWidth: '340px', display: 'flex', flexDirection: 'column', gap: '0.625rem', overflowY: 'auto' }}>
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} style={{ height: '90px', background: 'var(--bg-card)', borderRadius: '8px', animation: 'pulse 1.5s ease infinite' }} />
            ))
          ) : sequences.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', border: '1px dashed var(--border-color)', borderRadius: '10px', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>📧</div>
              <p>Aucune séquence créée</p>
              <p style={{ fontSize: '0.8125rem' }}>Créez votre première séquence de relance</p>
            </div>
          ) : (
            sequences.map(seq => {
              const statusCfg = STATUS_CONFIG[seq.status] || STATUS_CONFIG.draft;
              const isSelected = selected?.id === seq.id;
              return (
                <div
                  key={seq.id}
                  onClick={() => setSelected(isSelected ? null : seq)}
                  style={{
                    background: isSelected ? 'rgba(47,129,247,0.08)' : 'var(--bg-card)',
                    border: `1px solid ${isSelected ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
                    borderRadius: '8px', padding: '0.875rem', cursor: 'pointer', transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem' }}>{seq.name}</span>
                    <span style={{ padding: '2px 8px', borderRadius: '20px', fontSize: '0.7rem', background: statusCfg.bg, color: statusCfg.color }}>
                      {statusCfg.label}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '0.875rem', color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '0.625rem' }}>
                    <span>📋 {seq.steps || 0} étapes</span>
                    <span>👥 {seq.enrolled_count || 0} inscrits</span>
                    <span>📤 {seq.sent_count || 0} envois</span>
                    {(seq.open_rate || 0) > 0 && <span>👁 {seq.open_rate}%</span>}
                  </div>
                  <div style={{ display: 'flex', gap: '0.375rem', justifyContent: 'flex-end' }}>
                    <button
                      onClick={e => { e.stopPropagation(); toggleStatus(seq); }}
                      style={{
                        padding: '0.2rem 0.625rem', borderRadius: '6px', fontSize: '0.7rem',
                        background: seq.status === 'active' ? 'rgba(210,153,34,0.1)' : 'rgba(63,185,80,0.1)',
                        border: `1px solid ${seq.status === 'active' ? 'rgba(210,153,34,0.3)' : 'rgba(63,185,80,0.3)'}`,
                        color: seq.status === 'active' ? 'var(--accent-orange)' : 'var(--accent-green)',
                        cursor: 'pointer',
                      }}
                    >
                      {seq.status === 'active' ? '⏸ Pause' : '▶ Activer'}
                    </button>
                    <button
                      onClick={e => { e.stopPropagation(); deleteSequence(seq.id); }}
                      style={{ padding: '0.2rem 0.625rem', borderRadius: '6px', fontSize: '0.7rem', background: 'rgba(248,81,73,0.08)', border: '1px solid rgba(248,81,73,0.25)', color: 'var(--accent-red)', cursor: 'pointer' }}
                    >🗑</button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Detail panel */}
        {selected ? (
          <div style={{ flex: 1, background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1.25rem', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '1rem' }}>
                📋 {selected.name}
              </h3>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-green)' }}>{selected.open_rate || 0}%</div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Ouvertures</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-blue)' }}>{selected.reply_rate || 0}%</div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Réponses</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-orange)' }}>{selected.enrolled_count || 0}</div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Inscrits</div>
                </div>
              </div>
            </div>

            {/* Timeline étapes */}
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '19px', top: 0, bottom: 0, width: '2px', background: 'var(--border-color)' }} />
              {Array.from({ length: selected.steps || 0 }).map((_, i) => (
                <div key={i} style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', position: 'relative' }}>
                  <div style={{
                    width: '40px', height: '40px', borderRadius: '50%', flexShrink: 0,
                    background: 'rgba(47,129,247,0.15)', border: '2px solid rgba(47,129,247,0.4)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem', zIndex: 1,
                  }}>📧</div>
                  <div style={{ flex: 1, background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '0.75rem' }}>
                    <div style={{ color: 'var(--accent-blue)', fontSize: '0.75rem', fontWeight: 600 }}>
                      Étape {i + 1}
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '0.25rem' }}>
                      Email de relance #{i + 1}
                    </div>
                  </div>
                </div>
              ))}
              {(!selected.steps || selected.steps === 0) && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginLeft: '52px' }}>
                  Aucune étape configurée
                </p>
              )}
            </div>
          </div>
        ) : (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px dashed var(--border-color)', borderRadius: '10px', color: 'var(--text-muted)' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>←</div>
              <p style={{ fontSize: '0.875rem' }}>Sélectionnez une séquence</p>
            </div>
          </div>
        )}
      </div>

      {/* Create modal */}
      {showCreate && (
        <div
          style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}
          onClick={e => e.target === e.currentTarget && setShowCreate(false)}
        >
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1.5rem', width: '640px', maxWidth: '95vw', maxHeight: '90vh', overflow: 'auto', boxShadow: '0 24px 64px rgba(0,0,0,0.5)' }}>
            <h2 style={{ color: 'var(--text-primary)', margin: '0 0 1.25rem', fontSize: '1rem' }}>+ Nouvelle séquence email</h2>

            {/* Nom */}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>Nom de la séquence *</label>
              <input
                type="text" placeholder="Ex: Relance PME Hauts-de-France"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                style={{ width: '100%', padding: '0.625rem 0.875rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)', fontSize: '0.875rem', outline: 'none', boxSizing: 'border-box' as const }}
              />
            </div>

            {/* Steps */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Étapes ({form.steps.length})</label>
                <button onClick={addStep} style={{ padding: '0.25rem 0.625rem', borderRadius: '6px', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.75rem' }}>
                  + Ajouter étape
                </button>
              </div>

              {form.steps.map((step, i) => (
                <div key={i} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '0.875rem', marginBottom: '0.625rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ color: 'var(--accent-blue)', fontSize: '0.75rem', fontWeight: 600 }}>
                        Étape {step.step_number}
                      </span>
                      <select
                        value={step.wait_days}
                        onChange={e => setForm(f => ({ ...f, steps: f.steps.map((s, j) => j === i ? { ...s, wait_days: parseInt(e.target.value) } : s) }))}
                        style={{ padding: '0.2rem 0.5rem', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--text-secondary)', fontSize: '0.75rem' }}
                      >
                        {[0,1,2,3,5,7,10,14,21].map(d => (
                          <option key={d} value={d}>{d === 0 ? 'Immédiatement' : `J+${d}`}</option>
                        ))}
                      </select>
                    </div>
                    <button
                      onClick={() => setForm(f => ({
                        ...f,
                        steps: f.steps.filter((_, j) => j !== i).map((s, j) => ({ ...s, step_number: j + 1 }))
                      }))}
                      style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.875rem', padding: '0' }}
                    >✕</button>
                  </div>
                  <input
                    placeholder="Objet de l'email (ex: {{company_name}} — opportunité)"
                    value={step.subject_template}
                    onChange={e => setForm(f => ({ ...f, steps: f.steps.map((s, j) => j === i ? { ...s, subject_template: e.target.value } : s) }))}
                    style={{ width: '100%', padding: '0.4rem 0.625rem', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)', fontSize: '0.8125rem', marginBottom: '0.375rem', boxSizing: 'border-box' as const, outline: 'none' }}
                  />
                  <textarea
                    placeholder="Corps de l'email — variables : {{company_name}}, {{city}}, {{first_name}}..."
                    value={step.body_template}
                    rows={3}
                    onChange={e => setForm(f => ({ ...f, steps: f.steps.map((s, j) => j === i ? { ...s, body_template: e.target.value } : s) }))}
                    style={{ width: '100%', padding: '0.4rem 0.625rem', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-primary)', fontSize: '0.8125rem', resize: 'vertical' as const, boxSizing: 'border-box' as const, outline: 'none' }}
                  />
                </div>
              ))}
            </div>

            {/* IA */}
            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={form.use_ai} onChange={e => setForm(f => ({ ...f, use_ai: e.target.checked }))} />
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                  🤖 Personnalisation IA des emails (Claude)
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
                disabled={creating || !form.name.trim() || form.steps.length === 0}
                style={{ padding: '0.5rem 1rem', borderRadius: '8px', background: 'var(--accent-blue)', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '0.875rem', opacity: (creating || !form.name.trim() || form.steps.length === 0) ? 0.7 : 1 }}
              >{creating ? 'Création...' : `Créer (${form.steps.length} étape${form.steps.length > 1 ? 's' : ''})`}</button>
            </div>
          </div>
        </div>
      )}

      <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
}
