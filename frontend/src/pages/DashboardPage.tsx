import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
} from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  BookOpen,
  Calendar,
  ChevronRight,
  Trash2,
  CheckCircle,
  Clock,
  Star,
  Archive,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  Zap,
  FileText,
  HelpCircle,
  ClipboardList,
  Briefcase,
  FolderOpen,
  Award,
  StickyNote,
  Video,
  Activity,
  GraduationCap,
  Upload,
  Copy,
  Download,
  ArrowUpDown,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import {
  createUnit as createUnitApi,
  updateUnit as updateUnitApi,
  deleteUnit as deleteUnitApi,
  duplicateUnit as duplicateUnitApi,
  getArchivedUnits as getArchivedUnitsApi,
  restoreUnit as restoreUnitApi,
  quickCreateUnit as quickCreateUnitApi,
} from '../services/api';
import { downloadExport } from '../utils/downloadExport';
import { useUnitsStore } from '../stores/unitsStore';
import { useAuthStore } from '../stores/authStore';
import { getSectorProfile } from '../constants/sectorProfiles';
import {
  Modal,
  Alert,
  Button,
  LoadingState,
  EmptyState,
  FormInput,
  FormTextarea,
  FormSelect,
  useConfirmDialog,
} from '../components/ui';
import { useModal } from '../hooks';
import { analyticsApi } from '../services/unitStructureApi';
import StarRating from '../components/shared/StarRating';
import type { DashboardMetrics } from '../types/unitStructure';

import toast from 'react-hot-toast';

type SortKey =
  | 'name-asc'
  | 'name-desc'
  | 'quality-desc'
  | 'udl-desc'
  | 'completion-desc'
  | 'updated-desc';

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: 'name-asc', label: 'Name (A \u2192 Z)' },
  { value: 'name-desc', label: 'Name (Z \u2192 A)' },
  { value: 'quality-desc', label: 'Quality (highest)' },
  { value: 'udl-desc', label: 'UDL (highest)' },
  { value: 'completion-desc', label: 'Completion (most)' },
  { value: 'updated-desc', label: 'Recently updated' },
];

const SORT_STORAGE_KEY = 'dashboard-sort-key';

interface UnitFormData {
  title: string;
  code: string;
  description: string;
  pedagogyType: string;
  difficultyLevel: string;
  durationWeeks: number;
  topicLabel: string;
  unitLabel: string;
}

function makeInitialFormData(
  sectorId?: string | null | undefined
): UnitFormData {
  const profile = getSectorProfile(sectorId);
  return {
    title: '',
    code: '',
    description: '',
    pedagogyType: 'inquiry-based',
    difficultyLevel: 'intermediate',
    durationWeeks: profile.duration,
    topicLabel: profile.topicLabel,
    unitLabel: profile.unitLabel,
  };
}

const pedagogyOptions = [
  { value: 'inquiry-based', label: 'Inquiry Based' },
  { value: 'project-based', label: 'Project Based' },
  { value: 'traditional', label: 'Traditional' },
  { value: 'collaborative', label: 'Collaborative' },
  { value: 'game-based', label: 'Game Based' },
  { value: 'constructivist', label: 'Constructivist' },
  { value: 'problem-based', label: 'Problem Based' },
  { value: 'experiential', label: 'Experiential' },
  { value: 'competency-based', label: 'Competency Based' },
];

const difficultyOptions = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
];

interface StructurePreset {
  id: string;
  label: string;
  topicLabel: string | null;
  unitLabel: string | null;
  duration: number | null;
  accreditationDefaults: boolean;
  tooltip: string;
}

const STRUCTURE_PRESETS: StructurePreset[] = [
  {
    id: 'semester',
    label: 'Semester',
    topicLabel: 'Week',
    unitLabel: 'Unit',
    duration: 12,
    accreditationDefaults: true,
    tooltip: 'Standard 12-week university semester',
  },
  {
    id: 'trimester',
    label: 'Trimester',
    topicLabel: 'Week',
    unitLabel: 'Unit',
    duration: 10,
    accreditationDefaults: true,
    tooltip: '10-week trimester format',
  },
  {
    id: 'term',
    label: 'Term',
    topicLabel: 'Lesson',
    unitLabel: 'Subject',
    duration: 10,
    accreditationDefaults: false,
    tooltip: 'Standard 10-week school term',
  },
  {
    id: 'intensive',
    label: 'Intensive',
    topicLabel: 'Day',
    unitLabel: 'Program',
    duration: 5,
    accreditationDefaults: false,
    tooltip: 'Short block delivery over 5 days',
  },
  {
    id: 'workshop',
    label: 'Workshop',
    topicLabel: 'Session',
    unitLabel: 'Workshop',
    duration: 4,
    accreditationDefaults: false,
    tooltip: '4 focused practical sessions',
  },
  {
    id: 'self-paced',
    label: 'Self-paced',
    topicLabel: 'Module',
    unitLabel: 'Program',
    duration: 6,
    accreditationDefaults: false,
    tooltip: '6 self-study modules, no fixed schedule',
  },
  {
    id: 'custom',
    label: 'Custom',
    topicLabel: null,
    unitLabel: null,
    duration: null,
    accreditationDefaults: true,
    tooltip: 'Set your own duration and labels',
  },
];

