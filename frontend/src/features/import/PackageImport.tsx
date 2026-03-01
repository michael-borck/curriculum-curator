import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  Package,
  FileCheck,
  ArrowRight,
  BookOpen,
  ClipboardList,
  Loader2,
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle2,
  XCircle,
  FileQuestion,
  ChevronDown,
  ChevronUp,
  Image,
  Video,
  Music,
  Link,
  MessageSquare,
  Megaphone,
  Puzzle,
  Shield,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  unifiedAnalyze,
  unifiedApply,
  checkUnitCode,
} from '../../services/api';
import type {
  UnifiedImportPreview,
  FilePreviewItem,
  SkippedFile,
} from '../../services/api';
import { TaskProgressBar } from '../../components/TaskProgress';
import { useTaskProgress } from '../../hooks/useTaskProgress';
import type { TaskStatus } from '../../services/taskApi';

type Phase = 'upload' | 'preview' | 'processing' | 'done' | 'failed';

const LMS_LABELS: Record<string, string> = {
  canvas: 'Canvas',
  moodle: 'Moodle',
  blackboard: 'Blackboard',
  brightspace: 'Brightspace',
};

const PACKAGE_TYPE_LABELS: Record<string, string> = {
  imscc: 'IMSCC',
  scorm: 'SCORM',
  plain_zip: 'Plain ZIP',
  round_trip: 'Round-trip',
};

const PACKAGE_TYPE_COLORS: Record<string, string> = {
  imscc: 'bg-purple-100 text-purple-800',
  scorm: 'bg-indigo-100 text-indigo-800',
  plain_zip: 'bg-gray-100 text-gray-800',
  round_trip: 'bg-green-100 text-green-800',
};

const SKIP_REASON_LABELS: Record<string, string> = {
  unsupported_format: 'Unsupported format',
  too_large: 'File too large',
  corrupted: 'Corrupted',
  image_not_imported: 'Image not imported',
  video_url_needed: 'Video — URL needed',
  audio_not_supported: 'Audio not supported',
  lti_tool_not_supported: 'LTI tool not supported',
  external_link_not_imported: 'External link not imported',
  discussion_not_applicable: 'Discussion — not applicable',
  announcement_not_applicable: 'Announcement — not applicable',
};

const CONTENT_TYPE_ICONS: Record<
  string,
  React.ComponentType<{ className?: string | undefined }>
> = {
  image: Image,
  video: Video,
  audio: Music,
  lti_tool: Puzzle,
  external_link: Link,
  discussion: MessageSquare,
  announcement: Megaphone,
  access_control: Shield,
  unknown: FileQuestion,
};

const CATEGORY_LABELS: Record<string, string> = {
  action_needed: 'Action needed',
  not_supported: 'Not supported',
  not_applicable: 'Not applicable',
};

const CATEGORY_STYLES: Record<string, string> = {
  action_needed: 'bg-amber-50 border-amber-200 text-amber-800',
  not_supported: 'bg-gray-50 border-gray-200 text-gray-600',
  not_applicable: 'bg-gray-50 border-gray-100 text-gray-500',
};

