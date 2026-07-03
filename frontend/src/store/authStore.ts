import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '../services/api';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'supervisor' | 'operator' | 'viewer';
  avatar_url?: string | null;
  last_login_at?: string | null;
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<boolean>;
  updateUser: (user: Partial<User>) => void;
  hasRole: (minimum: 'viewer' | 'operator' | 'supervisor' | 'admin') => boolean;
}

const ROLE_LEVEL: Record<string, number> = {
  viewer: 0,
  operator: 1,
  supervisor: 2,
  admin: 3,
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        const { data } = await api.post('/api/v1/auth/login', { email, password });
        set({
          token: data.access_token,
          refreshToken: data.refresh_token,
          user: data.user,
          isAuthenticated: true,
        });
      },

      logout: async () => {
        const { refreshToken } = get();
        try {
          if (refreshToken) {
            await api.post('/api/v1/auth/logout', { refresh_token: refreshToken });
          }
        } catch {
          // best-effort
        }
        set({ token: null, refreshToken: null, user: null, isAuthenticated: false });
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get();
        if (!refreshToken) return false;
        try {
          const { data } = await api.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          });
          set({
            token: data.access_token,
            refreshToken: data.refresh_token,
            user: data.user,
            isAuthenticated: true,
          });
          return true;
        } catch {
          set({ token: null, refreshToken: null, user: null, isAuthenticated: false });
          return false;
        }
      },

      updateUser: (updates: Partial<User>) => {
        const { user } = get();
        if (user) set({ user: { ...user, ...updates } });
      },

      hasRole: (minimum) => {
        const { user } = get();
        if (!user) return false;
        return (ROLE_LEVEL[user.role] ?? -1) >= (ROLE_LEVEL[minimum] ?? 0);
      },
    }),
    { name: 'auth-storage', partialize: (s) => ({ token: s.token, refreshToken: s.refreshToken, user: s.user, isAuthenticated: s.isAuthenticated }) }
  )
);
