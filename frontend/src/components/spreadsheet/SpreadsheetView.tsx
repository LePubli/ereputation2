import { useState } from 'react';
import { Plus, Download, Settings2, Sparkles, RefreshCw, Trash2, Search } from 'lucide-react';
import type { Prospect } from '../../types';
import { CellRenderer } from './CellRenderer';
import { ColumnBuilder } from './ColumnBuilder';
import { AgentPanel } from '../agent/AgentPanel';
import { useProspects } from '../../hooks/useProspects';
import { useDeleteProspect } from '../../hooks/useProspects';
import { FilterBar } from '../prospects/FilterBar';
import type { ProspectFilters, ColumnConfig } from '../../types';

const DEFAULT_COLUMNS: ColumnConfig[] = [
  { id: 'company_name', name: 'Entreprise', source: 'core', field_path: 'company_name', display_type: 'text', width: 240, is_visible: true },
  { id: 'siren', name: 'SIREN', source: 'core', field_path: 'siren', display_type: 'mono', width: 110, is_visible: true },
  { id: 'city', name: 'Ville', source: 'core', field_path: 'city', display_type: 'text', width: 120, is_visible: true },
  { id: 'naf_label', name: 'Secteur', source: 'insee', field_path: 'naf_label', display_type: 'text', width: 180, is_visible: true },
  { id: 'employee_range', name: 'Effectifs', source: 'insee', field_path: 'employee_range', display_type: 'badge', width: 120, is_visible: true },
  { id: 'phone', name: 'Téléphone', source: 'pages_jaunes', field_path: 'phone', display_type: 'phone', width: 140, is_visible: true },
  { id: 'website', name: 'Site web', source: 'pappers', field_path: 'website', display_type: 'url', width: 180, is_visible: true },
  { id: 'propensity_score', name: 'Score', source: 'core', field_path: 'propensity_score', display_type: 'score', width: 80, is_visible: true },
  { id: 'propensity_category', name: 'Cat.', source: 'core', field_path: 'propensity_category', display_type: 'category', width: 75, is_visible: true },
  { id: 'sources_used', name: 'Sources', source: 'core', field_path: 'sources_used', display_type: 'sources', width: 150, is_visible: true },
];

const SOURCE_COLORS: Record<string, string> = {
  core: '#9aa3b0', insee: '#3468f6', bodacc: '#7c4dff',
  pappers: '#1bc15e', pages_jaunes: '#f5a623', google_maps: '#f64c4c',
  ai_agent: '#06b6d4', societe_com: '#ec4899', trustpilot: '#1bc15e',
};

