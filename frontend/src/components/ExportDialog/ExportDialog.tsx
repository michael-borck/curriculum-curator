import React, { useState, useEffect, useCallback } from 'react';
import { Download, Loader2, Package } from 'lucide-react';
import toast from 'react-hot-toast';
import { Modal, Button } from '../ui';
import MaterialExportRow from './MaterialExportRow';
import { TaskProgressToast } from '../TaskProgress';
import {
  fetchExportPreview,
  startPackageExport,
  type MaterialExportPreview,
  type ExportPackageRequest,
} from '../../services/exportApi';
import { useTaskProgress } from '../../hooks/useTaskProgress';
import { downloadTaskResult } from '../../services/taskApi';

// ─── Types ───────────────────────────────────────────────────────────

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  unitId: string;
}

type PackageType = 'imscc' | 'scorm';

const PACKAGE_OPTIONS: { value: PackageType; label: string }[] = [
  { value: 'imscc', label: 'IMSCC v1.1 (.imscc)' },
  { value: 'scorm', label: 'SCORM 1.2 (.zip)' },
];

const LMS_OPTIONS = [
  { value: 'generic', label: 'Not sure / another LMS' },
  { value: 'canvas', label: 'Canvas' },
  { value: 'moodle', label: 'Moodle' },
  { value: 'blackboard', label: 'Blackboard' },
  { value: 'brightspace', label: 'Brightspace' },
];

// ─── Component ───────────────────────────────────────────────────────

const ExportDialog: React.FC<ExportDialogProps> = ({
  isOpen,
  onClose,
  unitId,
}) => {
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [materials, setMaterials] = useState<MaterialExportPreview[]>([]);
  const [packageType, setPackageType] = useState<PackageType>('imscc');
  const [targetLms, setTargetLms] = useState('generic');
  // Per-material overrides: materialId → { contentType → targets[] }
  const [overrides, setOverrides] = useState<
    Record<string, Record<string, string[]>>
  >({});

  const {
    status: taskStatus,
    start: startTracking,
    stop: stopTracking,
  } = useTaskProgress({
    onComplete: s => {
      setExporting(false);
      const filename = (s.result?.filename as string | undefined) ?? 'export';
      void downloadTaskResult(s.taskId).then(() => {
        toast.success(`Exported: ${filename}`);
      });
    },
    onError: err => {
      setExporting(false);
      toast.error(`Export failed: ${err}`);
    },
  });

  const loadPreview = useCallback(async () => {
    if (!unitId) return;
    try {
      setLoading(true);
      const data = await fetchExportPreview(unitId);
      setMaterials(data.materials);
      setOverrides({});
    } catch {
      toast.error('Failed to load export preview');
    } finally {
      setLoading(false);
    }
  }, [unitId]);

  useEffect(() => {
    if (isOpen) {
      void loadPreview();
    }
  }, [isOpen, loadPreview]);

  // Cleanup tracking when dialog closes
  useEffect(() => {
    if (!isOpen) {
      stopTracking();
    }
  }, [isOpen, stopTracking]);

  const handleOverrideChange = (
    materialId: string,
    targets: Record<string, string[]>
  ) => {
    setOverrides(prev => ({ ...prev, [materialId]: targets }));
  };

  const handleExport = async () => {
    try {
      setExporting(true);

      // Build request with all overrides
      const materialTargets = materials
        .filter(m => overrides[m.materialId])
        .map(m => ({
          materialId: m.materialId,
          targets: overrides[m.materialId],
        }));

      const request: ExportPackageRequest = {
        packageType,
        targetLms,
        materialTargets,
      };

      const taskId = await startPackageExport(unitId, request);
      startTracking(taskId);
      // Close the dialog — the toast will show progress
      onClose();
    } catch {
      setExporting(false);
      toast.error('Export failed');
    }
  };

  // Group materials by week
  const weekNumbers = [...new Set(materials.map(m => m.weekNumber))].sort(
    (a, b) => a - b
  );

  const hasContent = materials.length > 0;

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title='Export or Share This Unit'
        size='2xl'
      >
        <div className='space-y-4'>
          <div className='text-sm text-gray-600 bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2'>
            <p>
              This downloads this unit as a single file. Nothing is sent
              anywhere yet — you then upload that file yourself:
            </p>
            <ul className='list-disc ml-5 space-y-1'>
              <li>
                <strong>To your LMS</strong> (such as Moodle, Canvas, or
                Blackboard): look there for its option to import or restore a
                course package, and choose this file.
              </li>
              <li>
                <strong>To another copy of Curriculum Curator</strong>: use
                Import Package there. The unit&apos;s outcomes, teaching
                approach, and alignment come with it, so this is also how you
                move or share a unit drafted on your own computer.
              </li>
            </ul>
            <p>
              Not sure which file type? Choose IMSCC — it suits most LMSs and
              moving a unit between copies of Curriculum Curator. Choose SCORM
              only if your LMS asks for it.
            </p>
          </div>

          {/* Package options */}
          <div className='flex items-center gap-4'>
            <div className='flex-1'>
              <label className='block text-xs font-medium text-gray-500 mb-1'>
                File type
              </label>
              <select
                value={packageType}
                onChange={e => setPackageType(e.target.value as PackageType)}
                className='w-full text-sm border border-gray-200 rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-purple-400'
              >
                {PACKAGE_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className='flex-1'>
              <label className='block text-xs font-medium text-gray-500 mb-1'>
                Where will you upload it?
              </label>
              <select
                value={targetLms}
                onChange={e => setTargetLms(e.target.value)}
                className='w-full text-sm border border-gray-200 rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-purple-400'
              >
                {LMS_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Materials list */}
          {loading ? (
            <div className='flex items-center justify-center py-12'>
              <Loader2 className='w-6 h-6 animate-spin text-purple-500' />
              <span className='ml-2 text-sm text-gray-500'>
                Loading materials...
              </span>
            </div>
          ) : !hasContent ? (
            <div className='text-center py-12 text-gray-400'>
              <Package className='w-10 h-10 mx-auto mb-2 opacity-50' />
              <p className='text-sm'>No materials to export.</p>
            </div>
          ) : (
            <div className='border border-gray-200 rounded-lg divide-y divide-gray-100 max-h-[50vh] overflow-y-auto'>
              {weekNumbers.map(week => {
                const weekMaterials = materials.filter(
                  m => m.weekNumber === week
                );
                return (
                  <div key={week}>
                    <div className='px-3 py-1.5 bg-gray-50 text-xs font-medium text-gray-500 sticky top-0'>
                      Week {week}
                    </div>
                    {weekMaterials.map(mat => (
                      <MaterialExportRow
                        key={mat.materialId}
                        material={mat}
                        overrides={overrides[mat.materialId] ?? {}}
                        onOverrideChange={handleOverrideChange}
                      />
                    ))}
                  </div>
                );
              })}
            </div>
          )}

          {/* Footer */}
          <div className='flex items-center justify-end gap-3 pt-2 border-t border-gray-100'>
            <Button variant='secondary' size='sm' onClick={onClose}>
              Cancel
            </Button>
            <Button
              size='sm'
              onClick={() => void handleExport()}
              loading={exporting}
              disabled={!hasContent || loading}
            >
              <Download className='w-4 h-4 mr-1' />
              Download file
            </Button>
          </div>
        </div>
      </Modal>

      {/* Progress toast (shown after dialog closes) */}
      {taskStatus && taskStatus.status !== 'pending' && (
        <TaskProgressToast status={taskStatus} onDismiss={stopTracking} />
      )}
    </>
  );
};

export default ExportDialog;
