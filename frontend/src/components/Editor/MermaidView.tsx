import React, { useState, useEffect, useRef, useId, useCallback } from 'react';
import { NodeViewWrapper } from '@tiptap/react';
import type { NodeViewProps } from '@tiptap/react';
import mermaid from 'mermaid';

mermaid.initialize({ startOnLoad: false, theme: 'default' });

const MermaidView: React.FC<NodeViewProps> = ({ node, updateAttributes }) => {
  const source: string = node.attrs.source ?? '';
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(source);
  const [svgHtml, setSvgHtml] = useState('');
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const uniqueId = useId().replace(/:/g, '_');

  const renderDiagram = useCallback(
    async (src: string) => {
      try {
        const { svg } = await mermaid.render(`mermaid_${uniqueId}`, src);
        setSvgHtml(svg);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Invalid Mermaid syntax');
        setSvgHtml('');
      }
    },
    [uniqueId]
  );

  useEffect(() => {
    if (source) {
      renderDiagram(source);
    }
  }, [source, renderDiagram]);

  const handleSave = () => {
    updateAttributes({ source: draft });
    setEditing(false);
  };

  const handleCancel = () => {
    setDraft(source);
    setEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    e.stopPropagation();
  };

  return (
    <NodeViewWrapper className='mermaid-node my-4'>
      {editing ? (
        <div className='border border-blue-300 rounded-lg p-3 bg-blue-50'>
          <textarea
            value={draft}
            onChange={e => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={8}
            className='w-full font-mono text-sm border border-gray-300 rounded p-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-400'
            placeholder='graph TD\n  A[Start] --> B[End]'
          />
          <div className='flex gap-2 mt-2'>
            <button
              type='button'
              onMouseDown={e => {
                e.preventDefault();
                handleSave();
              }}
              className='px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700'
            >
              Save
            </button>
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
          </div>
        </div>
      ) : (
        <div
          className='border border-gray-200 rounded-lg p-3 bg-white cursor-pointer hover:border-blue-300 transition-colors'
          ref={containerRef}
        >
          {error ? (
            <div className='text-red-600 text-sm p-2 bg-red-50 rounded'>
              {error}
            </div>
          ) : (
            <div
              className='mermaid-svg-output flex justify-center'
              dangerouslySetInnerHTML={{ __html: svgHtml }}
            />
          )}
          <div className='mt-2 flex justify-end'>
            <button
              type='button'
              onMouseDown={e => {
                e.preventDefault();
                setDraft(source);
                setEditing(true);
              }}
              className='px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200'
            >
              Edit source
            </button>
          </div>
        </div>
      )}
    </NodeViewWrapper>
  );
};

export default MermaidView;
