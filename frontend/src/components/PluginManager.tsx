import { useState } from 'react';
import toast from 'react-hot-toast';
import { pluginService, systemService } from '@/services';
import type { Plugin } from '@/types';

interface PluginManagerProps {
  onPluginChange?: () => void;
}

export function PluginManager({ onPluginChange }: PluginManagerProps) {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [installing, setInstalling] = useState(false);

  const fetchPlugins = async () => {
    try {
      setLoading(true);
      const data = await pluginService.list();
      setPlugins(data);
    } catch (error) {
      toast.error('Erreur lors du chargement des plugins');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (pluginName: string, currentlyActive: boolean) => {
    try {
      if (currentlyActive) {
        await pluginService.disable(pluginName);
        toast.success(`Plugin ${pluginName} désactivé`);
      } else {
        await pluginService.enable(pluginName);
        toast.success(`Plugin ${pluginName} activé`);
      }
      await fetchPlugins();
      onPluginChange?.();
    } catch (error) {
      toast.error(`Erreur lors de la modification du plugin`);
    }
  };

  const handleUpdate = async (pluginName: string) => {
    try {
      setUpdating(pluginName);
      await pluginService.update(pluginName);
      toast.success(`Plugin ${pluginName} mis à jour`);
      await fetchPlugins();
      onPluginChange?.();
    } catch (error) {
      toast.error(`Erreur lors de la mise à jour du plugin`);
    } finally {
      setUpdating(null);
    }
  };

  const handleUninstall = async (pluginName: string) => {
    if (!confirm(`Êtes-vous sûr de vouloir désinstaller le plugin ${pluginName}?`)) {
      return;
    }

    try {
      await pluginService.uninstall(pluginName);
      toast.success(`Plugin ${pluginName} désinstallé`);
      await fetchPlugins();
      onPluginChange?.();
    } catch (error) {
      toast.error(`Erreur lors de la désinstallation du plugin`);
    }
  };

  const handleInstallZip = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setInstalling(true);
      const result = await pluginService.installFromZip(file);
      toast.success(`Plugin ${result.pluginName} installé avec succès`);
      await fetchPlugins();
      onPluginChange?.();
    } catch (error) {
      toast.error('Erreur lors de l\'installation du plugin');
    } finally {
      setInstalling(false);
      event.target.value = '';
    }
  };

  const handleUpdateApp = async () => {
    if (!confirm('Voulez-vous vraiment mettre à jour l\'application?')) {
      return;
    }

    try {
      const result = await systemService.updateApp();
      toast.success(`Application mise à jour vers la version ${result.version}`);
    } catch (error) {
      toast.error('Erreur lors de la mise à jour de l\'application');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header avec actions globales */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Gestion des Plugins</h2>
        
        <div className="flex items-center gap-3">
          <label className="btn-primary cursor-pointer">
            <input
              type="file"
              accept=".zip"
              onChange={handleInstallZip}
              className="hidden"
              disabled={installing}
            />
            {installing ? 'Installation...' : 'Installer un plugin (.zip)'}
          </label>
          
          <button onClick={handleUpdateApp} className="btn-secondary">
            Mettre à jour l'application
          </button>
        </div>
      </div>

      {/* Liste des plugins */}
      <div className="grid gap-4">
        {plugins.map((plugin) => (
          <div
            key={plugin.name}
            className="card flex items-start justify-between hover:shadow-lg transition-shadow"
          >
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  {plugin.name}
                </h3>
                <span className="text-xs bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2 py-0.5 rounded">
                  v{plugin.version}
                </span>
                {plugin.active && (
                  <span className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-0.5 rounded">
                    Actif
                  </span>
                )}
              </div>
              
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                {plugin.description}
              </p>
              
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>Auteur: {plugin.author}</span>
                {plugin.dependencies.length > 0 && (
                  <span>Dépendances: {plugin.dependencies.join(', ')}</span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => handleToggle(plugin.name, plugin.active)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  plugin.active
                    ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200 dark:bg-yellow-900 dark:text-yellow-300'
                    : 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-300'
                }`}
              >
                {plugin.active ? 'Désactiver' : 'Activer'}
              </button>

              <button
                onClick={() => handleUpdate(plugin.name)}
                disabled={updating === plugin.name}
                className="btn-secondary text-sm py-1.5"
              >
                {updating === plugin.name ? '...' : 'Mettre à jour'}
              </button>

              <button
                onClick={() => handleUninstall(plugin.name)}
                className="bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900 dark:text-red-300 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
              >
                Désinstaller
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
