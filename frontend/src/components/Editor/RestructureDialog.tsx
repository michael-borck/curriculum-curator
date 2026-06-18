import React, { useState } from 'react';
import { Loader2, Sparkles, Wand2, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { aiApi, type RestructureContentResponse } from '../../services/aiApi';

interface RestructureDialogProps {
  materialId: string;
  /** Rough token estimate of the current content, shown before running. */
  estimatedTokens: number;
  onApply: (contentJson: Record<string, unknown>) => void;
  onClose: () => void;
}

type Stage = 'confirm' | 'working' | 'review';

/**
 * Propose/apply flow for AI structure recovery (story 6.16). Shows a cost
 * estimate, runs the restructure endpoint on the material's existing text,
 * and previews what was recovered (headings/lists/paragraphs) before the
 * user applies. Nothing changes until Apply.
 */
const RestructureDialog: React.FC<RestructureDialogProps> = ({
  materialId,
  estimatedTokens,
  onApply,
  onClose,
}) => {
  const [stage, setStage] = useState<Stage>('confirm');
  const [result, setResult] = useState<RestructureContentResponse | null>(null);

  const handleRun = async () => {
    setStage('working');
    try {
      const { data } = await aiApi.restructureContent(materialId);
      setResult(data);
      setStage('review');
    } catch {
      toast.error('Failed to restructure content');
      setStage('confirm');
    }
  };

  const handleApply = () => {
    if (result) onApply(result.contentJson);
    onClose();
  };

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
      <div className='bg-white rounded-xl shadow-xl w-full max-w-lg'>
        <div className='flex items-center justify-between px-5 py-3 border-b border-gray-100'>
          <h2 className='font-semibold text-gray-900 flex items-center gap-2'>
            <Wand2 className='w-4 h-4 text-purple-500' />
            Improve structure with AI
          </h2>
          <button
            onClick={onClose}
            className='p-1 text-gray-400 hover:text-gray-600'
            title='Close'
          >
            <X className='w-4 h-4' />
          </button>
        </div>

        <div className='px-5 py-4'>
          {stage === 'confirm' && (
            <div className='space-y-3 text-sm text-gray-600'>
              <p>
                This material looks like plain paragraphs (typical of a PDF
                import). AI will re-segment the existing text into headings and
                lists — it won&apos;t add, remove, or reword content.
                You&apos;ll review the result before anything is applied.
              </p>
              <p className='text-xs text-gray-400'>
                Roughly {estimatedTokens.toLocaleString()} input tokens will be
                sent to your configured AI provider.
              </p>
            </div>
          )}

          {stage === 'working' && (
            <div className='flex flex-col items-center justify-center py-8 text-gray-500'>
              <Loader2 className='w-6 h-6 animate-spin mb-3' />
              <p className='text-sm'>Recovering structure…</p>
            </div>
          )}

          {stage === 'review' && result && (
            <div className='space-y-2 text-sm text-gray-700'>
              <p className='flex items-center gap-2'>
                <Sparkles className='w-4 h-4 text-purple-500' />
                Recovered structure:
              </p>
              <ul className='list-disc list-inside text-gray-600'>
                <li>{result.headingCount} heading(s)</li>
                <li>{result.listCount} list(s)</li>
                <li>{result.paragraphCount} paragraph(s)</li>
              </ul>
              <p className='text-xs text-gray-400'>
                Applying replaces the editor content. Remember to save
                afterwards — and you can undo in the editor if needed.
              </p>
            </div>
          )}
        </div>

        <div className='flex items-center justify-end gap-3 px-5 py-3 border-t border-gray-100'>
          <button
            onClick={onClose}
            className='px-4 py-2 text-sm text-gray-600 hover:text-gray-800'
          >
            Cancel
          </button>
          {stage === 'confirm' && (
            <button
              onClick={handleRun}
              className='flex items-center gap-2 px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700'
            >
              <Wand2 className='w-4 h-4' />
              Improve structure
            </button>
          )}
          {stage === 'review' && (
            <button
              onClick={handleApply}
              className='px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700'
            >
              Apply
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default RestructureDialog;
