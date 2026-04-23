import { useState, useEffect, useCallback } from 'react';
import {
  ChevronDown,
  ChevronUp,
  GraduationCap,
  Loader2,
  Sparkles,
  Check,
  X,
  Target,
  Plus,
  Minus,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { cloSetsApi } from '../../services/cloSetsApi';
import { learningOutcomesApi } from '../../services/unitStructureApi';
import type { CLOItem, CLOSet } from '../../types/cloSets';
import type { ULOResponse } from '../../types/unitStructure';

interface CLOMappingPanelProps {
  unitId: string;
}

interface ULOWithMappings {
  ulo: ULOResponse;
  mappedCloItemIds: Set<string>;
}

export const CLOMappingPanel: React.FC<CLOMappingPanelProps> = ({ unitId }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [assignedSets, setAssignedSets] = useState<CLOSet[]>([]);
  const [allSets, setAllSets] = useState<CLOSet[]>([]);
  const [ulosWithMappings, setUlosWithMappings] = useState<ULOWithMappings[]>(
    []
  );
  const [suggesting, setSuggesting] = useState(false);
  const [pendingSuggestions, setPendingSuggestions] = useState<
    Map<string, string[]>
  >(new Map());
  const [showAssignPicker, setShowAssignPicker] = useState(false);
  const [savingMap, setSavingMap] = useState<Map<string, boolean>>(new Map());

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [assigned, all, ulos] = await Promise.all([
        cloSetsApi.getUnitCLOSets(unitId),
        cloSetsApi.listCLOSets(),
        learningOutcomesApi.getULOsByUnit(unitId, false),
      ]);
      setAssignedSets(assigned);
      setAllSets(all);

      const withMappings: ULOWithMappings[] = await Promise.all(
        ulos.map(async ulo => {
          try {
            const mappings = await cloSetsApi.getULOCLOMappings(ulo.id);
            return {
              ulo,
              mappedCloItemIds: new Set(mappings.map(m => m.cloItemId)),
            };
          } catch {
            return { ulo, mappedCloItemIds: new Set<string>() };
          }
        })
      );
      setUlosWithMappings(withMappings);
    } catch {
      toast.error('Failed to load CLO mapping data');
    } finally {
      setLoading(false);
    }
  }, [unitId]);

  useEffect(() => {
    if (isExpanded) {
      loadData();
    }
  }, [isExpanded, loadData]);

  const toggleMapping = async (uloId: string, cloItemId: string) => {
    const entry = ulosWithMappings.find(u => u.ulo.id === uloId);
    if (!entry) return;

    const alreadyMapped = entry.mappedCloItemIds.has(cloItemId);
    const newIds = new Set(entry.mappedCloItemIds);
    if (alreadyMapped) {
      newIds.delete(cloItemId);
    } else {
      newIds.add(cloItemId);
    }

    setSavingMap(prev => new Map(prev).set(uloId, true));
    try {
      await cloSetsApi.setULOCLOMappings(uloId, {
        cloItemIds: Array.from(newIds),
      });
      setUlosWithMappings(prev =>
        prev.map(u =>
          u.ulo.id === uloId ? { ...u, mappedCloItemIds: newIds } : u
        )
      );
    } catch {
      toast.error('Failed to save mapping');
    } finally {
      setSavingMap(prev => {
        const next = new Map(prev);
        next.delete(uloId);
        return next;
      });
    }
  };

  const handleSuggest = async () => {
    setSuggesting(true);
    try {
      const result = await cloSetsApi.suggestCLOMappings(unitId);
      const map = new Map<string, string[]>();
      for (const { uloId, cloItemId } of result.suggestions) {
        const existing = map.get(uloId) ?? [];
        map.set(uloId, [...existing, cloItemId]);
      }
      setPendingSuggestions(map);
      toast.success(
        `${result.suggestions.length} suggestions — review and accept`
      );
    } catch {
      toast.error('Failed to get AI suggestions');
    } finally {
      setSuggesting(false);
    }
  };

  const acceptSuggestions = async (uloId: string) => {
    const suggestions = pendingSuggestions.get(uloId);
    if (!suggestions) return;

    const entry = ulosWithMappings.find(u => u.ulo.id === uloId);
    if (!entry) return;

    const mergedIds = new Set([...entry.mappedCloItemIds, ...suggestions]);
    setSavingMap(prev => new Map(prev).set(uloId, true));
    try {
      await cloSetsApi.setULOCLOMappings(uloId, {
        cloItemIds: Array.from(mergedIds),
        isAiSuggested: true,
      });
      setUlosWithMappings(prev =>
        prev.map(u =>
          u.ulo.id === uloId ? { ...u, mappedCloItemIds: mergedIds } : u
        )
      );
      setPendingSuggestions(prev => {
        const next = new Map(prev);
        next.delete(uloId);
        return next;
      });
    } catch {
      toast.error('Failed to save suggestions');
    } finally {
      setSavingMap(prev => {
        const next = new Map(prev);
        next.delete(uloId);
        return next;
      });
    }
  };

  const rejectSuggestions = (uloId: string) => {
    setPendingSuggestions(prev => {
      const next = new Map(prev);
      next.delete(uloId);
      return next;
    });
  };

  const assignSet = async (setId: string) => {
    try {
      await cloSetsApi.assignCLOSet(unitId, setId);
      const set = allSets.find(s => s.id === setId);
      if (set) setAssignedSets(prev => [...prev, set]);
      setShowAssignPicker(false);
      toast.success('CLO set assigned');
    } catch {
      toast.error('Failed to assign CLO set');
    }
  };

  const unassignSet = async (setId: string) => {
    try {
      await cloSetsApi.unassignCLOSet(unitId, setId);
      setAssignedSets(prev => prev.filter(s => s.id !== setId));
    } catch {
      toast.error('Failed to unassign CLO set');
    }
  };

  const totalULOs = ulosWithMappings.length;
  const mappedULOs = ulosWithMappings.filter(
    u => u.mappedCloItemIds.size > 0
  ).length;

  const allCloItems: CLOItem[] = assignedSets.flatMap(s => s.items);

  const unassignedSets = allSets.filter(
    s => !assignedSets.some(a => a.id === s.id)
  );

  return (
    <div className='bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden'>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className='w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition'
      >
        <div className='flex items-center gap-3'>
          <GraduationCap className='w-5 h-5 text-blue-600' />
          <div className='text-left'>
            <h3 className='font-semibold text-gray-900'>
              Course Learning Outcomes
            </h3>
            <p className='text-xs text-gray-500'>
              Map ULOs to CLOs from assigned degree program sets
            </p>
          </div>
        </div>
        <div className='flex items-center gap-3'>
          {totalULOs > 0 && (
            <span className='px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full'>
              {mappedULOs} of {totalULOs} ULOs mapped
            </span>
          )}
          {isExpanded ? (
            <ChevronUp className='w-5 h-5 text-gray-400' />
          ) : (
            <ChevronDown className='w-5 h-5 text-gray-400' />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className='p-4 space-y-4'>
          {loading ? (
            <div className='flex items-center justify-center py-8'>
              <Loader2 className='w-6 h-6 text-blue-600 animate-spin' />
              <span className='ml-2 text-gray-500'>Loading...</span>
            </div>
          ) : (
            <>
              {/* Assigned CLO sets */}
              <div>
                <div className='flex items-center justify-between mb-2'>
                  <p className='text-sm font-medium text-gray-700'>
                    Assigned CLO Sets
                  </p>
                  <button
                    onClick={() => setShowAssignPicker(v => !v)}
                    className='flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800'
                  >
                    <Plus className='h-3.5 w-3.5' />
                    Assign set
                  </button>
                </div>

                {showAssignPicker && unassignedSets.length > 0 && (
                  <div className='mb-3 border border-blue-200 rounded-lg p-2 bg-blue-50 space-y-1'>
                    {unassignedSets.map(s => (
                      <button
                        key={s.id}
                        onClick={() => assignSet(s.id)}
                        className='w-full text-left px-3 py-1.5 rounded hover:bg-blue-100 text-sm flex items-center justify-between gap-2'
                      >
                        <span className='font-medium'>{s.name}</span>
                        {s.programCode && (
                          <span className='text-xs bg-blue-200 text-blue-700 px-1.5 rounded'>
                            {s.programCode}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                )}

                {showAssignPicker && unassignedSets.length === 0 && (
                  <p className='text-xs text-gray-400 mb-3'>
                    All CLO sets are already assigned.
                  </p>
                )}

                {assignedSets.length === 0 ? (
                  <p className='text-sm text-gray-400 py-2'>
                    No CLO sets assigned. Assign one above, or create sets in
                    Settings → CLO Sets.
                  </p>
                ) : (
                  <div className='flex flex-wrap gap-2'>
                    {assignedSets.map(s => (
                      <div
                        key={s.id}
                        className='flex items-center gap-1.5 bg-blue-50 border border-blue-200 rounded-full px-3 py-1 text-sm text-blue-800'
                      >
                        <GraduationCap className='h-3.5 w-3.5' />
                        <span>{s.name}</span>
                        {s.programCode && (
                          <span className='text-xs text-blue-500'>
                            ({s.programCode})
                          </span>
                        )}
                        <button
                          onClick={() => unassignSet(s.id)}
                          className='ml-1 text-blue-400 hover:text-red-500'
                        >
                          <Minus className='h-3 w-3' />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* ULO mappings */}
              {assignedSets.length > 0 && allCloItems.length > 0 && (
                <div className='border-t border-gray-100 pt-4'>
                  <div className='flex items-center justify-between mb-3'>
                    <p className='text-sm font-medium text-gray-700'>
                      ULO → CLO Mappings
                    </p>
                    <button
                      onClick={handleSuggest}
                      disabled={suggesting || totalULOs === 0}
                      className='flex items-center gap-1.5 text-xs px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50'
                    >
                      {suggesting ? (
                        <Loader2 className='h-3.5 w-3.5 animate-spin' />
                      ) : (
                        <Sparkles className='h-3.5 w-3.5' />
                      )}
                      AI Suggest
                    </button>
                  </div>

                  {totalULOs === 0 ? (
                    <div className='text-center py-6 text-gray-400'>
                      <Target className='w-7 h-7 mx-auto mb-2 text-gray-300' />
                      <p className='text-sm'>No ULOs defined yet.</p>
                    </div>
                  ) : (
                    <div className='space-y-4'>
                      {ulosWithMappings.map(({ ulo, mappedCloItemIds }) => {
                        const suggestions = pendingSuggestions.get(ulo.id);
                        const isSaving = savingMap.get(ulo.id) ?? false;

                        return (
                          <div
                            key={ulo.id}
                            className='border border-gray-100 rounded-lg p-3'
                          >
                            <div className='flex items-start gap-2 mb-2'>
                              {isSaving && (
                                <Loader2 className='h-3.5 w-3.5 animate-spin text-blue-500 mt-0.5 shrink-0' />
                              )}
                              <p className='text-sm text-gray-800 flex-1'>
                                <span className='font-mono text-xs bg-gray-100 px-1 rounded mr-1'>
                                  {ulo.code}
                                </span>
                                {ulo.description}
                              </p>
                            </div>

                            {/* Pending suggestions banner */}
                            {suggestions && suggestions.length > 0 && (
                              <div className='mb-2 flex items-center gap-2 text-xs bg-purple-50 border border-purple-200 rounded px-2 py-1.5'>
                                <Sparkles className='h-3.5 w-3.5 text-purple-500 shrink-0' />
                                <span className='flex-1 text-purple-700'>
                                  AI suggests:{' '}
                                  {suggestions
                                    .map(
                                      id =>
                                        allCloItems.find(c => c.id === id)
                                          ?.code ?? id
                                    )
                                    .join(', ')}
                                </span>
                                <button
                                  onClick={() => acceptSuggestions(ulo.id)}
                                  className='text-green-600 hover:text-green-800'
                                >
                                  <Check className='h-4 w-4' />
                                </button>
                                <button
                                  onClick={() => rejectSuggestions(ulo.id)}
                                  className='text-gray-400 hover:text-gray-600'
                                >
                                  <X className='h-4 w-4' />
                                </button>
                              </div>
                            )}

                            {/* CLO item chips */}
                            <div className='flex flex-wrap gap-1.5'>
                              {assignedSets.map(set => (
                                <div key={set.id} className='contents'>
                                  {set.items.map(item => {
                                    const isMapped = mappedCloItemIds.has(
                                      item.id
                                    );
                                    const isSuggested =
                                      suggestions?.includes(item.id) ?? false;
                                    return (
                                      <button
                                        key={item.id}
                                        onClick={() =>
                                          toggleMapping(ulo.id, item.id)
                                        }
                                        disabled={isSaving}
                                        title={item.description}
                                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono border transition ${
                                          isMapped
                                            ? 'bg-blue-600 text-white border-blue-600'
                                            : isSuggested
                                              ? 'bg-purple-100 text-purple-700 border-purple-300'
                                              : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
                                        }`}
                                      >
                                        {item.code}
                                      </button>
                                    );
                                  })}
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {assignedSets.length > 0 && allCloItems.length === 0 && (
                <p className='text-sm text-gray-400 border-t border-gray-100 pt-4'>
                  No CLO items in the assigned sets yet. Add items via Settings
                  → CLO Sets.
                </p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default CLOMappingPanel;
