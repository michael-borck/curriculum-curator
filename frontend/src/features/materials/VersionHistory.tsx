import React, { useState, useEffect, useCallback } from 'react';
import {
  Clock,
  GitBranch,
  ChevronRight,
  ChevronDown,
  RefreshCw,
  User,
  Calendar,
  Loader2,
  Eye,
  RotateCcw,
  AlertCircle,
} from 'lucide-react';
import { contentApi, type ContentVersion } from '../../services/contentApi';

interface VersionHistoryProps {
  unitId: string;
  contentId: string;
  onVersionRestore?: () => void;
}

const VersionHistory: React.FC<VersionHistoryProps> = ({
  unitId,
  contentId,
  onVersionRestore,
}) => {
  const [versions, setVersions] = useState<ContentVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedCommit, setExpandedCommit] = useState<string | null>(null);
  const [expandedBody, setExpandedBody] = useState<string | null>(null);
  const [restoringCommit, setRestoringCommit] = useState<string | null>(null);

  // Compare mode
  const [selectedCommits, setSelectedCommits] = useState<
    [string | undefined, string | undefined]
  >([undefined, undefined]);
  const [viewMode, setViewMode] = useState<'timeline' | 'compare'>('timeline');
  const [diffText, setDiffText] = useState<string | null>(null);
  const [diffLoading, setDiffLoading] = useState(false);

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      const { data } = await contentApi.history(unitId, contentId);
      setVersions(data.versions);
      if (data.versions.length >= 2) {
        setSelectedCommits([data.versions[1].commit, data.versions[0].commit]);
      }
    } catch (err) {
      console.error('Failed to fetch version history:', err);
    } finally {
      setLoading(false);
    }
  }, [unitId, contentId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleRestore = async (commit: string) => {
    try {
      setRestoringCommit(commit);
      await contentApi.revert(unitId, contentId, commit);
      onVersionRestore?.();
      await fetchHistory();
    } catch (err) {
      console.error('Failed to restore version:', err);
    } finally {
      setRestoringCommit(null);
    }
  };

  const handleExpand = async (commit: string) => {
    if (expandedCommit === commit) {
      setExpandedCommit(null);
      setExpandedBody(null);
      return;
    }
    setExpandedCommit(commit);
    try {
      const { data } = await contentApi.versionBody(unitId, contentId, commit);
      setExpandedBody(data.body);
    } catch {
      setExpandedBody('(failed to load)');
    }
  };

  const toggleCompareSelect = (commit: string) => {
    setSelectedCommits(prev => {
      if (prev[0] === commit) return [undefined, prev[1]];
      if (prev[1] === commit) return [prev[0], undefined];
      if (!prev[0]) return [commit, prev[1]];
      if (!prev[1]) return [prev[0], commit];
      return [prev[1], commit];
    });
  };

  const loadDiff = useCallback(async () => {
    const [oldC, newC] = selectedCommits;
    if (!oldC || !newC) return;
    try {
      setDiffLoading(true);
      const { data } = await contentApi.diff(unitId, contentId, oldC, newC);
      setDiffText(data.diff);
    } catch {
      setDiffText('(failed to load diff)');
    } finally {
      setDiffLoading(false);
    }
  }, [unitId, contentId, selectedCommits]);

  useEffect(() => {
    if (viewMode === 'compare' && selectedCommits[0] && selectedCommits[1]) {
      loadDiff();
    }
  }, [viewMode, loadDiff, selectedCommits]);

  const shortHash = (commit: string) => commit.slice(0, 7);

  // ─── Render ──────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <Loader2 className='h-8 w-8 animate-spin text-blue-600' />
      </div>
    );
  }

  return (
    <div className='bg-white rounded-lg shadow-md p-6'>
      {/* Header */}
      <div className='flex items-center justify-between mb-6'>
        <h2 className='text-2xl font-bold text-gray-900 flex items-center'>
          <Clock className='h-6 w-6 mr-2' />
          Version History
        </h2>

        <div className='flex items-center space-x-2'>
          <button
            onClick={() => setViewMode('timeline')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              viewMode === 'timeline'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <GitBranch className='h-4 w-4 inline mr-2' />
            Timeline
          </button>
          <button
            onClick={() => setViewMode('compare')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              viewMode === 'compare'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
            disabled={selectedCommits.filter(Boolean).length < 2}
          >
            Compare
          </button>
          <button
            onClick={fetchHistory}
            className='p-2 text-gray-600 hover:bg-gray-100 rounded-lg'
          >
            <RefreshCw className='h-5 w-5' />
          </button>
        </div>
      </div>

      {versions.length === 0 ? (
        <div className='text-center py-12'>
          <Clock className='h-12 w-12 text-gray-400 mx-auto mb-4' />
          <p className='text-gray-500'>No version history available</p>
        </div>
      ) : viewMode === 'timeline' ? (
        <div className='space-y-3'>
          {versions.map((v, idx) => {
            const isExpanded = expandedCommit === v.commit;
            const isLatest = idx === 0;

            return (
              <div
                key={v.commit}
                className={`border rounded-lg p-4 ${
                  isLatest
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 bg-white'
                }`}
              >
                <div className='flex items-start justify-between'>
                  <div className='flex-1'>
                    <div className='flex items-center space-x-3'>
                      <button
                        onClick={() => handleExpand(v.commit)}
                        className='text-gray-500 hover:text-gray-700'
                      >
                        {isExpanded ? (
                          <ChevronDown className='h-5 w-5' />
                        ) : (
                          <ChevronRight className='h-5 w-5' />
                        )}
                      </button>

                      <code className='text-sm font-mono bg-gray-100 px-2 py-0.5 rounded'>
                        {shortHash(v.commit)}
                      </code>

                      {isLatest && (
                        <span className='px-2 py-1 bg-green-600 text-white text-xs rounded-full'>
                          Latest
                        </span>
                      )}
                    </div>

                    <div className='ml-8 mt-2'>
                      <p className='text-gray-900 font-medium'>{v.message}</p>
                      <div className='flex items-center space-x-4 mt-2 text-sm text-gray-500'>
                        <span className='flex items-center'>
                          <Calendar className='h-4 w-4 mr-1' />
                          {new Date(v.date).toLocaleString()}
                        </span>
                        {v.authorEmail && (
                          <span className='flex items-center'>
                            <User className='h-4 w-4 mr-1' />
                            {v.authorEmail}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className='flex items-center space-x-2 ml-4'>
                    <button
                      onClick={() => toggleCompareSelect(v.commit)}
                      className={`px-3 py-1 rounded-lg text-sm ${
                        selectedCommits.includes(v.commit)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      Compare
                    </button>

                    {!isLatest && (
                      <button
                        onClick={() => handleRestore(v.commit)}
                        disabled={restoringCommit === v.commit}
                        className='px-3 py-1 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 text-sm disabled:opacity-50'
                      >
                        {restoringCommit === v.commit ? (
                          <Loader2 className='h-4 w-4 animate-spin inline' />
                        ) : (
                          <>
                            <RotateCcw className='h-4 w-4 inline mr-1' />
                            Restore
                          </>
                        )}
                      </button>
                    )}

                    <button
                      onClick={() => handleExpand(v.commit)}
                      className='px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm'
                    >
                      <Eye className='h-4 w-4 inline mr-1' />
                      View
                    </button>
                  </div>
                </div>

                {isExpanded && expandedBody !== null && (
                  <div className='mt-4 ml-8'>
                    <div className='bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto'>
                      <pre className='whitespace-pre-wrap text-sm text-gray-700'>
                        {expandedBody}
                      </pre>
                    </div>
                  </div>
                )}

                {idx < versions.length - 1 && (
                  <div className='ml-6 mt-4 border-l-2 border-gray-300 h-8' />
                )}
              </div>
            );
          })}
        </div>
      ) : (
        /* ── Compare View ──────────────────────────────────────── */
        <div className='space-y-4'>
          {!selectedCommits[0] || !selectedCommits[1] ? (
            <div className='text-center py-12'>
              <AlertCircle className='h-12 w-12 text-gray-400 mx-auto mb-4' />
              <p className='text-gray-500'>
                Select two versions from the timeline to compare
              </p>
            </div>
          ) : diffLoading ? (
            <div className='flex justify-center py-12'>
              <Loader2 className='h-8 w-8 animate-spin text-blue-600' />
            </div>
          ) : (
            <div className='bg-white border border-gray-200 rounded-lg p-4'>
              <h3 className='text-lg font-semibold mb-4'>
                Comparing{' '}
                <code className='text-sm bg-gray-100 px-1 rounded'>
                  {shortHash(selectedCommits[0])}
                </code>{' '}
                &rarr;{' '}
                <code className='text-sm bg-gray-100 px-1 rounded'>
                  {shortHash(selectedCommits[1])}
                </code>
              </h3>

              <div className='font-mono text-sm bg-gray-50 rounded-lg p-4 overflow-x-auto max-h-[600px] overflow-y-auto'>
                {diffText?.split('\n').map((line, i) => {
                  let cls = '';
                  if (line.startsWith('+')) cls = 'bg-green-100 text-green-800';
                  else if (line.startsWith('-'))
                    cls = 'bg-red-100 text-red-800';
                  else if (line.startsWith('@@'))
                    cls = 'bg-blue-50 text-blue-700';

                  return (
                    <div key={i} className={`${cls} px-2 py-0.5`}>
                      <span style={{ whiteSpace: 'pre-wrap' }}>{line}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VersionHistory;
