import { apiClient } from './client';
import type { PluginsResponse } from '../types';

export const pluginsApi = {
  list: async (): Promise<PluginsResponse> => {
    const { data } = await apiClient.get<PluginsResponse>('/plugins');
    return data;
  },

  toggle: async (name: string): Promise<{ name: string; active: boolean; message: string }> => {
    const { data } = await apiClient.post(`/plugins/${name}/toggle`);
    return data;
  },
};
