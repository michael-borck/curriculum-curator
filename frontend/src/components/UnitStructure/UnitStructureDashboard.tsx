import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Target,
  FileText,
  BarChart3,
  Calendar,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Clock,
} from 'lucide-react';
import ULOManager from './ULOManager';
import { WeeklyMaterialsManager } from './WeeklyMaterialsManager';
import { AssessmentsManager } from './AssessmentsManager';
import { analyticsApi } from '../../services/unitStructureApi';
import {
  UnitOverview,
  AlignmentReport,
  QualityScore,
} from '../../types/unitStructure';
import toast from 'react-hot-toast';

interface UnitStructureDashboardProps {
  unitId: string;
  unitName?: string;
}

type TabType =
  | 'overview'
  | 'outcomes'
  | 'materials'
  | 'assessments'
  | 'analytics';

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

export const UnitStructureDashboard: React.FC<UnitStructureDashboardProps> = ({
  unitId,
  unitName = 'Unit',
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedWeek, setSelectedWeek] = useState(1);
  const [overview, setOverview] = useState<UnitOverview | null>(null);
  const [alignmentReport, setAlignmentReport] =
    useState<AlignmentReport | null>(null);
  const [qualityScore, setQualityScore] = useState<QualityScore | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverviewData();
  }, [unitId]);

  const fetchOverviewData = async () => {
    try {
      setLoading(true);
      const [overviewData, alignmentData, qualityData] = await Promise.all([
        analyticsApi.getUnitOverview(unitId),
        analyticsApi.getAlignmentReport(unitId),
        analyticsApi.getQualityScore(unitId),
      ]);
      setOverview(overviewData);
      setAlignmentReport(alignmentData);
      setQualityScore(qualityData);
    } catch (error) {
      toast.error('Failed to fetch unit overview');
      console.error('Error fetching overview:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async (format: 'json' | 'csv' | 'pdf') => {
    try {
      const data = await analyticsApi.exportUnitData(unitId, format);
      toast.success(`Data exported as ${format.toUpperCase()}`);
      console.log('Exported data:', data); // eslint-disable-line no-console
    } catch (error) {
      toast.error('Failed to export data');
      console.error('Error exporting data:', error);
    }
  };

  const tabs = [
    {
      id: 'overview' as TabType,
      label: 'Overview',
      icon: <BarChart3 className='w-4 h-4' />,
    },
    {
      id: 'outcomes' as TabType,
      label: 'Learning Outcomes',
      icon: <Target className='w-4 h-4' />,
    },
    {
      id: 'materials' as TabType,
      label: 'Weekly Materials',
      icon: <BookOpen className='w-4 h-4' />,
    },
    {
      id: 'assessments' as TabType,
      label: 'Assessments',
      icon: <FileText className='w-4 h-4' />,
    },
    {
      id: 'analytics' as TabType,
      label: 'Analytics',
      icon: <TrendingUp className='w-4 h-4' />,
    },
  ];

  const getQualityGradeColor = (grade: string) => {
    const colors: Record<string, string> = {
      A: 'text-green-600',
      B: 'text-blue-600',
      C: 'text-yellow-600',
      D: 'text-orange-600',
      F: 'text-red-600',
    };
    return colors[grade] || 'text-gray-600';
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600'></div>
      </div>
    );
  }

  return (
    <div className='min-h-screen bg-gray-50'>
      <div className='bg-white shadow'>
        <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'>
          <div className='py-6'>
            <h1 className='text-2xl font-bold text-gray-900'>
              {unitName} Structure Management
            </h1>
            <p className='mt-1 text-sm text-gray-600'>
              Manage learning outcomes, materials, and assessments
            </p>
          </div>

          <div className='border-b border-gray-200'>
            <nav className='-mb-px flex space-x-8'>
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2
                    ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>
      </div>

      <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8'>
        {activeTab === 'overview' && overview && (
          <div className='space-y-6'>
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

            {qualityScore && (
              <div className='bg-white rounded-lg shadow p-6'>
                <div className='flex items-center justify-between mb-4'>
                  <h3 className='text-lg font-semibold text-gray-900'>
                    Quality Score
                  </h3>
                  <span
                    className={`text-4xl font-bold ${getQualityGradeColor(qualityScore.grade)}`}
                  >
                    {qualityScore.grade}
                  </span>
                </div>
                <div className='space-y-3'>
                  <div>
                    <div className='flex justify-between text-sm mb-1'>
                      <span>Overall Score</span>
                      <span>{qualityScore.overallScore.toFixed(1)}%</span>
                    </div>
                    <div className='w-full bg-gray-200 rounded-full h-2'>
                      <div
                        className='bg-blue-600 h-2 rounded-full'
                        style={{ width: `${qualityScore.overallScore}%` }}
                      />
                    </div>
                  </div>
                  <div className='grid grid-cols-3 gap-4 pt-2'>
                    <div>
                      <p className='text-xs text-gray-600'>Alignment</p>
                      <p className='text-lg font-semibold'>
                        {qualityScore.subScores.alignment.toFixed(0)}%
                      </p>
                    </div>
                    <div>
                      <p className='text-xs text-gray-600'>Completion</p>
                      <p className='text-lg font-semibold'>
                        {qualityScore.subScores.completion.toFixed(0)}%
                      </p>
                    </div>
                    <div>
                      <p className='text-xs text-gray-600'>
                        Assessment Balance
                      </p>
                      <p className='text-lg font-semibold'>
                        {qualityScore.subScores.assessmentWeights.toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

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
                      <div className='ml-2'>
                        <p className='text-sm font-medium text-yellow-800'>
                          Recommendations
                        </p>
                        <ul className='mt-1 text-sm text-yellow-700 list-disc list-inside'>
                          {alignmentReport.recommendations.map((rec, idx) => (
                            <li key={idx}>{rec}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

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
          </div>
        )}

        {activeTab === 'outcomes' && <ULOManager unitId={unitId} />}

        {activeTab === 'materials' && (
          <div className='space-y-6'>
            <div className='bg-white rounded-lg shadow p-4'>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Select Week
              </label>
              <select
                value={selectedWeek}
                onChange={e => setSelectedWeek(parseInt(e.target.value))}
                className='block w-full md:w-48 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
              >
                {Array.from({ length: 52 }, (_, i) => i + 1).map(week => (
                  <option key={week} value={week}>
                    Week {week}
                  </option>
                ))}
              </select>
            </div>

            <WeeklyMaterialsManager unitId={unitId} weekNumber={selectedWeek} />
          </div>
        )}

        {activeTab === 'assessments' && <AssessmentsManager unitId={unitId} />}

        {activeTab === 'analytics' && (
          <div className='space-y-6'>
            <div className='bg-white rounded-lg shadow p-6'>
              <h3 className='text-lg font-semibold text-gray-900 mb-4'>
                Analytics & Reports
              </h3>

              <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                <button
                  onClick={async () => {
                    const data = await analyticsApi.getProgressReport(
                      unitId,
                      true
                    );
                    console.log('Progress Report:', data); // eslint-disable-line no-console
                    toast.success('Progress report generated - check console');
                  }}
                  className='p-4 border rounded-lg hover:bg-gray-50 text-left'
                >
                  <div className='flex items-center justify-between'>
                    <div>
                      <h4 className='font-medium'>Progress Report</h4>
                      <p className='text-sm text-gray-600'>
                        View detailed progress metrics
                      </p>
                    </div>
                    <TrendingUp className='w-5 h-5 text-gray-400' />
                  </div>
                </button>

                <button
                  onClick={async () => {
                    const data = await analyticsApi.getWeeklyWorkload(unitId);
                    console.log('Weekly Workload:', data); // eslint-disable-line no-console
                    toast.success(
                      'Workload analysis generated - check console'
                    );
                  }}
                  className='p-4 border rounded-lg hover:bg-gray-50 text-left'
                >
                  <div className='flex items-center justify-between'>
                    <div>
                      <h4 className='font-medium'>Workload Analysis</h4>
                      <p className='text-sm text-gray-600'>
                        Analyze weekly student workload
                      </p>
                    </div>
                    <Clock className='w-5 h-5 text-gray-400' />
                  </div>
                </button>

                <button
                  onClick={async () => {
                    const data = await analyticsApi.getRecommendations(unitId);
                    console.log('Recommendations:', data); // eslint-disable-line no-console
                    toast.success('Recommendations generated - check console');
                  }}
                  className='p-4 border rounded-lg hover:bg-gray-50 text-left'
                >
                  <div className='flex items-center justify-between'>
                    <div>
                      <h4 className='font-medium'>AI Recommendations</h4>
                      <p className='text-sm text-gray-600'>
                        Get improvement suggestions
                      </p>
                    </div>
                    <AlertCircle className='w-5 h-5 text-gray-400' />
                  </div>
                </button>

                <button
                  onClick={async () => {
                    const data = await analyticsApi.validateUnit(unitId, true);
                    console.log('Validation Results:', data); // eslint-disable-line no-console
                    toast.success('Validation complete - check console');
                  }}
                  className='p-4 border rounded-lg hover:bg-gray-50 text-left'
                >
                  <div className='flex items-center justify-between'>
                    <div>
                      <h4 className='font-medium'>Unit Validation</h4>
                      <p className='text-sm text-gray-600'>
                        Check for completeness and issues
                      </p>
                    </div>
                    <CheckCircle className='w-5 h-5 text-gray-400' />
                  </div>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
