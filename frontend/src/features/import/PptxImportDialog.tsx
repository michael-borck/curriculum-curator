import React, { useState, useCallback, useEffect } from 'react';
import {
  Upload,
  FileText,
  AlertCircle,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Modal, Button, FormInput, FormSelect } from '../../components/ui';
import {
  listMaterialParsers,
  previewSingleMaterial,
  applySingleMaterial,
  type ParserInfo,
  type MaterialPreviewResponse,
} from '../../services/materialImportApi';

/**
 * PptxImportDialog — Mode A (single PPTX → existing unit) frontend.
 *
 * Three-phase flow mirroring OutlineImport:
 *   upload → parsing → preview (review) → applying → done
 *
 * The user selects a .pptx file, the dialog calls /preview to parse it
 * without persisting, displays the result for review (parser used, title,
 * image count, warnings, content snippet), and on confirmation calls
 * /apply to create a WeeklyMaterial in the current week.
 *
 * Per the structured-import-plan, this is the foundation for Mode A.
 * Mode B (multi-file zip → existing unit) and Mode C (LMS package → new
 * unit) ship as separate UIs in later phases.
 */

interface PptxImportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  unitId: string;
  weekNumber: number;
  onImported: () => void;
}

type Phase = 'upload' | 'parsing' | 'preview' | 'applying';

const ALLOWED_EXTENSIONS = ['pptx'];
const MAX_FILE_SIZE_MB = 50;

const CATEGORY_OPTIONS = [
  { value: 'general', label: 'General' },
  { value: 'pre_class', label: 'Pre-class' },
  { value: 'in_class', label: 'In-class' },
  { value: 'post_class', label: 'Post-class' },
  { value: 'resources', label: 'Resources' },
];

const TYPE_OPTIONS = [
  { value: 'lecture', label: 'Lecture' },
  { value: 'tutorial', label: 'Tutorial' },
  { value: 'lab', label: 'Lab' },
  { value: 'workshop', label: 'Workshop' },
  { value: 'seminar', label: 'Seminar' },
  { value: 'reading', label: 'Reading' },
];

