import React, { useState } from 'react';
import { Download, FileStack, Loader2, Star } from 'lucide-react';
import toast from 'react-hot-toast';
import {
  downloadSourceFile,
  promoteSourceFile,
  type AttachedSourceFile,
} from '../../services/materialImportApi';

interface SourceFilesPanelProps {
  materialId: string;
  /** Raw material_metadata.attached_source_files (snake_case keys passthrough). */
  sourceFiles: AttachedSourceFile[];
  /** Called after a promote so the parent can reload the material's content. */
  onPromoted: () => void;
}

function formatSize(bytes: number | undefined): string {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Lists the source files attached to a material (the non-canonical members
 * of a multi-format import group). Each is downloadable as-is, and can be
 * promoted to become the material's editable content (Mode B, story 6.15).
 */
const SourceFilesPanel: React.FC<SourceFilesPanelProps> = ({
  materialId,
  sourceFiles,
  onPromoted,
}) => {
  const [busy, setBusy] = useState<string | null>(null);

  if (sourceFiles.length === 0) return null;

  const handleDownload = async (filename: string) => {
    try {
      await downloadSourceFile(materialId, filename);
    } catch {
      toast.error('Failed to download source file');
    }
  };

  const handlePromote = async (filename: string) => {
    if (
      !window.confirm(
        `Replace this material's editable content with the parsed contents of ${filename}? Your current content will be overwritten.`
      )
    ) {
      return;
    }
    setBusy(filename);
    try {
      await promoteSourceFile(materialId, filename);
      toast.success(`Promoted ${filename} to editable content`);
      onPromoted();
    } catch {
      toast.error('Failed to promote source file');
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className='mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3'>
      <div className='flex items-center gap-2 text-sm font-medium text-gray-700 mb-2'>
        <FileStack className='w-4 h-4 text-gray-400' />
        Source files
      </div>
      <p className='text-xs text-gray-500 mb-2'>
        Other formats imported alongside this material. Download them as-is, or
        promote one to become the editable content.
      </p>
      <ul className='space-y-1.5'>
        {sourceFiles.map(sf => {
          const fmt = sf.fileFormat ?? sf.file_format;
          const size = sf.originalSize ?? sf.original_size;
          return (
            <li
              key={sf.filename}
              className='flex items-center justify-between gap-3 bg-white border border-gray-100 rounded px-2.5 py-1.5'
            >
              <span className='min-w-0 text-sm text-gray-700 truncate'>
                {sf.filename}
                <span className='ml-2 text-xs text-gray-400'>
                  {fmt ? fmt.toUpperCase() : ''}
                  {size ? ` · ${formatSize(size)}` : ''}
                </span>
              </span>
              <span className='flex items-center gap-1 shrink-0'>
                <button
                  onClick={() => handleDownload(sf.filename)}
                  className='p-1 text-gray-400 hover:text-emerald-600'
                  title='Download'
                >
                  <Download className='w-4 h-4' />
                </button>
                <button
                  onClick={() => handlePromote(sf.filename)}
                  disabled={busy !== null}
                  className='p-1 text-gray-400 hover:text-purple-600 disabled:opacity-50'
                  title='Promote to editable content'
                >
                  {busy === sf.filename ? (
                    <Loader2 className='w-4 h-4 animate-spin' />
                  ) : (
                    <Star className='w-4 h-4' />
                  )}
                </button>
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default SourceFilesPanel;
