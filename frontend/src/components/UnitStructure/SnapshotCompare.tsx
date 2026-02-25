import React, { useState, useEffect, useCallback } from 'react';
import {
  Camera,
  Trash2,
  GitCompareArrows,
  ChevronDown,
  ChevronRight,
  ArrowUp,
  ArrowDown,
  Minus,
  Loader2,
  Clock,
  Tag,
} from 'lucide-react';
import { analyticsApi } from '../../services/unitStructureApi';
import type {
  SnapshotListItem,
  SnapshotComparison,
} from '../../types/unitStructure';
import StarRating from '../shared/StarRating';
import toast from 'react-hot-toast';

interface SnapshotCompareProps {
  unitId: string;
}

const qualityDimensionLabels: Record<string, string> = {
  completeness: 'Completeness',
  contentQuality: 'Content Quality',
  uloAlignment: 'ULO Alignment',
  workloadBalance: 'Workload Balance',
  materialDiversity: 'Material Diversity',
  assessmentDistribution: 'Assessment Distribution',
};

const udlDimensionLabels: Record<string, string> = {
  representation: 'Representation',
  engagement: 'Engagement',
  expression: 'Expression',
  accessibility: 'Accessibility',
};

const formatDate = (iso: string): string => {
  const d = new Date(iso);
  return d.toLocaleDateString('en-AU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const DeltaIndicator: React.FC<{ value: number }> = ({ value }) => {
  if (Math.abs(value) < 0.01) {
    return (
      <span className='inline-flex items-center gap-0.5 text-gray-400 text-xs'>
        <Minus className='w-3 h-3' /> 0
      </span>
    );
  }
  if (value > 0) {
    return (
      <span className='inline-flex items-center gap-0.5 text-green-600 text-xs font-medium'>
        <ArrowUp className='w-3 h-3' /> +{value.toFixed(1)}
      </span>
    );
  }
  return (
    <span className='inline-flex items-center gap-0.5 text-red-600 text-xs font-medium'>
      <ArrowDown className='w-3 h-3' /> {value.toFixed(1)}
    </span>
  );
};

const getBarColor = (score: number): string => {
  if (score >= 80) return 'bg-green-500';
  if (score >= 60) return 'bg-blue-500';
  if (score >= 40) return 'bg-yellow-500';
  if (score >= 20) return 'bg-orange-500';
  return 'bg-red-500';
};

export const SnapshotCompare: React.FC<SnapshotCompareProps> = ({ unitId }) => {
  const [expanded, setExpanded] = useState(false);
  const [snapshots, setSnapshots] = useState<SnapshotListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [labelInput, setLabelInput] = useState('');
  const [showLabelInput, setShowLabelInput] = useState(false);

  // Compare state
  const [compareA, setCompareA] = useState<string>('');
  const [compareB, setCompareB] = useState<string>('current');
  const [comparison, setComparison] = useState<SnapshotComparison | null>(null);
  const [comparing, setComparing] = useState(false);

  const fetchSnapshots = useCallback(async () => {
    try {
      setLoading(true);
      const data = await analyticsApi.listSnapshots(unitId);
      setSnapshots(data);
    } catch {
      // Silently fail — snapshots are supplementary
    } finally {
      setLoading(false);
    }
  }, [unitId]);

  useEffect(() => {
    if (expanded) {
      fetchSnapshots();
    }
  }, [expanded, fetchSnapshots]);

  const handleSave = async () => {
    try {
      setSaving(true);
      await analyticsApi.createSnapshot(unitId, labelInput.trim() || undefined);
      toast.success('Snapshot saved');
      setShowLabelInput(false);
      setLabelInput('');
      await fetchSnapshots();
    } catch {
      toast.error('Failed to save snapshot');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (snapshotId: string) => {
    try {
      await analyticsApi.deleteSnapshot(unitId, snapshotId);
      toast.success('Snapshot deleted');
      setSnapshots(prev => prev.filter(s => s.id !== snapshotId));
      if (compareA === snapshotId) setCompareA('');
      if (compareB === snapshotId) setCompareB('current');
      setComparison(null);
    } catch {
      toast.error('Failed to delete snapshot');
    }
  };

  const handleCompare = async () => {
    if (!compareA) {
      toast.error('Select a snapshot to compare');
      return;
    }
    try {
      setComparing(true);
      const result = await analyticsApi.compareSnapshots(
        unitId,
        compareA,
        compareB
      );
      setComparison(result);
    } catch {
      toast.error('Failed to compare snapshots');
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className='bg-white rounded-lg shadow'>
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className='w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition rounded-lg'
      >
        <div className='flex items-center gap-2'>
          {expanded ? (
            <ChevronDown className='w-5 h-5 text-gray-400' />
          ) : (
            <ChevronRight className='w-5 h-5 text-gray-400' />
          )}
          <Camera className='w-5 h-5 text-indigo-500' />
          <h3 className='text-lg font-semibold text-gray-900'>
            Score History & Comparison
          </h3>
        </div>
        {!expanded && snapshots.length > 0 && (
          <span className='text-sm text-gray-400'>
            {snapshots.length} snapshot{snapshots.length !== 1 ? 's' : ''}
          </span>
        )}
      </button>

      {expanded && (
        <div className='px-4 pb-4 space-y-4'>
          {/* Save Snapshot */}
          <div className='flex items-center gap-2'>
            {showLabelInput ? (
              <div className='flex items-center gap-2 flex-1'>
                <input
                  type='text'
                  value={labelInput}
                  onChange={e => setLabelInput(e.target.value)}
                  placeholder='Label (optional), e.g. "Semester 1 Final"'
                  className='flex-1 text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleSave();
                    if (e.key === 'Escape') {
                      setShowLabelInput(false);
                      setLabelInput('');
                    }
                  }}
                />
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className='inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition'
                >
                  {saving ? (
                    <Loader2 className='w-4 h-4 animate-spin' />
                  ) : (
                    <Camera className='w-4 h-4' />
                  )}
                  Save
                </button>
                <button
                  onClick={() => {
                    setShowLabelInput(false);
                    setLabelInput('');
                  }}
                  className='text-sm text-gray-500 hover:text-gray-700'
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowLabelInput(true)}
                className='inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-indigo-700 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition'
              >
                <Camera className='w-4 h-4' />
                Save Snapshot
              </button>
            )}
          </div>

          {/* Snapshot List */}
          {loading ? (
            <div className='flex justify-center py-4'>
              <Loader2 className='w-6 h-6 animate-spin text-gray-400' />
            </div>
          ) : snapshots.length === 0 ? (
            <p className='text-sm text-gray-500 py-2'>
              No snapshots yet. Snapshots are created automatically when you
              view analytics, or you can save one manually above.
            </p>
          ) : (
            <>
              <div className='border rounded-lg divide-y max-h-64 overflow-y-auto'>
                {snapshots.map(snap => (
                  <div
                    key={snap.id}
                    className='flex items-center justify-between px-3 py-2 text-sm hover:bg-gray-50'
                  >
                    <div className='flex items-center gap-3 min-w-0'>
                      {snap.isAuto ? (
                        <Clock className='w-4 h-4 text-gray-400 shrink-0' />
                      ) : (
                        <Tag className='w-4 h-4 text-indigo-500 shrink-0' />
                      )}
                      <div className='min-w-0'>
                        <p className='font-medium text-gray-900 truncate'>
                          {snap.label ||
                            (snap.isAuto ? 'Auto-snapshot' : 'Manual snapshot')}
                        </p>
                        <p className='text-xs text-gray-400'>
                          {formatDate(snap.createdAt)}
                        </p>
                      </div>
                    </div>
                    <div className='flex items-center gap-3 shrink-0'>
                      <div className='text-right'>
                        <div className='flex items-center gap-2'>
                          <span className='text-xs text-gray-500'>Q:</span>
                          <StarRating
                            rating={snap.qualityStarRating}
                            size='sm'
                          />
                        </div>
                        <div className='flex items-center gap-2'>
                          <span className='text-xs text-gray-500'>U:</span>
                          <StarRating rating={snap.udlStarRating} size='sm' />
                        </div>
                      </div>
                      <button
                        onClick={() => handleDelete(snap.id)}
                        className='p-1 text-gray-400 hover:text-red-500 transition'
                        title='Delete snapshot'
                      >
                        <Trash2 className='w-4 h-4' />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Compare Controls */}
              <div className='bg-gray-50 rounded-lg p-3 space-y-3'>
                <h4 className='text-sm font-medium text-gray-700 flex items-center gap-1.5'>
                  <GitCompareArrows className='w-4 h-4' />
                  Compare
                </h4>
                <div className='flex items-center gap-2 flex-wrap'>
                  <select
                    value={compareA}
                    onChange={e => {
                      setCompareA(e.target.value);
                      setComparison(null);
                    }}
                    className='text-sm border border-gray-300 rounded-lg px-2 py-1.5 bg-white'
                  >
                    <option value=''>Select snapshot A...</option>
                    {snapshots.map(s => (
                      <option key={s.id} value={s.id}>
                        {s.label || (s.isAuto ? 'Auto' : 'Manual')} —{' '}
                        {formatDate(s.createdAt)}
                      </option>
                    ))}
                  </select>
                  <span className='text-sm text-gray-400'>vs</span>
                  <select
                    value={compareB}
                    onChange={e => {
                      setCompareB(e.target.value);
                      setComparison(null);
                    }}
                    className='text-sm border border-gray-300 rounded-lg px-2 py-1.5 bg-white'
                  >
                    <option value='current'>Current (live)</option>
                    {snapshots.map(s => (
                      <option key={s.id} value={s.id}>
                        {s.label || (s.isAuto ? 'Auto' : 'Manual')} —{' '}
                        {formatDate(s.createdAt)}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={handleCompare}
                    disabled={!compareA || comparing}
                    className='inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition'
                  >
                    {comparing ? (
                      <Loader2 className='w-4 h-4 animate-spin' />
                    ) : (
                      <GitCompareArrows className='w-4 h-4' />
                    )}
                    Compare
                  </button>
                </div>
              </div>

              {/* Comparison Results */}
              {comparison && (
                <div className='space-y-4'>
                  {/* Overall Scores */}
                  <div className='grid grid-cols-2 gap-4'>
                    <div className='bg-blue-50 rounded-lg p-3'>
                      <p className='text-xs font-medium text-blue-600 mb-1'>
                        Snapshot A
                      </p>
                      <p className='text-sm text-gray-500 truncate'>
                        {comparison.a.label || 'Snapshot'}
                      </p>
                      <div className='mt-2 space-y-1'>
                        <div className='flex items-center justify-between'>
                          <span className='text-xs text-gray-500'>Quality</span>
                          <span className='text-sm font-medium'>
                            {comparison.a.qualityOverall.toFixed(1)}%
                          </span>
                        </div>
                        <div className='flex items-center justify-between'>
                          <span className='text-xs text-gray-500'>UDL</span>
                          <span className='text-sm font-medium'>
                            {comparison.a.udlOverall.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className='bg-green-50 rounded-lg p-3'>
                      <p className='text-xs font-medium text-green-600 mb-1'>
                        {comparison.b.id === 'current'
                          ? 'Current'
                          : 'Snapshot B'}
                      </p>
                      <p className='text-sm text-gray-500 truncate'>
                        {comparison.b.label ||
                          (comparison.b.id === 'current'
                            ? 'Live scores'
                            : 'Snapshot')}
                      </p>
                      <div className='mt-2 space-y-1'>
                        <div className='flex items-center justify-between'>
                          <span className='text-xs text-gray-500'>Quality</span>
                          <div className='flex items-center gap-2'>
                            <span className='text-sm font-medium'>
                              {comparison.b.qualityOverall.toFixed(1)}%
                            </span>
                            <DeltaIndicator
                              value={comparison.delta.qualityOverall}
                            />
                          </div>
                        </div>
                        <div className='flex items-center justify-between'>
                          <span className='text-xs text-gray-500'>UDL</span>
                          <div className='flex items-center gap-2'>
                            <span className='text-sm font-medium'>
                              {comparison.b.udlOverall.toFixed(1)}%
                            </span>
                            <DeltaIndicator
                              value={comparison.delta.udlOverall}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Quality Dimension Comparison */}
                  <div className='bg-white border rounded-lg p-3'>
                    <h5 className='text-sm font-medium text-gray-700 mb-3'>
                      Quality Dimensions
                    </h5>
                    <div className='space-y-2'>
                      {Object.entries(qualityDimensionLabels).map(
                        ([key, label]) => {
                          const aScore =
                            comparison.a.qualitySubScores[key] ?? 0;
                          const bScore =
                            comparison.b.qualitySubScores[key] ?? 0;
                          const delta =
                            comparison.delta.qualitySubScores[key] ?? 0;
                          return (
                            <div key={key}>
                              <div className='flex items-center justify-between text-xs mb-0.5'>
                                <span className='text-gray-600'>{label}</span>
                                <div className='flex items-center gap-3'>
                                  <span className='text-gray-400'>
                                    {aScore.toFixed(0)}%
                                  </span>
                                  <span className='text-gray-900 font-medium'>
                                    {bScore.toFixed(0)}%
                                  </span>
                                  <DeltaIndicator value={delta} />
                                </div>
                              </div>
                              <div className='flex gap-1 h-1.5'>
                                <div className='flex-1 bg-gray-100 rounded-full overflow-hidden'>
                                  <div
                                    className={`h-full rounded-full ${getBarColor(aScore)} opacity-40`}
                                    style={{
                                      width: `${Math.min(aScore, 100)}%`,
                                    }}
                                  />
                                </div>
                                <div className='flex-1 bg-gray-100 rounded-full overflow-hidden'>
                                  <div
                                    className={`h-full rounded-full ${getBarColor(bScore)}`}
                                    style={{
                                      width: `${Math.min(bScore, 100)}%`,
                                    }}
                                  />
                                </div>
                              </div>
                            </div>
                          );
                        }
                      )}
                    </div>
                  </div>

                  {/* UDL Dimension Comparison */}
                  <div className='bg-white border rounded-lg p-3'>
                    <h5 className='text-sm font-medium text-gray-700 mb-3'>
                      UDL Dimensions
                    </h5>
                    <div className='space-y-2'>
                      {Object.entries(udlDimensionLabels).map(
                        ([key, label]) => {
                          const aScore = comparison.a.udlSubScores[key] ?? 0;
                          const bScore = comparison.b.udlSubScores[key] ?? 0;
                          const delta = comparison.delta.udlSubScores[key] ?? 0;
                          return (
                            <div key={key}>
                              <div className='flex items-center justify-between text-xs mb-0.5'>
                                <span className='text-gray-600'>{label}</span>
                                <div className='flex items-center gap-3'>
                                  <span className='text-gray-400'>
                                    {aScore.toFixed(0)}%
                                  </span>
                                  <span className='text-gray-900 font-medium'>
                                    {bScore.toFixed(0)}%
                                  </span>
                                  <DeltaIndicator value={delta} />
                                </div>
                              </div>
                              <div className='flex gap-1 h-1.5'>
                                <div className='flex-1 bg-gray-100 rounded-full overflow-hidden'>
                                  <div
                                    className={`h-full rounded-full ${getBarColor(aScore)} opacity-40`}
                                    style={{
                                      width: `${Math.min(aScore, 100)}%`,
                                    }}
                                  />
                                </div>
                                <div className='flex-1 bg-gray-100 rounded-full overflow-hidden'>
                                  <div
                                    className={`h-full rounded-full ${getBarColor(bScore)}`}
                                    style={{
                                      width: `${Math.min(bScore, 100)}%`,
                                    }}
                                  />
                                </div>
                              </div>
                            </div>
                          );
                        }
                      )}
                    </div>
                  </div>

                  {/* Summary Stats Comparison */}
                  {'materialCount' in comparison.a && (
                    <div className='bg-white border rounded-lg p-3'>
                      <h5 className='text-sm font-medium text-gray-700 mb-2'>
                        Unit Structure
                      </h5>
                      <div className='grid grid-cols-4 gap-2 text-center'>
                        {(
                          [
                            ['Materials', 'materialCount'],
                            ['Assessments', 'assessmentCount'],
                            ['ULOs', 'uloCount'],
                            ['Weeks', 'weeksWithContent'],
                          ] as const
                        ).map(([label, key]) => (
                          <div key={key} className='text-xs'>
                            <p className='text-gray-500 mb-0.5'>{label}</p>
                            <p className='text-gray-400'>{comparison.a[key]}</p>
                            <p className='font-medium text-gray-900'>
                              {comparison.b[key]}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SnapshotCompare;
