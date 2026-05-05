import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { systemService } from '@/services';

export default function Settings() {
  const [version, setVersion] = useState<string>('');
  const [health, setHealth] = useState<any>(null);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        const [versionData, healthData] = await Promise.all([
          systemService.getVersion(),
          systemService.healthCheck(),
        ]);
        setVersion(versionData.version || '1.0.0');
        setHealth(healthData);
      } catch (error) {
        console.error('Error fetching info:', error);
      }
    };

    fetchInfo();
  }, []);

  const handleUpdate = async () => {
    if (!confirm('Voulez-vous vraiment mettre à jour l\'application vers la dernière version?')) {
      return;
    }

    try {
      setUpdating(true);
      const result = await systemService.updateApp();
      toast.success(`Application mise à jour vers ${result.version}`);
      setVersion(result.version);
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Paramètres</h1>
        <p className="text-gray-500 mt-1">Configuration système et informations</p>
      </div>

      {/* Version Info */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Informations système
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">
              Version actuelle
            </label>
            <p className="text-lg font-mono text-gray-900 dark:text-white">{version}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">
              État du système
            </label>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-lg text-gray-900 dark:text-white capitalize">
                {health?.status || 'inconnu'}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">
              Plugins actifs
            </label>
            <p className="text-lg text-gray-900 dark:text-white">
              {health?.plugins_active?.length || 0}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">
              Application
            </label>
            <p className="text-lg text-gray-900 dark:text-white">
              {health?.app || 'B2B Prospector'}
            </p>
          </div>
        </div>
      </div>

      {/* Update Section */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Mises à jour
        </h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-700 dark:text-gray-300">
              Vérifiez et installez les dernières mises à jour de l'application
            </p>
            <p className="text-sm text-gray-500 mt-1">
              La mise à jour peut prendre quelques minutes
            </p>
          </div>
          <button
            onClick={handleUpdate}
            disabled={updating}
            className="btn-primary"
          >
            {updating ? 'Mise à jour en cours...' : 'Mettre à jour'}
          </button>
        </div>
      </div>

      {/* API Endpoints */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Points d'accès API
        </h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <code className="text-sm text-primary-600">/api/v1/prospects</code>
            <span className="text-xs text-gray-500">Gestion des prospects</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <code className="text-sm text-primary-600">/api/v1/audit/digital</code>
            <span className="text-xs text-gray-500">Audit digital</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <code className="text-sm text-primary-600">/api/v1/pipeline</code>
            <span className="text-xs text-gray-500">Pipeline Kanban</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <code className="text-sm text-primary-600">/api/v1/plugins</code>
            <span className="text-xs text-gray-500">Gestion des plugins</span>
          </div>
        </div>
      </div>
    </div>
  );
}
