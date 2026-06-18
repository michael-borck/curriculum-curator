import { describe, it, expect } from 'vitest';
import { isPlainParagraphContent, estimateTokens } from './contentStructure';

const para = (text: string) => ({
  type: 'paragraph',
  content: [{ type: 'text', text }],
});

const doc = (...content: object[]) => ({ type: 'doc', content });

describe('isPlainParagraphContent', () => {
  it('is true for two or more plain paragraphs', () => {
    expect(isPlainParagraphContent(doc(para('a'), para('b')))).toBe(true);
  });

  it('is false for a single paragraph', () => {
    expect(isPlainParagraphContent(doc(para('only one')))).toBe(false);
  });

  it('is false when a heading is present', () => {
    expect(
      isPlainParagraphContent(
        doc({ type: 'heading', attrs: { level: 1 } }, para('body'))
      )
    ).toBe(false);
  });

  it('is false when a list is present', () => {
    expect(
      isPlainParagraphContent(doc(para('intro'), { type: 'bulletList' }))
    ).toBe(false);
  });

  it('is false for slide and quiz materials', () => {
    expect(
      isPlainParagraphContent(doc(para('a'), { type: 'slideBreak' }))
    ).toBe(false);
  });

  it('is false for missing or malformed content', () => {
    expect(isPlainParagraphContent(undefined)).toBe(false);
    expect(isPlainParagraphContent({})).toBe(false);
  });
});

describe('estimateTokens', () => {
  it('estimates roughly 4 characters per token', () => {
    // "aaaaaaaa" = 8 chars → 2 tokens
    expect(estimateTokens(doc(para('aaaaaaaa')))).toBe(2);
  });

  it('returns 0 for empty content', () => {
    expect(estimateTokens(undefined)).toBe(0);
  });
});
