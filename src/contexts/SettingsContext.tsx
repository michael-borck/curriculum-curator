// Settings Context for React State Management

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import type { UserSettings, UserProfile, ContentDefaults, UIPreferences } from '../types/settings';
import { settingsStorage } from '../utils/settingsStorage';

// Context State
interface SettingsState {
  settings: UserSettings | null;
  isLoading: boolean;
  error: string | null;
  isInitialized: boolean;
}

// Context Actions
type SettingsAction = 
  | { type: 'SETTINGS_LOADING' }
  | { type: 'SETTINGS_LOADED'; payload: UserSettings }
  | { type: 'SETTINGS_ERROR'; payload: string }
  | { type: 'UPDATE_PROFILE'; payload: Partial<UserProfile> }
  | { type: 'UPDATE_DEFAULTS'; payload: Partial<ContentDefaults> }
  | { type: 'UPDATE_PREFERENCES'; payload: Partial<UIPreferences> }
  | { type: 'RESET_SETTINGS' }
  | { type: 'INITIALIZE_SETTINGS'; payload: UserSettings };

// Context Interface
interface SettingsContextType {
  state: SettingsState;
  actions: {
    loadSettings: () => Promise<void>;
    saveSettings: (settings: UserSettings) => Promise<boolean>;
    updateProfile: (profile: Partial<UserProfile>) => Promise<boolean>;
    updateDefaults: (defaults: Partial<ContentDefaults>) => Promise<boolean>;
    updatePreferences: (preferences: Partial<UIPreferences>) => Promise<boolean>;
    resetSettings: () => Promise<boolean>;
    createUserProfile: (profile: Partial<UserProfile>) => Promise<boolean>;
    exportSettings: () => string;
    importSettings: (settingsJson: string) => Promise<boolean>;
  };
}

// Initial State
const initialState: SettingsState = {
  settings: null,
  isLoading: false,
  error: null,
  isInitialized: false
};

// Reducer
function settingsReducer(state: SettingsState, action: SettingsAction): SettingsState {
  switch (action.type) {
    case 'SETTINGS_LOADING':
      return {
        ...state,
        isLoading: true,
        error: null
      };

    case 'SETTINGS_LOADED':
      return {
        ...state,
        settings: action.payload,
        isLoading: false,
        error: null,
        isInitialized: true
      };

    case 'SETTINGS_ERROR':
      return {
        ...state,
        isLoading: false,
        error: action.payload
      };

    case 'INITIALIZE_SETTINGS':
      return {
        ...state,
        settings: action.payload,
        isLoading: false,
        error: null,
        isInitialized: true
      };

    case 'UPDATE_PROFILE':
      if (!state.settings) return state;
      return {
        ...state,
        settings: {
          ...state.settings,
          profile: {
            ...state.settings.profile,
            ...action.payload,
            updatedAt: new Date()
          }
        }
      };

    case 'UPDATE_DEFAULTS':
      if (!state.settings) return state;
      return {
        ...state,
        settings: {
          ...state.settings,
          defaults: {
            ...state.settings.defaults,
            ...action.payload
          }
        }
      };

    case 'UPDATE_PREFERENCES':
      if (!state.settings) return state;
      return {
        ...state,
        settings: {
          ...state.settings,
          preferences: {
            ...state.settings.preferences,
            ...action.payload
          }
        }
      };

    case 'RESET_SETTINGS':
      return {
        ...initialState,
        isInitialized: true
      };

    default:
      return state;
  }
}

// Create Context
const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

// Provider Component
interface SettingsProviderProps {
  children: ReactNode;
}