function groupByCategory(files: SkippedFile[]): Record<string, SkippedFile[]> {
  const groups: Record<string, SkippedFile[]> = {};
  for (const f of files) {
    const cat = f.category || 'not_supported';
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(f);
  }
  return groups;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function PackageImport() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<UnifiedImportPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [showSkipped, setShowSkipped] = useState(false);

  // Background task tracking via SSE
  const { status: taskStatus, start: startTracking } = useTaskProgress({
    onComplete: () => {
      setPhase('done');
      toast.success('Package imported successfully');
    },
    onError: err => {
      setPhase('failed');
      setError(err);
      toast.error('Import failed');
    },
  });

  // Editable overrides
  const [unitCode, setUnitCode] = useState('');
  const [unitTitle, setUnitTitle] = useState('');

  // Editable file list (mutable copy of preview.files)
  const [editableFiles, setEditableFiles] = useState<FilePreviewItem[]>([]);

  // Duplicate code check
  const [codeExists, setCodeExists] = useState(false);
  const [checkingCode, setCheckingCode] = useState(false);
  const codeCheckTimer = useRef<number | null>(null);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (codeCheckTimer.current) window.clearTimeout(codeCheckTimer.current);
    };
  }, []);

  // Debounced duplicate code check
  useEffect(() => {
    if (!unitCode.trim()) {
      setCodeExists(false);
      return;
    }
    if (codeCheckTimer.current) window.clearTimeout(codeCheckTimer.current);
    setCheckingCode(true);
    codeCheckTimer.current = window.setTimeout(async () => {
      try {
        const res = await checkUnitCode(unitCode.trim());
        setCodeExists(res.data.exists);
      } catch {
        setCodeExists(false);
      } finally {
        setCheckingCode(false);
      }
    }, 500);
  }, [unitCode]);

  const handleFile = useCallback(async (f: File) => {
    setFile(f);
    setError(null);
    setAnalyzing(true);
    try {
      const res = await unifiedAnalyze(f);
      const data = res.data;
      setPreview(data);
      setUnitCode(data.unitCode);
      setUnitTitle(data.unitTitle);
      setEditableFiles([...data.files]);
      setPhase('preview');
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : String(
              (err as { response?: { data?: { detail?: string } } })?.response
                ?.data?.detail ?? 'Failed to analyse package'
            );
      setError(msg);
    } finally {
      setAnalyzing(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

  const handleImport = useCallback(async () => {
    if (!file) return;
    setPhase('processing');
    setError(null);
    try {
      const res = await unifiedApply(file, {
        unitCode: unitCode || undefined,
        unitTitle: unitTitle || undefined,
        durationWeeks: preview?.durationWeeks,
      });
      const taskId = res.data.taskId;
      startTracking(taskId);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : String(
              (err as { response?: { data?: { detail?: string } } })?.response
                ?.data?.detail ?? 'Import failed'
            );
      setError(msg);
      setPhase('preview');
      toast.error('Import failed');
    }
  }, [file, unitCode, unitTitle, preview?.durationWeeks, startTracking]);

  const updateFile = (index: number, updates: Partial<FilePreviewItem>) => {
    setEditableFiles(prev => {
      const next = [...prev];
      next[index] = { ...next[index], ...updates };
      return next;
    });
  };

  const materialCount = editableFiles.filter(
    f => f.detectedType === 'material'
  ).length;
  const assessmentCount = editableFiles.filter(
    f => f.detectedType === 'assessment'
  ).length;

  return (
    <div className='p-6 max-w-4xl mx-auto'>
      <h1 className='text-2xl font-bold text-gray-900 mb-2'>Import Package</h1>
      <p className='text-gray-600 mb-6'>
        Import a unit from an IMSCC, SCORM, or plain ZIP package. All file types
        (PDF, DOCX, PPTX, HTML, TXT, MD) are supported.
      </p>

      {error && (
        <div className='mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-2'>
          <AlertCircle className='h-5 w-5 flex-shrink-0 mt-0.5' />
          <span>{error}</span>
        </div>
      )}

      {/* Phase: Upload */}
      {phase === 'upload' && (
        <div
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
          className='border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-purple-400 transition-colors cursor-pointer'
          onClick={() => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.imscc,.zip';
            input.onchange = () => {
              const f = input.files?.[0];
              if (f) handleFile(f);
            };
            input.click();
          }}
        >
          {analyzing ? (
            <div className='flex flex-col items-center'>
              <Loader2 className='h-12 w-12 text-purple-500 animate-spin mb-4' />
              <p className='text-gray-700 font-medium'>Analysing package...</p>
            </div>
          ) : (
            <>
              <Upload className='h-12 w-12 text-gray-400 mx-auto mb-4' />
              <p className='text-gray-700 font-medium mb-1'>
                Drop an .imscc or .zip file here
              </p>
              <p className='text-gray-500 text-sm'>or click to browse</p>
            </>
          )}
        </div>
      )}

      {/* Phase: Preview */}
      {phase === 'preview' && preview && (
        <div className='space-y-6'>
          {/* Package type + source badges */}
          <div className='flex items-center gap-2 flex-wrap'>
            <Package className='h-5 w-5 text-purple-600' />
            <span
              className={`inline-flex items-center rounded-full px-3 py-0.5 text-sm font-medium ${PACKAGE_TYPE_COLORS[preview.packageType] ?? 'bg-gray-100 text-gray-800'}`}
            >
              {PACKAGE_TYPE_LABELS[preview.packageType] ?? preview.packageType}
            </span>
            {preview.isRoundTrip && (
              <span className='inline-flex items-center rounded-full bg-green-100 px-3 py-0.5 text-sm font-medium text-green-800'>
                <FileCheck className='h-3.5 w-3.5 mr-1' />
                Round-trip
              </span>
            )}
            {preview.sourceLms && (
              <span className='inline-flex items-center rounded-full bg-blue-100 px-3 py-0.5 text-sm font-medium text-blue-800'>
                {LMS_LABELS[preview.sourceLms] ?? preview.sourceLms}
              </span>
            )}
          </div>

          {/* Info banner for non-round-trip */}
          {!preview.isRoundTrip && (
            <div className='p-3 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 flex items-start gap-2 text-sm'>
              <Info className='h-5 w-5 flex-shrink-0 mt-0.5' />
              <span>
                Structure has been inferred from the package. Review the file
                mapping below and adjust types/weeks as needed before importing.
              </span>
            </div>
          )}

          {/* Blackboard content-area info banner */}
          {preview.sourceLms === 'blackboard' &&
            preview.detectedContentAreas &&
            preview.detectedContentAreas.length > 0 && (
              <div className='p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 flex items-start gap-2 text-sm'>
                <AlertTriangle className='h-5 w-5 flex-shrink-0 mt-0.5' />
                <div>
                  <p className='font-medium mb-1'>
                    Blackboard content areas detected
                  </p>
                  <p className='mb-2'>
                    This package uses Blackboard&apos;s content-area structure
                    instead of weekly modules. Content areas have been mapped to
                    weeks for import, but you may want to reorganise the
                    materials after importing.
                  </p>
                  <div className='flex flex-wrap gap-1'>
                    {preview.detectedContentAreas.map(area => (
                      <span
                        key={area}
                        className='inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700'
                      >
                        {area}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

          {/* Editable unit fields */}
          <div className='grid grid-cols-2 gap-4'>
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Unit Code
              </label>
              <input
                type='text'
                value={unitCode}
                onChange={e => setUnitCode(e.target.value)}
                className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 ${codeExists ? 'border-yellow-400' : 'border-gray-300'}`}
              />
            </div>
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Unit Title
              </label>
              <input
                type='text'
                value={unitTitle}
                onChange={e => setUnitTitle(e.target.value)}
                className='w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
              />
            </div>
          </div>

          {/* Duplicate code warning */}
          {codeExists && !checkingCode && (
            <div className='p-3 rounded-lg bg-yellow-50 border border-yellow-200 text-yellow-800 flex items-start gap-2 text-sm'>
              <AlertTriangle className='h-5 w-5 flex-shrink-0 mt-0.5' />
              <span>
                A unit with code <strong>{unitCode.trim()}</strong> already
                exists. Importing will create a second unit with the same code.
              </span>
            </div>
          )}

          {/* Summary counts */}
          <div className='grid grid-cols-2 sm:grid-cols-4 gap-3'>
            <StatCard icon={BookOpen} label='Materials' count={materialCount} />
            <StatCard
              icon={ClipboardList}
              label='Assessments'
              count={assessmentCount}
            />
            <StatCard
              icon={CheckCircle2}
              label='Processable'
              count={preview.totalProcessable}
            />
            <StatCard
              icon={XCircle}
              label='Skipped'
              count={preview.totalSkipped}
            />
          </div>

          {/* File table */}
          <div className='border border-gray-200 rounded-lg overflow-hidden'>
            <table className='w-full text-sm'>
              <thead className='bg-gray-50 border-b border-gray-200'>
                <tr>
                  <th className='text-left px-3 py-2 font-medium text-gray-600'>
                    File
                  </th>
                  <th className='text-left px-3 py-2 font-medium text-gray-600 w-28'>
                    Type
                  </th>
                  <th className='text-left px-3 py-2 font-medium text-gray-600 w-20'>
                    Week
                  </th>
                  <th className='text-left px-3 py-2 font-medium text-gray-600'>
                    Title
                  </th>
                  <th className='text-right px-3 py-2 font-medium text-gray-600 w-20'>
                    Size
                  </th>
                </tr>
              </thead>
              <tbody className='divide-y divide-gray-100'>
                {editableFiles.map((f, i) => (
                  <tr key={f.path} className='hover:bg-gray-50'>
                    <td
                      className='px-3 py-2 text-gray-700 truncate max-w-[200px]'
                      title={f.path}
                    >
                      <span className='inline-flex items-center gap-1'>
                        <span className='text-xs text-gray-400 uppercase font-mono'>
                          {f.extension}
                        </span>
                        <span className='truncate'>{f.filename}</span>
                      </span>
                    </td>
                    <td className='px-3 py-2'>
                      <select
                        value={f.detectedType}
                        onChange={e =>
                          updateFile(i, { detectedType: e.target.value })
                        }
                        className='w-full rounded border border-gray-200 px-1.5 py-1 text-xs'
                      >
                        <option value='material'>Material</option>
                        <option value='assessment'>Assessment</option>
                        <option value='outline'>Outline</option>
                      </select>
                    </td>
                    <td className='px-3 py-2'>
                      <input
                        type='number'
                        min={1}
                        max={52}
                        value={f.weekNumber ?? ''}
                        onChange={e =>
                          updateFile(i, {
                            weekNumber: e.target.value
                              ? Number(e.target.value)
                              : null,
                          })
                        }
                        placeholder='-'
                        className='w-full rounded border border-gray-200 px-1.5 py-1 text-xs text-center'
                      />
                    </td>
                    <td className='px-3 py-2'>
                      <input
                        type='text'
                        value={f.title}
                        onChange={e => updateFile(i, { title: e.target.value })}
                        className='w-full rounded border border-gray-200 px-1.5 py-1 text-xs'
                      />
                    </td>
                    <td className='px-3 py-2 text-right text-gray-500 text-xs'>
                      {formatBytes(f.sizeBytes)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Skipped files — categorised */}
          {preview.skippedFiles.length > 0 && (
            <div>
              <button
                onClick={() => setShowSkipped(!showSkipped)}
                className='flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700'
              >
                {showSkipped ? (
                  <ChevronUp className='h-4 w-4' />
                ) : (
                  <ChevronDown className='h-4 w-4' />
                )}
                {preview.skippedFiles.length} skipped item
                {preview.skippedFiles.length !== 1 ? 's' : ''}
              </button>
              {showSkipped && <SkippedFilesList files={preview.skippedFiles} />}
            </div>
          )}

          {/* Import button */}
          <button
            onClick={handleImport}
            className='w-full flex items-center justify-center gap-2 rounded-lg bg-purple-600 px-4 py-3 text-white font-medium hover:bg-purple-700 transition-colors'
          >
            <Package className='h-5 w-5' />
            Import Unit
          </button>
        </div>
      )}

      {/* Phase: Processing */}
      {phase === 'processing' && (
        <div className='py-12 space-y-4'>
          <div className='flex flex-col items-center'>
            <Loader2 className='h-12 w-12 text-purple-500 animate-spin mb-4' />
            <p className='text-gray-700 font-medium'>Importing package...</p>
          </div>
          {taskStatus && (
            <div className='max-w-md mx-auto'>
              <TaskProgressBar status={taskStatus} />
            </div>
          )}
        </div>
      )}

      {/* Phase: Failed */}
      {phase === 'failed' && (
        <div className='space-y-6'>
          <div className='bg-red-50 border border-red-200 rounded-xl p-6 text-center'>
            <XCircle className='h-10 w-10 text-red-600 mx-auto mb-3' />
            <h2 className='text-lg font-semibold text-gray-900 mb-1'>
              Import Failed
            </h2>
            <p className='text-gray-600 text-sm'>{error}</p>
          </div>
          <button
            onClick={() => {
              setPhase('preview');
              setError(null);
            }}
            className='w-full flex items-center justify-center gap-2 rounded-lg bg-gray-100 px-4 py-3 text-gray-700 font-medium hover:bg-gray-200 transition-colors'
          >
            Back to Preview
          </button>
        </div>
      )}

      {/* Phase: Done */}
      {phase === 'done' && taskStatus && (
        <DonePhase taskStatus={taskStatus} navigate={navigate} />
      )}
    </div>
  );
}

function DonePhase({
  taskStatus,
  navigate,
}: {
  taskStatus: TaskStatus;
  navigate: ReturnType<typeof useNavigate>;
}) {
  const unitId = taskStatus.meta.unit_id as string | undefined;
  const unitCodeVal = taskStatus.meta.unit_code as string | undefined;
  const unitTitleVal = taskStatus.meta.unit_title as string | undefined;
  const skippedItems = (taskStatus.meta.skipped_items ?? []) as SkippedFile[];

  return (
    <div className='space-y-6'>
      <div className='bg-green-50 border border-green-200 rounded-xl p-6 text-center'>
        <FileCheck className='h-10 w-10 text-green-600 mx-auto mb-3' />
        <h2 className='text-lg font-semibold text-gray-900 mb-1'>
          Import Complete
        </h2>
        <p className='text-gray-600'>
          <strong>{unitCodeVal}</strong> — {unitTitleVal}
        </p>
        <p className='text-sm text-gray-500 mt-1'>
          {taskStatus.progress} file
          {taskStatus.progress !== 1 ? 's' : ''} processed
        </p>
      </div>

      {taskStatus.errors.length > 0 && (
        <div className='p-3 rounded-lg bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm'>
          <p className='font-medium mb-1'>
            Some files had issues ({taskStatus.errors.length}):
          </p>
          <ul className='list-disc list-inside space-y-0.5'>
            {taskStatus.errors.slice(0, 5).map((err, i) => (
              <li key={i}>{err}</li>
            ))}
            {taskStatus.errors.length > 5 && (
              <li>...and {taskStatus.errors.length - 5} more</li>
            )}
          </ul>
        </div>
      )}

      {skippedItems.length > 0 && <SkippedFilesList files={skippedItems} />}

      {unitId && (
        <button
          onClick={() => navigate(`/units/${unitId}`)}
          className='w-full flex items-center justify-center gap-2 rounded-lg bg-purple-600 px-4 py-3 text-white font-medium hover:bg-purple-700 transition-colors'
        >
          Go to Unit
          <ArrowRight className='h-5 w-5' />
        </button>
      )}
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  count,
}: {
  icon: React.ComponentType<{ className?: string | undefined }>;
  label: string;
  count: number;
}) {
  return (
    <div className='bg-white border border-gray-200 rounded-lg p-3 text-center'>
      <Icon className='h-5 w-5 text-purple-600 mx-auto mb-1' />
      <div className='text-xl font-bold text-gray-900'>{count}</div>
      <div className='text-xs text-gray-500'>{label}</div>
    </div>
  );
}

/** Renders skipped files grouped by category (action_needed, not_supported, not_applicable). */
function SkippedFilesList({ files }: { files: SkippedFile[] }) {
  const groups = groupByCategory(files);
  const categoryOrder = ['action_needed', 'not_supported', 'not_applicable'];

  return (
    <div className='mt-2 space-y-3'>
      {categoryOrder.map(cat => {
        const items = groups[cat];
        if (!items || items.length === 0) return null;
        const style =
          CATEGORY_STYLES[cat] ?? 'bg-gray-50 border-gray-200 text-gray-600';
        return (
          <div key={cat} className={`rounded-lg border p-3 ${style}`}>
            <p className='text-sm font-medium mb-2'>
              {CATEGORY_LABELS[cat] ?? cat} ({items.length})
            </p>
            <div className='space-y-1'>
              {items.map(sf => {
                const Icon = CONTENT_TYPE_ICONS[sf.contentType] ?? FileQuestion;
                return (
                  <div
                    key={sf.path + sf.filename}
                    className='flex items-center gap-2 text-sm'
                  >
                    <Icon className='h-4 w-4 flex-shrink-0' />
                    <span className='truncate'>{sf.filename}</span>
                    <span className='text-xs opacity-70'>
                      {SKIP_REASON_LABELS[sf.reason] ?? sf.reason}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
