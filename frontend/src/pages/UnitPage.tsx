import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import {
  Calendar,
  Target,
  FileText,
  BarChart3,
  Edit,
  Trash2,
  ArrowLeft,
  Sparkles,
  GitBranch,
  Download,
  Brain,
  ChevronDown,
  Star,
} from 'lucide-react';
import { getUnit, deleteUnit as deleteUnitApi } from '../services/api';
import api from '../services/api';
import axios from 'axios';
import ULOManager from '../components/UnitStructure/ULOManager';
import { AssessmentsManager } from '../components/UnitStructure/AssessmentsManager';
import { UnitStructureDashboard } from '../components/UnitStructure/UnitStructureDashboard';
import CoursePlanner from '../components/UnitStructure/CoursePlanner';
import WeekAccordion from '../components/UnitStructure/WeekAccordion';
import LearningOutcomeMap from '../components/UnitStructure/LearningOutcomeMap';
import GraduateCapabilitiesPanel from '../components/UnitStructure/GraduateCapabilitiesPanel';
import AoLMappingPanel from '../components/UnitStructure/AoLMappingPanel';
import SDGMappingPanel from '../components/UnitStructure/SDGMappingPanel';
import AIAssistant from '../features/ai/AIAssistant';
import UnitScaffoldReview from '../components/UnitStructure/UnitScaffoldReview';
import { QualityDashboard } from '../components/UnitStructure/QualityDashboard';
import AILevelBadge from '../components/shared/AILevelBadge';
import { aiApi, type ScaffoldUnitResponse } from '../services/aiApi';
import type { Unit } from '../types';
import { LoadingState, Button, Modal, Alert } from '../components/ui';
import { useAILevel } from '../hooks/useAILevel';
import { useUnitDesign } from '../hooks/useUnitDesign';
import { useWorkingContextStore } from '../stores/workingContextStore';
import toast from 'react-hot-toast';
import { Wand2 } from 'lucide-react';

type TabType =
  | 'structure'
  | 'outcomes'
  | 'assessments'
  | 'analytics'
  | 'quality';

