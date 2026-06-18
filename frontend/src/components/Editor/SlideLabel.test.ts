import { describe, it, expect } from 'vitest';
import { computeSlideLabels, type SlideLabelNode } from './SlideLabel';

const heading = (text: string): SlideLabelNode => ({ type: 'heading', text });
const para = (): SlideLabelNode => ({ type: 'paragraph', text: '' });
const brk = (): SlideLabelNode => ({ type: 'slideBreak', text: '' });

describe('computeSlideLabels', () => {
  it('labels each break with the following slide number and title', () => {
    const nodes = [
      heading('Intro'),
      para(),
      brk(),
      heading('Base cases'),
      para(),
      brk(),
      heading('Recursive cases'),
    ];
    const labels = computeSlideLabels(nodes);
    // breaks are at indices 2 and 5
    expect(labels.get(2)).toBe('Slide 2 — Base cases');
    expect(labels.get(5)).toBe('Slide 3 — Recursive cases');
    // no label on non-break nodes
    expect(labels.has(0)).toBe(false);
  });

  it('falls back to just the slide number when a slide has no heading', () => {
    const nodes = [heading('Intro'), brk(), para(), para()];
    const labels = computeSlideLabels(nodes);
    expect(labels.get(1)).toBe('Slide 2');
  });

  it('uses the first heading when a slide has several', () => {
    const nodes = [brk(), heading('First'), heading('Second')];
    const labels = computeSlideLabels(nodes);
    expect(labels.get(0)).toBe('Slide 2 — First');
  });

  it('returns no labels for a document without slide breaks', () => {
    const labels = computeSlideLabels([heading('A'), para()]);
    expect(labels.size).toBe(0);
  });
});
