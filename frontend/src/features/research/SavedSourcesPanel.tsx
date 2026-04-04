import { useState, useEffect, useCallback } from 'react';
import {
  Loader2,
  ExternalLink,
  Trash2,
  Star,
  Search,
  ChevronLeft,
  ChevronRight,
  BookmarkX,
  AlertCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  listSources,
  deleteSource,
  toggleFavorite,
} from '../../services/researchSourceApi';
import type { ResearchSourceResponse } from '../../services/researchSourceApi';
import * as researchApi from '../../services/researchApi';
import SourceSelector from './SourceSelector';
import ProposalReview from './ProposalReview';
import type { ActionParams } from './SourceSelector';
import type {
  SourceInput,
  ResearchAction,
  ResearchStage,
  ScaffoldUnitResponse,
  ComparisonProposal,
  ReadingListProposal,
} from '../../types/research';

const PAGE_SIZE = 20;

/** Convert a saved source to the SourceInput format needed by proposal endpoints. */
function toSourceInput(s: ResearchSourceResponse): SourceInput {
  return {
    title: s.title,
    url: s.url,
    summary: s.summary,
  };
}

const SavedSourcesPanel = () => {
  const [sources, setSources] = useState<ResearchSourceResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Selection state
  const [selected, setSelected] = useState<Set<string>>(new Set());

  // Workflow state (mirrors SearchPanel pattern)
  const [stage, setStage] = useState<ResearchStage>('input');
  const [proposing, setProposing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [proposalAction, setProposalAction] = useState<ResearchAction | null>(
    null
  );
  const [proposal, setProposal] = useState<
    ScaffoldUnitResponse | ComparisonProposal | ReadingListProposal | null
  >(null);

  // Debounce search input
  useEffect(() => {
    const timer = window.setTimeout(
      () => setDebouncedSearch(searchFilter),
      300
    );
    return () => window.clearTimeout(timer);
  }, [searchFilter]);

  const fetchSources = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listSources({
        page,
        pageSize: PAGE_SIZE,
        search: debouncedSearch || undefined,
      });
      setSources(res.data.sources);
      setTotal(res.data.total);
      setHasMore(res.data.hasMore);
    } catch {
      toast.error('Failed to load saved sources');
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch]);

  useEffect(() => {
    void fetchSources();
  }, [fetchSources]);

  // Reset to page 1 when search changes
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const handleDelete = async (id: string) => {
    try {
      await deleteSource(id);
      setSources(prev => prev.filter(s => s.id !== id));
      setTotal(prev => prev - 1);
      setSelected(prev => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      toast.success('Source deleted');
    } catch {
      toast.error('Failed to delete source');
    }
  };

  const handleToggleFavorite = async (id: string) => {
    try {
      const res = await toggleFavorite(id);
      setSources(prev =>
        prev.map(s =>
          s.id === id ? { ...s, isFavorite: res.data.isFavorite } : s
        )
      );
    } catch {
      toast.error('Failed to update favorite');
    }
  };

  const toggleSelect = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === sources.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(sources.map(s => s.id)));
    }
  };

  const selectedSources: SourceInput[] = sources
    .filter(s => selected.has(s.id))
    .map(toSourceInput);

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

  const handleResetWorkflow = () => {
    setStage('input');
    setProposal(null);
    setProposalAction(null);
    setError(null);
  };

  // Action selection / proposal / review stages
  if (stage === 'select-action' || stage === 'proposing') {
    return (
      <div className='space-y-6'>
        <button
          onClick={handleResetWorkflow}
          className='text-sm text-purple-600 hover:underline'
        >
          &larr; Back to saved sources
        </button>
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
        <SourceSelector
          sources={selectedSources}
          onAction={handleAction}
          loading={proposing}
        />
      </div>
    );
  }

  if (stage === 'review' && proposal && proposalAction) {
    return (
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
          onDone={() => {
            handleResetWorkflow();
            setSelected(new Set());
          }}
        />
      </div>
    );
  }

  // Default: source list view
  return (
    <div className='space-y-4'>
      {/* Search filter + action bar */}
      <div className='flex items-center gap-3'>
        <div className='relative flex-1'>
          <Search className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400' />
          <input
            type='text'
            value={searchFilter}
            onChange={e => setSearchFilter(e.target.value)}
            placeholder='Filter saved sources...'
            className='w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent'
          />
        </div>
        {selected.size > 0 && (
          <button
            onClick={() => setStage('select-action')}
            className='px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition whitespace-nowrap'
          >
            Use {selected.size} selected
          </button>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className='flex justify-center py-12'>
          <Loader2 className='w-6 h-6 animate-spin text-purple-600' />
        </div>
      )}

      {/* Empty state */}
      {!loading && sources.length === 0 && (
        <div className='text-center py-12'>
          <BookmarkX className='w-10 h-10 text-gray-300 mx-auto mb-3' />
          <p className='text-gray-500'>
            {debouncedSearch
              ? 'No sources match your filter.'
              : 'No saved sources yet. Use the Search or Browse tabs to find and save academic sources.'}
          </p>
        </div>
      )}

      {/* Source list */}
      {!loading && sources.length > 0 && (
        <>
          <div className='flex items-center justify-between'>
            <div className='flex items-center gap-3'>
              <label className='flex items-center gap-2 text-sm text-gray-600 cursor-pointer'>
                <input
                  type='checkbox'
                  checked={
                    sources.length > 0 && selected.size === sources.length
                  }
                  onChange={toggleSelectAll}
                  className='h-4 w-4 text-purple-600 rounded border-gray-300'
                />
                Select all
              </label>
              <span className='text-sm text-gray-500'>
                {total} saved source{total !== 1 ? 's' : ''}
                {selected.size > 0 && ` (${selected.size} selected)`}
              </span>
            </div>
          </div>

          <div className='space-y-2'>
            {sources.map(source => (
              <div
                key={source.id}
                className={`flex items-center gap-3 p-3 border rounded-lg transition ${
                  selected.has(source.id)
                    ? 'border-purple-300 bg-purple-50/50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type='checkbox'
                  checked={selected.has(source.id)}
                  onChange={() => toggleSelect(source.id)}
                  className='h-4 w-4 text-purple-600 rounded border-gray-300 flex-shrink-0'
                />
                <div className='flex-1 min-w-0'>
                  <div className='flex items-center gap-2'>
                    <a
                      href={source.url}
                      target='_blank'
                      rel='noreferrer'
                      className='text-sm font-medium text-blue-700 hover:underline truncate flex items-center gap-1'
                    >
                      {source.title}
                      <ExternalLink className='w-3 h-3 flex-shrink-0' />
                    </a>
                  </div>
                  <div className='flex items-center gap-3 mt-1 text-xs text-gray-500'>
                    {source.academicScore > 0 && (
                      <span className='inline-flex items-center gap-1 px-1.5 py-0.5 bg-indigo-50 text-indigo-700 rounded font-medium'>
                        Score: {(source.academicScore * 100).toFixed(0)}
                      </span>
                    )}
                    <span>
                      Saved {new Date(source.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                  {source.summary && (
                    <p className='text-xs text-gray-500 mt-1 line-clamp-1'>
                      {source.summary}
                    </p>
                  )}
                </div>
                <div className='flex items-center gap-1'>
                  <button
                    onClick={() => handleToggleFavorite(source.id)}
                    title={
                      source.isFavorite ? 'Remove favorite' : 'Add favorite'
                    }
                    className={`p-1.5 rounded transition ${
                      source.isFavorite
                        ? 'text-yellow-500 hover:text-yellow-600'
                        : 'text-gray-300 hover:text-yellow-500'
                    }`}
                  >
                    <Star
                      className='w-4 h-4'
                      fill={source.isFavorite ? 'currentColor' : 'none'}
                    />
                  </button>
                  <button
                    onClick={() => handleDelete(source.id)}
                    title='Delete source'
                    className='p-1.5 text-gray-300 hover:text-red-500 rounded transition'
                  >
                    <Trash2 className='w-4 h-4' />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {total > PAGE_SIZE && (
            <div className='flex items-center justify-center gap-3 pt-2'>
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className='p-1.5 rounded border border-gray-300 disabled:opacity-30 hover:bg-gray-50 transition'
              >
                <ChevronLeft className='w-4 h-4' />
              </button>
              <span className='text-sm text-gray-600'>
                Page {page} of {Math.ceil(total / PAGE_SIZE)}
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={!hasMore}
                className='p-1.5 rounded border border-gray-300 disabled:opacity-30 hover:bg-gray-50 transition'
              >
                <ChevronRight className='w-4 h-4' />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default SavedSourcesPanel;
