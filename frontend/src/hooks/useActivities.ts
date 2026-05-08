import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { activitiesApi } from '../api/activities';

export const useActivities = (prospect_id: string | undefined) =>
  useQuery({
    queryKey: ['activities', prospect_id],
    queryFn: () => activitiesApi.list(prospect_id!),
    enabled: !!prospect_id,
    staleTime: 15_000,
  });

export const useCreateActivity = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: activitiesApi.create,
    onSuccess: (data) => {
      toast.success('Activité ajoutée');
      qc.invalidateQueries({ queryKey: ['activities', data.prospect_id] });
      qc.invalidateQueries({ queryKey: ['prospect', data.prospect_id] });
    },
  });
};

export const useDeleteActivity = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, prospect_id }: { id: string; prospect_id: string }) =>
      activitiesApi.delete(id),
    onSuccess: (_, vars) => {
      toast.success('Activité supprimée');
      qc.invalidateQueries({ queryKey: ['activities', vars.prospect_id] });
    },
  });
};
