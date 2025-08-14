import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileText,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Activity,
  Target,
  Package,
  Layers,
  Grid,
  List,
  Plus,
  Download,
  Share2,
  Settings,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import api from '../../services/api';

interface CourseDetails {
  id: string;
  title: string;
  code: string;
  description: string;
  status: string;
  teaching_philosophy: string;
  semester: string;
  credits: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  owner_id: string;
  // Statistics
  module_count: number;
  material_count: number;
  lrd_count: number;
  task_count: number;
  completed_tasks: number;
  progress_percentage: number;
  // Additional data
  modules?: Module[];
  recent_materials?: Material[];
  pending_tasks?: Task[];
}

interface Module {
  id: string;
  title: string;
  description: string;
  order: number;
  status: string;
  material_count: number;
  completed_count: number;
}

interface Material {
  id: string;
  title: string;
  type: string;
  status: string;
  created_at: string;
  version: number;
  word_count?: number;
}

interface Task {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  due_date?: string;
  assigned_to?: string;
}

const CourseDashboard = () => {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState<CourseDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const fetchCourseDetails = async () => {
      try {
        const response = await api.get(`/courses/${courseId}`);
        setCourse(response.data);
      } catch (error) {
        console.error('Error fetching course:', error);
      } finally {
        setLoading(false);
      }
    };

    const fetchCourseStatistics = async () => {
      try {
        // Fetch additional statistics
        const [modulesRes, materialsRes, tasksRes] = await Promise.all([
          api
            .get(`/course-modules?course_id=${courseId}`)
            .catch(() => ({ data: [] })),
          api
            .get(`/materials?course_id=${courseId}&limit=5`)
            .catch(() => ({ data: { items: [] } })),
          api
            .get(`/tasks?course_id=${courseId}&status=pending&limit=5`)
            .catch(() => ({ data: [] })),
        ]);

        setCourse(prev =>
          prev
            ? {
                ...prev,
                modules: modulesRes.data,
                recent_materials: materialsRes.data.items || [],
                pending_tasks: tasksRes.data,
              }
            : null
        );
      } catch (error) {
        console.error('Error fetching statistics:', error);
      }
    };

    fetchCourseDetails();
    fetchCourseStatistics();
  }, [courseId]);

  if (loading) {
    return (
      <div className='flex items-center justify-center h-96'>
        <Loader2 className='h-8 w-8 animate-spin text-blue-600' />
      </div>
    );
  }

  if (!course) {
    return (
      <div className='text-center py-12'>
        <AlertCircle className='h-12 w-12 text-red-500 mx-auto mb-4' />
        <h2 className='text-xl font-semibold text-gray-900'>
          Course not found
        </h2>
        <button
          onClick={() => navigate('/courses')}
          className='mt-4 text-blue-600 hover:underline'
        >
          Back to courses
        </button>
      </div>
    );
  }

  const stats = [
    {
      title: 'Progress',
      value: `${course.progress_percentage || 0}%`,
      icon: TrendingUp,
      color: 'bg-blue-500',
      change: '+5% this week',
    },
    {
      title: 'Modules',
      value: course.module_count || 0,
      icon: Layers,
      color: 'bg-green-500',
      subtitle: `${course.modules?.filter(m => m.status === 'completed').length || 0} completed`,
    },
    {
      title: 'Materials',
      value: course.material_count || 0,
      icon: FileText,
      color: 'bg-purple-500',
      subtitle: 'Total resources',
    },
    {
      title: 'Tasks',
      value: `${course.completed_tasks || 0}/${course.task_count || 0}`,
      icon: CheckCircle,
      color: 'bg-orange-500',
      subtitle: 'Completed',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE':
      case 'PUBLISHED':
        return 'text-green-600 bg-green-100';
      case 'DRAFT':
        return 'text-yellow-600 bg-yellow-100';
      case 'ARCHIVED':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-blue-600 bg-blue-100';
    }
  };

  const getContentTypeIcon = (type: string) => {
    switch (type) {
      case 'lecture':
        return '📚';
      case 'quiz':
        return '📝';
      case 'worksheet':
        return '✏️';
      case 'lab':
        return '🔬';
      case 'case_study':
        return '💼';
      case 'interactive':
        return '🎮';
      case 'presentation':
        return '🎯';
      case 'reading':
        return '📖';
      case 'video_script':
        return '🎥';
      default:
        return '📄';
    }
  };

  return (
    <div className='p-6 max-w-7xl mx-auto'>
      {/* Header */}
      <div className='mb-8'>
        <div className='flex items-center justify-between mb-4'>
          <div>
            <div className='flex items-center space-x-2 text-sm text-gray-600 mb-2'>
              <button
                onClick={() => navigate('/courses')}
                className='hover:text-blue-600'
              >
                Courses
              </button>
              <ChevronRight className='h-4 w-4' />
              <span>{course.code}</span>
            </div>
            <h1 className='text-3xl font-bold text-gray-900'>{course.title}</h1>
            <p className='text-gray-600 mt-2'>{course.description}</p>
          </div>

          <div className='flex items-center space-x-3'>
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(course.status)}`}
            >
              {course.status}
            </span>
            <button
              onClick={() => navigate(`/courses/${courseId}/settings`)}
              className='p-2 text-gray-600 hover:bg-gray-100 rounded-lg'
            >
              <Settings className='h-5 w-5' />
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className='flex space-x-3 mt-4'>
          <button
            onClick={() => navigate(`/courses/${courseId}/lrd/create`)}
            className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center'
          >
            <Plus className='h-4 w-4 mr-2' />
            Create LRD
          </button>
          <button
            onClick={() => navigate(`/import?course=${courseId}`)}
            className='px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center'
          >
            <Download className='h-4 w-4 mr-2' />
            Import Materials
          </button>
          <button
            onClick={() => navigate(`/courses/${courseId}/generate`)}
            className='px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center'
          >
            <Activity className='h-4 w-4 mr-2' />
            Generate Content
          </button>
          <button className='px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center'>
            <Share2 className='h-4 w-4 mr-2' />
            Share
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8'>
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className='bg-white rounded-lg shadow-md p-6'>
              <div className='flex items-center justify-between mb-4'>
                <div className={`p-3 rounded-lg ${stat.color} bg-opacity-10`}>
                  <Icon
                    className={`h-6 w-6 ${stat.color.replace('bg-', 'text-')}`}
                  />
                </div>
                {stat.change && (
                  <span className='text-sm text-green-600 font-medium'>
                    {stat.change}
                  </span>
                )}
              </div>
              <h3 className='text-2xl font-bold text-gray-900'>{stat.value}</h3>
              <p className='text-sm text-gray-600 mt-1'>{stat.title}</p>
              {stat.subtitle && (
                <p className='text-xs text-gray-500 mt-1'>{stat.subtitle}</p>
              )}
            </div>
          );
        })}
      </div>

      {/* Tabs */}
      <div className='border-b border-gray-200 mb-6'>
        <nav className='flex space-x-8'>
          {['overview', 'modules', 'materials', 'tasks', 'analytics'].map(
            tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab}
              </button>
            )
          )}
        </nav>
      </div>

      {/* Tab Content */}
      <div className='bg-white rounded-lg shadow-md p-6'>
        {activeTab === 'overview' && (
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
            {/* Recent Materials */}
            <div>
              <h3 className='text-lg font-semibold mb-4 flex items-center'>
                <FileText className='h-5 w-5 mr-2 text-gray-600' />
                Recent Materials
              </h3>
              {course.recent_materials && course.recent_materials.length > 0 ? (
                <div className='space-y-3'>
                  {course.recent_materials.map(material => (
                    <button
                      key={material.id}
                      className='flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer w-full text-left'
                      onClick={() => navigate(`/materials/${material.id}`)}
                    >
                      <div className='flex items-center space-x-3'>
                        <span className='text-2xl'>
                          {getContentTypeIcon(material.type)}
                        </span>
                        <div>
                          <p className='font-medium text-gray-900'>
                            {material.title}
                          </p>
                          <p className='text-sm text-gray-500'>
                            Version {material.version} •{' '}
                            {material.word_count || 0} words
                          </p>
                        </div>
                      </div>
                      <ChevronRight className='h-5 w-5 text-gray-400' />
                    </button>
                  ))}
                </div>
              ) : (
                <p className='text-gray-500 text-center py-8'>
                  No materials yet
                </p>
              )}
              <button
                onClick={() => navigate(`/courses/${courseId}/materials`)}
                className='mt-4 text-blue-600 hover:underline text-sm'
              >
                View all materials →
              </button>
            </div>

            {/* Pending Tasks */}
            <div>
              <h3 className='text-lg font-semibold mb-4 flex items-center'>
                <Target className='h-5 w-5 mr-2 text-gray-600' />
                Pending Tasks
              </h3>
              {course.pending_tasks && course.pending_tasks.length > 0 ? (
                <div className='space-y-3'>
                  {course.pending_tasks.map(task => (
                    <div
                      key={task.id}
                      className='flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50'
                    >
                      <div className='flex items-center space-x-3'>
                        <input
                          type='checkbox'
                          className='h-4 w-4 text-blue-600 rounded border-gray-300'
                          onChange={() => {
                            // Handle task completion
                          }}
                        />
                        <div>
                          <p className='font-medium text-gray-900'>
                            {task.title}
                          </p>
                          {task.due_date && (
                            <p className='text-sm text-gray-500'>
                              Due:{' '}
                              {new Date(task.due_date).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                      <span
                        className={`px-2 py-1 text-xs rounded-full font-medium ${
                          task.priority === 'high'
                            ? 'bg-red-100 text-red-600'
                            : task.priority === 'medium'
                              ? 'bg-yellow-100 text-yellow-600'
                              : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {task.priority}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className='text-gray-500 text-center py-8'>
                  No pending tasks
                </p>
              )}
              <button
                onClick={() => navigate(`/courses/${courseId}/tasks`)}
                className='mt-4 text-blue-600 hover:underline text-sm'
              >
                Manage all tasks →
              </button>
            </div>
          </div>
        )}

        {activeTab === 'modules' && (
          <div>
            <div className='flex justify-between items-center mb-4'>
              <h3 className='text-lg font-semibold'>Course Modules</h3>
              <button
                onClick={() => navigate(`/courses/${courseId}/modules/create`)}
                className='px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm flex items-center'
              >
                <Plus className='h-4 w-4 mr-1' />
                Add Module
              </button>
            </div>

            {course.modules && course.modules.length > 0 ? (
              <div className='space-y-4'>
                {course.modules.map(module => (
                  <div
                    key={module.id}
                    className='border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow'
                  >
                    <div className='flex items-center justify-between'>
                      <div className='flex-1'>
                        <h4 className='font-semibold text-gray-900'>
                          Module {module.order}: {module.title}
                        </h4>
                        <p className='text-sm text-gray-600 mt-1'>
                          {module.description}
                        </p>
                        <div className='flex items-center space-x-4 mt-3 text-sm text-gray-500'>
                          <span>{module.material_count} materials</span>
                          <span>•</span>
                          <span>{module.completed_count} completed</span>
                          <span>•</span>
                          <span
                            className={`font-medium ${
                              module.status === 'completed'
                                ? 'text-green-600'
                                : 'text-yellow-600'
                            }`}
                          >
                            {module.status}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() =>
                          navigate(`/courses/${courseId}/modules/${module.id}`)
                        }
                        className='px-3 py-1 text-blue-600 hover:bg-blue-50 rounded-lg text-sm'
                      >
                        View Details
                      </button>
                    </div>

                    {/* Progress bar */}
                    <div className='mt-4'>
                      <div className='w-full bg-gray-200 rounded-full h-2'>
                        <div
                          className='bg-blue-600 h-2 rounded-full'
                          style={{
                            width: `${
                              module.material_count > 0
                                ? (module.completed_count /
                                    module.material_count) *
                                  100
                                : 0
                            }%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className='text-center py-12'>
                <Package className='h-12 w-12 text-gray-400 mx-auto mb-4' />
                <p className='text-gray-500'>No modules created yet</p>
                <button
                  onClick={() =>
                    navigate(`/courses/${courseId}/modules/create`)
                  }
                  className='mt-4 text-blue-600 hover:underline'
                >
                  Create your first module
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'materials' && (
          <div>
            <div className='flex justify-between items-center mb-4'>
              <h3 className='text-lg font-semibold'>Course Materials</h3>
              <div className='flex items-center space-x-2'>
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  <Grid className='h-4 w-4' />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  <List className='h-4 w-4' />
                </button>
              </div>
            </div>

            {viewMode === 'grid' ? (
              <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
                {course.recent_materials?.map(material => (
                  <button
                    key={material.id}
                    className='border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer w-full text-left'
                    onClick={() => navigate(`/materials/${material.id}`)}
                  >
                    <div className='flex items-start justify-between mb-3'>
                      <span className='text-3xl'>
                        {getContentTypeIcon(material.type)}
                      </span>
                      <span
                        className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(material.status)}`}
                      >
                        {material.status}
                      </span>
                    </div>
                    <h4 className='font-semibold text-gray-900 mb-2'>
                      {material.title}
                    </h4>
                    <div className='text-sm text-gray-500'>
                      <p>Version {material.version}</p>
                      <p>{material.word_count || 0} words</p>
                      <p className='mt-2 text-xs'>
                        Created{' '}
                        {new Date(material.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className='space-y-2'>
                {course.recent_materials?.map(material => (
                  <button
                    key={material.id}
                    className='flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer w-full text-left'
                    onClick={() => navigate(`/materials/${material.id}`)}
                  >
                    <div className='flex items-center space-x-3'>
                      <span className='text-2xl'>
                        {getContentTypeIcon(material.type)}
                      </span>
                      <div>
                        <p className='font-medium text-gray-900'>
                          {material.title}
                        </p>
                        <p className='text-sm text-gray-500'>
                          {material.type} • Version {material.version} •{' '}
                          {material.word_count || 0} words
                        </p>
                      </div>
                    </div>
                    <div className='flex items-center space-x-3'>
                      <span
                        className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(material.status)}`}
                      >
                        {material.status}
                      </span>
                      <ChevronRight className='h-5 w-5 text-gray-400' />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className='text-center py-12'>
            <Target className='h-12 w-12 text-gray-400 mx-auto mb-4' />
            <p className='text-gray-500'>Task management coming soon</p>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div>
            <h3 className='text-lg font-semibold mb-4'>Course Analytics</h3>
            <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
              {/* Progress Chart */}
              <div className='border border-gray-200 rounded-lg p-4'>
                <h4 className='font-medium text-gray-900 mb-3'>
                  Progress Overview
                </h4>
                <div className='space-y-3'>
                  <div>
                    <div className='flex justify-between text-sm mb-1'>
                      <span>Content Creation</span>
                      <span className='font-medium'>75%</span>
                    </div>
                    <div className='w-full bg-gray-200 rounded-full h-2'>
                      <div
                        className='bg-blue-600 h-2 rounded-full'
                        style={{ width: '75%' }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className='flex justify-between text-sm mb-1'>
                      <span>Quality Review</span>
                      <span className='font-medium'>60%</span>
                    </div>
                    <div className='w-full bg-gray-200 rounded-full h-2'>
                      <div
                        className='bg-green-600 h-2 rounded-full'
                        style={{ width: '60%' }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className='flex justify-between text-sm mb-1'>
                      <span>Publishing</span>
                      <span className='font-medium'>45%</span>
                    </div>
                    <div className='w-full bg-gray-200 rounded-full h-2'>
                      <div
                        className='bg-purple-600 h-2 rounded-full'
                        style={{ width: '45%' }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Content Type Distribution */}
              <div className='border border-gray-200 rounded-lg p-4'>
                <h4 className='font-medium text-gray-900 mb-3'>
                  Content Distribution
                </h4>
                <div className='space-y-2'>
                  {[
                    { type: 'Lectures', count: 12, icon: '📚' },
                    { type: 'Quizzes', count: 8, icon: '📝' },
                    { type: 'Worksheets', count: 6, icon: '✏️' },
                    { type: 'Labs', count: 4, icon: '🔬' },
                    { type: 'Case Studies', count: 2, icon: '💼' },
                  ].map(item => (
                    <div
                      key={item.type}
                      className='flex items-center justify-between'
                    >
                      <div className='flex items-center space-x-2'>
                        <span className='text-xl'>{item.icon}</span>
                        <span className='text-sm text-gray-600'>
                          {item.type}
                        </span>
                      </div>
                      <span className='font-medium text-gray-900'>
                        {item.count}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Course Info Footer */}
      <div className='mt-8 p-4 bg-gray-50 rounded-lg'>
        <div className='grid grid-cols-2 md:grid-cols-4 gap-4 text-sm'>
          <div>
            <span className='text-gray-600'>Semester:</span>
            <span className='ml-2 font-medium'>{course.semester}</span>
          </div>
          <div>
            <span className='text-gray-600'>Credits:</span>
            <span className='ml-2 font-medium'>{course.credits}</span>
          </div>
          <div>
            <span className='text-gray-600'>Philosophy:</span>
            <span className='ml-2 font-medium capitalize'>
              {course.teaching_philosophy.replace(/_/g, ' ').toLowerCase()}
            </span>
          </div>
          <div>
            <span className='text-gray-600'>Created:</span>
            <span className='ml-2 font-medium'>
              {new Date(course.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseDashboard;
