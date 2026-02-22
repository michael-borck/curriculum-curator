import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface WorkingContextState {
  activeUnitId: string | null;
  activeUnitTitle: string | null;
  activeUnitCode: string | null;
  activeWeek: number | null;
  activeULOs: Array<{ code: string; description: string }>;
  activeDesignId: string | null;

  setActiveUnit: (unit: { id: string; title: string; code: string }) => void;
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
      activeWeek: null,
      activeULOs: [],
      activeDesignId: null,

      setActiveUnit: (unit: { id: string; title: string; code: string }) =>
        set({
          activeUnitId: unit.id,
          activeUnitTitle: unit.title,
          activeUnitCode: unit.code,
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
        activeWeek: state.activeWeek,
      }),
    }
  )
);