const UnitPage = () => {
  const { unitId } = useParams<{ unitId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [unit, setUnit] = useState<Unit | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showPlanner, setShowPlanner] = useState(false);
  const [showOutcomeMap, setShowOutcomeMap] = useState(false);
  const [expandedWeek, setExpandedWeek] = useState<number | null>(null);
  const [showAI, setShowAI] = useState(false);
  const [scaffoldData, setScaffoldData] = useState<ScaffoldUnitResponse | null>(
    null
  );
  const [scaffolding, setScaffolding] = useState(false);
  const [acceptingScaffold, setAcceptingScaffold] = useState(false);
  const [unitULOs, setUnitULOs] = useState<
    Array<{ code: string; description: string }>
  >([]);
  const { isAIDisabled, canScaffold } = useAILevel();
  const { designId, hasDesign } = useUnitDesign(unitId);

  // Sync designId to working context when it resolves
  useEffect(() => {
    if (designId !== undefined) {
      useWorkingContextStore
        .getState()
        .setUnitDetails({ designId: designId ?? null });
    }
  }, [designId]);

  // Get active tab and week from URL
  const activeTab = (searchParams.get('tab') as TabType) || 'structure';
  const selectedWeek = parseInt(searchParams.get('week') || '0', 10);

  const setActiveTab = (tab: TabType) => {
    const params = new URLSearchParams(searchParams);
    params.set('tab', tab);
    if (tab !== 'structure') {
      params.delete('week');
    }
    setSearchParams(params);
  };

  // Sync expanded week with URL param
  useEffect(() => {
    if (selectedWeek > 0) {
      setExpandedWeek(selectedWeek);
    }
  }, [selectedWeek]);

  const handleWeekToggle = (weekNumber: number) => {
    if (expandedWeek === weekNumber) {
      setExpandedWeek(null);
      // Clear week from URL
      const params = new URLSearchParams(searchParams);
      params.delete('week');
      setSearchParams(params);
    } else {
      setExpandedWeek(weekNumber);
      // Update URL with week
      const params = new URLSearchParams(searchParams);
      params.set('tab', 'structure');
      params.set('week', String(weekNumber));
      setSearchParams(params);
    }
  };

  const handleAddMaterial = (weekNumber: number) => {
    // Navigate to content creator with week pre-selected
    navigate(`/content/create?unitId=${unitId}&week=${weekNumber}`);
  };

  const fetchUnit = useCallback(async () => {
    if (!unitId) return;
    try {
      setLoading(true);
      const response = await getUnit(unitId);
      setUnit(response.data);
    } catch (err) {
      setError('Failed to load unit');
      console.error('Error fetching unit:', err);
    } finally {
      setLoading(false);
    }
  }, [unitId]);

  // Write to working context store when unit loads
  useEffect(() => {
    if (unit) {
      useWorkingContextStore
        .getState()
        .setActiveUnit({ id: unit.id, title: unit.title, code: unit.code });
    }
  }, [unit]);

  useEffect(() => {
    fetchUnit();
  }, [fetchUnit]);

  // Fetch ULOs for AI context
  useEffect(() => {
    if (!unitId) return;
    api
      .get(`/outcomes/units/${unitId}/ulos`)
      .then(res => {
        const ulos = (
          res.data as Array<{ code: string; description: string }>
        ).map(u => ({
          code: u.code,
          description: u.description,
        }));
        setUnitULOs(ulos);
        useWorkingContextStore.getState().setUnitDetails({ ulos });
      })
      .catch(() => {
        /* non-critical */
      });
  }, [unitId]);

  // Reset AI sidebar when AI is disabled
  useEffect(() => {
    if (isAIDisabled) {
      setShowAI(false);
    }
  }, [isAIDisabled]);

  const isLocalMode = import.meta.env.VITE_LOCAL_MODE === 'true';
  const [showPermanentDelete, setShowPermanentDelete] = useState(false);

  const handleSoftDelete = async () => {
    if (!unitId) return;
    try {
      setDeleting(true);
      await deleteUnitApi(unitId, false);
      toast.success('Unit removed from dashboard');
      navigate('/');
    } catch (err) {
      toast.error('Failed to remove unit');
      console.error('Error removing unit:', err);
    } finally {
      setDeleting(false);
      setShowDeleteModal(false);
    }
  };

  const handlePermanentDelete = async () => {
    if (!unitId) return;
    try {
      setDeleting(true);
      await deleteUnitApi(unitId, true);
      toast.success('Unit permanently deleted');
      navigate('/');
    } catch (err) {
      toast.error('Failed to delete unit');
      console.error('Error deleting unit:', err);
    } finally {
      setDeleting(false);
      setShowDeleteModal(false);
      setShowPermanentDelete(false);
    }
  };

  const handleScaffold = async () => {
    if (!unit) return;
    try {
      setScaffolding(true);
      const { data } = await aiApi.scaffoldUnit({
        title: unit.title,
        description: unit.description,
        durationWeeks: unit.durationWeeks || 12,
        pedagogyStyle: unit.pedagogyType || 'mixed_approach',
        unitId,
        designId: designId ?? undefined,
      });
      setScaffoldData(data);
    } catch {
      toast.error('Failed to generate scaffold');
    } finally {
      setScaffolding(false);
    }
  };

  const handleAcceptScaffold = async (scaffold: ScaffoldUnitResponse) => {
    if (!unitId) return;
    try {
      setAcceptingScaffold(true);

      // Bulk-create ULOs
      if (scaffold.ulos.length > 0) {
        await api.post(`/outcomes/units/${unitId}/ulos/bulk`, {
          ulos: scaffold.ulos.map((u, i) => ({
            code: u.code,
            description: u.description,
            bloomLevel: u.bloomLevel,
            orderIndex: i,
          })),
        });
      }

      // Create assessments
      for (const asmt of scaffold.assessments) {
        await api.post(`/assessments/units/${unitId}/assessments`, {
          title: asmt.title,
          type: 'summative',
          category: asmt.category,
          weight: asmt.weight,
          dueWeek: asmt.dueWeek,
        });
      }

      toast.success('Unit scaffold applied successfully!');
      setScaffoldData(null);
      fetchUnit();
    } catch {
      toast.error('Failed to apply scaffold');
    } finally {
      setAcceptingScaffold(false);
    }
  };

  const [exporting, setExporting] = useState(false);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const exportMenuRef = React.useRef<HTMLDivElement>(null);

  // Close export menu on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        exportMenuRef.current &&
        !exportMenuRef.current.contains(e.target as Node)
      ) {
        setExportMenuOpen(false);
      }
    };
    if (exportMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [exportMenuOpen]);

  const [materialsExportOpen, setMaterialsExportOpen] = useState(false);

  const handleMaterialsExport = async (
    format: 'html' | 'pdf' | 'docx' | 'pptx'
  ) => {
    if (!unitId) return;
    setExportMenuOpen(false);
    setMaterialsExportOpen(false);
    try {
      setExporting(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `/api/units/${unitId}/export/materials?format=${format}`,
        {
          responseType: 'blob',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
      const disposition = response.headers['content-disposition'] as
        | string
        | undefined;
      const filenameMatch = disposition?.match(/filename="?([^"]+)"?/);
      const filename = filenameMatch?.[1] ?? 'materials.zip';
      const url = URL.createObjectURL(response.data as Blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      URL.revokeObjectURL(url);
      a.remove();
      toast.success(`Materials exported as ${format.toUpperCase()} ZIP`);
    } catch (err) {
      toast.error('Failed to export materials');
      console.error('Materials export error:', err);
    } finally {
      setExporting(false);
    }
  };

  const handleExport = async (format: 'imscc' | 'scorm' | 'html') => {
    if (!unitId) return;
    setExportMenuOpen(false);
    try {
      setExporting(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `/api/units/${unitId}/export/${format}`,
        {
          responseType: 'blob',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
      const disposition = response.headers['content-disposition'] as
        | string
        | undefined;
      const filenameMatch = disposition?.match(/filename="?([^"]+)"?/);
      const fallback =
        format === 'imscc'
          ? 'export.imscc'
          : format === 'html'
            ? 'export.html'
            : 'export.zip';
      const filename = filenameMatch?.[1] ?? fallback;
      const url = URL.createObjectURL(response.data as Blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      URL.revokeObjectURL(url);
      a.remove();
      const label =
        format === 'imscc'
          ? 'IMSCC v1.1'
          : format === 'html'
            ? 'HTML'
            : 'SCORM 1.2';
      toast.success(`${label} exported successfully`);
    } catch (err) {
      const label =
        format === 'imscc'
          ? 'IMSCC v1.1'
          : format === 'html'
            ? 'HTML'
            : 'SCORM 1.2';
      toast.error(`Failed to export ${label}`);
      console.error('Export error:', err);
    } finally {
      setExporting(false);
    }
  };

  const tabs = [
    {
      id: 'structure' as TabType,
      label: 'Structure & Content',
      icon: <Calendar className='w-4 h-4' />,
    },
    {
      id: 'outcomes' as TabType,
      label: 'Learning Outcomes',
      icon: <Target className='w-4 h-4' />,
    },
    {
      id: 'assessments' as TabType,
      label: 'Assessments',
      icon: <FileText className='w-4 h-4' />,
    },
    {
      id: 'analytics' as TabType,
      label: 'Analytics',
      icon: <BarChart3 className='w-4 h-4' />,
    },
    {
      id: 'quality' as TabType,
      label: 'Quality',
      icon: <Star className='w-4 h-4' />,
    },
  ];

  if (loading) {
    return <LoadingState message='Loading unit...' />;
  }

  if (error || !unit) {
    return (
      <div className='p-6'>
        <Alert variant='error'>{error || 'Unit not found'}</Alert>
        <Button className='mt-4' onClick={() => navigate('/')}>
          <ArrowLeft className='w-4 h-4 mr-2' />
          Back to Dashboard
        </Button>
      </div>
    );
  }

  const durationWeeks = unit.durationWeeks || 12;

  return (
    <div className='min-h-full'>
      {/* Unit Header */}
      <div className='bg-white border-b border-gray-200'>
        <div className='px-6 py-4'>
          <div className='flex items-start justify-between'>
            <div>
              <div className='flex items-center gap-3'>
                <h1 className='text-2xl font-bold text-gray-900'>
                  {unit.code}
                </h1>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${
                    unit.status === 'ACTIVE'
                      ? 'bg-green-100 text-green-800'
                      : unit.status === 'COMPLETED'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {unit.status}
                </span>
              </div>
              <p className='text-lg text-gray-600 mt-1'>{unit.title}</p>
              {unit.description && (
                <p className='text-sm text-gray-500 mt-2 max-w-2xl'>
                  {unit.description}
                </p>
              )}
              <div className='flex items-center gap-4 mt-3 text-sm text-gray-500'>
                <span>{unit.semester}</span>
                <span>•</span>
                <span>{unit.creditPoints} credits</span>
                <span>•</span>
                <span>{durationWeeks} weeks</span>
                {unit.pedagogyType && (
                  <>
                    <span>•</span>
                    <span className='capitalize'>
                      {unit.pedagogyType.replace(/-/g, ' ')}
                    </span>
                  </>
                )}
              </div>
            </div>
            <div className='flex items-center gap-2'>
              {!isAIDisabled && (
                <>
                  <AILevelBadge hasDesign={hasDesign} />
                  <Button
                    variant={showAI ? 'primary' : 'secondary'}
                    size='sm'
                    onClick={() => setShowAI(!showAI)}
                  >
                    <Brain className='w-4 h-4 mr-1' />
                    {showAI ? 'Close AI' : 'AI Assist'}
                  </Button>
                </>
              )}
              <div className='relative' ref={exportMenuRef}>
                <Button
                  variant='secondary'
                  size='sm'
                  onClick={() => setExportMenuOpen(!exportMenuOpen)}
                  loading={exporting}
                >
                  <Download className='w-4 h-4 mr-1' />
                  Export
                  <ChevronDown className='w-3 h-3 ml-1' />
                </Button>
                {exportMenuOpen && (
                  <div className='absolute right-0 mt-1 w-52 bg-white border border-gray-200 rounded-lg shadow-lg z-50'>
                    <button
                      className='w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-t-lg'
                      onClick={() => handleExport('imscc')}
                    >
                      Export IMSCC v1.1 (.imscc)
                    </button>
                    <button
                      className='w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50'
                      onClick={() => handleExport('scorm')}
                    >
                      Export SCORM 1.2 (.zip)
                    </button>
                    <button
                      className='w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50'
                      onClick={() => handleExport('html')}
                    >
                      Export as HTML (.html)
                    </button>
                    <div className='border-t border-gray-100' />
                    <button
                      className='w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center justify-between rounded-b-lg'
                      onClick={() =>
                        setMaterialsExportOpen(!materialsExportOpen)
                      }
                    >
                      <span>Materials ZIP</span>
                      <ChevronDown
                        className={`w-3 h-3 transition-transform ${materialsExportOpen ? 'rotate-180' : ''}`}
                      />
                    </button>
                    {materialsExportOpen && (
                      <div className='border-t border-gray-100 bg-gray-50'>
                        {(
                          [
                            { value: 'html', label: 'HTML' },
                            { value: 'pdf', label: 'PDF' },
                            { value: 'docx', label: 'DOCX' },
                            { value: 'pptx', label: 'PPTX' },
                          ] as const
                        ).map(fmt => (
                          <button
                            key={fmt.value}
                            className='w-full text-left px-6 py-2 text-sm text-gray-600 hover:bg-gray-100 last:rounded-b-lg'
                            onClick={() => handleMaterialsExport(fmt.value)}
                          >
                            All materials as {fmt.label} (.zip)
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
              <Button
                variant='secondary'
                size='sm'
                onClick={() => navigate(`/units/${unitId}/edit`)}
              >
                <Edit className='w-4 h-4 mr-1' />
                Edit
              </Button>
              <Button
                variant='secondary'
                size='sm'
                onClick={() => setShowDeleteModal(true)}
                className='text-red-600 hover:text-red-700 hover:bg-red-50'
              >
                <Trash2 className='w-4 h-4' />
              </Button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className='px-6'>
          <nav className='-mb-px flex space-x-8'>
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2
                  ${
                    activeTab === tab.id
                      ? 'border-purple-500 text-purple-600'
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

      {/* Tab Content + AI Sidebar */}
      <div className={`flex ${showAI ? 'gap-6' : ''}`}>
        <div className={`p-6 ${showAI ? 'flex-1 min-w-0' : 'w-full'}`}>
          {activeTab === 'structure' && (
            <div>
              {/* Action Bar */}
              <div className='flex items-center justify-between mb-6'>
                <div>
                  <h2 className='text-lg font-semibold text-gray-900'>
                    Weekly Content
                  </h2>
                  <p className='text-sm text-gray-500'>
                    Click on a week to view and manage materials
                  </p>
                </div>
                <div className='flex items-center gap-2'>
                  {canScaffold && (
                    <Button
                      variant='secondary'
                      size='sm'
                      onClick={handleScaffold}
                      loading={scaffolding}
                    >
                      <Wand2 className='w-4 h-4 mr-1' />
                      Quick Scaffold
                    </Button>
                  )}
                  <Button
                    variant='secondary'
                    size='sm'
                    onClick={() => setShowOutcomeMap(true)}
                  >
                    <GitBranch className='w-4 h-4 mr-1' />
                    View Map
                  </Button>
                  {canScaffold && (
                    <Button
                      variant={showPlanner ? 'primary' : 'secondary'}
                      size='sm'
                      onClick={() => setShowPlanner(!showPlanner)}
                    >
                      <Sparkles className='w-4 h-4 mr-1' />
                      {showPlanner ? 'Close Planner' : 'Course Planner'}
                    </Button>
                  )}
                </div>
              </div>

              {/* Course Planner */}
              {showPlanner && unit && (
                <div className='mb-6'>
                  <CoursePlanner
                    unit={unit}
                    designId={designId ?? undefined}
                    onApplySchedule={() => {
                      setShowPlanner(false);
                    }}
                    onClose={() => setShowPlanner(false)}
                  />
                </div>
              )}

              {/* Scaffold Review */}
              {scaffoldData && (
                <div className='mb-6'>
                  <UnitScaffoldReview
                    scaffold={scaffoldData}
                    onAccept={handleAcceptScaffold}
                    onCancel={() => setScaffoldData(null)}
                    accepting={acceptingScaffold}
                  />
                </div>
              )}

              {/* Accreditation Mapping Panels */}
              <div className='mb-6 space-y-4'>
                <GraduateCapabilitiesPanel
                  unitId={unitId!}
                  onViewMap={() => setShowOutcomeMap(true)}
                />
                <AoLMappingPanel unitId={unitId!} />
                <SDGMappingPanel unitId={unitId!} />
              </div>

              {/* Week Accordion */}
              <WeekAccordion
                unitId={unitId!}
                durationWeeks={durationWeeks}
                expandedWeek={expandedWeek}
                onWeekToggle={handleWeekToggle}
                onAddMaterial={handleAddMaterial}
              />

              {/* Learning Outcome Map Modal */}
              <LearningOutcomeMap
                unitId={unitId!}
                isOpen={showOutcomeMap}
                onClose={() => setShowOutcomeMap(false)}
              />
            </div>
          )}

          {activeTab === 'outcomes' && <ULOManager unitId={unitId!} />}

          {activeTab === 'assessments' && (
            <AssessmentsManager unitId={unitId!} />
          )}

          {activeTab === 'analytics' && (
            <UnitStructureDashboard
              unitId={unitId!}
              unitName={unit.title}
              durationWeeks={durationWeeks}
            />
          )}

          {activeTab === 'quality' && (
            <QualityDashboard unitId={unitId!} durationWeeks={durationWeeks} />
          )}
        </div>

        {/* AI Sidebar */}
        {showAI && (
          <div className='w-96 shrink-0 p-6 pl-0'>
            <div className='sticky top-6 h-[calc(100vh-12rem)]'>
              <AIAssistant
                embedded
                unitId={unitId!}
                unitTitle={unit.title}
                unitULOs={unitULOs}
                designId={designId ?? undefined}
                onClose={() => setShowAI(false)}
              />
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setShowPermanentDelete(false);
        }}
        title='Remove Unit'
      >
        <div className='space-y-4'>
          <p className='text-gray-600'>
            What would you like to do with{' '}
            <strong>
              {unit.code} - {unit.title}
            </strong>
            ?
          </p>

          {/* Option A: Soft Delete (primary, safe) */}
          <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
            <p className='text-sm font-medium text-blue-900'>
              Remove from Dashboard
            </p>
            <p className='text-sm text-blue-700 mt-1'>
              Hides this unit from the dashboard. All data and version history
              is preserved. You can restore it later from the archived units
              section.
            </p>
            <div className='mt-3'>
              <Button
                onClick={handleSoftDelete}
                loading={deleting && !showPermanentDelete}
                className='bg-blue-600 hover:bg-blue-700'
              >
                Remove from Dashboard
              </Button>
            </div>
          </div>

          {/* Option B: Hard Delete (destructive, conditional) */}
          {isLocalMode && (
            <div>
              {!showPermanentDelete ? (
                <button
                  onClick={() => setShowPermanentDelete(true)}
                  className='text-sm text-gray-500 hover:text-red-600 underline'
                >
                  Or delete permanently...
                </button>
              ) : (
                <div className='bg-red-50 border border-red-200 rounded-lg p-4'>
                  <p className='text-sm font-medium text-red-900'>
                    Delete Permanently
                  </p>
                  <p className='text-sm text-red-700 mt-1'>
                    This will permanently delete all content, learning outcomes,
                    assessments, and the entire version history.
                  </p>
                  <p className='mt-1 text-sm font-medium text-red-800'>
                    This action cannot be undone.
                  </p>
                  <div className='mt-3 flex gap-2'>
                    <Button
                      onClick={handlePermanentDelete}
                      loading={deleting && showPermanentDelete}
                      className='bg-red-600 hover:bg-red-700'
                    >
                      Delete Permanently
                    </Button>
                    <Button
                      variant='secondary'
                      onClick={() => setShowPermanentDelete(false)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className='flex justify-end'>
            <Button
              variant='secondary'
              onClick={() => {
                setShowDeleteModal(false);
                setShowPermanentDelete(false);
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default UnitPage;
