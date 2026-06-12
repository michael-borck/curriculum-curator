import { describe, it, expect, beforeEach } from 'vitest';
import { useWorkingContextStore } from './workingContextStore';

describe('WorkingContextStore', () => {
  beforeEach(() => {
    useWorkingContextStore.getState().clearContext();
  });

  it('initializes with an empty context', () => {
    const state = useWorkingContextStore.getState();

    expect(state.activeUnitId).toBeNull();
    expect(state.activeUnitTitle).toBeNull();
    expect(state.activeWeek).toBeNull();
    expect(state.activeULOs).toEqual([]);
    expect(state.activeDesignId).toBeNull();
  });

  it('setActiveUnit stores unit identity and applies label defaults', () => {
    useWorkingContextStore.getState().setActiveUnit({
      id: 'u1',
      title: 'Programming 101',
      code: 'COMP1001',
    });

    const state = useWorkingContextStore.getState();
    expect(state.activeUnitId).toBe('u1');
    expect(state.activeUnitTitle).toBe('Programming 101');
    expect(state.activeUnitCode).toBe('COMP1001');
    expect(state.activeTopicLabel).toBe('Week');
    expect(state.activeUnitLabel).toBe('Learning Program');
  });

  it('setActiveUnit honours custom labels', () => {
    useWorkingContextStore.getState().setActiveUnit({
      id: 'u1',
      title: 'Programming 101',
      code: 'COMP1001',
      topicLabel: 'Module',
      unitLabel: 'Subject',
    });

    const state = useWorkingContextStore.getState();
    expect(state.activeTopicLabel).toBe('Module');
    expect(state.activeUnitLabel).toBe('Subject');
  });

  it('setActiveUnit resets week, ULOs, and design from a previous unit', () => {
    const store = useWorkingContextStore.getState();
    store.setActiveUnit({ id: 'u1', title: 'A', code: 'A100' });
    store.setActiveWeek(5);
    store.setUnitDetails({
      ulos: [{ code: 'ULO1', description: 'Explain things' }],
      designId: 'd1',
    });

    useWorkingContextStore
      .getState()
      .setActiveUnit({ id: 'u2', title: 'B', code: 'B100' });

    const state = useWorkingContextStore.getState();
    expect(state.activeUnitId).toBe('u2');
    expect(state.activeWeek).toBeNull();
    expect(state.activeULOs).toEqual([]);
    expect(state.activeDesignId).toBeNull();
  });

  it('setUnitDetails updates only the provided fields', () => {
    const store = useWorkingContextStore.getState();
    store.setActiveUnit({ id: 'u1', title: 'A', code: 'A100' });
    store.setUnitDetails({
      ulos: [{ code: 'ULO1', description: 'Explain things' }],
      designId: 'd1',
    });

    useWorkingContextStore.getState().setUnitDetails({ designId: 'd2' });

    const state = useWorkingContextStore.getState();
    expect(state.activeDesignId).toBe('d2');
    expect(state.activeULOs).toEqual([
      { code: 'ULO1', description: 'Explain things' },
    ]);
    expect(state.activeUnitId).toBe('u1');
  });

  it('setActiveWeek sets and clears the active week', () => {
    useWorkingContextStore.getState().setActiveWeek(3);
    expect(useWorkingContextStore.getState().activeWeek).toBe(3);

    useWorkingContextStore.getState().setActiveWeek(null);
    expect(useWorkingContextStore.getState().activeWeek).toBeNull();
  });

  it('clearContext resets everything', () => {
    const store = useWorkingContextStore.getState();
    store.setActiveUnit({ id: 'u1', title: 'A', code: 'A100' });
    store.setActiveWeek(2);
    store.setUnitDetails({
      ulos: [{ code: 'ULO1', description: 'x' }],
      designId: 'd1',
    });

    useWorkingContextStore.getState().clearContext();

    const state = useWorkingContextStore.getState();
    expect(state.activeUnitId).toBeNull();
    expect(state.activeUnitTitle).toBeNull();
    expect(state.activeUnitCode).toBeNull();
    expect(state.activeWeek).toBeNull();
    expect(state.activeULOs).toEqual([]);
    expect(state.activeDesignId).toBeNull();
  });
});
