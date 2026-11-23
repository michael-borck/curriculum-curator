import { useState } from 'react';
import { Loader2, Layers, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { AiDataNotice } from '../shared/AiDataNotice';
import { aiApi, type FlashcardDeck } from '../../services/aiApi';

interface FlashcardGenerateDialogProps {
  materialId: string;
  onApply: (deck: FlashcardDeck) => void;
  onClose: () => void;
}

type Stage = 'options' | 'generating' | 'review';

const FlashcardGenerateDialog = ({
  materialId,
  onApply,
  onClose,
}: FlashcardGenerateDialogProps) => {
  const [stage, setStage] = useState<Stage>('options');
  const [count, setCount] = useState(10);
  const [deck, setDeck] = useState<FlashcardDeck | null>(null);

  const generate = async () => {
    setStage('generating');
    try {
      const { data } = await aiApi.generateFlashcards(materialId, count);
      setDeck(data);
      setStage('review');
    } catch {
      toast.error('Failed to generate flashcards');
      setStage('options');
    }
  };

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
      <div className='bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col'>
        <div className='flex items-center justify-between px-5 py-3 border-b border-gray-100'>
          <h2 className='font-semibold text-gray-900 flex items-center gap-2'>
            <Layers className='w-4 h-4 text-purple-500' />
            Generate study flashcards
          </h2>
          <button
            onClick={onClose}
            className='p-1 text-gray-400 hover:text-gray-600'
            title='Close'
          >
            <X className='w-4 h-4' />
          </button>
        </div>

        <div className='flex-1 overflow-y-auto px-5 py-4'>
          {stage === 'options' && (
            <>
              <p className='text-sm text-gray-600 mb-3'>
                Drafts retrieval-practice cards from this material as a
                two-column table you can review before inserting.
              </p>
              <AiDataNotice className='mb-3' />
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Number of cards
              </label>
              <input
                type='number'
                min={1}
                max={30}
                value={count}
                onChange={e =>
                  setCount(
                    Math.min(30, Math.max(1, Number(e.target.value) || 10))
                  )
                }
                className='w-24 border border-gray-300 rounded-md px-3 py-2 text-sm'
              />
            </>
          )}

          {stage === 'generating' && (
            <div className='flex flex-col items-center justify-center py-12 text-gray-500'>
              <Loader2 className='w-6 h-6 animate-spin mb-3' />
              <p className='text-sm'>Writing cards…</p>
            </div>
          )}

          {stage === 'review' && deck && (
            <div className='space-y-3'>
              <h3 className='text-base font-semibold text-gray-900'>
                {deck.title}
              </h3>
              <div className='divide-y divide-gray-100 border border-gray-200 rounded-lg'>
                {deck.cards.map((card, index) => (
                  <div
                    key={index}
                    className='grid grid-cols-2 gap-3 p-3 text-sm'
                  >
                    <div className='font-medium text-gray-800'>
                      {card.front}
                    </div>
                    <div className='text-gray-600'>{card.back}</div>
                  </div>
                ))}
              </div>
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
          {stage === 'options' && (
            <button
              onClick={() => void generate()}
              className='flex items-center gap-2 px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700'
            >
              <Layers className='w-4 h-4' />
              Draft cards
            </button>
          )}
          {stage === 'review' && deck && (
            <button
              onClick={() => {
                onApply(deck);
                onClose();
              }}
              className='px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700'
            >
              Insert deck
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default FlashcardGenerateDialog;
