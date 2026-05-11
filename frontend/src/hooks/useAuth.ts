import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi } from '../api/auth';
import { apiClient } from '../api/client';
import type { AuthUser } from '../types';

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<boolean>;
  setTokens: (access: string, refresh: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setTokens: (access: string, refresh: string) => {
        set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${access}`;
      },

      login: async (email: string, password: string) => {
        const tokens = await authApi.login(email, password);
        get().setTokens(tokens.access_token, tokens.refresh_token);
        const user = await authApi.me();
        set({ user });
      },

      logout: async () => {
        const { refreshToken } = get();
        if (refreshToken) {
          try { await authApi.logout(refreshToken); } catch {}
        }
        delete apiClient.defaults.headers.common['Authorization'];
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get();
        if (!refreshToken) return false;
        try {
          const tokens = await authApi.refresh(refreshToken);
          get().setTokens(tokens.access_token, tokens.refresh_token);
          return true;
        } catch {
          get().logout();
          return false;
        }
      },
    }),
    {
      name: 'b2b-auth',
      partialState: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    } as any,
  )
);

// Injecte le token dans axios au boot
const { accessToken } = useAuthStore.getState();
if (accessToken) {
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
}

// Interceptor pour auto-refresh sur 401
apiClient.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshed = await useAuthStore.getState().refreshAccessToken();
      if (refreshed) {
        const { accessToken } = useAuthStore.getState();
        error.config.headers['Authorization'] = `Bearer ${accessToken}`;
        return apiClient.request(error.config);
      }
    }
    return Promise.reject(error);
  }
);

// Hook helper for components
export function useAuth() {
  const { user, isAuthenticated, logout } = useAuthStore();
  return { user, isAuthenticated, logout };
}
