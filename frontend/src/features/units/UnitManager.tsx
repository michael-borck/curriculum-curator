import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  BookOpen,
  Users,
  Calendar,
  ChevronRight,
  Edit,
  Trash2,
  FileText,
  Loader2,
  CheckCircle,
  Clock,
} from 'lucide-react';
import api from '../../services/api';

interface Unit {
  id: string;
  title: string;
  code: string;
  description: string;
  status: string;
  teaching_philosophy: string;
  semester: string;
  credits: number;
  created_at: string;
  is_active: boolean;
  progress_percentage?: number;
  module_count?: number;
  material_count?: number;
  lrd_count?: number;
}

const UnitManager = () => {
  const navigate = useNavigate();
  const [units, setUnits] = useState<Unit[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUnit, setNewUnit] = useState({
    title: '',
    code: '',
    description: '',
    teaching_philosophy: 'TRADITIONAL',
    semester: '2024-S1',
    credits: 3,
  });
  const [errors, setErrors] = useState<any>({});

  useEffect(() => {
    fetchUnits();
  }, []);

  const fetchUnits = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/units');
      console.log('Fetched units:', response.data);
      setUnits(response.data.units || []);
    } catch (error) {
      console.error('Error fetching units:', error);
    } finally {
      setLoading(false);
    }
  };

  const createUnit = async () => {
    try {
      setErrors({});

      // Map frontend fields to backend schema
      const unitData = {
        title: newUnit.title,
        code: newUnit.code,
        description: newUnit.description,
        year: parseInt(newUnit.semester.split('-')[0]) || 2024, // Extract year from semester
        semester: newUnit.semester,
        pedagogy_type: newUnit.teaching_philosophy
          .toLowerCase()
          .replace('_', '-'),
        difficulty_level: 'intermediate', // Default value
        duration_weeks: 12, // Default value
        credit_points: newUnit.credits,
        status: 'draft',
      };

      const response = await api.post('/api/units', unitData);
      setUnits([...units, response.data]);
      setShowCreateModal(false);
      setNewUnit({
        title: '',
        code: '',
        description: '',
        teaching_philosophy: 'TRADITIONAL',
        semester: '2024-S1',
        credits: 3,
      });
    } catch (error: any) {
      console.error('Unit creation error:', error);
      setErrors(
        error.response?.data?.detail || { general: 'Failed to create unit' }
      );
    }
  };

  const deleteUnit = async (unitId: string) => {
    if (window.confirm('Are you sure you want to delete this unit?')) {
      try {
        await api.delete(`/api/units/${unitId}`);
        setUnits(units.filter(c => c.id !== unitId));
      } catch (error) {
        console.error('Error deleting unit:', error);
      }
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: any = {
      PLANNING: { color: 'bg-gray-100 text-gray-800', icon: Edit },
      ACTIVE: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      COMPLETED: { color: 'bg-blue-100 text-blue-800', icon: CheckCircle },
      ARCHIVED: { color: 'bg-gray-100 text-gray-600', icon: Clock },
    };

    const config = statusConfig[status] || statusConfig.PLANNING;
    const Icon = config.icon;

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}
      >
        <Icon className='h-3 w-3 mr-1' />
        {status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className='flex justify-center items-center h-64'>
        <Loader2 className='h-8 w-8 animate-spin text-blue-600' />
      </div>
    );
  }

  return (
    <div className='p-6'>
      {/* Header */}
      <div className='flex justify-between items-center mb-8'>
        <div>
          <h1 className='text-3xl font-bold text-gray-900'>My Units</h1>
          <p className='text-gray-600 mt-2'>
            Manage your unit curriculum and learning resources
          </p>
          <p className='text-sm text-gray-500 mt-1'>
            {units.length} unit(s) loaded
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center'
        >
          <Plus className='h-5 w-5 mr-2' />
          New Unit
        </button>
      </div>

      {/* Units Grid */}
      {units.length === 0 ? (
        <div className='bg-white rounded-lg shadow-md p-12 text-center'>
          <BookOpen className='h-12 w-12 text-gray-400 mx-auto mb-4' />
          <h3 className='text-lg font-medium text-gray-900 mb-2'>
            No Units Yet
          </h3>
          <p className='text-gray-600 mb-6'>
            Create your first unit to start building curriculum
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className='px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700'
          >
            Create Your First Unit
          </button>
        </div>
      ) : (
        <div className='grid gap-6 md:grid-cols-2 lg:grid-cols-3'>
          {units.map(unit => (
            <div
              key={unit.id}
              className='bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer'
              onClick={() => navigate(`/units/${unit.id}/dashboard`)}
            >
              <div className='p-6'>
                {/* Unit Header */}
                <div className='flex justify-between items-start mb-4'>
                  <div className='flex-1'>
                    <h3 className='text-lg font-semibold text-gray-900 mb-1'>
                      {unit.title}
                    </h3>
                    <p className='text-sm text-gray-600'>{unit.code}</p>
                  </div>
                  {getStatusBadge(unit.status)}
                </div>

                {/* Unit Description */}
                {unit.description && (
                  <p className='text-sm text-gray-600 mb-4 line-clamp-2'>
                    {unit.description}
                  </p>
                )}

                {/* Unit Stats */}
                <div className='space-y-2 mb-4'>
                  <div className='flex items-center text-sm text-gray-600'>
                    <Calendar className='h-4 w-4 mr-2' />
                    {unit.semester || 'Not set'} • {unit.credits || 0} credits
                  </div>
                  <div className='flex items-center text-sm text-gray-600'>
                    <Users className='h-4 w-4 mr-2' />
                    {unit.teaching_philosophy
                      ? unit.teaching_philosophy.replace('_', ' ')
                      : 'Not specified'}
                  </div>
                </div>

                {/* Progress Bar */}
                {unit.progress_percentage !== undefined && (
                  <div className='mb-4'>
                    <div className='flex justify-between text-sm mb-1'>
                      <span className='text-gray-600'>Progress</span>
                      <span className='font-medium'>
                        {unit.progress_percentage}%
                      </span>
                    </div>
                    <div className='w-full bg-gray-200 rounded-full h-2'>
                      <div
                        className='bg-blue-600 h-2 rounded-full transition-all'
                        style={{ width: `${unit.progress_percentage}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Quick Stats */}
                <div className='grid grid-cols-3 gap-2 mb-4'>
                  <div className='text-center'>
                    <p className='text-lg font-semibold text-gray-900'>
                      {unit.module_count || 0}
                    </p>
                    <p className='text-xs text-gray-600'>Modules</p>
                  </div>
                  <div className='text-center'>
                    <p className='text-lg font-semibold text-gray-900'>
                      {unit.material_count || 0}
                    </p>
                    <p className='text-xs text-gray-600'>Materials</p>
                  </div>
                  <div className='text-center'>
                    <p className='text-lg font-semibold text-gray-900'>
                      {unit.lrd_count || 0}
                    </p>
                    <p className='text-xs text-gray-600'>LRDs</p>
                  </div>
                </div>

                {/* Actions */}
                <div className='flex justify-between items-center'>
                  <div className='flex space-x-2'>
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        navigate(`/units/${unit.id}/dashboard`);
                      }}
                      className='p-2 text-blue-600 hover:bg-blue-50 rounded-lg'
                      title='Manage LRDs'
                    >
                      <FileText className='h-4 w-4' />
                    </button>
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        // Navigate to edit unit
                      }}
                      className='p-2 text-gray-600 hover:bg-gray-50 rounded-lg'
                      title='Edit Unit'
                    >
                      <Edit className='h-4 w-4' />
                    </button>
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        deleteUnit(unit.id);
                      }}
                      className='p-2 text-red-600 hover:bg-red-50 rounded-lg'
                      title='Delete Unit'
                    >
                      <Trash2 className='h-4 w-4' />
                    </button>
                  </div>
                  <ChevronRight className='h-5 w-5 text-gray-400' />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Unit Modal */}
      {showCreateModal && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
          <div className='bg-white rounded-lg p-6 max-w-md w-full'>
            <h2 className='text-xl font-semibold mb-4'>Create New Unit</h2>

            {errors.general && (
              <div className='mb-4 p-3 bg-red-50 border border-red-200 rounded-lg'>
                <p className='text-red-800 text-sm'>{errors.general}</p>
              </div>
            )}

            <div className='space-y-4'>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Unit Title *
                </label>
                <input
                  type='text'
                  value={newUnit.title}
                  onChange={e =>
                    setNewUnit({ ...newUnit, title: e.target.value })
                  }
                  className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                  placeholder='e.g., Programming Fundamentals'
                />
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Unit Code *
                </label>
                <input
                  type='text'
                  value={newUnit.code}
                  onChange={e =>
                    setNewUnit({ ...newUnit, code: e.target.value })
                  }
                  className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                  placeholder='e.g., CS101'
                />
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Description
                </label>
                <textarea
                  value={newUnit.description}
                  onChange={e =>
                    setNewUnit({ ...newUnit, description: e.target.value })
                  }
                  className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                  rows={3}
                  placeholder='Brief description of the unit...'
                />
              </div>

              <div className='grid grid-cols-2 gap-4'>
                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Semester
                  </label>
                  <input
                    type='text'
                    value={newUnit.semester}
                    onChange={e =>
                      setNewUnit({ ...newUnit, semester: e.target.value })
                    }
                    className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                    placeholder='2024-S1'
                  />
                </div>

                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Credits
                  </label>
                  <input
                    type='number'
                    value={newUnit.credits}
                    onChange={e =>
                      setNewUnit({
                        ...newUnit,
                        credits: parseInt(e.target.value),
                      })
                    }
                    className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                    min='1'
                    max='6'
                  />
                </div>
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Teaching Philosophy
                </label>
                <select
                  value={newUnit.teaching_philosophy}
                  onChange={e =>
                    setNewUnit({
                      ...newUnit,
                      teaching_philosophy: e.target.value,
                    })
                  }
                  className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                >
                  <option value='TRADITIONAL'>Traditional</option>
                  <option value='FLIPPED_CLASSROOM'>Flipped Classroom</option>
                  <option value='CONSTRUCTIVIST'>Constructivist</option>
                  <option value='PROJECT_BASED'>Project Based</option>
                  <option value='INQUIRY_BASED'>Inquiry Based</option>
                  <option value='COLLABORATIVE'>Collaborative</option>
                  <option value='EXPERIENTIAL'>Experiential</option>
                  <option value='PROBLEM_BASED'>Problem Based</option>
                  <option value='MIXED_APPROACH'>Mixed Approach</option>
                </select>
              </div>
            </div>

            <div className='flex justify-end space-x-3 mt-6'>
              <button
                onClick={() => setShowCreateModal(false)}
                className='px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200'
              >
                Cancel
              </button>
              <button
                onClick={createUnit}
                className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700'
              >
                Create Unit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UnitManager;
