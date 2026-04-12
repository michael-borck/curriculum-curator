import React, { useCallback, useEffect, useState } from 'react';
import {
  AlertCircle,
  BarChart3,
  BookOpen,
  Calendar,
  CheckCircle,
  Clock,
  Copy,
  FileText,
  Loader2,
  Sparkles,
  Target,
  TrendingUp,
  X,
} from 'lucide-react';
import toast from 'react-hot-toast';

import { aiApi } from '../../services/aiApi';
import { analyticsApi } from '../../services/unitStructureApi';
import { useAILevel } from '../../hooks/useAILevel';
import type {
  AlignmentReport,
  UnitOverview,
  WeeklyWorkload,
} from '../../types/unitStructure';

interface UnitAnalyticsProps {
  unitId: string;
}

interface ProgressData {
  materials: {
    total: number;
    published: number;
    draft: number;
    completionPercentage: number;
  };
  assessments: {
    total: number;
    published: number;
    draft: number;
    completionPercentage: number;
  };
  overallCompletion: number;
}

interface ValidationData {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  validation: {
    hasUlos: boolean;
    hasMaterials: boolean;
    hasAssessments: boolean;
    assessmentWeightValid: boolean;
    allUlosAssessed: boolean;
  };
}

interface RecommendationItem {
  type: string;
  priority: string;
  message: string;
  suggestion: string;
}

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ReactElement;
  color: string;
  subtitle?: string;
}> = ({ title, value, icon, color, subtitle }) => (
  <div className='bg-white rounded-lg shadow p-6'>
    <div className='flex items-center justify-between'>
      <div>
        <p className='text-sm font-medium text-gray-600'>{title}</p>
        <p className='mt-2 text-3xl font-semibold text-gray-900'>{value}</p>
        {subtitle && <p className='mt-1 text-sm text-gray-500'>{subtitle}</p>}
      </div>
      <div className={`p-3 rounded-full ${color}`}>
        {React.cloneElement(icon, { className: 'w-6 h-6 text-white' })}
      </div>
    </div>
  </div>
);

