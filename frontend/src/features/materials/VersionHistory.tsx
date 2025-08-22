import React, { useState, useEffect, useCallback } from 'react';
import {
  Clock,
  GitBranch,
  ChevronRight,
  ChevronDown,
  RefreshCw,
  FileText,
  User,
  Calendar,
  CheckCircle,
  AlertCircle,
  Loader2,
  Eye,
  Diff,
  RotateCcw,
} from 'lucide-react';
import api from '../../services/api';
import { diffLines } from 'diff';

interface MaterialVersion {
  id: string;
  material_id: string;
  version: number;
  parent_version_id?: string;
  title: string;
  content: any;
  raw_content?: string;
  createdAt: string;
  created_by?: string;
  change_summary?: string;
  is_latest: boolean;
  word_count?: number;
  quality_score?: number;
}

interface VersionHistoryProps {
  materialId: string;
  currentVersion?: number;
  onVersionRestore?: (versionId: string) => void;
}

interface DiffViewProps {
  oldContent: string;
  newContent: string;
  viewMode: 'unified' | 'split';
}

const DiffView: React.FC<DiffViewProps> = ({
  oldContent,
  newContent,
  viewMode,
}) => {
  const changes = diffLines(oldContent || '', newContent || '');

  if (viewMode === 'unified') {
    return (
      <div className='font-mono text-sm bg-gray-50 rounded-lg p-4 overflow-x-auto'>
        {changes.map((part, index) => {
          const color = part.added
            ? 'bg-green-100 text-green-800'
            : part.removed
              ? 'bg-red-100 text-red-800'
              : '';
          const prefix = part.added ? '+' : part.removed ? '-' : ' ';

          return (
            <div key={index} className={`${color} px-2 py-1`}>
              <span className='select-none mr-3 text-gray-500'>{prefix}</span>
              <span style={{ whiteSpace: 'pre-wrap' }}>{part.value}</span>
            </div>
          );
        })}
      </div>
    );
  }

  // Split view
  const oldLines = oldContent.split('\n');
  const newLines = newContent.split('\n');

  return (
    <div className='grid grid-cols-2 gap-4 font-mono text-sm'>
      <div className='bg-red-50 rounded-lg p-4 overflow-x-auto'>
        <h4 className='font-sans font-semibold text-red-700 mb-2'>
          Previous Version
        </h4>
        {oldLines.map((line, index) => (
          <div key={index} className='px-2 py-1'>
            <span className='select-none mr-3 text-gray-500'>{index + 1}</span>
            <span style={{ whiteSpace: 'pre-wrap' }}>{line}</span>
          </div>
        ))}
      </div>
      <div className='bg-green-50 rounded-lg p-4 overflow-x-auto'>
        <h4 className='font-sans font-semibold text-green-700 mb-2'>
          Current Version
        </h4>
        {newLines.map((line, index) => (
          <div key={index} className='px-2 py-1'>
            <span className='select-none mr-3 text-gray-500'>{index + 1}</span>
            <span style={{ whiteSpace: 'pre-wrap' }}>{line}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const VersionHistory: React.FC<VersionHistoryProps> = ({
  materialId,
  currentVersion,
  onVersionRestore,
}) => {
  const [versions, setVersions] = useState<MaterialVersion[]>([]);
  const [selectedVersions, setSelectedVersions] = useState<
    [string | undefined, string | undefined]
  >([undefined, undefined]);
  const [loading, setLoading] = useState(true);
  const [expandedVersions, setExpandedVersions] = useState<Set<string>>(
    new Set()
  );
  const [viewMode, setViewMode] = useState<'timeline' | 'compare'>('timeline');
  const [diffViewMode, setDiffViewMode] = useState<'unified' | 'split'>(
    'unified'
  );
  const [restoringVersion, setRestoringVersion] = useState<string | null>(null);

  const fetchVersionHistory = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get(`/materials/${materialId}/versions`);
      setVersions(response.data);

      // Auto-select latest two versions for comparison
      if (response.data.length >= 2) {
        setSelectedVersions([response.data[1].id, response.data[0].id]);
      }
    } catch (error) {
      console.error('Failed to fetch version history:', error);
    } finally {
      setLoading(false);
    }
  }, [materialId]);

  useEffect(() => {
    fetchVersionHistory();
  }, [fetchVersionHistory]);

  const handleVersionRestore = async (versionId: string) => {
    try {
      setRestoringVersion(versionId);
      await api.post(`/materials/${materialId}/restore/${versionId}`);

      if (onVersionRestore) {
        onVersionRestore(versionId);
      }

      // Refresh version history
      await fetchVersionHistory();
    } catch (error) {
      console.error('Failed to restore version:', error);
    } finally {
      setRestoringVersion(null);
    }
  };

  const toggleVersionExpand = (versionId: string) => {
    const newExpanded = new Set(expandedVersions);
    if (newExpanded.has(versionId)) {
      newExpanded.delete(versionId);
    } else {
      newExpanded.add(versionId);
    }
    setExpandedVersions(newExpanded);
  };

  const selectVersionForComparison = (versionId: string) => {
    setSelectedVersions(prev => {
      if (prev[0] === versionId || prev[1] === versionId) {
        // Deselect if already selected
        if (prev[0] === versionId) {
          return [undefined, prev[1]];
        } else {
          return [prev[0], undefined];
        }
      }
      // Add to selection (max 2)
      if (!prev[0]) return [versionId, prev[1]];
      if (!prev[1]) return [prev[0], versionId];
      return [prev[1], versionId]; // Replace oldest selection
    });
  };

  const getVersionById = (id: string) => versions.find(v => v.id === id);

  const renderVersionTimeline = () => (
    <div className='space-y-4'>
      {versions.map((version, index) => {
        const isExpanded = expandedVersions.has(version.id);
        const isLatest = version.is_latest;
        const isCurrent = version.version === currentVersion;

        return (
          <div
            key={version.id}
            className={`border rounded-lg p-4 ${
              isLatest
                ? 'border-green-500 bg-green-50'
                : isCurrent
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white'
            }`}
          >
            <div className='flex items-start justify-between'>
              <div className='flex-1'>
                <div className='flex items-center space-x-3'>
                  <button
                    onClick={() => toggleVersionExpand(version.id)}
                    className='text-gray-500 hover:text-gray-700'
                  >
                    {isExpanded ? (
                      <ChevronDown className='h-5 w-5' />
                    ) : (
                      <ChevronRight className='h-5 w-5' />
                    )}
                  </button>

                  <div className='flex items-center space-x-2'>
                    <span className='font-semibold text-lg'>
                      Version {version.version}
                    </span>
                    {isLatest && (
                      <span className='px-2 py-1 bg-green-600 text-white text-xs rounded-full'>
                        Latest
                      </span>
                    )}
                    {isCurrent && !isLatest && (
                      <span className='px-2 py-1 bg-blue-600 text-white text-xs rounded-full'>
                        Current
                      </span>
                    )}
                  </div>
                </div>

                <div className='ml-8 mt-2'>
                  <p className='text-gray-900 font-medium'>{version.title}</p>
                  {version.change_summary && (
                    <p className='text-gray-600 text-sm mt-1'>
                      {version.change_summary}
                    </p>
                  )}

                  <div className='flex items-center space-x-4 mt-3 text-sm text-gray-500'>
                    <span className='flex items-center'>
                      <Calendar className='h-4 w-4 mr-1' />
                      {new Date(version.createdAt).toLocaleDateString()}
                    </span>
                    {version.created_by && (
                      <span className='flex items-center'>
                        <User className='h-4 w-4 mr-1' />
                        {version.created_by}
                      </span>
                    )}
                    {version.word_count && (
                      <span className='flex items-center'>
                        <FileText className='h-4 w-4 mr-1' />
                        {version.word_count} words
                      </span>
                    )}
                    {version.quality_score !== null &&
                      version.quality_score !== undefined && (
                        <span className='flex items-center'>
                          <CheckCircle className='h-4 w-4 mr-1' />
                          Quality: {version.quality_score}%
                        </span>
                      )}
                  </div>
                </div>
              </div>

              <div className='flex items-center space-x-2 ml-4'>
                <button
                  onClick={() => selectVersionForComparison(version.id)}
                  className={`px-3 py-1 rounded-lg text-sm ${
                    selectedVersions.includes(version.id)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <Diff className='h-4 w-4 inline mr-1' />
                  Compare
                </button>

                {!isLatest && (
                  <button
                    onClick={() => handleVersionRestore(version.id)}
                    disabled={restoringVersion === version.id}
                    className='px-3 py-1 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 text-sm disabled:opacity-50'
                  >
                    {restoringVersion === version.id ? (
                      <Loader2 className='h-4 w-4 animate-spin inline' />
                    ) : (
                      <>
                        <RotateCcw className='h-4 w-4 inline mr-1' />
                        Restore
                      </>
                    )}
                  </button>
                )}

                <button className='px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm'>
                  <Eye className='h-4 w-4 inline mr-1' />
                  View
                </button>
              </div>
            </div>

            {isExpanded && version.raw_content && (
              <div className='mt-4 ml-8'>
                <div className='bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto'>
                  <pre className='whitespace-pre-wrap text-sm text-gray-700'>
                    {version.raw_content}
                  </pre>
                </div>
              </div>
            )}

            {/* Version tree line */}
            {index < versions.length - 1 && (
              <div className='ml-6 mt-4 border-l-2 border-gray-300 h-8' />
            )}
          </div>
        );
      })}
    </div>
  );

  const renderVersionComparison = () => {
    const [oldVersionId, newVersionId] = selectedVersions;
    const oldVersion = oldVersionId ? getVersionById(oldVersionId) : null;
    const newVersion = newVersionId ? getVersionById(newVersionId) : null;

    if (!oldVersion || !newVersion) {
      return (
        <div className='text-center py-12'>
          <AlertCircle className='h-12 w-12 text-gray-400 mx-auto mb-4' />
          <p className='text-gray-500'>
            Select two versions from the timeline to compare
          </p>
        </div>
      );
    }

    return (
      <div className='space-y-4'>
        <div className='bg-white border border-gray-200 rounded-lg p-4'>
          <div className='flex items-center justify-between mb-4'>
            <h3 className='text-lg font-semibold'>
              Comparing Version {oldVersion.version} → Version{' '}
              {newVersion.version}
            </h3>
            <div className='flex items-center space-x-2'>
              <button
                onClick={() => setDiffViewMode('unified')}
                className={`px-3 py-1 rounded text-sm ${
                  diffViewMode === 'unified'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Unified
              </button>
              <button
                onClick={() => setDiffViewMode('split')}
                className={`px-3 py-1 rounded text-sm ${
                  diffViewMode === 'split'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Split
              </button>
            </div>
          </div>

          <div className='grid grid-cols-2 gap-4 mb-4 text-sm'>
            <div className='bg-red-50 rounded-lg p-3'>
              <div className='font-semibold text-red-700'>
                Version {oldVersion.version}
              </div>
              <div className='text-gray-600 mt-1'>
                {new Date(oldVersion.createdAt).toLocaleString()}
              </div>
              {oldVersion.change_summary && (
                <div className='text-gray-700 mt-2'>
                  {oldVersion.change_summary}
                </div>
              )}
            </div>
            <div className='bg-green-50 rounded-lg p-3'>
              <div className='font-semibold text-green-700'>
                Version {newVersion.version}
              </div>
              <div className='text-gray-600 mt-1'>
                {new Date(newVersion.createdAt).toLocaleString()}
              </div>
              {newVersion.change_summary && (
                <div className='text-gray-700 mt-2'>
                  {newVersion.change_summary}
                </div>
              )}
            </div>
          </div>

          <DiffView
            oldContent={oldVersion.raw_content || ''}
            newContent={newVersion.raw_content || ''}
            viewMode={diffViewMode}
          />
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <Loader2 className='h-8 w-8 animate-spin text-blue-600' />
      </div>
    );
  }

  return (
    <div className='bg-white rounded-lg shadow-md p-6'>
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
            disabled={selectedVersions.filter(Boolean).length < 2}
          >
            <Diff className='h-4 w-4 inline mr-2' />
            Compare
          </button>
          <button
            onClick={fetchVersionHistory}
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
        renderVersionTimeline()
      ) : (
        renderVersionComparison()
      )}
    </div>
  );
};

export default VersionHistory;
