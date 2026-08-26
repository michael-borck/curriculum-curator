import React, { useState } from 'react';
import { GitFork, Loader2, AlertTriangle, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { aiApi, type BranchingCardDraft } from '../../services/aiApi';

interface BranchingGenerateDialogProps {
  materialId: string;
  onApply: (cards: BranchingCardDraft[]) => void;
  onClose: () => void;
}

type Stage = 'options' | 'generating' | 'review';

/**
 * Propose/apply flow for AI branching scenarios (19A.7, ADR-068): choose
 * size and audience, generate typed card drafts, review each, then apply
 * the accepted ones. Nothing touches the document until Apply.
 */
const BranchingGenerateDialog: React.FC<BranchingGenerateDialogProps> = ({
  materialId,
  onApply,
  onClose,
}) => {
  const [stage, setStage] = useState<Stage>('options');
  const [cardCount, setCardCount] = useState(6);
  const [audience, setAudience] = useState('');
  const [cards, setCards] = useState<BranchingCardDraft[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [accepted, setAccepted] = useState<Set<string>>(new Set());

  const toggleAccepted = (cardId: string) => {
    setAccepted(prev => {
      const next = new Set(prev);
      if (next.has(cardId)) next.delete(cardId);
      else next.add(cardId);
      return next;
    });
  };

  const handleGenerate = async () => {
    setStage('generating');
    try {
      const { data } = await aiApi.generateBranching(materialId, {
        cardCount,
        audience: audience.trim() || undefined,
      });
      if (data.cards.length === 0) {
        toast.error('No cards were generated — try again');
        setStage('options');
        return;
      }
      // Rejecting the start card would orphan the graph; keep it selected.
      setCards(data.cards);
      setWarnings(data.warnings ?? []);
      setAccepted(
        new Set([data.startCardId, ...data.cards.map(c => c.cardId)])
      );
      setStage('review');
    } catch {
      toast.error('Failed to generate branching scenario');
      setStage('options');
    }
  };

  const handleApply = () => {
    onApply(cards.filter(card => accepted.has(card.cardId)));
    onClose();
  };

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
      <div className='bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col'>
        <div className='flex items-center justify-between px-5 py-3 border-b border-gray-100'>
          <h2 className='font-semibold text-gray-900 flex items-center gap-2'>
            <GitFork className='w-4 h-4 text-purple-500' />
            Generate branching scenario
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
                Drafts a choice-driven scenario from this material&apos;s
                content as editable branching cards. Reviewed before anything is
                saved.
              </p>
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Approximate number of cards
              </label>
              <input
                type='number'
                min={3}
                max={12}
                value={cardCount}
                onChange={e =>
                  setCardCount(
                    Math.min(12, Math.max(3, Number(e.target.value) || 6))
                  )
                }
                className='w-24 border border-gray-300 rounded-md px-3 py-2 text-sm mb-3'
              />
              <label className='block text-xs font-medium text-gray-600 mb-1'>
                Audience{' '}
                <span className='text-gray-400 font-normal'>(optional)</span>
              </label>
              <input
                type='text'
                value={audience}
                onChange={e => setAudience(e.target.value)}
                placeholder='e.g. first-year undergraduates, night class'
                className='w-full border border-gray-300 rounded-md px-3 py-2 text-sm mb-4'
              />
            </>
          )}

          {stage === 'generating' && (
            <div className='flex flex-col items-center justify-center py-12 text-gray-500'>
              <Loader2 className='w-6 h-6 animate-spin mb-3' />
              <p className='text-sm'>Drafting scenario…</p>
            </div>
          )}

          {stage === 'review' && (
            <div className='space-y-4'>
              {warnings.length > 0 && (
                <div className='flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800'>
                  <AlertTriangle className='w-4 h-4 shrink-0 mt-0.5' />
                  <ul className='space-y-1'>
                    {warnings.map((warning, i) => (
                      <li key={i}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
              {cards.map(card => (
                <div
                  key={card.cardId}
                  className='border border-gray-200 rounded-lg p-3'
                >
                  <label className='flex items-center gap-2 mb-1 cursor-pointer'>
                    <input
                      type='checkbox'
                      checked={accepted.has(card.cardId)}
                      onChange={() => toggleAccepted(card.cardId)}
                    />
                    <span className='text-sm font-medium text-gray-800'>
                      {card.cardTitle || '(untitled card)'}
                    </span>
                    <span className='ml-auto text-xs uppercase tracking-wide text-gray-400'>
                      {card.cardType}
                      {card.cardType === 'ending' &&
                        ` · score ${card.endScore}`}
                    </span>
                  </label>
                  <p className='text-sm text-gray-700 whitespace-pre-wrap'>
                    {card.cardContent}
                  </p>
                  {card.choices.length > 0 && (
                    <ul className='mt-2 space-y-1'>
                      {card.choices.map(choice => (
                        <li key={choice.id} className='text-xs text-gray-600'>
                          → {choice.text}{' '}
                          <span className='text-gray-400'>
                            (goes to {choice.targetCardId})
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
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
              onClick={handleGenerate}
              className='flex items-center gap-2 px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700'
            >
              <GitFork className='w-4 h-4' />
              Draft scenario
            </button>
          )}
          {stage === 'review' && (
            <button
              onClick={handleApply}
              disabled={accepted.size === 0}
              className='px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50'
            >
              Apply {accepted.size} card{accepted.size === 1 ? '' : 's'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default BranchingGenerateDialog;
