import { useState, useEffect } from 'react';
import { prospectService } from '@/services';

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
