import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface WorkingContextState {
  activeUnitId: string | null;
  activeUnitTitle: string | null;
  activeUnitCode: string | null;
  activeTopicLabel: string | null;
  activeWeek: number | null;
  activeULOs: Array<{ code: string; description: string }>;
  activeDesignId: string | null;

  setActiveUnit: (unit: {
    id: string;
    title: string;
    code: string;
    topicLabel?: string | undefined;
  }) => void;
  setUnitDetails: (details: {
    ulos?: Array<{ code: string; description: string }> | undefined;
    designId?: string | null | undefined;
  }) => void;
  setActiveWeek: (week: number | null) => void;
  clearContext: () => void;
}

export const useWorkingContextStore = create<WorkingContextState>()(
  persist(
    set => ({
      activeUnitId: null,
      activeUnitTitle: null,
      activeUnitCode: null,
      activeTopicLabel: null,
      activeWeek: null,
      activeULOs: [],
      activeDesignId: null,

      setActiveUnit: (unit: {
        id: string;
        title: string;
        code: string;
        topicLabel?: string | undefined;
      }) =>
        set({
          activeUnitId: unit.id,
          activeUnitTitle: unit.title,
          activeUnitCode: unit.code,
          activeTopicLabel: unit.topicLabel || 'Week',
          activeWeek: null,
          activeULOs: [],
          activeDesignId: null,
        }),

      setUnitDetails: (details: {
        ulos?: Array<{ code: string; description: string }> | undefined;
        designId?: string | null | undefined;
      }) =>
        set(state => ({
          ...(details.ulos !== undefined ? { activeULOs: details.ulos } : {}),
          ...(details.designId !== undefined
            ? { activeDesignId: details.designId }
            : {}),
          // Keep other state unchanged
          activeUnitId: state.activeUnitId,
        })),

      setActiveWeek: (week: number | null) => set({ activeWeek: week }),

      clearContext: () =>
        set({
          activeUnitId: null,
          activeUnitTitle: null,
          activeUnitCode: null,
          activeTopicLabel: null,
          activeWeek: null,
          activeULOs: [],
          activeDesignId: null,
        }),
    }),
    {
      name: 'working-context-storage',
      partialize: state => ({
        activeUnitId: state.activeUnitId,
        activeUnitTitle: state.activeUnitTitle,
        activeUnitCode: state.activeUnitCode,
        activeTopicLabel: state.activeTopicLabel,
        activeWeek: state.activeWeek,
      }),
    }
  )
);
