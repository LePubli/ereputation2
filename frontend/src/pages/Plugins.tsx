import { Puzzle, Power } from 'lucide-react';
import { usePlugins, useTogglePlugin } from '../hooks/usePlugins';
import { PageHeader } from '../components/layout/AppShell';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';

export default function Plugins() {
  const { data, isLoading, error, refetch } = usePlugins();
  const toggleMutation = useTogglePlugin();

  if (isLoading) {
    return (
      <>
        <PageHeader title="Plugins" description="Modules optionnels de l'application" />
        <div className="p-6 space-y-3">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-20" />)}
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <PageHeader title="Plugins" />
        <div className="p-6">
          <EmptyState
            title="Impossible de charger les plugins"
            description="Le backend n'a pas répondu. Vérifiez que les routes plugins sont bien chargées."
            icon={<Puzzle className="w-12 h-12" />}
            action={
              <button onClick={() => refetch()} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                Réessayer
              </button>
            }
          />
        </div>
      </>
    );
  }

  const plugins = data?.plugins ?? [];

  return (
    <>
      <PageHeader
        title="Plugins"
        description={`${data?.active_count ?? 0} actif(s) sur ${data?.total ?? 0}`}
      />
      <div className="p-6">
        {plugins.length === 0 ? (
          <EmptyState
            title="Aucun plugin enregistré"
            description="Le seed initial n'a pas été exécuté."
            icon={<Puzzle className="w-12 h-12" />}
          />
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 divide-y">
            {plugins.map((plugin) => (
              <div key={plugin.name} className="flex items-center justify-between p-4 hover:bg-gray-50">
                <div className="flex items-start gap-3">
                  <div className={`w-2 h-2 mt-2 rounded-full ${plugin.active ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">{plugin.name}</h3>
                      <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded font-mono">
                        v{plugin.version}
                      </span>
                      {plugin.active ? (
                        <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded">Actif</span>
                      ) : (
                        <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">Inactif</span>
                      )}
                    </div>
                    {plugin.description && (
                      <p className="text-sm text-gray-500 mt-1">{plugin.description}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => toggleMutation.mutate(plugin.name)}
                  disabled={toggleMutation.isPending}
                  className={`flex items-center gap-2 px-3 py-1.5 text-sm rounded transition disabled:opacity-50 ${
                    plugin.active
                      ? 'bg-red-50 text-red-700 hover:bg-red-100'
                      : 'bg-green-50 text-green-700 hover:bg-green-100'
                  }`}
                >
                  <Power className="w-4 h-4" />
                  {plugin.active ? 'Désactiver' : 'Activer'}
                </button>
              </div>
            ))}
          </div>
        )}

        <p className="text-xs text-gray-400 mt-4">
          ⚠️ La modification d'un plugin nécessite un redémarrage du backend pour être effective.
        </p>
      </div>
    </>
  );
}
