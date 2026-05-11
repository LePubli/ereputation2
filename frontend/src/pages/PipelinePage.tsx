import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface Prospect {
  id: string;
  company_name: string;
  city?: string;
  score?: number;
  email?: string;
  phone?: string;
  pipeline_stage: string;
  naf_label?: string;
}

interface Stage {
  id: string;
  name: string;
  color: string;
  icon: string;
}

const PIPELINE_STAGES: Stage[] = [
  { id: 'Nouveau', name: 'Nouveau', color: '#8b949e', icon: '🆕' },
  { id: 'Contacté', name: 'Contacté', color: '#2f81f7', icon: '📞' },
  { id: 'Qualifié', name: 'Qualifié', color: '#8b5cf6', icon: '✅' },
  { id: 'Proposition', name: 'Proposition', color: '#d29922', icon: '📄' },
  { id: 'Négociation', name: 'Négociation', color: '#f97316', icon: '🤝' },
  { id: 'Gagné', name: 'Gagné', color: '#3fb950', icon: '🏆' },
  { id: 'Perdu', name: 'Perdu', color: '#f85149', icon: '❌' },
];

const SCORE_COLOR = (s: number) =>
  s >= 75 ? '#3fb950' : s >= 50 ? '#2f81f7' : s >= 25 ? '#d29922' : '#f85149';

