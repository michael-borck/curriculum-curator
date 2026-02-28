import React, { useState } from 'react';
import { X, Upload, Youtube } from 'lucide-react';
import {
  transcriptApi,
  type TranscriptSegment,
} from '../../services/transcriptApi';

interface TranscriptLoadDialogProps {
  videoUrl: string;
  onClose: () => void;
  onLoaded: (segments: TranscriptSegment[]) => void;
}

type TabId = 'youtube' | 'upload';

const TranscriptLoadDialog: React.FC<TranscriptLoadDialogProps> = ({
  videoUrl,
  onClose,
  onLoaded,
}) => {
  const [activeTab, setActiveTab] = useState<TabId>(
    videoUrl && /youtube|youtu\.be/i.test(videoUrl) ? 'youtube' : 'upload'
  );
  const [ytUrl, setYtUrl] = useState(videoUrl || '');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFetchYoutube = async () => {
    if (!ytUrl.trim()) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await transcriptApi.fetchYoutube(ytUrl.trim());
      if (!data.segments.length) {
        setError('No transcript segments found for this video.');
        return;
      }
      onLoaded(data.segments);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : 'Failed to fetch transcript';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await transcriptApi.parseVtt(file);
      if (!data.segments.length) {
        setError('No transcript segments found in the file.');
        return;
      }
      onLoaded(data.segments);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : 'Failed to parse subtitle file';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    e.stopPropagation();
    if (e.key === 'Escape') onClose();
  };

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40'>
      <div
        className='bg-white rounded-lg shadow-xl w-full max-w-md mx-4'
        onKeyDown={handleKeyDown}
      >
        {/* Header */}
        <div className='flex items-center justify-between px-4 py-3 border-b'>
          <h3 className='text-sm font-medium text-gray-800'>Load Transcript</h3>
          <button
            type='button'
            onClick={onClose}
            className='text-gray-400 hover:text-gray-600'
          >
            <X size={18} />
          </button>
        </div>

        {/* Tabs */}
        <div className='flex border-b'>
          <button
            type='button'
            onClick={() => setActiveTab('youtube')}
            className={`flex-1 px-4 py-2 text-sm font-medium flex items-center justify-center gap-1.5 ${
              activeTab === 'youtube'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Youtube size={14} />
            YouTube
          </button>
          <button
            type='button'
            onClick={() => setActiveTab('upload')}
            className={`flex-1 px-4 py-2 text-sm font-medium flex items-center justify-center gap-1.5 ${
              activeTab === 'upload'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Upload size={14} />
            Upload VTT/SRT
          </button>
        </div>

        {/* Content */}
        <div className='p-4 space-y-3'>
          {activeTab === 'youtube' && (
            <>
              <input
                type='text'
                value={ytUrl}
                onChange={e => setYtUrl(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder='https://www.youtube.com/watch?v=...'
                className='w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400'
              />
              <button
                type='button'
                onClick={handleFetchYoutube}
                disabled={loading || !ytUrl.trim()}
                className='w-full px-4 py-2 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed'
              >
                {loading ? 'Fetching…' : 'Fetch Transcript'}
              </button>
            </>
          )}

          {activeTab === 'upload' && (
            <>
              <div className='border-2 border-dashed border-gray-300 rounded-lg p-4 text-center'>
                <input
                  type='file'
                  accept='.vtt,.srt'
                  onChange={e => setFile(e.target.files?.[0] || null)}
                  className='text-sm text-gray-600'
                />
                {file && (
                  <p className='text-xs text-gray-500 mt-1'>{file.name}</p>
                )}
              </div>
              <button
                type='button'
                onClick={handleUpload}
                disabled={loading || !file}
                className='w-full px-4 py-2 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed'
              >
                {loading ? 'Parsing…' : 'Parse & Load'}
              </button>
            </>
          )}

          {error && (
            <p className='text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2'>
              {error}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default TranscriptLoadDialog;
