import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Upload,
  FileText,
  File,
  CheckCircle,
  AlertCircle,
  Loader2,
  X,
  FileSpreadsheet,
  FileImage,
  FileVideo,
  Info,
  CheckSquare,
  Square,
  Plus,
  FolderOpen,
  Sparkles,
} from 'lucide-react';
import api, {
  enhanceContent,
  getContent,
  updateContent,
} from '../../services/api';
import { useNavigate } from 'react-router-dom';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  error?: string;
  result?: FileResult;
  file?: File;
}

interface FileResult {
  content_id?: string;
  content_type?: string;
  content_type_confidence?: number;
  wordCount?: number;
  sections_found?: number;
  week_number?: number | null;
  isZipAnalysis?: boolean;
  analysis?: ZipAnalysis;
  categorization?: {
    difficultyLevel?: string;
    estimatedDuration?: number;
    alternative_types?: string[];
  };
  suggestions?: string[];
  gaps?: Array<{ element: string; severity: string; suggestion: string }>;
}

interface ZipAnalysis {
  total_files: number;
  files_by_week: Record<string, unknown[]>;
  unit_outline_found: boolean;
  unit_outline_file?: {
    filename: string;
    path: string;
  };
  suggested_structure?: Array<{
    week: number;
    total_files: number;
    file_types: Record<string, number>;
  }>;
}

interface WeekAssignment {
  content_id: string;
  week_number: number | null;
}

interface Unit {
  id: string;
  title: string;
  code: string;
  description?: string;
}

interface NewUnitForm {
  title: string;
  code: string;
  description: string;
}

