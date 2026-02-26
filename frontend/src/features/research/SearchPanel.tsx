import { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Loader2,
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Users,
  Calendar,
  Quote,
  Award,
} from 'lucide-react';
import * as researchApi from '../../services/researchApi';
import SourceSelector from './SourceSelector';
import ProposalReview from './ProposalReview';
import type { ActionParams } from './SourceSelector';
import type {
  AcademicSearchResultItem,
  TierInfo,
  SourceInput,
  ResearchStage,
  ResearchAction,
  ScaffoldUnitResponse,
  ComparisonProposal,
  ReadingListProposal,
} from '../../types/research';

const SearchPanel = () => {
  const [query, setQuery] = useState('');
  const [maxResults, setMaxResults] = useState(10);
  const [preferredTier, setPreferredTier] = useState<number | undefined>(
    undefined
  );
  const [tiers, setTiers] = useState<TierInfo[]>([]);

  const [stage, setStage] = useState<ResearchStage>('input');
  const [results, setResults] = useState<AcademicSearchResultItem[]>([]);
  const [tierUsed, setTierUsed] = useState('');
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [proposing, setProposing] = useState(false);

  // Proposal state
  const [proposalAction, setProposalAction] = useState<ResearchAction | null>(
    null
  );
  const [proposal, setProposal] = useState<
    ScaffoldUnitResponse | ComparisonProposal | ReadingListProposal | null
  >(null);

  // Load tiers on mount
  useEffect(() => {
    researchApi
      .getAvailableTiers()
      .then(res => setTiers(res.tiers))
      .catch(() => {});
  }, []);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setError(null);
    setStage('searching');
    try {
      const res = await researchApi.searchAcademic({
        query: query.trim(),
        maxResults,
        preferredTier,
      });
      setResults(res.results);
      setTierUsed(res.tierName);
      setSelected(new Set());
      setStage('results');
    } catch (e: unknown) {
      const msg =
        e instanceof Error ? e.message : 'Search failed. Please try again.';
      setError(msg);
      setStage('input');
    }
  }, [query, maxResults, preferredTier]);

  const toggleSelect = (idx: number) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const selectedSources: SourceInput[] = [...selected].map(i => ({
    title: results[i].title,
    url: results[i].url,
    summary: results[i].abstract,
  }));

  const handleAction = async (actionParams: ActionParams) => {
    setProposing(true);
    setError(null);
    setStage('proposing');
    try {
      let result:
        | ScaffoldUnitResponse
        | ComparisonProposal
        | ReadingListProposal;
      if (actionParams.action === 'scaffold') {
        result = await researchApi.proposeScaffold({
          sourceData: selectedSources,
          unitTitle: actionParams.params.unitTitle,
          unitDescription: actionParams.params.unitDescription,
          durationWeeks: actionParams.params.durationWeeks,
          pedagogyStyle: actionParams.params.pedagogyStyle,
        });
      } else if (actionParams.action === 'compare') {
        result = await researchApi.proposeComparison({
          sourceData: selectedSources,
          unitId: actionParams.params.unitId,
        });
      } else {
        result = await researchApi.proposeReadingList({
          sourceData: selectedSources,
          unitId: actionParams.params.unitId,
        });
      }
      setProposalAction(actionParams.action);
      setProposal(result);
      setStage('review');
    } catch (e: unknown) {
      let msg = 'Failed to generate proposal. Please try again.';
      if (
        e &&
        typeof e === 'object' &&
        'response' in e &&
        (e as Record<string, unknown>).response
      ) {
        const resp = (e as { response: { data?: { detail?: string } } })
          .response;
        if (resp.data?.detail) {
          msg = resp.data.detail;
        }
      } else if (e instanceof Error) {
        msg = e.message;
      }
      setError(msg);
      setStage('select-action');
    } finally {
      setProposing(false);
    }
  };

  const handleReset = () => {
    setStage('input');
    setResults([]);
    setSelected(new Set());
    setProposal(null);
    setProposalAction(null);
    setError(null);
  };

  return (
    <div className='space-y-6'>
      {/* Search Input */}
      {(stage === 'input' || stage === 'searching') && (
        <div className='space-y-4'>
          <div className='flex gap-3'>
            <div className='flex-1 relative'>
              <Search className='absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400' />
              <input
                type='text'
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter') handleSearch();
                }}
                placeholder='Search academic papers, curricula, syllabi...'
                className='w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent'
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={!query.trim() || stage === 'searching'}
              className='px-5 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2'
            >
              {stage === 'searching' ? (
                <Loader2 className='w-4 h-4 animate-spin' />
              ) : (
                <Search className='w-4 h-4' />
              )}
              Search
            </button>
          </div>

          <div className='flex gap-4 items-center'>
            {tiers.length > 0 && (
              <div className='flex items-center gap-2'>
                <label className='text-sm text-gray-600'>Search tier:</label>
                <select
                  value={preferredTier ?? ''}
                  onChange={e =>
                    setPreferredTier(
                      e.target.value ? parseInt(e.target.value) : undefined
                    )
                  }
                  className='px-2 py-1 border border-gray-300 rounded text-sm'
                >
                  <option value=''>Auto</option>
                  {tiers.map(t => (
                    <option key={t.tier} value={t.tier} disabled={!t.available}>
                      {t.name}
                      {!t.available && t.reason ? ` (${t.reason})` : ''}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div className='flex items-center gap-2'>
              <label className='text-sm text-gray-600'>Max results:</label>
              <select
                value={maxResults}
                onChange={e => setMaxResults(parseInt(e.target.value))}
                className='px-2 py-1 border border-gray-300 rounded text-sm'
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div
          className={`p-3 rounded-lg flex items-start gap-2 ${
            error.includes('No AI provider')
              ? 'bg-amber-50 border border-amber-200'
              : 'bg-red-50 border border-red-200'
          }`}
        >
          <AlertCircle
            className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
              error.includes('No AI provider')
                ? 'text-amber-600'
                : 'text-red-600'
            }`}
          />
          <div className='text-sm'>
            <span
              className={
                error.includes('No AI provider')
                  ? 'text-amber-800'
                  : 'text-red-800'
              }
            >
              {error}
            </span>
            {error.includes('No AI provider') && (
              <>
                {' '}
                <a
                  href='/settings'
                  target='_blank'
                  rel='noreferrer'
                  className='text-amber-700 underline hover:text-amber-900'
                >
                  Open Settings
                </a>
              </>
            )}
          </div>
        </div>
      )}

      {/* Results */}
      {(stage === 'results' ||
        stage === 'select-action' ||
        stage === 'proposing') && (
        <>
          <div className='flex items-center justify-between'>
            <div className='text-sm text-gray-500'>
              {results.length} results via{' '}
              <span className='font-medium'>{tierUsed}</span>
            </div>
            <div className='flex gap-2'>
              {selected.size > 0 && stage === 'results' && (
                <button
                  onClick={() => setStage('select-action')}
                  className='px-4 py-1.5 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition'
                >
                  Continue with {selected.size} selected
                </button>
              )}
              <button
                onClick={handleReset}
                className='px-4 py-1.5 text-gray-600 text-sm border rounded-lg hover:bg-gray-50 transition'
              >
                New Search
              </button>
            </div>
          </div>

          {stage !== 'select-action' && stage !== 'proposing' && (
            <div className='space-y-3'>
              {results.map((item, i) => (
                <div
                  key={i}
                  className={`border rounded-lg transition ${
                    selected.has(i)
                      ? 'border-purple-300 bg-purple-50/50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className='flex items-start gap-3 p-4'>
                    <input
                      type='checkbox'
                      checked={selected.has(i)}
                      onChange={() => toggleSelect(i)}
                      className='mt-1 h-4 w-4 text-purple-600 rounded border-gray-300'
                    />
                    <div className='flex-1 min-w-0'>
                      <div className='flex items-start justify-between gap-2'>
                        <a
                          href={item.url}
                          target='_blank'
                          rel='noreferrer'
                          className='font-medium text-sm text-blue-700 hover:underline flex items-center gap-1'
                        >
                          {item.title}
                          <ExternalLink className='w-3 h-3 flex-shrink-0' />
                        </a>
                        <span className='flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-xs font-medium'>
                          <Award className='w-3 h-3' />
                          {(item.academicScore * 100).toFixed(0)}
                        </span>
                      </div>

                      <div className='flex flex-wrap gap-3 mt-1 text-xs text-gray-500'>
                        {item.authors.length > 0 && (
                          <span className='flex items-center gap-1'>
                            <Users className='w-3 h-3' />
                            {item.authors.slice(0, 3).join(', ')}
                            {item.authors.length > 3 && ' et al.'}
                          </span>
                        )}
                        {item.publicationYear && (
                          <span className='flex items-center gap-1'>
                            <Calendar className='w-3 h-3' />
                            {item.publicationYear}
                          </span>
                        )}
                        {item.citationCount != null &&
                          item.citationCount > 0 && (
                            <span className='flex items-center gap-1'>
                              <Quote className='w-3 h-3' />
                              {item.citationCount} citations
                            </span>
                          )}
                        {item.sourceName && (
                          <span className='text-gray-400'>
                            {item.sourceName}
                          </span>
                        )}
                      </div>

                      {item.abstract && (
                        <div className='mt-2'>
                          <p
                            className={`text-sm text-gray-600 ${expandedIdx === i ? '' : 'line-clamp-2'}`}
                          >
                            {item.abstract}
                          </p>
                          {item.abstract.length > 200 && (
                            <button
                              onClick={() =>
                                setExpandedIdx(expandedIdx === i ? null : i)
                              }
                              className='text-xs text-purple-600 hover:underline mt-0.5 flex items-center gap-0.5'
                            >
                              {expandedIdx === i ? (
                                <>
                                  Show less <ChevronUp className='w-3 h-3' />
                                </>
                              ) : (
                                <>
                                  Show more <ChevronDown className='w-3 h-3' />
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Source Selector */}
          {(stage === 'select-action' || stage === 'proposing') && (
            <SourceSelector
              sources={selectedSources}
              onAction={handleAction}
              loading={proposing}
            />
          )}
        </>
      )}

      {/* Proposal Review */}
      {stage === 'review' && proposal && proposalAction && (
        <div>
          <button
            onClick={() => setStage('select-action')}
            className='mb-4 text-sm text-purple-600 hover:underline'
          >
            &larr; Back to action selection
          </button>
          <ProposalReview
            action={proposalAction}
            proposal={proposal}
            onDone={handleReset}
          />
        </div>
      )}

      {/* Done */}
      {stage === 'done' && (
        <div className='text-center py-8'>
          <p className='text-gray-600 mb-4'>Action completed successfully.</p>
          <button
            onClick={handleReset}
            className='px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition'
          >
            Start New Research
          </button>
        </div>
      )}
    </div>
  );
};

export default SearchPanel;
