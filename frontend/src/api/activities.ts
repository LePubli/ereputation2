import { apiClient } from './client';
import type { Activity } from '../types';

export const activitiesApi = {
  list: async (prospect_id: string): Promise<Activity[]> => {
    const { data } = await apiClient.get<Activity[]>(`/activities/prospect/${prospect_id}`);
    return data;
  },
  create: async (payload: {
    prospect_id: string; type: string; title: string;
    body?: string; outcome?: string; scheduled_at?: string; is_completed?: boolean;
  }): Promise<Activity> => {
    const { data } = await apiClient.post<Activity>('/activities', payload);
    return data;
  },
  update: async (id: string, payload: Partial<Activity>): Promise<Activity> => {
    const { data } = await apiClient.patch<Activity>(`/activities/${id}`, payload);
    return data;
  },
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/activities/${id}`);
  },
};
