import { create } from 'zustand';
import type { User, AuthState } from '../types/index';

export const useAuthStore = create<AuthState>(set => ({
  user: null,
  isAuthenticated: false,
  login: (user: User) => set({ user, isAuthenticated: true }),
  logout: () => set({ user: null, isAuthenticated: false }),
}));
