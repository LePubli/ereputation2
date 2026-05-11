import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';

interface Activity {
  id: string;
  type: 'call' | 'email' | 'meeting' | 'note' | 'signal';
  title: string;
  description?: string;
  created_at: string;
  user_name?: string;
}

interface Prospect {
  id: string;
  company_name: string;
  siren?: string;
  siret?: string;
  naf_code?: string;
  naf_label?: string;
  city?: string;
  region?: string;
  postal_code?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  employee_count?: number;
  revenue_range?: string;
  score?: number;
  status?: string;
  pipeline_stage?: string;
  linkedin_url?: string;
  created_at?: string;
  sources?: string[];
  enrichment_data?: Record<string, unknown>;
}

interface Props {
  prospect: Prospect;
  onClose: () => void;
  onEdit?: (prospect: Prospect) => void;
  onStageChange?: (id: string, stage: string) => void;
}

const SCORE_COLOR = (s: number) =>
  s >= 75 ? 'var(--accent-green)' : s >= 50 ? 'var(--accent-blue)' : s >= 25 ? 'var(--accent-orange)' : 'var(--accent-red)';

const STAGE_OPTIONS = [
  'Nouveau', 'Contacté', 'Qualifié', 'Proposition', 'Négociation', 'Gagné', 'Perdu',
];

const ACTIVITY_ICONS: Record<string, string> = {
  call: '📞', email: '📧', meeting: '📅', note: '📝', signal: '⚡',
};

