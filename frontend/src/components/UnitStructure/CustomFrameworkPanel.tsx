import { useState, useEffect, useCallback } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Loader2,
  Save,
  Plus,
  Trash2,
  Edit3,
  Check,
  X,
} from 'lucide-react';
import {
  learningOutcomesApi,
  accreditationApi,
} from '../../services/unitStructureApi';
import type {
  ULOResponse,
  CustomAlignmentFramework,
  FrameworkItem,
} from '../../types/unitStructure';
import toast from 'react-hot-toast';

interface CustomFrameworkPanelProps {
  unitId: string;
  framework: CustomAlignmentFramework;
  onDelete: () => void;
  onUpdate: (updated: CustomAlignmentFramework) => void;
}

const COLOR_MAP: Record<
  string,
  { bg: string; text: string; badge: string; border: string }
> = {
  indigo: {
    bg: 'bg-indigo-50',
    text: 'text-indigo-600',
    badge: 'bg-indigo-100 text-indigo-800',
    border: 'border-indigo-200',
  },
  amber: {
    bg: 'bg-amber-50',
    text: 'text-amber-600',
    badge: 'bg-amber-100 text-amber-800',
    border: 'border-amber-200',
  },
  emerald: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-600',
    badge: 'bg-emerald-100 text-emerald-800',
    border: 'border-emerald-200',
  },
  orange: {
    bg: 'bg-orange-50',
    text: 'text-orange-600',
    badge: 'bg-orange-100 text-orange-800',
    border: 'border-orange-200',
  },
  purple: {
    bg: 'bg-purple-50',
    text: 'text-purple-600',
    badge: 'bg-purple-100 text-purple-800',
    border: 'border-purple-200',
  },
  gray: {
    bg: 'bg-gray-50',
    text: 'text-gray-600',
    badge: 'bg-gray-100 text-gray-800',
    border: 'border-gray-200',
  },
};

