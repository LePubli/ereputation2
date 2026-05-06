import { apiClient } from './client';
import type { KanbanBoard, PipelineStage } from '../types';

export const pipelineApi = {
  getBoard: async (): Promise<KanbanBoard> => {
    const { data } = await apiClient.get<KanbanBoard>('/pipeline/board');
    return data;
  },

  listStages: async (): Promise<PipelineStage[]> => {
    const { data } = await apiClient.get<PipelineStage[]>('/pipeline/stages');
    return data;
  },
};
