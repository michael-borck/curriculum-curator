import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  BookOpen,
  Calendar,
  ChevronRight,
  Trash2,
  CheckCircle,
  Clock,
  TrendingUp,
  Archive,
  RotateCcw,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  createUnit as createUnitApi,
  deleteUnit as deleteUnitApi,
  getArchivedUnits as getArchivedUnitsApi,
  restoreUnit as restoreUnitApi,
} from '../services/api';
import { useUnitsStore } from '../stores/unitsStore';
import {
  Modal,
  Alert,
  Button,
  LoadingState,
  EmptyState,
  FormInput,
  FormTextarea,
  FormSelect,
} from '../components/ui';
import { useModal } from '../hooks';

import toast from 'react-hot-toast';

interface UnitFormData {
  title: string;
  code: string;
  description: string;
  year: number;
  semester: string;
  pedagogyType: string;
  difficultyLevel: string;
  durationWeeks: number;
  creditPoints: number;
  prerequisites: string;
  learningHours: number;
}

const initialFormData: UnitFormData = {
  title: '',
  code: '',
  description: '',
  year: new Date().getFullYear(),
  semester: 'semester_1',
  pedagogyType: 'inquiry-based',
  difficultyLevel: 'intermediate',
  durationWeeks: 12,
  creditPoints: 25,
  prerequisites: '',
  learningHours: 150,
};

const semesterOptions = [
  { value: 'semester_1', label: 'Semester 1' },
  { value: 'semester_2', label: 'Semester 2' },
  { value: 'summer', label: 'Summer' },
  { value: 'winter', label: 'Winter' },
];

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

