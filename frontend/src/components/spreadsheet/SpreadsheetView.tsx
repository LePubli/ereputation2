import { useState, useCallback, useRef } from 'react';
import { Plus, Download, Settings2, Sparkles, RefreshCw, Trash2, ChevronDown } from 'lucide-react';
import type { Prospect } from '../../types';
import { CellRenderer } from './CellRenderer';
import { ColumnBuilder } from './ColumnBuilder';
import { AgentPanel } from '../agent/AgentPanel';
import { useProspects } from '../../hooks/useProspects';
import { useDeleteProspect } from '../../hooks/useProspects';
import { FilterBar } from '../prospects/FilterBar';
import type { ProspectFilters, ColumnConfig } from '../../types';

const DEFAULT_COLUMNS: ColumnConfig[] = [
  { id: 'company_name', name: 'Entreprise', source: 'core', field_path: 'company_name', display_type: 'text', width: 220, is_visible: true },
  { id: 'siren', name: 'SIREN', source: 'core', field_path: 'siren', display_type: 'mono', width: 110, is_visible: true },
  { id: 'city', name: 'Ville', source: 'core', field_path: 'city', display_type: 'text', width: 130, is_visible: true },
  { id: 'naf_label', name: 'Secteur', source: 'insee', field_path: 'naf_label', display_type: 'text', width: 200, is_visible: true },
  { id: 'employee_range', name: 'Effectifs', source: 'insee', field_path: 'employee_range', display_type: 'badge', width: 140, is_visible: true },
  { id: 'phone', name: 'Téléphone', source: 'pages_jaunes', field_path: 'phone', display_type: 'phone', width: 140, is_visible: true },
  { id: 'website', name: 'Site web', source: 'pappers', field_path: 'website', display_type: 'url', width: 200, is_visible: true },
  { id: 'propensity_score', name: 'Score', source: 'core', field_path: 'propensity_score', display_type: 'score', width: 90, is_visible: true },
  { id: 'propensity_category', name: 'Cat.', source: 'core', field_path: 'propensity_category', display_type: 'category', width: 80, is_visible: true },
  { id: 'sources_used', name: 'Sources', source: 'core', field_path: 'sources_used', display_type: 'sources', width: 160, is_visible: true },
];

