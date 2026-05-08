import { useState } from 'react';
import { Plus, Download, Users } from 'lucide-react';
import { useProspects } from '../hooks/useProspects';
import { PageHeader } from '../components/layout/AppShell';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { AddProspectModal } from '../components/prospects/AddProspectModal';
import { ImportCSVDropzone } from '../components/prospects/ImportCSVDropzone';
import { ProspectsTable } from '../components/prospects/ProspectsTable';
import { ProspectDrawer } from '../components/prospects/ProspectDrawer';
import { FilterBar } from '../components/prospects/FilterBar';
import type { Prospect, ProspectFilters } from '../types';

export default function Prospects() {
  const [filters, setFilters] = useState<ProspectFilters>({});
  const [page, setPage] = useState(1);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);

  const { data, isLoading, error, refetch } = useProspects({ ...filters, page, page_size: 25 });

  const handleFilterChange = (newFilters: ProspectFilters) => {
    setFilters(newFilters);
    setPage(1);
  };

  const handleExport = () => {
    const params = new URLSearchParams();
    if (filters.search) params.set('search', filters.search);
    if (filters.stage_id) params.set('stage_id', filters.stage_id);
    if (filters.naf_code) params.set('naf_code', filters.naf_code);
    if (filters.region) params.set('region', filters.region);
    if (filters.propensity_category) params.set('propensity_category', filters.propensity_category);
    window.open(`/api/v1/prospects/export/csv?${params.toString()}`, '_blank');
  };

  return (
    <>
      <PageHeader
        title="Prospects"
        description={data ? `${data.total} entreprise(s)` : 'Gestion des prospects B2B'}
        actions={
          <>
            <button onClick={() => setShowImport((v) => !v)} className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50">
              📤 Importer
            </button>
            <button onClick={handleExport} className="flex items-center gap-1.5 px-3 py-1.5 text-sm border rounded hover:bg-gray-50">
              <Download className="w-4 h-4" /> Export CSV
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" /> Ajouter
            </button>
          </>
        }
      />

      <div className="p-6 space-y-4">
        {showImport && <ImportCSVDropzone />}

        <FilterBar filters={filters} onChange={handleFilterChange} total={data?.total} />

        {isLoading && <div className="space-y-2">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-14" />)}</div>}

        {error && (
          <EmptyState
            title="Impossible de charger les prospects"
            action={<button onClick={() => refetch()} className="px-4 py-2 bg-blue-600 text-white rounded">Réessayer</button>}
          />
        )}

        {!isLoading && !error && data?.items.length === 0 && (
          <EmptyState
            title="Aucun prospect"
            description="Ajoutez votre premier prospect ou modifiez les filtres."
            icon={<Users className="w-12 h-12" />}
            action={
              <button onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded">
                <Plus className="w-4 h-4" /> Ajouter
              </button>
            }
          />
        )}

        {!isLoading && !error && data && data.items.length > 0 && (
          <>
            <ProspectsTable prospects={data.items} onRowClick={setSelectedProspect} />
            {data.total > data.page_size && (
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>Page {data.page} / {Math.ceil(data.total / data.page_size)}</span>
                <div className="flex gap-2">
                  <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
                    className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-gray-50">Précédent</button>
                  <button onClick={() => setPage((p) => p + 1)} disabled={page * data.page_size >= data.total}
                    className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-gray-50">Suivant</button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <AddProspectModal open={showAddModal} onClose={() => setShowAddModal(false)} />
      <ProspectDrawer prospect={selectedProspect} onClose={() => setSelectedProspect(null)} />
    </>
  );
}
