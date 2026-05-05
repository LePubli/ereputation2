import { PluginManager } from '@/components/PluginManager';

export default function Plugins() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Gestion des Plugins</h1>
        <p className="text-gray-500 mt-1">Installez, activez et mettez à jour vos plugins</p>
      </div>

      <PluginManager />
    </div>
  );
}
