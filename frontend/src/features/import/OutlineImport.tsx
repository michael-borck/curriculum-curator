import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  FileText,
  Loader2,
  AlertCircle,
  ArrowLeft,
  ChevronDown,
} from 'lucide-react';
import {
  listParsers,
  parseOutline,
  applyOutline,
  type ParserInfo,
  type OutlineParseResponse,
  type OutlineApplyRequest,
} from '../../services/outlineImportApi';
import { OutlineReviewForm } from './OutlineReviewForm';

type Phase = 'upload' | 'parsing' | 'review' | 'applying' | 'done' | 'error';

const ALLOWED_EXTENSIONS = ['pdf', 'docx', 'txt', 'md'];

const OutlineImport: React.FC = () => {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>('upload');
  const [parsers, setParsers] = useState<ParserInfo[]>([]);
  const [selectedParser, setSelectedParser] = useState('generic');
  const [file, setFile] = useState<File | null>(null);
  const [parseResult, setParseResult] = useState<OutlineParseResponse | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  // Load available parsers on mount
  useEffect(() => {
    listParsers()
      .then(setParsers)
      .catch(() => {
        // Fallback if endpoint not available yet
        setParsers([
          {
            id: 'generic',
            displayName: 'Generic (AI-Powered)',
            description: 'Works with any institution or format',
            supportedFormats: ['pdf', 'docx', 'txt'],
          },
        ]);
      });
  }, []);

  const validateFile = useCallback((f: File): string | null => {
    const ext = f.name.split('.').pop()?.toLowerCase() || '';
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported file type: .${ext}. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`;
    }
    if (f.size > 20 * 1024 * 1024) {
      return 'File too large. Maximum is 20MB.';
    }
    return null;
  }, []);

  const handleFileSelect = useCallback(
    (f: File) => {
      const err = validateFile(f);
      if (err) {
        setError(err);
        return;
      }
      setFile(f);
      setError(null);
    },
    [validateFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) handleFileSelect(droppedFile);
    },
    [handleFileSelect]
  );

  const handleParse = async () => {
    if (!file) return;
    setPhase('parsing');
    setError(null);

    try {
      const result = await parseOutline(file, selectedParser);
      setParseResult(result);
      setPhase('review');
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Failed to parse document.');
      setPhase('error');
    }
  };

  const handleApply = async (request: OutlineApplyRequest) => {
    setPhase('applying');
    setError(null);

    try {
      const result = await applyOutline(request);
      setPhase('done');
      // Navigate to the new unit
      navigate(`/units/${result.unitId}`);
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Failed to create unit.');
      setPhase('review'); // Go back to review so user can fix
    }
  };

  const handleReset = () => {
    setPhase('upload');
    setFile(null);
    setParseResult(null);
    setError(null);
  };

  return (
    <div className='max-w-4xl mx-auto px-4 py-8'>
      {/* Header */}
      <div className='mb-6'>
        <button
          onClick={() => navigate('/')}
          className='flex items-center text-gray-500 hover:text-gray-700 mb-4'
        >
          <ArrowLeft className='h-4 w-4 mr-1' />
          Back to Portfolio
        </button>
        <h1 className='text-2xl font-bold text-gray-900'>
          Create from Unit Outline
        </h1>
        <p className='text-gray-600 mt-1'>
          Upload a unit outline document and the system will extract the
          structure for you to review.
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div className='mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3'>
          <AlertCircle className='h-5 w-5 text-red-500 flex-shrink-0 mt-0.5' />
          <div>
            <p className='text-red-800 text-sm'>{error}</p>
            {phase === 'error' && (
              <button
                onClick={handleReset}
                className='text-sm text-red-600 underline mt-1'
              >
                Try again
              </button>
            )}
          </div>
        </div>
      )}

      {/* Upload phase */}
      {(phase === 'upload' || phase === 'error') && (
        <div className='space-y-6'>
          {/* Parser selector */}
          {parsers.length > 1 && (
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Parser
              </label>
              <div className='relative'>
                <select
                  value={selectedParser}
                  onChange={e => setSelectedParser(e.target.value)}
                  className='w-full rounded-lg border border-gray-300 px-3 py-2 pr-8 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-purple-500 appearance-none'
                >
                  {parsers.map(p => (
                    <option key={p.id} value={p.id}>
                      {p.displayName}
                    </option>
                  ))}
                </select>
                <ChevronDown className='h-4 w-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none' />
              </div>
              {parsers.find(p => p.id === selectedParser)?.description && (
                <p className='text-xs text-gray-500 mt-1'>
                  {parsers.find(p => p.id === selectedParser)?.description}
                </p>
              )}
            </div>
          )}

          {/* Drop zone */}
          <div
            onDragOver={e => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-12 text-center transition ${
              dragOver
                ? 'border-purple-400 bg-purple-50'
                : file
                  ? 'border-green-300 bg-green-50'
                  : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            {file ? (
              <div className='space-y-3'>
                <FileText className='h-12 w-12 text-green-500 mx-auto' />
                <div>
                  <p className='font-medium text-gray-900'>{file.name}</p>
                  <p className='text-sm text-gray-500'>
                    {(file.size / 1024).toFixed(0)} KB
                  </p>
                </div>
                <button
                  onClick={() => {
                    setFile(null);
                    setError(null);
                  }}
                  className='text-sm text-gray-500 underline'
                >
                  Remove
                </button>
              </div>
            ) : (
              <div className='space-y-3'>
                <Upload className='h-12 w-12 text-gray-400 mx-auto' />
                <div>
                  <p className='text-gray-700'>
                    Drag and drop your unit outline here, or{' '}
                    <label className='text-purple-600 hover:text-purple-700 cursor-pointer underline'>
                      browse
                      <input
                        type='file'
                        className='hidden'
                        accept='.pdf,.docx,.txt,.md'
                        onChange={e => {
                          const f = e.target.files?.[0];
                          if (f) handleFileSelect(f);
                        }}
                      />
                    </label>
                  </p>
                  <p className='text-sm text-gray-500 mt-1'>
                    Supported: PDF, DOCX, TXT (max 20MB)
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Parse button */}
          {file && (
            <div className='flex justify-end'>
              <button
                onClick={handleParse}
                className='px-6 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium text-sm transition'
              >
                Parse Document
              </button>
            </div>
          )}
        </div>
      )}

      {/* Parsing phase */}
      {phase === 'parsing' && (
        <div className='text-center py-16'>
          <Loader2 className='h-10 w-10 text-purple-500 mx-auto animate-spin' />
          <p className='text-gray-600 mt-4 font-medium'>
            Parsing your document...
          </p>
          <p className='text-gray-500 text-sm mt-1'>
            {selectedParser === 'generic'
              ? 'Using AI to extract structure — this may take a moment.'
              : 'Analysing document structure...'}
          </p>
        </div>
      )}

      {/* Review phase */}
      {phase === 'review' && parseResult && (
        <OutlineReviewForm
          parseResult={parseResult}
          onApply={handleApply}
          onBack={handleReset}
        />
      )}

      {/* Applying phase */}
      {phase === 'applying' && (
        <div className='text-center py-16'>
          <Loader2 className='h-10 w-10 text-purple-500 mx-auto animate-spin' />
          <p className='text-gray-600 mt-4 font-medium'>
            Creating your unit...
          </p>
        </div>
      )}
    </div>
  );
};

export default OutlineImport;
