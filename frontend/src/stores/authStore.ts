import { create } from 'zustand';
import type { User, AuthState } from '../types/index';
import api from '../services/api';
import { useTeachingStyleStore } from './teachingStyleStore';
import { useWorkingContextStore } from './workingContextStore';

interface ExtendedAuthState extends AuthState {
  isInitialized: boolean;
  isLoading: boolean;
  isLocalMode: boolean;
  initializeAuth: () => Promise<void>;
}

export const useAuthStore = create<ExtendedAuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isInitialized: false,
  isLoading: true,
  isLocalMode: false,

  login: (user: User) => set({ user, isAuthenticated: true }),

  logout: () => {
    // In local mode, logout is a no-op (nowhere to log out to)
    if (get().isLocalMode) return;

    // Clear token and persisted context from localStorage
    // Security note: token stored in localStorage is vulnerable to XSS.
    // TODO: migrate to httpOnly cookies for production hardening.
    localStorage.removeItem('token');
    useWorkingContextStore.getState().clearContext();
    set({ user: null, isAuthenticated: false });
  },

  initializeAuth: async () => {
    // Don't re-initialize if already done
    if (get().isInitialized) {
      return;
    }

    try {
      // Check if we're in local mode
      const configResponse = await api.get('/auth/config');
      if (configResponse.data?.localMode) {
        // Local mode: get a session automatically
        const sessionResponse = await api.get('/auth/local-session');
        if (sessionResponse.status === 200 && sessionResponse.data) {
          const { access_token, user } = sessionResponse.data;
          // Security note: storing JWT in localStorage — XSS risk accepted
          // for now. Future: migrate to httpOnly cookie-based auth.
          localStorage.setItem('token', access_token);
          set({
            user,
            isAuthenticated: true,
            isInitialized: true,
            isLoading: false,
            isLocalMode: true,
          });
          // Sync teaching style from user profile
          if (user.teachingPhilosophy) {
            useTeachingStyleStore
              .getState()
              .initFromUser(
                user.teachingPhilosophy,
                user.teachingPreferences?.aiAssistLevel
              );
          }
          return;
        }
      }
    } catch {
      // Config endpoint failed — not in local mode, continue normally
    }

    // Normal mode: check for existing token
    // Security note: token in localStorage is accessible to any JS on the page.
    // Future hardening: use httpOnly cookies instead.
    const token = localStorage.getItem('token');

    if (!token) {
      set({ isInitialized: true, isLoading: false });
      return;
    }

    try {
      // Validate token by fetching current user
      const response = await api.get('/auth/me');
      if (response.status === 200 && response.data) {
        set({
          user: response.data,
          isAuthenticated: true,
          isInitialized: true,
          isLoading: false,
        });
        // Sync teaching style from user profile
        if (response.data.teachingPhilosophy) {
          useTeachingStyleStore
            .getState()
            .initFromUser(
              response.data.teachingPhilosophy,
              response.data.teachingPreferences?.aiAssistLevel
            );
        }
      }
    } catch {
      // Token is invalid or expired - clear it
      // Security note: clearing localStorage token on auth failure
      localStorage.removeItem('token');
      useWorkingContextStore.getState().clearContext();
      set({
        user: null,
        isAuthenticated: false,
        isInitialized: true,
        isLoading: false,
      });
    }
  },
}));