export const UnitAnalytics: React.FC<UnitAnalyticsProps> = ({ unitId }) => {
  const { canGenerate } = useAILevel();
  const [overview, setOverview] = useState<UnitOverview | null>(null);
  const [alignmentReport, setAlignmentReport] =
    useState<AlignmentReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [generatingGap, setGeneratingGap] = useState<string | null>(null);
  const [generatedContent, setGeneratedContent] = useState<{
    gapType: string;
    content: string;
  } | null>(null);

  // Analytics report state
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [workload, setWorkload] = useState<WeeklyWorkload[]>([]);
  const [validation, setValidation] = useState<ValidationData | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>(
    []
  );
  const [loadingSection, setLoadingSection] = useState<string | null>(null);

  const fetchOverviewData = useCallback(async () => {
    try {
      setLoading(true);
      const [overviewData, alignmentData] = await Promise.all([
        analyticsApi.getUnitOverview(unitId),
        analyticsApi.getAlignmentReport(unitId),
      ]);
      setOverview(overviewData);
      setAlignmentReport(alignmentData);
    } catch (error) {
      toast.error('Failed to fetch unit overview');
      console.error('Error fetching overview:', error);
    } finally {
      setLoading(false);
    }
  }, [unitId]);

  useEffect(() => {
    fetchOverviewData();
  }, [fetchOverviewData]);

  const handleFillGap = async (gapType: string, context: string) => {
    try {
      setGeneratingGap(context);
      const { data } = await aiApi.fillGap({ unitId, gapType, context });
      setGeneratedContent({
        gapType: data.gapType,
        content: data.generatedContent,
      });
    } catch {
      toast.error('Failed to generate content');
    } finally {
      setGeneratingGap(null);
    }
  };

  const handleExportData = async (format: 'json' | 'csv' | 'pdf') => {
    try {
      await analyticsApi.exportUnitData(unitId, format);
      toast.success(`Data exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Failed to export data');
      console.error('Error exporting data:', error);
    }
  };

  const loadProgress = useCallback(async () => {
    setLoadingSection('progress');
    try {
      const data = await analyticsApi.getProgressReport(unitId, true);
      setProgress(data);
    } catch {
      toast.error('Failed to load progress report');
    } finally {
      setLoadingSection(null);
    }
  }, [unitId]);

  const loadWorkload = useCallback(async () => {
    setLoadingSection('workload');
    try {
      const data = await analyticsApi.getWeeklyWorkload(unitId);
      setWorkload(data);
    } catch {
      toast.error('Failed to load workload analysis');
    } finally {
      setLoadingSection(null);
    }
  }, [unitId]);

  const loadValidation = useCallback(async () => {
    setLoadingSection('validation');
    try {
      const data = await analyticsApi.validateUnit(unitId, true);
      setValidation(data);
    } catch {
      toast.error('Failed to validate unit');
    } finally {
      setLoadingSection(null);
    }
  }, [unitId]);

  const loadRecommendations = useCallback(async () => {
    setLoadingSection('recommendations');
    try {
      const data = await analyticsApi.getRecommendations(unitId);
      setRecommendations(data.recommendations);
    } catch {
      toast.error('Failed to load recommendations');
    } finally {
      setLoadingSection(null);
    }
  }, [unitId]);

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600'></div>
      </div>
    );
  }

  if (!overview) {
    return (
      <div className='bg-white rounded-lg shadow p-8 text-center'>
        <BarChart3 className='w-12 h-12 text-gray-300 mx-auto mb-4' />
        <h3 className='text-lg font-medium text-gray-900 mb-2'>No Data Yet</h3>
        <p className='text-gray-500'>
          Add content to your unit to see the analytics overview.
        </p>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Overview stat cards */}
      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6'>
        <StatCard
          title='Learning Outcomes'
          value={overview.uloCount}
          icon={<Target />}
          color='bg-blue-500'
          subtitle='Unit-level outcomes'
        />
        <StatCard
          title='Total Materials'
          value={overview.materials.total}
          icon={<BookOpen />}
          color='bg-green-500'
          subtitle={`${overview.materials.byStatus?.published || 0} published`}
        />
        <StatCard
          title='Assessments'
          value={overview.assessments.total}
          icon={<FileText />}
          color='bg-purple-500'
          subtitle={`${overview.totalAssessmentWeight}% total weight`}
        />
        <StatCard
          title='Active Weeks'
          value={overview.weeksWithContent}
          icon={<Calendar />}
          color='bg-yellow-500'
          subtitle='Weeks with content'
        />
      </div>

      {/* Alignment summary */}
      {alignmentReport && (
        <div className='bg-white rounded-lg shadow p-6'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4'>
            Alignment Summary
          </h3>
          <div className='grid grid-cols-2 md:grid-cols-5 gap-4'>
            <div className='text-center'>
              <p className='text-2xl font-bold text-gray-900'>
                {alignmentReport.summary.totalUlos}
              </p>
              <p className='text-xs text-gray-600'>Total ULOs</p>
            </div>
            <div className='text-center'>
              <p className='text-2xl font-bold text-green-600'>
                {alignmentReport.summary.fullyAligned}
              </p>
              <p className='text-xs text-gray-600'>Fully Aligned</p>
            </div>
            <div className='text-center'>
              <p className='text-2xl font-bold text-yellow-600'>
                {alignmentReport.summary.materialsOnly}
              </p>
              <p className='text-xs text-gray-600'>Materials Only</p>
            </div>
            <div className='text-center'>
              <p className='text-2xl font-bold text-orange-600'>
                {alignmentReport.summary.assessmentsOnly}
              </p>
              <p className='text-xs text-gray-600'>Assessments Only</p>
            </div>
            <div className='text-center'>
              <p className='text-2xl font-bold text-red-600'>
                {alignmentReport.summary.unaligned}
              </p>
              <p className='text-xs text-gray-600'>Unaligned</p>
            </div>
          </div>

          {alignmentReport.recommendations.length > 0 && (
            <div className='mt-4 p-3 bg-yellow-50 rounded-lg'>
              <div className='flex items-start'>
                <AlertCircle className='w-5 h-5 text-yellow-600 mt-0.5' />
                <div className='ml-2 flex-1'>
                  <p className='text-sm font-medium text-yellow-800'>
                    Recommendations
                  </p>
                  <ul className='mt-1 text-sm text-yellow-700 space-y-1'>
                    {alignmentReport.recommendations.map((rec, idx) => (
                      <li
                        key={idx}
                        className='flex items-center justify-between'
                      >
                        <span>{rec}</span>
                        {canGenerate && (
                          <button
                            onClick={() => {
                              const gapType = rec
                                .toLowerCase()
                                .includes('assessment')
                                ? 'assessment'
                                : rec.toLowerCase().includes('outcome')
                                  ? 'ulo'
                                  : 'material';
                              handleFillGap(gapType, rec);
                            }}
                            disabled={generatingGap === rec}
                            className='ml-2 shrink-0 px-2 py-0.5 text-xs bg-yellow-200 text-yellow-800 rounded hover:bg-yellow-300 disabled:opacity-50 flex items-center gap-1'
                          >
                            {generatingGap === rec ? (
                              <Loader2 className='w-3 h-3 animate-spin' />
                            ) : (
                              <Sparkles className='w-3 h-3' />
                            )}
                            Generate
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Analytics Reports */}
      <div className='bg-white rounded-lg shadow p-6'>
        <h3 className='text-lg font-semibold text-gray-900 mb-4'>
          Analytics &amp; Reports
        </h3>

        <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
          {/* Progress Report */}
          <div className='p-4 border rounded-lg'>
            <div className='flex items-center justify-between mb-3'>
              <div>
                <h4 className='font-medium'>Progress Report</h4>
                <p className='text-sm text-gray-600'>
                  Detailed progress metrics
                </p>
              </div>
              <button
                onClick={loadProgress}
                disabled={loadingSection === 'progress'}
                className='px-3 py-1.5 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 disabled:opacity-50'
              >
                {loadingSection === 'progress' ? (
                  <Loader2 className='w-4 h-4 animate-spin' />
                ) : (
                  <TrendingUp className='w-4 h-4' />
                )}
              </button>
            </div>
            {progress && (
              <div className='space-y-2 text-sm'>
                <div className='flex justify-between'>
                  <span className='text-gray-600'>Overall</span>
                  <span className='font-medium'>
                    {progress.overallCompletion.toFixed(0)}%
                  </span>
                </div>
                <div className='w-full bg-gray-100 rounded-full h-2'>
                  <div
                    className='bg-blue-500 h-2 rounded-full'
                    style={{
                      width: `${Math.min(progress.overallCompletion, 100)}%`,
                    }}
                  />
                </div>
                <div className='flex justify-between text-xs text-gray-500'>
                  <span>
                    Materials: {progress.materials.published}/
                    {progress.materials.total} published
                  </span>
                  <span>
                    Assessments: {progress.assessments.published}/
                    {progress.assessments.total}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Workload Analysis */}
          <div className='p-4 border rounded-lg'>
            <div className='flex items-center justify-between mb-3'>
              <div>
                <h4 className='font-medium'>Workload Analysis</h4>
                <p className='text-sm text-gray-600'>Weekly student workload</p>
              </div>
              <button
                onClick={loadWorkload}
                disabled={loadingSection === 'workload'}
                className='px-3 py-1.5 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 disabled:opacity-50'
              >
                {loadingSection === 'workload' ? (
                  <Loader2 className='w-4 h-4 animate-spin' />
                ) : (
                  <Clock className='w-4 h-4' />
                )}
              </button>
            </div>
            {workload.length > 0 && (
              <div className='space-y-1'>
                {workload.map(w => (
                  <div
                    key={w.weekNumber}
                    className='flex items-center gap-2 text-xs'
                  >
                    <span className='w-12 text-gray-500'>
                      Wk {w.weekNumber}
                    </span>
                    <div className='flex-1 bg-gray-100 rounded-full h-2'>
                      <div
                        className='bg-green-500 h-2 rounded-full'
                        style={{
                          width: `${Math.min((w.workloadHours / 10) * 100, 100)}%`,
                        }}
                      />
                    </div>
                    <span className='w-12 text-right text-gray-600'>
                      {w.workloadHours.toFixed(1)}h
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recommendations */}
          {canGenerate && (
            <div className='p-4 border rounded-lg'>
              <div className='flex items-center justify-between mb-3'>
                <div>
                  <h4 className='font-medium'>Recommendations</h4>
                  <p className='text-sm text-gray-600'>
                    Improvement suggestions
                  </p>
                </div>
                <button
                  onClick={loadRecommendations}
                  disabled={loadingSection === 'recommendations'}
                  className='px-3 py-1.5 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 disabled:opacity-50'
                >
                  {loadingSection === 'recommendations' ? (
                    <Loader2 className='w-4 h-4 animate-spin' />
                  ) : (
                    <AlertCircle className='w-4 h-4' />
                  )}
                </button>
              </div>
              {recommendations.length > 0 && (
                <ul className='space-y-2 text-sm'>
                  {recommendations.map((rec, idx) => (
                    <li key={idx} className='flex items-start gap-2'>
                      <span
                        className={`mt-0.5 w-2 h-2 rounded-full shrink-0 ${
                          rec.priority === 'high'
                            ? 'bg-red-400'
                            : 'bg-yellow-400'
                        }`}
                      />
                      <span className='text-gray-700'>{rec.suggestion}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Validation */}
          <div className='p-4 border rounded-lg'>
            <div className='flex items-center justify-between mb-3'>
              <div>
                <h4 className='font-medium'>Unit Validation</h4>
                <p className='text-sm text-gray-600'>Completeness check</p>
              </div>
              <button
                onClick={loadValidation}
                disabled={loadingSection === 'validation'}
                className='px-3 py-1.5 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 disabled:opacity-50'
              >
                {loadingSection === 'validation' ? (
                  <Loader2 className='w-4 h-4 animate-spin' />
                ) : (
                  <CheckCircle className='w-4 h-4' />
                )}
              </button>
            </div>
            {validation && (
              <div className='space-y-2 text-sm'>
                <div
                  className={`flex items-center gap-2 font-medium ${
                    validation.isValid ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {validation.isValid ? (
                    <CheckCircle className='w-4 h-4' />
                  ) : (
                    <AlertCircle className='w-4 h-4' />
                  )}
                  {validation.isValid ? 'Valid' : 'Issues Found'}
                </div>
                {validation.errors.map((err, idx) => (
                  <p key={idx} className='text-red-600 text-xs'>
                    {err}
                  </p>
                ))}
                {validation.warnings.map((warn, idx) => (
                  <p key={idx} className='text-yellow-600 text-xs'>
                    {warn}
                  </p>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Data export buttons */}
      <div className='flex justify-end space-x-3'>
        <button
          onClick={() => handleExportData('json')}
          className='px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50'
        >
          Export JSON
        </button>
        <button
          onClick={() => handleExportData('csv')}
          className='px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50'
        >
          Export CSV
        </button>
        <button
          onClick={() => handleExportData('pdf')}
          className='px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50'
        >
          Export PDF
        </button>
      </div>

      {/* Generated Content Review Modal */}
      {generatedContent && (
        <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40'>
          <div className='bg-white rounded-lg shadow-xl w-full max-w-lg mx-4'>
            <div className='p-4 border-b border-gray-200 flex items-center justify-between'>
              <div className='flex items-center gap-2'>
                <Sparkles className='h-5 w-5 text-yellow-500' />
                <h3 className='text-lg font-semibold text-gray-900'>
                  Generated{' '}
                  {generatedContent.gapType === 'ulo'
                    ? 'Learning Outcome'
                    : generatedContent.gapType === 'assessment'
                      ? 'Assessment'
                      : 'Material'}
                </h3>
              </div>
              <button
                onClick={() => setGeneratedContent(null)}
                className='text-gray-400 hover:text-gray-600'
              >
                <X className='h-5 w-5' />
              </button>
            </div>
            <div className='p-4'>
              <div className='bg-gray-50 rounded-lg p-4 text-sm text-gray-800 whitespace-pre-wrap max-h-[50vh] overflow-y-auto'>
                {generatedContent.content}
              </div>
            </div>
            <div className='p-4 border-t border-gray-200 flex justify-end gap-3'>
              <button
                onClick={() => setGeneratedContent(null)}
                className='px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200'
              >
                Dismiss
              </button>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(generatedContent.content);
                  toast.success('Copied to clipboard');
                }}
                className='px-4 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700 flex items-center gap-2'
              >
                <Copy className='h-4 w-4' />
                Copy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UnitAnalytics;
