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
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  listSources,
  deleteSource,
  toggleFavorite,
} from '../../services/researchSourceApi';
import type { ResearchSourceResponse } from '../../services/researchSourceApi';

const PAGE_SIZE = 20;

const SavedSourcesPanel = () => {
  const [sources, setSources] = useState<ResearchSourceResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

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

  return (
    <div className='space-y-4'>
      {/* Search filter */}
      <div className='relative'>
        <Search className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400' />
        <input
          type='text'
          value={searchFilter}
          onChange={e => setSearchFilter(e.target.value)}
          placeholder='Filter saved sources...'
          className='w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent'
        />
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
              : 'No saved sources yet. Use the Search tab to find and save academic sources.'}
          </p>
        </div>
      )}

      {/* Source list */}
      {!loading && sources.length > 0 && (
        <>
          <div className='text-sm text-gray-500'>
            {total} saved source{total !== 1 ? 's' : ''}
          </div>
          <div className='space-y-2'>
            {sources.map(source => (
              <div
                key={source.id}
                className='flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:border-gray-300 transition'
              >
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
