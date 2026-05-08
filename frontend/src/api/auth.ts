import { apiClient } from './client';
import type { AuthUser, TokenResponse } from '../types';

export const authApi = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    const { data } = await apiClient.post<TokenResponse>('/auth/login', { email, password });
    return data;
  },
  refresh: async (refresh_token: string): Promise<TokenResponse> => {
    const { data } = await apiClient.post<TokenResponse>('/auth/refresh', { refresh_token });
    return data;
  },
  logout: async (refresh_token: string): Promise<void> => {
    await apiClient.post('/auth/logout', { refresh_token });
  },
  me: async (): Promise<AuthUser> => {
    const { data } = await apiClient.get<AuthUser>('/auth/me');
    return data;
  },
  changePassword: async (current_password: string, new_password: string): Promise<void> => {
    await apiClient.post('/auth/change-password', { current_password, new_password });
  },
};
