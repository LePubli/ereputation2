import { apiClient } from './client';
import type { AuthUser, TokenResponse } from '../types';

export const authApi = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    return apiClient.login(email, password) as Promise<TokenResponse>;
  },
  refresh: async (refresh_token: string): Promise<TokenResponse> => {
    return apiClient.post<TokenResponse>('/auth/refresh', { refresh_token });
  },
  logout: async (refresh_token: string): Promise<void> => {
    await apiClient.post('/auth/logout', { refresh_token });
  },
  me: async (): Promise<AuthUser> => {
    return apiClient.get<AuthUser>('/auth/me');
  },
  changePassword: async (current_password: string, new_password: string): Promise<void> => {
    await apiClient.post('/auth/change-password', { current_password, new_password });
  },
};
