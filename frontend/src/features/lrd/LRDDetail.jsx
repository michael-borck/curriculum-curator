import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  FileText,
  Target,
  Clock,
  Users,
  CheckCircle,
  AlertCircle,
  Edit,
  Send,
  Download,
  Printer,
  Calendar,
  BookOpen,
  Loader2
} from 'lucide-react';
import api from '../../services/api';

const LRDDetail = () => {
  const { courseId, lrdId } = useParams();
  const navigate = useNavigate();
  
  const [lrd, setLrd] = useState(null);
  const [course, setCourse] = useState(null);
  const [taskList, setTaskList] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchData();
  }, [courseId, lrdId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [lrdRes, courseRes] = await Promise.all([
        api.get(`/lrds/${lrdId}`),
        api.get(`/courses/${courseId}`)
      ]);
      
      setLrd(lrdRes.data);
      setCourse(courseRes.data);
      
      // Fetch associated task list if exists
      if (lrdRes.data.task_lists && lrdRes.data.task_lists.length > 0) {
        const taskRes = await api.get(`/task-lists/${lrdRes.data.task_lists[0].id}`);
        setTaskList(taskRes.data);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      DRAFT: { color: 'bg-gray-100 text-gray-800', icon: Edit },
      IN_REVIEW: { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      APPROVED: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      REJECTED: { color: 'bg-red-100 text-red-800', icon: AlertCircle }
    };
    
    const config = statusConfig[status] || statusConfig.DRAFT;
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.color}`}>
        <Icon className="h-4 w-4 mr-1" />
        {status.replace('_', ' ')}
      </span>
    );
  };

  const handleExport = async () => {
    try {
      const response = await api.get(`/lrds/${lrdId}/export`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `LRD_${lrd.content?.topic || 'document'}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting LRD:', error);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!lrd) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">LRD not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(`/courses/${courseId}/lrds`)}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to LRDs
        </button>
        
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {lrd.content?.topic || 'Untitled LRD'}
            </h1>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span>Version {lrd.version}</span>
              <span>•</span>
              <span>Created {new Date(lrd.created_at).toLocaleDateString()}</span>
              <span>•</span>
              {getStatusBadge(lrd.status)}
            </div>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={handlePrint}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center"
            >
              <Printer className="h-4 w-4 mr-2" />
              Print
            </button>
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center"
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </button>
            {lrd.status === 'DRAFT' && (
              <button
                onClick={() => navigate(`/courses/${courseId}/lrds/${lrdId}/edit`)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
              >
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('structure')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'structure'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Class Structure
          </button>
          <button
            onClick={() => setActiveTab('assessment')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'assessment'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Assessment
          </button>
          <button
            onClick={() => setActiveTab('resources')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'resources'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Resources
          </button>
          {taskList && (
            <button
              onClick={() => setActiveTab('tasks')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'tasks'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Tasks
            </button>
          )}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <>
            {/* Basic Information */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <BookOpen className="h-5 w-5 mr-2 text-blue-600" />
                Basic Information
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Duration
                  </label>
                  <p className="text-gray-900">{lrd.content?.duration || 'Not specified'}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Teaching Philosophy
                  </label>
                  <p className="text-gray-900">
                    {lrd.content?.teaching_philosophy?.replace('_', ' ') || course?.teaching_philosophy?.replace('_', ' ') || 'Not specified'}
                  </p>
                </div>
              </div>
            </div>

            {/* Learning Objectives */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <Target className="h-5 w-5 mr-2 text-green-600" />
                Learning Objectives
              </h2>
              
              {lrd.content?.objectives && lrd.content.objectives.length > 0 ? (
                <ul className="list-disc list-inside space-y-2">
                  {lrd.content.objectives.map((objective, index) => (
                    <li key={index} className="text-gray-700">{objective}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500">No objectives defined</p>
              )}
            </div>

            {/* Learning Outcomes */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <CheckCircle className="h-5 w-5 mr-2 text-purple-600" />
                Learning Outcomes
              </h2>
              
              {lrd.content?.learning_outcomes && lrd.content.learning_outcomes.length > 0 ? (
                <ul className="list-disc list-inside space-y-2">
                  {lrd.content.learning_outcomes.map((outcome, index) => (
                    <li key={index} className="text-gray-700">{outcome}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500">No outcomes defined</p>
              )}
            </div>

            {/* Prerequisites */}
            {lrd.content?.prerequisites && lrd.content.prerequisites.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold mb-4 flex items-center">
                  <AlertCircle className="h-5 w-5 mr-2 text-orange-600" />
                  Prerequisites
                </h2>
                
                <ul className="list-disc list-inside space-y-2">
                  {lrd.content.prerequisites.map((prereq, index) => (
                    <li key={index} className="text-gray-700">{prereq}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        {activeTab === 'structure' && (
          <div className="space-y-6">
            {/* Pre-Class */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="border-l-4 border-yellow-400 pl-4">
                <h3 className="text-lg font-semibold mb-3">Pre-Class Activities</h3>
                
                {lrd.content?.structure?.pre_class?.duration && (
                  <p className="text-sm text-gray-600 mb-3">
                    <Clock className="inline h-4 w-4 mr-1" />
                    Duration: {lrd.content.structure.pre_class.duration}
                  </p>
                )}
                
                {lrd.content?.structure?.pre_class?.activities && 
                 lrd.content.structure.pre_class.activities.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-medium text-gray-700 mb-2">Activities:</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {lrd.content.structure.pre_class.activities.map((activity, index) => (
                        <li key={index} className="text-gray-600">{activity}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {lrd.content?.structure?.pre_class?.materials && 
                 lrd.content.structure.pre_class.materials.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Materials:</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {lrd.content.structure.pre_class.materials.map((material, index) => (
                        <li key={index} className="text-gray-600">{material}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* In-Class */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="border-l-4 border-green-400 pl-4">
                <h3 className="text-lg font-semibold mb-3">In-Class Activities</h3>
                
                {lrd.content?.structure?.in_class?.duration && (
                  <p className="text-sm text-gray-600 mb-3">
                    <Clock className="inline h-4 w-4 mr-1" />
                    Duration: {lrd.content.structure.in_class.duration}
                  </p>
                )}
                
                {lrd.content?.structure?.in_class?.activities && 
                 lrd.content.structure.in_class.activities.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-medium text-gray-700 mb-2">Activities:</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {lrd.content.structure.in_class.activities.map((activity, index) => (
                        <li key={index} className="text-gray-600">{activity}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {lrd.content?.structure?.in_class?.materials && 
                 lrd.content.structure.in_class.materials.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Materials:</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {lrd.content.structure.in_class.materials.map((material, index) => (
                        <li key={index} className="text-gray-600">{material}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Post-Class */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="border-l-4 border-blue-400 pl-4">
                <h3 className="text-lg font-semibold mb-3">Post-Class Activities</h3>
                
                {lrd.content?.structure?.post_class?.duration && (
                  <p className="text-sm text-gray-600 mb-3">
                    <Clock className="inline h-4 w-4 mr-1" />
                    Duration: {lrd.content.structure.post_class.duration}
                  </p>
                )}
                
                {lrd.content?.structure?.post_class?.activities && 
                 lrd.content.structure.post_class.activities.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-medium text-gray-700 mb-2">Activities:</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {lrd.content.structure.post_class.activities.map((activity, index) => (
                        <li key={index} className="text-gray-600">{activity}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {lrd.content?.structure?.post_class?.materials && 
                 lrd.content.structure.post_class.materials.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Materials:</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {lrd.content.structure.post_class.materials.map((material, index) => (
                        <li key={index} className="text-gray-600">{material}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'assessment' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Assessment Details</h2>
            
            {lrd.content?.assessment ? (
              <div className="space-y-4">
                {lrd.content.assessment.type && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Assessment Type
                    </label>
                    <p className="text-gray-900">{lrd.content.assessment.type}</p>
                  </div>
                )}
                
                {lrd.content.assessment.weight && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Weight
                    </label>
                    <p className="text-gray-900">{lrd.content.assessment.weight}</p>
                  </div>
                )}
                
                {lrd.content.assessment.description && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <p className="text-gray-900">{lrd.content.assessment.description}</p>
                  </div>
                )}
                
                {lrd.content.assessment.criteria && 
                 lrd.content.assessment.criteria.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Assessment Criteria
                    </label>
                    <ul className="list-disc list-inside space-y-1">
                      {lrd.content.assessment.criteria.map((criterion, index) => (
                        <li key={index} className="text-gray-700">{criterion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500">No assessment information defined</p>
            )}
          </div>
        )}

        {activeTab === 'resources' && (
          <div className="space-y-6">
            {/* Required Resources */}
            {lrd.content?.resources?.required && 
             lrd.content.resources.required.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-3">Required Resources</h3>
                <ul className="list-disc list-inside space-y-1">
                  {lrd.content.resources.required.map((resource, index) => (
                    <li key={index} className="text-gray-700">{resource}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Recommended Resources */}
            {lrd.content?.resources?.recommended && 
             lrd.content.resources.recommended.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-3">Recommended Resources</h3>
                <ul className="list-disc list-inside space-y-1">
                  {lrd.content.resources.recommended.map((resource, index) => (
                    <li key={index} className="text-gray-700">{resource}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Supplementary Resources */}
            {lrd.content?.resources?.supplementary && 
             lrd.content.resources.supplementary.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-3">Supplementary Resources</h3>
                <ul className="list-disc list-inside space-y-1">
                  {lrd.content.resources.supplementary.map((resource, index) => (
                    <li key={index} className="text-gray-700">{resource}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Technology Requirements */}
            {lrd.content?.technology_requirements && 
             lrd.content.technology_requirements.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-3">Technology Requirements</h3>
                <ul className="list-disc list-inside space-y-1">
                  {lrd.content.technology_requirements.map((req, index) => (
                    <li key={index} className="text-gray-700">{req}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {activeTab === 'tasks' && taskList && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Generated Tasks</h2>
            
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">Progress</span>
                <span className="font-medium">
                  {taskList.completed_tasks}/{taskList.total_tasks} completed
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${taskList.progress_percentage || 0}%` }}
                />
              </div>
            </div>
            
            {taskList.tasks && (
              <div className="space-y-2">
                {Object.entries(taskList.tasks).map(([key, tasks]) => (
                  <div key={key}>
                    <h4 className="font-medium text-gray-700 mb-2 capitalize">
                      {key.replace('_', ' ')}
                    </h4>
                    <ul className="space-y-1">
                      {tasks.map((task, index) => (
                        <li key={index} className="flex items-center">
                          <CheckCircle 
                            className={`h-4 w-4 mr-2 ${
                              task.completed ? 'text-green-600' : 'text-gray-400'
                            }`}
                          />
                          <span className={task.completed ? 'line-through text-gray-500' : ''}>
                            {task.title || task}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
            
            <button
              onClick={() => navigate(`/courses/${courseId}/tasks/${taskList.id}`)}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Manage Tasks
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default LRDDetail;