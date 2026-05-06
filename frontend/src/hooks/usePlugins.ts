import { useState, useEffect } from 'react';
import { pluginService } from '@/services';

export function usePlugins() {
  const [plugins, setPlugins] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPlugins = async () => {
    try {
      setLoading(true);
      const data = await pluginService.list();
      setPlugins(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement des plugins');
    } finally {
      setLoading(false);
    }
  };

  const togglePlugin = async (pluginName: string, enable: boolean) => {
    try {
      if (enable) {
        await pluginService.enable(pluginName);
      } else {
        await pluginService.disable(pluginName);
      }
      await fetchPlugins();
    } catch (err) {
      throw err;
    }
  };

  useEffect(() => {
    fetchPlugins();
  }, []);

  return {
    plugins,
    loading,
    error,
    refresh: fetchPlugins,
    togglePlugin,
  };
}