export const CustomFrameworkPanel: React.FC<CustomFrameworkPanelProps> = ({
  unitId,
  framework,
  onDelete,
  onUpdate,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // Item CRUD state
  const [items, setItems] = useState<FrameworkItem[]>(framework.items);
  const [editingItem, setEditingItem] = useState<string | null>(null);
  const [editCode, setEditCode] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [addingItem, setAddingItem] = useState(false);
  const [newCode, setNewCode] = useState('');
  const [newDescription, setNewDescription] = useState('');

  // ULO→item mapping state
  const [ulos, setUlos] = useState<ULOResponse[]>([]);
  const [mappings, setMappings] = useState<Record<string, Set<string>>>({}); // uloId → Set<itemId>
  const [hasUnsavedMappings, setHasUnsavedMappings] = useState(false);

  const colors = COLOR_MAP[framework.colorHint ?? 'gray'] ?? COLOR_MAP.gray;

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const uloData = await learningOutcomesApi.getULOsByUnit(unitId, false);
      setUlos(uloData);

      // Load mappings for all ULOs
      const allMappings: Record<string, Set<string>> = {};
      await Promise.all(
        uloData.map(async ulo => {
          const uloMappings = await accreditationApi.getULOFrameworkMappings(
            ulo.id
          );
          // Filter to only items in this framework
          const frameworkItemIds = new Set(items.map(i => i.id));
          allMappings[ulo.id] = new Set(
            uloMappings
              .filter(m => frameworkItemIds.has(m.itemId))
              .map(m => m.itemId)
          );
        })
      );
      setMappings(allMappings);
      setHasUnsavedMappings(false);
    } catch {
      // Silently handle
    } finally {
      setLoading(false);
    }
  }, [unitId, items]);

  useEffect(() => {
    if (isExpanded) {
      loadData();
    }
  }, [isExpanded, loadData]);

  // Keep items in sync with framework prop
  useEffect(() => {
    setItems(framework.items);
  }, [framework.items]);

  // Item CRUD handlers
  const handleAddItem = async () => {
    if (!newCode.trim() || !newDescription.trim()) return;
    try {
      const created = await accreditationApi.addFrameworkItem(
        unitId,
        framework.id,
        {
          code: newCode.trim(),
          description: newDescription.trim(),
          orderIndex: items.length,
        }
      );
      const updatedItems = [...items, created];
      setItems(updatedItems);
      setNewCode('');
      setNewDescription('');
      setAddingItem(false);
      onUpdate({ ...framework, items: updatedItems });
      toast.success(`${created.code} added`);
    } catch {
      toast.error('Failed to add item');
    }
  };

  const handleStartEdit = (item: FrameworkItem) => {
    setEditingItem(item.id);
    setEditCode(item.code);
    setEditDescription(item.description);
  };

  const handleSaveEdit = async () => {
    if (!editingItem || !editCode.trim() || !editDescription.trim()) return;
    try {
      const updated = await accreditationApi.updateFrameworkItem(
        unitId,
        framework.id,
        editingItem,
        { code: editCode.trim(), description: editDescription.trim() }
      );
      const updatedItems = items.map(i => (i.id === editingItem ? updated : i));
      setItems(updatedItems);
      setEditingItem(null);
      onUpdate({ ...framework, items: updatedItems });
      toast.success('Item updated');
    } catch {
      toast.error('Failed to update item');
    }
  };

  const handleDeleteItem = async (itemId: string) => {
    try {
      await accreditationApi.deleteFrameworkItem(unitId, framework.id, itemId);
      const updatedItems = items.filter(i => i.id !== itemId);
      setItems(updatedItems);
      // Clean up mappings
      setMappings(prev => {
        const next: Record<string, Set<string>> = {};
        for (const [uloId, itemIds] of Object.entries(prev)) {
          const cleaned = new Set(itemIds);
          cleaned.delete(itemId);
          next[uloId] = cleaned;
        }
        return next;
      });
      onUpdate({ ...framework, items: updatedItems });
      toast.success('Item deleted');
    } catch {
      toast.error('Failed to delete item');
    }
  };

  const handleDeleteFramework = async () => {
    try {
      await accreditationApi.deleteFramework(unitId, framework.id);
      onDelete();
      toast.success(`${framework.name} deleted`);
    } catch {
      toast.error('Failed to delete framework');
    }
  };

  // Mapping toggle
  const handleToggleMapping = (uloId: string, itemId: string) => {
    setMappings(prev => {
      const uloSet = new Set(prev[uloId] ?? []);
      if (uloSet.has(itemId)) {
        uloSet.delete(itemId);
      } else {
        uloSet.add(itemId);
      }
      return { ...prev, [uloId]: uloSet };
    });
    setHasUnsavedMappings(true);
  };

  // Save all mappings
  const handleSaveMappings = async () => {
    setSaving(true);
    try {
      await Promise.all(
        ulos.map(async ulo => {
          const itemIds = Array.from(mappings[ulo.id] ?? []);
          await accreditationApi.updateULOFrameworkMappings(ulo.id, {
            mappings: itemIds.map(itemId => ({ itemId })),
          });
        })
      );
      setHasUnsavedMappings(false);
      toast.success('Mappings saved');
    } catch {
      toast.error('Failed to save mappings');
    } finally {
      setSaving(false);
    }
  };

  // Stats
  const mappedUloCount = ulos.filter(
    ulo => (mappings[ulo.id]?.size ?? 0) > 0
  ).length;

  return (
    <div className='bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden'>
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className='w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition'
      >
        <div className='flex items-center gap-3'>
          <span className='text-xl'>
            {framework.iconHint ?? '\uD83D\uDCCB'}
          </span>
          <div className='text-left'>
            <h3 className='font-semibold text-gray-900'>{framework.name}</h3>
            {framework.description && (
              <p className='text-xs text-gray-500'>{framework.description}</p>
            )}
          </div>
        </div>
        <div className='flex items-center gap-3'>
          {items.length > 0 && (
            <span
              className={`px-2 py-1 ${colors.badge} text-xs font-medium rounded-full`}
            >
              {items.length} items, {mappedUloCount} of {ulos.length} ULOs
              mapped
            </span>
          )}
          {isExpanded ? (
            <ChevronUp className='w-5 h-5 text-gray-400' />
          ) : (
            <ChevronDown className='w-5 h-5 text-gray-400' />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className='p-4'>
          {loading ? (
            <div className='flex items-center justify-center py-8'>
              <Loader2 className={`w-6 h-6 ${colors.text} animate-spin`} />
              <span className='ml-2 text-gray-500'>Loading...</span>
            </div>
          ) : (
            <>
              {/* Items List (CRUD) */}
              <div className='mb-6'>
                <div className='flex items-center justify-between mb-3'>
                  <h4 className='text-sm font-medium text-gray-700'>Items</h4>
                  <div className='flex items-center gap-2'>
                    {!addingItem && (
                      <button
                        onClick={() => setAddingItem(true)}
                        className={`flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium ${colors.text} ${colors.bg} rounded-lg hover:opacity-80 transition`}
                      >
                        <Plus className='w-3.5 h-3.5' />
                        Add Item
                      </button>
                    )}
                    <button
                      onClick={handleDeleteFramework}
                      className='flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition'
                    >
                      <Trash2 className='w-3.5 h-3.5' />
                      Delete Framework
                    </button>
                  </div>
                </div>

                {items.length === 0 && !addingItem && (
                  <p className='text-sm text-gray-500 py-4 text-center border border-dashed border-gray-200 rounded-lg'>
                    No items defined yet. Add items to map against your ULOs.
                  </p>
                )}

                <div className='space-y-2'>
                  {items.map(item => (
                    <div
                      key={item.id}
                      className='flex items-start gap-3 p-3 bg-gray-50 rounded-lg group'
                    >
                      {editingItem === item.id ? (
                        <>
                          <input
                            type='text'
                            value={editCode}
                            onChange={e => setEditCode(e.target.value)}
                            className='w-20 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500'
                            placeholder='Code'
                          />
                          <input
                            type='text'
                            value={editDescription}
                            onChange={e => setEditDescription(e.target.value)}
                            className='flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500'
                            placeholder='Description'
                          />
                          <button
                            onClick={handleSaveEdit}
                            className='p-1 text-green-600 hover:bg-green-50 rounded'
                          >
                            <Check className='w-4 h-4' />
                          </button>
                          <button
                            onClick={() => setEditingItem(null)}
                            className='p-1 text-gray-400 hover:bg-gray-100 rounded'
                          >
                            <X className='w-4 h-4' />
                          </button>
                        </>
                      ) : (
                        <>
                          <span
                            className={`px-2 py-0.5 ${colors.badge} text-xs font-bold rounded`}
                          >
                            {item.code}
                          </span>
                          <span className='flex-1 text-sm text-gray-700'>
                            {item.description}
                          </span>
                          <button
                            onClick={() => handleStartEdit(item)}
                            className='p-1 text-gray-400 hover:text-gray-600 opacity-0 group-hover:opacity-100 transition'
                          >
                            <Edit3 className='w-3.5 h-3.5' />
                          </button>
                          <button
                            onClick={() => handleDeleteItem(item.id)}
                            className='p-1 text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition'
                          >
                            <Trash2 className='w-3.5 h-3.5' />
                          </button>
                        </>
                      )}
                    </div>
                  ))}

                  {/* Add Item form */}
                  {addingItem && (
                    <div
                      className={`flex items-start gap-3 p-3 ${colors.bg} rounded-lg border ${colors.border}`}
                    >
                      <input
                        type='text'
                        value={newCode}
                        onChange={e => setNewCode(e.target.value)}
                        className='w-20 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500'
                        placeholder='Code'
                      />
                      <input
                        type='text'
                        value={newDescription}
                        onChange={e => setNewDescription(e.target.value)}
                        className='flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500'
                        placeholder='Description'
                        onKeyDown={e => {
                          if (e.key === 'Enter') handleAddItem();
                          if (e.key === 'Escape') setAddingItem(false);
                        }}
                      />
                      <button
                        onClick={handleAddItem}
                        disabled={!newCode.trim() || !newDescription.trim()}
                        className='p-1 text-green-600 hover:bg-green-50 rounded disabled:opacity-50'
                      >
                        <Check className='w-4 h-4' />
                      </button>
                      <button
                        onClick={() => {
                          setAddingItem(false);
                          setNewCode('');
                          setNewDescription('');
                        }}
                        className='p-1 text-gray-400 hover:bg-gray-100 rounded'
                      >
                        <X className='w-4 h-4' />
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* ULO→Item Mapping Matrix */}
              {items.length > 0 && ulos.length > 0 && (
                <div>
                  <div className='flex items-center justify-between mb-3'>
                    <h4 className='text-sm font-medium text-gray-700'>
                      ULO Alignment
                    </h4>
                    {hasUnsavedMappings && (
                      <button
                        onClick={handleSaveMappings}
                        disabled={saving}
                        className={`flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white
                               rounded-lg text-sm font-medium hover:bg-indigo-700 transition
                               disabled:opacity-50 disabled:cursor-not-allowed`}
                      >
                        {saving ? (
                          <Loader2 className='w-4 h-4 animate-spin' />
                        ) : (
                          <Save className='w-4 h-4' />
                        )}
                        Save Mappings
                      </button>
                    )}
                  </div>

                  <div className='border border-gray-200 rounded-lg overflow-x-auto'>
                    <table className='w-full'>
                      <thead>
                        <tr className='bg-gray-50'>
                          <th className='text-left px-4 py-2 text-sm font-medium text-gray-700 min-w-[200px]'>
                            ULO
                          </th>
                          {items.map(item => (
                            <th
                              key={item.id}
                              className='text-center px-2 py-2 text-sm font-medium text-gray-700 min-w-[60px]'
                              title={item.description}
                            >
                              {item.code}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {ulos.map((ulo, index) => {
                          const uloMappedCount = mappings[ulo.id]?.size ?? 0;
                          return (
                            <tr
                              key={ulo.id}
                              className={`border-t border-gray-100 ${
                                index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                              }`}
                            >
                              <td className='px-4 py-3'>
                                <div className='flex items-center gap-2'>
                                  <span
                                    className={`px-1.5 py-0.5 text-xs font-bold rounded ${
                                      uloMappedCount > 0
                                        ? colors.badge
                                        : 'bg-gray-100 text-gray-500'
                                    }`}
                                  >
                                    {ulo.code}
                                  </span>
                                  <span className='text-sm text-gray-600 truncate max-w-[300px]'>
                                    {ulo.description}
                                  </span>
                                </div>
                              </td>
                              {items.map(item => {
                                const isChecked =
                                  mappings[ulo.id]?.has(item.id) ?? false;
                                return (
                                  <td
                                    key={item.id}
                                    className='text-center px-2 py-3'
                                  >
                                    <button
                                      onClick={() =>
                                        handleToggleMapping(ulo.id, item.id)
                                      }
                                      className={`w-7 h-7 rounded border-2 flex items-center justify-center transition-all ${
                                        isChecked
                                          ? 'bg-indigo-600 border-indigo-600 text-white'
                                          : 'bg-white border-gray-300 hover:border-indigo-400'
                                      }`}
                                    >
                                      {isChecked && (
                                        <Check className='w-4 h-4' />
                                      )}
                                    </button>
                                  </td>
                                );
                              })}
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  <p className='mt-2 text-xs text-gray-400 text-right'>
                    Click checkboxes to map ULOs to items, then save
                  </p>
                </div>
              )}

              {items.length > 0 && ulos.length === 0 && (
                <p className='text-sm text-gray-500 py-4 text-center'>
                  Add Unit Learning Outcomes first to create mappings.
                </p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default CustomFrameworkPanel;
