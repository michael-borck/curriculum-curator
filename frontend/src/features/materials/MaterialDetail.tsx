import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileText,
  Edit,
  Download,
  Share2,
  Clock,
  User,
  Calendar,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowLeft,
  Save,
  X,
} from 'lucide-react';
import api from '../../services/api';
import VersionHistory from './VersionHistory';
import RichTextEditor from '../../components/Editor/RichTextEditor';

interface Material {
  id: string;
  unit_id: string;
  module_id?: string;
  type: string;
  title: string;
  description?: string;
  content: any;
  raw_content?: string;
  version: number;
  parent_version_id?: string;
  is_latest: boolean;
  validation_results?: any;
  quality_score?: number;
  generation_context?: any;
  teaching_philosophy?: string;
  created_at: string;
  updated_at: string;
  word_count?: number;
}

const MaterialDetail: React.FC = () => {
  const { materialId } = useParams<{ materialId: string }>();
  const navigate = useNavigate();
  const [material, setMaterial] = useState<Material | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    'content' | 'history' | 'metadata'
  >('content');
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [editedTitle, setEditedTitle] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchMaterial = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get(`/materials/${materialId}`);
      setMaterial(response.data);
      setEditedContent(response.data.raw_content || '');
      setEditedTitle(response.data.title || '');
    } catch (error) {
      console.error('Failed to fetch material:', error);
    } finally {
      setLoading(false);
    }
  }, [materialId]);

  useEffect(() => {
    if (materialId) {
      fetchMaterial();
    }
  }, [materialId, fetchMaterial]);

  const handleSave = async () => {
    if (!material) return;

    try {
      setSaving(true);
      await api.put(`/materials/${materialId}`, {
        title: editedTitle,
        raw_content: editedContent,
        content: { html: editedContent }, // Store as structured content
      });

      // Refresh material data
      await fetchMaterial();
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save material:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleExport = () => {
    if (!material) return;

    // Create a blob with the content
    const blob = new Blob([material.raw_content || ''], {
      type: 'text/markdown',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${material.title.replace(/\s+/g, '_')}_v${material.version}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleVersionRestore = async (_versionId: string) => {
    // Refresh the material after version restore
    await fetchMaterial();
    setActiveTab('content');
  };

  const getContentTypeIcon = (type: string) => {
    const icons: { [key: string]: string } = {
      lecture: '📚',
      quiz: '📝',
      worksheet: '✏️',
      lab: '🔬',
      case_study: '💼',
      interactive_html: '🎮',
      syllabus: '📋',
      reading: '📖',
      video: '🎥',
      assignment: '📄',
    };
    return icons[type] || '📄';
  };

  const getStatusColor = (score?: number) => {
    if (!score) return 'text-gray-600 bg-gray-100';
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-96'>
        <Loader2 className='h-8 w-8 animate-spin text-blue-600' />
      </div>
    );
  }

  if (!material) {
    return (
      <div className='text-center py-12'>
        <AlertCircle className='h-12 w-12 text-red-500 mx-auto mb-4' />
        <h2 className='text-xl font-semibold text-gray-900'>
          Material not found
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
                {getContentTypeIcon(material.type)}
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
                  {material.title}
                </h1>
              )}
            </div>

            {material.description && (
              <p className='text-gray-600 mt-2'>{material.description}</p>
            )}

            <div className='flex items-center space-x-4 mt-4 text-sm text-gray-500'>
              <span className='flex items-center'>
                <FileText className='h-4 w-4 mr-1' />
                Version {material.version}
              </span>
              <span className='flex items-center'>
                <Calendar className='h-4 w-4 mr-1' />
                {new Date(material.updated_at).toLocaleDateString()}
              </span>
              <span className='flex items-center'>
                <User className='h-4 w-4 mr-1' />
                {material.word_count || 0} words
              </span>
              {material.quality_score !== null &&
                material.quality_score !== undefined && (
                  <span
                    className={`flex items-center px-2 py-1 rounded-full ${getStatusColor(material.quality_score)}`}
                  >
                    <CheckCircle className='h-4 w-4 mr-1' />
                    Quality: {material.quality_score}%
                  </span>
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
                    setEditedContent(material.raw_content || '');
                    setEditedTitle(material.title);
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
                <button className='px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center'>
                  <Share2 className='h-4 w-4 mr-2' />
                  Share
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className='border-b border-gray-200 mb-6'>
        <nav className='flex space-x-8'>
          {['content', 'history', 'metadata'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
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
            <RichTextEditor
              content={editedContent}
              onChange={setEditedContent}
            />
          ) : (
            <div className='prose prose-lg max-w-none'>
              {material.raw_content ? (
                <div
                  dangerouslySetInnerHTML={{ __html: material.raw_content }}
                />
              ) : (
                <p className='text-gray-500'>No content available</p>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <VersionHistory
          materialId={materialId!}
          currentVersion={material.version}
          onVersionRestore={handleVersionRestore}
        />
      )}

      {activeTab === 'metadata' && (
        <div className='bg-white rounded-lg shadow-md p-6'>
          <h3 className='text-lg font-semibold mb-4'>Material Metadata</h3>

          <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
            <div>
              <h4 className='font-medium text-gray-700 mb-3'>
                Basic Information
              </h4>
              <dl className='space-y-2'>
                <div>
                  <dt className='text-sm text-gray-500'>Material ID</dt>
                  <dd className='text-sm font-mono'>{material.id}</dd>
                </div>
                <div>
                  <dt className='text-sm text-gray-500'>Unit ID</dt>
                  <dd className='text-sm font-mono'>{material.unit_id}</dd>
                </div>
                {material.module_id && (
                  <div>
                    <dt className='text-sm text-gray-500'>Module ID</dt>
                    <dd className='text-sm font-mono'>{material.module_id}</dd>
                  </div>
                )}
                <div>
                  <dt className='text-sm text-gray-500'>Type</dt>
                  <dd className='text-sm capitalize'>
                    {material.type.replace('_', ' ')}
                  </dd>
                </div>
                <div>
                  <dt className='text-sm text-gray-500'>Teaching Philosophy</dt>
                  <dd className='text-sm capitalize'>
                    {material.teaching_philosophy
                      ?.replace(/_/g, ' ')
                      .toLowerCase() || 'Not specified'}
                  </dd>
                </div>
              </dl>
            </div>

            <div>
              <h4 className='font-medium text-gray-700 mb-3'>
                Version Information
              </h4>
              <dl className='space-y-2'>
                <div>
                  <dt className='text-sm text-gray-500'>Current Version</dt>
                  <dd className='text-sm'>{material.version}</dd>
                </div>
                <div>
                  <dt className='text-sm text-gray-500'>Is Latest</dt>
                  <dd className='text-sm'>
                    {material.is_latest ? 'Yes' : 'No'}
                  </dd>
                </div>
                {material.parent_version_id && (
                  <div>
                    <dt className='text-sm text-gray-500'>Parent Version</dt>
                    <dd className='text-sm font-mono'>
                      {material.parent_version_id}
                    </dd>
                  </div>
                )}
                <div>
                  <dt className='text-sm text-gray-500'>Created</dt>
                  <dd className='text-sm'>
                    {new Date(material.created_at).toLocaleString()}
                  </dd>
                </div>
                <div>
                  <dt className='text-sm text-gray-500'>Last Updated</dt>
                  <dd className='text-sm'>
                    {new Date(material.updated_at).toLocaleString()}
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          {material.validation_results && (
            <div className='mt-6'>
              <h4 className='font-medium text-gray-700 mb-3'>
                Validation Results
              </h4>
              <pre className='bg-gray-50 rounded-lg p-4 text-xs overflow-x-auto'>
                {JSON.stringify(material.validation_results, null, 2)}
              </pre>
            </div>
          )}

          {material.generation_context && (
            <div className='mt-6'>
              <h4 className='font-medium text-gray-700 mb-3'>
                Generation Context
              </h4>
              <pre className='bg-gray-50 rounded-lg p-4 text-xs overflow-x-auto'>
                {JSON.stringify(material.generation_context, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MaterialDetail;
