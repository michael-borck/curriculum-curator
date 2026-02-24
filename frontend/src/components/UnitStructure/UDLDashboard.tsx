import React, { useState, useEffect, useCallback } from 'react';
import {
  Eye,
  Users,
  Pen,
  Accessibility,
  Loader2,
  Lightbulb,
  AlertTriangle,
  Info,
  Settings,
} from 'lucide-react';
import { analyticsApi } from '../../services/unitStructureApi';
import type {
  UDLUnitScore,
  UDLWeekScore,
  UDLSuggestion,
} from '../../types/unitStructure';
import type { UDLMetricVisibility } from '../../types';
import StarRating from '../shared/StarRating';
import toast from 'react-hot-toast';

interface UDLDashboardProps {
  unitId: string;
  durationWeeks?: number | undefined;
  topicLabel?: string | undefined;
  visibleDimensions?: UDLMetricVisibility | undefined;
}

const dimensionLabels: Record<
  string,
  { label: string; icon: React.ReactElement }
> = {
  representation: {
    label: 'Representation',
    icon: <Eye className='w-4 h-4' />,
  },
  engagement: {
    label: 'Engagement',
    icon: <Users className='w-4 h-4' />,
  },
  expression: {
    label: 'Action & Expression',
    icon: <Pen className='w-4 h-4' />,
  },
  accessibility: {
    label: 'Accessibility',
    icon: <Accessibility className='w-4 h-4' />,
  },
};

