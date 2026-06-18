/**
 * Helpers for the AI structure-recovery action (story 6.16).
 *
 * A material is a candidate for "Improve structure with AI" when its
 * content is essentially flat paragraphs — the shape a PDF (or other
 * plain) import produces. Materials that already have headings, lists,
 * tables, or structured nodes don't need it.
 */

interface ContentNode {
  type?: string;
  content?: ContentNode[];
  text?: string;
}

const STRUCTURED_TYPES = new Set([
  'heading',
  'bulletList',
  'orderedList',
  'table',
  'slideBreak',
  'quizQuestion',
  'branchingCard',
  'codeBlock',
]);

/**
 * True when the document is two or more blocks that are all plain
 * paragraphs (no structured nodes). Single-paragraph or empty docs return
 * false — there's nothing to recover.
 */
export function isPlainParagraphContent(
  contentJson: Record<string, unknown> | undefined | null
): boolean {
  const top = contentJson?.content;
  if (!Array.isArray(top)) return false;
  const nodes = top as ContentNode[];
  const blocks = nodes.filter(n => (n.text ?? '').trim() !== '' || n.content);
  if (blocks.length < 2) return false;
  if (nodes.some(n => n.type && STRUCTURED_TYPES.has(n.type))) return false;
  return nodes.every(n => n.type === 'paragraph');
}

function nodeText(node: ContentNode): string {
  if (node.text) return node.text;
  return (node.content ?? []).map(nodeText).join(' ');
}

/** Rough token estimate (~4 chars/token) for cost transparency. */
export function estimateTokens(
  contentJson: Record<string, unknown> | undefined | null
): number {
  const top = contentJson?.content;
  if (!Array.isArray(top)) return 0;
  const text = (top as ContentNode[]).map(nodeText).join(' ');
  return Math.ceil(text.length / 4);
}
