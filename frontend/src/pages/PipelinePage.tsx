import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface Prospect {
  id: string;
  company_name: string;
  city?: string;
  propensity_score?: number;
  email?: string;
  phone?: string;
  stage_id: string | null;
  naf_label?: string;
}

interface Stage {
  id: string;
  name: string;
  color: string;
  slug: string;
}

const SCORE_COLOR = (s: number) =>
  s >= 75 ? '#3fb950' : s >= 50 ? '#2f81f7' : s >= 25 ? '#d29922' : '#f85149';

const DEFAULT_STAGES: Stage[] = [
  { id: '', name: 'Sans étape', color: '#8b949e', slug: '' },
];

export default function PipelinePage() {
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [stages, setStages] = useState<Stage[]>(DEFAULT_STAGES);
  const [loading, setLoading] = useState(true);
  const [dragging, setDragging] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState<string | null>(null);
  const [movingId, setMovingId] = useState<string | null>(null);

  useEffect(() => { loadAll(); }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [pData, sData] = await Promise.all([
        apiClient.get('/prospects?limit=500&sort_by=propensity_score&sort_dir=desc'),
        apiClient.get('/pipeline/stages'),
      ]);
      setProspects(pData.items || []);
      if (sData && Array.isArray(sData)) {
        setStages(sData);
      } else if (sData?.stages) {
        setStages(sData.stages);
      }
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
    if (!dragging) { setDragOver(null); return; }
    const prospect = prospects.find(p => p.id === dragging);
    if (!prospect || prospect.stage_id === stageId) { setDragOver(null); return; }

    const prev_stage_id = prospect.stage_id;
    setProspects(prev => prev.map(p =>
      p.id === dragging ? { ...p, stage_id: stageId } : p
    ));
    setMovingId(dragging);
    setDragging(null);
    setDragOver(null);

    try {
      await apiClient.patch(`/prospects/${dragging}/stage`, { stage_id: stageId, position: 0 });
    } catch {
      setProspects(prev => prev.map(p =>
        p.id === dragging ? { ...p, stage_id: prev_stage_id } : p
      ));
    } finally { setMovingId(null); }
  };

  const byStage = (stageId: string) => prospects.filter(p =>
    stageId === '__none__' ? !p.stage_id : p.stage_id === stageId
  );

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

  const wonStage = stages.find(s => s.slug === 'gagne' || s.name === 'Gagné');
  const lostStage = stages.find(s => s.slug === 'perdu' || s.name === 'Perdu');
  const negStage = stages.find(s => s.slug === 'negociation' || s.name === 'En négociation');

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '1.5rem', gap: '1.25rem' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Pipeline Commercial
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
            {prospects.length} prospects
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          {[
            { stage: wonStage, label: 'Gagné', color: '#3fb950' },
            { stage: negStage, label: 'Négociation', color: '#f97316' },
            { stage: lostStage, label: 'Perdu', color: '#f85149' },
          ].filter(s => s.stage).map(({ stage, label, color }) => (
            <div key={label} style={{ padding: '0.5rem 1rem', borderRadius: '8px', background: 'var(--bg-card)', border: '1px solid var(--border-color)', textAlign: 'center' }}>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color }}>{byStage(stage!.id).length}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{label}</div>
            </div>
          ))}
          <button onClick={loadAll} style={{ padding: '0.5rem 0.875rem', borderRadius: '8px', background: 'var(--accent-blue)', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '0.8125rem', alignSelf: 'center' }}>↻</button>
        </div>
      </div>

      {/* Kanban board */}
      <div style={{ flex: 1, display: 'flex', gap: '0.875rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
        {stages.map(stage => {
          const cards = byStage(stage.id);
          const isDragTarget = dragOver === stage.id;
          const color = stage.color || '#8b949e';

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
                border: `1px solid ${isDragTarget ? color : 'var(--border-color)'}`,
                borderRadius: '10px', transition: 'all 0.15s',
              }}
            >
              <div style={{ padding: '0.875rem', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: color }} />
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.875rem' }}>
                    {stage.name}
                  </span>
                </div>
                <span style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', borderRadius: '20px', padding: '1px 8px', color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 600 }}>
                  {cards.length}
                </span>
              </div>

              <div style={{ flex: 1, overflowY: 'auto', padding: '0.625rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', minHeight: '120px' }}>
                {isDragTarget && cards.length === 0 && (
                  <div style={{ border: '2px dashed ' + color, borderRadius: '8px', padding: '1.5rem', textAlign: 'center', color, fontSize: '0.8125rem', opacity: 0.7 }}>
                    Déposer ici
                  </div>
                )}
                {cards.map(p => (
                  <KanbanCard
                    key={p.id}
                    prospect={p}
                    stageColor={color}
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
  const score = p.propensity_score ?? 0;
  return (
    <div
      draggable
      onDragStart={e => onDragStart(e, p.id)}
      style={{
        background: 'var(--bg-card)', border: '1px solid var(--border-color)',
        borderLeft: `3px solid ${stageColor}`, borderRadius: '8px', padding: '0.75rem',
        cursor: 'grab', opacity: isMoving ? 0.5 : 1, transition: 'all 0.15s', userSelect: 'none',
      }}
      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = stageColor; }}
      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-color)'; (e.currentTarget as HTMLElement).style.borderLeftColor = stageColor; }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.8125rem', lineHeight: 1.3, flex: 1 }}>
          {p.company_name}
        </span>
        {score > 0 && (
          <span style={{ flexShrink: 0, width: '28px', height: '28px', borderRadius: '50%', border: `2px solid ${SCORE_COLOR(score)}`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: SCORE_COLOR(score), fontWeight: 700, fontSize: '0.6875rem' }}>
            {Math.round(score)}
          </span>
        )}
      </div>
      {p.city && <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginBottom: '0.375rem' }}>📍 {p.city}</div>}
      {p.naf_label && <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.naf_label}</div>}
      <div style={{ display: 'flex', gap: '0.375rem', marginTop: '0.625rem' }}>
        {p.email && <span title={p.email} style={{ fontSize: '0.75rem' }}>📧</span>}
        {p.phone && <span title={p.phone} style={{ fontSize: '0.75rem' }}>📞</span>}
      </div>
    </div>
  );
}
