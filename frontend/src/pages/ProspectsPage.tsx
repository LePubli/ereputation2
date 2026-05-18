import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';
import ProspectDetailModal from '../components/prospects/ProspectDetailModal';
import BulkActionsBar from '../components/ui/BulkActionsBar';

interface Prospect {
  id: string;
  company_name: string;
  siren?: string;
  siret?: string;
  naf_code?: string;
  naf_label?: string;
  legal_form?: string;
  city?: string;
  region?: string;
  postal_code?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  employee_range?: string;
  propensity_score?: number;
  propensity_category?: string;
  estimated_revenue?: number;
  stage_id?: string;
  sources_used?: string[];
  enrichment?: Record<string, unknown>;
  tags?: string[];
  created_at?: string;
}

interface Filters {
  search: string;
  region: string;
  score_min: string;
  has_email: string;
  has_phone: string;
  stage: string;
}

const STAGES = ['', 'Nouveau', 'Contacté', 'Qualifié', 'Proposition', 'Négociation', 'Gagné', 'Perdu'];
const REGIONS = ['', 'Hauts-de-France', 'Île-de-France', 'Auvergne-Rhône-Alpes', 'Bretagne', 'Occitanie', 'Normandie', 'Grand Est', 'Nouvelle-Aquitaine', 'Pays de la Loire', 'Provence-Alpes-Côte d\'Azur', 'Bourgogne-Franche-Comté', 'Centre-Val de Loire', 'Corse'];

const SCORE_COLOR = (s: number) =>
  s >= 75 ? 'var(--accent-green)' : s >= 50 ? 'var(--accent-blue)' : s >= 25 ? 'var(--accent-orange)' : 'var(--accent-red)';

