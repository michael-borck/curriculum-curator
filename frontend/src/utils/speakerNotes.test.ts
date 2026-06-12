import { describe, it, expect } from 'vitest';
import {
  applySpeakerNotesDrafts,
  getSlideSegments,
  getSpeakerNotesCoverage,
} from './speakerNotes';

const paragraph = (text: string) => ({
  type: 'paragraph',
  content: text ? [{ type: 'text', text }] : [],
});

const notes = (text: string) => ({
  type: 'speakerNotes',
  content: [paragraph(text)],
});

const slideBreak = () => ({ type: 'slideBreak' });

const doc = (...content: object[]) => ({ type: 'doc', content });

describe('getSpeakerNotesCoverage', () => {
  it('returns null for non-slide documents', () => {
    expect(getSpeakerNotesCoverage(doc(paragraph('Just prose')))).toBeNull();
    expect(getSpeakerNotesCoverage(undefined)).toBeNull();
    expect(getSpeakerNotesCoverage({})).toBeNull();
  });

  it('counts slides and slides with notes', () => {
    const coverage = getSpeakerNotesCoverage(
      doc(
        paragraph('Slide one'),
        notes('Say hello'),
        slideBreak(),
        paragraph('Slide two'),
        slideBreak(),
        paragraph('Slide three'),
        notes('Wrap up')
      )
    );
    expect(coverage).toEqual({ slides: 3, withNotes: 2 });
  });

  it('treats empty notes blocks as no notes', () => {
    const coverage = getSpeakerNotesCoverage(
      doc(paragraph('Slide one'), notes(''), slideBreak(), paragraph('Two'))
    );
    expect(coverage).toEqual({ slides: 2, withNotes: 0 });
  });

  it('attaches notes placed right after a break to the previous slide', () => {
    const coverage = getSpeakerNotesCoverage(
      doc(
        paragraph('Slide one'),
        slideBreak(),
        notes('These describe slide one'),
        paragraph('Slide two')
      )
    );
    expect(coverage).toEqual({ slides: 2, withNotes: 1 });
  });

  it('ignores empty segments from leading or trailing breaks', () => {
    const coverage = getSpeakerNotesCoverage(
      doc(slideBreak(), paragraph('Only real slide'), slideBreak())
    );
    expect(coverage).toEqual({ slides: 1, withNotes: 0 });
  });
});

describe('getSlideSegments', () => {
  it('exposes notes text, node index, and aiSelected per slide', () => {
    const segments = getSlideSegments(
      doc(
        paragraph('Slide one'),
        {
          type: 'speakerNotes',
          attrs: { aiSelected: false },
          content: [paragraph('opted out')],
        },
        slideBreak(),
        paragraph('Slide two')
      )
    );
    expect(segments).toHaveLength(2);
    expect(segments?.[0]).toMatchObject({
      notesText: 'opted out',
      notesNodeIndex: 1,
      aiSelected: false,
    });
    expect(segments?.[1]).toMatchObject({
      notesText: '',
      notesNodeIndex: null,
      aiSelected: true,
    });
  });
});

describe('applySpeakerNotesDrafts', () => {
  it('inserts a new notes node at the end of a slide without notes', () => {
    const input = doc(
      paragraph('Slide one'),
      slideBreak(),
      paragraph('Slide two')
    );
    const result = applySpeakerNotesDrafts(input, [
      { slideIndex: 0, notes: 'Say hello' },
    ]);

    const types = (result.content as { type: string }[]).map(n => n.type);
    expect(types).toEqual([
      'paragraph',
      'speakerNotes',
      'slideBreak',
      'paragraph',
    ]);
    expect(getSpeakerNotesCoverage(result)).toEqual({
      slides: 2,
      withNotes: 1,
    });
  });

  it('replaces the content of an existing notes node, keeping attrs', () => {
    const input = doc(
      paragraph('Slide one'),
      {
        type: 'speakerNotes',
        attrs: { aiSelected: false },
        content: [paragraph('old notes')],
      },
      slideBreak(),
      paragraph('Slide two')
    );
    const result = applySpeakerNotesDrafts(input, [
      { slideIndex: 0, notes: 'new draft notes' },
    ]);

    const segments = getSlideSegments(result);
    expect(segments?.[0]?.notesText).toBe('new draft notes');
    expect(segments?.[0]?.aiSelected).toBe(false);
    // Document length unchanged — replaced, not inserted
    expect((result.content as unknown[]).length).toBe(
      (input.content as unknown[]).length
    );
  });

  it('applies multiple drafts without corrupting indices', () => {
    const input = doc(
      paragraph('One'),
      slideBreak(),
      paragraph('Two'),
      slideBreak(),
      paragraph('Three')
    );
    const result = applySpeakerNotesDrafts(input, [
      { slideIndex: 0, notes: 'notes one' },
      { slideIndex: 2, notes: 'notes three' },
    ]);

    const segments = getSlideSegments(result);
    expect(segments?.map(s => s.notesText)).toEqual([
      'notes one',
      '',
      'notes three',
    ]);
  });

  it('does not mutate the input document', () => {
    const input = doc(paragraph('One'), slideBreak(), paragraph('Two'));
    const snapshot = JSON.stringify(input);
    applySpeakerNotesDrafts(input, [{ slideIndex: 1, notes: 'x' }]);
    expect(JSON.stringify(input)).toBe(snapshot);
  });
});
