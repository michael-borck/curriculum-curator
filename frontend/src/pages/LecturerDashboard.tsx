import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  FileText,
  Users,
  TrendingUp,
  Calendar,
  Plus,
  Brain,
  Edit,
  Eye,
} from 'lucide-react';

const LecturerDashboard = () => {
  const navigate = useNavigate();

  const stats = [
    { label: 'Active Courses', value: 4, icon: BookOpen, color: 'bg-blue-500' },
    {
      label: 'Content Items',
      value: 127,
      icon: FileText,
      color: 'bg-green-500',
    },
    {
      label: "This Week's Tasks",
      value: 8,
      icon: Calendar,
      color: 'bg-yellow-500',
    },
    { label: 'AI Suggestions', value: 12, icon: Brain, color: 'bg-purple-500' },
  ];

  const courses = [
    {
      id: 1,
      title: 'Introduction to Computer Science',
      code: 'CS101',
      weeks: 12,
      items: 45,
      students: 120,
      progress: 75,
      nextDeadline: '3 days',
    },
    {
      id: 2,
      title: 'Data Structures & Algorithms',
      code: 'CS201',
      weeks: 12,
      items: 38,
      students: 85,
      progress: 60,
      nextDeadline: '1 week',
    },
    {
      id: 3,
      title: 'Web Development Fundamentals',
      code: 'CS150',
      weeks: 8,
      items: 28,
      students: 95,
      progress: 90,
      nextDeadline: '2 days',
    },
  ];

  const recentActivity = [
    {
      type: 'create',
      content: 'Created worksheet for Week 3',
      time: '2 hours ago',
    },
    { type: 'ai', content: 'AI enhanced lecture notes', time: '5 hours ago' },
    { type: 'edit', content: 'Updated CS101 syllabus', time: '1 day ago' },
    { type: 'review', content: 'Reviewed quiz questions', time: '2 days ago' },
  ];

  return (
    <div className='p-6'>
      {/* Welcome Header */}
      <div className='mb-8'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>
          Welcome back, Dr. Smith
        </h1>
        <p className='text-gray-600'>
          Teaching Philosophy:{' '}
          <span className='font-semibold text-purple-600'>
            Project-Based Learning
          </span>
        </p>
      </div>

      {/* Stats Grid */}
      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8'>
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div
              key={index}
              className='bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition'
            >
              <div className='flex items-center justify-between mb-4'>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className='w-6 h-6 text-white' />
                </div>
                <TrendingUp className='w-5 h-5 text-green-500' />
              </div>
              <p className='text-gray-600 text-sm mb-1'>{stat.label}</p>
              <p className='text-3xl font-bold text-gray-900'>{stat.value}</p>
            </div>
          );
        })}
      </div>

      <div className='grid lg:grid-cols-3 gap-6'>
        {/* Courses List */}
        <div className='lg:col-span-2'>
          <div className='bg-white rounded-xl shadow-sm border border-gray-200'>
            <div className='p-6 border-b border-gray-200'>
              <div className='flex items-center justify-between'>
                <h2 className='text-xl font-semibold text-gray-900'>
                  Your Courses
                </h2>
                <button
                  onClick={() => navigate('/create/course')}
                  className='flex items-center gap-2 text-purple-600 hover:text-purple-700 font-medium'
                >
                  <Plus className='w-5 h-5' />
                  New Course
                </button>
              </div>
            </div>
            <div className='divide-y divide-gray-200'>
              {courses.map(course => (
                <div
                  key={course.id}
                  className='p-6 hover:bg-gray-50 transition'
                >
                  <div className='flex items-center justify-between'>
                    <div className='flex-1'>
                      <div className='flex items-center gap-2 mb-2'>
                        <h3 className='text-lg font-semibold text-gray-900'>
                          {course.title}
                        </h3>
                        <span className='text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded'>
                          {course.code}
                        </span>
                      </div>
                      <div className='flex items-center gap-4 text-sm text-gray-600 mb-3'>
                        <span className='flex items-center gap-1'>
                          <Calendar className='w-4 h-4' />
                          {course.weeks} weeks
                        </span>
                        <span className='flex items-center gap-1'>
                          <FileText className='w-4 h-4' />
                          {course.items} items
                        </span>
                        <span className='flex items-center gap-1'>
                          <Users className='w-4 h-4' />
                          {course.students} students
                        </span>
                      </div>
                      <div className='flex items-center gap-2'>
                        <div className='flex-1 bg-gray-200 rounded-full h-2'>
                          <div
                            className='bg-purple-600 h-2 rounded-full'
                            style={{ width: `${course.progress}%` }}
                          />
                        </div>
                        <span className='text-sm text-gray-600'>
                          {course.progress}%
                        </span>
                      </div>
                      <p className='text-sm text-orange-600 mt-2'>
                        Next deadline: {course.nextDeadline}
                      </p>
                    </div>
                    <div className='flex gap-2 ml-4'>
                      <button className='p-2 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition'>
                        <Edit className='w-5 h-5' />
                      </button>
                      <button className='p-2 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition'>
                        <Eye className='w-5 h-5' />
                      </button>
                      <button className='p-2 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition'>
                        <Brain className='w-5 h-5' />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className='bg-white rounded-xl shadow-sm border border-gray-200'>
          <div className='p-6 border-b border-gray-200'>
            <h2 className='text-xl font-semibold text-gray-900'>
              Recent Activity
            </h2>
          </div>
          <div className='p-6'>
            <div className='space-y-4'>
              {recentActivity.map((activity, index) => (
                <div key={index} className='flex items-start gap-3'>
                  <div
                    className={`w-2 h-2 rounded-full mt-2 ${
                      activity.type === 'create'
                        ? 'bg-green-500'
                        : activity.type === 'ai'
                          ? 'bg-purple-500'
                          : activity.type === 'edit'
                            ? 'bg-blue-500'
                            : 'bg-gray-500'
                    }`}
                  />
                  <div className='flex-1'>
                    <p className='text-gray-900'>{activity.content}</p>
                    <p className='text-sm text-gray-500 mt-1'>
                      {activity.time}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            <button className='w-full mt-4 text-center text-purple-600 hover:text-purple-700 font-medium'>
              View All Activity
            </button>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className='mt-8 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 text-white'>
        <h3 className='text-xl font-semibold mb-4'>Quick Actions</h3>
        <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
          <button
            onClick={() => navigate('/create/lecture')}
            className='bg-white/20 backdrop-blur-sm rounded-lg p-4 hover:bg-white/30 transition text-left'
          >
            <FileText className='w-6 h-6 mb-2' />
            <p className='font-semibold'>Create Lecture</p>
            <p className='text-sm opacity-90'>Start with AI assistance</p>
          </button>
          <button
            onClick={() => navigate('/create/worksheet')}
            className='bg-white/20 backdrop-blur-sm rounded-lg p-4 hover:bg-white/30 transition text-left'
          >
            <Edit className='w-6 h-6 mb-2' />
            <p className='font-semibold'>New Worksheet</p>
            <p className='text-sm opacity-90'>Generate practice materials</p>
          </button>
          <button
            onClick={() => navigate('/import')}
            className='bg-white/20 backdrop-blur-sm rounded-lg p-4 hover:bg-white/30 transition text-left'
          >
            <Plus className='w-6 h-6 mb-2' />
            <p className='font-semibold'>Import Content</p>
            <p className='text-sm opacity-90'>Enhance existing materials</p>
          </button>
        </div>
      </div>
    </div>
  );
};

export default LecturerDashboard;
