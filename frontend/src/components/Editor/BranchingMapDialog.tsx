import React, { useMemo, useCallback, useRef, useEffect } from 'react';
import type { Editor } from '@tiptap/react';
import dagre from 'dagre';
import type { CardType, BranchingChoice } from './BranchingCardNode';

interface BranchingMapDialogProps {
  isOpen: boolean;
  onClose: () => void;
  editor: Editor;
}

interface CardNode {
  cardId: string;
  cardType: CardType;
  cardTitle: string;
  pos: number;
}

interface CardEdge {
  from: string;
  to: string;
  label: string;
}

const NODE_WIDTH = 180;
const NODE_HEIGHT = 60;

const TYPE_LABELS: Record<CardType, string> = {
  content: 'Content',
  branch: 'Branch',
  ending: 'Ending',
};

const TYPE_FILL: Record<CardType, string> = {
  content: '#dbeafe',
  branch: '#fef3c7',
  ending: '#fce7f3',
};

const TYPE_STROKE: Record<CardType, string> = {
  content: '#3b82f6',
  branch: '#f59e0b',
  ending: '#ec4899',
};

const BranchingMapDialog: React.FC<BranchingMapDialogProps> = ({
  isOpen,
  onClose,
  editor,
}) => {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (isOpen && !dialog.open) {
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  // Extract cards and edges from document
  const { cards, edges } = useMemo(() => {
    const foundCards: CardNode[] = [];
    editor.state.doc.descendants((node, pos) => {
      if (node.type.name === 'branchingCard') {
        foundCards.push({
          cardId: node.attrs.cardId as string,
          cardType: node.attrs.cardType as CardType,
          cardTitle: (node.attrs.cardTitle as string) || '(untitled)',
          pos,
        });
      }
    });

    const foundEdges: CardEdge[] = [];
    editor.state.doc.descendants(node => {
      if (node.type.name === 'branchingCard') {
        const cardId = node.attrs.cardId as string;
        const choices = (node.attrs.choices || []) as BranchingChoice[];
        for (const choice of choices) {
          if (choice.targetCardId) {
            foundEdges.push({
              from: cardId,
              to: choice.targetCardId,
              label: choice.text || '',
            });
          }
        }
      }
    });

    return { cards: foundCards, edges: foundEdges };
  }, [editor.state.doc]);

  // Find dead ends and orphans
  const { deadEnds, orphans } = useMemo(() => {
    const cardIds = new Set(cards.map(c => c.cardId));
    const outgoing = new Map<string, number>();
    for (const card of cards) {
      outgoing.set(card.cardId, 0);
    }
    for (const edge of edges) {
      outgoing.set(edge.from, (outgoing.get(edge.from) || 0) + 1);
    }

    // Dead ends: non-ending cards with no outgoing edges
    const deadEndSet = new Set<string>();
    for (const card of cards) {
      if (
        card.cardType !== 'ending' &&
        (outgoing.get(card.cardId) || 0) === 0
      ) {
        deadEndSet.add(card.cardId);
      }
    }

    // Orphans: unreachable from first card via BFS
    const orphanSet = new Set<string>(cardIds);
    if (cards.length > 0) {
      const queue = [cards[0].cardId];
      orphanSet.delete(cards[0].cardId);
      while (queue.length > 0) {
        const current = queue.shift()!;
        for (const edge of edges) {
          if (edge.from === current && orphanSet.has(edge.to)) {
            orphanSet.delete(edge.to);
            queue.push(edge.to);
          }
        }
      }
    }

    return { deadEnds: deadEndSet, orphans: orphanSet };
  }, [cards, edges]);

  // Layout with dagre
  const layout = useMemo(() => {
    const g = new dagre.graphlib.Graph();
    g.setGraph({ rankdir: 'TB', nodesep: 40, ranksep: 60 });
    g.setDefaultEdgeLabel(() => ({}));

    for (const card of cards) {
      g.setNode(card.cardId, { width: NODE_WIDTH, height: NODE_HEIGHT });
    }
    for (const edge of edges) {
      g.setEdge(edge.from, edge.to);
    }

    dagre.layout(g);

    const nodePositions = new Map<string, { x: number; y: number }>();
    for (const card of cards) {
      const n = g.node(card.cardId);
      if (n) {
        nodePositions.set(card.cardId, { x: n.x, y: n.y });
      }
    }

    return nodePositions;
  }, [cards, edges]);

  // Compute SVG viewBox
  const viewBox = useMemo(() => {
    if (layout.size === 0) return '0 0 400 200';
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;
    for (const pos of layout.values()) {
      minX = Math.min(minX, pos.x - NODE_WIDTH / 2);
      minY = Math.min(minY, pos.y - NODE_HEIGHT / 2);
      maxX = Math.max(maxX, pos.x + NODE_WIDTH / 2);
      maxY = Math.max(maxY, pos.y + NODE_HEIGHT / 2);
    }
    const pad = 40;
    return `${minX - pad} ${minY - pad} ${maxX - minX + pad * 2} ${maxY - minY + pad * 2}`;
  }, [layout]);

  const scrollToCard = useCallback(
    (pos: number) => {
      editor.commands.setTextSelection(pos);
      editor.commands.scrollIntoView();
      onClose();
    },
    [editor, onClose]
  );

  if (!isOpen) return null;

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      className='rounded-xl shadow-xl border border-gray-200 p-0 backdrop:bg-black/30 max-w-4xl w-full'
    >
      <div className='p-4'>
        <div className='flex items-center justify-between mb-4'>
          <h2 className='text-lg font-semibold text-gray-800'>Branching Map</h2>
          <button
            onClick={onClose}
            className='text-gray-400 hover:text-gray-600 text-xl px-2'
          >
            &times;
          </button>
        </div>

        {cards.length === 0 ? (
          <p className='text-gray-500 text-sm py-8 text-center'>
            No branching cards found in this document.
          </p>
        ) : (
          <>
            {/* Legend */}
            <div className='flex gap-4 mb-3 text-xs text-gray-500'>
              <span className='flex items-center gap-1'>
                <span
                  className='inline-block w-3 h-3 rounded'
                  style={{ background: TYPE_FILL.content }}
                />
                Content
              </span>
              <span className='flex items-center gap-1'>
                <span
                  className='inline-block w-3 h-3 rounded'
                  style={{ background: TYPE_FILL.branch }}
                />
                Branch
              </span>
              <span className='flex items-center gap-1'>
                <span
                  className='inline-block w-3 h-3 rounded'
                  style={{ background: TYPE_FILL.ending }}
                />
                Ending
              </span>
              {deadEnds.size > 0 && (
                <span className='flex items-center gap-1'>
                  <span className='inline-block w-3 h-3 rounded border-2 border-dashed border-red-400' />
                  Dead end
                </span>
              )}
              {orphans.size > 0 && (
                <span className='flex items-center gap-1'>
                  <span
                    className='inline-block w-3 h-3 rounded'
                    style={{ background: '#e5e7eb' }}
                  />
                  Orphan
                </span>
              )}
            </div>

            <svg
              viewBox={viewBox}
              className='w-full border border-gray-100 rounded-lg bg-gray-50'
              style={{ minHeight: '300px', maxHeight: '500px' }}
            >
              <defs>
                <marker
                  id='arrowhead'
                  markerWidth='10'
                  markerHeight='7'
                  refX='10'
                  refY='3.5'
                  orient='auto'
                >
                  <polygon points='0 0, 10 3.5, 0 7' fill='#9ca3af' />
                </marker>
              </defs>

              {/* Edges */}
              {edges.map((edge, i) => {
                const from = layout.get(edge.from);
                const to = layout.get(edge.to);
                if (!from || !to) return null;

                const x1 = from.x;
                const y1 = from.y + NODE_HEIGHT / 2;
                const x2 = to.x;
                const y2 = to.y - NODE_HEIGHT / 2;
                const midY = (y1 + y2) / 2;

                return (
                  <g key={`edge-${i}`}>
                    <path
                      d={`M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
                      fill='none'
                      stroke='#9ca3af'
                      strokeWidth='1.5'
                      markerEnd='url(#arrowhead)'
                    />
                    {edge.label && (
                      <text
                        x={(x1 + x2) / 2}
                        y={midY - 4}
                        textAnchor='middle'
                        fill='#6b7280'
                        fontSize='10'
                      >
                        {edge.label.length > 20
                          ? edge.label.slice(0, 20) + '…'
                          : edge.label}
                      </text>
                    )}
                  </g>
                );
              })}

              {/* Nodes */}
              {cards.map(card => {
                const pos = layout.get(card.cardId);
                if (!pos) return null;

                const isDeadEnd = deadEnds.has(card.cardId);
                const isOrphan = orphans.has(card.cardId);
                const fill = isOrphan ? '#e5e7eb' : TYPE_FILL[card.cardType];
                const stroke = isDeadEnd
                  ? '#ef4444'
                  : TYPE_STROKE[card.cardType];

                return (
                  <g
                    key={card.cardId}
                    style={{ cursor: 'pointer' }}
                    onClick={() => scrollToCard(card.pos)}
                  >
                    <rect
                      x={pos.x - NODE_WIDTH / 2}
                      y={pos.y - NODE_HEIGHT / 2}
                      width={NODE_WIDTH}
                      height={NODE_HEIGHT}
                      rx={8}
                      ry={8}
                      fill={fill}
                      stroke={stroke}
                      strokeWidth={isDeadEnd ? 2 : 1.5}
                      strokeDasharray={isDeadEnd ? '5,3' : undefined}
                    />
                    <text
                      x={pos.x}
                      y={pos.y - 4}
                      textAnchor='middle'
                      fill='#374151'
                      fontSize='12'
                      fontWeight='500'
                    >
                      {card.cardTitle.length > 22
                        ? card.cardTitle.slice(0, 22) + '…'
                        : card.cardTitle}
                    </text>
                    <text
                      x={pos.x}
                      y={pos.y + 14}
                      textAnchor='middle'
                      fill='#9ca3af'
                      fontSize='10'
                    >
                      {TYPE_LABELS[card.cardType]}
                    </text>
                  </g>
                );
              })}
            </svg>
          </>
        )}
      </div>
    </dialog>
  );
};

export default BranchingMapDialog;