export default function PipelinePage() {
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(true);
  const [dragging, setDragging] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState<string | null>(null);
  const [movingId, setMovingId] = useState<string | null>(null);

  useEffect(() => {
    loadPipeline();
  }, []);

  const loadPipeline = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/prospects/?limit=500&sort_by=score&sort_dir=desc');
      setProspects(data.items || []);
    } finally { setLoading(false); }
  };

  const handleDragStart = (e: React.DragEvent, id: string) => {
    setDragging(id);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, stageId: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOver(stageId);
  };

  const handleDrop = async (e: React.DragEvent, stageId: string) => {
    e.preventDefault();
    if (!dragging || dragging === stageId) { setDragOver(null); return; }
    const prospect = prospects.find(p => p.id === dragging);
    if (!prospect || prospect.pipeline_stage === stageId) { setDragOver(null); return; }

    // Optimistic update
    setProspects(prev => prev.map(p =>
      p.id === dragging ? { ...p, pipeline_stage: stageId } : p
    ));
    setMovingId(dragging);
    setDragging(null);
    setDragOver(null);

    try {
      await apiClient.patch(`/prospects/${dragging}`, { pipeline_stage: stageId });
    } catch {
      // Rollback
      setProspects(prev => prev.map(p =>
        p.id === dragging ? { ...p, pipeline_stage: prospect.pipeline_stage } : p
      ));
    } finally { setMovingId(null); }
  };

  const byStage = (stageId: string) => prospects.filter(p => p.pipeline_stage === stageId);

  const totalValue = prospects.filter(p => ['Proposition', 'Négociation', 'Gagné'].includes(p.pipeline_stage)).length;

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⚡</div>
          Chargement du pipeline...
        </div>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '1.5rem', gap: '1.25rem' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Pipeline Commercial
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
            {prospects.length} prospects · {totalValue} en cours de vente
          </p>
        </div>

        {/* KPIs */}
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          {[
            { stage: 'Gagné', color: '#3fb950' },
            { stage: 'Négociation', color: '#f97316' },
            { stage: 'Perdu', color: '#f85149' },
          ].map(({ stage, color }) => (
            <div key={stage} style={{
              padding: '0.5rem 1rem', borderRadius: '8px',
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color }}>{byStage(stage).length}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{stage}</div>
            </div>
          ))}
          <button
            onClick={loadPipeline}
            style={{
              padding: '0.5rem 0.875rem', borderRadius: '8px',
              background: 'var(--accent-blue)', border: 'none',
              color: '#fff', cursor: 'pointer', fontSize: '0.8125rem', alignSelf: 'center',
            }}
          >↻</button>
        </div>
      </div>

      {/* Kanban board */}
      <div style={{
        flex: 1, display: 'flex', gap: '0.875rem',
        overflowX: 'auto', paddingBottom: '0.5rem',
      }}>
        {PIPELINE_STAGES.map(stage => {
          const cards = byStage(stage.id);
          const isDragTarget = dragOver === stage.id;

          return (
            <div
              key={stage.id}
              onDragOver={e => handleDragOver(e, stage.id)}
              onDrop={e => handleDrop(e, stage.id)}
              onDragLeave={() => setDragOver(null)}
              style={{
                width: '240px', minWidth: '240px',
                display: 'flex', flexDirection: 'column',
                background: isDragTarget ? 'rgba(255,255,255,0.04)' : 'var(--bg-secondary)',
                border: `1px solid ${isDragTarget ? stage.color : 'var(--border-color)'}`,
                borderRadius: '10px',
                transition: 'all 0.15s',
              }}
            >
              {/* Stage header */}
              <div style={{
                padding: '0.875rem',
                borderBottom: '1px solid var(--border-color)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{
                    width: '8px', height: '8px', borderRadius: '50%',
                    background: stage.color,
                  }} />
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.875rem' }}>
                    {stage.icon} {stage.name}
                  </span>
                </div>
                <span style={{
                  background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                  borderRadius: '20px', padding: '1px 8px',
                  color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 600,
                }}>
                  {cards.length}
                </span>
              </div>

              {/* Cards */}
              <div style={{
                flex: 1, overflowY: 'auto', padding: '0.625rem',
                display: 'flex', flexDirection: 'column', gap: '0.5rem',
                minHeight: '120px',
              }}>
                {isDragTarget && cards.length === 0 && (
                  <div style={{
                    border: '2px dashed ' + stage.color, borderRadius: '8px',
                    padding: '1.5rem', textAlign: 'center',
                    color: stage.color, fontSize: '0.8125rem',
                    opacity: 0.7,
                  }}>
                    Déposer ici
                  </div>
                )}
                {cards.map(p => (
                  <KanbanCard
                    key={p.id}
                    prospect={p}
                    stageColor={stage.color}
                    onDragStart={handleDragStart}
                    isMoving={movingId === p.id}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function KanbanCard({ prospect: p, stageColor, onDragStart, isMoving }: {
  prospect: Prospect;
  stageColor: string;
  onDragStart: (e: React.DragEvent, id: string) => void;
  isMoving: boolean;
}) {
  const score = p.score ?? 0;
  return (
    <div
      draggable
      onDragStart={e => onDragStart(e, p.id)}
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderLeft: `3px solid ${stageColor}`,
        borderRadius: '8px', padding: '0.75rem',
        cursor: 'grab',
        opacity: isMoving ? 0.5 : 1,
        transition: 'all 0.15s',
        userSelect: 'none',
      }}
      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = stageColor; }}
      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-color)'; (e.currentTarget as HTMLElement).style.borderLeftColor = stageColor; }}
    >
      {/* Company + score */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <span style={{
          fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.8125rem',
          lineHeight: 1.3, flex: 1,
        }}>
          {p.company_name}
        </span>
        <span style={{
          flexShrink: 0, width: '28px', height: '28px', borderRadius: '50%',
          border: `2px solid ${SCORE_COLOR(score)}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: SCORE_COLOR(score), fontWeight: 700, fontSize: '0.6875rem',
        }}>
          {score}
        </span>
      </div>

      {/* Meta */}
      {p.city && (
        <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginBottom: '0.375rem' }}>
          📍 {p.city}
        </div>
      )}
      {p.naf_label && (
        <div style={{
          color: 'var(--text-secondary)', fontSize: '0.7rem',
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}>
          {p.naf_label}
        </div>
      )}

      {/* Contact icons */}
      <div style={{ display: 'flex', gap: '0.375rem', marginTop: '0.625rem' }}>
        {p.email && <span title={p.email} style={{ fontSize: '0.75rem' }}>📧</span>}
        {p.phone && <span title={p.phone} style={{ fontSize: '0.75rem' }}>📞</span>}
      </div>
    </div>
  );
}
