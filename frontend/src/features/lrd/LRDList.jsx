import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Plus,
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  Edit,
  Eye,
  Trash2,
  Send,
  Download,
  Copy,
  Loader2,
  ChevronRight
} from 'lucide-react';
import api from '../../services/api';

const LRDList = () => {
  const { courseId } = useParams();
  const navigate = useNavigate();
  
  const [lrds, setLrds] = useState([]);
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedLRD, setSelectedLRD] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetchData();
  }, [courseId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [courseRes, lrdsRes] = await Promise.all([
        api.get(`/courses/${courseId}`),
        api.get(`/courses/${courseId}/lrds`)
      ]);
      
      setCourse(courseRes.data);
      setLrds(lrdsRes.data);
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
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="h-3 w-3 mr-1" />
        {status.replace('_', ' ')}
      </span>
    );
  };

  const handleSubmitForReview = async (lrdId) => {
    try {
      await api.post(`/lrds/${lrdId}/submit-review`);
      fetchData();
    } catch (error) {
      console.error('Error submitting for review:', error);
    }
  };

  const handleApprove = async (lrdId) => {
    try {
      await api.post(`/lrds/${lrdId}/approve`);
      fetchData();
    } catch (error) {
      console.error('Error approving LRD:', error);
    }
  };

  const handleGenerateTasks = async (lrdId) => {
    try {
      const response = await api.post(`/lrds/${lrdId}/generate-tasks`);
      if (response.data.task_list_id) {
        navigate(`/courses/${courseId}/tasks/${response.data.task_list_id}`);
      }
    } catch (error) {
      console.error('Error generating tasks:', error);
    }
  };

  const handleDelete = async (lrdId) => {
    if (window.confirm('Are you sure you want to delete this LRD?')) {
      try {
        await api.delete(`/lrds/${lrdId}`);
        fetchData();
      } catch (error) {
        console.error('Error deleting LRD:', error);
      }
    }
  };

  const handleClone = async (lrdId) => {
    try {
      const response = await api.post(`/lrds/${lrdId}/clone`);
      navigate(`/courses/${courseId}/lrds/${response.data.id}/edit`);
    } catch (error) {
      console.error('Error cloning LRD:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8 flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Learning Resource Documents
          </h1>
          {course && (
            <p className="text-gray-600">
              {course.title} ({course.code})
            </p>
          )}
        </div>
        
        <button
          onClick={() => navigate(`/courses/${courseId}/lrds/new`)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
        >
          <Plus className="h-5 w-5 mr-2" />
          Create LRD
        </button>
      </div>

      {/* LRD Grid */}
      {lrds.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No LRDs Yet</h3>
          <p className="text-gray-600 mb-6">
            Create your first Learning Resource Document to define the course structure
          </p>
          <button
            onClick={() => navigate(`/courses/${courseId}/lrds/new`)}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create First LRD
          </button>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {lrds.map((lrd) => (
            <div key={lrd.id} className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
              <div className="p-6">
                {/* LRD Header */}
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {lrd.content?.topic || 'Untitled LRD'}
                    </h3>
                    <p className="text-sm text-gray-600">
                      Version {lrd.version} • Created {new Date(lrd.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  {getStatusBadge(lrd.status)}
                </div>

                {/* LRD Content Preview */}
                <div className="space-y-3 mb-4">
                  {lrd.content?.duration && (
                    <div className="flex items-center text-sm text-gray-600">
                      <Clock className="h-4 w-4 mr-2" />
                      Duration: {lrd.content.duration}
                    </div>
                  )}
                  
                  {lrd.content?.objectives && lrd.content.objectives.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-1">Objectives:</p>
                      <ul className="list-disc list-inside text-sm text-gray-600">
                        {lrd.content.objectives.slice(0, 2).map((obj, idx) => (
                          <li key={idx} className="truncate">{obj}</li>
                        ))}
                        {lrd.content.objectives.length > 2 && (
                          <li className="text-blue-600">
                            +{lrd.content.objectives.length - 2} more
                          </li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Task Progress */}
                {lrd.task_lists && lrd.task_lists.length > 0 && (
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Task Progress</span>
                      <span className="font-medium">
                        {lrd.task_lists[0].completed_tasks}/{lrd.task_lists[0].total_tasks}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${lrd.task_lists[0].progress_percentage || 0}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => navigate(`/courses/${courseId}/lrds/${lrd.id}`)}
                    className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 flex items-center"
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    View
                  </button>
                  
                  {lrd.status === 'DRAFT' && (
                    <>
                      <button
                        onClick={() => navigate(`/courses/${courseId}/lrds/${lrd.id}/edit`)}
                        className="px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 flex items-center"
                      >
                        <Edit className="h-4 w-4 mr-1" />
                        Edit
                      </button>
                      
                      <button
                        onClick={() => handleSubmitForReview(lrd.id)}
                        className="px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 flex items-center"
                      >
                        <Send className="h-4 w-4 mr-1" />
                        Submit
                      </button>
                    </>
                  )}
                  
                  {lrd.status === 'APPROVED' && (
                    <button
                      onClick={() => handleGenerateTasks(lrd.id)}
                      className="px-3 py-1.5 text-sm bg-purple-100 text-purple-700 rounded hover:bg-purple-200 flex items-center"
                    >
                      <CheckCircle className="h-4 w-4 mr-1" />
                      Generate Tasks
                    </button>
                  )}
                  
                  <button
                    onClick={() => handleClone(lrd.id)}
                    className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 flex items-center"
                  >
                    <Copy className="h-4 w-4 mr-1" />
                    Clone
                  </button>
                  
                  {lrd.status === 'DRAFT' && (
                    <button
                      onClick={() => handleDelete(lrd.id)}
                      className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 flex items-center"
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Delete
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LRDList;