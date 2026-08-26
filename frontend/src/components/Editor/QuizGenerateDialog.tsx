import React, { useState } from 'react';
import { HelpCircle, Loader2, X } from 'lucide-react';
import toast from 'react-hot-toast';
import {
  aiApi,
  type QuizQuestionDraft,
  type QuizQuestionType,
} from '../../services/aiApi';

interface QuizGenerateDialogProps {
  materialId: string;
  onApply: (questions: QuizQuestionDraft[]) => void;
  onClose: () => void;
}

type Stage = 'options' | 'generating' | 'review';

const QUESTION_TYPES: { value: QuizQuestionType; label: string }[] = [
  { value: 'multiple_choice', label: 'Multiple choice' },
  { value: 'true_false', label: 'True / false' },
  { value: 'multi_select', label: 'Multiple select' },
  { value: 'short_answer', label: 'Short answer' },
  { value: 'fill_in_blank', label: 'Fill in the blank' },
];

const DEFAULT_TYPES: Set<QuizQuestionType> = new Set([
  'multiple_choice',
  'true_false',
]);

/**
 * Propose/apply flow for AI practice quizzes (19C.6, ADR-068): pick
 * question types and count, generate typed drafts, review each, then apply
 * the accepted ones as structured quiz blocks. Nothing touches the document
 * until Apply.
 */
const QuizGenerateDialog: React.FC<QuizGenerateDialogProps> = ({
  materialId,
  onApply,
  onClose,
}) => {
  const [stage, setStage] = useState<Stage>('options');
  const [types, setTypes] = useState<Set<QuizQuestionType>>(
    () => new Set(DEFAULT_TYPES)
  );
  const [count, setCount] = useState(5);
  const [questions, setQuestions] = useState<QuizQuestionDraft[]>([]);
  const [accepted, setAccepted] = useState<Set<number>>(new Set());

  const toggleType = (value: QuizQuestionType) => {
    setTypes(prev => {
      const next = new Set(prev);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return next;
    });
  };

  const toggleAccepted = (index: number) => {
    setAccepted(prev => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  const handleGenerate = async () => {
    setStage('generating');
    try {
      const { data } = await aiApi.generateQuiz(materialId, {
        questionTypes: [...types],
        count,
      });
      if (data.questions.length === 0) {
        toast.error('No questions were generated — try again');
        setStage('options');
        return;
      }
      setQuestions(data.questions);
      setAccepted(new Set(data.questions.map((_, i) => i)));
      setStage('review');
    } catch {
      toast.error('Failed to generate quiz questions');
      setStage('options');
    }
  };

  const handleApply = () => {
    onApply(questions.filter((_, i) => accepted.has(i)));
    onClose();
  };

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
      <div className='bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col'>
        <div className='flex items-center justify-between px-5 py-3 border-b border-gray-100'>
          <h2 className='font-semibold text-gray-900 flex items-center gap-2'>
            <HelpCircle className='w-4 h-4 text-purple-500' />
            Generate practice quiz
          </h2>
          <button
            onClick={onClose}
            className='p-1 text-gray-400 hover:text-gray-600'
            title='Close'
          >
            <X className='w-4 h-4' />
          </button>
        </div>

        <div className='flex-1 overflow-y-auto px-5 py-4'>
          {stage === 'options' && (
            <>
              <p className='text-sm text-gray-600 mb-3'>
                Drafts practice questions from this material&apos;s content as
                structured quiz blocks. Reviewed before anything is saved.
              </p>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Question types
              </label>
              <div className='grid grid-cols-2 gap-2 mb-3'>
                {QUESTION_TYPES.map(type => (
                  <label
                    key={type.value}
                    className={`flex items-center gap-2 p-2 rounded-md border text-sm cursor-pointer ${
                      types.has(type.value)
                        ? 'border-purple-300 bg-purple-50 text-purple-800'
                        : 'border-gray-200 hover:border-gray-300 text-gray-600'
                    }`}
                  >
                    <input
                      type='checkbox'
                      checked={types.has(type.value)}
                      onChange={() => toggleType(type.value)}
                    />
                    {type.label}
                  </label>
                ))}
              </div>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Number of questions
              </label>
              <input
                type='number'
                min={1}
                max={20}
                value={count}
                onChange={e =>
                  setCount(
                    Math.min(20, Math.max(1, Number(e.target.value) || 5))
                  )
                }
                className='w-24 border border-gray-300 rounded-md px-3 py-2 text-sm mb-4'
              />
            </>
          )}

          {stage === 'generating' && (
            <div className='flex flex-col items-center justify-center py-12 text-gray-500'>
              <Loader2 className='w-6 h-6 animate-spin mb-3' />
              <p className='text-sm'>Writing questions…</p>
            </div>
          )}

          {stage === 'review' && (
            <div className='space-y-4'>
              {questions.map((question, index) => (
                <div
                  key={index}
                  className='border border-gray-200 rounded-lg p-3'
                >
                  <label className='flex items-start gap-2 cursor-pointer'>
                    <input
                      type='checkbox'
                      checked={accepted.has(index)}
                      onChange={() => toggleAccepted(index)}
                      className='mt-1'
                    />
                    <span>
                      <span className='block text-sm font-medium text-gray-800'>
                        {question.questionText}
                      </span>
                      <span className='text-xs uppercase tracking-wide text-gray-400'>
                        {question.questionType.replace('_', ' ')}
                      </span>
                    </span>
                  </label>
                  {question.options.length > 0 && (
                    <ul className='mt-2 ml-6 space-y-0.5'>
                      {question.options.map(option => (
                        <li key={option.id} className='text-xs text-gray-600'>
                          {option.correct ? '✓' : '○'} {option.text}
                        </li>
                      ))}
                    </ul>
                  )}
                  {question.feedback && (
                    <p className='mt-2 ml-6 text-xs text-emerald-700'>
                      Feedback: {question.feedback}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className='flex items-center justify-end gap-3 px-5 py-3 border-t border-gray-100'>
          <button
            onClick={onClose}
            className='px-4 py-2 text-sm text-gray-600 hover:text-gray-800'
          >
            Cancel
          </button>
          {stage === 'options' && (
            <button
              onClick={handleGenerate}
              disabled={types.size === 0}
              className='flex items-center gap-2 px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50'
            >
              <HelpCircle className='w-4 h-4' />
              Draft questions
            </button>
          )}
          {stage === 'review' && (
            <button
              onClick={handleApply}
              disabled={accepted.size === 0}
              className='px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50'
            >
              Apply {accepted.size} question{accepted.size === 1 ? '' : 's'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuizGenerateDialog;
