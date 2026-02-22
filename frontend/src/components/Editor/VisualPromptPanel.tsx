import { useState } from 'react';
import {
  X,
  Copy,
  Check,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Camera,
  Paintbrush,
  GitBranch,
  Layers,
  Droplets,
  Box,
} from 'lucide-react';
import { generateVisualPrompt } from '../../services/api';
import type {
  VisualPromptStyle,
  VisualPromptAspectRatio,
  VisualPromptResponse,
} from '../../types/index';

interface VisualPromptPanelProps {
  isOpen: boolean;
  onClose: () => void;
  selectedText: string;
}

const STYLES: {
  value: VisualPromptStyle;
  label: string;
  icon: React.ReactNode;
}[] = [
  { value: 'photographic', label: 'Photo', icon: <Camera size={18} /> },
  {
    value: 'illustration',
    label: 'Illustration',
    icon: <Paintbrush size={18} />,
  },
  { value: 'diagram', label: 'Diagram', icon: <GitBranch size={18} /> },
  { value: 'flat-vector', label: 'Flat Vector', icon: <Layers size={18} /> },
  { value: 'watercolor', label: 'Watercolour', icon: <Droplets size={18} /> },
  { value: '3d-render', label: '3D Render', icon: <Box size={18} /> },
];

const ASPECT_RATIOS: { value: VisualPromptAspectRatio; label: string }[] = [
  { value: 'square', label: 'Square' },
  { value: 'landscape', label: 'Landscape' },
  { value: 'portrait', label: 'Portrait' },
];

const VisualPromptPanel: React.FC<VisualPromptPanelProps> = ({
  isOpen,
  onClose,
  selectedText,
}) => {
  const [content, setContent] = useState(selectedText);
  const [style, setStyle] = useState<VisualPromptStyle>('photographic');
  const [aspectRatio, setAspectRatio] =
    useState<VisualPromptAspectRatio>('landscape');
  const [context, setContext] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VisualPromptResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [showNegative, setShowNegative] = useState(false);
  const [error, setError] = useState('');

  // Sync selectedText when panel opens with new selection
  const [lastSelectedText, setLastSelectedText] = useState(selectedText);
  if (selectedText !== lastSelectedText) {
    setLastSelectedText(selectedText);
    setContent(selectedText);
  }

  const handleGenerate = async () => {
    if (!content.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await generateVisualPrompt({
        content: content.trim(),
        style,
        aspectRatio,
        context: context.trim() || undefined,
      });
      setResult(response);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to generate prompt'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className='fixed inset-y-0 right-0 w-[400px] bg-white shadow-xl border-l border-gray-200 z-50 flex flex-col'>
      {/* Header */}
      <div className='flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50'>
        <h2 className='text-sm font-semibold text-gray-800'>
          Visual Prompt Generator
        </h2>
        <button
          onClick={onClose}
          className='p-1 rounded hover:bg-gray-200 text-gray-500'
        >
          <X size={18} />
        </button>
      </div>

      {/* Scrollable body */}
      <div className='flex-1 overflow-y-auto p-4 space-y-4'>
        {/* Content input */}
        <div>
          <label className='block text-xs font-medium text-gray-600 mb-1'>
            Content
          </label>
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            placeholder='Paste or type the content to visualise...'
            rows={4}
            className='w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-y'
          />
        </div>

        {/* Style selector */}
        <div>
          <label className='block text-xs font-medium text-gray-600 mb-1'>
            Style
          </label>
          <div className='grid grid-cols-3 gap-2'>
            {STYLES.map(s => (
              <button
                key={s.value}
                onClick={() => setStyle(s.value)}
                className={`flex flex-col items-center gap-1 p-2 rounded-md border text-xs transition-colors ${
                  style === s.value
                    ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                    : 'border-gray-200 hover:border-gray-300 text-gray-600'
                }`}
              >
                {s.icon}
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Aspect ratio */}
        <div>
          <label className='block text-xs font-medium text-gray-600 mb-1'>
            Aspect Ratio
          </label>
          <div className='flex gap-2'>
            {ASPECT_RATIOS.map(ar => (
              <label
                key={ar.value}
                className={`flex-1 text-center px-3 py-1.5 rounded-md border text-xs cursor-pointer transition-colors ${
                  aspectRatio === ar.value
                    ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                    : 'border-gray-200 hover:border-gray-300 text-gray-600'
                }`}
              >
                <input
                  type='radio'
                  name='aspectRatio'
                  value={ar.value}
                  checked={aspectRatio === ar.value}
                  onChange={() => setAspectRatio(ar.value)}
                  className='sr-only'
                />
                {ar.label}
              </label>
            ))}
          </div>
        </div>

        {/* Context */}
        <div>
          <label className='block text-xs font-medium text-gray-600 mb-1'>
            Context{' '}
            <span className='text-gray-400 font-normal'>(optional)</span>
          </label>
          <input
            type='text'
            value={context}
            onChange={e => setContext(e.target.value)}
            placeholder='e.g. hero image for week 3'
            className='w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400'
          />
        </div>

        {/* Generate button */}
        <button
          onClick={handleGenerate}
          disabled={loading || !content.trim()}
          className='w-full flex items-center justify-center gap-2 bg-indigo-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
        >
          {loading ? (
            <>
              <Loader2 size={16} className='animate-spin' />
              Generating...
            </>
          ) : (
            'Generate Prompt'
          )}
        </button>

        {/* Error */}
        {error && (
          <div className='text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-3'>
            {error}
          </div>
        )}

        {/* Result */}
        {result && (
          <div className='space-y-3'>
            {/* Main prompt */}
            <div>
              <div className='flex items-center justify-between mb-1'>
                <label className='text-xs font-medium text-gray-600'>
                  Prompt
                </label>
                <button
                  onClick={() => handleCopy(result.prompt)}
                  className='flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800'
                >
                  {copied ? <Check size={14} /> : <Copy size={14} />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
              <div className='bg-gray-50 border border-gray-200 rounded-md p-3 text-sm text-gray-800 leading-relaxed'>
                {result.prompt}
              </div>
            </div>

            {/* Negative prompt (collapsible) */}
            <div>
              <button
                onClick={() => setShowNegative(!showNegative)}
                className='flex items-center gap-1 text-xs font-medium text-gray-600 hover:text-gray-800'
              >
                {showNegative ? (
                  <ChevronUp size={14} />
                ) : (
                  <ChevronDown size={14} />
                )}
                Negative Prompt
              </button>
              {showNegative && (
                <div className='mt-1 bg-gray-50 border border-gray-200 rounded-md p-3 text-sm text-gray-600'>
                  {result.negativePrompt}
                </div>
              )}
            </div>

            {/* Style notes */}
            <div className='bg-amber-50 border border-amber-200 rounded-md p-3 text-xs text-amber-800'>
              <span className='font-medium'>Tip:</span> {result.styleNotes}
            </div>

            {/* Regenerate */}
            <button
              onClick={handleGenerate}
              disabled={loading}
              className='flex items-center gap-1 text-xs text-gray-500 hover:text-indigo-600'
            >
              <RefreshCw size={14} />
              Regenerate
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default VisualPromptPanel;
