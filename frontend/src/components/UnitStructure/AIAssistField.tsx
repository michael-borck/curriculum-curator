import React, { useState } from 'react';
import { Sparkles, Loader2, X } from 'lucide-react';
import api from '../../services/api';

interface AIAssistFieldProps {
  /** Current field value to provide context for improve/suggest */
  currentValue?: string | undefined;
  /** What kind of content this is (e.g. "ULO description", "assessment title") */
  fieldLabel: string;
  /** Extra context to include in the prompt (e.g. unit name, bloom level) */
  context?: string | undefined;
  /** Called when user accepts generated text */
  onAccept: (text: string) => void;
}

type ActionType = 'generate' | 'improve' | 'suggest';

const AIAssistField: React.FC<AIAssistFieldProps> = ({
  currentValue,
  fieldLabel,
  context,
  onAccept,
}) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAction = async (action: ActionType) => {
    setLoading(true);
    setError(null);
    setResult(null);

    const prompts: Record<ActionType, string> = {
      generate: `Generate a concise, professional ${fieldLabel} for a university unit.${context ? ` Context: ${context}` : ''} Return only the text, no extra formatting.`,
      improve: `Improve the following ${fieldLabel}. Make it clearer, more specific, and aligned with academic standards.${context ? ` Context: ${context}` : ''}\n\nCurrent text: "${currentValue}"\n\nReturn only the improved text.`,
      suggest: `Suggest 3 alternative versions of this ${fieldLabel}, each on a new line, numbered 1-3.${context ? ` Context: ${context}` : ''}\n\nCurrent text: "${currentValue}"`,
    };

    try {
      const { data } = await api.post<{ content: string }>('/ai/generate', {
        prompt: prompts[action],
      });
      setResult(data.content);
    } catch {
      setError('Failed to generate content');
    } finally {
      setLoading(false);
    }
  };

  if (!open) {
    return (
      <button
        type='button'
        onClick={() => setOpen(true)}
        className='p-1 text-purple-400 hover:text-purple-600'
        title='AI Assist'
      >
        <Sparkles className='w-4 h-4' />
      </button>
    );
  }

  return (
    <div className='relative'>
      <div className='absolute right-0 top-0 z-10 w-80 bg-white border border-purple-200 rounded-lg shadow-lg'>
        <div className='p-3 border-b border-purple-100 flex items-center justify-between'>
          <div className='flex items-center gap-1.5'>
            <Sparkles className='w-4 h-4 text-purple-600' />
            <span className='text-sm font-medium text-purple-900'>
              AI Assist
            </span>
          </div>
          <button
            onClick={() => {
              setOpen(false);
              setResult(null);
              setError(null);
            }}
            className='text-gray-400 hover:text-gray-600'
          >
            <X className='w-4 h-4' />
          </button>
        </div>

        <div className='p-3'>
          {!result && !loading && !error && (
            <div className='space-y-2'>
              <button
                onClick={() => handleAction('generate')}
                className='w-full text-left px-3 py-2 text-sm rounded-md hover:bg-purple-50 text-gray-700'
              >
                Generate new {fieldLabel}
              </button>
              {currentValue && (
                <>
                  <button
                    onClick={() => handleAction('improve')}
                    className='w-full text-left px-3 py-2 text-sm rounded-md hover:bg-purple-50 text-gray-700'
                  >
                    Improve current text
                  </button>
                  <button
                    onClick={() => handleAction('suggest')}
                    className='w-full text-left px-3 py-2 text-sm rounded-md hover:bg-purple-50 text-gray-700'
                  >
                    Suggest alternatives
                  </button>
                </>
              )}
            </div>
          )}

          {loading && (
            <div className='flex items-center justify-center py-4 text-purple-600'>
              <Loader2 className='w-5 h-5 animate-spin mr-2' />
              <span className='text-sm'>Generating...</span>
            </div>
          )}

          {error && <div className='text-sm text-red-600 py-2'>{error}</div>}

          {result && (
            <div className='space-y-3'>
              <div className='bg-gray-50 rounded p-2 text-sm text-gray-800 whitespace-pre-wrap max-h-40 overflow-y-auto'>
                {result}
              </div>
              <div className='flex gap-2'>
                <button
                  onClick={() => {
                    onAccept(result);
                    setOpen(false);
                    setResult(null);
                  }}
                  className='flex-1 px-3 py-1.5 text-sm text-white bg-purple-600 rounded-md hover:bg-purple-700'
                >
                  Accept
                </button>
                <button
                  onClick={() => setResult(null)}
                  className='flex-1 px-3 py-1.5 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200'
                >
                  Try Again
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIAssistField;
