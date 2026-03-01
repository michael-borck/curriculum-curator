import React, { useState } from 'react';
import { NodeViewWrapper } from '@tiptap/react';
import type { NodeViewProps } from '@tiptap/react';
import type { QuestionType, QuizOption } from './QuizQuestionNode';
import { Loader2, Sparkles, Zap } from 'lucide-react';
import { useAILevel } from '../../hooks/useAILevel';
import { useWorkingContextStore } from '../../stores/workingContextStore';
import { videoInteractionApi } from '../../services/videoInteractionApi';

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

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${String(secs).padStart(2, '0')}`;
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

const VideoInteractionView: React.FC<NodeViewProps> = ({
  node,
  editor,
  getPos,
  updateAttributes,
}) => {
  const attrs = node.attrs as {
    interactionId: string;
    time: number;
    pause: boolean;
    questionType: QuestionType;
    questionText: string;
    options: QuizOption[];
    feedback: string;
    points: number;
    explanation: string;
  };

  const { canGenerate } = useAILevel();
  const ctx = useWorkingContextStore();
  const isNew = !attrs.questionText && attrs.options.every(o => !o.text);
  const [editing, setEditing] = useState(isNew);
  const [draft, setDraft] = useState({ ...attrs, options: [...attrs.options] });
  const [showFeedback, setShowFeedback] = useState(!!attrs.feedback);
  const [aiGenerating, setAiGenerating] = useState(false);

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
    if (isNew) return;
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

  const handleAIGenerate = async () => {
    if (!editor || typeof getPos !== 'function' || aiGenerating) return;

    // Find nearest transcript segment before this interaction
    const myPos = getPos();
    let nearestText = '';
    editor.state.doc.descendants((n, pos) => {
      if (n.type.name === 'transcriptSegment' && pos < myPos) {
        nearestText = n.textContent;
      }
    });

    if (!nearestText) return;

    setAiGenerating(true);
    try {
      const resp = await videoInteractionApi.generateInteraction({
        segmentText: nearestText,
        questionType: draft.questionType,
        unitId: ctx.activeUnitId ?? undefined,
        designId: ctx.activeDesignId ?? undefined,
        weekNumber: ctx.activeWeek ?? undefined,
      });
      const data = resp.data;

      setDraft({
        ...draft,
        questionText: data.questionText,
        questionType: data.questionType as QuestionType,
        options: data.options.map(o => ({
          id: generateId(),
          text: o.text,
          correct: o.correct,
        })),
        feedback: data.feedback,
        explanation: data.explanation,
        points: data.points,
      });
      setShowFeedback(!!data.feedback);
    } catch (err) {
      console.error('AI interaction generation failed:', err);
    } finally {
      setAiGenerating(false);
    }
  };

  // ── Edit mode ──────────────────────────────────────────────
  if (editing) {
    return (
      <NodeViewWrapper className='video-interaction-node my-4'>
        <div className='border-2 border-blue-300 rounded-lg p-4 bg-blue-50 space-y-3 border-l-4 border-l-blue-500'>
          {/* Header */}
          <div className='flex items-center gap-3'>
            <Zap size={16} className='text-blue-600' />
            <span className='text-sm font-medium text-blue-700'>
              Interaction
            </span>
            <label className='text-sm text-gray-600 flex items-center gap-1'>
              @
              <input
                type='number'
                min={0}
                step={1}
                value={Math.round(draft.time)}
                onChange={e =>
                  setDraft({
                    ...draft,
                    time: Math.max(0, parseInt(e.target.value, 10) || 0),
                  })
                }
                onKeyDown={handleKeyDown}
                className='w-16 border border-gray-300 rounded px-2 py-1 text-sm'
              />
              s
            </label>
            <label className='text-sm text-gray-600 flex items-center gap-1 ml-2'>
              <input
                type='checkbox'
                checked={draft.pause}
                onChange={e => setDraft({ ...draft, pause: e.target.checked })}
              />
              Pause video
            </label>

            {canGenerate && (
              <button
                type='button'
                disabled={aiGenerating}
                onMouseDown={e => {
                  e.preventDefault();
                  void handleAIGenerate();
                }}
                className='ml-auto flex items-center gap-1 px-2 py-1 text-xs text-purple-600 hover:text-purple-800 hover:bg-purple-50 rounded disabled:opacity-50'
                title='Generate question with AI from nearby transcript'
              >
                {aiGenerating ? (
                  <Loader2 size={14} className='animate-spin' />
                ) : (
                  <Sparkles size={14} />
                )}
                <span>{aiGenerating ? 'Generating…' : 'AI'}</span>
              </button>
            )}
          </div>

          {/* Question type & points */}
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
            className='w-full border border-gray-300 rounded p-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-400'
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
                      name={`tf-${draft.interactionId}`}
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
                      name={`opt-${draft.interactionId}`}
                      checked={opt.correct}
                      onChange={() => toggleCorrect(idx)}
                    />
                    <input
                      type='text'
                      value={opt.text}
                      onChange={e => setOption(idx, { text: e.target.value })}
                      onKeyDown={handleKeyDown}
                      placeholder={`Option ${idx + 1}`}
                      className='flex-1 border border-gray-300 rounded px-2 py-1 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-400'
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
                  className='text-sm text-blue-600 hover:text-blue-800'
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
                  className='w-full border border-gray-300 rounded px-2 py-1 text-sm mt-1 bg-white focus:outline-none focus:ring-2 focus:ring-blue-400'
                />
              </div>
            )}
          </div>

          {/* Feedback */}
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
                className='w-full border border-gray-300 rounded p-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-400'
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
              className='px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700'
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
    <NodeViewWrapper className='video-interaction-node my-4'>
      <div className='border-2 border-blue-200 rounded-lg p-4 bg-white border-l-4 border-l-blue-500'>
        {/* Header badges */}
        <div className='flex items-center gap-2 mb-2'>
          <Zap size={14} className='text-blue-600' />
          <span className='inline-block text-xs font-medium bg-blue-100 text-blue-700 rounded-full px-2 py-0.5'>
            @ {formatTime(attrs.time)}
          </span>
          <span className='inline-block text-xs font-medium bg-gray-100 text-gray-600 rounded-full px-2 py-0.5'>
            {TYPE_LABELS[attrs.questionType]}
          </span>
          <span className='inline-block text-xs font-medium bg-gray-100 text-gray-600 rounded-full px-2 py-0.5'>
            {attrs.points} {attrs.points === 1 ? 'pt' : 'pts'}
          </span>
          {attrs.pause && (
            <span className='inline-block text-xs font-medium bg-amber-100 text-amber-700 rounded-full px-2 py-0.5'>
              pauses
            </span>
          )}
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

export default VideoInteractionView;
