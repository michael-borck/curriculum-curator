import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileText,
  Edit,
  Download,
  Clock,
  Calendar,
  Loader2,
  ArrowLeft,
  Save,
  X,
  AlertCircle,
} from 'lucide-react';
import { contentApi } from '../../services/contentApi';
import VersionHistory from './VersionHistory';
import UnifiedEditor from '../../components/Editor/UnifiedEditor';
import type { Content } from '../../types';
import { useWorkingContextStore } from '../../stores/workingContextStore';

const MaterialDetail: React.FC = () => {
  const { unitId, contentId } = useParams<{
    unitId: string;
    contentId: string;
  }>();
  const navigate = useNavigate();
  const topicLabel = useWorkingContextStore(s => s.activeTopicLabel) || 'Week';

  const [content, setContent] = useState<Content | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    'content' | 'history' | 'metadata'
  >('content');
  const [isEditing, setIsEditing] = useState(false);
  const [editedBody, setEditedBody] = useState('');
  const [editedTitle, setEditedTitle] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchContent = useCallback(async () => {
    if (!unitId || !contentId) return;
    try {
      setLoading(true);
      const { data } = await contentApi.get(unitId, contentId);
      setContent(data);
      setEditedBody(data.body || '');
      setEditedTitle(data.title || '');
    } catch (err) {
      console.error('Failed to fetch content:', err);
    } finally {
      setLoading(false);
    }
  }, [unitId, contentId]);

  useEffect(() => {
    fetchContent();
  }, [fetchContent]);

  const handleSave = async () => {
    if (!content || !unitId || !contentId) return;
    try {
      setSaving(true);
      await contentApi.update(unitId, contentId, {
        title: editedTitle,
        body: editedBody,
      });
      await fetchContent();
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to save content:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleExport = () => {
    if (!content) return;
    const blob = new Blob([content.body || ''], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${content.title.replace(/\s+/g, '_')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleVersionRestore = async () => {
    await fetchContent();
    setActiveTab('content');
  };

  const getContentTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      lecture: '📚',
      worksheet: '✏️',
      quiz: '📝',
      case_study: '💼',
      reading: '📖',
      assignment: '📄',
      project: '🚀',
      assessment: '📊',
      notes: '🗒️',
      video: '🎥',
      activity: '🎯',
    };
    return icons[type] || '📄';
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-96'>
        <Loader2 className='h-8 w-8 animate-spin text-blue-600' />
      </div>
    );
  }

  if (!content) {
    return (
      <div className='text-center py-12'>
        <AlertCircle className='h-12 w-12 text-red-500 mx-auto mb-4' />
        <h2 className='text-xl font-semibold text-gray-900'>
          Content not found
        </h2>
        <button
          onClick={() => navigate(-1)}
          className='mt-4 text-blue-600 hover:underline'
        >
          Go back
        </button>
      </div>
    );
  }

  return (
    <div className='p-6 max-w-7xl mx-auto'>
      {/* Header */}
      <div className='mb-6'>
        <button
          onClick={() => navigate(-1)}
          className='flex items-center text-gray-600 hover:text-gray-900 mb-4'
        >
          <ArrowLeft className='h-4 w-4 mr-2' />
          Back
        </button>

        <div className='flex items-start justify-between'>
          <div className='flex-1'>
            <div className='flex items-center space-x-3'>
              <span className='text-4xl'>
                {getContentTypeIcon(content.contentType)}
              </span>
              {isEditing ? (
                <input
                  type='text'
                  value={editedTitle}
                  onChange={e => setEditedTitle(e.target.value)}
                  className='text-3xl font-bold text-gray-900 border-b-2 border-blue-500 outline-none'
                />
              ) : (
                <h1 className='text-3xl font-bold text-gray-900'>
                  {content.title}
                </h1>
              )}
            </div>

            {content.summary && (
              <p className='text-gray-600 mt-2'>{content.summary}</p>
            )}

            <div className='flex items-center space-x-4 mt-4 text-sm text-gray-500'>
              <span className='flex items-center'>
                <FileText className='h-4 w-4 mr-1' />
                {content.contentType.replace(/_/g, ' ')}
              </span>
              <span className='flex items-center'>
                <Calendar className='h-4 w-4 mr-1' />
                {new Date(
                  content.updatedAt || content.createdAt
                ).toLocaleDateString()}
              </span>
              {content.weekNumber && (
                <span>
                  {topicLabel} {content.weekNumber}
                </span>
              )}
              {content.estimatedDurationMinutes && (
                <span>{content.estimatedDurationMinutes} min</span>
              )}
              {content.currentCommit && (
                <code className='bg-gray-100 px-1.5 py-0.5 rounded text-xs'>
                  {content.currentCommit.slice(0, 7)}
                </code>
              )}
            </div>
          </div>

          <div className='flex items-center space-x-2'>
            {isEditing ? (
              <>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className='px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center'
                >
                  {saving ? (
                    <Loader2 className='h-4 w-4 animate-spin mr-2' />
                  ) : (
                    <Save className='h-4 w-4 mr-2' />
                  )}
                  Save
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false);
                    setEditedBody(content.body || '');
                    setEditedTitle(content.title);
                  }}
                  className='px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 flex items-center'
                >
                  <X className='h-4 w-4 mr-2' />
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setIsEditing(true)}
                  className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center'
                >
                  <Edit className='h-4 w-4 mr-2' />
                  Edit
                </button>
                <button
                  onClick={handleExport}
                  className='px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center'
                >
                  <Download className='h-4 w-4 mr-2' />
                  Export
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className='border-b border-gray-200 mb-6'>
        <nav className='flex space-x-8'>
          {(['content', 'history', 'metadata'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'history' && <Clock className='h-4 w-4 inline mr-2' />}
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'content' && (
        <div className='bg-white rounded-lg shadow-md p-6'>
          {isEditing ? (
            <UnifiedEditor
              content={editedBody}
              onChange={setEditedBody}
              contentId={contentId}
            />
          ) : (
            <div className='prose prose-lg max-w-none'>
              {content.body ? (
                <div dangerouslySetInnerHTML={{ __html: content.body }} />
              ) : (
                <p className='text-gray-500'>No content available</p>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && unitId && contentId && (
        <VersionHistory
          unitId={unitId}
          contentId={contentId}
          onVersionRestore={handleVersionRestore}
        />
      )}

      {activeTab === 'metadata' && (
        <div className='bg-white rounded-lg shadow-md p-6'>
          <h3 className='text-lg font-semibold mb-4'>Content Metadata</h3>
          <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
            <div>
              <h4 className='font-medium text-gray-700 mb-3'>
                Basic Information
              </h4>
              <dl className='space-y-2'>
                <div>
                  <dt className='text-sm text-gray-500'>Content ID</dt>
                  <dd className='text-sm font-mono'>{content.id}</dd>
                </div>
                <div>
                  <dt className='text-sm text-gray-500'>Unit ID</dt>
                  <dd className='text-sm font-mono'>{content.unitId}</dd>
                </div>
                <div>
                  <dt className='text-sm text-gray-500'>Type</dt>
                  <dd className='text-sm capitalize'>
                    {content.contentType.replace(/_/g, ' ')}
                  </dd>
                </div>
                <div>
                  <dt className='text-sm text-gray-500'>Status</dt>
                  <dd className='text-sm capitalize'>{content.status}</dd>
                </div>
              </dl>
            </div>

            <div>
              <h4 className='font-medium text-gray-700 mb-3'>
                Version Information
              </h4>
              <dl className='space-y-2'>
                {content.currentCommit && (
                  <div>
                    <dt className='text-sm text-gray-500'>Current Commit</dt>
                    <dd className='text-sm font-mono'>
                      {content.currentCommit}
                    </dd>
                  </div>
                )}
                <div>
                  <dt className='text-sm text-gray-500'>Created</dt>
                  <dd className='text-sm'>
                    {new Date(content.createdAt).toLocaleString()}
                  </dd>
                </div>
                {content.updatedAt && (
                  <div>
                    <dt className='text-sm text-gray-500'>Last Updated</dt>
                    <dd className='text-sm'>
                      {new Date(content.updatedAt).toLocaleString()}
                    </dd>
                  </div>
                )}
                {content.weekNumber && (
                  <div>
                    <dt className='text-sm text-gray-500'>{topicLabel}</dt>
                    <dd className='text-sm'>
                      {topicLabel} {content.weekNumber}
                    </dd>
                  </div>
                )}
                {content.estimatedDurationMinutes && (
                  <div>
                    <dt className='text-sm text-gray-500'>Est. Duration</dt>
                    <dd className='text-sm'>
                      {content.estimatedDurationMinutes} minutes
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MaterialDetail;
