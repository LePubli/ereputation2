import { useState, useEffect } from 'react';
import { pipelineService } from '@/services';

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
