import { useCallback, useEffect, useRef, useState } from 'react';
import { Upload, Trash2, FileText, Presentation, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import {
  exportTemplateApi,
  type TemplateInfo,
} from '../../services/exportTemplateApi';

interface FormatCardProps {
  format: string;
  label: string;
  icon: React.ReactNode;
  accept: string;
  template: TemplateInfo | undefined;
  onUpload: (file: File) => Promise<void>;
  onRemove: (id: string) => Promise<void>;
  uploading: boolean;
}

const FormatCard: React.FC<FormatCardProps> = ({
  format,
  label,
  icon,
  accept,
  template,
  onUpload,
  onRemove,
  uploading,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext !== format) {
        toast.error(`Please upload a .${format} file`);
        return;
      }
      void onUpload(file);
    },
    [format, onUpload]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      className={`border rounded-lg p-4 transition ${
        dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-200'
      }`}
      onDragOver={e => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      <div className='flex items-center gap-2 mb-3'>
        {icon}
        <h3 className='font-medium text-gray-800'>{label}</h3>
      </div>

      {template ? (
        <div className='flex items-center justify-between'>
          <div className='min-w-0'>
            <p className='text-sm font-medium text-gray-700 truncate'>
              {template.filename}
            </p>
            <p className='text-xs text-gray-500'>
              Uploaded{' '}
              {new Date(template.uploadedAt).toLocaleDateString('en-AU', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
              })}
            </p>
          </div>
          <button
            onClick={() => void onRemove(template.id)}
            className='ml-3 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-md transition flex items-center gap-1'
          >
            <Trash2 className='h-3.5 w-3.5' />
            Remove
          </button>
        </div>
      ) : (
        <div>
          <input
            ref={inputRef}
            type='file'
            accept={accept}
            className='hidden'
            onChange={e => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
              // Reset so re-uploading same file triggers onChange
              e.target.value = '';
            }}
          />
          <button
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
            className='w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:border-blue-400 hover:text-blue-600 transition flex items-center justify-center gap-2 disabled:opacity-50'
          >
            {uploading ? (
              <Loader2 className='h-4 w-4 animate-spin' />
            ) : (
              <Upload className='h-4 w-4' />
            )}
            {uploading ? 'Uploading...' : `Upload .${format} template`}
          </button>
        </div>
      )}
    </div>
  );
};

const ExportTemplates: React.FC = () => {
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const loadTemplates = useCallback(async () => {
    try {
      const { data } = await exportTemplateApi.list();
      setTemplates(data.templates);
    } catch {
      toast.error('Failed to load export templates');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTemplates();
  }, [loadTemplates]);

  const handleUpload = useCallback(
    async (file: File) => {
      setUploading(true);
      try {
        await exportTemplateApi.upload(file);
        toast.success('Template uploaded');
        await loadTemplates();
      } catch {
        toast.error('Failed to upload template');
      } finally {
        setUploading(false);
      }
    },
    [loadTemplates]
  );

  const handleRemove = useCallback(
    async (id: string) => {
      try {
        await exportTemplateApi.remove(id);
        toast.success('Template removed');
        await loadTemplates();
      } catch {
        toast.error('Failed to remove template');
      }
    },
    [loadTemplates]
  );

  const pptxTemplate = templates.find(t => t.format === 'pptx' && t.isDefault);
  const docxTemplate = templates.find(t => t.format === 'docx' && t.isDefault);

  if (loading) {
    return (
      <div className='bg-white rounded-lg shadow-md p-6 flex items-center justify-center h-40'>
        <Loader2 className='animate-spin text-blue-600' size={32} />
      </div>
    );
  }

  return (
    <div className='bg-white rounded-lg shadow-md p-6'>
      <h2 className='text-xl font-semibold mb-2'>Export Templates</h2>
      <p className='text-sm text-gray-600 mb-6'>
        Upload reference documents used to style PPTX and DOCX exports.
        Templates control fonts, colours, and slide layouts.
      </p>

      <div className='space-y-4'>
        <FormatCard
          format='pptx'
          label='Presentations (.pptx)'
          icon={<Presentation className='h-5 w-5 text-orange-500' />}
          accept='.pptx'
          template={pptxTemplate}
          onUpload={handleUpload}
          onRemove={handleRemove}
          uploading={uploading}
        />

        <FormatCard
          format='docx'
          label='Documents (.docx)'
          icon={<FileText className='h-5 w-5 text-blue-500' />}
          accept='.docx'
          template={docxTemplate}
          onUpload={handleUpload}
          onRemove={handleRemove}
          uploading={uploading}
        />
      </div>

      <p className='text-xs text-gray-400 mt-4'>
        Exports without a template use Pandoc defaults.
      </p>
    </div>
  );
};

export default ExportTemplates;