export function SettingsProvider({ children }: SettingsProviderProps) {
  const [state, dispatch] = useReducer(settingsReducer, initialState);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  // Auto-save when settings change (if auto-save is enabled)
  useEffect(() => {
    if (state.settings && state.isInitialized && state.settings.preferences.autoSaveSettings) {
      const timeoutId = setTimeout(() => {
        settingsStorage.saveSettings(state.settings);
      }, 1000); // Debounce saves

      return () => clearTimeout(timeoutId);
    }
  }, [state.settings, state.isInitialized]);

  // Actions
  const loadSettings = async (): Promise<void> => {
    dispatch({ type: 'SETTINGS_LOADING' });
    
    try {
      const settings = settingsStorage.loadSettings();
      
      if (settings) {
        dispatch({ type: 'SETTINGS_LOADED', payload: settings });
      } else {
        // Create default settings for first-time user
        const defaultSettings = settingsStorage.createDefaultSettings();
        dispatch({ type: 'INITIALIZE_SETTINGS', payload: defaultSettings });
      }
    } catch (error) {
      dispatch({ type: 'SETTINGS_ERROR', payload: 'Failed to load settings' });
    }
  };

  const saveSettings = async (settings: UserSettings): Promise<boolean> => {
    try {
      const success = settingsStorage.saveSettings(settings);
      if (success) {
        dispatch({ type: 'SETTINGS_LOADED', payload: settings });
      }
      return success;
    } catch (error) {
      dispatch({ type: 'SETTINGS_ERROR', payload: 'Failed to save settings' });
      return false;
    }
  };

  const updateProfile = async (profile: Partial<UserProfile>): Promise<boolean> => {
    if (!state.settings) return false;

    try {
      dispatch({ type: 'UPDATE_PROFILE', payload: profile });
      
      // Save to storage if auto-save is disabled
      if (!state.settings.preferences.autoSaveSettings) {
        const updatedSettings = {
          ...state.settings,
          profile: { ...state.settings.profile, ...profile, updatedAt: new Date() }
        };
        return settingsStorage.saveSettings(updatedSettings);
      }
      
      return true;
    } catch (error) {
      dispatch({ type: 'SETTINGS_ERROR', payload: 'Failed to update profile' });
      return false;
    }
  };

  const updateDefaults = async (defaults: Partial<ContentDefaults>): Promise<boolean> => {
    if (!state.settings) return false;

    try {
      dispatch({ type: 'UPDATE_DEFAULTS', payload: defaults });
      
      if (!state.settings.preferences.autoSaveSettings) {
        const updatedSettings = {
          ...state.settings,
          defaults: { ...state.settings.defaults, ...defaults }
        };
        return settingsStorage.saveSettings(updatedSettings);
      }
      
      return true;
    } catch (error) {
      dispatch({ type: 'SETTINGS_ERROR', payload: 'Failed to update defaults' });
      return false;
    }
  };

  const updatePreferences = async (preferences: Partial<UIPreferences>): Promise<boolean> => {
    if (!state.settings) return false;

    try {
      dispatch({ type: 'UPDATE_PREFERENCES', payload: preferences });
      
      if (!state.settings.preferences.autoSaveSettings) {
        const updatedSettings = {
          ...state.settings,
          preferences: { ...state.settings.preferences, ...preferences }
        };
        return settingsStorage.saveSettings(updatedSettings);
      }
      
      return true;
    } catch (error) {
      dispatch({ type: 'SETTINGS_ERROR', payload: 'Failed to update preferences' });
      return false;
    }
  };

  const resetSettings = async (): Promise<boolean> => {
    try {
      const success = settingsStorage.clearSettings();
      if (success) {
        dispatch({ type: 'RESET_SETTINGS' });
        // Reload default settings
        const defaultSettings = settingsStorage.createDefaultSettings();
        dispatch({ type: 'INITIALIZE_SETTINGS', payload: defaultSettings });
      }
      return success;
    } catch (error) {
      dispatch({ type: 'SETTINGS_ERROR', payload: 'Failed to reset settings' });
      return false;
    }
  };

  const createUserProfile = async (profile: Partial<UserProfile>): Promise<boolean> => {
    try {
      const defaultSettings = settingsStorage.createDefaultSettings(profile);
      const success = settingsStorage.saveSettings(defaultSettings);
      
      if (success) {
        dispatch({ type: 'SETTINGS_LOADED', payload: defaultSettings });
      }
      
      return success;
    } catch (error) {
      dispatch({ type: 'SETTINGS_ERROR', payload: 'Failed to create user profile' });
      return false;
    }
  };

  const exportSettings = (): string => {
    return settingsStorage.exportSettings();
  };

  const importSettings = async (settingsJson: string): Promise<boolean> => {
    try {
      const success = settingsStorage.importSettings(settingsJson);
      
      if (success) {
        // Reload settings
        await loadSettings();
      }
      
      return success;
    } catch (error) {
      dispatch({ type: 'SETTINGS_ERROR', payload: 'Failed to import settings' });
      return false;
    }
  };

  const contextValue: SettingsContextType = {
    state,
    actions: {
      loadSettings,
      saveSettings,
      updateProfile,
      updateDefaults,
      updatePreferences,
      resetSettings,
      createUserProfile,
      exportSettings,
      importSettings
    }
  };

  return (
    <SettingsContext.Provider value={contextValue}>
      {children}
    </SettingsContext.Provider>
  );
}

// Hook to use settings context
export function useSettings(): SettingsContextType {
  const context = useContext(SettingsContext);
  
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  
  return context;
}

// Helper hooks for specific parts of settings
export function useUserProfile(): [UserProfile | null, (profile: Partial<UserProfile>) => Promise<boolean>] {
  const { state, actions } = useSettings();
  return [state.settings?.profile || null, actions.updateProfile];
}

export function useContentDefaults(): [ContentDefaults | null, (defaults: Partial<ContentDefaults>) => Promise<boolean>] {
  const { state, actions } = useSettings();
  return [state.settings?.defaults || null, actions.updateDefaults];
}

export function useUIPreferences(): [UIPreferences | null, (prefs: Partial<UIPreferences>) => Promise<boolean>] {
  const { state, actions } = useSettings();
  return [state.settings?.preferences || null, actions.updatePreferences];
}