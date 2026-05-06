import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/dashboard';

export const useDashboardStats = () =>
  useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.getStats(),
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  });
