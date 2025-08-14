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
} from 'lucide-react';
import api from '../../services/api';
import { useNavigate } from 'react-router-dom';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  error?: string;
  result?: any;
  file?: File;
}

// Content type descriptions (currently unused but may be useful for UI)
// const contentTypeInfo = {
//   general: {
//     name: 'General Content',
//     description: 'Unspecified educational material',
//     icon: '📄',
//   },
//   lecture: {
//     name: 'Lecture',
//     description: 'Teaching material for direct instruction',
//     icon: '📚',
//   },
//   quiz: {
//     name: 'Quiz/Assessment',
//     description: 'Tests, quizzes, or evaluations',
//     icon: '📝',
//   },
//   worksheet: {
//     name: 'Worksheet',
//     description: 'Practice problems and exercises',
//     icon: '✏️',
//   },
//   lab: {
//     name: 'Lab/Practical',
//     description: 'Hands-on experiments or activities',
//     icon: '🔬',
//   },
//   case_study: {
//     name: 'Case Study',
//     description: 'Real-world scenarios for analysis',
//     icon: '💼',
//   },
//   interactive: {
//     name: 'Interactive Content',
//     description: 'Games, simulations, or interactive HTML',
//     icon: '🎮',
//   },
//   presentation: {
//     name: 'Presentation',
//     description: 'Slides or presentation materials',
//     icon: '🎯',
//   },
//   reading: {
//     name: 'Reading Material',
//     description: 'Articles, papers, or textbook content',
//     icon: '📖',
//   },
//   video_script: {
//     name: 'Video/Media',
//     description: 'Video transcripts or multimedia content',
//     icon: '🎥',
//   },
// };

