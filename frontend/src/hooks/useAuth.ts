import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi } from '../api/auth';
import { apiClient } from '../api/client';
import type { AuthUser } from '../types';

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: apiClient.isAuthenticated(),
      loading: false,

      login: async (email: string, password: string) => {
        set({ loading: true });
        try {
          await apiClient.login(email, password);
          const user = await authApi.me();
          set({ user, isAuthenticated: true, loading: false });
        } catch (e) {
          set({ loading: false });
          throw e;
        }
      },

      logout: async () => {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          try { await authApi.logout(refreshToken); } catch {}
        }
        apiClient.logout();
        set({ user: null, isAuthenticated: false });
      },
    }),
    {
      name: 'b2b-auth',
      partialize: (state) => ({ user: state.user }),
    } as any,
  )
);

export function useAuth() {
  const { user, isAuthenticated, loading, login, logout } = useAuthStore();
  return { user, isAuthenticated, loading, login, logout };
}
