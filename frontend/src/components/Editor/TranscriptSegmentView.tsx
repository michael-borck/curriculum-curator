import React, { useState } from 'react';
import { NodeViewWrapper, NodeViewContent } from '@tiptap/react';
import type { NodeViewProps } from '@tiptap/react';
import { Loader2, Plus, Sparkles, Wand2 } from 'lucide-react';
import { useAILevel } from '../../hooks/useAILevel';
import { useWorkingContextStore } from '../../stores/workingContextStore';
import { videoInteractionApi } from '../../services/videoInteractionApi';
import type { SuggestedInteraction } from '../../services/videoInteractionApi';

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${String(secs).padStart(2, '0')}`;
}

/** Collect all transcript segment texts (with neighbours) from the editor doc. */
function gatherSegmentContext(
  editor: NodeViewProps['editor'],
  getPos: () => number,
  node: NodeViewProps['node']
): string {
  if (!editor) return node.textContent;

  const doc = editor.state.doc;
  const myPos = getPos();
  const segments: { pos: number; text: string }[] = [];

  doc.descendants((n, pos) => {
    if (n.type.name === 'transcriptSegment') {
      segments.push({ pos, text: n.textContent });
    }
  });

  // Find current segment index
  const idx = segments.findIndex(s => s.pos === myPos);
  if (idx === -1) return node.textContent;

  // Return current + 1 neighbour on each side for context
  const start = Math.max(0, idx - 1);
  const end = Math.min(segments.length, idx + 2);
  return segments
    .slice(start, end)
    .map(s => s.text)
    .join(' ');
}

/** Collect all transcript segments from the doc for batch suggestion. */
function gatherAllSegments(
  editor: NodeViewProps['editor']
): { start: number; end: number; text: string }[] {
  if (!editor) return [];

  const segments: { start: number; end: number; text: string }[] = [];
  editor.state.doc.descendants(n => {
    if (n.type.name === 'transcriptSegment') {
      const attrs = n.attrs as { startTime: number; endTime: number };
      segments.push({
        start: attrs.startTime,
        end: attrs.endTime,
        text: n.textContent,
      });
    }
  });
  return segments;
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

  const { canGenerate } = useAILevel();
  const ctx = useWorkingContextStore();
  const [generating, setGenerating] = useState(false);
  const [suggestingAll, setSuggestingAll] = useState(false);

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

  const handleGenerateWithAI = async () => {
    if (!editor || typeof getPos !== 'function' || generating) return;

    setGenerating(true);
    try {
      const segmentText = gatherSegmentContext(editor, getPos, node);
      const resp = await videoInteractionApi.generateInteraction({
        segmentText,
        questionType: 'multiple_choice',
        unitId: ctx.activeUnitId ?? undefined,
        designId: ctx.activeDesignId ?? undefined,
        weekNumber: ctx.activeWeek ?? undefined,
      });
      const data = resp.data;

      const pos = getPos() + node.nodeSize;
      editor
        .chain()
        .focus()
        .insertContentAt(pos, {
          type: 'videoInteraction',
          attrs: {
            interactionId: globalThis.crypto.randomUUID(),
            time: attrs.endTime,
            pause: true,
            questionType: data.questionType,
            questionText: data.questionText,
            options: data.options.map(o => ({
              id: globalThis.crypto.randomUUID(),
              text: o.text,
              correct: o.correct,
            })),
            feedback: data.feedback,
            points: data.points,
            explanation: data.explanation,
          },
        })
        .run();
    } catch (err) {
      console.error('AI interaction generation failed:', err);
    } finally {
      setGenerating(false);
    }
  };

  const insertSuggestedInteractions = (
    interactions: SuggestedInteraction[]
  ) => {
    if (!editor) return;

    // Find all transcript segment positions and their end times
    const segmentPositions: {
      pos: number;
      endTime: number;
      nodeSize: number;
    }[] = [];
    editor.state.doc.descendants((n, pos) => {
      if (n.type.name === 'transcriptSegment') {
        const a = n.attrs as { endTime: number };
        segmentPositions.push({
          pos,
          endTime: a.endTime,
          nodeSize: n.nodeSize,
        });
      }
    });

    // Sort interactions by time descending so insertions don't shift positions
    const sorted = [...interactions].sort((a, b) => b.time - a.time);

    for (const interaction of sorted) {
      // Find the segment whose endTime is closest to (but <= ) interaction.time
      let bestSeg = segmentPositions[0];
      for (const seg of segmentPositions) {
        if (seg.endTime <= interaction.time) {
          bestSeg = seg;
        }
      }
      if (!bestSeg) continue;

      const insertPos = bestSeg.pos + bestSeg.nodeSize;
      editor
        .chain()
        .insertContentAt(insertPos, {
          type: 'videoInteraction',
          attrs: {
            interactionId: globalThis.crypto.randomUUID(),
            time: interaction.time,
            pause: true,
            questionType: interaction.questionType,
            questionText: interaction.questionText,
            options: interaction.options.map(o => ({
              id: globalThis.crypto.randomUUID(),
              text: o.text,
              correct: o.correct,
            })),
            feedback: interaction.feedback,
            points: interaction.points,
            explanation: interaction.explanation,
          },
        })
        .run();
    }
  };

  const handleSuggestAll = async () => {
    if (!editor || suggestingAll) return;

    setSuggestingAll(true);
    try {
      const segments = gatherAllSegments(editor);
      if (segments.length === 0) return;

      const resp = await videoInteractionApi.suggestInteractionPoints({
        transcriptSegments: segments,
        unitId: ctx.activeUnitId ?? undefined,
        designId: ctx.activeDesignId ?? undefined,
        weekNumber: ctx.activeWeek ?? undefined,
      });

      insertSuggestedInteractions(resp.data.interactions);
    } catch (err) {
      console.error('AI suggest-all failed:', err);
    } finally {
      setSuggestingAll(false);
    }
  };

  // Show the "Suggest all" button only on the first transcript segment
  const isFirst = (() => {
    if (!editor) return false;
    let firstPos = -1;
    editor.state.doc.descendants((n, pos) => {
      if (n.type.name === 'transcriptSegment' && firstPos === -1) {
        firstPos = pos;
      }
    });
    return typeof getPos === 'function' && getPos() === firstPos;
  })();

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

      {/* Action buttons (hover) */}
      <div className='flex justify-center gap-2 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity'>
        <button
          type='button'
          onMouseDown={e => {
            e.preventDefault();
            handleInsertInteraction();
          }}
          className='flex items-center gap-1 px-2 py-0.5 text-xs text-indigo-500 hover:text-indigo-700 hover:bg-indigo-50 rounded'
          title='Insert blank interaction here'
        >
          <Plus size={12} />
          <span>Insert interaction</span>
        </button>

        {canGenerate && (
          <button
            type='button'
            disabled={generating}
            onMouseDown={e => {
              e.preventDefault();
              void handleGenerateWithAI();
            }}
            className='flex items-center gap-1 px-2 py-0.5 text-xs text-purple-500 hover:text-purple-700 hover:bg-purple-50 rounded disabled:opacity-50'
            title='Generate quiz interaction with AI'
          >
            {generating ? (
              <Loader2 size={12} className='animate-spin' />
            ) : (
              <Sparkles size={12} />
            )}
            <span>{generating ? 'Generating…' : 'Generate with AI'}</span>
          </button>
        )}

        {canGenerate && isFirst && (
          <button
            type='button'
            disabled={suggestingAll}
            onMouseDown={e => {
              e.preventDefault();
              void handleSuggestAll();
            }}
            className='flex items-center gap-1 px-2 py-0.5 text-xs text-amber-600 hover:text-amber-800 hover:bg-amber-50 rounded disabled:opacity-50'
            title='AI suggests interaction points across full transcript'
          >
            {suggestingAll ? (
              <Loader2 size={12} className='animate-spin' />
            ) : (
              <Wand2 size={12} />
            )}
            <span>{suggestingAll ? 'Analysing…' : 'Suggest all'}</span>
          </button>
        )}
      </div>
    </NodeViewWrapper>
  );
};

export default TranscriptSegmentView;
