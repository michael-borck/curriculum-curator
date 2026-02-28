import React, { useState } from 'react';
import { NodeViewWrapper } from '@tiptap/react';
import type { NodeViewProps } from '@tiptap/react';
import { Video, ExternalLink } from 'lucide-react';
import TranscriptLoadDialog from './TranscriptLoadDialog';

function detectPlatform(url: string): string {
  if (/youtube\.com|youtu\.be/i.test(url)) return 'youtube';
  if (/vimeo\.com/i.test(url)) return 'vimeo';
  if (/echo360/i.test(url)) return 'echo360';
  return 'other';
}

function extractYoutubeId(url: string): string | null {
  const m = url.match(
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/
  );
  return m ? m[1] : null;
}

const PLATFORM_COLORS: Record<string, string> = {
  youtube: 'bg-red-100 text-red-700',
  vimeo: 'bg-blue-100 text-blue-700',
  echo360: 'bg-green-100 text-green-700',
  other: 'bg-gray-100 text-gray-700',
};

const InteractiveVideoEmbedView: React.FC<NodeViewProps> = ({
  node,
  updateAttributes,
  editor,
}) => {
  const attrs = node.attrs as {
    url: string;
    platform: string;
    title: string;
  };

  const [editing, setEditing] = useState(!attrs.url);
  const [draft, setDraft] = useState({ ...attrs });
  const [showTranscriptDialog, setShowTranscriptDialog] = useState(false);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    e.stopPropagation();
  };

  const handleSave = () => {
    const platform = detectPlatform(draft.url);
    updateAttributes({ ...draft, platform });
    setEditing(false);
  };

  const handleCancel = () => {
    if (!attrs.url) return;
    setDraft({ ...attrs });
    setEditing(false);
  };

  const handleTranscriptLoaded = (
    segments: { start: number; end: number; text: string }[]
  ) => {
    if (!editor) return;

    // Find position after this node
    const { state } = editor;
    let insertPos: number | null = null;

    state.doc.descendants((n, pos) => {
      if (n.type.name === 'interactiveVideoEmbed' && insertPos === null) {
        insertPos = pos + n.nodeSize;
      }
    });

    if (insertPos === null) return;

    // Remove existing transcript segments and video interactions
    const nodesToRemove: { from: number; to: number }[] = [];
    state.doc.descendants((n, pos) => {
      if (
        n.type.name === 'transcriptSegment' ||
        n.type.name === 'videoInteraction'
      ) {
        nodesToRemove.push({ from: pos, to: pos + n.nodeSize });
      }
    });

    // Build insertion content
    const content = segments.map(seg => ({
      type: 'transcriptSegment' as const,
      attrs: { startTime: seg.start, endTime: seg.end },
      content: [{ type: 'text' as const, text: seg.text }],
    }));

    // Apply as a single transaction
    const { tr } = state;

    // Remove old segments in reverse order to preserve positions
    for (const range of nodesToRemove.reverse()) {
      tr.delete(range.from, range.to);
    }

    // Recalculate insertPos after deletions
    const mappedPos = tr.mapping.map(insertPos);
    tr.insert(
      mappedPos,
      content.map(c => state.schema.nodeFromJSON(c))
    );

    editor.view.dispatch(tr);
    setShowTranscriptDialog(false);
  };

  const youtubeId =
    attrs.platform === 'youtube' ? extractYoutubeId(attrs.url) : null;

  // Edit mode
  if (editing) {
    return (
      <NodeViewWrapper className='interactive-video-embed my-4'>
        <div className='border-2 border-indigo-300 rounded-lg p-4 bg-indigo-50 space-y-3'>
          <div className='text-sm font-medium text-indigo-700'>
            Interactive Video
          </div>
          <input
            type='text'
            value={draft.title}
            onChange={e => setDraft({ ...draft, title: e.target.value })}
            onKeyDown={handleKeyDown}
            placeholder='Video title…'
            className='w-full border border-gray-300 rounded px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400'
          />
          <input
            type='text'
            value={draft.url}
            onChange={e => setDraft({ ...draft, url: e.target.value })}
            onKeyDown={handleKeyDown}
            placeholder='Paste video URL (YouTube, Vimeo, Echo360)…'
            className='w-full border border-gray-300 rounded px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400'
          />
          <div className='flex gap-2'>
            <button
              type='button'
              onMouseDown={e => {
                e.preventDefault();
                handleSave();
              }}
              className='px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700'
            >
              Save
            </button>
            {attrs.url && (
              <button
                type='button'
                onMouseDown={e => {
                  e.preventDefault();
                  handleCancel();
                }}
                className='px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300'
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      </NodeViewWrapper>
    );
  }

  // View mode
  return (
    <NodeViewWrapper className='interactive-video-embed my-4'>
      <div className='border-2 border-indigo-200 rounded-lg overflow-hidden bg-white'>
        {/* Header */}
        <div className='flex items-center gap-2 px-4 py-2 bg-indigo-50 border-b border-indigo-200'>
          <Video size={16} className='text-indigo-600' />
          <span className='text-sm font-medium text-indigo-800'>
            {attrs.title || 'Interactive Video'}
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              PLATFORM_COLORS[attrs.platform] || PLATFORM_COLORS.other
            }`}
          >
            {attrs.platform}
          </span>
          {attrs.url && (
            <a
              href={attrs.url}
              target='_blank'
              rel='noopener noreferrer'
              className='ml-auto text-indigo-500 hover:text-indigo-700'
            >
              <ExternalLink size={14} />
            </a>
          )}
        </div>

        {/* YouTube preview */}
        {youtubeId && (
          <div className='aspect-video'>
            <iframe
              src={`https://www.youtube.com/embed/${youtubeId}`}
              className='w-full h-full'
              allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture'
              allowFullScreen
              title={attrs.title}
            />
          </div>
        )}

        {/* Actions */}
        <div className='flex gap-2 px-4 py-2 border-t border-gray-100'>
          <button
            type='button'
            onMouseDown={e => {
              e.preventDefault();
              setShowTranscriptDialog(true);
            }}
            className='px-3 py-1 text-sm bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200'
          >
            Load Transcript
          </button>
          <button
            type='button'
            onMouseDown={e => {
              e.preventDefault();
              setDraft({ ...attrs });
              setEditing(true);
            }}
            className='px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded hover:bg-gray-200'
          >
            Edit
          </button>
        </div>
      </div>

      {showTranscriptDialog && (
        <TranscriptLoadDialog
          videoUrl={attrs.url}
          onClose={() => setShowTranscriptDialog(false)}
          onLoaded={handleTranscriptLoaded}
        />
      )}
    </NodeViewWrapper>
  );
};

export default InteractiveVideoEmbedView;
