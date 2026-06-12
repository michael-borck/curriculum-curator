/**
 * Speaker-notes helpers for slide-style materials.
 *
 * Mirrors the segmentation semantics of the backend slide splitter
 * (backend/app/services/slide_splitter.py): the document splits at
 * slideBreak nodes, speakerNotes nodes immediately after a break belong
 * to the previous slide, and empty segments don't count as slides.
 * Slide indices produced here line up with the indices the
 * generate-speaker-notes endpoint uses.
 */

interface ContentNode {
  type?: string;
  attrs?: Record<string, unknown>;
  content?: ContentNode[];
  text?: string;
}

export interface SpeakerNotesCoverage {
  slides: number;
  withNotes: number;
}

export interface SlideSegment {
  /** Top-level node indices belonging to this slide, in document order */
  nodeIndices: number[];
  /** Plain text of the slide content, excluding speaker notes */
  text: string;
  /** Plain text of the slide's existing notes ('' when none) */
  notesText: string;
  /** Top-level index of the slide's speakerNotes node, if present */
  notesNodeIndex: number | null;
  /** aiSelected attr of the notes node (default true; true when no node) */
  aiSelected: boolean;
}

function nodeText(node: ContentNode): string {
  if (node.text) return node.text;
  return (node.content ?? []).map(nodeText).join(' ');
}

function segmentHasContent(nodes: ContentNode[]): boolean {
  return nodes.some(
    node =>
      node.type !== 'speakerNotes' &&
      (nodeText(node).trim() !== '' || node.type !== 'paragraph')
  );
}

/**
 * Split a TipTap document into slide segments, or return null for
 * non-slide documents (no slideBreak nodes).
 */
export function getSlideSegments(
  contentJson: Record<string, unknown> | undefined | null
): SlideSegment[] | null {
  const topContent = contentJson?.content;
  if (!Array.isArray(topContent)) return null;

  const nodes = topContent as ContentNode[];
  if (!nodes.some(node => node.type === 'slideBreak')) return null;

  // Split at slideBreak boundaries, tracking original top-level indices
  const rawSegments: number[][] = [];
  let current: number[] = [];
  nodes.forEach((node, index) => {
    if (node.type === 'slideBreak') {
      rawSegments.push(current);
      current = [];
    } else {
      current.push(index);
    }
  });
  rawSegments.push(current);

  // Reattach leading speakerNotes to the previous segment (the editor's
  // natural cursor position after inserting a break), matching the splitter.
  for (let i = 1; i < rawSegments.length; i++) {
    const segment = rawSegments[i];
    if (!segment) continue;
    const leading: number[] = [];
    while (
      segment.length > 0 &&
      nodes[segment[0] as number]?.type === 'speakerNotes'
    ) {
      leading.push(segment.shift() as number);
    }
    if (leading.length > 0) {
      const previous = rawSegments[i - 1];
      const previousHasContent = (previous ?? []).some(
        index => nodes[index]?.type !== 'speakerNotes'
      );
      if (previous && previousHasContent) {
        previous.push(...leading);
      } else {
        segment.unshift(...leading);
      }
    }
  }

  return rawSegments
    .filter(segment => segment.length > 0)
    .map(indices => {
      const segmentNodes = indices.map(index => nodes[index] as ContentNode);
      const notesIndex = indices.find(
        index => nodes[index]?.type === 'speakerNotes'
      );
      const notesNode =
        notesIndex !== undefined ? (nodes[notesIndex] as ContentNode) : null;
      return {
        nodeIndices: indices,
        text: segmentNodes
          .filter(node => node.type !== 'speakerNotes')
          .map(nodeText)
          .join(' ')
          .trim(),
        notesText: notesNode ? nodeText(notesNode).trim() : '',
        notesNodeIndex: notesIndex ?? null,
        aiSelected: notesNode?.attrs?.aiSelected !== false,
      };
    });
}

/**
 * Returns slide/notes counts, or null for non-slide materials.
 */
export function getSpeakerNotesCoverage(
  contentJson: Record<string, unknown> | undefined | null
): SpeakerNotesCoverage | null {
  const segments = getSlideSegments(contentJson);
  if (!segments) return null;
  const topContent = (contentJson?.content ?? []) as ContentNode[];
  const slideSegments = segments.filter(segment =>
    segmentHasContent(segment.nodeIndices.map(index => topContent[index]!))
  );
  return {
    slides: slideSegments.length,
    withNotes: slideSegments.filter(segment => segment.notesText !== '').length,
  };
}

/** Build a speakerNotes node from plain draft text (paragraph per line). */
function notesNodeFromText(
  text: string,
  attrs: Record<string, unknown> | undefined
): ContentNode {
  const paragraphs = text
    .split(/\n+/)
    .map(line => line.trim())
    .filter(Boolean)
    .map(line => ({
      type: 'paragraph',
      content: [{ type: 'text', text: line }],
    }));
  return {
    type: 'speakerNotes',
    attrs: attrs ?? { aiSelected: true },
    content: paragraphs.length
      ? paragraphs
      : [{ type: 'paragraph', content: [] }],
  };
}

export interface SpeakerNotesDraftInput {
  slideIndex: number;
  notes: string;
}

/**
 * Apply accepted AI drafts to a document: replace the content of each
 * slide's existing notes node, or insert a new notes node at the end of
 * the slide. Returns a new document; the input is not mutated.
 */
export function applySpeakerNotesDrafts(
  contentJson: Record<string, unknown>,
  drafts: SpeakerNotesDraftInput[]
): Record<string, unknown> {
  const segments = getSlideSegments(contentJson);
  const topContent = contentJson.content;
  if (!segments || !Array.isArray(topContent)) return contentJson;

  const nodes = [...(topContent as ContentNode[])];
  // Process from the highest insertion point down so indices stay valid
  const ordered = [...drafts].sort((a, b) => b.slideIndex - a.slideIndex);
  for (const draft of ordered) {
    const segment = segments[draft.slideIndex];
    if (!segment || !draft.notes.trim()) continue;
    if (segment.notesNodeIndex !== null) {
      const existing = nodes[segment.notesNodeIndex] as ContentNode;
      nodes[segment.notesNodeIndex] = notesNodeFromText(
        draft.notes,
        existing.attrs
      );
    } else {
      const lastIndex = Math.max(...segment.nodeIndices);
      nodes.splice(lastIndex + 1, 0, notesNodeFromText(draft.notes, undefined));
    }
  }
  return { ...contentJson, content: nodes };
}
