import React, { useState, useEffect } from 'react';
import {
  Plus,
  Edit2,
  Trash2,
  Calendar,
  Clock,
  Users,
  FileText,
  AlertCircle,
  CheckCircle,
  BarChart,
} from 'lucide-react';
import { assessmentsApi } from '../../services/unitStructureApi';
import {
  AssessmentResponse,
  AssessmentCreate,
  AssessmentUpdate,
  AssessmentType,
  AssessmentCategory,
  AssessmentStatus,
  GradeDistribution,
} from '../../types/unitStructure';
import toast from 'react-hot-toast';

interface AssessmentsManagerProps {
  unitId: string;
}

interface AssessmentFormData {
  title: string;
  type: AssessmentType;
  category: AssessmentCategory;
  weight: number;
  description: string;
  releaseWeek: number | undefined;
  dueWeek: number | undefined;
  duration: number | undefined;
  wordCount: number | undefined;
  groupWork: boolean;
  status: AssessmentStatus;
}

const categoryIcons: Record<AssessmentCategory, React.ReactElement> = {
  [AssessmentCategory.EXAM]: <FileText className='w-4 h-4' />,
  [AssessmentCategory.ASSIGNMENT]: <FileText className='w-4 h-4' />,
  [AssessmentCategory.PROJECT]: <Users className='w-4 h-4' />,
  [AssessmentCategory.PRESENTATION]: <Users className='w-4 h-4' />,
  [AssessmentCategory.PARTICIPATION]: <Users className='w-4 h-4' />,
  [AssessmentCategory.QUIZ]: <FileText className='w-4 h-4' />,
  [AssessmentCategory.LAB_REPORT]: <FileText className='w-4 h-4' />,
  [AssessmentCategory.PORTFOLIO]: <FileText className='w-4 h-4' />,
  [AssessmentCategory.OTHER]: <FileText className='w-4 h-4' />,
};

