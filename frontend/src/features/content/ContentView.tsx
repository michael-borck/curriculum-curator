import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Edit,
  Trash2,
  Clock,
  Calendar,
  FileText,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { getContent, deleteContent } from '../../services/api';
import { Modal, Button, LoadingState, Alert } from '../../components/ui';
import type { Content } from '../../types/index';
import { useWorkingContextStore } from '../../stores/workingContextStore';

const ContentView = () => {
  const { unitId, contentId } = useParams<{
    unitId: string;
    contentId: string;
  }>();
  const navigate = useNavigate();
  const topicLabel = useWorkingContextStore(s => s.activeTopicLabel) || 'Week';
  const [content, setContent] = useState<Content | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const fetchContent = async () => {
      if (!contentId || !unitId) {
        setLoading(false);
        setError('No content ID or unit ID provided');
        return;
      }

      try {
        const response = await getContent(unitId, contentId);
        setContent(response.data);
      } catch (err: unknown) {
        console.error('Failed to fetch content:', err);
        setError('Failed to load content');
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [contentId, unitId]);

  const handleDelete = async () => {
    if (!contentId || !unitId) return;

    setIsDeleting(true);
    try {
      await deleteContent(unitId, contentId);
      toast.success('Content deleted successfully');
      navigate(`/units/${unitId}`);
    } catch (err: unknown) {
      console.error('Failed to delete content:', err);
      toast.error('Failed to delete content');
    } finally {
      setIsDeleting(false);
      setShowDeleteModal(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-AU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getContentTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      slides: 'Slides',
      notes: 'Notes',
      worksheet: 'Worksheet',
      handout: 'Handout',
      quiz: 'Quiz',
      case_study: 'Case Study',
      reading: 'Reading',
      video: 'Video',
      discussion: 'Discussion',
      activity: 'Activity',
      assignment: 'Assignment',
      resource: 'Resource',
      // Legacy support
      lecture: 'Slides',
      syllabus: 'Resource',
      interactive: 'Activity',
      tutorial: 'Activity',
    };
    return labels[type] || type;
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      draft: 'bg-yellow-100 text-yellow-800',
      published: 'bg-green-100 text-green-800',
      archived: 'bg-gray-100 text-gray-800',
    };
    return (
      <span
        className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-800'}`}
      >
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  if (loading) {
    return <LoadingState message='Loading content...' />;
  }

  if (error || !content) {
    return (
      <div className='max-w-4xl mx-auto p-6'>
        <Alert variant='error' title='Error'>
          {error || 'Content not found'}
        </Alert>
        <Link
          to={`/units/${unitId}`}
          className='inline-flex items-center text-purple-600 hover:text-purple-700 mt-4'
        >
          <ArrowLeft size={20} className='mr-2' />
          Back to unit
        </Link>
      </div>
    );
  }

  return (
    <div className='max-w-4xl mx-auto p-6'>
      {/* Header */}
      <div className='mb-6'>
        <Link
          to={`/units/${unitId}`}
          className='inline-flex items-center text-purple-600 hover:text-purple-700 mb-4'
        >
          <ArrowLeft size={20} className='mr-2' />
          Back to unit
        </Link>

        <div className='flex justify-between items-start'>
          <div>
            <div className='flex items-center gap-3 mb-2'>
              <h1 className='text-3xl font-bold text-gray-900'>
                {content.title}
              </h1>
              {getStatusBadge(content.status)}
            </div>
            <div className='flex items-center gap-4 text-sm text-gray-500'>
              <span className='flex items-center gap-1'>
                <FileText size={16} />
                {getContentTypeLabel(content.contentType)}
              </span>
              {content.estimatedDurationMinutes && (
                <span className='flex items-center gap-1'>
                  <Clock size={16} />
                  {content.estimatedDurationMinutes} min
                </span>
              )}
              <span className='flex items-center gap-1'>
                <Calendar size={16} />
                {formatDate(content.createdAt)}
              </span>
            </div>
          </div>

          <div className='flex gap-2'>
            <Button
              variant='primary'
              onClick={() =>
                navigate(`/units/${unitId}/content/${contentId}/edit`)
              }
            >
              <Edit size={18} />
              Edit
            </Button>
            <Button variant='danger' onClick={() => setShowDeleteModal(true)}>
              <Trash2 size={18} />
              Delete
            </Button>
          </div>
        </div>
      </div>

      {/* Summary */}
      {content.summary && (
        <div className='bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6'>
          <h2 className='text-sm font-medium text-purple-800 mb-1'>Summary</h2>
          <p className='text-purple-900'>{content.summary}</p>
        </div>
      )}

      {/* Main Content */}
      <div className='bg-white rounded-lg shadow-md p-6'>
        <div
          className='prose prose-purple max-w-none'
          dangerouslySetInnerHTML={{ __html: content.body }}
        />
      </div>

      {/* Metadata */}
      <div className='mt-6 bg-gray-50 rounded-lg p-4'>
        <h3 className='text-sm font-medium text-gray-700 mb-2'>Details</h3>
        <div className='grid grid-cols-2 md:grid-cols-4 gap-4 text-sm'>
          <div>
            <span className='text-gray-500'>Created</span>
            <p className='font-medium'>{formatDate(content.createdAt)}</p>
          </div>
          <div>
            <span className='text-gray-500'>Last Updated</span>
            <p className='font-medium'>
              {content.updatedAt ? formatDate(content.updatedAt) : 'N/A'}
            </p>
          </div>
          {content.weekNumber && (
            <div>
              <span className='text-gray-500'>{topicLabel}</span>
              <p className='font-medium'>
                {topicLabel} {content.weekNumber}
              </p>
            </div>
          )}
          <div>
            <span className='text-gray-500'>Order</span>
            <p className='font-medium'>{content.orderIndex + 1}</p>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title='Delete Content'
        size='sm'
      >
        <p className='text-gray-600 mb-6'>
          Are you sure you want to delete &ldquo;{content.title}&rdquo;? This
          action cannot be undone.
        </p>
        <div className='flex justify-end gap-3'>
          <Button variant='secondary' onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button
            variant='danger'
            onClick={handleDelete}
            disabled={isDeleting}
            loading={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </div>
      </Modal>
    </div>
  );
};

export default ContentView;
