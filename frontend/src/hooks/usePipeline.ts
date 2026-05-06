import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { pipelineApi } from '../api/pipeline';
import { prospectsApi } from '../api/prospects';

export const usePipelineBoard = () =>
  useQuery({
    queryKey: ['pipeline-board'],
    queryFn: () => pipelineApi.getBoard(),
    staleTime: 30_000,
  });

export const usePipelineStages = () =>
  useQuery({
    queryKey: ['pipeline-stages'],
    queryFn: () => pipelineApi.listStages(),
    staleTime: 5 * 60_000,
  });

export const useMoveProspect = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, stage_id, position }: { id: string; stage_id: string; position: number }) =>
      prospectsApi.updateStage(id, stage_id, position),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pipeline-board'] });
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
    onError: () => {
      toast.error("Échec du déplacement");
    },
  });
};
