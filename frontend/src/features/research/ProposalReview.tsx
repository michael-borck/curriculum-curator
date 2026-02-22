import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useAsyncAction } from '../../hooks/useAsyncAction';
import { useWorkingContextStore } from '../../stores/workingContextStore';
import * as researchApi from '../../services/researchApi';
import type {
  ScaffoldUnitResponse,
  ScaffoldULO,
  ScaffoldWeek,
  ScaffoldAssessment,
  ComparisonProposal,
  ReadingListProposal,
  ResourceMatch,
  ResearchAction,
} from '../../types/research';

// =============================================================================
// Scaffold Review
// =============================================================================

interface ScaffoldReviewProps {
  proposal: ScaffoldUnitResponse;
  onDone: () => void;
}

const BLOOM_LEVELS = [
  'Remember',
  'Understand',
  'Apply',
  'Analyse',
  'Evaluate',
  'Create',
];

const ScaffoldReview = ({ proposal, onDone }: ScaffoldReviewProps) => {
  const navigate = useNavigate();
  const topicLabel = useWorkingContextStore(s => s.activeTopicLabel) || 'Week';
  const [title, setTitle] = useState(proposal.title);
  const [description, setDescription] = useState(proposal.description);
  const [ulos, setUlos] = useState<ScaffoldULO[]>(proposal.ulos);
  const [weeks, setWeeks] = useState<ScaffoldWeek[]>(proposal.weeks);
  const [assessments, setAssessments] = useState<ScaffoldAssessment[]>(
    proposal.assessments
  );

  const { execute, loading, error } = useAsyncAction(
    async () => {
      const result = await researchApi.applyScaffold({
        proposal: { title, description, ulos, weeks, assessments },
      });
      return result;
    },
    {
      onSuccess: result => {
        if (result.unitId) {
          navigate(`/units/${result.unitId}`);
        }
        onDone();
      },
    }
  );

  const updateUlo = (idx: number, field: keyof ScaffoldULO, value: string) => {
    setUlos(prev =>
      prev.map((u, i) => (i === idx ? { ...u, [field]: value } : u))
    );
  };

  const updateWeek = (
    idx: number,
    field: keyof ScaffoldWeek,
    value: string | string[]
  ) => {
    setWeeks(prev =>
      prev.map((w, i) => (i === idx ? { ...w, [field]: value } : w))
    );
  };

  const updateAssessment = (
    idx: number,
    field: keyof ScaffoldAssessment,
    value: string | number
  ) => {
    setAssessments(prev =>
      prev.map((a, i) => (i === idx ? { ...a, [field]: value } : a))
    );
  };

  return (
    <div className='space-y-6'>
      <h3 className='text-lg font-semibold'>Review Scaffolded Unit</h3>

      {error && (
        <div className='p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2'>
          <AlertCircle className='w-5 h-5 text-red-600 mt-0.5 flex-shrink-0' />
          <span className='text-sm text-red-800'>{error}</span>
        </div>
      )}

      {/* Title & Description */}
      <div className='grid grid-cols-1 gap-4'>
        <div>
          <label className='block text-sm font-medium text-gray-700 mb-1'>
            Title
          </label>
          <input
            type='text'
            value={title}
            onChange={e => setTitle(e.target.value)}
            className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
          />
        </div>
        <div>
          <label className='block text-sm font-medium text-gray-700 mb-1'>
            Description
          </label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={3}
            className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
          />
        </div>
      </div>

      {/* ULOs */}
      <div>
        <h4 className='font-medium text-sm mb-2'>
          Unit Learning Outcomes ({ulos.length})
        </h4>
        <div className='border rounded-lg overflow-hidden'>
          <table className='w-full text-sm'>
            <thead className='bg-gray-50'>
              <tr>
                <th className='px-3 py-2 text-left font-medium text-gray-600'>
                  Code
                </th>
                <th className='px-3 py-2 text-left font-medium text-gray-600'>
                  Description
                </th>
                <th className='px-3 py-2 text-left font-medium text-gray-600 w-36'>
                  Bloom Level
                </th>
              </tr>
            </thead>
            <tbody className='divide-y'>
              {ulos.map((ulo, i) => (
                <tr key={i}>
                  <td className='px-3 py-2'>
                    <input
                      type='text'
                      value={ulo.code}
                      onChange={e => updateUlo(i, 'code', e.target.value)}
                      className='w-20 px-2 py-1 border border-gray-200 rounded text-sm'
                    />
                  </td>
                  <td className='px-3 py-2'>
                    <input
                      type='text'
                      value={ulo.description}
                      onChange={e =>
                        updateUlo(i, 'description', e.target.value)
                      }
                      className='w-full px-2 py-1 border border-gray-200 rounded text-sm'
                    />
                  </td>
                  <td className='px-3 py-2'>
                    <select
                      value={ulo.bloomLevel}
                      onChange={e => updateUlo(i, 'bloomLevel', e.target.value)}
                      className='w-full px-2 py-1 border border-gray-200 rounded text-sm'
                    >
                      {BLOOM_LEVELS.map(level => (
                        <option key={level} value={level}>
                          {level}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Weeks */}
      <div>
        <h4 className='font-medium text-sm mb-2'>
          Weekly Topics ({weeks.length})
        </h4>
        <div className='border rounded-lg overflow-hidden'>
          <table className='w-full text-sm'>
            <thead className='bg-gray-50'>
              <tr>
                <th className='px-3 py-2 text-left font-medium text-gray-600 w-16'>
                  {topicLabel}
                </th>
                <th className='px-3 py-2 text-left font-medium text-gray-600'>
                  Topic
                </th>
                <th className='px-3 py-2 text-left font-medium text-gray-600'>
                  Activities
                </th>
              </tr>
            </thead>
            <tbody className='divide-y'>
              {weeks.map((week, i) => (
                <tr key={i}>
                  <td className='px-3 py-2 text-gray-500'>{week.weekNumber}</td>
                  <td className='px-3 py-2'>
                    <input
                      type='text'
                      value={week.topic}
                      onChange={e => updateWeek(i, 'topic', e.target.value)}
                      className='w-full px-2 py-1 border border-gray-200 rounded text-sm'
                    />
                  </td>
                  <td className='px-3 py-2'>
                    <input
                      type='text'
                      value={week.activities.join(', ')}
                      onChange={e =>
                        updateWeek(
                          i,
                          'activities',
                          e.target.value.split(',').map(s => s.trim())
                        )
                      }
                      className='w-full px-2 py-1 border border-gray-200 rounded text-sm'
                      placeholder='Comma-separated activities'
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Assessments */}
      <div>
        <h4 className='font-medium text-sm mb-2'>
          Assessments ({assessments.length})
        </h4>
        <div className='border rounded-lg overflow-hidden'>
          <table className='w-full text-sm'>
            <thead className='bg-gray-50'>
              <tr>
                <th className='px-3 py-2 text-left font-medium text-gray-600'>
                  Title
                </th>
                <th className='px-3 py-2 text-left font-medium text-gray-600 w-32'>
                  Category
                </th>
                <th className='px-3 py-2 text-left font-medium text-gray-600 w-20'>
                  Weight %
                </th>
                <th className='px-3 py-2 text-left font-medium text-gray-600 w-20'>
                  Due Week
                </th>
              </tr>
            </thead>
            <tbody className='divide-y'>
              {assessments.map((a, i) => (
                <tr key={i}>
                  <td className='px-3 py-2'>
                    <input
                      type='text'
                      value={a.title}
                      onChange={e =>
                        updateAssessment(i, 'title', e.target.value)
                      }
                      className='w-full px-2 py-1 border border-gray-200 rounded text-sm'
                    />
                  </td>
                  <td className='px-3 py-2'>
                    <input
                      type='text'
                      value={a.category}
                      onChange={e =>
                        updateAssessment(i, 'category', e.target.value)
                      }
                      className='w-full px-2 py-1 border border-gray-200 rounded text-sm'
                    />
                  </td>
                  <td className='px-3 py-2'>
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
                      className='w-full px-2 py-1 border border-gray-200 rounded text-sm'
                    />
                  </td>
                  <td className='px-3 py-2'>
                    <input
                      type='number'
                      value={a.dueWeek ?? ''}
                      onChange={e =>
                        updateAssessment(
                          i,
                          'dueWeek',
                          parseInt(e.target.value) || 0
                        )
                      }
                      min={1}
                      className='w-full px-2 py-1 border border-gray-200 rounded text-sm'
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className='flex justify-end'>
        <button
          onClick={() => execute()}
          disabled={loading}
          className='flex items-center gap-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition'
        >
          {loading ? (
            <Loader2 className='w-4 h-4 animate-spin' />
          ) : (
            <CheckCircle className='w-4 h-4' />
          )}
          {loading ? 'Creating Unit...' : 'Create Unit'}
        </button>
      </div>
    </div>
  );
};

// =============================================================================
// Comparison Review
// =============================================================================

interface ComparisonReviewProps {
  proposal: ComparisonProposal;
  onDone: () => void;
}

const COVERAGE_COLORS: Record<string, string> = {
  well_covered: 'bg-green-100 text-green-800',
  partially_covered: 'bg-yellow-100 text-yellow-800',
  not_covered: 'bg-red-100 text-red-800',
};

const COVERAGE_LABELS: Record<string, string> = {
  well_covered: 'Well Covered',
  partially_covered: 'Partially Covered',
  not_covered: 'Not Covered',
};

const ComparisonReview = ({ proposal, onDone }: ComparisonReviewProps) => {
  const topicLabel = useWorkingContextStore(s => s.activeTopicLabel) || 'Week';
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<number>>(
    () => new Set(proposal.suggestions.map((_, i) => i))
  );

  const { execute, loading, error, success } = useAsyncAction(
    async () => {
      return researchApi.applyComparison({
        proposal,
        selectedSuggestions: [...selectedSuggestions],
      });
    },
    { onSuccess: () => onDone() }
  );

  const toggleSuggestion = (idx: number) => {
    setSelectedSuggestions(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  return (
    <div className='space-y-6'>
      <h3 className='text-lg font-semibold'>Comparison Analysis</h3>

      {error && (
        <div className='p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2'>
          <AlertCircle className='w-5 h-5 text-red-600 mt-0.5 flex-shrink-0' />
          <span className='text-sm text-red-800'>{error}</span>
        </div>
      )}

      {success && (
        <div className='p-3 bg-green-50 border border-green-200 rounded-lg flex items-start gap-2'>
          <CheckCircle className='w-5 h-5 text-green-600 mt-0.5 flex-shrink-0' />
          <span className='text-sm text-green-800'>
            Suggestions applied successfully.
          </span>
        </div>
      )}

      {/* Weekly coverage table */}
      <div>
        <h4 className='font-medium text-sm mb-2'>{topicLabel} Coverage</h4>
        <div className='border rounded-lg overflow-hidden'>
          <table className='w-full text-sm'>
            <thead className='bg-gray-50'>
              <tr>
                <th className='px-3 py-2 text-left font-medium text-gray-600 w-16'>
                  {topicLabel}
                </th>
                <th className='px-3 py-2 text-left font-medium text-gray-600'>
                  Topic
                </th>
                <th className='px-3 py-2 text-left font-medium text-gray-600 w-40'>
                  Coverage
                </th>
                <th className='px-3 py-2 text-left font-medium text-gray-600'>
                  Matching Sources
                </th>
              </tr>
            </thead>
            <tbody className='divide-y'>
              {proposal.weeks.map(week => (
                <tr key={week.weekNumber}>
                  <td className='px-3 py-2 text-gray-500'>{week.weekNumber}</td>
                  <td className='px-3 py-2'>{week.topic}</td>
                  <td className='px-3 py-2'>
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${COVERAGE_COLORS[week.coverage] ?? 'bg-gray-100 text-gray-800'}`}
                    >
                      {COVERAGE_LABELS[week.coverage] ?? week.coverage}
                    </span>
                  </td>
                  <td className='px-3 py-2 text-gray-500 text-xs'>
                    {week.matchingSources.length > 0
                      ? week.matchingSources.join(', ')
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Gaps */}
      {proposal.gaps.length > 0 && (
        <div>
          <h4 className='font-medium text-sm mb-2'>Gaps</h4>
          <ul className='list-disc list-inside text-sm text-gray-700 space-y-1'>
            {proposal.gaps.map((gap, i) => (
              <li key={i}>{gap}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Overlaps */}
      {proposal.overlaps.length > 0 && (
        <div>
          <h4 className='font-medium text-sm mb-2'>Overlaps</h4>
          <ul className='list-disc list-inside text-sm text-gray-700 space-y-1'>
            {proposal.overlaps.map((overlap, i) => (
              <li key={i}>{overlap}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggestions with checkboxes */}
      {proposal.suggestions.length > 0 && (
        <div>
          <h4 className='font-medium text-sm mb-2'>Suggestions</h4>
          <div className='space-y-2'>
            {proposal.suggestions.map((suggestion, i) => (
              <label
                key={i}
                className='flex items-start gap-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer'
              >
                <input
                  type='checkbox'
                  checked={selectedSuggestions.has(i)}
                  onChange={() => toggleSuggestion(i)}
                  className='mt-0.5 h-4 w-4 text-purple-600 rounded border-gray-300'
                />
                <span className='text-sm'>{suggestion}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {!success && proposal.suggestions.length > 0 && (
        <div className='flex justify-end'>
          <button
            onClick={() => execute()}
            disabled={loading || selectedSuggestions.size === 0}
            className='flex items-center gap-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition'
          >
            {loading ? (
              <Loader2 className='w-4 h-4 animate-spin' />
            ) : (
              <CheckCircle className='w-4 h-4' />
            )}
            {loading
              ? 'Applying...'
              : `Apply ${selectedSuggestions.size} Suggestion${selectedSuggestions.size !== 1 ? 's' : ''}`}
          </button>
        </div>
      )}
    </div>
  );
};

// =============================================================================
// Reading List Review
// =============================================================================

interface ReadingListReviewProps {
  proposal: ReadingListProposal;
  onDone: () => void;
}

const confidenceColor = (c: number): string => {
  if (c >= 0.7) return 'text-green-600 bg-green-50';
  if (c >= 0.4) return 'text-yellow-600 bg-yellow-50';
  return 'text-red-600 bg-red-50';
};

const ReadingListReview = ({ proposal, onDone }: ReadingListReviewProps) => {
  const topicLabel = useWorkingContextStore(s => s.activeTopicLabel) || 'Week';
  const [matches, setMatches] = useState<ResourceMatch[]>(proposal.matches);
  const [saveAsSources, setSaveAsSources] = useState(true);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const { execute, loading, error, success } = useAsyncAction(
    async () => {
      return researchApi.applyReadingList({
        proposal: { ...proposal, matches },
        saveAsSources,
      });
    },
    { onSuccess: () => onDone() }
  );

  const updateMatch = (idx: number, updates: Partial<ResourceMatch>) => {
    setMatches(prev =>
      prev.map((m, i) => (i === idx ? { ...m, ...updates } : m))
    );
  };

  const weekOptions = proposal.unitWeeks;

  return (
    <div className='space-y-6'>
      <div className='flex items-center justify-between'>
        <h3 className='text-lg font-semibold'>Reading List Matching</h3>
        <span className='text-sm text-gray-500'>
          Avg confidence:{' '}
          <span className='font-medium'>
            {(proposal.avgConfidence * 100).toFixed(0)}%
          </span>
        </span>
      </div>

      {error && (
        <div className='p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2'>
          <AlertCircle className='w-5 h-5 text-red-600 mt-0.5 flex-shrink-0' />
          <span className='text-sm text-red-800'>{error}</span>
        </div>
      )}

      {success && (
        <div className='p-3 bg-green-50 border border-green-200 rounded-lg flex items-start gap-2'>
          <CheckCircle className='w-5 h-5 text-green-600 mt-0.5 flex-shrink-0' />
          <span className='text-sm text-green-800'>
            Reading list applied successfully.
          </span>
        </div>
      )}

      {/* Matched resources */}
      <div className='space-y-3'>
        {matches.map((match, i) => (
          <div
            key={i}
            className={`border rounded-lg overflow-hidden ${match.skipped ? 'opacity-60' : ''}`}
          >
            <div className='flex items-center gap-3 p-3'>
              <div className='flex-1 min-w-0'>
                <p className='font-medium text-sm truncate'>{match.title}</p>
                <a
                  href={match.url}
                  target='_blank'
                  rel='noreferrer'
                  className='text-xs text-blue-600 hover:underline truncate block'
                >
                  {match.url}
                </a>
              </div>

              <span
                className={`text-xs font-medium px-2 py-0.5 rounded ${confidenceColor(match.confidence)}`}
              >
                {(match.confidence * 100).toFixed(0)}%
              </span>

              <select
                value={
                  match.skipped
                    ? 'skip'
                    : String(match.assignedWeek ?? match.suggestedWeek)
                }
                onChange={e => {
                  if (e.target.value === 'skip') {
                    updateMatch(i, { skipped: true, assignedWeek: undefined });
                  } else {
                    updateMatch(i, {
                      skipped: false,
                      assignedWeek: parseInt(e.target.value),
                    });
                  }
                }}
                className='px-2 py-1 border border-gray-200 rounded text-sm w-36'
              >
                {weekOptions.map(w => (
                  <option key={w.weekNumber} value={String(w.weekNumber)}>
                    {topicLabel} {w.weekNumber}
                  </option>
                ))}
                <option value='skip'>Skip</option>
              </select>

              <button
                onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}
                className='p-1 text-gray-400 hover:text-gray-600'
              >
                {expandedIdx === i ? (
                  <ChevronUp className='w-4 h-4' />
                ) : (
                  <ChevronDown className='w-4 h-4' />
                )}
              </button>
            </div>

            {expandedIdx === i && (
              <div className='px-3 pb-3 border-t bg-gray-50'>
                <p className='text-xs text-gray-600 mt-2'>
                  <span className='font-medium'>AI reasoning:</span>{' '}
                  {match.reasoning}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Options & Apply */}
      {!success && (
        <div className='flex items-center justify-between'>
          <label className='flex items-center gap-2 text-sm'>
            <input
              type='checkbox'
              checked={saveAsSources}
              onChange={e => setSaveAsSources(e.target.checked)}
              className='h-4 w-4 text-purple-600 rounded border-gray-300'
            />
            Save as research sources
          </label>

          <button
            onClick={() => execute()}
            disabled={loading}
            className='flex items-center gap-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition'
          >
            {loading ? (
              <Loader2 className='w-4 h-4 animate-spin' />
            ) : (
              <CheckCircle className='w-4 h-4' />
            )}
            {loading ? 'Applying...' : 'Apply Reading List'}
          </button>
        </div>
      )}
    </div>
  );
};

// =============================================================================
// Main ProposalReview dispatcher
// =============================================================================

interface ProposalReviewProps {
  action: ResearchAction;
  proposal: ScaffoldUnitResponse | ComparisonProposal | ReadingListProposal;
  onDone: () => void;
}

const ProposalReview = ({ action, proposal, onDone }: ProposalReviewProps) => {
  switch (action) {
    case 'scaffold':
      return (
        <ScaffoldReview
          proposal={proposal as ScaffoldUnitResponse}
          onDone={onDone}
        />
      );
    case 'compare':
      return (
        <ComparisonReview
          proposal={proposal as ComparisonProposal}
          onDone={onDone}
        />
      );
    case 'reading-list':
      return (
        <ReadingListReview
          proposal={proposal as ReadingListProposal}
          onDone={onDone}
        />
      );
  }
};

export default ProposalReview;