export function SpreadsheetView() {
  const [filters, setFilters] = useState<ProspectFilters>({});
  const [page, setPage] = useState(1);
  const [columns, setColumns] = useState<ColumnConfig[]>(DEFAULT_COLUMNS);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [showColumnBuilder, setShowColumnBuilder] = useState(false);
  const [agentProspect, setAgentProspect] = useState<Prospect | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const { data, isLoading, refetch } = useProspects({ ...filters, page, page_size: 50 });
  const deleteMutation = useDeleteProspect();

  const toggleSelect = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
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
    if (filters.propensity_category) params.set('propensity_category', filters.propensity_category);
    window.open(`/api/v1/prospects/export/csv?${params.toString()}`, '_blank');
  };

  const visibleColumns = columns.filter((c) => c.is_visible);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar Clay-style */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-white flex-shrink-0">
        <div className="flex items-center gap-2">
          {selected.size > 0 ? (
            <>
              <span className="text-sm font-medium text-blue-600">{selected.size} sélectionné(s)</span>
              <button onClick={() => setAgentProspect(data?.items.find(p => selected.has(p.id)) || null)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-purple-600 text-white rounded hover:bg-purple-700">
                <Sparkles className="w-3.5 h-3.5" /> Agent IA ({selected.size})
              </button>
              <button onClick={handleDeleteSelected}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-red-50 text-red-700 border border-red-200 rounded hover:bg-red-100">
                <Trash2 className="w-3.5 h-3.5" /> Supprimer
              </button>
              <button onClick={() => setSelected(new Set())} className="text-xs text-gray-500 hover:text-gray-700">
                Désélectionner
              </button>
            </>
          ) : (
            <>
              <button onClick={() => setShowFilters(v => !v)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs border rounded hover:bg-gray-50">
                <Settings2 className="w-3.5 h-3.5" />
                Filtres {Object.values(filters).filter(Boolean).length > 0 && `(${Object.values(filters).filter(Boolean).length})`}
              </button>
              <button onClick={() => refetch()}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs border rounded hover:bg-gray-50">
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          {data && (
            <span className="text-xs text-gray-500">{data.total} prospect(s)</span>
          )}
          <button onClick={handleExport}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs border rounded hover:bg-gray-50">
            <Download className="w-3.5 h-3.5" /> CSV
          </button>
          <button onClick={() => setShowColumnBuilder(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700">
            <Plus className="w-3.5 h-3.5" /> Colonne
          </button>
        </div>
      </div>

      {/* Filtres dépliables */}
      {showFilters && (
        <div className="px-4 py-2 border-b bg-gray-50">
          <FilterBar filters={filters} onChange={(f) => { setFilters(f); setPage(1); }} total={data?.total} />
        </div>
      )}

      {/* Table scrollable */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <SpreadsheetSkeleton />
        ) : (
          <table className="clay-table">
            <thead>
              <tr>
                {/* Checkbox col */}
                <th className="clay-th" style={{ width: 40, minWidth: 40 }}>
                  <input type="checkbox"
                    checked={data && selected.size === data.items.length && data.items.length > 0}
                    onChange={toggleSelectAll}
                    className="w-3.5 h-3.5 accent-blue-600"
                  />
                </th>
                {/* # row */}
                <th className="clay-th" style={{ width: 40, minWidth: 40, color: '#d1d5db' }}>#</th>
                {visibleColumns.map((col) => (
                  <th key={col.id} className="clay-th" style={{ width: col.width, minWidth: col.width }}>
                    <div className="flex items-center gap-1.5">
                      <SourceDot source={col.source} />
                      <span>{col.name}</span>
                    </div>
                  </th>
                ))}
                {/* + Add column */}
                <th className="clay-th" style={{ width: 48, minWidth: 48 }}>
                  <button onClick={() => setShowColumnBuilder(true)}
                    className="text-gray-300 hover:text-blue-500 transition">
                    <Plus className="w-4 h-4" />
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((prospect, idx) => (
                <tr key={prospect.id}
                  className={`clay-tr ${selected.has(prospect.id) ? 'selected' : ''}`}
                  onClick={() => toggleSelect(prospect.id)}
                >
                  <td className="clay-td" onClick={(e) => e.stopPropagation()}>
                    <input type="checkbox" checked={selected.has(prospect.id)}
                      onChange={() => toggleSelect(prospect.id)}
                      className="w-3.5 h-3.5 accent-blue-600" />
                  </td>
                  <td className="clay-td" style={{ color: '#d1d5db', fontSize: 11 }}>
                    {(page - 1) * 50 + idx + 1}
                  </td>
                  {visibleColumns.map((col) => (
                    <td key={col.id} className="clay-td" style={{ width: col.width }}>
                      <CellRenderer
                        prospect={prospect}
                        column={col}
                        onAgentClick={(p) => setAgentProspect(p)}
                      />
                    </td>
                  ))}
                  <td className="clay-td" />
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {data && data.total > 50 && (
        <div className="flex items-center justify-between px-4 py-2 border-t bg-white flex-shrink-0 text-xs text-gray-500">
          <span>Page {page} / {Math.ceil(data.total / 50)}</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
              className="px-2.5 py-1 border rounded disabled:opacity-40 hover:bg-gray-50">← Précédent</button>
            <button onClick={() => setPage(p => p + 1)} disabled={page * 50 >= data.total}
              className="px-2.5 py-1 border rounded disabled:opacity-40 hover:bg-gray-50">Suivant →</button>
          </div>
        </div>
      )}

      {/* Modales */}
      {showColumnBuilder && (
        <ColumnBuilder
          columns={columns}
          onSave={(cols) => { setColumns(cols); setShowColumnBuilder(false); }}
          onClose={() => setShowColumnBuilder(false)}
        />
      )}
      {agentProspect && (
        <AgentPanel
          prospect={agentProspect}
          onClose={() => setAgentProspect(null)}
        />
      )}
    </div>
  );
}

function SourceDot({ source }: { source: string }) {
  const colors: Record<string, string> = {
    core: '#6b7280', insee: '#2563eb', bodacc: '#be185d',
    pappers: '#16a34a', pages_jaunes: '#d97706', google_maps: '#ea580c',
    ai_agent: '#7c3aed', societe_com: '#dc2626', trustpilot: '#065f46',
  };
  return (
    <span className="w-2 h-2 rounded-full flex-shrink-0 inline-block"
      style={{ background: colors[source] || '#9ca3af' }} />
  );
}

function SpreadsheetSkeleton() {
  return (
    <div className="p-4 space-y-2">
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className="h-9 skeleton rounded" />
      ))}
    </div>
  );
}
