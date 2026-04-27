import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Download,
  RefreshCw,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  downloadOutline,
  triggerCourseBuild,
  listCourseJobs,
  downloadCourseArchive,
} from '../../services/curtinApi';
import type { CurtinJobResponse } from '../../services/curtinApi';

// =============================================================================
// Helpers
// =============================================================================

function triggerBrowserDownload(
  data: ArrayBuffer,
  filename: string,
  mimeType: string
): void {
  const blob = new Blob([data], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString('en-AU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function isCredentialsError(err: unknown): boolean {
  if (err && typeof err === 'object') {
    const e = err as { response?: { data?: { detail?: string } } };
    const detail = e.response?.data?.detail ?? '';
    return detail.toLowerCase().includes('credential');
  }
  return false;
}

function getErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (err && typeof err === 'object') {
    const e = err as { response?: { data?: { detail?: string } } };
    return e.response?.data?.detail ?? 'An unexpected error occurred';
  }
  return 'An unexpected error occurred';
}

// =============================================================================
// Status badge
// =============================================================================

interface StatusBadgeProps {
  status: string;
}

function StatusBadge({ status }: StatusBadgeProps) {
  if (status === 'triggered' || status === 'pending') {
    return (
      <span className='inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800'>
        <Clock className='h-3 w-3' />
        {status}
      </span>
    );
  }
  if (status === 'downloaded' || status === 'complete') {
    return (
      <span className='inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800'>
        <CheckCircle className='h-3 w-3' />
        {status}
      </span>
    );
  }
  if (status === 'failed' || status === 'error') {
    return (
      <span className='inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800'>
        <XCircle className='h-3 w-3' />
        {status}
      </span>
    );
  }
  return (
    <span className='inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700'>
      {status}
    </span>
  );
}

// =============================================================================
// Outline section
// =============================================================================

function OutlineSection() {
  const navigate = useNavigate();
  const [unitCode, setUnitCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = useCallback(async () => {
    if (!unitCode.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { filename, data } = await downloadOutline(unitCode.trim());
      // Trigger browser file download
      triggerBrowserDownload(data, filename, 'application/pdf');
      toast.success(`Downloaded ${filename}`);
      // Navigate to outline import with the file data
      navigate('/import/outline', {
        state: { curtinFile: { name: filename, data } },
      });
    } catch (err: unknown) {
      if (isCredentialsError(err)) {
        setError(
          'Please configure your Curtin credentials in Settings → Curtin'
        );
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }, [unitCode, navigate]);

  return (
    <section className='bg-white rounded-lg border border-gray-200 p-6'>
      <h2 className='text-lg font-semibold text-gray-900 mb-1'>
        Download Unit Outline
      </h2>
      <p className='text-sm text-gray-500 mb-4'>
        Enter a unit code to download its outline PDF from LITEC.
      </p>

      {error && (
        <div className='mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-2'>
          <AlertCircle className='h-5 w-5 flex-shrink-0 mt-0.5' />
          <span className='text-sm'>{error}</span>
        </div>
      )}

      <div className='flex gap-3'>
        <input
          type='text'
          value={unitCode}
          onChange={e => setUnitCode(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') void handleDownload();
          }}
          placeholder='e.g. COMP1000'
          className='flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
          disabled={loading}
        />
        <button
          onClick={() => void handleDownload()}
          disabled={loading || !unitCode.trim()}
          className='inline-flex items-center gap-2 rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
        >
          {loading ? (
            <Loader2 className='h-4 w-4 animate-spin' />
          ) : (
            <Download className='h-4 w-4' />
          )}
          {loading ? 'Downloading...' : 'Download Outline PDF'}
        </button>
      </div>
    </section>
  );
}

// =============================================================================
// Course archive section
// =============================================================================

interface JobRowProps {
  job: CurtinJobResponse;
  onDownload: (job: CurtinJobResponse) => void;
  downloadingId: string | null;
  jobError: { id: string; message: string } | null;
}

function JobRow({ job, onDownload, downloadingId, jobError }: JobRowProps) {
  const isDownloading = downloadingId === job.id;
  const rowError = jobError?.id === job.id ? jobError.message : null;

  return (
    <>
      <tr className='hover:bg-gray-50'>
        <td className='px-4 py-3 text-sm text-gray-900 font-mono'>
          {job.courseName}
        </td>
        <td className='px-4 py-3'>
          <StatusBadge status={job.status} />
        </td>
        <td className='px-4 py-3 text-sm text-gray-500'>
          {formatDate(job.triggeredAt)}
        </td>
        <td className='px-4 py-3 text-right'>
          <button
            onClick={() => onDownload(job)}
            disabled={isDownloading}
            className='inline-flex items-center gap-1.5 rounded-lg bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
          >
            {isDownloading ? (
              <Loader2 className='h-3.5 w-3.5 animate-spin' />
            ) : (
              <Download className='h-3.5 w-3.5' />
            )}
            {isDownloading ? 'Downloading...' : 'Download'}
          </button>
        </td>
      </tr>
      {rowError && (
        <tr>
          <td colSpan={4} className='px-4 pb-2'>
            <div className='flex items-start gap-1.5 text-xs text-red-700 bg-red-50 border border-red-200 rounded px-2 py-1.5'>
              <AlertCircle className='h-3.5 w-3.5 flex-shrink-0 mt-0.5' />
              <span>{rowError}</span>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function CourseSection() {
  const navigate = useNavigate();
  const [courseName, setCourseName] = useState('');
  const [triggering, setTriggering] = useState(false);
  const [triggerError, setTriggerError] = useState<string | null>(null);

  const [jobs, setJobs] = useState<CurtinJobResponse[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [jobsError, setJobsError] = useState<string | null>(null);

  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [jobError, setJobError] = useState<{
    id: string;
    message: string;
  } | null>(null);

  const fetchJobs = useCallback(async () => {
    setLoadingJobs(true);
    setJobsError(null);
    try {
      const data = await listCourseJobs();
      setJobs(data.slice(0, 10));
    } catch (err: unknown) {
      setJobsError(getErrorMessage(err));
    } finally {
      setLoadingJobs(false);
    }
  }, []);

  useEffect(() => {
    void fetchJobs();
  }, [fetchJobs]);

  const handleTrigger = useCallback(async () => {
    if (!courseName.trim()) return;
    setTriggering(true);
    setTriggerError(null);
    try {
      await triggerCourseBuild(courseName.trim());
      toast.success(`Build triggered for ${courseName.trim()}`);
      setCourseName('');
      await fetchJobs();
    } catch (err: unknown) {
      if (isCredentialsError(err)) {
        setTriggerError(
          'Please configure your Curtin credentials in Settings → Curtin'
        );
      } else {
        setTriggerError(getErrorMessage(err));
      }
    } finally {
      setTriggering(false);
    }
  }, [courseName, fetchJobs]);

  const handleJobDownload = useCallback(
    async (job: CurtinJobResponse) => {
      setDownloadingId(job.id);
      setJobError(null);
      try {
        const { filename, data } = await downloadCourseArchive(job.id);
        triggerBrowserDownload(data, filename, 'application/zip');
        toast.success(`Downloaded ${filename}`);
        navigate('/import/package', {
          state: { curtinFile: { name: filename, data } },
        });
      } catch (err: unknown) {
        if (err && typeof err === 'object' && 'notReady' in err) {
          setJobError({
            id: job.id,
            message: 'Export not ready yet. Check back in 15-30 minutes.',
          });
        } else {
          setJobError({
            id: job.id,
            message: getErrorMessage(err),
          });
        }
      } finally {
        setDownloadingId(null);
      }
    },
    [navigate]
  );

  return (
    <section className='bg-white rounded-lg border border-gray-200 p-6'>
      <h2 className='text-lg font-semibold text-gray-900 mb-1'>
        Blackboard Course Export
      </h2>
      <p className='text-sm text-gray-500 mb-4'>
        Trigger a Blackboard course archive export. Exports typically take 15-30
        minutes to prepare.
      </p>

      {triggerError && (
        <div className='mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-2'>
          <AlertCircle className='h-5 w-5 flex-shrink-0 mt-0.5' />
          <span className='text-sm'>{triggerError}</span>
        </div>
      )}

      <div className='flex gap-3 mb-6'>
        <input
          type='text'
          value={courseName}
          onChange={e => setCourseName(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') void handleTrigger();
          }}
          placeholder='e.g. COMP1000_S1_2025'
          className='flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500'
          disabled={triggering}
        />
        <button
          onClick={() => void handleTrigger()}
          disabled={triggering || !courseName.trim()}
          className='inline-flex items-center gap-2 rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
        >
          {triggering ? <Loader2 className='h-4 w-4 animate-spin' /> : null}
          {triggering ? 'Triggering...' : 'Trigger Build'}
        </button>
      </div>

      {/* Jobs list */}
      <div>
        <div className='flex items-center justify-between mb-3'>
          <h3 className='text-sm font-medium text-gray-700'>Recent Jobs</h3>
          <button
            onClick={() => void fetchJobs()}
            disabled={loadingJobs}
            className='inline-flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 disabled:opacity-50'
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${loadingJobs ? 'animate-spin' : ''}`}
            />
            Refresh
          </button>
        </div>

        {jobsError && (
          <div className='p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-2 text-sm'>
            <AlertCircle className='h-5 w-5 flex-shrink-0 mt-0.5' />
            <span>{jobsError}</span>
          </div>
        )}

        {!jobsError && (
          <div className='border border-gray-200 rounded-lg overflow-hidden'>
            <table className='w-full text-sm'>
              <thead className='bg-gray-50 border-b border-gray-200'>
                <tr>
                  <th className='text-left px-4 py-2.5 font-medium text-gray-600'>
                    Course Name
                  </th>
                  <th className='text-left px-4 py-2.5 font-medium text-gray-600 w-32'>
                    Status
                  </th>
                  <th className='text-left px-4 py-2.5 font-medium text-gray-600 w-40'>
                    Triggered
                  </th>
                  <th className='text-right px-4 py-2.5 font-medium text-gray-600 w-32'>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className='divide-y divide-gray-100'>
                {loadingJobs && jobs.length === 0 ? (
                  <tr>
                    <td
                      colSpan={4}
                      className='px-4 py-8 text-center text-gray-400 text-sm'
                    >
                      <Loader2 className='h-5 w-5 animate-spin mx-auto mb-2' />
                      Loading jobs...
                    </td>
                  </tr>
                ) : jobs.length === 0 ? (
                  <tr>
                    <td
                      colSpan={4}
                      className='px-4 py-8 text-center text-gray-400 text-sm'
                    >
                      No jobs yet. Trigger a build above.
                    </td>
                  </tr>
                ) : (
                  jobs.map(job => (
                    <JobRow
                      key={job.id}
                      job={job}
                      onDownload={job => void handleJobDownload(job)}
                      downloadingId={downloadingId}
                      jobError={jobError}
                    />
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

// =============================================================================
// Main page
// =============================================================================

export default function CurtinImport() {
  return (
    <div className='p-6 max-w-4xl mx-auto'>
      <h1 className='text-2xl font-bold text-gray-900 mb-1'>Curtin Import</h1>
      <p className='text-gray-600 mb-6'>
        Download unit outlines from LITEC or trigger Blackboard course archive
        exports.
      </p>

      <div className='space-y-6'>
        <OutlineSection />
        <CourseSection />
      </div>
    </div>
  );
}
