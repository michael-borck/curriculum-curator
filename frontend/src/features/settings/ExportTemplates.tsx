import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Upload,
  Trash2,
  FileText,
  Presentation,
  Loader2,
  Star,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  exportTemplateApi,
  type TemplateInfo,
} from '../../services/exportTemplateApi';

interface FormatSectionProps {
  format: string;
  label: string;
  icon: React.ReactNode;
  accept: string;
  templates: TemplateInfo[];
  onUpload: (file: File) => Promise<void>;
  onRemove: (id: string) => Promise<void>;
  onSetDefault: (id: string) => Promise<void>;
  uploading: boolean;
}

const FormatSection: React.FC<FormatSectionProps> = ({
  format,
  label,
  icon,
  accept,
  templates,
  onUpload,
  onRemove,
  onSetDefault,
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
      <div className='flex items-center justify-between mb-3'>
        <div className='flex items-center gap-2'>
          {icon}
          <h3 className='font-medium text-gray-800'>{label}</h3>
          <span className='text-xs text-gray-400'>
            {templates.length} template{templates.length !== 1 ? 's' : ''}
          </span>
        </div>
        <div>
          <input
            ref={inputRef}
            type='file'
            accept={accept}
            className='hidden'
            onChange={e => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
              e.target.value = '';
            }}
          />
          <button
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
            className='px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-md transition flex items-center gap-1 disabled:opacity-50'
          >
            {uploading ? (
              <Loader2 className='h-3.5 w-3.5 animate-spin' />
            ) : (
              <Upload className='h-3.5 w-3.5' />
            )}
            Upload
          </button>
        </div>
      </div>

      {templates.length === 0 ? (
        <p className='text-sm text-gray-400 py-2'>
          No templates yet. Upload a .{format} file to use as a reference for
          exports.
        </p>
      ) : (
        <div className='space-y-2'>
          {templates.map(t => (
            <div
              key={t.id}
              className={`flex items-center justify-between py-2 px-3 rounded-md ${
                t.isDefault ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'
              }`}
            >
              <div className='min-w-0 flex-1'>
                <div className='flex items-center gap-2'>
                  <p className='text-sm font-medium text-gray-700 truncate'>
                    {t.filename}
                  </p>
                  {t.isDefault && (
                    <span className='text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-medium flex-shrink-0'>
                      Default
                    </span>
                  )}
                </div>
                <p className='text-xs text-gray-500'>
                  {new Date(t.uploadedAt).toLocaleDateString('en-AU', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                  })}
                </p>
              </div>
              <div className='flex items-center gap-1 ml-3'>
                {!t.isDefault && (
                  <button
                    onClick={() => void onSetDefault(t.id)}
                    title='Set as default'
                    className='p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition'
                  >
                    <Star className='h-3.5 w-3.5' />
                  </button>
                )}
                <button
                  onClick={() => void onRemove(t.id)}
                  title='Remove template'
                  className='p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition'
                >
                  <Trash2 className='h-3.5 w-3.5' />
                </button>
              </div>
            </div>
          ))}
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

  const handleSetDefault = useCallback(
    async (id: string) => {
      try {
        await exportTemplateApi.setDefault(id);
        toast.success('Default template updated');
        await loadTemplates();
      } catch {
        toast.error('Failed to set default template');
      }
    },
    [loadTemplates]
  );

  const pptxTemplates = templates.filter(t => t.format === 'pptx');
  const docxTemplates = templates.filter(t => t.format === 'docx');

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
        Templates control fonts, colours, and layouts. The default template is
        used automatically when exporting.
      </p>

      <div className='space-y-4'>
        <FormatSection
          format='pptx'
          label='Presentations (.pptx)'
          icon={<Presentation className='h-5 w-5 text-orange-500' />}
          accept='.pptx'
          templates={pptxTemplates}
          onUpload={handleUpload}
          onRemove={handleRemove}
          onSetDefault={handleSetDefault}
          uploading={uploading}
        />

        <FormatSection
          format='docx'
          label='Documents (.docx)'
          icon={<FileText className='h-5 w-5 text-blue-500' />}
          accept='.docx'
          templates={docxTemplates}
          onUpload={handleUpload}
          onRemove={handleRemove}
          onSetDefault={handleSetDefault}
          uploading={uploading}
        />
      </div>

      <p className='text-xs text-gray-400 mt-4'>
        Exports without a template use Pandoc defaults. Templates can also be
        extracted automatically when importing PPTX or DOCX files.
      </p>
    </div>
  );
};

export default ExportTemplates;
