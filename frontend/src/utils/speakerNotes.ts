/**
 * Speaker-notes coverage for slide-style materials ("Notes: N/M" badge).
 *
 * Mirrors the segmentation semantics of the backend slide splitter
 * (backend/app/services/slide_splitter.py): the document splits at
 * slideBreak nodes, speakerNotes nodes immediately after a break belong
 * to the previous slide, and empty segments don't count as slides.
 */

interface ContentNode {
  type?: string;
  content?: ContentNode[];
  text?: string;
}

export interface SpeakerNotesCoverage {
  slides: number;
  withNotes: number;
}

function nodeText(node: ContentNode): string {
  if (node.text) return node.text;
  return (node.content ?? []).map(nodeText).join('');
}

function hasNonEmptyNotes(segment: ContentNode[]): boolean {
  return segment.some(
    node => node.type === 'speakerNotes' && nodeText(node).trim() !== ''
  );
}

function hasContent(segment: ContentNode[]): boolean {
  return segment.some(
    node =>
      node.type !== 'speakerNotes' &&
      (nodeText(node).trim() !== '' || node.type !== 'paragraph')
  );
}

/**
 * Returns slide/notes counts, or null for non-slide materials
 * (documents without any slideBreak node).
 */
export function getSpeakerNotesCoverage(
  contentJson: Record<string, unknown> | undefined | null
): SpeakerNotesCoverage | null {
  const topContent = contentJson?.content;
  if (!Array.isArray(topContent)) return null;

  const nodes = topContent as ContentNode[];
  if (!nodes.some(node => node.type === 'slideBreak')) return null;

  // Split at slideBreak boundaries
  const segments: ContentNode[][] = [];
  let current: ContentNode[] = [];
  for (const node of nodes) {
    if (node.type === 'slideBreak') {
      segments.push(current);
      current = [];
    } else {
      current.push(node);
    }
  }
  segments.push(current);

  // Reattach leading speakerNotes to the previous segment (the editor's
  // natural cursor position after inserting a break), matching the splitter.
  for (let i = 1; i < segments.length; i++) {
    const segment = segments[i];
    if (!segment) continue;
    const leadingNotes: ContentNode[] = [];
    while (segment.length > 0 && segment[0]?.type === 'speakerNotes') {
      leadingNotes.push(segment.shift() as ContentNode);
    }
    if (leadingNotes.length > 0) {
      const previous = segments[i - 1];
      const previousHasContent = (previous ?? []).some(
        node => node.type !== 'speakerNotes'
      );
      if (previous && previousHasContent) {
        previous.push(...leadingNotes);
      } else {
        segment.unshift(...leadingNotes);
      }
    }
  }

  const slideSegments = segments.filter(segment => segment.length > 0);
  return {
    slides: slideSegments.filter(hasContent).length,
    withNotes: slideSegments.filter(
      segment => hasContent(segment) && hasNonEmptyNotes(segment)
    ).length,
  };
}
