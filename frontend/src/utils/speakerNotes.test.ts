import { describe, it, expect } from 'vitest';
import { getSpeakerNotesCoverage } from './speakerNotes';

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
