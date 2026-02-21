import { useState, useEffect, useCallback } from 'react';
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
  Copy,
  Loader2,
} from 'lucide-react';
import api from '../../services/api';

const DesignList = () => {
  const { unitId } = useParams();
  const navigate = useNavigate();

  const [designs, setDesigns] = useState<any[]>([]);
  const [unit, setUnit] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [unitRes, designsRes] = await Promise.all([
        api.get(`/units/${unitId}`),
        api.get(`/units/${unitId}/designs`),
      ]);

      setUnit(unitRes.data);
      setDesigns(designsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, [unitId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      DRAFT: { color: 'bg-gray-100 text-gray-800', icon: Edit },
      IN_REVIEW: { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      APPROVED: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      REJECTED: { color: 'bg-red-100 text-red-800', icon: AlertCircle },
    };

    const config =
      statusConfig[status as keyof typeof statusConfig] || statusConfig.DRAFT;
    const Icon = config.icon;

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}
      >
        <Icon className='h-3 w-3 mr-1' />
        {status.replace('_', ' ')}
      </span>
    );
  };

  const handleSubmitForReview = async (designId: string) => {
    try {
      await api.post(`/designs/${designId}/submit-review`);
      fetchData();
    } catch (error) {
      console.error('Error submitting for review:', error);
    }
  };

  const handleGenerateTasks = async (designId: string) => {
    try {
      const response = await api.post(`/designs/${designId}/generate-tasks`);
      if (response.data.task_list_id) {
        navigate(`/units/${unitId}/tasks/${response.data.task_list_id}`);
      }
    } catch (error) {
      console.error('Error generating tasks:', error);
    }
  };

  const handleDelete = async (designId: string) => {
    if (
      window.confirm('Are you sure you want to delete this learning design?')
    ) {
      try {
        await api.delete(`/designs/${designId}`);
        fetchData();
      } catch (error) {
        console.error('Error deleting learning design:', error);
      }
    }
  };

  const handleClone = async (designId: string) => {
    try {
      const response = await api.post(`/designs/${designId}/clone`);
      navigate(`/units/${unitId}/designs/${response.data.id}/edit`);
    } catch (error) {
      console.error('Error cloning learning design:', error);
    }
  };

  if (loading) {
    return (
      <div className='flex justify-center items-center h-64'>
        <Loader2 className='h-8 w-8 animate-spin text-blue-600' />
      </div>
    );
  }

  return (
    <div className='max-w-7xl mx-auto p-6'>
      {/* Header */}
      <div className='mb-8 flex justify-between items-start'>
        <div>
          <h1 className='text-3xl font-bold text-gray-900 mb-2'>
            Learning Designs
          </h1>
          {unit && (
            <p className='text-gray-600'>
              {unit.title} ({unit.code})
            </p>
          )}
        </div>

        <button
          onClick={() => navigate(`/units/${unitId}/designs/new`)}
          className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center'
        >
          <Plus className='h-5 w-5 mr-2' />
          Create Learning Design
        </button>
      </div>

      {/* Design Grid */}
      {designs.length === 0 ? (
        <div className='bg-white rounded-lg shadow-md p-12 text-center'>
          <FileText className='h-12 w-12 text-gray-400 mx-auto mb-4' />
          <h3 className='text-lg font-medium text-gray-900 mb-2'>
            No Learning Designs Yet
          </h3>
          <p className='text-gray-600 mb-6'>
            Create your first learning design to define the unit structure
          </p>
          <button
            onClick={() => navigate(`/units/${unitId}/designs/new`)}
            className='px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700'
          >
            Create First Learning Design
          </button>
        </div>
      ) : (
        <div className='grid gap-6 lg:grid-cols-2'>
          {designs.map(design => (
            <div
              key={design.id}
              className='bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow'
            >
              <div className='p-6'>
                {/* Design Header */}
                <div className='flex justify-between items-start mb-4'>
                  <div>
                    <h3 className='text-lg font-semibold text-gray-900 mb-1'>
                      {design.content?.topic || 'Untitled Design'}
                    </h3>
                    <p className='text-sm text-gray-600'>
                      Version {design.version} • Created{' '}
                      {new Date(design.createdAt).toLocaleDateString()}
                    </p>
                  </div>
                  {getStatusBadge(design.status)}
                </div>

                {/* Design Content Preview */}
                <div className='space-y-3 mb-4'>
                  {design.content?.duration && (
                    <div className='flex items-center text-sm text-gray-600'>
                      <Clock className='h-4 w-4 mr-2' />
                      Duration: {design.content.duration}
                    </div>
                  )}

                  {design.content?.objectives &&
                    design.content.objectives.length > 0 && (
                      <div>
                        <p className='text-sm font-medium text-gray-700 mb-1'>
                          Objectives:
                        </p>
                        <ul className='list-disc list-inside text-sm text-gray-600'>
                          {design.content.objectives
                            .slice(0, 2)
                            .map((obj: string, idx: number) => (
                              <li key={idx} className='truncate'>
                                {obj}
                              </li>
                            ))}
                          {design.content.objectives.length > 2 && (
                            <li className='text-blue-600'>
                              +{design.content.objectives.length - 2} more
                            </li>
                          )}
                        </ul>
                      </div>
                    )}
                </div>

                {/* Task Progress */}
                {design.taskLists && design.taskLists.length > 0 && (
                  <div className='mb-4'>
                    <div className='flex justify-between text-sm mb-1'>
                      <span className='text-gray-600'>Task Progress</span>
                      <span className='font-medium'>
                        {design.taskLists[0].completedTasks}/
                        {design.taskLists[0].totalTasks}
                      </span>
                    </div>
                    <div className='w-full bg-gray-200 rounded-full h-2'>
                      <div
                        className='bg-blue-600 h-2 rounded-full'
                        style={{
                          width: `${design.taskLists[0].progressPercentage || 0}%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className='flex flex-wrap gap-2'>
                  <button
                    onClick={() =>
                      navigate(`/units/${unitId}/designs/${design.id}`)
                    }
                    className='px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 flex items-center'
                  >
                    <Eye className='h-4 w-4 mr-1' />
                    View
                  </button>

                  {design.status === 'DRAFT' && (
                    <>
                      <button
                        onClick={() =>
                          navigate(`/units/${unitId}/designs/${design.id}/edit`)
                        }
                        className='px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 flex items-center'
                      >
                        <Edit className='h-4 w-4 mr-1' />
                        Edit
                      </button>

                      <button
                        onClick={() => handleSubmitForReview(design.id)}
                        className='px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 flex items-center'
                      >
                        <Send className='h-4 w-4 mr-1' />
                        Submit
                      </button>
                    </>
                  )}

                  {design.status === 'APPROVED' && (
                    <button
                      onClick={() => handleGenerateTasks(design.id)}
                      className='px-3 py-1.5 text-sm bg-purple-100 text-purple-700 rounded hover:bg-purple-200 flex items-center'
                    >
                      <CheckCircle className='h-4 w-4 mr-1' />
                      Generate Tasks
                    </button>
                  )}

                  <button
                    onClick={() => handleClone(design.id)}
                    className='px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 flex items-center'
                  >
                    <Copy className='h-4 w-4 mr-1' />
                    Clone
                  </button>

                  {design.status === 'DRAFT' && (
                    <button
                      onClick={() => handleDelete(design.id)}
                      className='px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 flex items-center'
                    >
                      <Trash2 className='h-4 w-4 mr-1' />
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

export default DesignList;