const contentTypeCards: { value: string; label: string; icon: LucideIcon }[] = [
  { value: 'lecture', label: 'Lecture', icon: GraduationCap },
  { value: 'worksheet', label: 'Worksheet', icon: FileText },
  { value: 'quiz', label: 'Quiz', icon: HelpCircle },
  { value: 'case_study', label: 'Case Study', icon: Briefcase },
  { value: 'assignment', label: 'Assignment', icon: ClipboardList },
  { value: 'project', label: 'Project', icon: FolderOpen },
  { value: 'assessment', label: 'Assessment', icon: Award },
  { value: 'notes', label: 'Notes', icon: StickyNote },
  { value: 'video', label: 'Video', icon: Video },
  { value: 'activity', label: 'Activity', icon: Activity },
];

const DashboardPage = () => {
  const navigate = useNavigate();
  const confirm = useConfirmDialog();
  const createModal = useModal();
  const quickCreateModal = useModal();

  // Use shared units store
  const { units, loading, fetchUnits, addUnit, removeUnit, invalidate } =
    useUnitsStore();

  const { user } = useAuthStore();
  const sectorProfile = useMemo(
    () => getSectorProfile(user?.educationSector),
    [user?.educationSector]
  );
  const filteredPresets = useMemo(
    () => STRUCTURE_PRESETS.filter(p => sectorProfile.presets.includes(p.id)),
    [sectorProfile]
  );

  const [newUnit, setNewUnit] = useState<UnitFormData>(() =>
    makeInitialFormData(user?.educationSector)
  );
  const [selectedPreset, setSelectedPreset] = useState(() =>
    filteredPresets.length > 0 ? filteredPresets[0].id : 'semester'
  );
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  // Quick create state
  const [quickCreateTitle, setQuickCreateTitle] = useState('');
  const [quickCreating, setQuickCreating] = useState(false);
  const [showQuickContent, setShowQuickContent] = useState(true);

  // Archived units
  const [showArchived, setShowArchived] = useState(false);
  const [archivedUnits, setArchivedUnits] = useState<
    Array<{
      id: string;
      title: string;
      code: string;
      status: string;
      semester: string;
      creditPoints?: number;
      durationWeeks?: number;
      pedagogyType?: string;
    }>
  >([]);
  const [archivedLoading, setArchivedLoading] = useState(false);
  const [restoringId, setRestoringId] = useState<string | null>(null);

  // Dashboard metrics & sorting
  const [metrics, setMetrics] = useState<Record<string, DashboardMetrics>>({});
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>(
    () =>
      (localStorage.getItem(SORT_STORAGE_KEY) as SortKey | null) || 'name-asc'
  );

  // Quick action state
  const [cloningId, setCloningId] = useState<string | null>(null);
  const [exportMenuUnitId, setExportMenuUnitId] = useState<string | null>(null);
  const [importMenuUnitId, setImportMenuUnitId] = useState<string | null>(null);
  const [exportingId, setExportingId] = useState<string | null>(null);
  const exportMenuRef = useRef<HTMLDivElement>(null);
  const importMenuRef = useRef<HTMLDivElement>(null);

  const fetchArchivedUnits = async () => {
    try {
      setArchivedLoading(true);
      const response = await getArchivedUnitsApi();
      setArchivedUnits(response.data?.units ?? []);
    } catch {
      toast.error('Failed to load archived units');
    } finally {
      setArchivedLoading(false);
    }
  };

  const handleRestoreUnit = async (unitId: string) => {
    try {
      setRestoringId(unitId);
      await restoreUnitApi(unitId);
      toast.success('Unit restored');
      // Refresh both lists
      setArchivedUnits(prev => prev.filter(u => u.id !== unitId));
      invalidate();
      fetchUnits();
    } catch {
      toast.error('Failed to restore unit');
    } finally {
      setRestoringId(null);
    }
  };

  const toggleArchived = () => {
    const next = !showArchived;
    setShowArchived(next);
    if (next) {
      fetchArchivedUnits();
    }
  };

  // Close dropdowns on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        exportMenuRef.current &&
        !exportMenuRef.current.contains(e.target as Node)
      ) {
        setExportMenuUnitId(null);
      }
      if (
        importMenuRef.current &&
        !importMenuRef.current.contains(e.target as Node)
      ) {
        setImportMenuUnitId(null);
      }
    };
    if (exportMenuUnitId || importMenuUnitId) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [exportMenuUnitId, importMenuUnitId]);

  const handleClone = async (unitId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      setCloningId(unitId);
      const response = await duplicateUnitApi(unitId);
      const newUnit = response.data;
      toast.success('Unit cloned successfully');
      invalidate();
      fetchUnits();
      navigate(`/units/${newUnit.id}`);
    } catch {
      toast.error('Failed to clone unit');
    } finally {
      setCloningId(null);
    }
  };

  const handleQuickExport = async (
    unitId: string,
    format: 'imscc' | 'scorm' | 'html'
  ) => {
    setExportMenuUnitId(null);
    const label =
      format === 'imscc'
        ? 'IMSCC v1.1'
        : format === 'html'
          ? 'HTML'
          : 'SCORM 1.2';
    try {
      setExportingId(unitId);
      await downloadExport(unitId, format);
      toast.success(`${label} exported successfully`);
    } catch {
      toast.error(`Failed to export ${label}`);
    } finally {
      setExportingId(null);
    }
  };

  const handleQuickCreate = async (contentType: string) => {
    try {
      setQuickCreating(true);
      const response = await quickCreateUnitApi({
        contentType,
        title: quickCreateTitle || undefined,
      });
      const result = response.data;
      toast.success(`Created ${result.contentType.replace('_', ' ')}`);
      quickCreateModal.close();
      setQuickCreateTitle('');
      invalidate();
      fetchUnits();
      navigate(`/units/${result.unitId}/content/${result.contentId}/edit`);
    } catch {
      toast.error('Failed to quick-create content');
    } finally {
      setQuickCreating(false);
    }
  };

  // Split units into regular and quick-created
  const regularUnits = units.filter(
    u =>
      !(
        u.unitMetadata &&
        typeof u.unitMetadata === 'object' &&
        u.unitMetadata.quick_create
      )
  );
  const quickUnits = units.filter(
    u =>
      u.unitMetadata &&
      typeof u.unitMetadata === 'object' &&
      u.unitMetadata.quick_create
  );

  useEffect(() => {
    fetchUnits();
  }, [fetchUnits]);

  // Fetch dashboard metrics when units load
  const fetchMetrics = useCallback(async (unitIds: string[]) => {
    if (unitIds.length === 0) return;
    try {
      setMetricsLoading(true);
      const response = await analyticsApi.getBatchDashboardMetrics(unitIds);
      setMetrics(prev => ({ ...prev, ...response.metrics }));
    } catch {
      // Metrics are non-critical — fail silently
    } finally {
      setMetricsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (units.length > 0) {
      fetchMetrics(units.map(u => u.id));
    }
  }, [units, fetchMetrics]);

  // Fetch archived metrics when expanded
  useEffect(() => {
    if (showArchived && archivedUnits.length > 0) {
      const archivedIds = archivedUnits
        .map(u => u.id)
        .filter(id => !(id in metrics));
      if (archivedIds.length > 0) {
        fetchMetrics(archivedIds);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showArchived, archivedUnits]);

  // Persist sort key
  const handleSortChange = (key: SortKey) => {
    setSortKey(key);
    localStorage.setItem(SORT_STORAGE_KEY, key);
  };

  // Sort comparator
  const sortUnits = useCallback(
    <
      T extends {
        id: string;
        title?: string;
        code?: string;
        updatedAt?: string;
      },
    >(
      list: T[]
    ): T[] => {
      return [...list].sort((a, b) => {
        const ma = metrics[a.id];
        const mb = metrics[b.id];
        switch (sortKey) {
          case 'name-asc':
            return (a.title || a.code || '').localeCompare(
              b.title || b.code || ''
            );
          case 'name-desc':
            return (b.title || b.code || '').localeCompare(
              a.title || a.code || ''
            );
          case 'quality-desc':
            return (mb?.qualityStars ?? 0) - (ma?.qualityStars ?? 0);
          case 'udl-desc':
            return (mb?.udlStars ?? 0) - (ma?.udlStars ?? 0);
          case 'completion-desc':
            return (mb?.weeksWithContent ?? 0) - (ma?.weeksWithContent ?? 0);
          case 'updated-desc':
            return (b.updatedAt || '').localeCompare(a.updatedAt || '');
          default:
            return 0;
        }
      });
    },
    [sortKey, metrics]
  );

  const sortedRegularUnits = useMemo(
    () => sortUnits(regularUnits),
    [regularUnits, sortUnits]
  );
  const sortedQuickUnits = useMemo(
    () => sortUnits(quickUnits),
    [quickUnits, sortUnits]
  );
  const sortedArchivedUnits = useMemo(
    () => sortUnits(archivedUnits),
    [archivedUnits, sortUnits]
  );

  const handlePresetClick = (preset: StructurePreset) => {
    setSelectedPreset(preset.id);
    if (preset.id !== 'custom') {
      setNewUnit(prev => ({
        ...prev,
        durationWeeks: preset.duration!,
        topicLabel: preset.topicLabel!,
        unitLabel: preset.unitLabel!,
      }));
    }
  };

  const doCreateUnit = async (): Promise<string | null> => {
    setError(null);

    if (!newUnit.title || !newUnit.code) {
      setError('Unit title and code are required');
      return null;
    }

    try {
      setCreating(true);
      const unitData = {
        ...newUnit,
        description: newUnit.description || '',
        status: 'draft',
      };

      const response = await createUnitApi(unitData);
      toast.success(
        `${newUnit.unitLabel || 'Learning Program'} created successfully`
      );
      createModal.close();

      const createdId = response.data.id as string;
      const activePreset = STRUCTURE_PRESETS.find(p => p.id === selectedPreset);
      const disableAccreditation =
        (activePreset && !activePreset.accreditationDefaults) ||
        !sectorProfile.showAccreditation;
      if (disableAccreditation) {
        // Fire-and-forget: disable accreditation toggles for non-formal presets
        updateUnitApi(createdId, {
          unitMetadata: {
            features: {
              graduateCapabilities: false,
              aolMapping: false,
              sdgMapping: false,
            },
          },
        }).catch(() => {
          // Silently ignore — user can toggle manually in Settings
        });
      }

      resetForm();
      addUnit(response.data);
      return createdId;
    } catch (err: unknown) {
      const errorMessage = extractErrorMessage(err);
      setError(errorMessage);
      return null;
    } finally {
      setCreating(false);
    }
  };

  const handleCreate = async () => {
    const id = await doCreateUnit();
    if (id) navigate(`/units/${id}`);
  };

  const handleCreateAndImport = async () => {
    const id = await doCreateUnit();
    if (id) navigate(`/import?unitId=${id}`);
  };

  const extractErrorMessage = (err: unknown): string => {
    const error = err as {
      response?: {
        data?: { detail?: string | Array<{ loc?: string[]; msg: string }> };
      };
    };
    const errorDetail = error.response?.data?.detail;

    if (typeof errorDetail === 'string') {
      return errorDetail;
    }

    if (Array.isArray(errorDetail)) {
      const fieldMapping: Record<string, string> = {
        durationWeeks: 'Duration',
        title: 'Unit Title',
        code: 'Unit Code',
      };

      const messages = errorDetail.map(err => {
        const fieldName = err.loc?.[err.loc.length - 1];
        const displayName = fieldName
          ? fieldMapping[fieldName] || fieldName
          : '';
        let msg = err.msg || 'Invalid value';

        const lessMatch = msg.match(/less than or equal to (\d+)/);
        if (lessMatch) msg = `Must be ${lessMatch[1]} or less`;

        const greaterMatch = msg.match(/greater than or equal to (\d+)/);
        if (greaterMatch) msg = `Must be ${greaterMatch[1]} or more`;

        return displayName ? `${displayName}: ${msg}` : msg;
      });

      return messages.join('. ');
    }

    return 'Failed to create unit. Please check all required fields and try again.';
  };

  const resetForm = () => {
    setNewUnit(makeInitialFormData(user?.educationSector));
    setSelectedPreset(
      filteredPresets.length > 0 ? filteredPresets[0].id : 'semester'
    );
    setError(null);
  };

  const openCreateModal = () => {
    resetForm();
    createModal.open();
  };

  const deleteUnit = async (unitId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const unitToDelete = units.find(u => u.id === unitId);
    const unitName = unitToDelete
      ? `"${unitToDelete.code} - ${unitToDelete.title}"`
      : 'this unit';

    const confirmed = await confirm({
      title: `Archive ${unitName}?`,
      message:
        'All data and version history will be preserved. ' +
        'You can restore it later from the archived section.',
      confirmLabel: 'Archive',
      variant: 'warning',
    });

    if (confirmed) {
      try {
        await deleteUnitApi(unitId, false);
        removeUnit(unitId);
        toast.success('Removed from portfolio');
      } catch {
        toast.error('Failed to remove unit');
      }
    }
  };

  const updateField = (field: keyof UnitFormData, value: string | number) => {
    setNewUnit(prev => ({ ...prev, [field]: value }));
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; label: string }> = {
      PLANNING: { color: 'bg-gray-100 text-gray-800', label: 'Planning' },
      ACTIVE: { color: 'bg-green-100 text-green-800', label: 'Active' },
      COMPLETED: { color: 'bg-blue-100 text-blue-800', label: 'Completed' },
      ARCHIVED: { color: 'bg-gray-100 text-gray-600', label: 'Archived' },
      draft: { color: 'bg-yellow-100 text-yellow-800', label: 'Draft' },
    };

    const config = statusConfig[status] || statusConfig.PLANNING;

    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${config.color}`}
      >
        {config.label}
      </span>
    );
  };

  const MetricsRow: React.FC<{
    unitId: string;
    durationWeeks?: number | undefined;
  }> = ({ unitId, durationWeeks = 12 }) => {
    const m = metrics[unitId];
    if (metricsLoading && !m) {
      return (
        <div className='flex items-center gap-4 mt-1.5'>
          <div className='h-3.5 w-24 bg-gray-100 rounded animate-pulse' />
          <div className='h-3.5 w-24 bg-gray-100 rounded animate-pulse' />
          <div className='h-3.5 w-20 bg-gray-100 rounded animate-pulse' />
        </div>
      );
    }
    if (!m) return null;
    const hasContent =
      m.qualityStars > 0 || m.udlStars > 0 || m.weeksWithContent > 0;
    if (!hasContent) {
      return (
        <div className='flex items-center gap-4 mt-1.5 text-xs text-gray-400'>
          <span>No content yet</span>
        </div>
      );
    }
    const completionPct =
      durationWeeks > 0
        ? Math.min(100, Math.round((m.weeksWithContent / durationWeeks) * 100))
        : 0;
    return (
      <div className='flex items-center gap-4 mt-1.5 text-xs text-gray-500'>
        <span className='flex items-center gap-1' title='Quality'>
          <StarRating rating={m.qualityStars} size='sm' />
          <span className='text-gray-400'>Quality</span>
        </span>
        <span className='flex items-center gap-1' title='UDL'>
          <StarRating rating={m.udlStars} size='sm' />
          <span className='text-gray-400'>UDL</span>
        </span>
        <span
          className='flex items-center gap-1.5'
          title={`${m.weeksWithContent}/${durationWeeks} weeks with content`}
        >
          <span>
            {m.weeksWithContent}/{durationWeeks}
          </span>
          <div className='w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden'>
            <div
              className='h-full bg-purple-500 rounded-full transition-all'
              style={{ width: `${completionPct}%` }}
            />
          </div>
        </span>
      </div>
    );
  };

  if (loading) {
    return <LoadingState message='Loading units...' />;
  }

  return (
    <div className='p-6 max-w-7xl mx-auto'>
      {/* Header */}
      <div className='flex justify-between items-start mb-8'>
        <div>
          <h1 className='text-3xl font-bold text-gray-900'>Portfolio</h1>
          <p className='text-gray-600 mt-2'>
            Manage your learning programs and curriculum content
          </p>
        </div>
        <div className='flex items-center gap-3'>
          <Button
            variant='secondary'
            onClick={() => navigate('/import/package')}
          >
            <Upload className='h-5 w-5 mr-2' />
            Import Package
          </Button>
          <Button variant='secondary' onClick={quickCreateModal.open}>
            <Zap className='h-5 w-5 mr-2' />
            Quick Create
          </Button>
          <Button onClick={openCreateModal}>
            <Plus className='h-5 w-5 mr-2' />
            New Learning Program
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      {(() => {
        const metricsWithData = Object.values(metrics).filter(
          m => m.qualityStars > 0 || m.udlStars > 0
        );
        const avgQuality =
          metricsWithData.length > 0
            ? metricsWithData.reduce((sum, m) => sum + m.qualityStars, 0) /
              metricsWithData.length
            : 0;
        const avgUdl =
          metricsWithData.length > 0
            ? metricsWithData.reduce((sum, m) => sum + m.udlStars, 0) /
              metricsWithData.length
            : 0;

        return (
          <div className='grid grid-cols-2 md:grid-cols-5 gap-4 mb-8'>
            <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-4'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-gray-500'>Total Programs</p>
                  <p className='text-2xl font-bold text-gray-900'>
                    {units.length}
                  </p>
                </div>
                <BookOpen className='w-8 h-8 text-purple-500' />
              </div>
            </div>
            <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-4'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-gray-500'>Active</p>
                  <p className='text-2xl font-bold text-gray-900'>
                    {units.filter(u => u.status === 'ACTIVE').length}
                  </p>
                </div>
                <CheckCircle className='w-8 h-8 text-green-500' />
              </div>
            </div>
            <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-4'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-gray-500'>In Progress</p>
                  <p className='text-2xl font-bold text-gray-900'>
                    {
                      units.filter(
                        u => u.status === 'PLANNING' || u.status === 'draft'
                      ).length
                    }
                  </p>
                </div>
                <Clock className='w-8 h-8 text-yellow-500' />
              </div>
            </div>
            <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-4'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-gray-500'>Avg Quality</p>
                  <div className='mt-1'>
                    {avgQuality > 0 ? (
                      <StarRating rating={avgQuality} size='sm' />
                    ) : (
                      <span className='text-sm text-gray-400'>No data</span>
                    )}
                  </div>
                </div>
                <Star className='w-8 h-8 text-amber-500' />
              </div>
            </div>
            <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-4'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-gray-500'>Avg UDL</p>
                  <div className='mt-1'>
                    {avgUdl > 0 ? (
                      <StarRating rating={avgUdl} size='sm' />
                    ) : (
                      <span className='text-sm text-gray-400'>No data</span>
                    )}
                  </div>
                </div>
                <Star className='w-8 h-8 text-teal-500' />
              </div>
            </div>
          </div>
        );
      })()}

      {/* Sort Control */}
      {(regularUnits.length > 0 || quickUnits.length > 0) && (
        <div className='flex items-center justify-end mb-3'>
          <div className='flex items-center gap-1.5 text-sm text-gray-500'>
            <ArrowUpDown className='w-3.5 h-3.5' />
            <select
              value={sortKey}
              onChange={e => handleSortChange(e.target.value as SortKey)}
              className='text-sm border-none bg-transparent text-gray-600 cursor-pointer focus:ring-0 pr-6'
            >
              {SORT_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Units List */}
      {regularUnits.length === 0 && quickUnits.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title='No Learning Programs Yet'
          description='Create your first learning program to start building your curriculum. Choose a preset that matches your teaching context.'
          actionLabel='Create Your First Learning Program'
          onAction={openCreateModal}
          tips={[
            {
              title: 'Start with the basics',
              description:
                'Add a code, title, and duration. You can refine details later.',
            },
            {
              title: 'Build your schedule',
              description:
                'Once created, structure your content with topics, learning outcomes, and materials.',
            },
            {
              title: 'Create content',
              description:
                'Write, import, research, or generate materials aligned with your teaching style.',
            },
          ]}
        />
      ) : (
        <>
          {regularUnits.length > 0 && (
            <div className='bg-white rounded-lg shadow-sm border border-gray-200'>
              <div className='px-6 py-4 border-b border-gray-200'>
                <h2 className='text-lg font-semibold text-gray-900'>
                  My Learning Programs
                </h2>
              </div>
              <div className='divide-y divide-gray-200'>
                {sortedRegularUnits.map(unit => (
                  <div
                    key={unit.id}
                    className='px-6 py-4 hover:bg-gray-50 cursor-pointer transition flex items-center justify-between'
                    onClick={() => navigate(`/units/${unit.id}`)}
                  >
                    <div className='flex-1 min-w-0'>
                      <div className='flex items-center gap-3'>
                        <h3 className='text-sm font-semibold text-gray-900'>
                          {unit.code}
                        </h3>
                        {getStatusBadge(unit.status)}
                      </div>
                      <p className='text-sm text-gray-600 mt-1 truncate'>
                        {unit.title}
                      </p>
                      <div className='flex items-center gap-4 mt-2 text-xs text-gray-500'>
                        <span className='flex items-center gap-1'>
                          <Calendar className='w-3.5 h-3.5' />
                          {unit.semester}
                        </span>
                        <span>{unit.creditPoints} credits</span>
                        <span>
                          {unit.durationWeeks}{' '}
                          {(unit.topicLabel || 'Week').toLowerCase()}s
                        </span>
                        {unit.pedagogyType && (
                          <span className='capitalize'>
                            {unit.pedagogyType.replace(/-/g, ' ')}
                          </span>
                        )}
                      </div>
                      <MetricsRow
                        unitId={unit.id}
                        durationWeeks={unit.durationWeeks}
                      />
                    </div>
                    <div className='flex items-center gap-1 ml-4'>
                      <button
                        onClick={e => handleClone(unit.id, e)}
                        disabled={cloningId === unit.id}
                        className='p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition disabled:opacity-50'
                        title='Clone Unit'
                      >
                        <Copy className='h-4 w-4' />
                      </button>
                      <div
                        className='relative'
                        ref={
                          exportMenuUnitId === unit.id
                            ? exportMenuRef
                            : undefined
                        }
                      >
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            setImportMenuUnitId(null);
                            setExportMenuUnitId(
                              exportMenuUnitId === unit.id ? null : unit.id
                            );
                          }}
                          disabled={exportingId === unit.id}
                          className='p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition disabled:opacity-50'
                          title='Export'
                        >
                          <Download className='h-4 w-4' />
                        </button>
                        {exportMenuUnitId === unit.id && (
                          <div className='absolute right-0 mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50'>
                            <button
                              className='w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-t-lg'
                              onClick={e => {
                                e.stopPropagation();
                                handleQuickExport(unit.id, 'imscc');
                              }}
                            >
                              IMSCC v1.1 (.imscc)
                            </button>
                            <button
                              className='w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50'
                              onClick={e => {
                                e.stopPropagation();
                                handleQuickExport(unit.id, 'scorm');
                              }}
                            >
                              SCORM 1.2 (.zip)
                            </button>
                            <button
                              className='w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-b-lg'
                              onClick={e => {
                                e.stopPropagation();
                                handleQuickExport(unit.id, 'html');
                              }}
                            >
                              HTML (.html)
                            </button>
                          </div>
                        )}
                      </div>
                      <div
                        className='relative'
                        ref={
                          importMenuUnitId === unit.id
                            ? importMenuRef
                            : undefined
                        }
                      >
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            setExportMenuUnitId(null);
                            setImportMenuUnitId(
                              importMenuUnitId === unit.id ? null : unit.id
                            );
                          }}
                          className='p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition'
                          title='Import'
                        >
                          <Upload className='h-4 w-4' />
                        </button>
                        {importMenuUnitId === unit.id && (
                          <div className='absolute right-0 mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50'>
                            <button
                              className='w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-t-lg'
                              onClick={e => {
                                e.stopPropagation();
                                setImportMenuUnitId(null);
                                navigate(`/import?unitId=${unit.id}`);
                              }}
                            >
                              Import Files
                            </button>
                            <button
                              className='w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-b-lg'
                              onClick={e => {
                                e.stopPropagation();
                                setImportMenuUnitId(null);
                                navigate('/import/package');
                              }}
                            >
                              Import Package
                            </button>
                          </div>
                        )}
                      </div>
                      <button
                        onClick={e => deleteUnit(unit.id, e)}
                        className='p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition'
                        title='Remove from Portfolio'
                      >
                        <Trash2 className='h-4 w-4' />
                      </button>
                      <ChevronRight className='h-5 w-5 text-gray-400' />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Content Section */}
          {quickUnits.length > 0 && (
            <div className='mt-6'>
              <button
                onClick={() => setShowQuickContent(!showQuickContent)}
                className='flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition'
              >
                <Zap className='w-4 h-4' />
                <span>Quick Content ({quickUnits.length})</span>
                {showQuickContent ? (
                  <ChevronUp className='w-4 h-4' />
                ) : (
                  <ChevronDown className='w-4 h-4' />
                )}
              </button>

              {showQuickContent && (
                <div className='mt-3 bg-white rounded-lg border border-gray-200 shadow-sm'>
                  <div className='divide-y divide-gray-200'>
                    {sortedQuickUnits.map(unit => (
                      <div
                        key={unit.id}
                        className='px-6 py-3 hover:bg-gray-50 cursor-pointer transition flex items-center justify-between'
                        onClick={() => navigate(`/units/${unit.id}`)}
                      >
                        <div className='min-w-0'>
                          <h3 className='text-sm font-medium text-gray-900'>
                            {unit.title}
                          </h3>
                          <p className='text-xs text-gray-500 mt-0.5'>
                            {new Date(unit.createdAt).toLocaleDateString()}
                          </p>
                          <MetricsRow
                            unitId={unit.id}
                            durationWeeks={unit.durationWeeks}
                          />
                        </div>
                        <div className='flex items-center gap-2 ml-4'>
                          <button
                            onClick={e => deleteUnit(unit.id, e)}
                            className='p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition'
                            title='Remove'
                          >
                            <Trash2 className='h-4 w-4' />
                          </button>
                          <ChevronRight className='h-5 w-5 text-gray-400' />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Archived Units Toggle */}
      <div className='mt-6'>
        <button
          onClick={toggleArchived}
          className='flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition'
        >
          <Archive className='w-4 h-4' />
          <span>
            Archived units
            {archivedUnits.length > 0 && showArchived
              ? ` (${archivedUnits.length})`
              : ''}
          </span>
          {showArchived ? (
            <ChevronUp className='w-4 h-4' />
          ) : (
            <ChevronDown className='w-4 h-4' />
          )}
        </button>

        {showArchived && (
          <div className='mt-3'>
            {archivedLoading ? (
              <p className='text-sm text-gray-400 py-4'>
                Loading archived units...
              </p>
            ) : archivedUnits.length === 0 ? (
              <p className='text-sm text-gray-400 py-4'>No archived units.</p>
            ) : (
              <div className='bg-gray-50 rounded-lg border border-gray-200'>
                <div className='divide-y divide-gray-200'>
                  {sortedArchivedUnits.map(archivedUnit => (
                    <div
                      key={archivedUnit.id}
                      className='px-6 py-3 flex items-center justify-between opacity-70'
                    >
                      <div className='min-w-0'>
                        <div className='flex items-center gap-2'>
                          <h3 className='text-sm font-medium text-gray-600'>
                            {archivedUnit.code}
                          </h3>
                          <span className='inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500'>
                            Archived
                          </span>
                        </div>
                        <p className='text-sm text-gray-500 truncate'>
                          {archivedUnit.title}
                        </p>
                        <MetricsRow
                          unitId={archivedUnit.id}
                          durationWeeks={archivedUnit.durationWeeks}
                        />
                      </div>
                      <Button
                        variant='secondary'
                        size='sm'
                        onClick={() => handleRestoreUnit(archivedUnit.id)}
                        loading={restoringId === archivedUnit.id}
                      >
                        <RotateCcw className='w-3.5 h-3.5 mr-1' />
                        Restore
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create Unit Modal */}
      <Modal
        isOpen={createModal.isOpen}
        onClose={createModal.close}
        title={`Create New ${newUnit.unitLabel || 'Learning Program'}`}
        size='lg'
      >
        {error && (
          <Alert
            variant='error'
            onDismiss={() => setError(null)}
            className='mb-4'
          >
            {error}
          </Alert>
        )}

        <div className='space-y-4'>
          <FormInput
            label={`${newUnit.unitLabel || 'Learning Program'} Title`}
            required
            value={newUnit.title}
            onChange={e => updateField('title', e.target.value)}
            placeholder='e.g., Programming Fundamentals'
          />

          <FormInput
            label={sectorProfile.codeLabel}
            required
            value={newUnit.code}
            onChange={e => updateField('code', e.target.value)}
            placeholder={sectorProfile.codePlaceholder}
          />

          <FormTextarea
            label='Description'
            value={newUnit.description}
            onChange={e => updateField('description', e.target.value)}
            rows={3}
            placeholder='Brief description of the unit...'
          />

          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Structure
            </label>
            <div className='flex flex-wrap gap-2'>
              {filteredPresets.map(preset => (
                <button
                  key={preset.id}
                  type='button'
                  onClick={() => handlePresetClick(preset)}
                  title={preset.tooltip}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition ${
                    selectedPreset === preset.id
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            {selectedPreset === 'custom' ? (
              <div className='grid grid-cols-3 gap-3 mt-3'>
                <FormInput
                  label='Duration'
                  type='number'
                  value={newUnit.durationWeeks}
                  onChange={e =>
                    updateField('durationWeeks', parseInt(e.target.value))
                  }
                  min={1}
                  max={52}
                />
                <FormInput
                  label='Topic Label'
                  type='text'
                  value={newUnit.topicLabel}
                  onChange={e => updateField('topicLabel', e.target.value)}
                  placeholder='e.g. Week, Module, Session'
                />
                <FormInput
                  label='Label'
                  type='text'
                  value={newUnit.unitLabel}
                  onChange={e => updateField('unitLabel', e.target.value)}
                  placeholder='e.g. Unit, Workshop, Program'
                />
              </div>
            ) : (
              <p className='text-sm text-gray-500 mt-2'>
                {newUnit.durationWeeks} {newUnit.topicLabel.toLowerCase()}s
              </p>
            )}
          </div>

          <FormSelect
            label='Pedagogy Type'
            value={newUnit.pedagogyType}
            onChange={e => updateField('pedagogyType', e.target.value)}
            options={pedagogyOptions}
          />

          <FormSelect
            label='Difficulty Level'
            value={newUnit.difficultyLevel}
            onChange={e => updateField('difficultyLevel', e.target.value)}
            options={difficultyOptions}
          />
        </div>

        <div className='flex justify-end space-x-3 mt-6'>
          <Button variant='secondary' onClick={createModal.close}>
            Cancel
          </Button>
          <Button
            variant='secondary'
            onClick={handleCreateAndImport}
            loading={creating}
          >
            <Upload className='h-4 w-4 mr-2' />
            Create and Import
          </Button>
          <Button onClick={handleCreate} loading={creating}>
            Create {newUnit.unitLabel || 'Learning Program'}
          </Button>
        </div>
      </Modal>

      {/* Quick Create Modal */}
      <Modal
        isOpen={quickCreateModal.isOpen}
        onClose={quickCreateModal.close}
        title='Quick Create'
        size='lg'
      >
        <p className='text-sm text-gray-600 mb-4'>
          Choose a content type. A lightweight unit will be created
          automatically.
        </p>

        <FormInput
          label='Title (optional)'
          value={quickCreateTitle}
          onChange={e => setQuickCreateTitle(e.target.value)}
          placeholder='Auto-generated if left blank'
        />

        <div className='grid grid-cols-3 sm:grid-cols-4 gap-3 mt-4'>
          {contentTypeCards.map(ct => {
            const Icon = ct.icon;
            return (
              <button
                key={ct.value}
                disabled={quickCreating}
                onClick={() => handleQuickCreate(ct.value)}
                className='flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 hover:border-purple-400 hover:bg-purple-50 transition disabled:opacity-50 disabled:cursor-not-allowed'
              >
                <Icon className='w-6 h-6 text-purple-600' />
                <span className='text-xs font-medium text-gray-700'>
                  {ct.label}
                </span>
              </button>
            );
          })}
        </div>

        {quickCreating && (
          <p className='text-sm text-gray-500 mt-4 text-center'>Creating...</p>
        )}
      </Modal>
    </div>
  );
};

export default DashboardPage;
