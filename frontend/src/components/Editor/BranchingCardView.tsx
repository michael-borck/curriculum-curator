import React, { useState, useMemo } from 'react';
import { NodeViewWrapper } from '@tiptap/react';
import type { NodeViewProps } from '@tiptap/react';
import type { CardType, BranchingChoice } from './BranchingCardNode';

const TYPE_LABELS: Record<CardType, string> = {
  content: 'Content',
  branch: 'Branch Point',
  ending: 'Ending',
};

const TYPE_COLORS: Record<
  CardType,
  { bg: string; border: string; badge: string }
> = {
  content: {
    bg: 'bg-blue-50',
    border: 'border-blue-300',
    badge: 'bg-blue-100 text-blue-700',
  },
  branch: {
    bg: 'bg-amber-50',
    border: 'border-amber-300',
    badge: 'bg-amber-100 text-amber-700',
  },
  ending: {
    bg: 'bg-pink-50',
    border: 'border-pink-300',
    badge: 'bg-pink-100 text-pink-700',
  },
};

function generateId(): string {
  return globalThis.crypto.randomUUID();
}

interface CardInfo {
  cardId: string;
  cardTitle: string;
}

const BranchingCardView: React.FC<NodeViewProps> = ({
  node,
  updateAttributes,
  editor,
}) => {
  const attrs = node.attrs as {
    cardId: string;
    cardType: CardType;
    cardTitle: string;
    cardContent: string;
    choices: BranchingChoice[];
    endScore: number;
    endMessage: string;
  };

  const isNew = !attrs.cardTitle && !attrs.cardContent;
  const [editing, setEditing] = useState(isNew);
  const [draft, setDraft] = useState({
    ...attrs,
    choices: [...attrs.choices],
  });

  // Collect all branching cards in the document for target dropdowns
  const allCards = useMemo(() => {
    const cards: CardInfo[] = [];
    editor.state.doc.descendants(n => {
      if (n.type.name === 'branchingCard') {
        cards.push({
          cardId: n.attrs.cardId as string,
          cardTitle: (n.attrs.cardTitle as string) || '(untitled)',
        });
      }
    });
    return cards;
  }, [editor.state.doc]);

  const getCardTitle = (cardId: string): string => {
    const card = allCards.find(c => c.cardId === cardId);
    return card ? card.cardTitle : '(unknown)';
  };

  const colors = TYPE_COLORS[attrs.cardType];

  const startEdit = () => {
    setDraft({ ...attrs, choices: [...attrs.choices] });
    setEditing(true);
  };

  const handleSave = () => {
    updateAttributes(draft);
    setEditing(false);
  };

  const handleCancel = () => {
    if (isNew) return;
    setDraft({ ...attrs, choices: [...attrs.choices] });
    setEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    e.stopPropagation();
  };

  const setChoice = (idx: number, patch: Partial<BranchingChoice>) => {
    const next = draft.choices.map((c, i) =>
      i === idx ? { ...c, ...patch } : c
    );
    setDraft({ ...draft, choices: next });
  };

  const addChoice = () => {
    setDraft({
      ...draft,
      choices: [
        ...draft.choices,
        { id: generateId(), text: '', targetCardId: '', feedback: '' },
      ],
    });
  };

  const removeChoice = (idx: number) => {
    if (draft.choices.length <= 2) return;
    setDraft({
      ...draft,
      choices: draft.choices.filter((_, i) => i !== idx),
    });
  };

  const handleTypeChange = (newType: CardType) => {
    if (newType === 'branch' && draft.choices.length < 2) {
      setDraft({
        ...draft,
        cardType: newType,
        choices: [
          { id: generateId(), text: '', targetCardId: '', feedback: '' },
          { id: generateId(), text: '', targetCardId: '', feedback: '' },
        ],
      });
    } else {
      setDraft({ ...draft, cardType: newType });
    }
  };

  // ── Edit mode ──────────────────────────────────────────────
  if (editing) {
    const editColors = TYPE_COLORS[draft.cardType];
    return (
      <NodeViewWrapper className='branching-card-node my-4'>
        <div
          className={`border-2 ${editColors.border} rounded-lg p-4 ${editColors.bg} space-y-3`}
        >
          {/* Header */}
          <div className='flex items-center gap-3'>
            <select
              value={draft.cardType}
              onChange={e => handleTypeChange(e.target.value as CardType)}
              onKeyDown={handleKeyDown}
              className='text-sm border border-gray-300 rounded px-2 py-1 bg-white'
            >
              {Object.entries(TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            <span className='text-xs text-gray-400'>
              ID: {draft.cardId.slice(0, 8)}
            </span>
          </div>

          {/* Title */}
          <input
            type='text'
            value={draft.cardTitle}
            onChange={e => setDraft({ ...draft, cardTitle: e.target.value })}
            onKeyDown={handleKeyDown}
            placeholder='Card title…'
            className='w-full border border-gray-300 rounded px-2 py-1 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-400'
          />

          {/* Content */}
          <textarea
            value={draft.cardContent}
            onChange={e => setDraft({ ...draft, cardContent: e.target.value })}
            onKeyDown={handleKeyDown}
            rows={3}
            placeholder='Card content…'
            className='w-full border border-gray-300 rounded p-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-400'
          />

          {/* Choices (branch type) */}
          {draft.cardType === 'branch' && (
            <div className='space-y-2'>
              <p className='text-sm font-medium text-gray-700'>Choices:</p>
              {draft.choices.map((choice, idx) => (
                <div key={choice.id} className='flex items-center gap-2'>
                  <input
                    type='text'
                    value={choice.text}
                    onChange={e => setChoice(idx, { text: e.target.value })}
                    onKeyDown={handleKeyDown}
                    placeholder={`Choice ${idx + 1}`}
                    className='flex-1 border border-gray-300 rounded px-2 py-1 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-amber-400'
                  />
                  <select
                    value={choice.targetCardId}
                    onChange={e =>
                      setChoice(idx, {
                        targetCardId: e.target.value,
                      })
                    }
                    onKeyDown={handleKeyDown}
                    className='text-sm border border-gray-300 rounded px-2 py-1 bg-white max-w-[200px]'
                  >
                    <option value=''>→ (select target)</option>
                    {allCards
                      .filter(c => c.cardId !== attrs.cardId)
                      .map(c => (
                        <option key={c.cardId} value={c.cardId}>
                          → {c.cardTitle}
                        </option>
                      ))}
                  </select>
                  {draft.choices.length > 2 && (
                    <button
                      type='button'
                      onMouseDown={e => {
                        e.preventDefault();
                        removeChoice(idx);
                      }}
                      className='text-red-400 hover:text-red-600 text-sm px-1'
                      title='Remove choice'
                    >
                      &times;
                    </button>
                  )}
                </div>
              ))}
              <button
                type='button'
                onMouseDown={e => {
                  e.preventDefault();
                  addChoice();
                }}
                className='text-sm text-amber-600 hover:text-amber-800'
              >
                + Add choice
              </button>
            </div>
          )}

          {/* Ending fields */}
          {draft.cardType === 'ending' && (
            <div className='space-y-2'>
              <label className='text-sm text-gray-600 flex items-center gap-1'>
                Score:
                <input
                  type='number'
                  min={0}
                  max={100}
                  value={draft.endScore}
                  onChange={e =>
                    setDraft({
                      ...draft,
                      endScore: Math.max(0, parseInt(e.target.value, 10) || 0),
                    })
                  }
                  onKeyDown={handleKeyDown}
                  className='w-20 border border-gray-300 rounded px-2 py-1 text-sm'
                />
              </label>
              <textarea
                value={draft.endMessage}
                onChange={e =>
                  setDraft({ ...draft, endMessage: e.target.value })
                }
                onKeyDown={handleKeyDown}
                rows={2}
                placeholder='End message…'
                className='w-full border border-gray-300 rounded p-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-pink-400'
              />
            </div>
          )}

          {/* Actions */}
          <div className='flex gap-2'>
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
            {!isNew && (
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

  // ── View mode ──────────────────────────────────────────────
  return (
    <NodeViewWrapper className='branching-card-node my-4'>
      <div className={`border-2 ${colors.border} rounded-lg p-4 bg-white`}>
        {/* Header badges */}
        <div className='flex items-center gap-2 mb-2'>
          <span
            className={`inline-block text-xs font-medium ${colors.badge} rounded-full px-2 py-0.5`}
          >
            {TYPE_LABELS[attrs.cardType]}
          </span>
          {attrs.cardType === 'ending' && (
            <span className='inline-block text-xs font-medium bg-gray-100 text-gray-600 rounded-full px-2 py-0.5'>
              Score: {attrs.endScore}
            </span>
          )}
        </div>

        {/* Title */}
        <p className='text-sm font-medium text-gray-800 mb-1'>
          {attrs.cardTitle || '(untitled card)'}
        </p>

        {/* Content preview */}
        {attrs.cardContent && (
          <p className='text-sm text-gray-600 mb-3 line-clamp-3'>
            {attrs.cardContent}
          </p>
        )}

        {/* Choices display (branch) */}
        {attrs.cardType === 'branch' && attrs.choices.length > 0 && (
          <ul className='space-y-1 mb-3'>
            {attrs.choices.map(choice => (
              <li key={choice.id} className='flex items-center gap-2 text-sm'>
                <span className='text-amber-500'>→</span>
                <span className='text-gray-700'>
                  {choice.text || '(empty)'}
                </span>
                {choice.targetCardId && (
                  <span className='text-xs text-gray-400'>
                    → {getCardTitle(choice.targetCardId)}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}

        {/* End message (ending) */}
        {attrs.cardType === 'ending' && attrs.endMessage && (
          <div className='bg-pink-50 border border-pink-200 rounded p-2 text-sm text-pink-700 mb-3'>
            {attrs.endMessage}
          </div>
        )}

        {/* Edit button */}
        <div className='flex justify-end'>
          <button
            type='button'
            onMouseDown={e => {
              e.preventDefault();
              startEdit();
            }}
            className='px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200'
          >
            Edit
          </button>
        </div>
      </div>
    </NodeViewWrapper>
  );
};

export default BranchingCardView;
