/**
 * Content-type starter templates (story 19C.1).
 *
 * Each template is a TipTap document the material editor loads so the author
 * starts from the right structure instead of a blank page. Templates are
 * decoupled from the session-format field (lecture/tutorial/…): "what kind
 * of content" is independent of "what kind of session".
 *
 * Node ids in the JSON are placeholders. `getTemplateForContentType`
 * regenerates them on every insert so two materials built from the same
 * template never share a quizQuestion/branchingCard id, and branching
 * card links are remapped consistently so they keep pointing at the right
 * (newly-identified) cards.
 */

import quizTemplate from './quiz.json';
import slidesTemplate from './slides.json';
import caseStudyTemplate from './case_study.json';
import interactiveVideoTemplate from './interactive_video.json';

export type TemplateKey =
  | 'blank'
  | 'quiz'
  | 'slides'
  | 'case_study'
  | 'interactive_video';

export interface TemplateOption {
  key: TemplateKey;
  label: string;
  description: string;
}

export const TEMPLATE_OPTIONS: TemplateOption[] = [
  { key: 'blank', label: 'Blank', description: 'Start from an empty page' },
  {
    key: 'quiz',
    label: 'Quiz',
    description: 'Structured questions with feedback',
  },
  {
    key: 'slides',
    label: 'Slides',
    description: 'Slide breaks with speaker notes',
  },
  {
    key: 'case_study',
    label: 'Case study',
    description: 'Branching scenario with decision points',
  },
  {
    key: 'interactive_video',
    label: 'Interactive video',
    description: 'Embedded video with quiz interactions',
  },
];

type JsonDoc = Record<string, unknown>;

const TEMPLATES: Record<Exclude<TemplateKey, 'blank'>, JsonDoc> = {
  quiz: quizTemplate as JsonDoc,
  slides: slidesTemplate as JsonDoc,
  case_study: caseStudyTemplate as JsonDoc,
  interactive_video: interactiveVideoTemplate as JsonDoc,
};

interface Node {
  type?: string;
  attrs?: Record<string, unknown>;
  content?: Node[];
}

function newId(): string {
  return globalThis.crypto.randomUUID();
}

/** Collect a fresh id for every branchingCard cardId in the document. */
function buildCardIdMap(nodes: Node[], map: Map<string, string>): void {
  for (const node of nodes) {
    if (node.type === 'branchingCard') {
      const old = node.attrs?.cardId;
      if (typeof old === 'string' && old && !map.has(old)) {
        map.set(old, newId());
      }
    }
    if (Array.isArray(node.content)) buildCardIdMap(node.content, map);
  }
}

function remapNode(node: Node, cardIdMap: Map<string, string>): void {
  const attrs = node.attrs;

  if (node.type === 'quizQuestion' && attrs) {
    attrs.questionId = newId();
    if (Array.isArray(attrs.options)) {
      attrs.options = (attrs.options as Record<string, unknown>[]).map(o => ({
        ...o,
        id: newId(),
      }));
    }
  }

  if (node.type === 'branchingCard' && attrs) {
    const oldCardId = attrs.cardId;
    if (typeof oldCardId === 'string') {
      attrs.cardId = cardIdMap.get(oldCardId) ?? newId();
    }
    if (Array.isArray(attrs.choices)) {
      attrs.choices = (attrs.choices as Record<string, unknown>[]).map(c => {
        const target = c.targetCardId;
        return {
          ...c,
          id: newId(),
          // Keep the link pointing at the same card under its new id
          targetCardId:
            typeof target === 'string' && cardIdMap.has(target)
              ? cardIdMap.get(target)
              : (target ?? ''),
        };
      });
    }
  }

  if (Array.isArray(node.content)) {
    for (const child of node.content) remapNode(child, cardIdMap);
  }
}

/**
 * Return a deep copy of the template for `key` with all node ids freshly
 * generated, or null for 'blank'/unknown keys.
 */
export function getTemplateForContentType(
  key: TemplateKey
): Record<string, unknown> | null {
  if (key === 'blank') return null;
  const template = TEMPLATES[key];
  if (!template) return null;

  const clone = globalThis.structuredClone(template) as JsonDoc & {
    content?: Node[];
  };
  const content = Array.isArray(clone.content) ? clone.content : [];

  const cardIdMap = new Map<string, string>();
  buildCardIdMap(content, cardIdMap);
  for (const node of content) remapNode(node, cardIdMap);

  return clone;
}
