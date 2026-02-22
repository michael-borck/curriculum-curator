import React, { useState } from 'react';
import { CheckCircle, Trash2, Plus, Loader2, X, Sparkles } from 'lucide-react';
import type {
  ScaffoldUnitResponse,
  ScaffoldULO,
  ScaffoldAssessment,
} from '../../services/aiApi';
import { useWorkingContextStore } from '../../stores/workingContextStore';

interface UnitScaffoldReviewProps {
  scaffold: ScaffoldUnitResponse;
  onAccept: (scaffold: ScaffoldUnitResponse) => void;
  onCancel: () => void;
  accepting?: boolean | undefined;
}

const UnitScaffoldReview: React.FC<UnitScaffoldReviewProps> = ({
  scaffold: initialScaffold,
  onAccept,
  onCancel,
  accepting = false,
}) => {
  const topicLabel = useWorkingContextStore(s => s.activeTopicLabel) || 'Week';
  const [scaffold, setScaffold] =
    useState<ScaffoldUnitResponse>(initialScaffold);

  // ─── ULO helpers ─────────────────────────────────────────────────────────
  const updateULO = (index: number, field: keyof ScaffoldULO, value: string) =>
    setScaffold(s => ({
      ...s,
      ulos: s.ulos.map((u, i) => (i === index ? { ...u, [field]: value } : u)),
    }));

  const removeULO = (index: number) =>
    setScaffold(s => ({ ...s, ulos: s.ulos.filter((_, i) => i !== index) }));

  const addULO = () =>
    setScaffold(s => ({
      ...s,
      ulos: [
        ...s.ulos,
        {
          code: `ULO${s.ulos.length + 1}`,
          description: '',
          bloomLevel: 'understand',
        },
      ],
    }));

  // ─── Week helpers ────────────────────────────────────────────────────────
  const updateWeek = (index: number, topic: string) =>
    setScaffold(s => ({
      ...s,
      weeks: s.weeks.map((w, i) => (i === index ? { ...w, topic } : w)),
    }));

  // ─── Assessment helpers ──────────────────────────────────────────────────
  const updateAssessment = (
    index: number,
    field: keyof ScaffoldAssessment,
    value: string | number | null
  ) =>
    setScaffold(s => ({
      ...s,
      assessments: s.assessments.map((a, i) =>
        i === index ? { ...a, [field]: value } : a
      ),
    }));

  const removeAssessment = (index: number) =>
    setScaffold(s => ({
      ...s,
      assessments: s.assessments.filter((_, i) => i !== index),
    }));

  const addAssessment = () =>
    setScaffold(s => ({
      ...s,
      assessments: [
        ...s.assessments,
        { title: '', category: 'assignment', weight: 0, dueWeek: null },
      ],
    }));

  const totalWeight = scaffold.assessments.reduce(
    (sum, a) => sum + (a.weight || 0),
    0
  );

  return (
    <div className='bg-white border border-gray-200 rounded-lg shadow-sm'>
      {/* Header */}
      <div className='p-4 border-b border-gray-200 flex items-center justify-between'>
        <div className='flex items-center gap-2'>
          <Sparkles className='h-5 w-5 text-yellow-500' />
          <h3 className='text-lg font-semibold text-gray-900'>
            Review Generated Structure
          </h3>
        </div>
        <button
          onClick={onCancel}
          className='text-gray-400 hover:text-gray-600'
        >
          <X className='h-5 w-5' />
        </button>
      </div>

      <div className='p-4 space-y-6 max-h-[70vh] overflow-y-auto'>
        {/* Description */}
        <div>
          <label className='block text-sm font-medium text-gray-700 mb-1'>
            Description
          </label>
          <textarea
            value={scaffold.description}
            onChange={e =>
              setScaffold(s => ({ ...s, description: e.target.value }))
            }
            rows={2}
            className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg'
          />
        </div>

        {/* ULOs */}
        <div>
          <div className='flex items-center justify-between mb-2'>
            <h4 className='font-medium text-gray-800'>
              Learning Outcomes ({scaffold.ulos.length})
            </h4>
            <button
              onClick={addULO}
              className='text-blue-600 hover:text-blue-800 flex items-center text-sm'
            >
              <Plus className='w-4 h-4 mr-1' />
              Add
            </button>
          </div>
          <div className='space-y-2'>
            {scaffold.ulos.map((ulo, i) => (
              <div key={i} className='flex items-start gap-2'>
                <input
                  value={ulo.code}
                  onChange={e => updateULO(i, 'code', e.target.value)}
                  className='w-20 px-2 py-1.5 text-sm border border-gray-300 rounded-lg'
                />
                <input
                  value={ulo.description}
                  onChange={e => updateULO(i, 'description', e.target.value)}
                  className='flex-1 px-2 py-1.5 text-sm border border-gray-300 rounded-lg'
                  placeholder='Description...'
                />
                <select
                  value={ulo.bloomLevel}
                  onChange={e => updateULO(i, 'bloomLevel', e.target.value)}
                  className='w-28 px-2 py-1.5 text-sm border border-gray-300 rounded-lg'
                >
                  {[
                    { value: 'remember', label: 'remember' },
                    { value: 'understand', label: 'understand' },
                    { value: 'apply', label: 'apply' },
                    { value: 'analyze', label: 'analyse' },
                    { value: 'evaluate', label: 'evaluate' },
                    { value: 'create', label: 'create' },
                  ].map(lvl => (
                    <option key={lvl.value} value={lvl.value}>
                      {lvl.label}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => removeULO(i)}
                  className='text-red-400 hover:text-red-600 mt-1'
                >
                  <Trash2 className='w-4 h-4' />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Weekly Topics */}
        <div>
          <h4 className='font-medium text-gray-800 mb-2'>
            Topics ({scaffold.weeks.length} {topicLabel.toLowerCase()}s)
          </h4>
          <div className='space-y-2'>
            {scaffold.weeks.map((week, i) => (
              <div key={i} className='flex items-center gap-2'>
                <span className='text-sm text-gray-500 w-16'>
                  {topicLabel} {week.weekNumber}
                </span>
                <input
                  value={week.topic}
                  onChange={e => updateWeek(i, e.target.value)}
                  className='flex-1 px-2 py-1.5 text-sm border border-gray-300 rounded-lg'
                />
              </div>
            ))}
          </div>
        </div>

        {/* Assessments */}
        <div>
          <div className='flex items-center justify-between mb-2'>
            <h4 className='font-medium text-gray-800'>
              Assessments
              <span
                className={`ml-2 text-sm ${totalWeight === 100 ? 'text-green-600' : 'text-red-600'}`}
              >
                (Total: {totalWeight}%)
              </span>
            </h4>
            <button
              onClick={addAssessment}
              className='text-blue-600 hover:text-blue-800 flex items-center text-sm'
            >
              <Plus className='w-4 h-4 mr-1' />
              Add
            </button>
          </div>
          <div className='space-y-2'>
            {scaffold.assessments.map((asmt, i) => (
              <div key={i} className='flex items-center gap-2'>
                <input
                  value={asmt.title}
                  onChange={e => updateAssessment(i, 'title', e.target.value)}
                  className='flex-1 px-2 py-1.5 text-sm border border-gray-300 rounded-lg'
                  placeholder='Title'
                />
                <select
                  value={asmt.category}
                  onChange={e =>
                    updateAssessment(i, 'category', e.target.value)
                  }
                  className='w-28 px-2 py-1.5 text-sm border border-gray-300 rounded-lg'
                >
                  {[
                    'quiz',
                    'exam',
                    'assignment',
                    'project',
                    'presentation',
                    'report',
                  ].map(cat => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
                <input
                  type='number'
                  value={asmt.weight}
                  onChange={e =>
                    updateAssessment(i, 'weight', Number(e.target.value))
                  }
                  className='w-20 px-2 py-1.5 text-sm border border-gray-300 rounded-lg'
                  placeholder='%'
                />
                <button
                  onClick={() => removeAssessment(i)}
                  className='text-red-400 hover:text-red-600'
                >
                  <Trash2 className='w-4 h-4' />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className='p-4 border-t border-gray-200 flex justify-end gap-3'>
        <button
          onClick={onCancel}
          className='px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200'
        >
          Cancel
        </button>
        <button
          onClick={() => onAccept(scaffold)}
          disabled={accepting}
          className='px-4 py-2 text-sm text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2'
        >
          {accepting ? (
            <Loader2 className='h-4 w-4 animate-spin' />
          ) : (
            <CheckCircle className='h-4 w-4' />
          )}
          Accept & Create
        </button>
      </div>
    </div>
  );
};

export default UnitScaffoldReview;