export function SpreadsheetView() {
  const [filters, setFilters] = useState<ProspectFilters>({});
  const [page, setPage] = useState(1);
  const [columns, setColumns] = useState<ColumnConfig[]>(DEFAULT_COLUMNS);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [showColumnBuilder, setShowColumnBuilder] = useState(false);
  const [agentProspect, setAgentProspect] = useState<Prospect | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [search, setSearch] = useState('');

  const { data, isLoading, refetch } = useProspects({ ...filters, search: search || undefined, page, page_size: 50 });
  const deleteMutation = useDeleteProspect();

  const toggleSelect = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id); else next.add(id);
    setSelected(next);
  };

  const toggleSelectAll = () => {
    if (!data) return;
    if (selected.size === data.items.length) setSelected(new Set());
    else setSelected(new Set(data.items.map((p) => p.id)));
  };

  const handleDeleteSelected = async () => {
    if (!confirm(`Supprimer ${selected.size} prospect(s) ?`)) return;
    for (const id of selected) await deleteMutation.mutateAsync(id);
    setSelected(new Set());
  };

  const handleExport = () => {
    const params = new URLSearchParams();
    if (filters.search) params.set('search', filters.search);
    window.open(`/api/v1/prospects/export/csv?${params.toString()}`, '_blank');
  };

  const visibleColumns = columns.filter((c) => c.is_visible);
  const totalPages = data ? Math.ceil(data.total / 50) : 1;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#fff' }}>

      {/* Toolbar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--border-color)',
        background: '#fff', flexShrink: 0, gap: '0.75rem', flexWrap: 'wrap',
      }}>
        {/* Left */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {selected.size > 0 ? (
            <>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--accent-blue)' }}>
                {selected.size} sélectionné{selected.size > 1 ? 's' : ''}
              </span>
              <ToolBtn icon={<Sparkles size={13} />} label={`Agent IA (${selected.size})`} color="var(--accent-purple)"
                onClick={() => setAgentProspect(data?.items.find(p => selected.has(p.id)) || null)} />
              <ToolBtn icon={<Trash2 size={13} />} label="Supprimer" color="var(--accent-red)"
                onClick={handleDeleteSelected} />
              <button onClick={() => setSelected(new Set())}
                style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', padding: '0 4px' }}>
                ✕ Désélectionner
              </button>
            </>
          ) : (
            <>
              <ToolBtn icon={<Settings2 size={13} />} label={`Filtres${Object.values(filters).filter(Boolean).length > 0 ? ` (${Object.values(filters).filter(Boolean).length})` : ''}`}
                active={showFilters} onClick={() => setShowFilters(v => !v)} />
              <ToolBtn icon={<RefreshCw size={13} />} onClick={() => refetch()} />
            </>
          )}
        </div>

        {/* Center: search */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '0.375rem 0.75rem', flex: '1', maxWidth: '320px' }}>
          <Search size={13} color="var(--text-muted)" />
          <input
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
            placeholder="Rechercher un prospect..."
            style={{ background: 'none', border: 'none', outline: 'none', fontSize: '0.8125rem', color: 'var(--text-primary)', flex: 1, minWidth: 0 }}
          />
        </div>

        {/* Right */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {data && (
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
              {data.total.toLocaleString('fr-FR')} prospect{data.total > 1 ? 's' : ''}
            </span>
          )}
          <ToolBtn icon={<Download size={13} />} label="CSV" onClick={handleExport} />
          <button
            onClick={() => setShowColumnBuilder(true)}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.375rem',
              padding: '0.375rem 0.875rem', borderRadius: '8px',
              background: 'var(--accent-blue)', border: 'none',
              color: '#fff', cursor: 'pointer', fontSize: '0.8125rem', fontWeight: 500,
              boxShadow: '0 2px 8px rgba(52,104,246,0.25)',
            }}
          >
            <Plus size={13} /> Colonne
          </button>
        </div>
      </div>

      {/* Filter bar */}
      {showFilters && (
        <div style={{ padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--border-color)', background: 'var(--bg-tertiary)' }}>
          <FilterBar filters={filters} onChange={(f) => { setFilters(f); setPage(1); }} total={data?.total} />
        </div>
      )}

      {/* Table */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {isLoading ? (
          <SpreadsheetSkeleton />
        ) : (
          <table style={{ borderCollapse: 'collapse', width: 'max-content', minWidth: '100%', tableLayout: 'fixed' }}>
            <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
              <tr style={{ background: 'var(--table-header-bg)' }}>
                <th style={thStyle(40)}>
                  <input type="checkbox"
                    checked={!!(data && selected.size === data.items.length && data.items.length > 0)}
                    onChange={toggleSelectAll}
                    style={{ accentColor: 'var(--accent-blue)', cursor: 'pointer' }}
                  />
                </th>
                <th style={{ ...thStyle(40), color: 'var(--text-muted)', fontSize: '0.7rem' }}>#</th>
                {visibleColumns.map((col) => (
                  <th key={col.id} style={thStyle(col.width)}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ width: '7px', height: '7px', borderRadius: '50%', flexShrink: 0, background: SOURCE_COLORS[col.source] || '#9aa3b0', display: 'inline-block' }} />
                      {col.name}
                    </div>
                  </th>
                ))}
                <th style={thStyle(48)}>
                  <button onClick={() => setShowColumnBuilder(true)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
                    <Plus size={15} />
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              {data?.items.length === 0 ? (
                <tr>
                  <td colSpan={visibleColumns.length + 3} style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                    <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🏢</div>
                    Aucun prospect trouvé
                  </td>
                </tr>
              ) : (
                data?.items.map((prospect, idx) => (
                  <tr
                    key={prospect.id}
                    onClick={() => toggleSelect(prospect.id)}
                    style={{
                      borderBottom: '1px solid #f0f2f8',
                      background: selected.has(prospect.id) ? 'rgba(52,104,246,0.04)' : 'transparent',
                      cursor: 'pointer', transition: 'background 0.1s',
                    }}
                    onMouseEnter={e => { if (!selected.has(prospect.id)) (e.currentTarget as HTMLElement).style.background = 'var(--table-row-hover)'; }}
                    onMouseLeave={e => { if (!selected.has(prospect.id)) (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
                  >
                    <td style={tdStyle(40)} onClick={e => e.stopPropagation()}>
                      <input type="checkbox" checked={selected.has(prospect.id)}
                        onChange={() => toggleSelect(prospect.id)}
                        style={{ accentColor: 'var(--accent-blue)', cursor: 'pointer' }} />
                    </td>
                    <td style={{ ...tdStyle(40), color: 'var(--text-muted)', fontSize: '0.7rem', fontFamily: 'monospace' }}>
                      {(page - 1) * 50 + idx + 1}
                    </td>
                    {visibleColumns.map((col) => (
                      <td key={col.id} style={tdStyle(col.width)}>
                        <CellRenderer prospect={prospect} column={col} onAgentClick={(p) => setAgentProspect(p)} />
                      </td>
                    ))}
                    <td style={tdStyle(48)} />
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {data && data.total > 50 && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0.75rem 1.25rem', borderTop: '1px solid var(--border-color)',
          background: '#fff', flexShrink: 0,
        }}>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            Page <strong style={{ color: 'var(--text-primary)' }}>{page}</strong> sur {totalPages} — {data.total.toLocaleString('fr-FR')} résultats
          </span>
          <div style={{ display: 'flex', gap: '0.375rem' }}>
            <PagBtn label="← Précédent" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} />
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const p = Math.max(1, Math.min(page - 2, totalPages - 4)) + i;
              return (
                <PagBtn key={p} label={String(p)} onClick={() => setPage(p)} active={p === page} />
              );
            })}
            <PagBtn label="Suivant →" onClick={() => setPage(p => p + 1)} disabled={page * 50 >= data.total} />
          </div>
        </div>
      )}

      {showColumnBuilder && (
        <ColumnBuilder columns={columns} onSave={(cols) => { setColumns(cols); setShowColumnBuilder(false); }} onClose={() => setShowColumnBuilder(false)} />
      )}
      {agentProspect && <AgentPanel prospect={agentProspect} onClose={() => setAgentProspect(null)} />}
    </div>
  );
}

// ── Helpers styles
const thStyle = (w: number): React.CSSProperties => ({
  width: w, minWidth: w, maxWidth: w,
  padding: '0.625rem 0.875rem',
  fontSize: '0.75rem', fontWeight: 600,
  color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em',
  borderBottom: '2px solid var(--border-color)',
  whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
  textAlign: 'left', background: 'var(--table-header-bg)',
});

const tdStyle = (w: number): React.CSSProperties => ({
  width: w, minWidth: w, maxWidth: w,
  padding: '0.625rem 0.875rem',
  fontSize: '0.8125rem', color: 'var(--text-secondary)',
  whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
  verticalAlign: 'middle',
});

function ToolBtn({ icon, label, onClick, active, color }: {
  icon?: React.ReactNode; label?: string; onClick?: () => void; active?: boolean; color?: string;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: '0.375rem',
        padding: label ? '0.375rem 0.75rem' : '0.375rem',
        borderRadius: '8px', background: active ? 'rgba(52,104,246,0.08)' : '#fff',
        border: `1px solid ${active ? 'rgba(52,104,246,0.3)' : 'var(--border-color)'}`,
        color: color || (active ? 'var(--accent-blue)' : 'var(--text-secondary)'),
        cursor: 'pointer', fontSize: '0.8125rem', fontWeight: 500,
        transition: 'all 0.15s',
      }}
      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-hover)'; }}
      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = active ? 'rgba(52,104,246,0.08)' : '#fff'; }}
    >
      {icon}{label}
    </button>
  );
}

function PagBtn({ label, onClick, disabled, active }: { label: string; onClick: () => void; disabled?: boolean; active?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '0.3125rem 0.625rem', borderRadius: '6px', fontSize: '0.8125rem',
        background: active ? 'var(--accent-blue)' : '#fff',
        border: `1px solid ${active ? 'var(--accent-blue)' : 'var(--border-color)'}`,
        color: active ? '#fff' : 'var(--text-secondary)',
        cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.4 : 1,
        fontWeight: active ? 600 : 400, transition: 'all 0.1s',
      }}
    >{label}</button>
  );
}

function SpreadsheetSkeleton() {
  return (
    <div style={{ padding: '1rem' }}>
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} style={{ height: '40px', borderRadius: '4px', background: 'linear-gradient(90deg, #f0f2f8 25%, #e8ecf4 50%, #f0f2f8 75%)', backgroundSize: '200% 100%', animation: 'shimmer 1.5s infinite', marginBottom: '4px' }} />
      ))}
    </div>
  );
}
