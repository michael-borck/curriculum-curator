import React, { useState } from 'react';
import { NodeViewWrapper } from '@tiptap/react';
import type { NodeViewProps } from '@tiptap/react';
import type { QuestionType, QuizOption } from './QuizQuestionNode';

const TYPE_LABELS: Record<QuestionType, string> = {
  multiple_choice: 'Multiple Choice',
  true_false: 'True / False',
  multi_select: 'Multi-Select',
  short_answer: 'Short Answer',
  fill_in_blank: 'Fill in the Blank',
};

function generateId(): string {
  return globalThis.crypto.randomUUID();
}

function resetOptionsForType(
  type: QuestionType,
  existing: QuizOption[]
): QuizOption[] {
  switch (type) {
    case 'true_false':
      return [
        { id: generateId(), text: 'True', correct: false },
        { id: generateId(), text: 'False', correct: false },
      ];
    case 'short_answer':
    case 'fill_in_blank':
      return [{ id: generateId(), text: '', correct: true }];
    case 'multiple_choice':
    case 'multi_select':
      return existing.length >= 2
        ? existing
        : [
            { id: generateId(), text: '', correct: false },
            { id: generateId(), text: '', correct: false },
          ];
  }
}

const QuizQuestionView: React.FC<NodeViewProps> = ({
  node,
  updateAttributes,
}) => {
  const attrs = node.attrs as {
    questionId: string;
    questionType: QuestionType;
    questionText: string;
    options: QuizOption[];
    feedback: string;
    points: number;
    explanation: string;
  };

  const isNew = !attrs.questionText && attrs.options.every(o => !o.text);
  const [editing, setEditing] = useState(isNew);
  const [draft, setDraft] = useState({ ...attrs, options: [...attrs.options] });
  const [showFeedback, setShowFeedback] = useState(!!attrs.feedback);

  const startEdit = () => {
    setDraft({ ...attrs, options: [...attrs.options] });
    setShowFeedback(!!attrs.feedback);
    setEditing(true);
  };

  const handleSave = () => {
    updateAttributes(draft);
    setEditing(false);
  };

  const handleCancel = () => {
    if (isNew) return; // can't cancel a brand-new question
    setDraft({ ...attrs, options: [...attrs.options] });
    setEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    e.stopPropagation();
  };

  const setOption = (idx: number, patch: Partial<QuizOption>) => {
    const next = draft.options.map((o, i) =>
      i === idx ? { ...o, ...patch } : o
    );
    setDraft({ ...draft, options: next });
  };

  const toggleCorrect = (idx: number) => {
    if (draft.questionType === 'multiple_choice') {
      // radio — only one correct
      const next = draft.options.map((o, i) => ({
        ...o,
        correct: i === idx,
      }));
      setDraft({ ...draft, options: next });
    } else {
      setOption(idx, { correct: !draft.options[idx].correct });
    }
  };

  const addOption = () => {
    setDraft({
      ...draft,
      options: [
        ...draft.options,
        { id: generateId(), text: '', correct: false },
      ],
    });
  };

  const removeOption = (idx: number) => {
    if (draft.options.length <= 2) return;
    setDraft({ ...draft, options: draft.options.filter((_, i) => i !== idx) });
  };

  const handleTypeChange = (newType: QuestionType) => {
    const newOptions = resetOptionsForType(newType, draft.options);
    setDraft({ ...draft, questionType: newType, options: newOptions });
  };

  // ── Edit mode ──────────────────────────────────────────────
  if (editing) {
    return (
      <NodeViewWrapper className='quiz-question-node my-4'>
        <div className='border-2 border-purple-300 rounded-lg p-4 bg-purple-50 space-y-3'>
          {/* Header */}
          <div className='flex items-center gap-3'>
            <select
              value={draft.questionType}
              onChange={e => handleTypeChange(e.target.value as QuestionType)}
              onKeyDown={handleKeyDown}
              className='text-sm border border-gray-300 rounded px-2 py-1 bg-white'
            >
              {Object.entries(TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            <label className='text-sm text-gray-600 flex items-center gap-1'>
              Points:
              <input
                type='number'
                min={0}
                value={draft.points}
                onChange={e =>
                  setDraft({
                    ...draft,
                    points: Math.max(0, parseInt(e.target.value, 10) || 0),
                  })
                }
                onKeyDown={handleKeyDown}
                className='w-16 border border-gray-300 rounded px-2 py-1 text-sm'
              />
            </label>
          </div>

          {/* Question text */}
          <textarea
            value={draft.questionText}
            onChange={e => setDraft({ ...draft, questionText: e.target.value })}
            onKeyDown={handleKeyDown}
            rows={2}
            placeholder='Enter question text…'
            className='w-full border border-gray-300 rounded p-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-purple-400'
          />

          {/* Options editor */}
          <div className='space-y-2'>
            {draft.questionType === 'true_false' && (
              <div className='space-y-1'>
                {draft.options.map((opt, idx) => (
                  <label
                    key={opt.id}
                    className='flex items-center gap-2 text-sm'
                  >
                    <input
                      type='radio'
                      name={`tf-${draft.questionId}`}
                      checked={opt.correct}
                      onChange={() => toggleCorrect(idx)}
                    />
                    <span>{opt.text}</span>
                    {opt.correct && (
                      <span className='text-green-600 text-xs ml-1'>
                        (correct)
                      </span>
                    )}
                  </label>
                ))}
              </div>
            )}

            {(draft.questionType === 'multiple_choice' ||
              draft.questionType === 'multi_select') && (
              <div className='space-y-1'>
                {draft.options.map((opt, idx) => (
                  <div key={opt.id} className='flex items-center gap-2'>
                    <input
                      type={
                        draft.questionType === 'multiple_choice'
                          ? 'radio'
                          : 'checkbox'
                      }
                      name={`opt-${draft.questionId}`}
                      checked={opt.correct}
                      onChange={() => toggleCorrect(idx)}
                    />
                    <input
                      type='text'
                      value={opt.text}
                      onChange={e => setOption(idx, { text: e.target.value })}
                      onKeyDown={handleKeyDown}
                      placeholder={`Option ${idx + 1}`}
                      className='flex-1 border border-gray-300 rounded px-2 py-1 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-purple-400'
                    />
                    {draft.options.length > 2 && (
                      <button
                        type='button'
                        onMouseDown={e => {
                          e.preventDefault();
                          removeOption(idx);
                        }}
                        className='text-red-400 hover:text-red-600 text-sm px-1'
                        title='Remove option'
                      >
                        &times;
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type='button'
                  onMouseDown={e => {
                    e.preventDefault();
                    addOption();
                  }}
                  className='text-sm text-purple-600 hover:text-purple-800'
                >
                  + Add option
                </button>
              </div>
            )}

            {(draft.questionType === 'short_answer' ||
              draft.questionType === 'fill_in_blank') && (
              <div>
                <label className='text-sm text-gray-600'>
                  Expected answer:
                </label>
                <input
                  type='text'
                  value={draft.options[0]?.text ?? ''}
                  onChange={e => setOption(0, { text: e.target.value })}
                  onKeyDown={handleKeyDown}
                  placeholder='Type the expected answer…'
                  className='w-full border border-gray-300 rounded px-2 py-1 text-sm mt-1 bg-white focus:outline-none focus:ring-2 focus:ring-purple-400'
                />
              </div>
            )}
          </div>

          {/* Feedback (collapsible) */}
          <div>
            {!showFeedback ? (
              <button
                type='button'
                onMouseDown={e => {
                  e.preventDefault();
                  setShowFeedback(true);
                }}
                className='text-sm text-gray-500 hover:text-gray-700'
              >
                + Add feedback
              </button>
            ) : (
              <textarea
                value={draft.feedback}
                onChange={e => setDraft({ ...draft, feedback: e.target.value })}
                onKeyDown={handleKeyDown}
                rows={2}
                placeholder='Feedback shown after answering…'
                className='w-full border border-gray-300 rounded p-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-purple-400'
              />
            )}
          </div>

          {/* Actions */}
          <div className='flex gap-2'>
            <button
              type='button'
              onMouseDown={e => {
                e.preventDefault();
                handleSave();
              }}
              className='px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700'
            >
              Save
            </button>
            {!isNew && (
              <button
                type='button'
                onMouseDown={e => {
                  e.preventDefault();
                  handleCancel();
                }}
                className='px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300'
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      </NodeViewWrapper>
    );
  }

  // ── View mode ──────────────────────────────────────────────
  return (
    <NodeViewWrapper className='quiz-question-node my-4'>
      <div className='border-2 border-purple-200 rounded-lg p-4 bg-white'>
        {/* Header badges */}
        <div className='flex items-center gap-2 mb-2'>
          <span className='inline-block text-xs font-medium bg-purple-100 text-purple-700 rounded-full px-2 py-0.5'>
            {TYPE_LABELS[attrs.questionType]}
          </span>
          <span className='inline-block text-xs font-medium bg-gray-100 text-gray-600 rounded-full px-2 py-0.5'>
            {attrs.points} {attrs.points === 1 ? 'pt' : 'pts'}
          </span>
        </div>

        {/* Question text */}
        <p className='text-sm font-medium text-gray-800 mb-3'>
          {attrs.questionText || '(no question text)'}
        </p>

        {/* Options display */}
        {(attrs.questionType === 'multiple_choice' ||
          attrs.questionType === 'multi_select' ||
          attrs.questionType === 'true_false') && (
          <ul className='space-y-1 mb-3'>
            {attrs.options.map(opt => (
              <li key={opt.id} className='flex items-center gap-2 text-sm'>
                {attrs.questionType === 'multi_select' ? (
                  <span className='text-gray-400'>
                    {opt.correct ? '\u2611' : '\u2610'}
                  </span>
                ) : (
                  <span className='text-gray-400'>
                    {opt.correct ? '\u25C9' : '\u25CB'}
                  </span>
                )}
                <span
                  className={
                    opt.correct ? 'text-green-700 font-medium' : 'text-gray-700'
                  }
                >
                  {opt.text || '(empty)'}
                </span>
              </li>
            ))}
          </ul>
        )}

        {(attrs.questionType === 'short_answer' ||
          attrs.questionType === 'fill_in_blank') && (
          <p className='text-sm text-gray-600 mb-3'>
            <span className='font-medium'>Expected:</span>{' '}
            {attrs.options[0]?.text || '(none)'}
          </p>
        )}

        {/* Feedback callout */}
        {attrs.feedback && (
          <div className='bg-blue-50 border border-blue-200 rounded p-2 text-sm text-blue-700 mb-3'>
            <span className='font-medium'>Feedback:</span> {attrs.feedback}
          </div>
        )}

        {/* Edit button */}
        <div className='flex justify-end'>
          <button
            type='button'
            onMouseDown={e => {
              e.preventDefault();
              startEdit();
            }}
            className='px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200'
          >
            Edit
          </button>
        </div>
      </div>
    </NodeViewWrapper>
  );
};

export default QuizQuestionView;
