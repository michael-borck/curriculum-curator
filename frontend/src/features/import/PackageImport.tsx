import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  Package,
  FileCheck,
  ArrowRight,
  BookOpen,
  GraduationCap,
  ClipboardList,
  Award,
  Loader2,
  AlertCircle,
  Info,
  Calendar,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { analyzePackage, createFromPackage } from '../../services/api';
import type {
  PackageImportPreview,
  PackageImportResult,
} from '../../services/api';

type Phase = 'upload' | 'preview' | 'importing' | 'done';

const LMS_LABELS: Record<string, string> = {
  canvas: 'Canvas',
  moodle: 'Moodle',
  blackboard: 'Blackboard',
  brightspace: 'Brightspace',
};

export default function PackageImport() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PackageImportPreview | null>(null);
  const [result, setResult] = useState<PackageImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  // Editable overrides
  const [unitCode, setUnitCode] = useState('');
  const [unitTitle, setUnitTitle] = useState('');

  const handleFile = useCallback(async (f: File) => {
    setFile(f);
    setError(null);
    setAnalyzing(true);
    try {
      const res = await analyzePackage(f);
      const data = res.data;
      setPreview(data);
      setUnitCode(data.unitCode);
      setUnitTitle(data.unitTitle);
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
    setPhase('importing');
    setError(null);
    try {
      const res = await createFromPackage(file, {
        unitCode: unitCode || undefined,
        unitTitle: unitTitle || undefined,
      });
      setResult(res.data);
      setPhase('done');
      toast.success('Package imported successfully');
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
  }, [file, unitCode, unitTitle]);

  return (
    <div className='p-6 max-w-3xl mx-auto'>
      <h1 className='text-2xl font-bold text-gray-900 mb-2'>Import Package</h1>
      <p className='text-gray-600 mb-6'>
        Import a unit from an IMSCC or SCORM package — from Curriculum Curator
        or any LMS (Canvas, Moodle, Blackboard).
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
          {/* Format + source badges */}
          <div className='flex items-center gap-2 flex-wrap'>
            <Package className='h-5 w-5 text-purple-600' />
            <span className='inline-flex items-center rounded-full bg-purple-100 px-3 py-0.5 text-sm font-medium text-purple-800'>
              {preview.format === 'scorm_1.2' ? 'SCORM 1.2' : 'IMSCC'}
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

          {/* Info banner for generic imports */}
          {!preview.isRoundTrip && (
            <div className='p-3 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 flex items-start gap-2 text-sm'>
              <Info className='h-5 w-5 flex-shrink-0 mt-0.5' />
              <span>
                This package was not exported by Curriculum Curator. Structure
                has been inferred from the manifest — ULOs, pedagogy, and
                accreditation data will need to be added after import.
              </span>
            </div>
          )}

          {/* Editable fields */}
          <div className='grid grid-cols-2 gap-4'>
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Unit Code
              </label>
              <input
                type='text'
                value={unitCode}
                onChange={e => setUnitCode(e.target.value)}
                className='w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
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

          {/* Counts grid */}
          <div className='grid grid-cols-2 sm:grid-cols-4 gap-3'>
            <StatCard
              icon={GraduationCap}
              label='ULOs'
              count={preview.uloCount}
            />
            <StatCard
              icon={BookOpen}
              label='Materials'
              count={preview.materialCount}
            />
            <StatCard
              icon={ClipboardList}
              label='Assessments'
              count={preview.assessmentCount}
            />
            {preview.isRoundTrip ? (
              <StatCard
                icon={Award}
                label='Accreditation'
                count={
                  preview.aolMappingCount +
                  preview.sdgMappingCount +
                  preview.gcMappingCount
                }
              />
            ) : (
              <StatCard
                icon={Calendar}
                label='Weeks'
                count={preview.durationWeeks}
              />
            )}
          </div>

          {/* Unit metadata summary */}
          <div className='bg-gray-50 rounded-lg p-4 text-sm text-gray-600 grid grid-cols-2 sm:grid-cols-3 gap-2'>
            <span>
              <strong>Year:</strong> {preview.year}
            </span>
            <span>
              <strong>Semester:</strong> {preview.semester.replace('_', ' ')}
            </span>
            <span>
              <strong>Weeks:</strong> {preview.durationWeeks}
            </span>
            <span>
              <strong>Credits:</strong> {preview.creditPoints}
            </span>
            <span>
              <strong>Pedagogy:</strong>{' '}
              {preview.pedagogyType.replace(/-/g, ' ')}
            </span>
            <span>
              <strong>Level:</strong> {preview.difficultyLevel}
            </span>
          </div>

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

      {/* Phase: Importing */}
      {phase === 'importing' && (
        <div className='text-center py-12'>
          <Loader2 className='h-12 w-12 text-purple-500 animate-spin mx-auto mb-4' />
          <p className='text-gray-700 font-medium'>Importing package...</p>
        </div>
      )}

      {/* Phase: Done */}
      {phase === 'done' && result && (
        <div className='space-y-6'>
          <div className='bg-green-50 border border-green-200 rounded-xl p-6 text-center'>
            <FileCheck className='h-10 w-10 text-green-600 mx-auto mb-3' />
            <h2 className='text-lg font-semibold text-gray-900 mb-1'>
              Import Complete
            </h2>
            <p className='text-gray-600'>
              <strong>{result.unitCode}</strong> — {result.unitTitle}
            </p>
          </div>

          <div className='grid grid-cols-2 sm:grid-cols-4 gap-3'>
            <StatCard
              icon={GraduationCap}
              label='ULOs'
              count={result.uloCount}
            />
            <StatCard
              icon={BookOpen}
              label='Materials'
              count={result.materialCount}
            />
            <StatCard
              icon={ClipboardList}
              label='Assessments'
              count={result.assessmentCount}
            />
            <StatCard
              icon={Award}
              label='Accreditation'
              count={
                result.aolMappingCount +
                result.sdgMappingCount +
                result.gcMappingCount
              }
            />
          </div>

          <button
            onClick={() => navigate(`/units/${result.unitId}`)}
            className='w-full flex items-center justify-center gap-2 rounded-lg bg-purple-600 px-4 py-3 text-white font-medium hover:bg-purple-700 transition-colors'
          >
            Go to Unit
            <ArrowRight className='h-5 w-5' />
          </button>
        </div>
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
