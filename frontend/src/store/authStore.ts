import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '../services/api';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        const response = await api.post('/api/v1/auth/login', { email, password });
        const { access_token, user } = response.data;
        set({ token: access_token, user, isAuthenticated: true });
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false });
        delete api.defaults.headers.common['Authorization'];
      },
    }),
    { name: 'auth-storage' }
  )
);
