import { useState, useEffect } from 'react';
import { pipelineService, prospectService } from '@/services';

export function usePipeline() {
  const [pipeline, setPipeline] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPipeline = async () => {
    try {
      setLoading(true);
      const [pipelineData, metricsData, alertsData] = await Promise.all([
        pipelineService.getPipeline(),
        pipelineService.getMetrics(),
        pipelineService.getAlerts(),
      ]);
      setPipeline(pipelineData);
      setMetrics(metricsData);
      setAlerts(alertsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement du pipeline');
    } finally {
      setLoading(false);
    }
  };

  const changeStage = async (prospectId: string, stage: string) => {
    try {
      await pipelineService.changeStage(prospectId, stage);
      await fetchPipeline(); // Refresh after update
    } catch (err) {
      throw err;
    }
  };

  useEffect(() => {
    fetchPipeline();
  }, []);

  return {
    pipeline,
    metrics,
    alerts,
    loading,
    error,
    refresh: fetchPipeline,
    changeStage,
  };
}

export function useProspects() {
  const [prospects, setProspects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProspects = async () => {
    try {
      setLoading(true);
      const data = await prospectService.list();
      setProspects(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement des prospects');
    } finally {
      setLoading(false);
    }
  };

  const searchProspects = async (query: string) => {
    try {
      const data = await prospectService.search(query);
      setProspects(data);
    } catch (err) {
      throw err;
    }
  };

  useEffect(() => {
    fetchProspects();
  }, []);

  return {
    prospects,
    loading,
    error,
    refresh: fetchProspects,
    search: searchProspects,
  };
}

export function usePlugins() {
  const [plugins, setPlugins] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPlugins = async () => {
    try {
      setLoading(true);
      const data = await import('@/services').then(m => m.pluginService.list());
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
        await import('@/services').then(m => m.pluginService.enable(pluginName));
      } else {
        await import('@/services').then(m => m.pluginService.disable(pluginName));
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