const ImportMaterials = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [selectedUnit, setSelectedUnit] = useState('');
  const [units, setUnits] = useState<Unit[]>([]);
  const [unitsLoading, setUnitsLoading] = useState(true);
  const [unitsError, setUnitsError] = useState<string | null>(null);
  const [weekAssignments, setWeekAssignments] = useState<WeekAssignment[]>([]);
  const [bulkWeek, setBulkWeek] = useState<number | ''>('');
  const [showUnassigned, setShowUnassigned] = useState(false);
  const [unassignedContent, setUnassignedContent] = useState<
    Array<{
      id: string;
      title: string;
      content_type: string;
    }>
  >([]);
  const [loadingUnassigned, setLoadingUnassigned] = useState(false);

  // AI enhance state
  const [enhancingFiles, setEnhancingFiles] = useState<Set<string>>(new Set());
  const [enhancedFiles, setEnhancedFiles] = useState<Set<string>>(new Set());
  const [batchEnhancing, setBatchEnhancing] = useState(false);
  const [batchEnhanceProgress, setBatchEnhanceProgress] = useState({
    current: 0,
    total: 0,
  });

  // New unit creation state
  const [showCreateUnit, setShowCreateUnit] = useState(false);
  const [creatingUnit, setCreatingUnit] = useState(false);
  const [createUnitError, setCreateUnitError] = useState<string | null>(null);
  const [newUnitForm, setNewUnitForm] = useState<NewUnitForm>({
    title: '',
    code: '',
    description: '',
  });

  // Suggested unit details from ZIP analysis
  const [suggestedUnitDetails, setSuggestedUnitDetails] = useState<{
    title?: string | undefined;
    code?: string | undefined;
    fromZip: boolean;
  } | null>(null);

  useEffect(() => {
    fetchUnits();
  }, []);

  const fetchUnassignedContent = useCallback(async () => {
    if (!selectedUnit) return;

    setLoadingUnassigned(true);
    try {
      const response = await api.get(
        `/units/${selectedUnit}/content/unassigned`
      );
      setUnassignedContent(response.data.contents || []);
    } catch (error) {
      console.error('Error fetching unassigned content:', error);
      setUnassignedContent([]);
    } finally {
      setLoadingUnassigned(false);
    }
  }, [selectedUnit]);

  useEffect(() => {
    if (selectedUnit) {
      fetchUnassignedContent();
    }
  }, [selectedUnit, fetchUnassignedContent]);

  const fetchUnits = async () => {
    setUnitsLoading(true);
    setUnitsError(null);
    try {
      const response = await api.get('/units');
      // Handle both { units: [...] } and direct array response formats
      const unitsData = response.data.units || response.data || [];
      setUnits(Array.isArray(unitsData) ? unitsData : []);
    } catch (error) {
      console.error('Error fetching units:', error);
      setUnitsError('Failed to load units. Please try again.');
      setUnits([]);
    } finally {
      setUnitsLoading(false);
    }
  };

  const createUnit = async () => {
    if (!newUnitForm.title.trim() || !newUnitForm.code.trim()) {
      setCreateUnitError('Title and code are required');
      return;
    }

    setCreatingUnit(true);
    setCreateUnitError(null);

    try {
      const response = await api.post('/units/create', {
        title: newUnitForm.title.trim(),
        code: newUnitForm.code.trim(),
        description: newUnitForm.description.trim() || undefined,
      });

      const newUnit = response.data;

      // Add to units list and select it
      setUnits(prev => [newUnit, ...prev]);
      setSelectedUnit(newUnit.id);

      // Reset form
      setNewUnitForm({ title: '', code: '', description: '' });
      setShowCreateUnit(false);
      setSuggestedUnitDetails(null);
    } catch (error: unknown) {
      console.error('Error creating unit:', error);
      const err = error as { response?: { data?: { detail?: string } } };
      setCreateUnitError(
        err.response?.data?.detail || 'Failed to create unit. Please try again.'
      );
    } finally {
      setCreatingUnit(false);
    }
  };

  const updateWeekAssignment = async (
    contentId: string,
    weekNumber: number | null
  ) => {
    try {
      await api.patch(
        `/units/${selectedUnit}/content/${contentId}/week`,
        null,
        {
          params: { week_number: weekNumber },
        }
      );

      // Update local state
      setFiles(prev =>
        prev.map(f =>
          f.result?.content_id === contentId
            ? {
                ...f,
                result: {
                  ...f.result,
                  week_number: weekNumber,
                },
              }
            : f
        )
      );

      // Also update unassigned list if needed
      if (weekNumber === null) {
        // If setting to null, add to unassigned list
        const file = files.find(f => f.result?.content_id === contentId);
        if (file) {
          setUnassignedContent(prev => [
            ...prev,
            {
              id: contentId,
              title: file.name,
              content_type: file.result?.content_type || 'general',
            },
          ]);
        }
      } else {
        // If assigning a week, remove from unassigned list
        setUnassignedContent(prev =>
          prev.filter(item => item.id !== contentId)
        );
      }

      return true;
    } catch (error) {
      console.error('Error updating week assignment:', error);
      return false;
    }
  };

  const bulkUpdateWeeks = async () => {
    if (bulkWeek === '' || bulkWeek === null || bulkWeek === undefined) return;

    const updates = weekAssignments.map(assignment => ({
      content_id: assignment.content_id,
      week_number: bulkWeek,
    }));

    try {
      const response = await api.post(
        `/units/${selectedUnit}/content/bulk/week`,
        updates
      );

      if (response.data.success) {
        // Update local state for all selected files
        setFiles(prev =>
          prev.map(f => {
            const assignment = weekAssignments.find(
              a => a.content_id === f.result?.content_id
            );
            if (assignment) {
              return {
                ...f,
                result: {
                  ...f.result,
                  week_number: bulkWeek,
                },
              };
            }
            return f;
          })
        );

        // Clear selections
        setWeekAssignments([]);
        setBulkWeek('');

        // Refresh unassigned list
        fetchUnassignedContent();
      }
    } catch (error) {
      console.error('Error bulk updating weeks:', error);
    }
  };

  const handleEnhanceImported = async (fileInfo: UploadedFile) => {
    const contentId = fileInfo.result?.content_id;
    if (!contentId || !selectedUnit) return;

    setEnhancingFiles(prev => new Set(prev).add(fileInfo.id));

    try {
      // Fetch the content body
      const contentResponse = await getContent(selectedUnit, contentId);
      const body = contentResponse.data.body;
      if (!body) throw new Error('No content body found');

      // Enhance with AI
      const enhanceResponse = await enhanceContent(body, 'inquiry-based', {
        unitId: selectedUnit,
      });
      const enhancedBody = enhanceResponse.data.enhanced_content;
      if (!enhancedBody) throw new Error('No enhanced content returned');

      // Save the enhanced content back
      await updateContent(selectedUnit, contentId, { body: enhancedBody });

      setEnhancedFiles(prev => new Set(prev).add(fileInfo.id));
    } catch (error) {
      console.error('Enhancement failed:', error);
      const err = error as { message?: string };
      window.alert(`Enhancement failed: ${err.message || 'Unknown error'}`);
    } finally {
      setEnhancingFiles(prev => {
        const next = new Set(prev);
        next.delete(fileInfo.id);
        return next;
      });
    }
  };

  const handleEnhanceAll = async () => {
    const eligibleFiles = files.filter(
      f =>
        f.status === 'completed' &&
        f.result?.content_id &&
        !enhancedFiles.has(f.id) &&
        !enhancingFiles.has(f.id)
    );
    if (eligibleFiles.length === 0) return;

    setBatchEnhancing(true);
    setBatchEnhanceProgress({ current: 0, total: eligibleFiles.length });

    for (let i = 0; i < eligibleFiles.length; i++) {
      setBatchEnhanceProgress({ current: i + 1, total: eligibleFiles.length });
      await handleEnhanceImported(eligibleFiles[i]);
    }

    setBatchEnhancing(false);
  };

  const toggleWeekAssignment = (
    contentId: string,
    weekNumber: number | null
  ) => {
    setWeekAssignments(prev => {
      const existing = prev.find(a => a.content_id === contentId);
      if (existing) {
        return prev.filter(a => a.content_id !== contentId);
      } else {
        return [...prev, { content_id: contentId, week_number: weekNumber }];
      }
    });
  };

  // Extract unit details from filename (for ZIP files)
  const extractUnitDetailsFromFilename = (filename: string) => {
    // Common patterns: "COMP101_Unit_Materials.zip", "Web Development 2024.zip"
    const codePattern = /([A-Z]{2,4}\d{3,4})/i;
    const codeMatch = filename.match(codePattern);

    // Remove extension and common suffixes
    let title = filename
      .replace(/\.(zip|pdf|docx?)$/i, '')
      .replace(/_materials?|_content|_unit/gi, ' ')
      .replace(/_/g, ' ')
      .trim();

    // If we found a code, remove it from title
    if (codeMatch) {
      title = title.replace(codeMatch[0], '').trim();
    }

    // Clean up title
    title = title.replace(/\s+/g, ' ').trim();

    return {
      title: title || undefined,
      code: codeMatch?.[0]?.toUpperCase() || undefined,
    };
  };

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'pending' as const,
        progress: 0,
        file: file,
      }));
      setFiles(prev => [...prev, ...newFiles]);

      // If no units exist and a ZIP file is dropped, suggest unit creation
      if (units.length === 0 && !showCreateUnit) {
        const zipFile = acceptedFiles.find(
          f =>
            f.type === 'application/zip' ||
            f.type === 'application/x-zip-compressed' ||
            f.name.endsWith('.zip')
        );

        if (zipFile) {
          const details = extractUnitDetailsFromFilename(zipFile.name);
          if (details.title || details.code) {
            setSuggestedUnitDetails({
              title: details.title,
              code: details.code,
              fromZip: true,
            });
            setNewUnitForm(prev => ({
              ...prev,
              title: details.title ?? prev.title,
              code: details.code ?? prev.code,
            }));
          }
          setShowCreateUnit(true);
        } else if (acceptedFiles.length > 0) {
          // For non-ZIP files, just show create unit form
          setShowCreateUnit(true);
        }
      }
    },
    [units.length, showCreateUnit]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        ['.docx'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation':
        ['.pptx'],
      'text/markdown': ['.md'],
      'text/plain': ['.txt'],
      'text/html': ['.html'],
      'application/zip': ['.zip'],
      'application/x-zip-compressed': ['.zip'],
    },
    multiple: true,
  });

  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return <FileText className='h-5 w-5' />;
    if (type.includes('presentation') || type.includes('powerpoint'))
      return <FileSpreadsheet className='h-5 w-5' />;
    if (type.includes('word')) return <FileText className='h-5 w-5' />;
    if (type.includes('image')) return <FileImage className='h-5 w-5' />;
    if (type.includes('video')) return <FileVideo className='h-5 w-5' />;
    return <File className='h-5 w-5' />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const handleZipUpload = async (file: UploadedFile) => {
    if (!file.file) return;

    const formData = new FormData();
    formData.append('file', file.file);

    try {
      setFiles(prev =>
        prev.map(f =>
          f.id === file.id ? { ...f, status: 'uploading', progress: 0 } : f
        )
      );

      const response = await api.post(
        `/content/import/zip/${selectedUnit}`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: progressEvent => {
            const progress = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0;
            setFiles(prev =>
              prev.map(f => (f.id === file.id ? { ...f, progress } : f))
            );
          },
        }
      );

      // Mark as completed
      setFiles(prev =>
        prev.map(f =>
          f.id === file.id
            ? {
                ...f,
                status: 'completed',
                progress: 100,
                result: {
                  ...response.data,
                  isZipAnalysis: true,
                },
              }
            : f
        )
      );

      // Show ZIP analysis results
      const analysis = response.data.analysis as ZipAnalysis;
      const weekCount = Object.keys(analysis.files_by_week || {}).length;
      window.alert(
        `ZIP analysis complete!\n\nFound ${analysis.total_files} files across ${weekCount} weeks.\n\n${analysis.unit_outline_found ? 'Unit outline detected' : 'No unit outline found'}\n\nCheck the suggestions below for organizing your content.`
      );
    } catch (error: unknown) {
      console.error('ZIP upload error:', error);
      const err = error as {
        response?: { data?: { detail?: string } };
        message?: string;
      };
      setFiles(prev =>
        prev.map(f =>
          f.id === file.id
            ? {
                ...f,
                status: 'error',
                error:
                  'ZIP upload failed: ' +
                  (err.response?.data?.detail || err.message),
              }
            : f
        )
      );
    }
  };

  const handleSingleUpload = async (fileInfo: UploadedFile) => {
    const actualFile = fileInfo.file;
    if (!actualFile) return;

    const formData = new FormData();
    formData.append('file', actualFile);

    try {
      setFiles(prev =>
        prev.map(f =>
          f.id === fileInfo.id ? { ...f, status: 'uploading', progress: 0 } : f
        )
      );

      const response = await api.post(
        `/units/${selectedUnit}/content/upload`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: progressEvent => {
            const progress = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0;
            setFiles(prev =>
              prev.map(f => (f.id === fileInfo.id ? { ...f, progress } : f))
            );
          },
        }
      );

      // Mark as completed with results
      setFiles(prev =>
        prev.map(f =>
          f.id === fileInfo.id
            ? {
                ...f,
                status: 'completed',
                progress: 100,
                result: response.data,
              }
            : f
        )
      );

      // Add to unassigned list since week number isn't specified during upload
      if (response.data.content_id) {
        setUnassignedContent(prev => [
          ...prev,
          {
            id: response.data.content_id,
            title: fileInfo.name,
            content_type: response.data.content_type || 'general',
          },
        ]);
      }
    } catch (error: unknown) {
      console.error('Upload error:', error);
      const err = error as {
        response?: { data?: { detail?: string } };
        message?: string;
      };
      setFiles(prev =>
        prev.map(f =>
          f.id === fileInfo.id
            ? {
                ...f,
                status: 'error',
                error:
                  'Upload failed: ' +
                  (err.response?.data?.detail || err.message),
              }
            : f
        )
      );
    }
  };

  const handleBatchUpload = async (filesToUpload: UploadedFile[]) => {
    const formData = new FormData();
    const fileMap = new Map<string, string>();

    for (const fileInfo of filesToUpload) {
      const actualFile = fileInfo.file;
      if (actualFile) {
        formData.append('files', actualFile);
        fileMap.set(actualFile.name, fileInfo.id);
      }
    }

    // Mark all as uploading
    setFiles(prev =>
      prev.map(f => {
        if (filesToUpload.some(u => u.id === f.id)) {
          return { ...f, status: 'uploading', progress: 0 };
        }
        return f;
      })
    );

    try {
      const response = await api.post(
        `/units/${selectedUnit}/content/upload/batch`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      );

      // Update file statuses based on response
      interface BatchResult {
        filename: string;
        success: boolean;
        error?: string;
        content_id?: string;
        content_type?: string;
      }

      response.data.results.forEach((result: BatchResult) => {
        const fileId = fileMap.get(result.filename);
        if (fileId) {
          setFiles(prev =>
            prev.map(f => {
              if (f.id !== fileId) return f;
              const updated: UploadedFile = {
                ...f,
                status: result.success
                  ? ('completed' as const)
                  : ('error' as const),
                progress: 100,
                result: result,
              };
              if (result.error) {
                updated.error = result.error;
              }
              return updated;
            })
          );

          // Add to unassigned list since batch upload doesn't specify week number
          if (result.success && result.content_id) {
            const fileInfo = filesToUpload.find(f => f.id === fileId);
            if (fileInfo) {
              setUnassignedContent(prev => [
                ...prev,
                {
                  id: result.content_id as string,
                  title: fileInfo.name,
                  content_type: result.content_type || 'general',
                },
              ]);
            }
          }
        }
      });
    } catch (error: unknown) {
      // Mark all as error
      console.error('Batch upload error:', error);
      filesToUpload.forEach(fileInfo => {
        setFiles(prev =>
          prev.map(f =>
            f.id === fileInfo.id
              ? {
                  ...f,
                  status: 'error',
                  error: 'Batch upload failed',
                }
              : f
          )
        );
      });
    }
  };

  const uploadFiles = async () => {
    if (!selectedUnit) {
      if (units.length === 0) {
        setShowCreateUnit(true);
      } else {
        window.alert('Please select a unit first');
      }
      return;
    }

    setUploading(true);
    const pendingFiles = files.filter(f => f.status === 'pending');

    // Check for ZIP files
    const zipFiles = pendingFiles.filter(
      f =>
        f.type === 'application/zip' ||
        f.type === 'application/x-zip-compressed' ||
        f.name?.endsWith('.zip')
    );

    const regularFiles = pendingFiles.filter(
      f =>
        !(
          f.type === 'application/zip' ||
          f.type === 'application/x-zip-compressed' ||
          f.name?.endsWith('.zip')
        )
    );

    // Handle ZIP files separately (one at a time)
    if (zipFiles.length > 0) {
      if (zipFiles.length > 1) {
        window.alert('Please upload only one ZIP file at a time');
        setUploading(false);
        return;
      }

      const zipFile = zipFiles[0];
      await handleZipUpload(zipFile);

      // If there are also regular files, upload them too
      if (regularFiles.length > 0) {
        if (regularFiles.length === 1) {
          await handleSingleUpload(regularFiles[0]);
        } else {
          await handleBatchUpload(regularFiles);
        }
      }

      setUploading(false);
      return;
    }

    // Handle regular files
    if (regularFiles.length > 0) {
      if (regularFiles.length === 1) {
        await handleSingleUpload(regularFiles[0]);
      } else {
        await handleBatchUpload(regularFiles);
      }
    }

    setUploading(false);

    // Redirect to unit page after upload completes
    if (selectedUnit) {
      window.setTimeout(() => {
        navigate(`/units/${selectedUnit}`);
      }, 1000);
    }
  };

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  // Check if we have files ready to import
  const hasPendingFiles = files.some(f => f.status === 'pending');
  const canImport = selectedUnit && hasPendingFiles && !uploading;

  return (
    <div className='p-6 max-w-6xl mx-auto'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>
          Import Materials
        </h1>
        <p className='text-gray-600'>
          Upload and import existing unit materials for enhancement
        </p>
      </div>

      {/* Auto-Detection Info */}
      <div className='bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6'>
        <div className='flex items-start'>
          <Info className='h-5 w-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0' />
          <div className='text-sm'>
            <p className='font-medium text-blue-900 mb-1'>
              Smart Content Detection
            </p>
            <p className='text-blue-800'>
              Files are automatically categorized based on their content (e.g.,
              &quot;Quiz 1&quot; to Quiz, &quot;Lab Exercise&quot; to Lab). You
              can change the type using the dropdown if the detection is
              incorrect. ZIP archives will be analyzed to detect unit structure
              and week organization.
            </p>
          </div>
        </div>
      </div>

      {/* Unit Selection Section */}
      <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
        <label className='block text-sm font-medium text-gray-700 mb-2'>
          Target Unit {!showCreateUnit && '*'}
        </label>

        {unitsLoading ? (
          <div className='flex items-center text-gray-500'>
            <Loader2 className='h-5 w-5 animate-spin mr-2' />
            Loading units...
          </div>
        ) : unitsError ? (
          <div className='text-red-600 flex items-center'>
            <AlertCircle className='h-5 w-5 mr-2' />
            {unitsError}
            <button
              onClick={fetchUnits}
              className='ml-2 text-blue-600 hover:underline'
            >
              Retry
            </button>
          </div>
        ) : units.length === 0 && !showCreateUnit ? (
          /* No Units Empty State */
          <div className='border-2 border-dashed border-gray-300 rounded-lg p-8 text-center'>
            <FolderOpen className='h-12 w-12 text-gray-400 mx-auto mb-4' />
            <h3 className='text-lg font-medium text-gray-900 mb-2'>
              No Units Found
            </h3>
            <p className='text-gray-600 mb-4'>
              You need to create a unit before importing materials.
              {files.length > 0 && (
                <span className='block mt-1 text-blue-600'>
                  We detected {files.length} file(s) ready to import.
                </span>
              )}
            </p>
            <button
              onClick={() => setShowCreateUnit(true)}
              className='inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700'
            >
              <Plus className='h-4 w-4 mr-2' />
              Create New Unit
            </button>
          </div>
        ) : showCreateUnit ? (
          /* Inline Unit Creation Form */
          <div className='border border-blue-200 bg-blue-50 rounded-lg p-4'>
            <div className='flex items-center justify-between mb-4'>
              <h3 className='font-medium text-blue-900'>Create New Unit</h3>
              {units.length > 0 && (
                <button
                  onClick={() => {
                    setShowCreateUnit(false);
                    setSuggestedUnitDetails(null);
                    setCreateUnitError(null);
                  }}
                  className='text-gray-500 hover:text-gray-700'
                >
                  <X className='h-5 w-5' />
                </button>
              )}
            </div>

            {suggestedUnitDetails?.fromZip && (
              <div className='bg-green-50 border border-green-200 rounded p-3 mb-4 text-sm text-green-800'>
                <CheckCircle className='h-4 w-4 inline mr-2' />
                We detected unit details from your ZIP file. Review and adjust
                if needed.
              </div>
            )}

            <div className='space-y-4'>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Unit Title *
                </label>
                <input
                  type='text'
                  value={newUnitForm.title}
                  onChange={e =>
                    setNewUnitForm(prev => ({ ...prev, title: e.target.value }))
                  }
                  placeholder='e.g., Introduction to Web Development'
                  className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                />
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Unit Code *
                </label>
                <input
                  type='text'
                  value={newUnitForm.code}
                  onChange={e =>
                    setNewUnitForm(prev => ({
                      ...prev,
                      code: e.target.value.toUpperCase(),
                    }))
                  }
                  placeholder='e.g., COMP101'
                  className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                />
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Description (optional)
                </label>
                <textarea
                  value={newUnitForm.description}
                  onChange={e =>
                    setNewUnitForm(prev => ({
                      ...prev,
                      description: e.target.value,
                    }))
                  }
                  placeholder='Brief description of the unit...'
                  rows={2}
                  className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                />
              </div>

              {createUnitError && (
                <div className='text-red-600 text-sm flex items-center'>
                  <AlertCircle className='h-4 w-4 mr-1' />
                  {createUnitError}
                </div>
              )}

              <div className='flex justify-end space-x-3'>
                {units.length > 0 && (
                  <button
                    onClick={() => {
                      setShowCreateUnit(false);
                      setSuggestedUnitDetails(null);
                      setCreateUnitError(null);
                    }}
                    className='px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50'
                  >
                    Cancel
                  </button>
                )}
                <button
                  onClick={createUnit}
                  disabled={
                    creatingUnit ||
                    !newUnitForm.title.trim() ||
                    !newUnitForm.code.trim()
                  }
                  className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center'
                >
                  {creatingUnit ? (
                    <>
                      <Loader2 className='h-4 w-4 mr-2 animate-spin' />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Plus className='h-4 w-4 mr-2' />
                      Create Unit
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Unit Selector Dropdown */
          <div className='space-y-2'>
            <select
              value={selectedUnit}
              onChange={e => setSelectedUnit(e.target.value)}
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            >
              <option value=''>Select a unit...</option>
              {units.map(unit => (
                <option key={unit.id} value={unit.id}>
                  {unit.title} ({unit.code})
                </option>
              ))}
            </select>
            <button
              onClick={() => setShowCreateUnit(true)}
              className='text-sm text-blue-600 hover:text-blue-800 flex items-center'
            >
              <Plus className='h-4 w-4 mr-1' />
              Create new unit
            </button>
          </div>
        )}
      </div>

      {/* Upload Area */}
      <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className='h-12 w-12 text-gray-400 mx-auto mb-4' />
          {isDragActive ? (
            <p className='text-lg text-blue-600'>Drop the files here...</p>
          ) : (
            <>
              <p className='text-lg text-gray-700 mb-2'>
                Drag & drop files here, or click to select
              </p>
              <p className='text-sm text-gray-500'>
                Supported formats: PDF, PPTX, DOCX, MD, TXT, HTML, ZIP
              </p>
              {units.length === 0 && (
                <p className='text-sm text-blue-600 mt-2'>
                  Drop a ZIP file to auto-detect unit details
                </p>
              )}
            </>
          )}
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
          <h3 className='text-lg font-semibold mb-4'>Files to Import</h3>

          <div className='space-y-3'>
            {files.map(file => (
              <div
                key={file.id}
                className='flex items-center justify-between p-3 border border-gray-200 rounded-lg'
              >
                <div className='flex items-center space-x-3'>
                  {file.status === 'completed' ? (
                    <CheckCircle className='h-5 w-5 text-green-600' />
                  ) : file.status === 'error' ? (
                    <AlertCircle className='h-5 w-5 text-red-600' />
                  ) : file.status === 'uploading' ||
                    file.status === 'processing' ? (
                    <Loader2 className='h-5 w-5 text-blue-600 animate-spin' />
                  ) : (
                    getFileIcon(file.type)
                  )}

                  <div>
                    <p className='font-medium text-gray-900'>{file.name}</p>
                    <p className='text-sm text-gray-500'>
                      {formatFileSize(file.size)}
                      {file.status === 'uploading' && ` - ${file.progress}%`}
                      {file.status === 'processing' && ' - Processing...'}
                      {file.status === 'completed' && ' - Ready'}
                      {file.error && ` - ${file.error}`}
                    </p>
                  </div>
                </div>

                <div className='flex items-center space-x-2'>
                  {(file.status === 'uploading' ||
                    file.status === 'processing') && (
                    <div className='w-32'>
                      <div className='w-full bg-gray-200 rounded-full h-2'>
                        <div
                          className='bg-blue-600 h-2 rounded-full transition-all'
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  <button
                    onClick={() => removeFile(file.id)}
                    className='p-1 text-gray-400 hover:text-red-600'
                    disabled={
                      file.status === 'uploading' ||
                      file.status === 'processing'
                    }
                  >
                    <X className='h-4 w-4' />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className='mt-6 flex justify-between'>
            <button
              onClick={() => setFiles([])}
              className='px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200'
            >
              Clear All
            </button>

            <div className='flex items-center space-x-3'>
              <button
                onClick={() => navigate('/units')}
                className='px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200'
              >
                Cancel
              </button>
              <button
                onClick={uploadFiles}
                disabled={!canImport}
                className='px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center'
              >
                {uploading ? (
                  <>
                    <Loader2 className='h-4 w-4 mr-2 animate-spin' />
                    Processing...
                  </>
                ) : (
                  <>
                    <Upload className='h-4 w-4 mr-2' />
                    Import Materials
                  </>
                )}
              </button>
            </div>
          </div>

          {!selectedUnit && hasPendingFiles && !showCreateUnit && (
            <p className='mt-3 text-sm text-amber-600 flex items-center'>
              <AlertCircle className='h-4 w-4 mr-1' />
              Please select or create a unit before importing
            </p>
          )}
        </div>
      )}

      {/* Import Results */}
      {files.some(f => f.status === 'completed' && f.result) && (
        <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
          <div className='flex items-center justify-between mb-4'>
            <h3 className='text-lg font-semibold'>Import Analysis</h3>
            {selectedUnit &&
              files.some(
                f =>
                  f.status === 'completed' &&
                  f.result?.content_id &&
                  !enhancedFiles.has(f.id)
              ) && (
                <button
                  onClick={handleEnhanceAll}
                  disabled={batchEnhancing || enhancingFiles.size > 0}
                  className='px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center text-sm'
                >
                  {batchEnhancing ? (
                    <>
                      <Loader2 className='h-4 w-4 mr-2 animate-spin' />
                      Enhancing {batchEnhanceProgress.current} of{' '}
                      {batchEnhanceProgress.total}...
                    </>
                  ) : (
                    <>
                      <Sparkles className='h-4 w-4 mr-2' />
                      Enhance All with AI
                    </>
                  )}
                </button>
              )}
          </div>

          {files
            .filter(f => f.status === 'completed' && f.result)
            .map(file => (
              <div
                key={file.id}
                className='mb-6 p-4 border border-gray-200 rounded-lg'
              >
                <h4 className='font-medium text-gray-900 mb-3'>{file.name}</h4>

                {file.result && (
                  <div className='space-y-3'>
                    {/* Content Type & Stats */}
                    <div className='space-y-3'>
                      <div className='grid grid-cols-4 gap-4 text-sm'>
                        <div>
                          <span className='text-gray-600'>Detected Type:</span>
                          <div className='flex items-center mt-1'>
                            <select
                              className='text-sm font-medium capitalize border border-gray-300 rounded px-2 py-1'
                              value={file.result.content_type}
                              onChange={async e => {
                                const newType = e.target.value;
                                try {
                                  await api.patch(
                                    `/content/${file.result?.content_id}/type?new_type=${newType}`
                                  );
                                  // Update local state
                                  setFiles(prev =>
                                    prev.map(f =>
                                      f.id === file.id
                                        ? {
                                            ...f,
                                            result: {
                                              ...f.result,
                                              content_type: newType,
                                            },
                                          }
                                        : f
                                    )
                                  );
                                } catch (error) {
                                  console.error(
                                    'Failed to update content type:',
                                    error
                                  );
                                }
                              }}
                            >
                              <option value='general'>General Content</option>
                              <option value='lecture'>Lecture</option>
                              <option value='quiz'>Quiz/Assessment</option>
                              <option value='worksheet'>
                                Worksheet/Exercise
                              </option>
                              <option value='lab'>Lab/Practical</option>
                              <option value='case_study'>Case Study</option>
                              <option value='interactive'>
                                Interactive Content
                              </option>
                              <option value='presentation'>Presentation</option>
                              <option value='reading'>Reading Material</option>
                              <option value='video_script'>Video/Media</option>
                            </select>
                            {file.result.content_type_confidence !==
                              undefined && (
                              <span
                                className={`ml-2 text-xs px-2 py-1 rounded ${
                                  file.result.content_type_confidence > 0.7
                                    ? 'bg-green-100 text-green-700'
                                    : file.result.content_type_confidence > 0.4
                                      ? 'bg-yellow-100 text-yellow-700'
                                      : 'bg-red-100 text-red-700'
                                }`}
                              >
                                {Math.round(
                                  file.result.content_type_confidence * 100
                                )}
                                % confidence
                              </span>
                            )}
                          </div>
                        </div>
                        <div>
                          <span className='text-gray-600'>Week:</span>
                          <div className='flex items-center mt-1'>
                            <select
                              className='text-sm font-medium border border-gray-300 rounded px-2 py-1'
                              value={file.result.week_number || ''}
                              onChange={async e => {
                                const newWeek =
                                  e.target.value === ''
                                    ? null
                                    : parseInt(e.target.value);
                                if (file.result?.content_id) {
                                  const success = await updateWeekAssignment(
                                    file.result.content_id,
                                    newWeek
                                  );
                                  if (success) {
                                    // Update local state
                                    setFiles(prev =>
                                      prev.map(f =>
                                        f.id === file.id
                                          ? {
                                              ...f,
                                              result: {
                                                ...f.result,
                                                week_number: newWeek,
                                              },
                                            }
                                          : f
                                      )
                                    );
                                  }
                                }
                              }}
                            >
                              <option value=''>Unassigned</option>
                              {Array.from({ length: 52 }, (_, i) => i + 1).map(
                                week => (
                                  <option key={week} value={week}>
                                    Week {week}
                                  </option>
                                )
                              )}
                            </select>
                            {file.result.content_id && (
                              <button
                                onClick={() =>
                                  toggleWeekAssignment(
                                    file.result!.content_id!,
                                    file.result!.week_number ?? null
                                  )
                                }
                                className='ml-2 text-blue-600 hover:text-blue-800'
                              >
                                {weekAssignments.some(
                                  a => a.content_id === file.result?.content_id
                                ) ? (
                                  <CheckSquare className='h-4 w-4' />
                                ) : (
                                  <Square className='h-4 w-4' />
                                )}
                              </button>
                            )}
                          </div>
                        </div>
                        <div>
                          <span className='text-gray-600'>Words:</span>
                          <span className='ml-2 font-medium'>
                            {file.result.wordCount}
                          </span>
                        </div>
                        <div>
                          <span className='text-gray-600'>Sections:</span>
                          <span className='ml-2 font-medium'>
                            {file.result.sections_found}
                          </span>
                        </div>
                      </div>

                      {/* Show alternative types if confidence is low */}
                      {file.result.content_type_confidence !== undefined &&
                        file.result.content_type_confidence < 0.7 &&
                        file.result.categorization?.alternative_types &&
                        file.result.categorization.alternative_types.length >
                          0 && (
                          <div className='bg-gray-50 p-2 rounded text-sm'>
                            <span className='text-gray-600'>
                              Could also be:{' '}
                            </span>
                            {file.result.categorization.alternative_types.map(
                              (type: string, idx: number) => (
                                <button
                                  key={type}
                                  className='ml-2 text-blue-600 hover:underline capitalize'
                                  onClick={async () => {
                                    try {
                                      await api.patch(
                                        `/content/${file.result?.content_id}/type?new_type=${type}`
                                      );
                                      setFiles(prev =>
                                        prev.map(f =>
                                          f.id === file.id
                                            ? {
                                                ...f,
                                                result: {
                                                  ...f.result,
                                                  content_type: type,
                                                },
                                              }
                                            : f
                                        )
                                      );
                                    } catch (error) {
                                      console.error(
                                        'Failed to update content type:',
                                        error
                                      );
                                    }
                                  }}
                                >
                                  {type}
                                  {idx <
                                  (file.result?.categorization
                                    ?.alternative_types?.length ?? 0) -
                                    1
                                    ? ','
                                    : ''}
                                </button>
                              )
                            )}
                          </div>
                        )}
                    </div>

                    {/* Categorization */}
                    {file.result.categorization && (
                      <div className='bg-blue-50 p-3 rounded'>
                        <p className='text-sm font-medium text-blue-900 mb-1'>
                          Categorization
                        </p>
                        <div className='text-sm text-blue-800'>
                          <span>
                            Difficulty:{' '}
                            {file.result.categorization.difficultyLevel}
                          </span>
                          <span className='mx-2'>-</span>
                          <span>
                            Duration:{' '}
                            {file.result.categorization.estimatedDuration} min
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Suggestions */}
                    {file.result.suggestions &&
                      file.result.suggestions.length > 0 && (
                        <div className='bg-yellow-50 p-3 rounded'>
                          <p className='text-sm font-medium text-yellow-900 mb-2'>
                            Enhancement Suggestions
                          </p>
                          <ul className='text-sm text-yellow-800 space-y-1'>
                            {file.result.suggestions
                              .slice(0, 3)
                              .map((suggestion: string, idx: number) => (
                                <li key={idx} className='flex items-start'>
                                  <span className='mr-2'>-</span>
                                  <span>{suggestion}</span>
                                </li>
                              ))}
                          </ul>
                        </div>
                      )}

                    {/* Gaps */}
                    {file.result.gaps && file.result.gaps.length > 0 && (
                      <div className='bg-red-50 p-3 rounded'>
                        <p className='text-sm font-medium text-red-900 mb-2'>
                          Content Gaps
                        </p>
                        <ul className='text-sm text-red-800 space-y-1'>
                          {file.result.gaps
                            .filter(g => g.severity === 'high')
                            .slice(0, 3)
                            .map((gap, idx: number) => (
                              <li key={idx} className='flex items-start'>
                                <AlertCircle className='h-4 w-4 mr-2 mt-0.5 flex-shrink-0' />
                                <span>
                                  {gap.element}: {gap.suggestion}
                                </span>
                              </li>
                            ))}
                        </ul>
                      </div>
                    )}

                    {/* Action Buttons */}
                    {file.result.content_id && selectedUnit && (
                      <div className='flex space-x-2 mt-3'>
                        <button
                          className={`px-3 py-1 text-sm rounded flex items-center ${
                            enhancedFiles.has(file.id)
                              ? 'bg-green-600 text-white'
                              : 'bg-blue-600 text-white hover:bg-blue-700'
                          }`}
                          disabled={
                            enhancingFiles.has(file.id) ||
                            enhancedFiles.has(file.id)
                          }
                          onClick={() => handleEnhanceImported(file)}
                        >
                          {enhancingFiles.has(file.id) ? (
                            <>
                              <Loader2 className='h-3.5 w-3.5 mr-1.5 animate-spin' />
                              Enhancing...
                            </>
                          ) : enhancedFiles.has(file.id) ? (
                            <>
                              <CheckCircle className='h-3.5 w-3.5 mr-1.5' />
                              Enhanced
                            </>
                          ) : (
                            <>
                              <Sparkles className='h-3.5 w-3.5 mr-1.5' />
                              Enhance with AI
                            </>
                          )}
                        </button>
                        <button
                          className='px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700'
                          onClick={() => {
                            navigate(
                              `/units/${selectedUnit}/content/${file.result?.content_id}/edit`
                            );
                          }}
                        >
                          Edit Content
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
        </div>
      )}

      {/* Bulk Week Assignment */}
      {weekAssignments.length > 0 && (
        <div className='bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6'>
          <h3 className='text-lg font-semibold mb-2 text-yellow-900'>
            Bulk Week Assignment ({weekAssignments.length} selected)
          </h3>
          <div className='flex items-center space-x-4'>
            <div className='flex-1'>
              <label className='block text-sm font-medium text-yellow-800 mb-1'>
                Assign all selected to week:
              </label>
              <div className='flex items-center space-x-2'>
                <select
                  className='text-sm font-medium border border-gray-300 rounded px-3 py-2'
                  value={bulkWeek}
                  onChange={e =>
                    setBulkWeek(
                      e.target.value === '' ? '' : parseInt(e.target.value)
                    )
                  }
                >
                  <option value=''>Select week...</option>
                  {Array.from({ length: 52 }, (_, i) => i + 1).map(week => (
                    <option key={week} value={week}>
                      Week {week}
                    </option>
                  ))}
                </select>
                <button
                  onClick={bulkUpdateWeeks}
                  disabled={!bulkWeek}
                  className='px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed'
                >
                  Apply
                </button>
                <button
                  onClick={() => setWeekAssignments([])}
                  className='px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300'
                >
                  Clear Selection
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Unassigned Content Management */}
      {selectedUnit && (
        <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
          <div className='flex justify-between items-center mb-4'>
            <h3 className='text-lg font-semibold'>Unassigned Content</h3>
            <button
              onClick={() => setShowUnassigned(!showUnassigned)}
              className='px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200'
            >
              {showUnassigned ? 'Hide' : 'Show'} ({unassignedContent.length})
            </button>
          </div>

          {showUnassigned && (
            <>
              {loadingUnassigned ? (
                <div className='text-center py-4'>
                  <div className='inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-blue-600 border-r-transparent'></div>
                  <p className='mt-2 text-gray-600'>
                    Loading unassigned content...
                  </p>
                </div>
              ) : unassignedContent.length === 0 ? (
                <div className='text-center py-4 text-gray-500'>
                  No unassigned content found.
                </div>
              ) : (
                <div className='space-y-3'>
                  <div className='text-sm text-gray-600 mb-2'>
                    {unassignedContent.length} item(s) without week assignment
                  </div>
                  <div className='max-h-60 overflow-y-auto'>
                    {unassignedContent.map(item => (
                      <div
                        key={item.id}
                        className='flex items-center justify-between p-3 border border-gray-200 rounded-lg'
                      >
                        <div>
                          <div className='font-medium'>{item.title}</div>
                          <div className='text-sm text-gray-500 capitalize'>
                            {item.content_type}
                          </div>
                        </div>
                        <div className='flex items-center space-x-2'>
                          <select
                            className='text-sm border border-gray-300 rounded px-2 py-1'
                            defaultValue=''
                            onChange={async e => {
                              const weekNumber =
                                e.target.value === ''
                                  ? null
                                  : parseInt(e.target.value);
                              const success = await updateWeekAssignment(
                                item.id,
                                weekNumber
                              );
                              if (success && weekNumber !== null) {
                                // Remove from unassigned list
                                setUnassignedContent(prev =>
                                  prev.filter(i => i.id !== item.id)
                                );
                              }
                            }}
                          >
                            <option value=''>Assign to week...</option>
                            {Array.from({ length: 52 }, (_, i) => i + 1).map(
                              week => (
                                <option key={week} value={week}>
                                  Week {week}
                                </option>
                              )
                            )}
                          </select>
                          <button
                            onClick={() =>
                              navigate(
                                `/units/${selectedUnit}/content/${item.id}/edit`
                              )
                            }
                            className='px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200'
                          >
                            Edit
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Import Options */}
      <div className='bg-white rounded-lg shadow-md p-6'>
        <h3 className='text-lg font-semibold mb-4'>Import Options</h3>

        <div className='space-y-3'>
          <label className='flex items-center'>
            <input
              type='checkbox'
              className='mr-3 h-4 w-4 text-blue-600 rounded border-gray-300'
              defaultChecked
            />
            <span>
              Automatically categorize content (Lecture, Quiz, Worksheet, etc.)
            </span>
          </label>

          <label className='flex items-center'>
            <input
              type='checkbox'
              className='mr-3 h-4 w-4 text-blue-600 rounded border-gray-300'
              defaultChecked
            />
            <span>Run quality validation on imported content</span>
          </label>

          <label className='flex items-center'>
            <input
              type='checkbox'
              className='mr-3 h-4 w-4 text-blue-600 rounded border-gray-300'
            />
            <span>Enhance content with AI after import</span>
          </label>

          <label className='flex items-center'>
            <input
              type='checkbox'
              className='mr-3 h-4 w-4 text-blue-600 rounded border-gray-300'
            />
            <span>Generate learning designs from imported materials</span>
          </label>
        </div>
      </div>
    </div>
  );
};

export default ImportMaterials;
