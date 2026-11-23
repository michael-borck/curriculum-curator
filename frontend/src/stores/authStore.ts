import { create } from 'zustand';
import type { User, AuthState } from '../types/index';
import api from '../services/api';
import {
  clearStoredToken,
  getStoredToken,
  isDesktopClient,
  setStoredToken,
} from '../services/authSession';
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

    // Ask the server to revoke this token/cookie before dropping it locally.
    // Fire-and-forget: local state clears even if the call fails.
    api.post('/auth/logout').catch(() => undefined);

    clearStoredToken();
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
          // Desktop stores the token; web relies on the httpOnly cookie.
          setStoredToken(access_token);
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

    // Normal mode: desktop needs a stored token; web authenticates by cookie.
    const token = getStoredToken();

    if (!token && isDesktopClient()) {
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
      } else {
        set({
          user: null,
          isAuthenticated: false,
          isInitialized: true,
          isLoading: false,
        });
      }
    } catch {
      // Token/cookie is invalid or expired - clear local state.
      clearStoredToken();
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