const ImportMaterials = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [courses, setCourses] = useState<any[]>([]);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const response = await api.get('/courses');
      setCourses(response.data);
    } catch (error) {
      console.error('Error fetching courses:', error);
    }
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map(
      file =>
        ({
          id: Math.random().toString(36).substr(2, 9),
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'pending' as const,
          progress: 0,
          file: file, // Store the actual File object
        }) as any
    );
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.ms-powerpoint': ['.ppt'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation':
        ['.pptx'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        ['.docx'],
      'text/markdown': ['.md'],
      'text/plain': ['.txt'],
    },
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

  const uploadFiles = async () => {
    if (!selectedCourse) {
      window.alert('Please select a course first');
      return;
    }

    setUploading(true);
    const pendingFiles = files.filter(f => f.status === 'pending');

    // Create FormData for batch upload
    const formData = new FormData();
    const fileMap = new Map();

    for (const fileInfo of pendingFiles) {
      // Get the actual File object from the dropzone
      const actualFile = (fileInfo as any).file;
      if (actualFile) {
        formData.append('files', actualFile);
        fileMap.set(actualFile.name, fileInfo.id);
      }
    }

    if (pendingFiles.length === 1) {
      // Single file upload
      const fileInfo = pendingFiles[0];
      const actualFile = (fileInfo as any).file;

      if (actualFile) {
        setFiles(prev =>
          prev.map(f =>
            f.id === fileInfo.id
              ? { ...f, status: 'uploading', progress: 50 }
              : f
          )
        );

        const formData = new FormData();
        formData.append('file', actualFile);

        try {
          const response = await api.post(
            `/content/upload?unit_id=${selectedCourse}`,
            formData,
            {
              headers: { 'Content-Type': 'multipart/form-data' },
              onUploadProgress: progressEvent => {
                const progress = progressEvent.total
                  ? Math.round(
                      (progressEvent.loaded * 100) / progressEvent.total
                    )
                  : 0;
                setFiles(prev =>
                  prev.map(f => (f.id === fileInfo.id ? { ...f, progress } : f))
                );
              },
            }
          );

          // Mark as processing
          setFiles(prev =>
            prev.map(f =>
              f.id === fileInfo.id ? { ...f, status: 'processing' } : f
            )
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
        } catch (error: any) {
          console.error('Upload error:', error);
          setFiles(prev =>
            prev.map(f =>
              f.id === fileInfo.id
                ? {
                    ...f,
                    status: 'error',
                    error:
                      'Upload failed: ' +
                      (error.response?.data?.detail || error.message),
                  }
                : f
            )
          );
        }
      }
    } else if (pendingFiles.length > 1) {
      // Batch upload
      try {
        const response = await api.post(
          `/content/upload/batch?unit_id=${selectedCourse}`,
          formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' },
          }
        );

        // Update file statuses based on response
        response.data.results.forEach((result: any) => {
          const fileId = fileMap.get(result.filename);
          if (fileId) {
            setFiles(prev =>
              prev.map(f =>
                f.id === fileId
                  ? {
                      ...f,
                      status: result.success ? 'completed' : 'error',
                      progress: 100,
                      error: result.error,
                      result: result,
                    }
                  : f
              )
            );
          }
        });
      } catch (error: unknown) {
        // Mark all as error
        console.error('Batch upload error:', error);
        pendingFiles.forEach(fileInfo => {
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
    }

    setUploading(false);
  };

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  return (
    <div className='p-6 max-w-6xl mx-auto'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>
          Import Materials
        </h1>
        <p className='text-gray-600'>
          Upload and import existing course materials for enhancement
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
              &quot;Quiz 1&quot; → Quiz, &quot;Lab Exercise&quot; → Lab). You
              can change the type using the dropdown if the detection is
              incorrect. Creative formats like interactive HTML will be detected
              and properly categorized.
            </p>
          </div>
        </div>
      </div>

      {/* Course Selection */}
      <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
        <label className='block text-sm font-medium text-gray-700 mb-2'>
          Select Target Course *
        </label>
        <select
          value={selectedCourse}
          onChange={e => setSelectedCourse(e.target.value)}
          className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        >
          <option value=''>Select a course...</option>
          {courses.map(course => (
            <option key={course.id} value={course.id}>
              {course.title} ({course.code})
            </option>
          ))}
        </select>
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
                Supported formats: PDF, PPT, PPTX, DOC, DOCX, MD, TXT
              </p>
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
                      {file.status === 'uploading' && ` • ${file.progress}%`}
                      {file.status === 'processing' && ' • Processing...'}
                      {file.status === 'completed' && ' • Ready'}
                      {file.error && ` • ${file.error}`}
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

            <div className='space-x-3'>
              <button
                onClick={() => navigate('/courses')}
                className='px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200'
              >
                Cancel
              </button>
              <button
                onClick={uploadFiles}
                disabled={uploading || files.length === 0 || !selectedCourse}
                className='px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center'
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
        </div>
      )}

      {/* Import Results */}
      {files.some(f => f.status === 'completed' && f.result) && (
        <div className='bg-white rounded-lg shadow-md p-6 mb-6'>
          <h3 className='text-lg font-semibold mb-4'>Import Analysis</h3>

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
                      <div className='grid grid-cols-3 gap-4 text-sm'>
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
                                    `/content/${file.result.content_id}/type?new_type=${newType}`
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
                          <span className='text-gray-600'>Words:</span>
                          <span className='ml-2 font-medium'>
                            {file.result.word_count}
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
                      {file.result.content_type_confidence < 0.7 &&
                        file.result.categorization?.alternative_types?.length >
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
                                        `/content/${file.result.content_id}/type?new_type=${type}`
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
                                  file.result.categorization.alternative_types
                                    .length -
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
                            {file.result.categorization.difficulty_level}
                          </span>
                          <span className='mx-2'>•</span>
                          <span>
                            Duration:{' '}
                            {file.result.categorization.estimated_duration} min
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
                                  <span className='mr-2'>•</span>
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
                            .filter((g: any) => g.severity === 'high')
                            .slice(0, 3)
                            .map((gap: any, idx: number) => (
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
                    <div className='flex space-x-2 mt-3'>
                      <button
                        className='px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700'
                        onClick={() => {
                          // Navigate to enhance content
                          navigate(
                            `/content/${file.result.content_id}/enhance`
                          );
                        }}
                      >
                        Enhance with AI
                      </button>
                      <button
                        className='px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700'
                        onClick={() => {
                          // Navigate to edit content
                          navigate(`/content/${file.result.content_id}/edit`);
                        }}
                      >
                        Edit Content
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
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
            <span>Generate LRDs from imported materials</span>
          </label>
        </div>
      </div>
    </div>
  );
};

export default ImportMaterials;
