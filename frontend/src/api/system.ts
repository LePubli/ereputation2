import { apiClient } from './client';
import type { SystemInfo } from '../types';

export const systemApi = {
  health: async () => {
    const { data } = await apiClient.get('/system/health');
    return data;
  },

  info: async (): Promise<SystemInfo> => {
    const { data } = await apiClient.get<SystemInfo>('/system/info');
    return data;
  },
};
