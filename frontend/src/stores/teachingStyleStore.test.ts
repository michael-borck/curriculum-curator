import { describe, it, expect, beforeEach } from 'vitest';
import {
  useTeachingStyleStore,
  pedagogyOptions,
  getPedagogyHint,
  getPedagogyStaticGuidance,
} from './teachingStyleStore';

describe('TeachingStyleStore', () => {
  beforeEach(() => {
    useTeachingStyleStore.setState({
      globalStyle: 'inquiry-based',
      isSet: false,
      aiAssistLevel: 'create',
    });
  });

  it('initializes with inquiry-based default and isSet false', () => {
    const state = useTeachingStyleStore.getState();
    expect(state.globalStyle).toBe('inquiry-based');
    expect(state.isSet).toBe(false);
    expect(state.aiAssistLevel).toBe('create');
  });

  it('setGlobalStyle updates the style and marks it as set', () => {
    useTeachingStyleStore.getState().setGlobalStyle('project-based');

    const state = useTeachingStyleStore.getState();
    expect(state.globalStyle).toBe('project-based');
    expect(state.isSet).toBe(true);
  });

  it('setAIAssistLevel updates the assist level only', () => {
    useTeachingStyleStore.getState().setAIAssistLevel('refine');

    const state = useTeachingStyleStore.getState();
    expect(state.aiAssistLevel).toBe('refine');
    expect(state.isSet).toBe(false);
  });

  describe('initFromUser', () => {
    it('applies a teaching philosophy from the user profile', () => {
      useTeachingStyleStore.getState().initFromUser('collaborative');

      const state = useTeachingStyleStore.getState();
      expect(state.globalStyle).toBe('collaborative');
      expect(state.isSet).toBe(true);
    });

    it('applies both philosophy and assist level when provided', () => {
      useTeachingStyleStore.getState().initFromUser('traditional', 'refine');

      const state = useTeachingStyleStore.getState();
      expect(state.globalStyle).toBe('traditional');
      expect(state.aiAssistLevel).toBe('refine');
    });

    it('leaves state untouched when nothing is provided', () => {
      useTeachingStyleStore.getState().initFromUser(undefined);

      const state = useTeachingStyleStore.getState();
      expect(state.globalStyle).toBe('inquiry-based');
      expect(state.isSet).toBe(false);
      expect(state.aiAssistLevel).toBe('create');
    });
  });

  describe('pedagogy helpers', () => {
    it('exposes nine pedagogy options with unique ids', () => {
      expect(pedagogyOptions).toHaveLength(9);
      const ids = pedagogyOptions.map(o => o.id);
      expect(new Set(ids).size).toBe(9);
    });

    it('returns a hint for every pedagogy option', () => {
      for (const option of pedagogyOptions) {
        expect(getPedagogyHint(option.id)).not.toBe('');
      }
    });

    it('returns static guidance for every pedagogy option', () => {
      for (const option of pedagogyOptions) {
        expect(getPedagogyStaticGuidance(option.id).length).toBeGreaterThan(0);
      }
    });
  });
});