const dimensionBadgeColors: Record<string, string> = {
  representation: 'bg-blue-100 text-blue-700',
  engagement: 'bg-green-100 text-green-700',
  expression: 'bg-purple-100 text-purple-700',
  accessibility: 'bg-orange-100 text-orange-700',
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

const getPriorityColor = (priority: string): string => {
  if (priority === 'high') return 'bg-red-50 border-red-100';
  if (priority === 'medium') return 'bg-yellow-50 border-yellow-100';
  return 'bg-blue-50 border-blue-100';
};

const getPriorityIconColor = (priority: string): string => {
  if (priority === 'high') return 'text-red-500';
  if (priority === 'medium') return 'text-yellow-500';
  return 'text-blue-500';
};

export const UDLDashboard: React.FC<UDLDashboardProps> = ({
  unitId,
  durationWeeks = 12,
  topicLabel = 'Week',
  visibleDimensions,
}) => {
  const [udlScore, setUdlScore] = useState<UDLUnitScore | null>(null);
  const [weeklyUdl, setWeeklyUdl] = useState<UDLWeekScore[]>([]);
  const [suggestions, setSuggestions] = useState<UDLSuggestion[]>([]);
  const [loading, setLoading] = useState(true);

  // Determine which dimensions are visible (default all true)
  const isVisible = (dim: keyof UDLMetricVisibility): boolean => {
    if (!visibleDimensions) return true;
    return visibleDimensions[dim] !== false;
  };

  const visibleDims = (
    Object.keys(dimensionLabels) as Array<keyof UDLMetricVisibility>
  ).filter(isVisible);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [scoreData, weeklyData, suggestionsData] = await Promise.all([
        analyticsApi.getUDLScore(unitId, durationWeeks),
        analyticsApi.getUDLWeekly(unitId, durationWeeks),
        analyticsApi.getUDLSuggestions(unitId, durationWeeks),
      ]);
      setUdlScore(scoreData);
      setWeeklyUdl(weeklyData);
      setSuggestions(suggestionsData.suggestions);
    } catch {
      toast.error('Failed to load UDL data');
    } finally {
      setLoading(false);
    }
  }, [unitId, durationWeeks]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // All dimensions disabled — info banner
  if (visibleDims.length === 0) {
    return (
      <div className='bg-blue-50 border border-blue-200 rounded-lg p-6 flex items-start gap-3'>
        <Info className='w-5 h-5 text-blue-500 mt-0.5 shrink-0' />
        <div>
          <p className='text-sm text-blue-800'>
            No UDL metrics are enabled for this unit.
          </p>
          <button
            onClick={() => {
              // Navigate to settings tab
              const settingsTab = document.querySelector(
                '[data-tab="settings"]'
              ) as HTMLElement | null;
              settingsTab?.click();
            }}
            className='text-sm text-blue-600 hover:text-blue-800 underline mt-1 inline-flex items-center gap-1'
          >
            <Settings className='w-3.5 h-3.5' />
            Enable metrics in Settings
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className='flex items-center justify-center h-48'>
        <Loader2 className='w-8 h-8 animate-spin text-teal-600' />
      </div>
    );
  }

  // Empty state
  if (!udlScore || udlScore.overallScore === 0) {
    return (
      <div className='bg-white rounded-lg shadow p-8 text-center'>
        <Accessibility className='w-12 h-12 text-gray-300 mx-auto mb-4' />
        <h3 className='text-lg font-medium text-gray-900 mb-2'>
          No UDL Data Yet
        </h3>
        <p className='text-gray-500 max-w-md mx-auto'>
          Add materials and assessments to see UDL inclusivity scores and
          suggestions.
        </p>
      </div>
    );
  }

  // Filter suggestions to only visible dimensions
  const filteredSuggestions = suggestions.filter(s =>
    visibleDims.includes(s.dimension as keyof UDLMetricVisibility)
  );

  return (
    <div className='space-y-6'>
      {/* Overall UDL Rating */}
      <div className='bg-white rounded-lg shadow p-6'>
        <div className='flex items-center justify-between'>
          <div>
            <h3 className='text-lg font-semibold text-gray-900 mb-2'>
              UDL Inclusivity
            </h3>
            <StarRating rating={udlScore.starRating} size='lg' showValue />
            <div className='flex items-center gap-3 mt-2'>
              <span className='text-sm text-gray-500'>
                Score: {udlScore.overallScore.toFixed(1)}%
              </span>
              <span
                className={`text-2xl font-bold ${getGradeColor(udlScore.grade)}`}
              >
                {udlScore.grade}
              </span>
            </div>
          </div>
          <div className='text-right'>
            <span className='text-xs text-gray-400 block'>
              Assessment diversity
            </span>
            <span className='text-sm text-gray-600'>
              {udlScore.assessmentFormatDiversity.toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* UDL Dimensions */}
      <div className='bg-white rounded-lg shadow p-6'>
        <h3 className='text-lg font-semibold text-gray-900 mb-4'>
          UDL Dimensions
        </h3>
        <div className='space-y-4'>
          {visibleDims.map(key => {
            const config = dimensionLabels[key];
            const score = udlScore.subScores[key] ?? 0;
            return (
              <div key={key}>
                <div className='flex items-center justify-between text-sm mb-1'>
                  <div className='flex items-center gap-2 text-gray-700'>
                    {config.icon}
                    <span>{config.label}</span>
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

      {/* Weekly UDL Grid */}
      <div className='bg-white rounded-lg shadow p-6'>
        <h3 className='text-lg font-semibold text-gray-900 mb-4'>
          {topicLabel} UDL Scores
        </h3>
        <div className='grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3'>
          {weeklyUdl.map(week => (
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
                <StarRating rating={week.starRating} size='sm' />
              ) : (
                <p className='text-xs text-gray-400 italic'>Empty</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* UDL Suggestions */}
      <div className='bg-white rounded-lg shadow p-6'>
        <h3 className='text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4'>
          <Lightbulb className='w-5 h-5 text-teal-500' />
          UDL Suggestions
        </h3>

        {filteredSuggestions.length === 0 ? (
          <p className='text-gray-500 text-sm'>
            No UDL improvements suggested. Your unit has good inclusivity
            design.
          </p>
        ) : (
          <div className='space-y-3'>
            {filteredSuggestions.map((sug, idx) => (
              <div
                key={idx}
                className={`flex items-start gap-3 p-3 rounded-lg border ${getPriorityColor(sug.priority)}`}
              >
                <AlertTriangle
                  className={`w-4 h-4 mt-0.5 shrink-0 ${getPriorityIconColor(sug.priority)}`}
                />
                <div className='flex-1'>
                  <div className='flex items-center gap-2 mb-1'>
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded-full ${dimensionBadgeColors[sug.dimension] || 'bg-gray-100 text-gray-700'}`}
                    >
                      {dimensionLabels[sug.dimension]?.label || sug.dimension}
                    </span>
                  </div>
                  <p className='text-sm font-medium text-gray-900'>
                    {sug.issue}
                  </p>
                  <p className='text-sm text-gray-600'>{sug.suggestion}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default UDLDashboard;
