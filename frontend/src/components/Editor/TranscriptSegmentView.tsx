import React from 'react';
import { NodeViewWrapper, NodeViewContent } from '@tiptap/react';
import type { NodeViewProps } from '@tiptap/react';
import { Plus } from 'lucide-react';

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${String(secs).padStart(2, '0')}`;
}

const TranscriptSegmentView: React.FC<NodeViewProps> = ({
  node,
  editor,
  getPos,
}) => {
  const attrs = node.attrs as {
    startTime: number;
    endTime: number;
  };

  const handleInsertInteraction = () => {
    if (!editor || typeof getPos !== 'function') return;

    const pos = getPos() + node.nodeSize;
    const interactionNode = editor.schema.nodes.videoInteraction;
    if (!interactionNode) return;

    editor
      .chain()
      .focus()
      .insertContentAt(pos, {
        type: 'videoInteraction',
        attrs: {
          interactionId: globalThis.crypto.randomUUID(),
          time: attrs.endTime,
          pause: true,
          questionType: 'multiple_choice',
          questionText: '',
          options: [
            {
              id: globalThis.crypto.randomUUID(),
              text: '',
              correct: false,
            },
            {
              id: globalThis.crypto.randomUUID(),
              text: '',
              correct: false,
            },
          ],
          feedback: '',
          points: 1,
          explanation: '',
        },
      })
      .run();
  };

  return (
    <NodeViewWrapper className='transcript-segment group relative my-1'>
      <div className='flex gap-3 items-start'>
        {/* Timestamp margin */}
        <div className='flex-shrink-0 w-24 text-right'>
          <span className='text-xs font-mono text-gray-400 select-none'>
            {formatTime(attrs.startTime)}&ndash;{formatTime(attrs.endTime)}
          </span>
        </div>

        {/* Transcript text — read-only content */}
        <div className='flex-1 min-w-0'>
          <NodeViewContent
            as='span'
            className='text-sm text-gray-500 leading-relaxed'
          />
        </div>
      </div>

      {/* Insert interaction button (hover) */}
      <div className='flex justify-center mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity'>
        <button
          type='button'
          onMouseDown={e => {
            e.preventDefault();
            handleInsertInteraction();
          }}
          className='flex items-center gap-1 px-2 py-0.5 text-xs text-indigo-500 hover:text-indigo-700 hover:bg-indigo-50 rounded'
          title='Insert quiz interaction here'
        >
          <Plus size={12} />
          <span>Insert interaction</span>
        </button>
      </div>
    </NodeViewWrapper>
  );
};

export default TranscriptSegmentView;
