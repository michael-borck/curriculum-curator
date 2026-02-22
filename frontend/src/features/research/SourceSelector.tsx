import { useState, useEffect } from 'react';
import {
  PlusCircle,
  GitCompare,
  BookOpen,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { useUnitsStore } from '../../stores/unitsStore';
import type { SourceInput, ResearchAction } from '../../types/research';
import type { PedagogyType } from '../../types';

interface ScaffoldParams {
  unitTitle: string;
  unitDescription: string;
  durationWeeks: number;
  pedagogyStyle: string;
}

interface UnitPickerParams {
  unitId: string;
}

export type ActionParams =
  | { action: 'scaffold'; params: ScaffoldParams }
  | { action: 'compare'; params: UnitPickerParams }
  | { action: 'reading-list'; params: UnitPickerParams };

interface SourceSelectorProps {
  sources: SourceInput[];
  onAction: (actionParams: ActionParams) => void;
  loading?: boolean | undefined;
}

const PEDAGOGY_OPTIONS: { value: PedagogyType; label: string }[] = [
  { value: 'inquiry-based', label: 'Inquiry-Based' },
  { value: 'project-based', label: 'Project-Based' },
  { value: 'traditional', label: 'Traditional' },
  { value: 'collaborative', label: 'Collaborative' },
  { value: 'game-based', label: 'Game-Based' },
  { value: 'constructivist', label: 'Constructivist' },
  { value: 'problem-based', label: 'Problem-Based' },
  { value: 'experiential', label: 'Experiential' },
  { value: 'competency-based', label: 'Competency-Based' },
];

const SourceSelector = ({
  sources,
  onAction,
  loading,
}: SourceSelectorProps) => {
  const { units, fetchUnits } = useUnitsStore();
  const [selectedAction, setSelectedAction] = useState<ResearchAction | null>(
    null
  );

  // Scaffold form state
  const [scaffoldForm, setScaffoldForm] = useState<ScaffoldParams>({
    unitTitle: '',
    unitDescription: '',
    durationWeeks: 12,
    pedagogyStyle: 'mixed_approach',
  });

  // Unit picker state
  const [selectedUnitId, setSelectedUnitId] = useState('');

  useEffect(() => {
    fetchUnits();
  }, [fetchUnits]);

  const handleSubmit = () => {
    if (!selectedAction) return;

    if (selectedAction === 'scaffold') {
      if (!scaffoldForm.unitTitle.trim()) return;
      onAction({ action: 'scaffold', params: scaffoldForm });
    } else {
      if (!selectedUnitId) return;
      onAction({
        action: selectedAction,
        params: { unitId: selectedUnitId },
      });
    }
  };

  const canSubmit =
    selectedAction === 'scaffold'
      ? scaffoldForm.unitTitle.trim().length > 0
      : selectedUnitId.length > 0;

  return (
    <div className='space-y-6'>
      {/* Selected sources summary */}
      <div>
        <h3 className='text-sm font-medium text-gray-700 mb-2'>
          Selected Sources ({sources.length})
        </h3>
        <div className='flex flex-wrap gap-2'>
          {sources.map((s, i) => (
            <div
              key={i}
              className='flex items-center gap-1.5 px-3 py-1.5 bg-purple-50 text-purple-700 rounded-full text-sm'
            >
              <span className='truncate max-w-[200px]'>{s.title}</span>
              {s.url && (
                <a
                  href={s.url}
                  target='_blank'
                  rel='noreferrer'
                  className='text-purple-400 hover:text-purple-600'
                  onClick={e => e.stopPropagation()}
                >
                  <ExternalLink className='w-3 h-3' />
                </a>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Action buttons */}
      <div>
        <h3 className='text-sm font-medium text-gray-700 mb-3'>
          What would you like to do?
        </h3>
        <div className='grid grid-cols-1 md:grid-cols-3 gap-3'>
          <button
            onClick={() => setSelectedAction('scaffold')}
            className={`p-4 rounded-lg border-2 text-left transition ${
              selectedAction === 'scaffold'
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <PlusCircle
              className={`w-5 h-5 mb-2 ${selectedAction === 'scaffold' ? 'text-purple-600' : 'text-gray-400'}`}
            />
            <p className='font-medium text-sm'>Scaffold New Unit</p>
            <p className='text-xs text-gray-500 mt-1'>
              Generate a complete unit structure from these sources
            </p>
          </button>

          <button
            onClick={() => setSelectedAction('compare')}
            className={`p-4 rounded-lg border-2 text-left transition ${
              selectedAction === 'compare'
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <GitCompare
              className={`w-5 h-5 mb-2 ${selectedAction === 'compare' ? 'text-purple-600' : 'text-gray-400'}`}
            />
            <p className='font-medium text-sm'>Compare to Existing Unit</p>
            <p className='text-xs text-gray-500 mt-1'>
              Analyse coverage gaps and overlaps with a unit
            </p>
          </button>

          <button
            onClick={() => setSelectedAction('reading-list')}
            className={`p-4 rounded-lg border-2 text-left transition ${
              selectedAction === 'reading-list'
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <BookOpen
              className={`w-5 h-5 mb-2 ${selectedAction === 'reading-list' ? 'text-purple-600' : 'text-gray-400'}`}
            />
            <p className='font-medium text-sm'>Match Reading List</p>
            <p className='text-xs text-gray-500 mt-1'>
              Assign sources to unit weeks as reading materials
            </p>
          </button>
        </div>
      </div>

      {/* Action-specific form */}
      {selectedAction === 'scaffold' && (
        <div className='bg-gray-50 rounded-lg p-4 space-y-4'>
          <h4 className='font-medium text-sm'>New Unit Details</h4>
          <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Unit Title *
              </label>
              <input
                type='text'
                value={scaffoldForm.unitTitle}
                onChange={e =>
                  setScaffoldForm(f => ({ ...f, unitTitle: e.target.value }))
                }
                className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent'
                placeholder='e.g., Introduction to Data Science'
              />
            </div>
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Duration (weeks)
              </label>
              <input
                type='number'
                value={scaffoldForm.durationWeeks}
                onChange={e =>
                  setScaffoldForm(f => ({
                    ...f,
                    durationWeeks: parseInt(e.target.value) || 12,
                  }))
                }
                min={1}
                max={52}
                className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent'
              />
            </div>
          </div>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              Description
            </label>
            <textarea
              value={scaffoldForm.unitDescription}
              onChange={e =>
                setScaffoldForm(f => ({
                  ...f,
                  unitDescription: e.target.value,
                }))
              }
              rows={3}
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent'
              placeholder='Brief description of the unit...'
            />
          </div>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              Pedagogy Style
            </label>
            <select
              value={scaffoldForm.pedagogyStyle}
              onChange={e =>
                setScaffoldForm(f => ({
                  ...f,
                  pedagogyStyle: e.target.value,
                }))
              }
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent'
            >
              <option value='mixed_approach'>Mixed Approach</option>
              {PEDAGOGY_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {(selectedAction === 'compare' || selectedAction === 'reading-list') && (
        <div className='bg-gray-50 rounded-lg p-4'>
          <label className='block text-sm font-medium text-gray-700 mb-2'>
            Select Unit
          </label>
          {units.length === 0 ? (
            <p className='text-sm text-gray-500'>
              No units found. Create a unit first.
            </p>
          ) : (
            <select
              value={selectedUnitId}
              onChange={e => setSelectedUnitId(e.target.value)}
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent'
            >
              <option value=''>Choose a unit...</option>
              {units.map(u => (
                <option key={u.id} value={u.id}>
                  {u.code} — {u.title}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      {/* Submit */}
      {selectedAction && (
        <div className='flex justify-end'>
          <button
            onClick={handleSubmit}
            disabled={!canSubmit || loading}
            className='flex items-center gap-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition'
          >
            {loading ? (
              <>
                <span className='animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent' />
                Generating proposal...
              </>
            ) : (
              <>
                Continue
                <ChevronRight className='w-4 h-4' />
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default SourceSelector;
