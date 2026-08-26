import React, { useEffect, useState } from 'react';
import { BookOpen, Loader2, X } from 'lucide-react';
import toast from 'react-hot-toast';
import {
  aiApi,
  type LessonPlanFramework,
  type LessonPlanResponse,
} from '../../services/aiApi';

interface LessonPlanDialogProps {
  content: string;
  onApply: (plan: LessonPlanResponse) => void;
  onClose: () => void;
}

type Stage = 'options' | 'generating' | 'review';

/**
 * Propose/apply flow for AI lesson plans (5.12/5.13, ADR-068): pick a
 * framework (with when-to-use guidance), session length, and context;
 * review the generated plan; then insert it as document nodes.
 */
const LessonPlanDialog: React.FC<LessonPlanDialogProps> = ({
  content,
  onApply,
  onClose,
}) => {
  const [stage, setStage] = useState<Stage>('options');
  const [frameworks, setFrameworks] = useState<
    Record<string, LessonPlanFramework>
  >({});
  const [frameworkId, setFrameworkId] = useState('');
  const [duration, setDuration] = useState(50);
  const [classSize, setClassSize] = useState('');
  const [deliveryMode, setDeliveryMode] = useState('');
  const [plan, setPlan] = useState<LessonPlanResponse | null>(null);

  useEffect(() => {
    aiApi
      .listLessonPlanFrameworks()
      .then(({ data }) => {
        setFrameworks(data);
        const first = Object.keys(data)[0];
        if (first) setFrameworkId(first);
      })
      .catch(() => toast.error('Could not load lesson-plan frameworks'));
  }, []);

  const totalMinutes = plan
    ? plan.segments.reduce((sum, segment) => sum + segment.minutes, 0)
    : 0;

  const handleGenerate = async () => {
    setStage('generating');
    try {
      const { data } = await aiApi.generateLessonPlan({
        content: content.slice(0, 20000),
        frameworkId,
        durationMinutes: duration,
        classSize: classSize ? Number(classSize) : undefined,
        deliveryMode: deliveryMode.trim() || undefined,
      });
      setPlan(data);
      setStage('review');
    } catch {
      toast.error('Failed to generate lesson plan');
      setStage('options');
    }
  };

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
      <div className='bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col'>
        <div className='flex items-center justify-between px-5 py-3 border-b border-gray-100'>
          <h2 className='font-semibold text-gray-900 flex items-center gap-2'>
            <BookOpen className='w-4 h-4 text-purple-500' />
            Generate lesson plan
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
                Builds a timed, framework-structured lesson plan from this
                material&apos;s content. Reviewed before anything is saved.
              </p>

              <label className='block text-xs font-medium text-gray-600 mb-2'>
                Framework
              </label>
              <div className='space-y-2 mb-4'>
                {Object.entries(frameworks).map(([id, fw]) => (
                  <label
                    key={id}
                    className={`block p-3 rounded-lg border cursor-pointer ${
                      frameworkId === id
                        ? 'border-purple-300 bg-purple-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <span className='flex items-center gap-2'>
                      <input
                        type='radio'
                        name='framework'
                        checked={frameworkId === id}
                        onChange={() => setFrameworkId(id)}
                      />
                      <span className='text-sm font-medium text-gray-800'>
                        {fw.name}
                      </span>
                    </span>
                    <span className='block mt-1 ml-6 text-xs text-gray-500'>
                      <span className='text-gray-400'>When to use: </span>
                      {fw.whenToUse}
                    </span>
                  </label>
                ))}
              </div>

              <div className='grid grid-cols-3 gap-3 mb-4'>
                <div>
                  <label className='block text-xs font-medium text-gray-600 mb-1'>
                    Minutes
                  </label>
                  <input
                    type='number'
                    min={10}
                    max={300}
                    value={duration}
                    onChange={e =>
                      setDuration(
                        Math.min(
                          300,
                          Math.max(10, Number(e.target.value) || 50)
                        )
                      )
                    }
                    className='w-full border border-gray-300 rounded-md px-3 py-2 text-sm'
                  />
                </div>
                <div>
                  <label className='block text-xs font-medium text-gray-600 mb-1'>
                    Class size{' '}
                    <span className='text-gray-400 font-normal'>(opt.)</span>
                  </label>
                  <input
                    type='number'
                    min={1}
                    value={classSize}
                    onChange={e => setClassSize(e.target.value)}
                    placeholder='—'
                    className='w-full border border-gray-300 rounded-md px-3 py-2 text-sm'
                  />
                </div>
                <div>
                  <label className='block text-xs font-medium text-gray-600 mb-1'>
                    Mode{' '}
                    <span className='text-gray-400 font-normal'>(opt.)</span>
                  </label>
                  <input
                    type='text'
                    value={deliveryMode}
                    onChange={e => setDeliveryMode(e.target.value)}
                    placeholder='on campus'
                    className='w-full border border-gray-300 rounded-md px-3 py-2 text-sm'
                  />
                </div>
              </div>
            </>
          )}

          {stage === 'generating' && (
            <div className='flex flex-col items-center justify-center py-12 text-gray-500'>
              <Loader2 className='w-6 h-6 animate-spin mb-3' />
              <p className='text-sm'>Planning the session…</p>
            </div>
          )}

          {stage === 'review' && plan && (
            <div className='space-y-4'>
              <h3 className='text-base font-semibold text-gray-900'>
                {plan.title}
              </h3>
              <div>
                <h4 className='text-xs font-medium uppercase tracking-wide text-gray-400 mb-1'>
                  Objectives
                </h4>
                <ul className='list-disc ml-5 text-sm text-gray-700'>
                  {plan.objectives.map((objective, i) => (
                    <li key={i}>
                      {objective.text}{' '}
                      <span className='text-xs text-gray-400'>
                        ({objective.bloomLevel})
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className='text-xs font-medium uppercase tracking-wide text-gray-400 mb-1'>
                  Segments — {totalMinutes} min total
                </h4>
                <ul className='space-y-1 text-sm text-gray-700'>
                  {plan.segments.map((segment, i) => (
                    <li key={i}>
                      <span className='font-medium'>{segment.name}</span> (
                      {segment.minutes} min) — {segment.description}
                    </li>
                  ))}
                </ul>
              </div>
              {plan.differentiationNotes && (
                <div className='bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm text-blue-800'>
                  <span className='font-medium'>Differentiation: </span>
                  {plan.differentiationNotes}
                </div>
              )}
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
              disabled={!frameworkId || !content.trim()}
              className='flex items-center gap-2 px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50'
            >
              <BookOpen className='w-4 h-4' />
              Draft plan
            </button>
          )}
          {stage === 'review' && plan && (
            <button
              onClick={() => {
                onApply(plan);
                onClose();
              }}
              className='px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700'
            >
              Insert plan
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default LessonPlanDialog;