export default function ProspectsPage() {
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const limit = 25;

  const [filters, setFilters] = useState<Filters>({
    search: '', region: '', score_min: '', has_email: '', has_phone: '', stage: '',
  });
  const [showFilters, setShowFilters] = useState(false);

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);

  const [enriching, setEnriching] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [sortField, setSortField] = useState('propensity_score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page), limit: String(limit),
        sort_by: sortField, sort_dir: sortDir,
      });
      if (filters.search) params.set('search', filters.search);
      if (filters.region) params.set('region', filters.region);
      if (filters.score_min) params.set('score_min', filters.score_min);
      if (filters.has_email === 'true') params.set('has_email', 'true');
      if (filters.has_phone === 'true') params.set('has_phone', 'true');
      if (filters.stage) params.set('pipeline_stage', filters.stage);

      const data = await apiClient.get(`/prospects/?${params}`);
      setProspects(data.items || []);
      setTotal(data.total || 0);
    } finally { setLoading(false); }
  }, [page, filters, sortField, sortDir]);

  useEffect(() => { load(); }, [load]);

  const handleSort = (field: string) => {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortField(field); setSortDir('desc'); }
  };

  const toggleSelect = (id: string) => {
    setSelected(prev => {
      const n = new Set(prev);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  };

  const toggleAll = () => {
    if (selected.size === prospects.length) setSelected(new Set());
    else setSelected(new Set(prospects.map(p => p.id)));
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const ids = selected.size > 0 ? Array.from(selected) : undefined;
      const params = new URLSearchParams();
      if (ids) ids.forEach(id => params.append('ids', id));
      const blob = await apiClient.getBlob(`/prospects/export?${params}`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url;
      a.download = `prospects_${new Date().toISOString().slice(0, 10)}.csv`; a.click();
      URL.revokeObjectURL(url);
    } finally { setExporting(false); }
  };

  const handleBulkEnrich = async () => {
    if (selected.size === 0) return;
    setEnriching(true);
    try {
      await apiClient.post('/prospects/bulk-enrich', { ids: Array.from(selected) });
      load();
    } finally { setEnriching(false); }
  };

  const handleBulkDelete = async () => {
    if (!confirm(`Supprimer ${selected.size} prospect(s) ?`)) return;
    await apiClient.post('/prospects/bulk-delete', { ids: Array.from(selected) });
    setSelected(new Set());
    load();
  };

  const handleStageChange = async (id: string, stage: string) => {
    await apiClient.patch(`/prospects/${id}`, { pipeline_stage: stage });
    setProspects(prev => prev.map(p => p.id === id ? { ...p, pipeline_stage: stage } : p));
  };

  const totalPages = Math.ceil(total / limit);
  const activeFiltersCount = Object.values(filters).filter(Boolean).length;

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1.5rem' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Prospects
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '0.25rem 0 0' }}>
            {total.toLocaleString('fr-FR')} entreprises · Page {page}/{totalPages || 1}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button
            onClick={() => setShowFilters(f => !f)}
            style={{
              padding: '0.5rem 0.875rem', borderRadius: '8px',
              background: showFilters ? 'rgba(47,129,247,0.15)' : 'var(--bg-tertiary)',
              border: `1px solid ${showFilters ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
              color: showFilters ? 'var(--accent-blue)' : 'var(--text-secondary)',
              cursor: 'pointer', fontSize: '0.8125rem',
              display: 'flex', alignItems: 'center', gap: '0.375rem',
            }}
          >
            🔽 Filtres
            {activeFiltersCount > 0 && (
              <span style={{
                background: 'var(--accent-blue)', color: '#fff',
                borderRadius: '10px', padding: '0 5px', fontSize: '0.7rem', fontWeight: 700,
              }}>{activeFiltersCount}</span>
            )}
          </button>
          <button
            onClick={handleExport}
            disabled={exporting}
            style={{
              padding: '0.5rem 0.875rem', borderRadius: '8px',
              background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
              color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.8125rem',
            }}
          >
            {exporting ? '...' : '⬇️ Export CSV'}
          </button>
          <button
            onClick={load}
            style={{
              padding: '0.5rem 0.875rem', borderRadius: '8px',
              background: 'var(--accent-blue)', border: 'none',
              color: '#fff', cursor: 'pointer', fontSize: '0.8125rem',
            }}
          >↻ Actualiser</button>
        </div>
      </div>

      {/* Search bar */}
      <div style={{ position: 'relative' }}>
        <span style={{
          position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)',
          color: 'var(--text-muted)', fontSize: '0.875rem',
        }}>🔍</span>
        <input
          type="text"
          placeholder="Rechercher par nom, SIREN, ville..."
          value={filters.search}
          onChange={e => { setFilters(f => ({ ...f, search: e.target.value })); setPage(1); }}
          style={{
            width: '100%', padding: '0.625rem 1rem 0.625rem 2.5rem',
            background: 'var(--bg-card)', border: '1px solid var(--border-color)',
            borderRadius: '8px', color: 'var(--text-primary)', fontSize: '0.875rem',
            outline: 'none', boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.75rem',
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: '8px', padding: '1rem',
          animation: 'fadeIn 0.15s ease',
        }}>
          <FilterSelect label="Région" value={filters.region} onChange={v => { setFilters(f => ({ ...f, region: v })); setPage(1); }} options={REGIONS} />
          <FilterSelect label="Étape pipeline" value={filters.stage} onChange={v => { setFilters(f => ({ ...f, stage: v })); setPage(1); }} options={STAGES} />
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>Score min</label>
            <input
              type="number" min="0" max="100"
              placeholder="0-100"
              value={filters.score_min}
              onChange={e => { setFilters(f => ({ ...f, score_min: e.target.value })); setPage(1); }}
              style={{
                width: '100%', padding: '0.5rem 0.75rem',
                background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                borderRadius: '6px', color: 'var(--text-primary)', fontSize: '0.875rem',
                outline: 'none', boxSizing: 'border-box',
              }}
            />
          </div>
          <FilterToggle label="A un email" value={filters.has_email} onChange={v => { setFilters(f => ({ ...f, has_email: v })); setPage(1); }} />
          <FilterToggle label="A un téléphone" value={filters.has_phone} onChange={v => { setFilters(f => ({ ...f, has_phone: v })); setPage(1); }} />
          <button
            onClick={() => { setFilters({ search: '', region: '', score_min: '', has_email: '', has_phone: '', stage: '' }); setPage(1); }}
            style={{
              padding: '0.5rem', borderRadius: '6px',
              background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
              color: 'var(--accent-red)', cursor: 'pointer', fontSize: '0.8125rem',
              alignSelf: 'flex-end',
            }}
          >✕ Réinitialiser</button>
        </div>
      )}

      {/* Table */}
      <div style={{
        flex: 1, overflow: 'auto',
        background: 'var(--bg-card)', border: '1px solid var(--border-color)',
        borderRadius: '10px',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
          <colgroup>
            <col style={{ width: '40px' }} />
            <col style={{ width: '240px' }} />
            <col style={{ width: '140px' }} />
            <col style={{ width: '160px' }} />
            <col style={{ width: '80px' }} />
            <col style={{ width: '80px' }} />
            <col style={{ width: '80px' }} />
            <col style={{ width: '130px' }} />
            <col style={{ width: '60px' }} />
          </colgroup>
          <thead>
            <tr style={{ background: 'var(--bg-secondary)', position: 'sticky', top: 0, zIndex: 10 }}>
              <th style={{ padding: '0.625rem 0.75rem', textAlign: 'center' }}>
                <input type="checkbox" checked={selected.size === prospects.length && prospects.length > 0} onChange={toggleAll} style={{ cursor: 'pointer' }} />
              </th>
              {[
                { key: 'company_name', label: 'Entreprise' },
                { key: 'city', label: 'Localisation' },
                { key: 'naf_label', label: 'Activité' },
                { key: 'employee_count', label: 'Effectif' },
                { key: null, label: 'Contact' },
                { key: null, label: 'Site' },
                { key: 'pipeline_stage', label: 'Étape' },
                { key: 'score', label: 'Score' },
              ].map(col => (
                <th
                  key={col.key || col.label}
                  onClick={() => col.key && handleSort(col.key)}
                  style={{
                    padding: '0.625rem 0.75rem', textAlign: 'left',
                    color: 'var(--text-muted)', fontSize: '0.75rem',
                    fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em',
                    cursor: col.key ? 'pointer' : 'default',
                    whiteSpace: 'nowrap',
                    borderBottom: '1px solid var(--border-color)',
                  }}
                >
                  {col.label}
                  {col.key === sortField && <span style={{ marginLeft: '4px' }}>{sortDir === 'asc' ? '↑' : '↓'}</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 9 }).map((_, j) => (
                    <td key={j} style={{ padding: '0.75rem' }}>
                      <div style={{
                        height: '14px', borderRadius: '4px',
                        background: 'var(--bg-tertiary)',
                        width: j === 0 ? '20px' : `${60 + Math.random() * 40}%`,
                        animation: 'pulse 1.5s ease infinite',
                      }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : prospects.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>🔍</div>
                  Aucun prospect trouvé
                </td>
              </tr>
            ) : (
              prospects.map(p => {
                const isSelected = selected.has(p.id);
                const score = p.score ?? 0;
                return (
                  <tr
                    key={p.id}
                    style={{
                      background: isSelected ? 'rgba(47,129,247,0.06)' : 'transparent',
                      borderBottom: '1px solid var(--border-color)',
                      transition: 'background 0.1s',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={e => { if (!isSelected) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.03)'; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = isSelected ? 'rgba(47,129,247,0.06)' : 'transparent'; }}
                  >
                    <td style={{ padding: '0.75rem', textAlign: 'center' }} onClick={e => e.stopPropagation()}>
                      <input type="checkbox" checked={isSelected} onChange={() => toggleSelect(p.id)} style={{ cursor: 'pointer' }} />
                    </td>
                    <td style={{ padding: '0.75rem' }} onClick={() => setSelectedProspect(p)}>
                      <div style={{
                        fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem',
                        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                      }}>
                        {p.company_name}
                      </div>
                      {p.siren && <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>SIREN {p.siren}</div>}
                    </td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-secondary)', fontSize: '0.8125rem' }} onClick={() => setSelectedProspect(p)}>
                      <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {p.city || '—'}
                        {p.postal_code && <span style={{ color: 'var(--text-muted)' }}> {p.postal_code}</span>}
                      </div>
                    </td>
                    <td style={{ padding: '0.75rem' }} onClick={() => setSelectedProspect(p)}>
                      <div style={{
                        color: 'var(--text-secondary)', fontSize: '0.75rem',
                        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                      }}>
                        {p.naf_label || '—'}
                      </div>
                      {p.naf_code && <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>{p.naf_code}</div>}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8125rem' }} onClick={() => setSelectedProspect(p)}>
                      {p.employee_count ? p.employee_count.toLocaleString() : '—'}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                      <div style={{ display: 'flex', gap: '4px', justifyContent: 'center' }}>
                        {p.email && <span title={p.email} style={{ cursor: 'pointer', fontSize: '0.875rem' }} onClick={e => { e.stopPropagation(); window.location.href = `mailto:${p.email}`; }}>📧</span>}
                        {p.phone && <span title={p.phone} style={{ cursor: 'pointer', fontSize: '0.875rem' }} onClick={e => { e.stopPropagation(); window.location.href = `tel:${p.phone}`; }}>📞</span>}
                        {!p.email && !p.phone && <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>—</span>}
                      </div>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                      {p.website
                        ? <a href={p.website} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} style={{ color: 'var(--accent-blue)', fontSize: '0.75rem' }}>🌐</a>
                        : <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>—</span>}
                    </td>
                    <td style={{ padding: '0.75rem' }} onClick={() => setSelectedProspect(p)}>
                      {p.pipeline_stage ? (
                        <span style={{
                          padding: '2px 8px', borderRadius: '20px', fontSize: '0.7rem',
                          background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
                          color: 'var(--text-secondary)', whiteSpace: 'nowrap',
                        }}>
                          {p.pipeline_stage}
                        </span>
                      ) : <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>—</span>}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }} onClick={() => setSelectedProspect(p)}>
                      <div style={{
                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                        width: '36px', height: '36px', borderRadius: '50%',
                        border: `2px solid ${SCORE_COLOR(score)}`,
                        color: SCORE_COLOR(score), fontWeight: 700, fontSize: '0.75rem',
                      }}>
                        {score}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', alignItems: 'center' }}>
          <button onClick={() => setPage(1)} disabled={page === 1} style={paginationBtn(page === 1)}>«</button>
          <button onClick={() => setPage(p => p - 1)} disabled={page === 1} style={paginationBtn(page === 1)}>‹</button>
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            const p = Math.max(1, Math.min(totalPages - 4, page - 2)) + i;
            return (
              <button key={p} onClick={() => setPage(p)} style={paginationBtn(false, p === page)}>{p}</button>
            );
          })}
          <button onClick={() => setPage(p => p + 1)} disabled={page === totalPages} style={paginationBtn(page === totalPages)}>›</button>
          <button onClick={() => setPage(totalPages)} disabled={page === totalPages} style={paginationBtn(page === totalPages)}>»</button>
        </div>
      )}

      {/* Bulk actions */}
      <BulkActionsBar
        count={selected.size}
        onClear={() => setSelected(new Set())}
        actions={[
          { label: 'Enrichir', icon: '⚡', action: handleBulkEnrich, loading: enriching, variant: 'success' },
          { label: 'Exporter', icon: '⬇️', action: handleExport, loading: exporting },
          { label: 'Supprimer', icon: '🗑️', action: handleBulkDelete, variant: 'danger' },
        ]}
      />

      {/* Detail modal */}
      {selectedProspect && (
        <ProspectDetailModal
          prospect={selectedProspect}
          onClose={() => setSelectedProspect(null)}
          onStageChange={handleStageChange}
        />
      )}

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        input[type="text"]::placeholder { color: var(--text-muted); }
      `}</style>
    </div>
  );
}

