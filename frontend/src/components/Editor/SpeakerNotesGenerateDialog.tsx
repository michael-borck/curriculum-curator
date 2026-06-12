import React, { useMemo, useState } from 'react';
import { Loader2, Sparkles, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { aiApi, type SpeakerNotesDraft } from '../../services/aiApi';
import { getSlideSegments, type SlideSegment } from '../../utils/speakerNotes';

interface SpeakerNotesGenerateDialogProps {
  materialId: string;
  contentJson: Record<string, unknown>;
  onApply: (drafts: SpeakerNotesDraft[]) => void;
  onClose: () => void;
}

type Stage = 'select' | 'generating' | 'review';

/**
 * Propose/apply flow for AI speaker notes (15.11): pick slides (defaults
 * from each notes block's aiSelected attr), generate drafts in one batched
 * call, review each against existing notes, then apply the accepted ones.
 * Nothing touches the document until Apply.
 */
const SpeakerNotesGenerateDialog: React.FC<SpeakerNotesGenerateDialogProps> = ({
  materialId,
  contentJson,
  onApply,
  onClose,
}) => {
  const segments = useMemo<SlideSegment[]>(
    () => getSlideSegments(contentJson) ?? [],
    [contentJson]
  );

  const [stage, setStage] = useState<Stage>('select');
  const [selected, setSelected] = useState<Set<number>>(
    () =>
      new Set(
        segments
          .map((segment, index) => ({ segment, index }))
          .filter(({ segment }) => segment.aiSelected && segment.text !== '')
          .map(({ index }) => index)
      )
  );
  const [drafts, setDrafts] = useState<SpeakerNotesDraft[]>([]);
  const [accepted, setAccepted] = useState<Set<number>>(new Set());

  const toggleSelected = (index: number) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  const toggleAccepted = (index: number) => {
    setAccepted(prev => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  const handleGenerate = async () => {
    setStage('generating');
    try {
      const { data } = await aiApi.generateSpeakerNotes(materialId, [
        ...selected,
      ]);
      setDrafts(data.drafts);
      setAccepted(new Set(data.drafts.map(draft => draft.slideIndex)));
      setStage('review');
    } catch {
      toast.error('Failed to generate speaker notes');
      setStage('select');
    }
  };

  const handleApply = () => {
    onApply(drafts.filter(draft => accepted.has(draft.slideIndex)));
    onClose();
  };

  const slidePreview = (index: number) =>
    segments[index]?.text.slice(0, 120) ?? '';

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4'>
      <div className='bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col'>
        <div className='flex items-center justify-between px-5 py-3 border-b border-gray-100'>
          <h2 className='font-semibold text-gray-900 flex items-center gap-2'>
            <Sparkles className='w-4 h-4 text-purple-500' />
            Generate speaker notes
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
          {stage === 'select' && (
            <>
              <p className='text-sm text-gray-600 mb-3'>
                Choose which slides to draft notes for. Drafts are reviewed
                before anything is saved.
              </p>
              <div className='space-y-2'>
                {segments.map((segment, index) => (
                  <label
                    key={index}
                    className='flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer'
                  >
                    <input
                      type='checkbox'
                      checked={selected.has(index)}
                      onChange={() => toggleSelected(index)}
                      disabled={segment.text === ''}
                      className='mt-1'
                    />
                    <span className='min-w-0'>
                      <span className='text-sm font-medium text-gray-800'>
                        Slide {index + 1}
                        {segment.notesText && (
                          <span className='ml-2 text-xs text-amber-600'>
                            has notes — will be improved
                          </span>
                        )}
                      </span>
                      <span className='block text-xs text-gray-500 truncate'>
                        {slidePreview(index) || '(empty slide)'}
                      </span>
                    </span>
                  </label>
                ))}
              </div>
            </>
          )}

          {stage === 'generating' && (
            <div className='flex flex-col items-center justify-center py-12 text-gray-500'>
              <Loader2 className='w-6 h-6 animate-spin mb-3' />
              <p className='text-sm'>
                Drafting notes for {selected.size} slide
                {selected.size === 1 ? '' : 's'}…
              </p>
            </div>
          )}

          {stage === 'review' && (
            <div className='space-y-4'>
              {drafts.map(draft => (
                <div
                  key={draft.slideIndex}
                  className='border border-gray-200 rounded-lg p-3'
                >
                  <label className='flex items-center gap-2 mb-2 cursor-pointer'>
                    <input
                      type='checkbox'
                      checked={accepted.has(draft.slideIndex)}
                      onChange={() => toggleAccepted(draft.slideIndex)}
                    />
                    <span className='text-sm font-medium text-gray-800'>
                      Slide {draft.slideIndex + 1}
                    </span>
                  </label>
                  {segments[draft.slideIndex]?.notesText && (
                    <p className='text-xs text-gray-400 mb-1 line-through'>
                      {segments[draft.slideIndex]?.notesText}
                    </p>
                  )}
                  <p className='text-sm text-gray-700 whitespace-pre-wrap'>
                    {draft.notes}
                  </p>
                </div>
              ))}
              {drafts.length === 0 && (
                <p className='text-sm text-gray-500'>
                  No drafts were returned.
                </p>
              )}
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
          {stage === 'select' && (
            <button
              onClick={handleGenerate}
              disabled={selected.size === 0}
              className='flex items-center gap-2 px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50'
            >
              <Sparkles className='w-4 h-4' />
              Generate for {selected.size} slide
              {selected.size === 1 ? '' : 's'}
            </button>
          )}
          {stage === 'review' && (
            <button
              onClick={handleApply}
              disabled={accepted.size === 0}
              className='px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50'
            >
              Apply {accepted.size} draft{accepted.size === 1 ? '' : 's'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default SpeakerNotesGenerateDialog;
