import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { pipelineApi } from '../api/pipeline';
import { prospectsApi } from '../api/prospects';

export interface PipelineState {
  prospects: any[];
  stages: any[];
  loading: boolean;
  error: string | null;
}

// Hook principal utilisé par Pipeline.tsx
export const usePipeline = () => {
  const qc = useQueryClient();

  const { data: board, isLoading: boardLoading, error: boardError } = useQuery({
    queryKey: ['pipeline-board'],
    queryFn: () => pipelineApi.getBoard(),
    staleTime: 30_000,
  });

  const { data: stages, isLoading: stagesLoading, error: stagesError } = useQuery({
    queryKey: ['pipeline-stages'],
    queryFn: () => pipelineApi.listStages(),
    staleTime: 5 * 60_000,
  });

  const changeStage = async (id: string, stage_id: string, position?: number) => {
    await prospectsApi.updateStage(id, stage_id, position || 0);
    qc.invalidateQueries({ queryKey: ['pipeline-board'] });
    qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
  };

  const refresh = async () => {
    await qc.invalidateQueries({ queryKey: ['pipeline-board'] });
    await qc.invalidateQueries({ queryKey: ['pipeline-stages'] });
  };

  return {
    pipeline: board || { prospects: [], stages: [] },
    stages: stages || [],
    loading: boardLoading || stagesLoading,
    error: (boardError || stagesError)?.message || null,
    refresh,
    changeStage,
  };
};

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