/* ---------- Helpers ---------- */

function paginationBtn(disabled: boolean, active = false) {
  return {
    width: '32px', height: '32px', borderRadius: '6px',
    background: active ? 'var(--accent-blue)' : 'var(--bg-card)',
    border: `1px solid ${active ? 'var(--accent-blue)' : 'var(--border-color)'}`,
    color: active ? '#fff' : disabled ? 'var(--text-muted)' : 'var(--text-secondary)',
    cursor: disabled ? 'not-allowed' as const : 'pointer' as const,
    fontSize: '0.875rem', display: 'flex' as const, alignItems: 'center' as const, justifyContent: 'center' as const,
  } as React.CSSProperties;
}

function FilterSelect({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{
          width: '100%', padding: '0.5rem 0.75rem',
          background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
          borderRadius: '6px', color: value ? 'var(--text-primary)' : 'var(--text-muted)',
          fontSize: '0.875rem', outline: 'none', cursor: 'pointer',
        }}
      >
        {options.map(o => <option key={o} value={o}>{o || `Toutes (${label})`}</option>)}
      </select>
    </div>
  );
}

function FilterToggle({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>{label}</label>
      <div style={{ display: 'flex', gap: '0.25rem' }}>
        {[{ v: '', l: 'Tous' }, { v: 'true', l: 'Oui' }].map(opt => (
          <button
            key={opt.v}
            onClick={() => onChange(opt.v)}
            style={{
              flex: 1, padding: '0.5rem', borderRadius: '6px',
              background: value === opt.v ? 'rgba(47,129,247,0.15)' : 'var(--bg-secondary)',
              border: `1px solid ${value === opt.v ? 'rgba(47,129,247,0.4)' : 'var(--border-color)'}`,
              color: value === opt.v ? 'var(--accent-blue)' : 'var(--text-secondary)',
              cursor: 'pointer', fontSize: '0.8125rem',
            }}
          >{opt.l}</button>
        ))}
      </div>
    </div>
  );
}
