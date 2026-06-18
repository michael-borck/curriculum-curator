import { describe, it, expect } from 'vitest';
import { getTemplateForContentType, TEMPLATE_OPTIONS } from './index';

interface Node {
  type?: string;
  attrs?: Record<string, unknown>;
  content?: Node[];
}

function collect(doc: { content?: Node[] }, type: string): Node[] {
  const out: Node[] = [];
  const walk = (nodes: Node[]) => {
    for (const n of nodes) {
      if (n.type === type) out.push(n);
      if (Array.isArray(n.content)) walk(n.content);
    }
  };
  walk(doc.content ?? []);
  return out;
}

describe('getTemplateForContentType', () => {
  it('returns null for blank', () => {
    expect(getTemplateForContentType('blank')).toBeNull();
  });

  it('builds a quiz with fresh question and option ids', () => {
    const a = getTemplateForContentType('quiz') as { content?: Node[] };
    const b = getTemplateForContentType('quiz') as { content?: Node[] };
    const qa = collect(a, 'quizQuestion');
    const qb = collect(b, 'quizQuestion');
    expect(qa.length).toBeGreaterThan(0);
    // No id is shared between two instantiations
    const idsA = qa.map(q => q.attrs?.questionId as string);
    const idsB = qb.map(q => q.attrs?.questionId as string);
    expect(idsA.some(id => idsB.includes(id))).toBe(false);
    // Placeholder ids are gone
    expect(idsA).not.toContain('tmpl-q-mc');
    // Option ids regenerated too
    const opts = qa[0]?.attrs?.options as { id: string }[];
    expect(opts.every(o => o.id && o.id !== 'tmpl-mc-a')).toBe(true);
  });

  it('remaps branching card links consistently', () => {
    const doc = getTemplateForContentType('case_study') as {
      content?: Node[];
    };
    const cards = collect(doc, 'branchingCard');
    const cardIds = new Set(cards.map(c => c.attrs?.cardId as string));
    // Every non-empty choice target points at a real (new) card id
    for (const card of cards) {
      const choices = (card.attrs?.choices ?? []) as {
        targetCardId?: string;
      }[];
      for (const choice of choices) {
        if (choice.targetCardId) {
          expect(cardIds.has(choice.targetCardId)).toBe(true);
        }
      }
    }
    // Placeholder ids no longer present
    expect([...cardIds]).not.toContain('card-intro-001');
  });

  it('does not mutate the shared template (repeat calls independent)', () => {
    const first = getTemplateForContentType('case_study') as {
      content?: Node[];
    };
    const second = getTemplateForContentType('case_study') as {
      content?: Node[];
    };
    const id1 = collect(first, 'branchingCard')[0]?.attrs?.cardId;
    const id2 = collect(second, 'branchingCard')[0]?.attrs?.cardId;
    expect(id1).not.toBe(id2);
  });

  it('every non-blank option has a working template', () => {
    for (const opt of TEMPLATE_OPTIONS) {
      if (opt.key === 'blank') continue;
      const doc = getTemplateForContentType(opt.key);
      expect(doc).not.toBeNull();
      expect((doc as { type?: string }).type).toBe('doc');
    }
  });
});