const PptxImportDialog: React.FC<PptxImportDialogProps> = ({
  isOpen,
  onClose,
  unitId,
  weekNumber,
  onImported,
}) => {
  const [phase, setPhase] = useState<Phase>('upload');
  const [parsers, setParsers] = useState<ParserInfo[]>([]);
  const [selectedParser, setSelectedParser] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<MaterialPreviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  // Form fields the user can adjust before applying
  const [titleOverride, setTitleOverride] = useState('');
  const [materialType, setMaterialType] = useState('lecture');
  const [category, setCategory] = useState('general');

  // Load registered parsers when the dialog opens
  useEffect(() => {
    if (!isOpen) return;
    listMaterialParsers('pptx')
      .then(p => {
        setParsers(p);
        const defaultParser = p.find(x => x.isDefault) || p[0];
        if (defaultParser) {
          setSelectedParser(defaultParser.id);
        }
      })
      .catch(() => {
        // Soft fallback so the dialog still works if /parsers errors —
        // the apply endpoint will use its own default
        setParsers([]);
      });
  }, [isOpen]);

  // Reset all state when the dialog closes so reopening starts fresh
  const handleClose = useCallback(() => {
    setPhase('upload');
    setFile(null);
    setPreview(null);
    setError(null);
    setTitleOverride('');
    setMaterialType('lecture');
    setCategory('general');
    setDragOver(false);
    onClose();
  }, [onClose]);

  const validateFile = useCallback((f: File): string | null => {
    const ext = f.name.split('.').pop()?.toLowerCase() || '';
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported file type: .${ext}. This phase supports PowerPoint (.pptx) only.`;
    }
    const maxBytes = MAX_FILE_SIZE_MB * 1024 * 1024;
    if (f.size > maxBytes) {
      return `File too large. Maximum is ${MAX_FILE_SIZE_MB} MB.`;
    }
    return null;
  }, []);

  const handleFileSelect = useCallback(
    (f: File) => {
      const err = validateFile(f);
      if (err) {
        setError(err);
        setFile(null);
        return;
      }
      setError(null);
      setFile(f);
    },
    [validateFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const dropped = e.dataTransfer.files[0];
      if (dropped) handleFileSelect(dropped);
    },
    [handleFileSelect]
  );

  const handlePreview = async () => {
    if (!file) return;
    setPhase('parsing');
    setError(null);
    try {
      const result = await previewSingleMaterial(
        file,
        unitId,
        selectedParser || undefined
      );
      setPreview(result);
      setTitleOverride(result.title);
      setPhase('preview');
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(
        e.response?.data?.detail ||
          'Failed to parse the file. Please check it is a valid PowerPoint document.'
      );
      setPhase('upload');
    }
  };

  const handleApply = async () => {
    if (!file) return;
    setPhase('applying');
    setError(null);
    try {
      const result = await applySingleMaterial({
        file,
        unitId,
        weekNumber,
        parserId: selectedParser || undefined,
        titleOverride: titleOverride.trim() || undefined,
        category,
        type: materialType,
      });
      toast.success(`Imported "${result.title}" into Week ${weekNumber}`);
      onImported();
      handleClose();
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(
        e.response?.data?.detail ||
          'Failed to import the file. Please try again.'
      );
      setPhase('preview');
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title='Import PowerPoint'
      size='2xl'
      closeOnBackdrop={phase === 'upload'}
    >
      <div className='space-y-4'>
        {/* Persistent week-context note */}
        <div className='text-sm text-gray-600'>
          Importing into <span className='font-medium'>Week {weekNumber}</span>.
          Slide structure, bullet points, tables, images, and speaker notes will
          be preserved as editable content.
        </div>

        {/* Error banner */}
        {error && (
          <div className='bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2'>
            <AlertCircle className='h-5 w-5 text-red-500 flex-shrink-0 mt-0.5' />
            <p className='text-red-800 text-sm'>{error}</p>
          </div>
        )}

        {/* ─── Upload phase ─────────────────────────────── */}
        {phase === 'upload' && (
          <div className='space-y-4'>
            {parsers.length > 1 && (
              <FormSelect
                label='Parser'
                value={selectedParser}
                onChange={e => setSelectedParser(e.target.value)}
                options={parsers.map(p => ({
                  value: p.id,
                  label: p.isDefault
                    ? `${p.displayName} (default)`
                    : p.displayName,
                }))}
                hint={
                  parsers.find(p => p.id === selectedParser)?.description || ''
                }
              />
            )}

            {/* Drop zone */}
            <div
              onDragOver={e => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
                dragOver
                  ? 'border-blue-400 bg-blue-50'
                  : file
                    ? 'border-green-300 bg-green-50'
                    : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              {file ? (
                <div className='space-y-2'>
                  <FileText className='h-10 w-10 text-green-500 mx-auto' />
                  <p className='font-medium text-gray-900'>{file.name}</p>
                  <p className='text-sm text-gray-500'>
                    {(file.size / 1024).toFixed(0)} KB
                  </p>
                  <button
                    type='button'
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
                <div className='space-y-2'>
                  <Upload className='h-10 w-10 text-gray-400 mx-auto' />
                  <p className='text-gray-700 text-sm'>
                    Drag and drop a .pptx file here, or{' '}
                    <label className='text-blue-600 hover:text-blue-700 cursor-pointer underline'>
                      browse
                      <input
                        type='file'
                        className='hidden'
                        accept='.pptx'
                        onChange={e => {
                          const f = e.target.files?.[0];
                          if (f) handleFileSelect(f);
                        }}
                      />
                    </label>
                  </p>
                  <p className='text-xs text-gray-500'>
                    PowerPoint (.pptx) only — max {MAX_FILE_SIZE_MB} MB
                  </p>
                </div>
              )}
            </div>

            <div className='flex justify-end gap-2'>
              <Button variant='outline' onClick={handleClose}>
                Cancel
              </Button>
              <Button
                variant='primary'
                onClick={handlePreview}
                disabled={!file}
              >
                Preview Import
              </Button>
            </div>
          </div>
        )}

        {/* ─── Parsing phase ────────────────────────────── */}
        {phase === 'parsing' && (
          <div className='py-12 text-center'>
            <Button loading variant='ghost' size='lg' disabled>
              Parsing PowerPoint...
            </Button>
            <p className='text-sm text-gray-500 mt-2'>
              Extracting slides, text, images, and speaker notes.
            </p>
          </div>
        )}

        {/* ─── Preview phase ─────────────────────────────── */}
        {phase === 'preview' && preview && (
          <div className='space-y-4'>
            {/* Summary card */}
            <div className='bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3'>
              <CheckCircle className='h-5 w-5 text-green-600 flex-shrink-0 mt-0.5' />
              <div className='flex-1 text-sm'>
                <p className='font-medium text-green-900'>
                  Parsed successfully with {preview.parserUsed}
                </p>
                <p className='text-green-700 mt-0.5'>
                  {preview.imageCount > 0
                    ? `${preview.imageCount} image${preview.imageCount === 1 ? '' : 's'} extracted. `
                    : ''}
                  Review the details below and adjust before importing.
                </p>
              </div>
            </div>

            {/* Warnings */}
            {preview.warnings.length > 0 && (
              <div className='bg-amber-50 border border-amber-200 rounded-lg p-3'>
                <div className='flex items-start gap-2'>
                  <AlertTriangle className='h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5' />
                  <div className='flex-1'>
                    <p className='text-sm font-medium text-amber-900 mb-1'>
                      Some content was dropped or simplified:
                    </p>
                    <ul className='text-sm text-amber-800 list-disc list-inside space-y-0.5'>
                      {preview.warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Editable form fields */}
            <div className='space-y-3'>
              <FormInput
                label='Title'
                value={titleOverride}
                onChange={e => setTitleOverride(e.target.value)}
                hint='Defaults to the first slide title — edit to override.'
              />
              <div className='grid grid-cols-2 gap-3'>
                <FormSelect
                  label='Type'
                  value={materialType}
                  onChange={e => setMaterialType(e.target.value)}
                  options={TYPE_OPTIONS}
                />
                <FormSelect
                  label='Category'
                  value={category}
                  onChange={e => setCategory(e.target.value)}
                  options={CATEGORY_OPTIONS}
                />
              </div>
            </div>

            <div className='flex justify-between'>
              <Button
                variant='ghost'
                onClick={() => {
                  setPhase('upload');
                  setPreview(null);
                  setError(null);
                }}
              >
                Back
              </Button>
              <div className='flex gap-2'>
                <Button variant='outline' onClick={handleClose}>
                  Cancel
                </Button>
                <Button variant='primary' onClick={handleApply}>
                  Import to Week {weekNumber}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ─── Applying phase ────────────────────────────── */}
        {phase === 'applying' && (
          <div className='py-12 text-center'>
            <Button loading variant='ghost' size='lg' disabled>
              Importing...
            </Button>
            <p className='text-sm text-gray-500 mt-2'>
              Creating the material and saving images.
            </p>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default PptxImportDialog;
