import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { Unit } from '../types/index';
import { useUnitsStore } from './unitsStore';
import { getUnits } from '../services/api';

vi.mock('../services/api', () => ({
  getUnits: vi.fn(),
}));

const mockedGetUnits = vi.mocked(getUnits);

const makeUnit = (overrides: Partial<Unit> = {}): Unit => ({
  id: 'unit-1',
  title: 'Programming 101',
  code: 'COMP1001',
  year: 2026,
  semester: 'semester_1',
  status: 'active',
  pedagogyType: 'inquiry-based',
  difficultyLevel: 'intro',
  durationWeeks: 12,
  topicLabel: 'Week',
  unitLabel: 'Unit',
  creditPoints: 25,
  ownerId: 'user-1',
  createdById: 'user-1',
  createdAt: '2026-01-01',
  updatedAt: '2026-01-01',
  ...overrides,
});

describe('UnitsStore', () => {
  beforeEach(() => {
    useUnitsStore.setState({
      units: [],
      loading: false,
      error: null,
      lastFetched: null,
    });
    mockedGetUnits.mockReset();
  });

  describe('fetchUnits', () => {
    it('loads units from the API', async () => {
      const unit = makeUnit();
      mockedGetUnits.mockResolvedValue({
        data: { units: [unit], total: 1 },
      } as never);

      await useUnitsStore.getState().fetchUnits();

      const state = useUnitsStore.getState();
      expect(state.units).toEqual([unit]);
      expect(state.loading).toBe(false);
      expect(state.error).toBeNull();
      expect(state.lastFetched).not.toBeNull();
    });

    it('sets an error message when the API call fails', async () => {
      mockedGetUnits.mockRejectedValue(new Error('network down'));

      await useUnitsStore.getState().fetchUnits();

      const state = useUnitsStore.getState();
      expect(state.error).toBe('Failed to load units');
      expect(state.loading).toBe(false);
      expect(state.units).toEqual([]);
    });

    it('skips refetching within the 5-second cache window', async () => {
      mockedGetUnits.mockResolvedValue({
        data: { units: [makeUnit()], total: 1 },
      } as never);

      await useUnitsStore.getState().fetchUnits();
      await useUnitsStore.getState().fetchUnits();

      expect(mockedGetUnits).toHaveBeenCalledTimes(1);
    });

    it('refetches after invalidate() clears the cache', async () => {
      mockedGetUnits.mockResolvedValue({
        data: { units: [makeUnit()], total: 1 },
      } as never);

      await useUnitsStore.getState().fetchUnits();
      useUnitsStore.getState().invalidate();
      await useUnitsStore.getState().fetchUnits();

      expect(mockedGetUnits).toHaveBeenCalledTimes(2);
    });

    it('falls back to an empty list when the response has no units', async () => {
      mockedGetUnits.mockResolvedValue({ data: undefined } as never);

      await useUnitsStore.getState().fetchUnits();

      expect(useUnitsStore.getState().units).toEqual([]);
    });
  });

  describe('local mutations', () => {
    it('addUnit appends to the list', () => {
      const a = makeUnit({ id: 'a' });
      const b = makeUnit({ id: 'b' });

      useUnitsStore.getState().addUnit(a);
      useUnitsStore.getState().addUnit(b);

      expect(useUnitsStore.getState().units).toEqual([a, b]);
    });

    it('removeUnit drops only the matching unit', () => {
      useUnitsStore.setState({
        units: [makeUnit({ id: 'a' }), makeUnit({ id: 'b' })],
      });

      useUnitsStore.getState().removeUnit('a');

      expect(useUnitsStore.getState().units.map(u => u.id)).toEqual(['b']);
    });

    it('updateUnit merges partial updates into the matching unit', () => {
      useUnitsStore.setState({
        units: [makeUnit({ id: 'a', title: 'Old' }), makeUnit({ id: 'b' })],
      });

      useUnitsStore.getState().updateUnit('a', { title: 'New' });

      const units = useUnitsStore.getState().units;
      expect(units[0]?.title).toBe('New');
      expect(units[0]?.code).toBe('COMP1001');
      expect(units[1]?.title).toBe('Programming 101');
    });
  });
});
