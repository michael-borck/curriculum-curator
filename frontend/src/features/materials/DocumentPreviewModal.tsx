import { useState, useEffect, useRef, useCallback } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { contentApi } from '../../services/contentApi';
import type { ExportAvailability } from '../../services/contentApi';

type PreviewFormat = 'pdf' | 'html';

interface DocumentPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  contentId: string;
  contentTitle: string;
  availability: ExportAvailability;
}

const DocumentPreviewModal: React.FC<DocumentPreviewModalProps> = ({
  isOpen,
  onClose,
  contentId,
  contentTitle,
  availability,
}) => {
  const defaultFormat: PreviewFormat = availability.pdfAvailable
    ? 'pdf'
    : 'html';
  const [format, setFormat] = useState<PreviewFormat>(defaultFormat);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const blobUrlRef = useRef<string | null>(null);

  const revokeBlobUrl = useCallback(() => {
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!isOpen) {
      revokeBlobUrl();
      setBlobUrl(null);
      setError(null);
      return;
    }

    let cancelled = false;

    const fetchPreview = async () => {
      setLoading(true);
      setError(null);
      revokeBlobUrl();
      setBlobUrl(null);

      try {
        const { data } = await contentApi.exportDocumentBlob(
          contentId,
          format,
          contentTitle
        );
        if (cancelled) return;
        const url = URL.createObjectURL(data);
        blobUrlRef.current = url;
        setBlobUrl(url);
      } catch (err) {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : 'Export failed';
        setError(message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchPreview();

    return () => {
      cancelled = true;
    };
  }, [isOpen, format, contentId, contentTitle, revokeBlobUrl]);

  // Cleanup on unmount
  useEffect(() => revokeBlobUrl, [revokeBlobUrl]);

  const formatButtons: {
    fmt: PreviewFormat;
    label: string;
    available: boolean;
  }[] = [
    { fmt: 'pdf', label: 'PDF', available: availability.pdfAvailable },
    { fmt: 'html', label: 'HTML', available: availability.htmlAvailable },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title='Document Preview'
      size='2xl'
    >
      {/* Format toggle */}
      <div className='flex items-center gap-2 mb-4'>
        {formatButtons.map(({ fmt, label, available }) => (
          <button
            key={fmt}
            onClick={() => setFormat(fmt)}
            disabled={!available}
            className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
              format === fmt
                ? 'bg-blue-600 text-white'
                : available
                  ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  : 'bg-gray-50 text-gray-400 cursor-not-allowed'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Content area */}
      <div className='w-full h-[70vh] border border-gray-200 rounded-lg overflow-hidden bg-gray-50'>
        {loading && (
          <div className='flex flex-col items-center justify-center h-full gap-3'>
            <Loader2 className='h-8 w-8 animate-spin text-blue-600' />
            <p className='text-sm text-gray-500'>
              Rendering {format.toUpperCase()}...
            </p>
          </div>
        )}

        {error && !loading && (
          <div className='flex flex-col items-center justify-center h-full gap-3 px-6 text-center'>
            <AlertCircle className='h-8 w-8 text-red-500' />
            <p className='text-sm text-red-600'>{error}</p>
            <p className='text-xs text-gray-500'>
              Make sure Pandoc and Typst are installed on the server.
            </p>
          </div>
        )}

        {blobUrl && !loading && !error && (
          <iframe
            src={blobUrl}
            title={`${contentTitle} preview`}
            className='w-full h-full'
            sandbox={format === 'html' ? 'allow-same-origin' : undefined}
          />
        )}
      </div>
    </Modal>
  );
};

export default DocumentPreviewModal;
