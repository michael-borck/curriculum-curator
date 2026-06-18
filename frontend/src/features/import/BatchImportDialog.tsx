import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Upload,
  FileText,
  AlertCircle,
  AlertTriangle,
  Layers,
  Loader2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Modal, Button } from '../../components/ui';
import {
  previewBatchMaterials,
  applyBatchMaterials,
  getBatchStatus,
  type BatchPreviewResponse,
  type BatchGroupOverride,
} from '../../services/materialImportApi';

/**
 * BatchImportDialog — Mode B (multi-file zip → existing unit) frontend.
 *
 * Flow: upload a zip → preview groups the files by (folder, filename stem)
 * and picks a canonical file per group (PPTX > DOCX > HTML > MD > PDF),
 * attaching the rest as source files → the user reviews and can override
 * which file is canonical per group → apply runs async and polls status.
 *
 * Week assignment is auto-detected from filename/folder; the user can
 * override per group in the review screen.
 */

interface BatchImportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  unitId: string;
  onImported: () => void;
}

type Phase = 'upload' | 'analyzing' | 'review' | 'importing';

const MAX_FILE_SIZE_MB = 200;

const BatchImportDialog: React.FC<BatchImportDialogProps> = ({
  isOpen,
  onClose,
  unitId,
  onImported,
}) => {
  const [phase, setPhase] = useState<Phase>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<BatchPreviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  // Per-group overrides keyed by group name
  const [overrides, setOverrides] = useState<
    Record<string, BatchGroupOverride>
  >({});
  const [progress, setProgress] = useState<{ done: number; total: number }>({
    done: 0,
    total: 0,
  });
  const pollRef = useRef<number | null>(null);

  const reset = useCallback(() => {
    setPhase('upload');
    setFile(null);
    setPreview(null);
    setError(null);
    setOverrides({});
    setProgress({ done: 0, total: 0 });
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!isOpen) reset();
  }, [isOpen, reset]);

  useEffect(
    () => () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    },
    []
  );

  const handleClose = () => {
    if (phase === 'importing') return; // don't abandon a running import
    onClose();
  };

  const validateAndSet = (f: File) => {
    setError(null);
    if (!f.name.toLowerCase().endsWith('.zip')) {
      setError('Please choose a .zip file.');
      return;
    }
    if (f.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`File is larger than ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }
    setFile(f);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setPhase('analyzing');
    setError(null);
    try {
      const result = await previewBatchMaterials(file, unitId);
      setPreview(result);
      setPhase('review');
    } catch {
      setError('Failed to analyze the zip. Check the file and try again.');
      setPhase('upload');
    }
  };

  const setGroupOverride = (
    name: string,
    patch: Partial<BatchGroupOverride>
  ) => {
    setOverrides(prev => ({
      ...prev,
      [name]: { ...prev[name], ...patch, name },
    }));
  };

  const handleApply = async () => {
    if (!file || !preview) return;
    setPhase('importing');
    setProgress({ done: 0, total: preview.totalMaterials });
    try {
      const overrideList = Object.values(overrides).filter(
        o => o.canonicalFilename !== undefined || o.weekNumber !== undefined
      );
      const taskId = await applyBatchMaterials(file, unitId, overrideList);
      pollRef.current = window.setInterval(async () => {
        try {
          const status = await getBatchStatus(taskId);
          setProgress({
            done: status.processedFiles,
            total: status.totalFiles || preview.totalMaterials,
          });
          if (status.status === 'completed' || status.status === 'failed') {
            if (pollRef.current) window.clearInterval(pollRef.current);
            pollRef.current = null;
            if (status.status === 'completed') {
              toast.success(
                `Imported ${status.processedFiles} material${status.processedFiles === 1 ? '' : 's'}`
              );
              onImported();
              onClose();
            } else {
              setError(
                status.errors[0] ?? 'Import failed. No materials were created.'
              );
              setPhase('review');
            }
          }
        } catch {
          if (pollRef.current) window.clearInterval(pollRef.current);
          pollRef.current = null;
          setError('Lost contact with the import task.');
          setPhase('review');
        }
      }, 1500);
    } catch {
      setError('Failed to start the import.');
      setPhase('review');
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title='Import folder of materials'
      size='2xl'
    >
      {phase === 'upload' && (
        <div className='space-y-4'>
          <p className='text-sm text-gray-600'>
            Upload a <strong>.zip</strong> of materials. We&apos;ll group
            multiple formats of the same lecture (e.g. PPTX + PDF + DOCX) into
            one editable material with the rest attached as source files, and
            guess each material&apos;s week from its filename and folder.
          </p>
          <div
            onDragOver={e => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={e => {
              e.preventDefault();
              setDragOver(false);
              const f = e.dataTransfer.files[0];
              if (f) validateAndSet(f);
            }}
            className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
              dragOver
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-300 bg-gray-50'
            }`}
          >
            <Upload className='w-8 h-8 mx-auto text-gray-400 mb-2' />
            <p className='text-sm text-gray-600 mb-2'>
              {file ? file.name : 'Drag a zip here, or'}
            </p>
            <label className='inline-block'>
              <span className='cursor-pointer text-sm font-medium text-blue-600 hover:text-blue-700'>
                browse files
              </span>
              <input
                type='file'
                accept='.zip'
                className='hidden'
                onChange={e => {
                  const f = e.target.files?.[0];
                  if (f) validateAndSet(f);
                }}
              />
            </label>
          </div>
          {error && (
            <div className='flex items-start gap-2 text-sm text-red-600'>
              <AlertCircle className='w-4 h-4 mt-0.5 shrink-0' />
              <span>{error}</span>
            </div>
          )}
          <div className='flex justify-end gap-2'>
            <Button variant='secondary' onClick={handleClose}>
              Cancel
            </Button>
            <Button onClick={handleAnalyze} disabled={!file}>
              Analyze
            </Button>
          </div>
        </div>
      )}

      {phase === 'analyzing' && (
        <div className='flex flex-col items-center justify-center py-12 text-gray-500'>
          <Loader2 className='w-6 h-6 animate-spin mb-3' />
          <p className='text-sm'>Analyzing the zip…</p>
        </div>
      )}

      {phase === 'review' && preview && (
        <div className='space-y-4'>
          <div className='flex items-center gap-2 text-sm text-gray-700'>
            <Layers className='w-4 h-4 text-blue-500' />
            <span>
              <strong>{preview.totalMaterials}</strong> material
              {preview.totalMaterials === 1 ? '' : 's'} will be created
              {preview.totalSourceFiles > 0 && (
                <>
                  , with <strong>{preview.totalSourceFiles}</strong> source file
                  {preview.totalSourceFiles === 1 ? '' : 's'} attached
                </>
              )}
              .
            </span>
          </div>

          {preview.warnings.length > 0 && (
            <div className='rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800'>
              <div className='flex items-center gap-2 font-medium mb-1'>
                <AlertTriangle className='w-4 h-4' />
                Some files were skipped
              </div>
              <ul className='list-disc list-inside space-y-0.5'>
                {preview.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <div className='max-h-80 overflow-y-auto space-y-2'>
            {preview.groups.map(group => {
              const override = overrides[group.name];
              const canonical =
                override?.canonicalFilename ?? group.canonicalFilename;
              const members = [
                group.canonicalFilename,
                ...group.sourceFiles.map(s => s.filename),
              ];
              const week = override?.weekNumber ?? group.detectedWeek;
              return (
                <div
                  key={group.name}
                  className='border border-gray-200 rounded-lg p-3'
                >
                  <div className='flex items-center justify-between gap-3 mb-2'>
                    <span className='text-sm font-medium text-gray-800 flex items-center gap-2'>
                      <Layers className='w-3.5 h-3.5 text-gray-400' />
                      {group.name}
                    </span>
                    <label className='text-xs text-gray-500 flex items-center gap-1'>
                      Week
                      <input
                        type='number'
                        min={1}
                        max={52}
                        value={week ?? ''}
                        placeholder='?'
                        onChange={e =>
                          setGroupOverride(group.name, {
                            weekNumber: e.target.value
                              ? Number(e.target.value)
                              : undefined,
                          })
                        }
                        className='w-14 border border-gray-200 rounded px-1.5 py-0.5 text-sm'
                      />
                    </label>
                  </div>
                  <label className='block text-xs text-gray-500 mb-1'>
                    Editable material (others attached as source files)
                  </label>
                  <select
                    value={canonical}
                    onChange={e =>
                      setGroupOverride(group.name, {
                        canonicalFilename: e.target.value,
                      })
                    }
                    className='w-full border border-gray-200 rounded px-2 py-1 text-sm'
                  >
                    {members.map(m => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </div>
              );
            })}

            {preview.standaloneFiles.map(sf => (
              <div
                key={sf.path}
                className='flex items-center justify-between gap-3 border border-gray-100 rounded-lg px-3 py-2 text-sm'
              >
                <span className='flex items-center gap-2 text-gray-700 min-w-0'>
                  <FileText className='w-3.5 h-3.5 text-gray-400 shrink-0' />
                  <span className='truncate'>{sf.filename}</span>
                </span>
                <span className='text-xs text-gray-400 shrink-0'>
                  {sf.detectedWeek ? `Week ${sf.detectedWeek}` : 'No week'}
                </span>
              </div>
            ))}
          </div>

          {error && (
            <div className='flex items-start gap-2 text-sm text-red-600'>
              <AlertCircle className='w-4 h-4 mt-0.5 shrink-0' />
              <span>{error}</span>
            </div>
          )}

          <div className='flex justify-end gap-2'>
            <Button variant='secondary' onClick={reset}>
              Back
            </Button>
            <Button
              onClick={handleApply}
              disabled={preview.totalMaterials === 0}
            >
              Import {preview.totalMaterials} material
              {preview.totalMaterials === 1 ? '' : 's'}
            </Button>
          </div>
        </div>
      )}

      {phase === 'importing' && (
        <div className='flex flex-col items-center justify-center py-12 text-gray-500'>
          <Loader2 className='w-6 h-6 animate-spin mb-3' />
          <p className='text-sm'>
            Importing… {progress.done}
            {progress.total ? ` / ${progress.total}` : ''}
          </p>
        </div>
      )}
    </Modal>
  );
};

export default BatchImportDialog;
