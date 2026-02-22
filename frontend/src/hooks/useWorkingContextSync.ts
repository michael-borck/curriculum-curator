import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useWorkingContextStore } from '../stores/workingContextStore';
import { useUnitsStore } from '../stores/unitsStore';

/**
 * Syncs the URL to the working context store.
 * When user navigates to /units/:unitId, the store is updated.
 * Navigating away does NOT clear context — only explicit user action does.
 */
export function useWorkingContextSync(): void {
  const pathname = useLocation().pathname;
  const units = useUnitsStore(s => s.units);
  const { activeUnitId, setActiveUnit, clearContext } =
    useWorkingContextStore();

  useEffect(() => {
    const match = pathname.match(/^\/units\/([^/]+)/);
    const urlUnitId = match?.[1];

    if (urlUnitId && urlUnitId !== 'new' && urlUnitId !== activeUnitId) {
      const unit = units.find(u => u.id === urlUnitId);
      if (unit) {
        setActiveUnit({ id: unit.id, title: unit.title, code: unit.code });
      }
    }
  }, [pathname, units, activeUnitId, setActiveUnit]);

  // Clear context if active unit no longer exists in units list
  useEffect(() => {
    if (activeUnitId && units.length > 0) {
      const stillExists = units.some(u => u.id === activeUnitId);
      if (!stillExists) {
        clearContext();
      }
    }
  }, [activeUnitId, units, clearContext]);
}
