/**
 * Transforms that apply AI-generated drafts (branching cards, quiz
 * questions, lesson plans) into a TipTap document JSON — the propose/apply
 * pattern from ADR-068. Nothing here mutates the editor directly; callers
 * pass the result to `editor.commands.setContent`.
 */
import type {
  BranchingCardDraft,
  LessonPlanResponse,
  QuizQuestionDraft,
} from '../services/aiApi';

/** Structural subset of a TipTap JSON node we build or read. */
interface JsonNode {
  type?: string;
  attrs?: Record<string, unknown>;
  content?: JsonNode[];
  text?: string;
}

interface DocJson {
  type?: string;
  content?: JsonNode[];
}

const uuid = (): string =>
  globalThis.crypto?.randomUUID?.() ??
  `id-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;

const paragraph = (text: string): JsonNode => ({
  type: 'paragraph',
  content: text ? [{ type: 'text', text }] : [],
});

const heading = (level: 1 | 2 | 3, text: string): JsonNode => ({
  type: 'heading',
  attrs: { level },
  content: [{ type: 'text', text }],
});

/** Append generated branching cards to the end of the document.
 *
 * Card ids from the draft are preserved verbatim — choices link by
 * targetCardId, so remapping would break the graph (unlike template
 * skeletons, which own their whole id space).
 */
export function appendBranchingCards(
  contentJson: DocJson,
  cards: BranchingCardDraft[]
): DocJson {
  const nodes: JsonNode[] = cards.map(card => ({
    type: 'branchingCard',
    attrs: {
      cardId: card.cardId,
      cardType: card.cardType,
      cardTitle: card.cardTitle,
      cardContent: card.cardContent,
      choices: card.choices,
      endScore: card.endScore ?? 0,
      endMessage: card.endMessage ?? '',
      stepThreshold: card.stepThreshold ?? 0,
      endMessageEfficient: card.endMessageEfficient ?? '',
      endMessageThorough: card.endMessageThorough ?? '',
    },
  }));
  return {
    ...contentJson,
    content: [...(contentJson.content ?? []), ...nodes],
  };
}

/** Append generated quiz questions to the end of the document. */
export function appendQuizQuestions(
  contentJson: DocJson,
  questions: QuizQuestionDraft[]
): DocJson {
  const nodes: JsonNode[] = questions.map(question => ({
    type: 'quizQuestion',
    attrs: {
      questionId: uuid(),
      questionType: question.questionType,
      questionText: question.questionText,
      options: question.options,
      pairs: [],
      feedback: question.feedback ?? '',
      points: question.points ?? 1,
      explanation: question.explanation ?? '',
    },
  }));
  return {
    ...contentJson,
    content: [...(contentJson.content ?? []), ...nodes],
  };
}

/** Convert a generated lesson plan into structured document nodes. */
export function lessonPlanToNodes(plan: LessonPlanResponse): JsonNode[] {
  const nodes: JsonNode[] = [];

  nodes.push(heading(1, plan.title));

  if (plan.objectives.length > 0) {
    nodes.push(heading(2, 'Objectives'));
    nodes.push({
      type: 'bulletList',
      content: plan.objectives.map(objective => ({
        type: 'listItem',
        content: [paragraph(`${objective.text} (${objective.bloomLevel})`)],
      })),
    });
  }

  for (const segment of plan.segments) {
    nodes.push(heading(2, `${segment.name} — ${segment.minutes} min`));
    nodes.push(paragraph(segment.description));
    const checks = plan.formativeChecks.filter(
      check => check.segment === segment.name
    );
    for (const check of checks) {
      nodes.push(paragraph(`Check: ${check.question}`));
      if (check.misconceptions.length > 0) {
        nodes.push(
          paragraph(
            `Watch for misconceptions: ${check.misconceptions.join('; ')}.`
          )
        );
      }
    }
  }

  if (plan.differentiationNotes) {
    nodes.push(heading(2, 'Differentiation'));
    nodes.push(paragraph(plan.differentiationNotes));
  }

  if (plan.materialsChecklist.length > 0) {
    nodes.push(heading(2, 'Materials checklist'));
    nodes.push({
      type: 'bulletList',
      content: plan.materialsChecklist.map(item => ({
        type: 'listItem',
        content: [paragraph(item)],
      })),
    });
  }

  if (plan.homeworkBridge) {
    nodes.push(heading(2, 'Homework bridge'));
    nodes.push(paragraph(plan.homeworkBridge));
  }

  return nodes;
}