const DashboardPage = () => {
  const navigate = useNavigate();
  const createModal = useModal();

  // Use shared units store
  const { units, loading, fetchUnits, addUnit, removeUnit, invalidate } =
    useUnitsStore();

  const [newUnit, setNewUnit] = useState<UnitFormData>(initialFormData);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

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

  useEffect(() => {
    fetchUnits();
  }, [fetchUnits]);

  const createUnit = async () => {
    setError(null);

    if (!newUnit.title || !newUnit.code) {
      setError('Unit title and code are required');
      return;
    }

    try {
      setCreating(true);
      const unitData = {
        title: newUnit.title,
        code: newUnit.code,
        description: newUnit.description || '',
        year: newUnit.year,
        semester: newUnit.semester,
        pedagogyType: newUnit.pedagogyType,
        difficultyLevel: newUnit.difficultyLevel,
        durationWeeks: newUnit.durationWeeks,
        creditPoints: newUnit.creditPoints,
        prerequisites: newUnit.prerequisites || '',
        learningHours: newUnit.learningHours || 150,
        status: 'draft',
      };

      const response = await createUnitApi(unitData);
      toast.success('Unit created successfully');
      createModal.close();
      resetForm();
      // Add unit to store so sidebar updates immediately
      addUnit(response.data);
      // Navigate to the new unit
      navigate(`/units/${response.data.id}`);
    } catch (err: unknown) {
      const errorMessage = extractErrorMessage(err);
      setError(errorMessage);
    } finally {
      setCreating(false);
    }
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
        creditPoints: 'Credit Points',
        durationWeeks: 'Duration',
        learningHours: 'Learning Hours',
        title: 'Unit Title',
        code: 'Unit Code',
        year: 'Year',
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
    setNewUnit(initialFormData);
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

    const confirmed = window.confirm(
      `Remove ${unitName} from the dashboard?\n\n` +
        'All data and version history will be preserved. ' +
        'You can restore it later from the archived units section.'
    );

    if (confirmed) {
      try {
        await deleteUnitApi(unitId, false);
        removeUnit(unitId);
        toast.success('Unit removed from dashboard');
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

  if (loading) {
    return <LoadingState message='Loading units...' />;
  }

  return (
    <div className='p-6 max-w-7xl mx-auto'>
      {/* Header */}
      <div className='flex justify-between items-start mb-8'>
        <div>
          <h1 className='text-3xl font-bold text-gray-900'>Dashboard</h1>
          <p className='text-gray-600 mt-2'>
            Manage your units and curriculum content
          </p>
        </div>
        <Button onClick={openCreateModal}>
          <Plus className='h-5 w-5 mr-2' />
          New Unit
        </Button>
      </div>

      {/* Quick Stats */}
      <div className='grid grid-cols-1 md:grid-cols-4 gap-4 mb-8'>
        <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-4'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-sm text-gray-500'>Total Units</p>
              <p className='text-2xl font-bold text-gray-900'>{units.length}</p>
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
              <p className='text-sm text-gray-500'>Total Credits</p>
              <p className='text-2xl font-bold text-gray-900'>
                {units.reduce((sum, u) => sum + (u.creditPoints || 0), 0)}
              </p>
            </div>
            <TrendingUp className='w-8 h-8 text-blue-500' />
          </div>
        </div>
      </div>

      {/* Units List */}
      {units.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title='No Units Yet'
          description='Create your first unit to start building your curriculum. Each unit represents a subject you teach for a semester.'
          actionLabel='Create Your First Unit'
          onAction={openCreateModal}
          tips={[
            {
              title: 'Start with unit basics',
              description:
                'Add your unit code, title, and duration. You can refine details later.',
            },
            {
              title: 'Use AI to generate schedules',
              description:
                'Once created, use the Course Planner to auto-generate a 12-week teaching schedule.',
            },
            {
              title: 'Create content with AI assistance',
              description:
                'Generate lectures, tutorials, and assessments aligned with your teaching style.',
            },
          ]}
        />
      ) : (
        <div className='bg-white rounded-lg shadow-sm border border-gray-200'>
          <div className='px-6 py-4 border-b border-gray-200'>
            <h2 className='text-lg font-semibold text-gray-900'>My Units</h2>
          </div>
          <div className='divide-y divide-gray-200'>
            {units.map(unit => (
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
                    <span>{unit.durationWeeks} weeks</span>
                    {unit.pedagogyType && (
                      <span className='capitalize'>
                        {unit.pedagogyType.replace(/-/g, ' ')}
                      </span>
                    )}
                  </div>
                </div>
                <div className='flex items-center gap-2 ml-4'>
                  <button
                    onClick={e => deleteUnit(unit.id, e)}
                    className='p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition'
                    title='Remove from Dashboard'
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
                  {archivedUnits.map(archivedUnit => (
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
        title='Create New Unit'
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
            label='Unit Title'
            required
            value={newUnit.title}
            onChange={e => updateField('title', e.target.value)}
            placeholder='e.g., Programming Fundamentals'
          />

          <FormInput
            label='Unit Code'
            required
            value={newUnit.code}
            onChange={e => updateField('code', e.target.value)}
            placeholder='e.g., CS101'
          />

          <FormTextarea
            label='Description'
            value={newUnit.description}
            onChange={e => updateField('description', e.target.value)}
            rows={3}
            placeholder='Brief description of the unit...'
          />

          <div className='grid grid-cols-2 gap-4'>
            <FormInput
              label='Year'
              type='number'
              value={newUnit.year}
              onChange={e => updateField('year', parseInt(e.target.value))}
              min={2020}
              max={2100}
            />

            <FormSelect
              label='Semester'
              value={newUnit.semester}
              onChange={e => updateField('semester', e.target.value)}
              options={semesterOptions}
            />
          </div>

          <div className='grid grid-cols-2 gap-4'>
            <FormInput
              label='Credit Points'
              type='number'
              value={newUnit.creditPoints}
              onChange={e =>
                updateField('creditPoints', parseInt(e.target.value))
              }
              min={1}
              max={100}
            />

            <FormInput
              label='Duration (weeks)'
              type='number'
              value={newUnit.durationWeeks}
              onChange={e =>
                updateField('durationWeeks', parseInt(e.target.value))
              }
              min={1}
              max={52}
            />
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
          <Button onClick={createUnit} loading={creating}>
            Create Unit
          </Button>
        </div>
      </Modal>
    </div>
  );
};

export default DashboardPage;
