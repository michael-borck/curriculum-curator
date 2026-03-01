import React, { useState } from 'react';
import {
  Plus,
  Trash2,
  GripVertical,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import {
  Rubric,
  RubricType,
  RubricLevel,
  RubricCriterion,
} from '../../types/unitStructure';
import { useConfirmDialog } from '../../components/ui';

interface RubricEditorProps {
  value: Rubric | undefined;
  onChange: (rubric: Rubric | undefined) => void;
  assessmentTitle: string;
  assessmentCategory: string;
}

const RUBRIC_TYPE_LABELS: Record<RubricType, string> = {
  [RubricType.ANALYTIC]: 'Analytic',
  [RubricType.SINGLE_POINT]: 'Single-Point',
  [RubricType.HOLISTIC]: 'Holistic',
  [RubricType.CHECKLIST]: 'Checklist',
};

const RUBRIC_TYPE_DESCRIPTIONS: Record<RubricType, string> = {
  [RubricType.ANALYTIC]:
    'Full grid with criteria rows and performance level columns',
  [RubricType.SINGLE_POINT]:
    'One proficient description per criterion, feedback columns either side',
  [RubricType.HOLISTIC]:
    'Overall performance levels with paragraph descriptions',
  [RubricType.CHECKLIST]: 'Simple met/not-met criteria list',
};

function defaultAnalytic(): Rubric {
  return {
    type: RubricType.ANALYTIC,
    levels: [
      { label: 'Excellent', points: 4, description: undefined },
      { label: 'Good', points: 3, description: undefined },
      { label: 'Satisfactory', points: 2, description: undefined },
      { label: 'Unsatisfactory', points: 0, description: undefined },
    ],
    criteria: [
      {
        name: 'Criterion 1',
        description: '',
        weight: 100,
        cells: ['', '', '', ''],
      },
    ],
    totalPoints: 100,
  };
}

function defaultSinglePoint(): Rubric {
  return {
    type: RubricType.SINGLE_POINT,
    levels: [{ label: 'Proficient', points: null, description: undefined }],
    criteria: [
      { name: 'Criterion 1', description: '', weight: 100, cells: [''] },
    ],
    totalPoints: 100,
  };
}

function defaultHolistic(): Rubric {
  return {
    type: RubricType.HOLISTIC,
    levels: [
      { label: 'Excellent', points: 4, description: '' },
      { label: 'Good', points: 3, description: '' },
      { label: 'Satisfactory', points: 2, description: '' },
      { label: 'Unsatisfactory', points: 0, description: '' },
    ],
    criteria: [],
    totalPoints: 100,
  };
}

function defaultChecklist(): Rubric {
  return {
    type: RubricType.CHECKLIST,
    levels: [
      { label: 'Met', points: 1, description: undefined },
      { label: 'Not Met', points: 0, description: undefined },
    ],
    criteria: [{ name: 'Criterion 1', description: '', weight: 0, cells: [] }],
    totalPoints: 100,
  };
}

function defaultForType(type: RubricType): Rubric {
  switch (type) {
    case RubricType.ANALYTIC:
      return defaultAnalytic();
    case RubricType.SINGLE_POINT:
      return defaultSinglePoint();
    case RubricType.HOLISTIC:
      return defaultHolistic();
    case RubricType.CHECKLIST:
      return defaultChecklist();
  }
}

function getRubricSummary(rubric: Rubric | undefined): string {
  if (!rubric) return 'No rubric';
  const label = RUBRIC_TYPE_LABELS[rubric.type] || rubric.type;
  if (rubric.type === RubricType.HOLISTIC) {
    return `${label}: ${rubric.levels.length} levels`;
  }
  return `${label}: ${rubric.criteria.length} criteria, ${rubric.levels.length} levels`;
}

// ---------------------------------------------------------------------------
// Sub-editors
// ---------------------------------------------------------------------------

const AnalyticEditor: React.FC<{
  rubric: Rubric;
  onChange: (r: Rubric) => void;
}> = ({ rubric, onChange }) => {
  const updateLevel = (
    idx: number,
    field: keyof RubricLevel,
    value: string | number | null
  ) => {
    const levels = [...rubric.levels];
    levels[idx] = { ...levels[idx], [field]: value };
    onChange({ ...rubric, levels });
  };

  const updateCriterion = (
    idx: number,
    field: keyof RubricCriterion,
    value: string | number | string[]
  ) => {
    const criteria = [...rubric.criteria];
    criteria[idx] = { ...criteria[idx], [field]: value };
    onChange({ ...rubric, criteria });
  };

  const updateCell = (criterionIdx: number, cellIdx: number, value: string) => {
    const criteria = [...rubric.criteria];
    const cells = [...criteria[criterionIdx].cells];
    cells[cellIdx] = value;
    criteria[criterionIdx] = { ...criteria[criterionIdx], cells };
    onChange({ ...rubric, criteria });
  };

  const addLevel = () => {
    const levels = [
      ...rubric.levels,
      { label: 'New Level', points: 0, description: undefined },
    ];
    const criteria = rubric.criteria.map(c => ({
      ...c,
      cells: [...c.cells, ''],
    }));
    onChange({ ...rubric, levels, criteria });
  };

  const removeLevel = (idx: number) => {
    if (rubric.levels.length <= 1) return;
    const levels = rubric.levels.filter((_, i) => i !== idx);
    const criteria = rubric.criteria.map(c => ({
      ...c,
      cells: c.cells.filter((_, i) => i !== idx),
    }));
    onChange({ ...rubric, levels, criteria });
  };

  const addCriterion = () => {
    const criteria = [
      ...rubric.criteria,
      {
        name: `Criterion ${rubric.criteria.length + 1}`,
        description: '',
        weight: 0,
        cells: rubric.levels.map(() => ''),
      },
    ];
    onChange({ ...rubric, criteria });
  };

  const removeCriterion = (idx: number) => {
    if (rubric.criteria.length <= 1) return;
    onChange({
      ...rubric,
      criteria: rubric.criteria.filter((_, i) => i !== idx),
    });
  };

  return (
    <div className='space-y-3'>
      <div className='overflow-x-auto'>
        <table className='min-w-full border-collapse text-sm'>
          <thead>
            <tr>
              <th className='border border-gray-300 bg-gray-50 px-3 py-2 text-left font-medium text-gray-700 w-40'>
                Criterion
              </th>
              <th className='border border-gray-300 bg-gray-50 px-2 py-2 text-center font-medium text-gray-700 w-16'>
                Weight %
              </th>
              {rubric.levels.map((level, li) => (
                <th
                  key={li}
                  className='border border-gray-300 bg-gray-50 px-2 py-1 text-center min-w-[140px]'
                >
                  <input
                    type='text'
                    value={level.label}
                    onChange={e => updateLevel(li, 'label', e.target.value)}
                    className='w-full text-center text-sm font-medium border-0 bg-transparent focus:ring-1 focus:ring-blue-400 rounded'
                  />
                  <div className='flex items-center justify-center gap-1 mt-1'>
                    <input
                      type='number'
                      value={level.points ?? ''}
                      onChange={e =>
                        updateLevel(
                          li,
                          'points',
                          e.target.value ? parseFloat(e.target.value) : null
                        )
                      }
                      className='w-14 text-center text-xs border border-gray-200 rounded px-1 py-0.5'
                      placeholder='pts'
                    />
                    {rubric.levels.length > 1 && (
                      <button
                        type='button'
                        onClick={() => removeLevel(li)}
                        className='text-gray-400 hover:text-red-500'
                        title='Remove level'
                      >
                        <Trash2 className='w-3 h-3' />
                      </button>
                    )}
                  </div>
                </th>
              ))}
              <th className='border border-gray-300 bg-gray-50 px-1 py-2 w-8'>
                <button
                  type='button'
                  onClick={addLevel}
                  className='text-blue-600 hover:text-blue-800'
                  title='Add level'
                >
                  <Plus className='w-4 h-4' />
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {rubric.criteria.map((criterion, ci) => (
              <tr key={ci}>
                <td className='border border-gray-300 px-2 py-1'>
                  <input
                    type='text'
                    value={criterion.name}
                    onChange={e => updateCriterion(ci, 'name', e.target.value)}
                    className='w-full text-sm border-0 bg-transparent focus:ring-1 focus:ring-blue-400 rounded font-medium'
                  />
                  <input
                    type='text'
                    value={criterion.description}
                    onChange={e =>
                      updateCriterion(ci, 'description', e.target.value)
                    }
                    className='w-full text-xs text-gray-500 border-0 bg-transparent focus:ring-1 focus:ring-blue-400 rounded mt-0.5'
                    placeholder='Description...'
                  />
                </td>
                <td className='border border-gray-300 px-1 py-1 text-center'>
                  <input
                    type='number'
                    value={criterion.weight}
                    onChange={e =>
                      updateCriterion(
                        ci,
                        'weight',
                        parseFloat(e.target.value) || 0
                      )
                    }
                    className='w-14 text-center text-sm border border-gray-200 rounded px-1 py-0.5'
                    min='0'
                    max='100'
                  />
                </td>
                {criterion.cells.map((cell, cellIdx) => (
                  <td
                    key={cellIdx}
                    className='border border-gray-300 px-1 py-1'
                  >
                    <textarea
                      value={cell}
                      onChange={e => updateCell(ci, cellIdx, e.target.value)}
                      className='w-full text-xs border-0 bg-transparent focus:ring-1 focus:ring-blue-400 rounded resize-none'
                      rows={3}
                      placeholder='Describe performance...'
                    />
                  </td>
                ))}
                <td className='border border-gray-300 px-1 py-1 text-center'>
                  {rubric.criteria.length > 1 && (
                    <button
                      type='button'
                      onClick={() => removeCriterion(ci)}
                      className='text-gray-400 hover:text-red-500'
                      title='Remove criterion'
                    >
                      <Trash2 className='w-3.5 h-3.5' />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button
        type='button'
        onClick={addCriterion}
        className='inline-flex items-center text-sm text-blue-600 hover:text-blue-800'
      >
        <Plus className='w-4 h-4 mr-1' /> Add Criterion
      </button>
    </div>
  );
};

const SinglePointEditor: React.FC<{
  rubric: Rubric;
  onChange: (r: Rubric) => void;
}> = ({ rubric, onChange }) => {
  const updateCriterion = (
    idx: number,
    field: keyof RubricCriterion,
    value: string | number | string[]
  ) => {
    const criteria = [...rubric.criteria];
    criteria[idx] = { ...criteria[idx], [field]: value };
    onChange({ ...rubric, criteria });
  };

  const updateCell = (idx: number, value: string) => {
    const criteria = [...rubric.criteria];
    criteria[idx] = { ...criteria[idx], cells: [value] };
    onChange({ ...rubric, criteria });
  };

  const addCriterion = () => {
    onChange({
      ...rubric,
      criteria: [
        ...rubric.criteria,
        {
          name: `Criterion ${rubric.criteria.length + 1}`,
          description: '',
          weight: 0,
          cells: [''],
        },
      ],
    });
  };

  const removeCriterion = (idx: number) => {
    if (rubric.criteria.length <= 1) return;
    onChange({
      ...rubric,
      criteria: rubric.criteria.filter((_, i) => i !== idx),
    });
  };

  return (
    <div className='space-y-3'>
      <div className='overflow-x-auto'>
        <table className='min-w-full border-collapse text-sm'>
          <thead>
            <tr>
              <th className='border border-gray-300 bg-yellow-50 px-3 py-2 text-center font-medium text-gray-600 w-1/4'>
                Concerns / Areas for Growth
              </th>
              <th className='border border-gray-300 bg-gray-50 px-3 py-2 text-left font-medium text-gray-700 w-1/4'>
                Criterion
              </th>
              <th className='border border-gray-300 bg-green-50 px-3 py-2 text-center font-medium text-gray-700 w-1/4'>
                Proficient
              </th>
              <th className='border border-gray-300 bg-blue-50 px-3 py-2 text-center font-medium text-gray-600 w-1/4'>
                Advanced / Exceeds
              </th>
              <th className='border border-gray-300 bg-gray-50 w-8' />
            </tr>
          </thead>
          <tbody>
            {rubric.criteria.map((criterion, ci) => (
              <tr key={ci}>
                <td className='border border-gray-300 bg-yellow-50/30 px-2 py-2 text-center text-xs text-gray-400 italic'>
                  Feedback area
                </td>
                <td className='border border-gray-300 px-2 py-1'>
                  <input
                    type='text'
                    value={criterion.name}
                    onChange={e => updateCriterion(ci, 'name', e.target.value)}
                    className='w-full text-sm border-0 bg-transparent focus:ring-1 focus:ring-blue-400 rounded font-medium'
                  />
                </td>
                <td className='border border-gray-300 bg-green-50/30 px-1 py-1'>
                  <textarea
                    value={criterion.cells[0] || ''}
                    onChange={e => updateCell(ci, e.target.value)}
                    className='w-full text-xs border-0 bg-transparent focus:ring-1 focus:ring-blue-400 rounded resize-none'
                    rows={3}
                    placeholder='Describe proficient performance...'
                  />
                </td>
                <td className='border border-gray-300 bg-blue-50/30 px-2 py-2 text-center text-xs text-gray-400 italic'>
                  Feedback area
                </td>
                <td className='border border-gray-300 px-1 py-1 text-center'>
                  {rubric.criteria.length > 1 && (
                    <button
                      type='button'
                      onClick={() => removeCriterion(ci)}
                      className='text-gray-400 hover:text-red-500'
                    >
                      <Trash2 className='w-3.5 h-3.5' />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button
        type='button'
        onClick={addCriterion}
        className='inline-flex items-center text-sm text-blue-600 hover:text-blue-800'
      >
        <Plus className='w-4 h-4 mr-1' /> Add Criterion
      </button>
    </div>
  );
};

const HolisticEditor: React.FC<{
  rubric: Rubric;
  onChange: (r: Rubric) => void;
}> = ({ rubric, onChange }) => {
  const updateLevel = (
    idx: number,
    field: keyof RubricLevel,
    value: string | number | null
  ) => {
    const levels = [...rubric.levels];
    levels[idx] = { ...levels[idx], [field]: value };
    onChange({ ...rubric, levels });
  };

  const addLevel = () => {
    onChange({
      ...rubric,
      levels: [
        ...rubric.levels,
        { label: 'New Level', points: 0, description: '' },
      ],
    });
  };

  const removeLevel = (idx: number) => {
    if (rubric.levels.length <= 1) return;
    onChange({ ...rubric, levels: rubric.levels.filter((_, i) => i !== idx) });
  };

  return (
    <div className='space-y-3'>
      {rubric.levels.map((level, li) => (
        <div
          key={li}
          className='border border-gray-200 rounded-lg p-3 bg-white'
        >
          <div className='flex items-center gap-3 mb-2'>
            <GripVertical className='w-4 h-4 text-gray-300' />
            <input
              type='text'
              value={level.label}
              onChange={e => updateLevel(li, 'label', e.target.value)}
              className='flex-1 text-sm font-medium border border-gray-200 rounded px-2 py-1 focus:ring-1 focus:ring-blue-400'
            />
            <div className='flex items-center gap-1'>
              <input
                type='number'
                value={level.points ?? ''}
                onChange={e =>
                  updateLevel(
                    li,
                    'points',
                    e.target.value ? parseFloat(e.target.value) : null
                  )
                }
                className='w-16 text-center text-sm border border-gray-200 rounded px-2 py-1'
                placeholder='pts'
              />
              <span className='text-xs text-gray-500'>pts</span>
            </div>
            {rubric.levels.length > 1 && (
              <button
                type='button'
                onClick={() => removeLevel(li)}
                className='text-gray-400 hover:text-red-500'
              >
                <Trash2 className='w-4 h-4' />
              </button>
            )}
          </div>
          <textarea
            value={level.description || ''}
            onChange={e => updateLevel(li, 'description', e.target.value)}
            className='w-full text-sm border border-gray-200 rounded px-2 py-1 focus:ring-1 focus:ring-blue-400 resize-none'
            rows={4}
            placeholder='Describe what performance at this level looks like...'
          />
        </div>
      ))}
      <button
        type='button'
        onClick={addLevel}
        className='inline-flex items-center text-sm text-blue-600 hover:text-blue-800'
      >
        <Plus className='w-4 h-4 mr-1' /> Add Level
      </button>
    </div>
  );
};

const ChecklistEditor: React.FC<{
  rubric: Rubric;
  onChange: (r: Rubric) => void;
}> = ({ rubric, onChange }) => {
  const updateCriterion = (
    idx: number,
    field: keyof RubricCriterion,
    value: string | number | string[]
  ) => {
    const criteria = [...rubric.criteria];
    criteria[idx] = { ...criteria[idx], [field]: value };
    onChange({ ...rubric, criteria });
  };

  const addCriterion = () => {
    onChange({
      ...rubric,
      criteria: [
        ...rubric.criteria,
        {
          name: `Criterion ${rubric.criteria.length + 1}`,
          description: '',
          weight: 0,
          cells: [],
        },
      ],
    });
  };

  const removeCriterion = (idx: number) => {
    if (rubric.criteria.length <= 1) return;
    onChange({
      ...rubric,
      criteria: rubric.criteria.filter((_, i) => i !== idx),
    });
  };

  return (
    <div className='space-y-2'>
      {rubric.criteria.map((criterion, ci) => (
        <div
          key={ci}
          className='flex items-start gap-2 border border-gray-200 rounded-lg p-3 bg-white'
        >
          <div className='pt-1'>
            <div className='w-5 h-5 border-2 border-gray-300 rounded bg-gray-50' />
          </div>
          <div className='flex-1 space-y-1'>
            <input
              type='text'
              value={criterion.name}
              onChange={e => updateCriterion(ci, 'name', e.target.value)}
              className='w-full text-sm font-medium border-0 bg-transparent focus:ring-1 focus:ring-blue-400 rounded'
            />
            <input
              type='text'
              value={criterion.description}
              onChange={e => updateCriterion(ci, 'description', e.target.value)}
              className='w-full text-xs text-gray-500 border-0 bg-transparent focus:ring-1 focus:ring-blue-400 rounded'
              placeholder='Optional description...'
            />
          </div>
          {rubric.criteria.length > 1 && (
            <button
              type='button'
              onClick={() => removeCriterion(ci)}
              className='text-gray-400 hover:text-red-500 pt-1'
            >
              <Trash2 className='w-3.5 h-3.5' />
            </button>
          )}
        </div>
      ))}
      <button
        type='button'
        onClick={addCriterion}
        className='inline-flex items-center text-sm text-blue-600 hover:text-blue-800'
      >
        <Plus className='w-4 h-4 mr-1' /> Add Criterion
      </button>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main RubricEditor
// ---------------------------------------------------------------------------

const RubricEditor: React.FC<RubricEditorProps> = ({ value, onChange }) => {
  const confirm = useConfirmDialog();
  const [expanded, setExpanded] = useState(false);

  const handleTypeChange = async (newType: RubricType) => {
    if (value && value.type !== newType) {
      const hasData =
        value.criteria.some(
          c => c.name !== '' && c.cells.some(cell => cell !== '')
        ) || value.levels.some(l => (l.description ?? '') !== '');
      if (hasData) {
        const ok = await confirm({
          title: 'Reset rubric?',
          message: 'Changing rubric type will reset the rubric. Continue?',
          confirmLabel: 'Continue',
          variant: 'warning',
        });
        if (!ok) return;
      }
    }
    onChange(defaultForType(newType));
    setExpanded(true);
  };

  const handleClear = async () => {
    if (value) {
      const ok = await confirm({
        title: 'Remove rubric?',
        message: 'Remove rubric from this assessment?',
        confirmLabel: 'Remove',
        variant: 'warning',
      });
      if (!ok) return;
    }
    onChange(undefined);
    setExpanded(false);
  };

  const summary = getRubricSummary(value);

  return (
    <div className='border border-gray-200 rounded-lg'>
      <button
        type='button'
        onClick={() => setExpanded(!expanded)}
        className='w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 rounded-lg'
      >
        <div className='flex items-center gap-2'>
          {expanded ? (
            <ChevronDown className='w-4 h-4 text-gray-500' />
          ) : (
            <ChevronRight className='w-4 h-4 text-gray-500' />
          )}
          <span className='text-sm font-medium text-gray-700'>Rubric</span>
          <span className='text-xs text-gray-500'>{summary}</span>
        </div>
        {value && (
          <span className='inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800'>
            {RUBRIC_TYPE_LABELS[value.type]}
          </span>
        )}
      </button>

      {expanded && (
        <div className='px-4 pb-4 space-y-4'>
          <div className='flex items-center gap-3'>
            <select
              value={value?.type || ''}
              onChange={e => handleTypeChange(e.target.value as RubricType)}
              className='text-sm rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            >
              {!value && <option value=''>Select rubric type...</option>}
              {Object.values(RubricType).map(t => (
                <option key={t} value={t}>
                  {RUBRIC_TYPE_LABELS[t]}
                </option>
              ))}
            </select>
            {value?.type && (
              <span className='text-xs text-gray-500'>
                {RUBRIC_TYPE_DESCRIPTIONS[value.type]}
              </span>
            )}
            {value && (
              <button
                type='button'
                onClick={handleClear}
                className='ml-auto text-xs text-red-500 hover:text-red-700'
              >
                Remove Rubric
              </button>
            )}
          </div>

          {value?.type && (
            <>
              <div className='flex items-center gap-3'>
                <label className='text-xs text-gray-600'>Total Points:</label>
                <input
                  type='number'
                  value={value.totalPoints}
                  onChange={e =>
                    onChange({
                      ...value,
                      totalPoints: parseFloat(e.target.value) || 0,
                    })
                  }
                  className='w-20 text-sm border border-gray-200 rounded px-2 py-1'
                  min='0'
                />
              </div>

              {value.type === RubricType.ANALYTIC && (
                <AnalyticEditor rubric={value} onChange={onChange} />
              )}
              {value.type === RubricType.SINGLE_POINT && (
                <SinglePointEditor rubric={value} onChange={onChange} />
              )}
              {value.type === RubricType.HOLISTIC && (
                <HolisticEditor rubric={value} onChange={onChange} />
              )}
              {value.type === RubricType.CHECKLIST && (
                <ChecklistEditor rubric={value} onChange={onChange} />
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default RubricEditor;
