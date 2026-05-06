import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { pluginsApi } from '../api/plugins';
import { systemApi } from '../api/system';

export const usePlugins = () =>
  useQuery({
    queryKey: ['plugins'],
    queryFn: () => pluginsApi.list(),
    staleTime: 60_000,
  });

export const useTogglePlugin = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => pluginsApi.toggle(name),
    onSuccess: (data) => {
      toast.success(data.message);
      qc.invalidateQueries({ queryKey: ['plugins'] });
      qc.invalidateQueries({ queryKey: ['system-info'] });
    },
  });
};

export const useSystemInfo = () =>
  useQuery({
    queryKey: ['system-info'],
    queryFn: () => systemApi.info(),
    staleTime: 30_000,
  });
