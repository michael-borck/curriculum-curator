import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  BookOpen,
  Target,
  Scale,
  Layers,
  Calendar,
  Lightbulb,
  Loader2,
  Sparkles,
  AlertTriangle,
  Info,
} from 'lucide-react';
import { analyticsApi } from '../../services/unitStructureApi';
import type { QualityScore, WeekQualityScore } from '../../types/unitStructure';
import type { QualityMetricVisibility } from '../../types';
import StarRating from '../shared/StarRating';
import SnapshotCompare from './SnapshotCompare';
import { useAILevel } from '../../hooks/useAILevel';
import toast from 'react-hot-toast';

interface QualityDashboardProps {
  unitId: string;
  durationWeeks?: number;
  topicLabel?: string | undefined;
  visibleDimensions?: QualityMetricVisibility | undefined;
}

interface Recommendation {
  category: string;
  priority: string;
  issue: string;
  suggestion: string;
}

interface RecommendationsResponse {
  recommendations: Recommendation[];
  source: string;
  llm_recommendations?: string[];
  llm_error?: string;
  model_name?: string;
}

const dimensionLabels: Record<
  string,
  { label: string; icon: React.ReactElement }
> = {
  completeness: {
    label: 'Completeness',
    icon: <BookOpen className='w-4 h-4' />,
  },
  contentQuality: {
    label: 'Content Quality',
    icon: <BarChart3 className='w-4 h-4' />,
  },
  uloAlignment: {
    label: 'ULO Alignment',
    icon: <Target className='w-4 h-4' />,
  },
  workloadBalance: {
    label: 'Workload Balance',
    icon: <Scale className='w-4 h-4' />,
  },
  materialDiversity: {
    label: 'Material Diversity',
    icon: <Layers className='w-4 h-4' />,
  },
  assessmentDistribution: {
    label: 'Assessment Distribution',
    icon: <Calendar className='w-4 h-4' />,
  },
};

const getBarColor = (score: number): string => {
  if (score >= 80) return 'bg-green-500';
  if (score >= 60) return 'bg-blue-500';
  if (score >= 40) return 'bg-yellow-500';
  if (score >= 20) return 'bg-orange-500';
  return 'bg-red-500';
};

const getGradeColor = (grade: string): string => {
  const colors: Record<string, string> = {
    A: 'text-green-600',
    B: 'text-blue-600',
    C: 'text-yellow-600',
    D: 'text-orange-600',
    F: 'text-red-600',
  };
  return colors[grade] || 'text-gray-600';
};