const AssessmentCard: React.FC<{
  assessment: AssessmentResponse;
  onEdit: (assessment: AssessmentResponse) => void;
  onDelete: (id: string) => void;
}> = ({ assessment, onEdit, onDelete }) => {
  const typeColor =
    assessment.type === AssessmentType.FORMATIVE
      ? 'bg-green-100 text-green-800'
      : 'bg-blue-100 text-blue-800';

  const statusColor = {
    [AssessmentStatus.DRAFT]: 'bg-yellow-100 text-yellow-800',
    [AssessmentStatus.PUBLISHED]: 'bg-green-100 text-green-800',
    [AssessmentStatus.ARCHIVED]: 'bg-gray-100 text-gray-800',
  }[assessment.status];

  return (
    <div className='bg-white border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow'>
      <div className='flex justify-between items-start'>
        <div className='flex-1'>
          <div className='flex items-center space-x-2 mb-2'>
            <span
              className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${typeColor}`}
            >
              {assessment.type}
            </span>
            <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800'>
              {categoryIcons[assessment.category]}
              <span className='ml-1'>
                {assessment.category.replace('_', ' ')}
              </span>
            </span>
            <span
              className={`px-2 py-1 rounded-full text-xs font-medium ${statusColor}`}
            >
              {assessment.status}
            </span>
            {assessment.groupWork && (
              <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800'>
                <Users className='w-3 h-3 mr-1' />
                Group
              </span>
            )}
          </div>

          <h4 className='font-medium text-gray-900 mb-1'>{assessment.title}</h4>

          <div className='flex items-center space-x-4 text-sm text-gray-600'>
            <span className='font-semibold text-gray-900'>
              {assessment.weight}% weight
            </span>

            {assessment.releaseWeek && (
              <span className='flex items-center'>
                <Calendar className='w-3 h-3 mr-1' />
                Release: Week {assessment.releaseWeek}
              </span>
            )}

            {assessment.dueWeek && (
              <span className='flex items-center'>
                <Calendar className='w-3 h-3 mr-1' />
                Due: Week {assessment.dueWeek}
              </span>
            )}

            {assessment.duration && (
              <span className='flex items-center'>
                <Clock className='w-3 h-3 mr-1' />
                {assessment.duration} min
              </span>
            )}

            {assessment.wordCount && <span>{assessment.wordCount} words</span>}
          </div>

          {assessment.description && (
            <p className='mt-2 text-sm text-gray-600'>
              {assessment.description}
            </p>
          )}
        </div>

        <div className='flex items-center space-x-2 ml-4'>
          <button
            onClick={() => onEdit(assessment)}
            className='p-1 text-gray-400 hover:text-blue-600'
            title='Edit'
          >
            <Edit2 className='w-4 h-4' />
          </button>
          <button
            onClick={() => onDelete(assessment.id)}
            className='p-1 text-gray-400 hover:text-red-600'
            title='Delete'
          >
            <Trash2 className='w-4 h-4' />
          </button>
        </div>
      </div>
    </div>
  );
};

export const AssessmentsManager: React.FC<AssessmentsManagerProps> = ({
  unitId,
}) => {
  const [assessments, setAssessments] = useState<AssessmentResponse[]>([]);
  const [gradeDistribution, setGradeDistribution] =
    useState<GradeDistribution | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingAssessment, setEditingAssessment] =
    useState<AssessmentResponse | null>(null);
  const [formData, setFormData] = useState<AssessmentFormData>({
    title: '',
    type: AssessmentType.SUMMATIVE,
    category: AssessmentCategory.ASSIGNMENT,
    weight: 0,
    description: '',
    releaseWeek: undefined,
    dueWeek: undefined,
    duration: undefined,
    wordCount: undefined,
    groupWork: false,
    status: AssessmentStatus.DRAFT,
  });

  useEffect(() => {
    fetchAssessments();
  }, [unitId]);

  const fetchAssessments = async () => {
    try {
      setLoading(true);
      const [assessmentsData, distributionData] = await Promise.all([
        assessmentsApi.getAssessmentsByUnit(unitId),
        assessmentsApi.getGradeDistribution(unitId),
      ]);
      setAssessments(assessmentsData);
      setGradeDistribution(distributionData);
    } catch (error) {
      toast.error('Failed to fetch assessments');
      console.error('Error fetching assessments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (editingAssessment) {
        const updateData: AssessmentUpdate = {
          title: formData.title,
          type: formData.type,
          category: formData.category,
          weight: formData.weight,
          ...(formData.description && { description: formData.description }),
          ...(formData.releaseWeek !== undefined && {
            releaseWeek: formData.releaseWeek,
          }),
          ...(formData.dueWeek !== undefined && { dueWeek: formData.dueWeek }),
          ...(formData.duration !== undefined && {
            duration: formData.duration,
          }),
          ...(formData.wordCount !== undefined && {
            wordCount: formData.wordCount,
          }),
          groupWork: formData.groupWork,
          status: formData.status,
        };

        await assessmentsApi.updateAssessment(editingAssessment.id, updateData);
        toast.success('Assessment updated successfully');
      } else {
        const createData: AssessmentCreate = {
          title: formData.title,
          type: formData.type,
          category: formData.category,
          weight: formData.weight,
          ...(formData.description && { description: formData.description }),
          ...(formData.releaseWeek !== undefined && {
            releaseWeek: formData.releaseWeek,
          }),
          ...(formData.dueWeek !== undefined && { dueWeek: formData.dueWeek }),
          ...(formData.duration !== undefined && {
            duration: formData.duration,
          }),
          ...(formData.wordCount !== undefined && {
            wordCount: formData.wordCount,
          }),
          groupWork: formData.groupWork,
          status: formData.status,
        };

        await assessmentsApi.createAssessment(unitId, createData);
        toast.success('Assessment created successfully');
      }

      await fetchAssessments();
      handleCancel();
    } catch (error) {
      toast.error(
        editingAssessment
          ? 'Failed to update assessment'
          : 'Failed to create assessment'
      );
      console.error('Error saving assessment:', error);
    }
  };

  const handleEdit = (assessment: AssessmentResponse) => {
    setEditingAssessment(assessment);
    setFormData({
      title: assessment.title,
      type: assessment.type,
      category: assessment.category,
      weight: assessment.weight,
      description: assessment.description || '',
      releaseWeek: assessment.releaseWeek,
      dueWeek: assessment.dueWeek,
      duration: assessment.duration,
      wordCount: assessment.wordCount,
      groupWork: assessment.groupWork,
      status: assessment.status,
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this assessment?')) return;

    try {
      await assessmentsApi.deleteAssessment(id);
      toast.success('Assessment deleted successfully');
      await fetchAssessments();
    } catch (error) {
      toast.error('Failed to delete assessment');
      console.error('Error deleting assessment:', error);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingAssessment(null);
    setFormData({
      title: '',
      type: AssessmentType.SUMMATIVE,
      category: AssessmentCategory.ASSIGNMENT,
      weight: 0,
      description: '',
      releaseWeek: undefined,
      dueWeek: undefined,
      duration: undefined,
      wordCount: undefined,
      groupWork: false,
      status: AssessmentStatus.DRAFT,
    });
  };

  if (loading) {
    return <div className='animate-pulse'>Loading assessments...</div>;
  }

  const totalWeight = gradeDistribution?.totalWeight || 0;
  const isWeightValid = Math.abs(totalWeight - 100) < 0.01;

  return (
    <div className='space-y-6'>
      <div className='flex justify-between items-center'>
        <div>
          <h3 className='text-lg font-semibold text-gray-900'>Assessments</h3>
          <p className='mt-1 text-sm text-gray-600'>
            Manage formative and summative assessments
          </p>
        </div>

        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className='inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700'
          >
            <Plus className='w-4 h-4 mr-2' />
            Add Assessment
          </button>
        )}
      </div>

      {gradeDistribution && (
        <div
          className={`p-4 rounded-lg border ${isWeightValid ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}
        >
          <div className='flex items-center justify-between'>
            <div className='flex items-center'>
              {isWeightValid ? (
                <CheckCircle className='w-5 h-5 text-green-600 mr-2' />
              ) : (
                <AlertCircle className='w-5 h-5 text-red-600 mr-2' />
              )}
              <span
                className={`font-medium ${isWeightValid ? 'text-green-900' : 'text-red-900'}`}
              >
                Total Weight: {totalWeight.toFixed(1)}%
              </span>
              {!isWeightValid && (
                <span className='ml-2 text-sm text-red-700'>
                  (Should equal 100%)
                </span>
              )}
            </div>

            <button
              onClick={() =>
                assessmentsApi.getAssessmentWorkload(unitId).then(data => {
                  console.log('Workload analysis:', data); // eslint-disable-line no-console
                  toast.success('Check console for workload analysis');
                })
              }
              className='inline-flex items-center px-2 py-1 text-sm text-blue-600 hover:text-blue-800'
            >
              <BarChart className='w-4 h-4 mr-1' />
              View Workload
            </button>
          </div>

          {gradeDistribution.byCategory &&
            Object.keys(gradeDistribution.byCategory).length > 0 && (
              <div className='mt-3 grid grid-cols-3 gap-2'>
                {Object.entries(gradeDistribution.byCategory).map(
                  ([category, weight]) => (
                    <div key={category} className='text-sm'>
                      <span className='text-gray-600'>
                        {category.replace('_', ' ')}:
                      </span>
                      <span className='ml-1 font-medium'>{weight}%</span>
                    </div>
                  )
                )}
              </div>
            )}
        </div>
      )}

      {showForm && (
        <div className='bg-white border rounded-lg p-6'>
          <h4 className='text-lg font-medium mb-4'>
            {editingAssessment ? 'Edit Assessment' : 'Add New Assessment'}
          </h4>

          <form onSubmit={handleSubmit} className='space-y-4'>
            <div>
              <label className='block text-sm font-medium text-gray-700'>
                Title *
              </label>
              <input
                type='text'
                value={formData.title}
                onChange={e =>
                  setFormData({ ...formData, title: e.target.value })
                }
                className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                required
              />
            </div>

            <div className='grid grid-cols-3 gap-4'>
              <div>
                <label className='block text-sm font-medium text-gray-700'>
                  Type *
                </label>
                <select
                  value={formData.type}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      type: e.target.value as AssessmentType,
                    })
                  }
                  className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                >
                  {Object.values(AssessmentType).map(type => (
                    <option key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700'>
                  Category *
                </label>
                <select
                  value={formData.category}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      category: e.target.value as AssessmentCategory,
                    })
                  }
                  className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                >
                  {Object.values(AssessmentCategory).map(category => (
                    <option key={category} value={category}>
                      {category.replace('_', ' ').charAt(0).toUpperCase() +
                        category.replace('_', ' ').slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700'>
                  Weight (%) *
                </label>
                <input
                  type='number'
                  value={formData.weight}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      weight: parseFloat(e.target.value) || 0,
                    })
                  }
                  className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                  min='0'
                  max='100'
                  step='0.1'
                  required
                />
              </div>
            </div>

            <div>
              <label className='block text-sm font-medium text-gray-700'>
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={e =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={3}
                className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
              />
            </div>

            <div className='grid grid-cols-2 gap-4'>
              <div>
                <label className='block text-sm font-medium text-gray-700'>
                  Release Week
                </label>
                <input
                  type='number'
                  value={formData.releaseWeek || ''}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      releaseWeek: e.target.value
                        ? parseInt(e.target.value)
                        : undefined,
                    })
                  }
                  className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                  min='1'
                  max='52'
                />
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700'>
                  Due Week
                </label>
                <input
                  type='number'
                  value={formData.dueWeek || ''}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      dueWeek: e.target.value
                        ? parseInt(e.target.value)
                        : undefined,
                    })
                  }
                  className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                  min='1'
                  max='52'
                />
              </div>
            </div>

            <div className='grid grid-cols-2 gap-4'>
              <div>
                <label className='block text-sm font-medium text-gray-700'>
                  Duration (minutes)
                </label>
                <input
                  type='number'
                  value={formData.duration || ''}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      duration: e.target.value
                        ? parseInt(e.target.value)
                        : undefined,
                    })
                  }
                  className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                  min='0'
                />
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700'>
                  Word Count
                </label>
                <input
                  type='number'
                  value={formData.wordCount || ''}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      wordCount: e.target.value
                        ? parseInt(e.target.value)
                        : undefined,
                    })
                  }
                  className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                  min='0'
                />
              </div>
            </div>

            <div className='flex items-center space-x-4'>
              <label className='flex items-center'>
                <input
                  type='checkbox'
                  checked={formData.groupWork}
                  onChange={e =>
                    setFormData({ ...formData, groupWork: e.target.checked })
                  }
                  className='rounded border-gray-300 text-blue-600 focus:ring-blue-500'
                />
                <span className='ml-2 text-sm text-gray-700'>Group Work</span>
              </label>

              <div className='flex items-center'>
                <label className='text-sm font-medium text-gray-700 mr-2'>
                  Status:
                </label>
                <select
                  value={formData.status}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      status: e.target.value as AssessmentStatus,
                    })
                  }
                  className='rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                >
                  {Object.values(AssessmentStatus).map(status => (
                    <option key={status} value={status}>
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className='flex justify-end space-x-3'>
              <button
                type='button'
                onClick={handleCancel}
                className='px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50'
              >
                Cancel
              </button>
              <button
                type='submit'
                className='px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700'
              >
                {editingAssessment ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className='space-y-3'>
        {assessments.length === 0 ? (
          <div className='text-center py-8 text-gray-500'>
            No assessments added yet.
          </div>
        ) : (
          assessments.map(assessment => (
            <AssessmentCard
              key={assessment.id}
              assessment={assessment}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>
    </div>
  );
};
