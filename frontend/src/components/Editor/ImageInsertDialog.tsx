import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Link, Loader2, ImagePlus } from 'lucide-react';
import { Modal } from '../ui/Modal';
import { uploadMaterialImage } from '../../services/api';
import toast from 'react-hot-toast';

interface ImageInsertDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onInsert: (src: string, alt: string) => void;
  unitId?: string | undefined;
  materialId?: string | undefined;
}

type Tab = 'upload' | 'url';

const ImageInsertDialog = ({
  isOpen,
  onClose,
  onInsert,
  unitId,
  materialId,
}: ImageInsertDialogProps) => {
  const canUpload = Boolean(unitId && materialId);
  const [activeTab, setActiveTab] = useState<Tab>(canUpload ? 'upload' : 'url');
  const [url, setUrl] = useState('');
  const [alt, setAlt] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const resetState = useCallback(() => {
    setUrl('');
    setAlt('');
    setPreview(null);
    setSelectedFile(null);
    setIsUploading(false);
    setActiveTab(canUpload ? 'upload' : 'url');
  }, [canUpload]);

  const handleClose = useCallback(() => {
    resetState();
    onClose();
  }, [resetState, onClose]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setSelectedFile(file);

      // Generate preview
      const reader = new FileReader();
      reader.onload = e => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);

      // Pre-fill alt from filename
      if (!alt) {
        const stem = file.name.replace(/\.[^.]+$/, '').replace(/[-_]/g, ' ');
        setAlt(stem);
      }
    },
    [alt]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/gif': ['.gif'],
      'image/svg+xml': ['.svg'],
      'image/webp': ['.webp'],
    },
    maxSize: 5 * 1024 * 1024,
    multiple: false,
    onDropRejected: rejections => {
      const err = rejections[0]?.errors[0];
      if (err?.code === 'file-too-large') {
        toast.error('Image must be under 5MB');
      } else if (err?.code === 'file-invalid-type') {
        toast.error('Only PNG, JPG, GIF, SVG, and WebP images are supported');
      } else {
        toast.error('Invalid file');
      }
    },
  });

  const handleUpload = async () => {
    if (!selectedFile || !unitId || !materialId) return;

    setIsUploading(true);
    try {
      const response = await uploadMaterialImage(
        unitId,
        materialId,
        selectedFile
      );
      const { url: imageUrl } = response.data;
      onInsert(imageUrl, alt);
      handleClose();
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error('Failed to upload image');
    } finally {
      setIsUploading(false);
    }
  };

  const handleUrlInsert = () => {
    if (!url.trim()) {
      toast.error('Please enter an image URL');
      return;
    }
    onInsert(url.trim(), alt);
    handleClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title='Insert Image' size='lg'>
      {/* Tabs */}
      {canUpload && (
        <div className='flex border-b border-gray-200 mb-4'>
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === 'upload'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Upload size={16} className='inline mr-1.5 -mt-0.5' />
            Upload
          </button>
          <button
            onClick={() => setActiveTab('url')}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === 'url'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Link size={16} className='inline mr-1.5 -mt-0.5' />
            URL
          </button>
        </div>
      )}

      {/* Upload Tab */}
      {activeTab === 'upload' && canUpload && (
        <div className='space-y-4'>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-purple-400 bg-purple-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            {preview ? (
              <div className='space-y-3'>
                <img
                  src={preview}
                  alt='Preview'
                  className='max-h-48 mx-auto rounded'
                />
                <p className='text-sm text-gray-500'>
                  {selectedFile?.name} — click or drop to replace
                </p>
              </div>
            ) : (
              <div className='space-y-2'>
                <ImagePlus size={40} className='mx-auto text-gray-400' />
                <p className='text-gray-600'>
                  {isDragActive
                    ? 'Drop your image here'
                    : 'Drag & drop an image, or click to browse'}
                </p>
                <p className='text-xs text-gray-400'>
                  PNG, JPG, GIF, SVG, WebP — max 5MB
                </p>
              </div>
            )}
          </div>

          <div>
            <label
              htmlFor='upload-alt'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Alt text
            </label>
            <input
              id='upload-alt'
              type='text'
              value={alt}
              onChange={e => setAlt(e.target.value)}
              placeholder='Describe this image...'
              className='w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
            />
          </div>

          <button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className='w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center gap-2'
          >
            {isUploading ? (
              <>
                <Loader2 size={18} className='animate-spin' />
                Uploading...
              </>
            ) : (
              <>
                <Upload size={18} />
                Upload & Insert
              </>
            )}
          </button>
        </div>
      )}

      {/* URL Tab */}
      {activeTab === 'url' && (
        <div className='space-y-4'>
          <div>
            <label
              htmlFor='image-url'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Image URL
            </label>
            <input
              id='image-url'
              type='url'
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder='https://example.com/image.png'
              className='w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
            />
          </div>

          <div>
            <label
              htmlFor='url-alt'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Alt text
            </label>
            <input
              id='url-alt'
              type='text'
              value={alt}
              onChange={e => setAlt(e.target.value)}
              placeholder='Describe this image...'
              className='w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
            />
          </div>

          <button
            onClick={handleUrlInsert}
            disabled={!url.trim()}
            className='w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center gap-2'
          >
            <ImagePlus size={18} />
            Insert Image
          </button>
        </div>
      )}
    </Modal>
  );
};

export default ImageInsertDialog;
