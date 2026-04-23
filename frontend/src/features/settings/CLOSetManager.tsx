import { useCallback, useEffect, useState } from 'react';
import {
  Check,
  ChevronDown,
  ChevronUp,
  GraduationCap,
  Loader2,
  Pencil,
  Plus,
  Trash2,
  X,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { cloSetsApi } from '../../services/cloSetsApi';
import type { CLOItem, CLOSet } from '../../types/cloSets';

interface EditingSet {
  id: string;
  name: string;
  description: string;
  programCode: string;
}

interface EditingItem {
  id: string;
  code: string;
  description: string;
}

const CLOSetManager: React.FC = () => {
  const [sets, setSets] = useState<CLOSet[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedSetId, setExpandedSetId] = useState<string | null>(null);
  const [editingSet, setEditingSet] = useState<EditingSet | null>(null);
  const [editingItem, setEditingItem] = useState<EditingItem | null>(null);
  const [newSetName, setNewSetName] = useState('');
  const [newSetCode, setNewSetCode] = useState('');
  const [showNewSetForm, setShowNewSetForm] = useState(false);
  const [newItemCode, setNewItemCode] = useState('');
  const [newItemDesc, setNewItemDesc] = useState('');
  const [addingItemToSetId, setAddingItemToSetId] = useState<string | null>(
    null
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await cloSetsApi.listCLOSets();
      setSets(data);
    } catch {
      toast.error('Failed to load CLO sets');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreateSet = async () => {
    if (!newSetName.trim()) return;
    try {
      const created = await cloSetsApi.createCLOSet({
        name: newSetName.trim(),
        ...(newSetCode.trim() ? { programCode: newSetCode.trim() } : {}),
      });
      setSets(prev => [...prev, created]);
      setNewSetName('');
      setNewSetCode('');
      setShowNewSetForm(false);
      setExpandedSetId(created.id);
      toast.success('CLO set created');
    } catch {
      toast.error('Failed to create CLO set');
    }
  };

  const handleSaveSetEdit = async () => {
    if (!editingSet) return;
    try {
      const updated = await cloSetsApi.updateCLOSet(editingSet.id, {
        name: editingSet.name,
        ...(editingSet.description
          ? { description: editingSet.description }
          : {}),
        ...(editingSet.programCode
          ? { programCode: editingSet.programCode }
          : {}),
      });
      setSets(prev => prev.map(s => (s.id === updated.id ? updated : s)));
      setEditingSet(null);
      toast.success('Saved');
    } catch {
      toast.error('Failed to save');
    }
  };

  const handleDeleteSet = async (setId: string) => {
    if (
      !window.confirm(
        'Delete this CLO set? It will be unassigned from all units.'
      )
    )
      return;
    try {
      await cloSetsApi.deleteCLOSet(setId);
      setSets(prev => prev.filter(s => s.id !== setId));
      toast.success('CLO set deleted');
    } catch {
      toast.error('Failed to delete CLO set');
    }
  };

  const handleAddItem = async (setId: string) => {
    if (!newItemCode.trim() || !newItemDesc.trim()) return;
    try {
      const item = await cloSetsApi.addCLOItem(setId, {
        code: newItemCode.trim(),
        description: newItemDesc.trim(),
        orderIndex: sets.find(s => s.id === setId)?.items.length ?? 0,
      });
      setSets(prev =>
        prev.map(s =>
          s.id === setId ? { ...s, items: [...s.items, item] } : s
        )
      );
      setNewItemCode('');
      setNewItemDesc('');
      setAddingItemToSetId(null);
      toast.success('CLO item added');
    } catch {
      toast.error('Failed to add item');
    }
  };

  const handleSaveItemEdit = async (setId: string) => {
    if (!editingItem) return;
    try {
      const updated = await cloSetsApi.updateCLOItem(setId, editingItem.id, {
        code: editingItem.code,
        description: editingItem.description,
      });
      setSets(prev =>
        prev.map(s =>
          s.id === setId
            ? {
                ...s,
                items: s.items.map((i: CLOItem) =>
                  i.id === updated.id ? updated : i
                ),
              }
            : s
        )
      );
      setEditingItem(null);
      toast.success('Saved');
    } catch {
      toast.error('Failed to save item');
    }
  };

  const handleDeleteItem = async (setId: string, itemId: string) => {
    try {
      await cloSetsApi.deleteCLOItem(setId, itemId);
      setSets(prev =>
        prev.map(s =>
          s.id === setId
            ? { ...s, items: s.items.filter((i: CLOItem) => i.id !== itemId) }
            : s
        )
      );
    } catch {
      toast.error('Failed to delete item');
    }
  };

  if (loading) {
    return (
      <div className='flex items-center gap-2 text-gray-500 py-8'>
        <Loader2 className='h-4 w-4 animate-spin' />
        Loading CLO sets...
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      <div className='flex items-center justify-between'>
        <div>
          <h2 className='text-lg font-semibold text-gray-900'>
            Course Learning Outcome Sets
          </h2>
          <p className='text-sm text-gray-500 mt-1'>
            Define CLO sets for your degree programs. Assign them to units and
            map ULOs to CLOs in the unit&apos;s alignment panel.
          </p>
        </div>
        <button
          onClick={() => setShowNewSetForm(true)}
          className='flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700'
        >
          <Plus className='h-4 w-4' />
          New CLO Set
        </button>
      </div>

      {showNewSetForm && (
        <div className='border border-blue-200 rounded-lg p-4 bg-blue-50 space-y-3'>
          <h3 className='font-medium text-gray-900 text-sm'>New CLO Set</h3>
          <div className='grid grid-cols-2 gap-3'>
            <input
              type='text'
              placeholder='Program name (e.g. Bachelor of CS)'
              value={newSetName}
              onChange={e => setNewSetName(e.target.value)}
              className='col-span-2 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
            />
            <input
              type='text'
              placeholder='Short code (e.g. BCS)'
              value={newSetCode}
              onChange={e => setNewSetCode(e.target.value)}
              className='border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
            />
          </div>
          <div className='flex gap-2'>
            <button
              onClick={handleCreateSet}
              disabled={!newSetName.trim()}
              className='px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50'
            >
              Create
            </button>
            <button
              onClick={() => setShowNewSetForm(false)}
              className='px-3 py-1.5 border border-gray-300 rounded text-sm hover:bg-gray-50'
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {sets.length === 0 && !showNewSetForm && (
        <div className='text-center py-12 text-gray-500'>
          <GraduationCap className='h-10 w-10 mx-auto mb-3 text-gray-300' />
          <p className='text-sm'>No CLO sets yet. Create one to get started.</p>
        </div>
      )}

      <div className='space-y-3'>
        {sets.map(cloSet => (
          <div
            key={cloSet.id}
            className='border border-gray-200 rounded-lg overflow-hidden'
          >
            {/* Set header */}
            <div className='flex items-center justify-between px-4 py-3 bg-gray-50'>
              {editingSet?.id === cloSet.id ? (
                <div className='flex items-center gap-2 flex-1'>
                  <input
                    value={editingSet.name}
                    onChange={e =>
                      setEditingSet({ ...editingSet, name: e.target.value })
                    }
                    className='border border-gray-300 rounded px-2 py-1 text-sm flex-1 focus:outline-none focus:ring-2 focus:ring-blue-500'
                  />
                  <input
                    value={editingSet.programCode}
                    onChange={e =>
                      setEditingSet({
                        ...editingSet,
                        programCode: e.target.value,
                      })
                    }
                    placeholder='Code'
                    className='border border-gray-300 rounded px-2 py-1 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-blue-500'
                  />
                  <button
                    onClick={handleSaveSetEdit}
                    className='p-1 text-green-600 hover:text-green-700'
                  >
                    <Check className='h-4 w-4' />
                  </button>
                  <button
                    onClick={() => setEditingSet(null)}
                    className='p-1 text-gray-400 hover:text-gray-600'
                  >
                    <X className='h-4 w-4' />
                  </button>
                </div>
              ) : (
                <div className='flex items-center gap-3 flex-1'>
                  <GraduationCap className='h-5 w-5 text-blue-500 shrink-0' />
                  <div>
                    <span className='font-medium text-gray-900 text-sm'>
                      {cloSet.name}
                    </span>
                    {cloSet.programCode && (
                      <span className='ml-2 text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded'>
                        {cloSet.programCode}
                      </span>
                    )}
                    <span className='ml-2 text-xs text-gray-400'>
                      {cloSet.items.length} CLO
                      {cloSet.items.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>
              )}
              <div className='flex items-center gap-1'>
                <button
                  onClick={() =>
                    setEditingSet({
                      id: cloSet.id,
                      name: cloSet.name,
                      description: cloSet.description ?? '',
                      programCode: cloSet.programCode ?? '',
                    })
                  }
                  className='p-1.5 text-gray-400 hover:text-gray-600 rounded'
                >
                  <Pencil className='h-3.5 w-3.5' />
                </button>
                <button
                  onClick={() => handleDeleteSet(cloSet.id)}
                  className='p-1.5 text-gray-400 hover:text-red-500 rounded'
                >
                  <Trash2 className='h-3.5 w-3.5' />
                </button>
                <button
                  onClick={() =>
                    setExpandedSetId(
                      expandedSetId === cloSet.id ? null : cloSet.id
                    )
                  }
                  className='p-1.5 text-gray-400 hover:text-gray-600 rounded'
                >
                  {expandedSetId === cloSet.id ? (
                    <ChevronUp className='h-4 w-4' />
                  ) : (
                    <ChevronDown className='h-4 w-4' />
                  )}
                </button>
              </div>
            </div>

            {/* Items */}
            {expandedSetId === cloSet.id && (
              <div className='divide-y divide-gray-100'>
                {cloSet.items.map((item: CLOItem) => (
                  <div
                    key={item.id}
                    className='px-4 py-2.5 flex items-start gap-3'
                  >
                    {editingItem?.id === item.id ? (
                      <div className='flex items-center gap-2 flex-1'>
                        <input
                          value={editingItem.code}
                          onChange={e =>
                            setEditingItem({
                              ...editingItem,
                              code: e.target.value,
                            })
                          }
                          className='border border-gray-300 rounded px-2 py-1 text-sm w-20 focus:outline-none focus:ring-2 focus:ring-blue-500'
                        />
                        <input
                          value={editingItem.description}
                          onChange={e =>
                            setEditingItem({
                              ...editingItem,
                              description: e.target.value,
                            })
                          }
                          className='border border-gray-300 rounded px-2 py-1 text-sm flex-1 focus:outline-none focus:ring-2 focus:ring-blue-500'
                        />
                        <button
                          onClick={() => handleSaveItemEdit(cloSet.id)}
                          className='p-1 text-green-600 hover:text-green-700'
                        >
                          <Check className='h-4 w-4' />
                        </button>
                        <button
                          onClick={() => setEditingItem(null)}
                          className='p-1 text-gray-400 hover:text-gray-600'
                        >
                          <X className='h-4 w-4' />
                        </button>
                      </div>
                    ) : (
                      <>
                        <span className='text-xs font-mono bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded shrink-0 mt-0.5'>
                          {item.code}
                        </span>
                        <span className='text-sm text-gray-700 flex-1'>
                          {item.description}
                        </span>
                        <div className='flex items-center gap-1 shrink-0'>
                          <button
                            onClick={() =>
                              setEditingItem({
                                id: item.id,
                                code: item.code,
                                description: item.description,
                              })
                            }
                            className='p-1 text-gray-300 hover:text-gray-500'
                          >
                            <Pencil className='h-3 w-3' />
                          </button>
                          <button
                            onClick={() => handleDeleteItem(cloSet.id, item.id)}
                            className='p-1 text-gray-300 hover:text-red-500'
                          >
                            <Trash2 className='h-3 w-3' />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ))}

                {/* Add item row */}
                {addingItemToSetId === cloSet.id ? (
                  <div className='px-4 py-2.5 flex items-center gap-2 bg-gray-50'>
                    <input
                      placeholder='CLO1'
                      value={newItemCode}
                      onChange={e => setNewItemCode(e.target.value)}
                      className='border border-gray-300 rounded px-2 py-1 text-sm w-20 focus:outline-none focus:ring-2 focus:ring-blue-500'
                    />
                    <input
                      placeholder='Outcome description...'
                      value={newItemDesc}
                      onChange={e => setNewItemDesc(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === 'Enter') handleAddItem(cloSet.id);
                      }}
                      className='border border-gray-300 rounded px-2 py-1 text-sm flex-1 focus:outline-none focus:ring-2 focus:ring-blue-500'
                    />
                    <button
                      onClick={() => handleAddItem(cloSet.id)}
                      disabled={!newItemCode.trim() || !newItemDesc.trim()}
                      className='p-1 text-green-600 hover:text-green-700 disabled:opacity-40'
                    >
                      <Check className='h-4 w-4' />
                    </button>
                    <button
                      onClick={() => {
                        setAddingItemToSetId(null);
                        setNewItemCode('');
                        setNewItemDesc('');
                      }}
                      className='p-1 text-gray-400 hover:text-gray-600'
                    >
                      <X className='h-4 w-4' />
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setAddingItemToSetId(cloSet.id)}
                    className='w-full px-4 py-2 text-sm text-gray-400 hover:text-blue-600 hover:bg-blue-50 text-left flex items-center gap-2'
                  >
                    <Plus className='h-3.5 w-3.5' />
                    Add CLO item
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default CLOSetManager;
