import { useState } from 'react';
import { Plus, Search, Users } from 'lucide-react';
import { useProspects } from '../hooks/useProspects';
import { PageHeader } from '../components/layout/AppShell';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { AddProspectModal } from '../components/prospects/AddProspectModal';
import { ImportCSVDropzone } from '../components/prospects/ImportCSVDropzone';
import { ProspectsTable } from '../components/prospects/ProspectsTable';

export default function Prospects() {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showImport, setShowImport] = useState(false);

  const { data, isLoading, error, refetch } = useProspects({
    search: search || undefined,
    page,
    page_size: 25,
  });

  return (
    <>
      <PageHeader
        title="Prospects"
        description={data ? `${data.total} entreprise(s) en base` : 'Gestion des prospects B2B'}
        actions={
          <>
            <button
              onClick={() => setShowImport((v) => !v)}
              className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50"
            >
              📤 Importer CSV
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Ajouter un prospect
            </button>
          </>
        }
      />

      <div className="p-6 space-y-4">
        {showImport && <ImportCSVDropzone />}

        {/* Recherche */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="search"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Rechercher par nom, SIREN, ville…"
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {isLoading && <div className="space-y-2">{[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-14" />)}</div>}

        {error && (
          <EmptyState
            title="Impossible de charger les prospects"
            description="Vérifiez la connexion au backend ou consultez les logs."
            action={
              <button onClick={() => refetch()} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                Réessayer
              </button>
            }
          />
        )}

        {!isLoading && !error && data && data.items.length === 0 && (
          <EmptyState
            title={search ? "Aucun résultat pour cette recherche" : "Aucun prospect en base"}
            description={search ? "Essayez d'autres termes" : "Commencez par ajouter votre premier prospect ou importez un fichier CSV."}
            icon={<Users className="w-12 h-12" />}
            action={
              !search ? (
                <button
                  onClick={() => setShowAddModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4" />
                  Ajouter le premier prospect
                </button>
              ) : null
            }
          />
        )}

        {!isLoading && !error && data && data.items.length > 0 && (
          <>
            <ProspectsTable prospects={data.items} />

            {/* Pagination */}
            {data.total > data.page_size && (
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>
                  Page {data.page} sur {Math.ceil(data.total / data.page_size)}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-gray-50"
                  >
                    Précédent
                  </button>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page * data.page_size >= data.total}
                    className="px-3 py-1 border rounded disabled:opacity-50 hover:bg-gray-50"
                  >
                    Suivant
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <AddProspectModal open={showAddModal} onClose={() => setShowAddModal(false)} />
    </>
  );
}
