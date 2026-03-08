import React, { useState } from 'react';
import {
  ArrowLeft,
  AlertTriangle,
  Trash2,
  Plus,
  ChevronDown,
  ChevronUp,
  BookOpen,
  CalendarDays,
  ClipboardList,
  Library,
  Info,
  CheckCircle,
} from 'lucide-react';
import type {
  OutlineParseResponse,
  OutlineApplyRequest,
  OutlineULO,
  OutlineWeek,
  OutlineAssessment,
  OutlineTextbook,
  OutlineSnippet,
} from '../../services/outlineImportApi';

const BLOOM_LEVELS = [
  'remember',
  'understand',
  'apply',
  'analyse',
  'evaluate',
  'create',
];

const SEMESTER_OPTIONS = [
  { value: 'semester_1', label: 'Semester 1' },
  { value: 'semester_2', label: 'Semester 2' },
  { value: 'summer', label: 'Summer' },
  { value: 'winter', label: 'Winter' },
];

interface Props {
  parseResult: OutlineParseResponse;
  onApply: (request: OutlineApplyRequest) => void;
  onBack: () => void;
}

export const OutlineReviewForm: React.FC<Props> = ({
  parseResult,
  onApply,
  onBack,
}) => {
  // --- Unit metadata ---
  const [unitCode, setUnitCode] = useState(parseResult.unitCode || '');
  const [unitTitle, setUnitTitle] = useState(parseResult.unitTitle || '');
  const [description, setDescription] = useState(parseResult.description || '');
  const [creditPoints, setCreditPoints] = useState(
    parseResult.creditPoints ?? 6
  );
  const [durationWeeks, setDurationWeeks] = useState(
    parseResult.durationWeeks ?? 12
  );
  const [year, setYear] = useState(
    parseResult.year ?? new Date().getFullYear()
  );
  const [semester, setSemester] = useState(
    parseResult.semester || 'semester_1'
  );
  const [prerequisites, setPrerequisites] = useState(
    parseResult.prerequisites || ''
  );
  const [deliveryMode, setDeliveryMode] = useState(
    parseResult.deliveryMode || ''
  );
  const [teachingPattern, setTeachingPattern] = useState(
    parseResult.teachingPattern || ''
  );

  // --- Structured data ---
  const [ulos, setUlos] = useState<OutlineULO[]>(
    parseResult.learningOutcomes.length > 0 ? parseResult.learningOutcomes : []
  );
  const [weeks, setWeeks] = useState<OutlineWeek[]>(
    parseResult.weeklySchedule.length > 0 ? parseResult.weeklySchedule : []
  );
  const [assessments, setAssessments] = useState<OutlineAssessment[]>(
    parseResult.assessments.length > 0 ? parseResult.assessments : []
  );
  const [textbooks, setTextbooks] = useState<OutlineTextbook[]>(
    parseResult.textbooks.length > 0 ? parseResult.textbooks : []
  );
  const [supplementary, setSupplementary] = useState<OutlineSnippet[]>(
    parseResult.supplementaryInfo.map(s => ({ ...s, keep: true }))
  );

  // --- Collapsed sections ---
  const [expandedSections, setExpandedSections] = useState<
    Record<string, boolean>
  >({
    details: true,
    ulos: true,
    schedule: true,
    assessments: true,
    textbooks: textbooks.length > 0,
    supplementary: supplementary.length > 0,
  });

  const toggleSection = (key: string) =>
    setExpandedSections(prev => ({ ...prev, [key]: !prev[key] }));

  // --- Validation ---
  const totalWeight = assessments.reduce((sum, a) => sum + a.weight, 0);
  const isValid = unitCode.trim().length > 0 && unitTitle.trim().length > 0;

  // --- Handlers ---
  const updateUlo = (index: number, field: keyof OutlineULO, value: string) => {
    setUlos(prev =>
      prev.map((u, i) => (i === index ? { ...u, [field]: value } : u))
    );
  };

  const removeUlo = (index: number) =>
    setUlos(prev => prev.filter((_, i) => i !== index));

  const addUlo = () =>
    setUlos(prev => [
      ...prev,
      {
        code: `ULO${prev.length + 1}`,
        description: '',
        bloomLevel: 'understand',
      },
    ]);

  const updateWeek = (
    index: number,
    field: keyof OutlineWeek,
    value: string | number
  ) => {
    setWeeks(prev =>
      prev.map((w, i) => (i === index ? { ...w, [field]: value } : w))
    );
  };

  const removeWeek = (index: number) =>
    setWeeks(prev => prev.filter((_, i) => i !== index));

  const addWeek = () =>
    setWeeks(prev => [
      ...prev,
      {
        weekNumber: prev.length > 0 ? prev[prev.length - 1].weekNumber + 1 : 1,
        topic: '',
        activities: [],
        readings: [],
      },
    ]);

  const updateAssessment = (
    index: number,
    field: keyof OutlineAssessment,
    value: string | number | null
  ) => {
    setAssessments(prev =>
      prev.map((a, i) => (i === index ? { ...a, [field]: value } : a))
    );
  };

  const removeAssessment = (index: number) =>
    setAssessments(prev => prev.filter((_, i) => i !== index));

  const addAssessment = () =>
    setAssessments(prev => [
      ...prev,
      {
        title: '',
        category: 'assignment',
        weight: 0,
        dueWeek: null,
        description: '',
      },
    ]);

  const updateTextbook = (
    index: number,
    field: keyof OutlineTextbook,
    value: string | boolean
  ) => {
    setTextbooks(prev =>
      prev.map((t, i) => (i === index ? { ...t, [field]: value } : t))
    );
  };

  const removeTextbook = (index: number) =>
    setTextbooks(prev => prev.filter((_, i) => i !== index));

  const toggleSupplementaryKeep = (index: number) => {
    setSupplementary(prev =>
      prev.map((s, i) => (i === index ? { ...s, keep: !s.keep } : s))
    );
  };

  const handleSubmit = () => {
    const request: OutlineApplyRequest = {
      unitCode,
      unitTitle,
      description,
      creditPoints,
      durationWeeks,
      year,
      semester,
      prerequisites,
      deliveryMode,
      teachingPattern,
      pedagogyType: 'mixed_approach',
      learningOutcomes: ulos.filter(u => u.description.trim()),
      weeklySchedule: weeks.filter(w => w.topic.trim()),
      assessments: assessments.filter(a => a.title.trim()),
      textbooks,
      supplementaryInfo: supplementary,
      parserUsed: parseResult.parserUsed,
    };
    onApply(request);
  };

  // --- Section header component ---
  const SectionHeader: React.FC<{
    sectionKey: string;
    icon: React.ReactNode;
    title: string;
    count?: number | undefined;
    badge?: React.ReactNode | undefined;
  }> = ({ sectionKey, icon, title, count, badge }) => (
    <button
      onClick={() => toggleSection(sectionKey)}
      className='w-full flex items-center justify-between py-3 px-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition'
    >
      <div className='flex items-center gap-2'>
        {icon}
        <span className='font-medium text-gray-900'>{title}</span>
        {count !== undefined && (
          <span className='text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full'>
            {count}
          </span>
        )}
        {badge}
      </div>
      {expandedSections[sectionKey] ? (
        <ChevronUp className='h-4 w-4 text-gray-400' />
      ) : (
        <ChevronDown className='h-4 w-4 text-gray-400' />
      )}
    </button>
  );

  return (
    <div className='space-y-6'>
      {/* Confidence + warnings banner */}
      <div className='flex items-center justify-between bg-gray-50 rounded-lg p-4'>
        <div className='flex items-center gap-3'>
          <CheckCircle className='h-5 w-5 text-green-500' />
          <div>
            <p className='text-sm font-medium text-gray-900'>
              Parsed with{' '}
              {parseResult.parserUsed === 'generic'
                ? 'Generic AI'
                : 'Curtin University'}{' '}
              parser
            </p>
            <p className='text-xs text-gray-500'>
              Confidence: {Math.round(parseResult.confidence * 100)}% — review
              and edit before creating
            </p>
          </div>
        </div>
        <button
          onClick={onBack}
          className='flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700'
        >
          <ArrowLeft className='h-4 w-4' />
          Re-upload
        </button>
      </div>

      {parseResult.warnings.length > 0 && (
        <div className='bg-amber-50 border border-amber-200 rounded-lg p-3'>
          {parseResult.warnings.map((w, i) => (
            <div
              key={i}
              className='flex items-start gap-2 text-sm text-amber-800'
            >
              <AlertTriangle className='h-4 w-4 flex-shrink-0 mt-0.5' />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}

      {/* Unit Details */}
      <div>
        <SectionHeader
          sectionKey='details'
          icon={<BookOpen className='h-4 w-4 text-purple-500' />}
          title='Unit Details'
        />
        {expandedSections.details && (
          <div className='mt-3 grid grid-cols-2 gap-4 px-1'>
            <div>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Unit Code *
              </label>
              <input
                value={unitCode}
                onChange={e => setUnitCode(e.target.value)}
                className='w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                placeholder='e.g. COMP1001'
              />
            </div>
            <div>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Title *
              </label>
              <input
                value={unitTitle}
                onChange={e => setUnitTitle(e.target.value)}
                className='w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                placeholder='e.g. Introduction to Programming'
              />
            </div>
            <div className='col-span-2'>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Description
              </label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={3}
                className='w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>
            <div>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Credit Points
              </label>
              <input
                type='number'
                value={creditPoints}
                onChange={e => setCreditPoints(parseInt(e.target.value) || 0)}
                min={0}
                max={100}
                className='w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>
            <div>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Duration (weeks)
              </label>
              <input
                type='number'
                value={durationWeeks}
                onChange={e => setDurationWeeks(parseInt(e.target.value) || 12)}
                min={1}
                max={52}
                className='w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>
            <div>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Year
              </label>
              <input
                type='number'
                value={year}
                onChange={e =>
                  setYear(parseInt(e.target.value) || new Date().getFullYear())
                }
                className='w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>
            <div>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Semester
              </label>
              <select
                value={semester}
                onChange={e => setSemester(e.target.value)}
                className='w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
              >
                {SEMESTER_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Delivery Mode
              </label>
              <input
                value={deliveryMode}
                onChange={e => setDeliveryMode(e.target.value)}
                className='w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                placeholder='e.g. Face-to-face, Online, Hybrid'
              />
            </div>
            <div>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Teaching Pattern
              </label>
              <input
                value={teachingPattern}
                onChange={e => setTeachingPattern(e.target.value)}
                className='w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                placeholder='e.g. 2hr lecture + 1hr tutorial'
              />
            </div>
            <div className='col-span-2'>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Prerequisites
              </label>
              <input
                value={prerequisites}
                onChange={e => setPrerequisites(e.target.value)}
                className='w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                placeholder='e.g. COMP1000 or equivalent'
              />
            </div>
          </div>
        )}
      </div>

      {/* Learning Outcomes */}
      <div>
        <SectionHeader
          sectionKey='ulos'
          icon={<BookOpen className='h-4 w-4 text-blue-500' />}
          title='Learning Outcomes'
          count={ulos.length}
        />
        {expandedSections.ulos && (
          <div className='mt-3 space-y-2 px-1'>
            {ulos.map((ulo, i) => (
              <div
                key={i}
                className='flex items-start gap-2 bg-white border border-gray-200 rounded-lg p-3'
              >
                <input
                  value={ulo.code}
                  onChange={e => updateUlo(i, 'code', e.target.value)}
                  className='w-20 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                  placeholder='ULO1'
                />
                <input
                  value={ulo.description}
                  onChange={e => updateUlo(i, 'description', e.target.value)}
                  className='flex-1 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                  placeholder='Outcome description...'
                />
                <select
                  value={ulo.bloomLevel}
                  onChange={e => updateUlo(i, 'bloomLevel', e.target.value)}
                  className='w-28 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                >
                  {BLOOM_LEVELS.map(level => (
                    <option key={level} value={level}>
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => removeUlo(i)}
                  className='text-gray-400 hover:text-red-500 p-1'
                  title='Remove'
                >
                  <Trash2 className='h-4 w-4' />
                </button>
              </div>
            ))}
            <button
              onClick={addUlo}
              className='flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700 px-3 py-1.5'
            >
              <Plus className='h-4 w-4' />
              Add Outcome
            </button>
          </div>
        )}
      </div>

      {/* Weekly Schedule */}
      <div>
        <SectionHeader
          sectionKey='schedule'
          icon={<CalendarDays className='h-4 w-4 text-green-500' />}
          title='Weekly Schedule'
          count={weeks.length}
        />
        {expandedSections.schedule && (
          <div className='mt-3 space-y-2 px-1'>
            {weeks.map((week, i) => (
              <div
                key={i}
                className='flex items-center gap-2 bg-white border border-gray-200 rounded-lg p-3'
              >
                <span className='text-sm font-medium text-gray-500 w-14 flex-shrink-0'>
                  Wk {week.weekNumber}
                </span>
                <input
                  value={week.topic}
                  onChange={e => updateWeek(i, 'topic', e.target.value)}
                  className='flex-1 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                  placeholder='Topic title...'
                />
                <button
                  onClick={() => removeWeek(i)}
                  className='text-gray-400 hover:text-red-500 p-1'
                  title='Remove'
                >
                  <Trash2 className='h-4 w-4' />
                </button>
              </div>
            ))}
            <button
              onClick={addWeek}
              className='flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700 px-3 py-1.5'
            >
              <Plus className='h-4 w-4' />
              Add Week
            </button>
          </div>
        )}
      </div>

      {/* Assessments */}
      <div>
        <SectionHeader
          sectionKey='assessments'
          icon={<ClipboardList className='h-4 w-4 text-orange-500' />}
          title='Assessments'
          count={assessments.length}
          badge={
            assessments.length > 0 && Math.abs(totalWeight - 100) > 0.5 ? (
              <span className='text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full flex items-center gap-1'>
                <AlertTriangle className='h-3 w-3' />
                {totalWeight.toFixed(0)}%
              </span>
            ) : assessments.length > 0 ? (
              <span className='text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full'>
                100%
              </span>
            ) : undefined
          }
        />
        {expandedSections.assessments && (
          <div className='mt-3 space-y-2 px-1'>
            {assessments.map((a, i) => (
              <div
                key={i}
                className='flex items-center gap-2 bg-white border border-gray-200 rounded-lg p-3'
              >
                <input
                  value={a.title}
                  onChange={e => updateAssessment(i, 'title', e.target.value)}
                  className='flex-1 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                  placeholder='Assessment title...'
                />
                <input
                  value={a.category}
                  onChange={e =>
                    updateAssessment(i, 'category', e.target.value)
                  }
                  className='w-28 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                  placeholder='Category'
                />
                <div className='flex items-center gap-1'>
                  <input
                    type='number'
                    value={a.weight}
                    onChange={e =>
                      updateAssessment(
                        i,
                        'weight',
                        parseFloat(e.target.value) || 0
                      )
                    }
                    min={0}
                    max={100}
                    className='w-16 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 text-right'
                  />
                  <span className='text-sm text-gray-500'>%</span>
                </div>
                <div className='flex items-center gap-1'>
                  <span className='text-xs text-gray-500'>Wk</span>
                  <input
                    type='number'
                    value={a.dueWeek ?? ''}
                    onChange={e =>
                      updateAssessment(
                        i,
                        'dueWeek',
                        e.target.value ? parseInt(e.target.value) : null
                      )
                    }
                    min={1}
                    max={52}
                    className='w-14 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                    placeholder='-'
                  />
                </div>
                <button
                  onClick={() => removeAssessment(i)}
                  className='text-gray-400 hover:text-red-500 p-1'
                  title='Remove'
                >
                  <Trash2 className='h-4 w-4' />
                </button>
              </div>
            ))}
            <button
              onClick={addAssessment}
              className='flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700 px-3 py-1.5'
            >
              <Plus className='h-4 w-4' />
              Add Assessment
            </button>
          </div>
        )}
      </div>

      {/* Textbooks */}
      {(textbooks.length > 0 || expandedSections.textbooks) && (
        <div>
          <SectionHeader
            sectionKey='textbooks'
            icon={<Library className='h-4 w-4 text-teal-500' />}
            title='Textbooks'
            count={textbooks.length}
          />
          {expandedSections.textbooks && (
            <div className='mt-3 space-y-2 px-1'>
              {textbooks.map((t, i) => (
                <div
                  key={i}
                  className='flex items-center gap-2 bg-white border border-gray-200 rounded-lg p-3'
                >
                  <input
                    value={t.title}
                    onChange={e => updateTextbook(i, 'title', e.target.value)}
                    className='flex-1 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                    placeholder='Textbook title...'
                  />
                  <input
                    value={t.authors}
                    onChange={e => updateTextbook(i, 'authors', e.target.value)}
                    className='w-40 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
                    placeholder='Authors'
                  />
                  <label className='flex items-center gap-1 text-xs text-gray-600 cursor-pointer'>
                    <input
                      type='checkbox'
                      checked={t.required}
                      onChange={e =>
                        updateTextbook(i, 'required', e.target.checked)
                      }
                      className='rounded border-gray-300 text-purple-600 focus:ring-purple-500'
                    />
                    Required
                  </label>
                  <button
                    onClick={() => removeTextbook(i)}
                    className='text-gray-400 hover:text-red-500 p-1'
                    title='Remove'
                  >
                    <Trash2 className='h-4 w-4' />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Supplementary Info */}
      {supplementary.length > 0 && (
        <div>
          <SectionHeader
            sectionKey='supplementary'
            icon={<Info className='h-4 w-4 text-gray-500' />}
            title='Supplementary Info'
            count={supplementary.filter(s => s.keep).length}
          />
          {expandedSections.supplementary && (
            <div className='mt-3 space-y-2 px-1'>
              <p className='text-xs text-gray-500 px-1 mb-2'>
                Content that doesn&apos;t map to unit structure. Toggle to keep
                as reference notes or drop.
              </p>
              {supplementary.map((s, i) => (
                <div
                  key={i}
                  className={`border rounded-lg p-3 transition ${
                    s.keep
                      ? 'border-gray-200 bg-white'
                      : 'border-gray-100 bg-gray-50 opacity-60'
                  }`}
                >
                  <div className='flex items-center justify-between mb-1'>
                    <span className='text-sm font-medium text-gray-700'>
                      {s.heading}
                    </span>
                    <button
                      onClick={() => toggleSupplementaryKeep(i)}
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        s.keep
                          ? 'bg-green-100 text-green-700 hover:bg-green-200'
                          : 'bg-gray-200 text-gray-500 hover:bg-gray-300'
                      }`}
                    >
                      {s.keep ? 'Keep' : 'Dropped'}
                    </button>
                  </div>
                  <p className='text-xs text-gray-600 line-clamp-3'>
                    {s.content}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Action bar */}
      <div className='flex items-center justify-between pt-4 border-t'>
        <button
          onClick={onBack}
          className='px-4 py-2 text-sm text-gray-600 hover:text-gray-800'
        >
          Cancel
        </button>
        <div className='flex items-center gap-3'>
          {!isValid && (
            <span className='text-xs text-amber-600'>
              Unit code and title are required
            </span>
          )}
          <button
            onClick={handleSubmit}
            disabled={!isValid}
            className='px-6 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium text-sm transition disabled:opacity-50 disabled:cursor-not-allowed'
          >
            Create Unit
          </button>
        </div>
      </div>
    </div>
  );
};