export const QualityDashboard: React.FC<QualityDashboardProps> = ({
  unitId,
  durationWeeks = 12,
  topicLabel = 'Week',
  visibleDimensions,
}) => {
  const { canGenerate } = useAILevel();

  // Determine which dimensions are visible (default all true)
  const isVisible = (dim: string): boolean => {
    if (!visibleDimensions) return true;
    return visibleDimensions[dim as keyof QualityMetricVisibility] !== false;
  };
  const visibleDims = Object.keys(dimensionLabels).filter(isVisible);

  const [quality, setQuality] = useState<QualityScore | null>(null);
  const [weeklyQuality, setWeeklyQuality] = useState<WeekQualityScore[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [llmRecs, setLlmRecs] = useState<string[]>([]);
  const [llmLoading, setLlmLoading] = useState(false);
  const [llmModelName, setLlmModelName] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [qualityData, weeklyData, recsData] = await Promise.all([
        analyticsApi.getQualityScore(unitId, durationWeeks),
        analyticsApi.getWeeklyQuality(unitId, durationWeeks),
        analyticsApi.getRecommendations(
          unitId
        ) as Promise<RecommendationsResponse>,
      ]);
      setQuality(qualityData);
      setWeeklyQuality(weeklyData);
      setRecommendations(recsData.recommendations);
    } catch {
      toast.error('Failed to load quality data');
    } finally {
      setLoading(false);
    }
  }, [unitId, durationWeeks]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleGetLLMRecs = async () => {
    try {
      setLlmLoading(true);
      const data = (await analyticsApi.getRecommendations(
        unitId
      )) as unknown as RecommendationsResponse;
      // The API now has a source param but we call it separately
      const llmData = await (
        await import('../../services/api')
      ).default.get(`/analytics/units/${unitId}/recommendations`, {
        params: { source: 'llm' },
      });
      const resp = llmData.data as RecommendationsResponse;
      if (resp.llm_recommendations) {
        setLlmRecs(resp.llm_recommendations);
        setLlmModelName(resp.model_name ?? null);
      } else if (resp.llm_error) {
        toast.error('AI recommendations unavailable');
      }
      // Also update rule-based recs
      setRecommendations(data.recommendations);
    } catch {
      toast.error('Failed to get AI recommendations');
    } finally {
      setLlmLoading(false);
    }
  };

  // All dimensions disabled — info banner
  if (visibleDims.length === 0) {
    return (
      <div className='bg-blue-50 border border-blue-200 rounded-lg p-6 flex items-start gap-3'>
        <Info className='w-5 h-5 text-blue-500 mt-0.5 shrink-0' />
        <div>
          <p className='text-sm text-blue-800'>
            No quality metrics are enabled for this unit.
          </p>
          <button
            onClick={() => {
              const settingsTab = document.querySelector(
                '[data-tab="settings"]'
              ) as HTMLElement | null;
              settingsTab?.click();
            }}
            className='text-sm text-blue-600 hover:text-blue-800 underline mt-1 inline-flex items-center gap-1'
          >
            Enable metrics in Settings
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <Loader2 className='w-8 h-8 animate-spin text-purple-600' />
      </div>
    );
  }

  // Empty state
  if (!quality || quality.overallScore === 0) {
    return (
      <div className='bg-white rounded-lg shadow p-8 text-center'>
        <BarChart3 className='w-12 h-12 text-gray-300 mx-auto mb-4' />
        <h3 className='text-lg font-medium text-gray-900 mb-2'>
          No Quality Data Yet
        </h3>
        <p className='text-gray-500 max-w-md mx-auto'>
          Add content, learning outcomes, and assessments to your unit to see
          quality scores and recommendations.
        </p>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Overall Rating Card */}
      <div className='bg-white rounded-lg shadow p-6'>
        <div className='flex items-center justify-between'>
          <div>
            <h3 className='text-lg font-semibold text-gray-900 mb-2'>
              Overall Quality
            </h3>
            <StarRating rating={quality.starRating} size='lg' showValue />
            <div className='flex items-center gap-3 mt-2'>
              <span className='text-sm text-gray-500'>
                Score: {quality.overallScore.toFixed(1)}%
              </span>
              <span
                className={`text-2xl font-bold ${getGradeColor(quality.grade)}`}
              >
                {quality.grade}
              </span>
            </div>
          </div>
          <div className='text-right'>
            <span className='text-xs text-gray-400 block'>Rating method</span>
            <span className='text-sm text-gray-600 capitalize'>
              {quality.ratingMethod.replace(/_/g, ' ')}
            </span>
          </div>
        </div>
      </div>

      {/* Dimension Breakdown */}
      <div className='bg-white rounded-lg shadow p-6'>
        <h3 className='text-lg font-semibold text-gray-900 mb-4'>
          Quality Dimensions
        </h3>
        <div className='space-y-4'>
          {Object.entries(dimensionLabels)
            .filter(([key]) => isVisible(key))
            .map(([key, { label, icon }]) => {
              const score =
                quality.subScores[key as keyof typeof quality.subScores] ?? 0;
              return (
                <div key={key}>
                  <div className='flex items-center justify-between text-sm mb-1'>
                    <div className='flex items-center gap-2 text-gray-700'>
                      {icon}
                      <span>{label}</span>
                    </div>
                    <span className='font-medium'>{score.toFixed(0)}%</span>
                  </div>
                  <div className='w-full bg-gray-100 rounded-full h-2.5'>
                    <div
                      className={`h-2.5 rounded-full transition-all ${getBarColor(score)}`}
                      style={{ width: `${Math.min(score, 100)}%` }}
                    />
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* Weekly Quality Grid */}
      <div className='bg-white rounded-lg shadow p-6'>
        <h3 className='text-lg font-semibold text-gray-900 mb-4'>
          {topicLabel} Quality
        </h3>
        <div className='grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3'>
          {weeklyQuality.map(week => (
            <div
              key={week.weekNumber}
              className={`rounded-lg border p-3 text-center ${
                week.hasContent
                  ? 'border-gray-200 bg-white'
                  : 'border-dashed border-gray-200 bg-gray-50'
              }`}
            >
              <p className='text-xs font-medium text-gray-500 mb-1'>
                {topicLabel} {week.weekNumber}
              </p>
              {week.hasContent ? (
                <>
                  <StarRating rating={week.starRating} size='sm' />
                  <p className='text-xs text-gray-400 mt-1'>
                    {week.materialCount} material
                    {week.materialCount !== 1 ? 's' : ''}
                  </p>
                  {week.totalDurationMinutes > 0 && (
                    <p className='text-xs text-gray-400'>
                      {Math.floor(week.totalDurationMinutes / 60) > 0
                        ? `${Math.floor(week.totalDurationMinutes / 60)}h `
                        : ''}
                      {week.totalDurationMinutes % 60 > 0
                        ? `${week.totalDurationMinutes % 60}m`
                        : ''}
                    </p>
                  )}
                </>
              ) : (
                <p className='text-xs text-gray-400 italic'>Empty</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Improvement Suggestions */}
      <div className='bg-white rounded-lg shadow p-6'>
        <div className='flex items-center justify-between mb-4'>
          <h3 className='text-lg font-semibold text-gray-900 flex items-center gap-2'>
            <Lightbulb className='w-5 h-5 text-yellow-500' />
            Improvement Suggestions
          </h3>
          {canGenerate && (
            <button
              onClick={handleGetLLMRecs}
              disabled={llmLoading}
              className='inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-purple-700 bg-purple-50 rounded-lg hover:bg-purple-100 disabled:opacity-50 transition'
            >
              {llmLoading ? (
                <Loader2 className='w-4 h-4 animate-spin' />
              ) : (
                <Sparkles className='w-4 h-4' />
              )}
              Get AI Recommendations
            </button>
          )}
        </div>

        {recommendations.length === 0 && llmRecs.length === 0 ? (
          <p className='text-gray-500 text-sm'>
            No specific improvements suggested. Your unit looks well-structured.
          </p>
        ) : (
          <div className='space-y-3'>
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                className={`flex items-start gap-3 p-3 rounded-lg ${
                  rec.priority === 'high'
                    ? 'bg-red-50 border border-red-100'
                    : 'bg-yellow-50 border border-yellow-100'
                }`}
              >
                <AlertTriangle
                  className={`w-4 h-4 mt-0.5 shrink-0 ${
                    rec.priority === 'high' ? 'text-red-500' : 'text-yellow-500'
                  }`}
                />
                <div>
                  <p className='text-sm font-medium text-gray-900'>
                    {rec.issue}
                  </p>
                  <p className='text-sm text-gray-600'>{rec.suggestion}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* LLM Recommendations */}
        {llmRecs.length > 0 && (
          <div className='mt-4 pt-4 border-t border-gray-200'>
            <div className='flex items-center gap-2 mb-3'>
              <Sparkles className='w-4 h-4 text-purple-500' />
              <span className='text-sm font-medium text-purple-700'>
                AI Recommendations
              </span>
            </div>
            <div className='space-y-2'>
              {llmRecs.map((rec, idx) => (
                <div
                  key={idx}
                  className='flex items-start gap-3 p-3 bg-purple-50 border border-purple-100 rounded-lg'
                >
                  <span className='text-purple-400 font-medium text-sm shrink-0'>
                    {idx + 1}.
                  </span>
                  <p className='text-sm text-gray-700'>{rec}</p>
                </div>
              ))}
            </div>
            {llmModelName && (
              <p className='mt-2 text-xs text-gray-400 flex items-center gap-1'>
                <Info className='w-3 h-3' />
                Generated by {llmModelName}. Recommendations are suggestions
                only.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Score History & Comparison */}
      <SnapshotCompare unitId={unitId} />
    </div>
  );
};

export default QualityDashboard;
