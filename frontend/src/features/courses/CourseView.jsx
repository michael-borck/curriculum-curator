import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Edit, Download, Share, BookOpen, Clock, Users, Target } from 'lucide-react';

const CourseView = () => {
  const { id } = useParams();
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCourse = async () => {
      try {
        // Mock course data for now
        setCourse({
          id: id,
          title: `Course ${id}`,
          description: 'A comprehensive course created with pedagogically-aware content generation.',
          pedagogy: 'inquiry-based',
          difficulty: 'intermediate',
          duration: '8 weeks',
          learningObjectives: [
            'Understand core concepts and principles',
            'Apply knowledge to real-world scenarios',
            'Develop critical thinking skills'
          ],
          modules: [
            { id: 1, title: 'Introduction', type: 'lecture', completed: true },
            { id: 2, title: 'Core Concepts', type: 'assignment', completed: true },
            { id: 3, title: 'Practical Applications', type: 'project', completed: false },
            { id: 4, title: 'Assessment', type: 'quiz', completed: false }
          ],
          createdAt: new Date().toISOString().split('T')[0]
        });
      } catch (error) {
        console.error('Failed to fetch course:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCourse();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Course not found</h2>
        <Link to="/courses" className="text-purple-600 hover:text-purple-700">
          ← Back to courses
        </Link>
      </div>
    );
  }

  const getModuleIcon = (type) => {
    const icons = {
      lecture: BookOpen,
      assignment: Edit,
      project: Target,
      quiz: Users
    };
    return icons[type] || BookOpen;
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <Link
          to="/courses"
          className="inline-flex items-center text-purple-600 hover:text-purple-700 mb-4"
        >
          <ArrowLeft size={20} className="mr-2" />
          Back to courses
        </Link>
        
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{course.title}</h1>
            <p className="text-gray-600 text-lg mb-4">{course.description}</p>
            
            <div className="flex gap-4 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Clock size={16} />
                {course.duration}
              </span>
              <span className="capitalize">{course.difficulty}</span>
              <span className="capitalize">{course.pedagogy.replace('-', ' ')}</span>
            </div>
          </div>
          
          <div className="flex gap-2">
            <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2">
              <Edit size={18} />
              Edit Course
            </button>
            <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2">
              <Share size={18} />
              Share
            </button>
            <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2">
              <Download size={18} />
              Export
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Course Modules</h2>
            
            <div className="space-y-4">
              {course.modules.map((module, index) => {
                const IconComponent = getModuleIcon(module.type);
                
                return (
                  <div
                    key={module.id}
                    className={`
                      p-4 rounded-lg border-2 flex items-center gap-4
                      ${module.completed 
                        ? 'bg-green-50 border-green-200' 
                        : 'bg-white border-gray-200'
                      }
                    `}
                  >
                    <div className={`
                      p-2 rounded-full
                      ${module.completed ? 'bg-green-100' : 'bg-gray-100'}
                    `}>
                      <IconComponent 
                        size={20} 
                        className={module.completed ? 'text-green-600' : 'text-gray-600'} 
                      />
                    </div>
                    
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">
                        Module {index + 1}: {module.title}
                      </h3>
                      <p className="text-sm text-gray-600 capitalize">{module.type}</p>
                    </div>
                    
                    {module.completed && (
                      <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Learning Objectives</h3>
            <ul className="space-y-2">
              {course.learningObjectives.map((objective, index) => (
                <li key={index} className="flex items-start gap-2">
                  <Target size={16} className="text-purple-600 mt-1 flex-shrink-0" />
                  <span className="text-gray-700">{objective}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Course Details</h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-500">Created</label>
                <p className="text-gray-900">{course.createdAt}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Teaching Approach</label>
                <p className="text-gray-900 capitalize">{course.pedagogy.replace('-', ' ')}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Difficulty</label>
                <p className="text-gray-900 capitalize">{course.difficulty}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Duration</label>
                <p className="text-gray-900">{course.duration}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <Link
                to={`/create/lecture`}
                className="w-full px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 flex items-center justify-center gap-2"
              >
                <BookOpen size={18} />
                Add Lecture
              </Link>
              <Link
                to={`/create/assignment`}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2"
              >
                <Edit size={18} />
                Add Assignment
              </Link>
              <Link
                to={`/create/quiz`}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2"
              >
                <Users size={18} />
                Add Quiz
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseView;