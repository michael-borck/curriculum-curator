import { useTeachingStyleStore } from '../stores/teachingStyleStore';
import type { AIAssistLevel } from '../types/index';

interface UseAILevelReturn {
  level: AIAssistLevel;
  isAIDisabled: boolean;
  canGenerate: boolean;
  canRefine: boolean;
  canChat: boolean;
  canScaffold: boolean;
}

export const useAILevel = (): UseAILevelReturn => {
  const level = useTeachingStyleStore(state => state.aiAssistLevel);

  return {
    level,
    isAIDisabled: level === 'none',
    canGenerate: level === 'create',
    canRefine: level === 'refine' || level === 'create',
    canChat: level === 'create',
    canScaffold: level === 'create',
  };
};
