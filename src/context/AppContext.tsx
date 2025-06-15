import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { ContentRequest, GeneratedContent, Session, LLMProvider, UISettings } from '../types';

type AppMode = 'wizard' | 'expert';

// App state interface
interface AppState {
  currentMode: AppMode;
  session: Session | null;
  contentRequest: ContentRequest | null;
  generatedContent: GeneratedContent[];
  availableProviders: LLMProvider[];
  activeProvider: LLMProvider | null;
  uiSettings: UISettings;
  isGenerating: boolean;
  lastError: string | null;
}

// Action types
type AppAction =
  | { type: 'SET_MODE'; payload: AppMode }
  | { type: 'SET_SESSION'; payload: Session | null }
  | { type: 'SET_CONTENT_REQUEST'; payload: ContentRequest }
  | { type: 'SET_GENERATED_CONTENT'; payload: GeneratedContent[] }
  | { type: 'ADD_GENERATED_CONTENT'; payload: GeneratedContent }
  | { type: 'SET_PROVIDERS'; payload: LLMProvider[] }
  | { type: 'SET_ACTIVE_PROVIDER'; payload: LLMProvider }
  | { type: 'UPDATE_UI_SETTINGS'; payload: Partial<UISettings> }
  | { type: 'SET_GENERATING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ERROR' };

// Initial state
const initialState: AppState = {
  currentMode: 'wizard',
  session: null,
  contentRequest: null,
  generatedContent: [],
  availableProviders: [],
  activeProvider: null,
  uiSettings: {
    mode: 'wizard',
    theme: 'system',
    fontSize: 'medium',
    showAdvancedOptions: false,
  },
  isGenerating: false,
  lastError: null,
};

// Reducer function
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_MODE':
      return {
        ...state,
        currentMode: action.payload,
        uiSettings: {
          ...state.uiSettings,
          mode: action.payload,
        },
      };
    case 'SET_SESSION':
      return {
        ...state,
        session: action.payload,
      };
    case 'SET_CONTENT_REQUEST':
      return {
        ...state,
        contentRequest: action.payload,
      };
    case 'SET_GENERATED_CONTENT':
      return {
        ...state,
        generatedContent: action.payload,
      };
    case 'ADD_GENERATED_CONTENT':
      return {
        ...state,
        generatedContent: [...state.generatedContent, action.payload],
      };
    case 'SET_PROVIDERS':
      return {
        ...state,
        availableProviders: action.payload,
      };
    case 'SET_ACTIVE_PROVIDER':
      return {
        ...state,
        activeProvider: action.payload,
      };
    case 'UPDATE_UI_SETTINGS':
      return {
        ...state,
        uiSettings: {
          ...state.uiSettings,
          ...action.payload,
        },
      };
    case 'SET_GENERATING':
      return {
        ...state,
        isGenerating: action.payload,
      };
    case 'SET_ERROR':
      return {
        ...state,
        lastError: action.payload,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        lastError: null,
      };
    default:
      return state;
  }
}

// Context interface
interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  // Helper functions
  setMode: (mode: AppMode) => void;
  setSession: (session: Session | null) => void;
  setContentRequest: (request: ContentRequest) => void;
  addGeneratedContent: (content: GeneratedContent) => void;
  setActiveProvider: (provider: LLMProvider) => void;
  updateUISettings: (settings: Partial<UISettings>) => void;
  setGenerating: (generating: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

// Create context
const AppContext = createContext<AppContextType | undefined>(undefined);

// Context provider component
interface AppProviderProps {
  children: ReactNode;
}

export function AppProvider({ children }: AppProviderProps) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Helper functions for common actions
  const setMode = (mode: AppMode) => {
    dispatch({ type: 'SET_MODE', payload: mode });
  };

  const setSession = (session: Session | null) => {
    dispatch({ type: 'SET_SESSION', payload: session });
  };

  const setContentRequest = (request: ContentRequest) => {
    dispatch({ type: 'SET_CONTENT_REQUEST', payload: request });
  };

  const addGeneratedContent = (content: GeneratedContent) => {
    dispatch({ type: 'ADD_GENERATED_CONTENT', payload: content });
  };

  const setActiveProvider = (provider: LLMProvider) => {
    dispatch({ type: 'SET_ACTIVE_PROVIDER', payload: provider });
  };

  const updateUISettings = (settings: Partial<UISettings>) => {
    dispatch({ type: 'UPDATE_UI_SETTINGS', payload: settings });
  };

  const setGenerating = (generating: boolean) => {
    dispatch({ type: 'SET_GENERATING', payload: generating });
  };

  const setError = (error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const contextValue: AppContextType = {
    state,
    dispatch,
    setMode,
    setSession,
    setContentRequest,
    addGeneratedContent,
    setActiveProvider,
    updateUISettings,
    setGenerating,
    setError,
    clearError,
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
}

// Hook for using the app context
export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}