export default function ProspectDetailModal({ prospect, onClose, onStageChange }: Props) {
  const [activeTab, setActiveTab] = useState<'overview' | 'activities' | 'enrichment' | 'contacts'>('overview');
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loadingActs, setLoadingActs] = useState(false);
  const [newNote, setNewNote] = useState('');
  const [addingNote, setAddingNote] = useState(false);
  const [currentStage, setCurrentStage] = useState(prospect.pipeline_stage || 'Nouveau');

  useEffect(() => {
    if (activeTab === 'activities') loadActivities();
  }, [activeTab]);

  const loadActivities = async () => {
    setLoadingActs(true);
    try {
      const data = await apiClient.get(`/activities/?prospect_id=${prospect.id}&limit=50`);
      setActivities(data.items || []);
    } catch { setActivities([]); }
    finally { setLoadingActs(false); }
  };

  const addNote = async () => {
    if (!newNote.trim()) return;
    setAddingNote(true);
    try {
      await apiClient.post('/activities/', {
        prospect_id: prospect.id,
        type: 'note',
        title: 'Note',
        description: newNote,
      });
      setNewNote('');
      loadActivities();
    } catch { } finally { setAddingNote(false); }
  };

  const handleStageChange = async (stage: string) => {
    setCurrentStage(stage);
    onStageChange?.(prospect.id, stage);
  };

  const score = prospect.score ?? 0;

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '1rem',
      }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        width: '100%', maxWidth: '860px',
        maxHeight: '90vh', overflow: 'hidden',
        display: 'flex', flexDirection: 'column',
        boxShadow: '0 24px 64px rgba(0,0,0,0.5)',
      }}>
        {/* Header */}
        <div style={{
          padding: '1.5rem',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex', alignItems: 'flex-start', gap: '1rem',
        }}>
          {/* Avatar */}
          <div style={{
            width: '52px', height: '52px', borderRadius: '12px',
            background: 'linear-gradient(135deg, var(--accent-blue), #7c3aed)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.375rem', flexShrink: 0,
          }}>
            🏢
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <h2 style={{
              fontSize: '1.25rem', fontWeight: 700,
              color: 'var(--text-primary)', margin: '0 0 0.25rem',
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}>
              {prospect.company_name}
            </h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
              {prospect.city && (
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                  📍 {prospect.city} {prospect.postal_code && `(${prospect.postal_code})`}
                </span>
              )}
              {prospect.naf_label && (
                <span style={{
                  padding: '2px 8px', borderRadius: '4px',
                  background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                  fontSize: '0.75rem', color: 'var(--text-secondary)',
                }}>
                  {prospect.naf_code} · {prospect.naf_label}
                </span>
              )}
              {prospect.siren && (
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  SIREN {prospect.siren}
                </span>
              )}
            </div>
          </div>

          {/* Score */}
          <div style={{ textAlign: 'center', flexShrink: 0 }}>
            <div style={{
              width: '56px', height: '56px', borderRadius: '50%',
              border: `3px solid ${SCORE_COLOR(score)}`,
              display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ fontSize: '1.125rem', fontWeight: 700, color: SCORE_COLOR(score), lineHeight: 1 }}>
                {score}
              </span>
              <span style={{ fontSize: '0.5rem', color: 'var(--text-muted)' }}>score</span>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'none', border: '1px solid var(--border-color)',
              borderRadius: '8px', padding: '0.375rem 0.75rem',
              color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1rem',
              flexShrink: 0,
            }}
          >✕</button>
        </div>

        {/* Stage selector */}
        <div style={{
          padding: '0.75rem 1.5rem',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex', alignItems: 'center', gap: '0.5rem',
          overflowX: 'auto',
        }}>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', flexShrink: 0 }}>Étape :</span>
          {STAGE_OPTIONS.map(s => (
            <button
              key={s}
              onClick={() => handleStageChange(s)}
              style={{
                padding: '0.25rem 0.75rem', borderRadius: '20px',
                border: '1px solid',
                borderColor: currentStage === s ? 'var(--accent-blue)' : 'var(--border-color)',
                background: currentStage === s ? 'rgba(47,129,247,0.15)' : 'var(--bg-tertiary)',
                color: currentStage === s ? 'var(--accent-blue)' : 'var(--text-secondary)',
                cursor: 'pointer', fontSize: '0.75rem', fontWeight: currentStage === s ? 600 : 400,
                flexShrink: 0, whiteSpace: 'nowrap', transition: 'all 0.15s',
              }}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex', gap: '0',
          borderBottom: '1px solid var(--border-color)',
          padding: '0 1.5rem',
        }}>
          {(['overview', 'activities', 'enrichment', 'contacts'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '0.75rem 1rem',
                border: 'none', borderBottom: '2px solid',
                borderBottomColor: activeTab === tab ? 'var(--accent-blue)' : 'transparent',
                background: 'none',
                color: activeTab === tab ? 'var(--accent-blue)' : 'var(--text-secondary)',
                cursor: 'pointer', fontSize: '0.875rem', fontWeight: activeTab === tab ? 600 : 400,
                transition: 'all 0.15s',
              }}
            >
              {{ overview: '📋 Vue d\'ensemble', activities: '📅 Activités', enrichment: '🔍 Enrichissement', contacts: '👤 Contacts' }[tab]}
            </button>
          ))}
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>

          {/* OVERVIEW */}
          {activeTab === 'overview' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              {/* Coordonnées */}
              <InfoCard title="📞 Coordonnées">
                <InfoRow label="Téléphone" value={prospect.phone} href={`tel:${prospect.phone}`} />
                <InfoRow label="Email" value={prospect.email} href={`mailto:${prospect.email}`} />
                <InfoRow label="Site web" value={prospect.website} href={prospect.website} external />
                <InfoRow label="LinkedIn" value={prospect.linkedin_url ? 'Voir profil' : undefined} href={prospect.linkedin_url} external />
              </InfoCard>

              {/* Entreprise */}
              <InfoCard title="🏢 Entreprise">
                <InfoRow label="Effectif" value={prospect.employee_count ? `${prospect.employee_count} salariés` : undefined} />
                <InfoRow label="CA estimé" value={prospect.revenue_range} />
                <InfoRow label="SIREN" value={prospect.siren} />
                <InfoRow label="SIRET" value={prospect.siret} />
              </InfoCard>

              {/* Localisation */}
              <InfoCard title="📍 Localisation">
                <InfoRow label="Adresse" value={prospect.address} />
                <InfoRow label="Ville" value={prospect.city} />
                <InfoRow label="Code postal" value={prospect.postal_code} />
                <InfoRow label="Région" value={prospect.region} />
              </InfoCard>

              {/* Sources */}
              <InfoCard title="🔗 Sources de données">
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
                  {(prospect.sources || []).map(s => (
                    <span key={s} style={{
                      padding: '2px 10px', borderRadius: '20px',
                      background: 'rgba(47,129,247,0.1)', border: '1px solid rgba(47,129,247,0.3)',
                      color: 'var(--accent-blue)', fontSize: '0.75rem',
                    }}>{s}</span>
                  ))}
                  {!prospect.sources?.length && (
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Aucune source</span>
                  )}
                </div>
              </InfoCard>
            </div>
          )}

          {/* ACTIVITIES */}
          {activeTab === 'activities' && (
            <div>
              {/* Add note */}
              <div style={{
                background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                borderRadius: '8px', padding: '1rem', marginBottom: '1.5rem',
              }}>
                <textarea
                  value={newNote}
                  onChange={e => setNewNote(e.target.value)}
                  placeholder="Ajouter une note, un compte-rendu d'appel..."
                  rows={3}
                  style={{
                    width: '100%', background: 'none', border: 'none',
                    color: 'var(--text-primary)', fontSize: '0.875rem',
                    resize: 'none', outline: 'none', boxSizing: 'border-box',
                  }}
                />
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                  <button
                    onClick={addNote}
                    disabled={addingNote || !newNote.trim()}
                    style={{
                      padding: '0.375rem 1rem', borderRadius: '6px',
                      background: 'var(--accent-blue)', border: 'none',
                      color: '#fff', fontSize: '0.8125rem', cursor: 'pointer',
                      opacity: addingNote || !newNote.trim() ? 0.5 : 1,
                    }}
                  >
                    {addingNote ? 'Enregistrement...' : '+ Ajouter note'}
                  </button>
                </div>
              </div>

              {/* Timeline */}
              {loadingActs ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                  Chargement...
                </div>
              ) : activities.length === 0 ? (
                <div style={{
                  textAlign: 'center', color: 'var(--text-muted)', padding: '3rem',
                  border: '1px dashed var(--border-color)', borderRadius: '8px',
                }}>
                  Aucune activité pour ce prospect
                </div>
              ) : (
                <div style={{ position: 'relative' }}>
                  <div style={{
                    position: 'absolute', left: '20px', top: 0, bottom: 0,
                    width: '2px', background: 'var(--border-color)',
                  }} />
                  {activities.map(act => (
                    <div key={act.id} style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', position: 'relative' }}>
                      <div style={{
                        width: '40px', height: '40px', borderRadius: '50%',
                        background: 'var(--bg-tertiary)', border: '2px solid var(--border-color)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '1rem', flexShrink: 0, zIndex: 1,
                      }}>
                        {ACTIVITY_ICONS[act.type] || '📋'}
                      </div>
                      <div style={{
                        flex: 1, background: 'var(--bg-secondary)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '8px', padding: '0.75rem',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem' }}>
                            {act.title}
                          </span>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                            {new Date(act.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        {act.description && (
                          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', margin: 0 }}>
                            {act.description}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ENRICHMENT */}
          {activeTab === 'enrichment' && (
            <div>
              {prospect.enrichment_data && Object.keys(prospect.enrichment_data).length > 0 ? (
                <div style={{ display: 'grid', gap: '0.75rem' }}>
                  {Object.entries(prospect.enrichment_data).map(([source, data]) => (
                    <div key={source} style={{
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px', padding: '1rem',
                    }}>
                      <div style={{
                        fontWeight: 600, color: 'var(--text-primary)',
                        fontSize: '0.875rem', marginBottom: '0.75rem',
                        textTransform: 'capitalize',
                      }}>
                        🔍 {source}
                      </div>
                      <pre style={{
                        color: 'var(--text-secondary)', fontSize: '0.75rem',
                        margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                      }}>
                        {JSON.stringify(data, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{
                  textAlign: 'center', padding: '3rem',
                  border: '1px dashed var(--border-color)', borderRadius: '8px',
                  color: 'var(--text-muted)',
                }}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>🔍</div>
                  <p>Aucune donnée d'enrichissement disponible</p>
                  <p style={{ fontSize: '0.8125rem' }}>Lancez l'enrichissement waterfall depuis la liste des prospects</p>
                </div>
              )}
            </div>
          )}

          {/* CONTACTS */}
          {activeTab === 'contacts' && (
            <div style={{
              textAlign: 'center', padding: '3rem',
              border: '1px dashed var(--border-color)', borderRadius: '8px',
              color: 'var(--text-muted)',
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>👤</div>
              <p>Intelligence Contacts</p>
              <p style={{ fontSize: '0.8125rem' }}>Utilisez la page Contact Intelligence pour trouver les décideurs</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '1rem 1.5rem',
          borderTop: '1px solid var(--border-color)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          background: 'var(--bg-secondary)',
        }}>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
            Ajouté le {prospect.created_at ? new Date(prospect.created_at).toLocaleDateString('fr-FR') : '—'}
          </span>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {prospect.phone && (
              <a href={`tel:${prospect.phone}`} style={{
                padding: '0.5rem 1rem', borderRadius: '8px',
                background: 'rgba(63,185,80,0.15)', border: '1px solid rgba(63,185,80,0.3)',
                color: 'var(--accent-green)', fontSize: '0.8125rem',
                textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem',
              }}>📞 Appeler</a>
            )}
            {prospect.email && (
              <a href={`mailto:${prospect.email}`} style={{
                padding: '0.5rem 1rem', borderRadius: '8px',
                background: 'rgba(47,129,247,0.15)', border: '1px solid rgba(47,129,247,0.3)',
                color: 'var(--accent-blue)', fontSize: '0.8125rem',
                textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem',
              }}>📧 Email</a>
            )}
            {prospect.website && (
              <a href={prospect.website} target="_blank" rel="noreferrer" style={{
                padding: '0.5rem 1rem', borderRadius: '8px',
                background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                color: 'var(--text-secondary)', fontSize: '0.8125rem',
                textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem',
              }}>🌐 Site</a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Sub-components ---------- */

function InfoCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
      borderRadius: '8px', padding: '1rem',
    }}>
      <div style={{ fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.8125rem', marginBottom: '0.75rem' }}>
        {title}
      </div>
      <div style={{ display: 'grid', gap: '0.5rem' }}>
        {children}
      </div>
    </div>
  );
}

function InfoRow({ label, value, href, external }: { label: string; value?: string | number; href?: string; external?: boolean }) {
  if (!value) return null;
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '0.5rem' }}>
      <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', flexShrink: 0 }}>{label}</span>
      {href ? (
        <a href={href} target={external ? '_blank' : undefined} rel="noreferrer"
          style={{ color: 'var(--accent-blue)', fontSize: '0.8125rem', textDecoration: 'none', textAlign: 'right', wordBreak: 'break-all' }}>
          {String(value)}
        </a>
      ) : (
        <span style={{ color: 'var(--text-primary)', fontSize: '0.8125rem', textAlign: 'right' }}>
          {String(value)}
        </span>
      )}
    </div>
  );
}
