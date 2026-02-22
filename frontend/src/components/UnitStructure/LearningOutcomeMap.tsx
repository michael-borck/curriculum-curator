import { useState, useEffect, useCallback } from 'react';
import {
  X,
  ChevronDown,
  ChevronRight,
  Target,
  BookOpen,
  FileText,
  Loader2,
  AlertCircle,
  Sparkles,
  Save,
  Edit3,
  Check,
} from 'lucide-react';
import {
  learningOutcomesApi,
  materialsApi,
  accreditationApi,
} from '../../services/unitStructureApi';
import {
  ULOWithMappings,
  MaterialWithOutcomes,
  GraduateCapabilityCode,
} from '../../types/unitStructure';
import {
  GraduateCapability,
  GRADUATE_CAPABILITIES,
  getTopCapabilitySuggestions,
  getCapabilityByCode,
} from '../../constants/graduateCapabilities';
import toast from 'react-hot-toast';

interface LearningOutcomeMapProps {
  unitId: string;
  isOpen: boolean;
  onClose: () => void;
  topicLabel?: string | undefined;
}

interface TreeNode {
  id: string;
  type: 'ulo' | 'week' | 'material' | 'llo';
  label: string;
  sublabel?: string;
  children: TreeNode[];
  isExpanded?: boolean;
  metadata?: Record<string, unknown>;
  suggestedCapabilities?: GraduateCapability[];
  savedCapabilities?: GraduateCapability[];
  uloId?: string; // Store the actual ULO ID for saving
}

// Track capability mappings per ULO
interface ULOCapabilityState {
  saved: GraduateCapabilityCode[];
  current: GraduateCapabilityCode[];
  suggested: GraduateCapabilityCode[];
}

const BLOOM_COLORS: Record<string, string> = {
  remember: 'bg-blue-100 text-blue-800',
  understand: 'bg-green-100 text-green-800',
  apply: 'bg-yellow-100 text-yellow-800',
  analyze: 'bg-orange-100 text-orange-800',
  evaluate: 'bg-purple-100 text-purple-800',
  create: 'bg-red-100 text-red-800',
};

export const LearningOutcomeMap: React.FC<LearningOutcomeMapProps> = ({
  unitId,
  isOpen,
  onClose,
  topicLabel = 'Week',
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [hoveredCapability, setHoveredCapability] =
    useState<GraduateCapability | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  // Track capability mappings per ULO
  const [capabilityStates, setCapabilityStates] = useState<
    Map<string, ULOCapabilityState>
  >(new Map());
  const [editingUloId, setEditingUloId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Check if there are unsaved changes
  const hasUnsavedChanges = Array.from(capabilityStates.values()).some(
    state =>
      state.saved.length !== state.current.length ||
      !state.saved.every(s => state.current.includes(s))
  );

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Load ULOs with mappings
      const ulos = await learningOutcomesApi.getULOsByUnit(unitId, true);

      // Load all materials
      const materials = await materialsApi.getMaterialsByUnit(unitId);

      // Load materials with outcomes for LLO data
      const materialsWithOutcomes: MaterialWithOutcomes[] = await Promise.all(
        materials.map(m => materialsApi.getMaterial(m.id, true))
      );

      // Load existing GC mappings for each ULO
      const newCapabilityStates = new Map<string, ULOCapabilityState>();

      for (const ulo of ulos) {
        try {
          const gcMappings = await accreditationApi.getULOGraduateCapabilities(
            ulo.id
          );
          const savedCodes = gcMappings.map(
            m => m.capabilityCode as GraduateCapabilityCode
          );
          const suggestedCodes = getTopCapabilitySuggestions(
            ulo.description,
            ulo.bloomLevel,
            3
          ).map(gc => gc.code as GraduateCapabilityCode);

          newCapabilityStates.set(ulo.id, {
            saved: savedCodes,
            current: savedCodes.length > 0 ? [...savedCodes] : [],
            suggested: suggestedCodes,
          });
        } catch {
          // API might not exist - use suggestions only
          const suggestedCodes = getTopCapabilitySuggestions(
            ulo.description,
            ulo.bloomLevel,
            3
          ).map(gc => gc.code as GraduateCapabilityCode);

          newCapabilityStates.set(ulo.id, {
            saved: [],
            current: [],
            suggested: suggestedCodes,
          });
        }
      }

      setCapabilityStates(newCapabilityStates);

      // Build tree structure
      const tree = buildTree(ulos, materialsWithOutcomes, newCapabilityStates);
      setTreeData(tree);

      // Auto-expand ULOs
      const initialExpanded = new Set(ulos.map(ulo => `ulo-${ulo.id}`));
      setExpandedNodes(initialExpanded);
    } catch (err) {
      console.error('Error loading learning outcome data:', err);
      setError('Failed to load learning outcome hierarchy');
    } finally {
      setLoading(false);
    }
  }, [unitId]);

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen, loadData]);

  const buildTree = (
    ulos: ULOWithMappings[],
    materials: MaterialWithOutcomes[],
    capStates: Map<string, ULOCapabilityState>
  ): TreeNode[] => {
    // Group materials by week
    const materialsByWeek = new Map<number, MaterialWithOutcomes[]>();
    materials.forEach(m => {
      const week = m.weekNumber;
      if (!materialsByWeek.has(week)) {
        materialsByWeek.set(week, []);
      }
      materialsByWeek.get(week)!.push(m);
    });

    // Build tree for each ULO
    return ulos.map(ulo => {
      // Find materials mapped to this ULO
      const mappedMaterials = materials.filter(m =>
        m.mappedUlos?.some(u => u.id === ulo.id)
      );

      // Group mapped materials by week
      const weekNodes: TreeNode[] = [];
      const weekGroups = new Map<number, MaterialWithOutcomes[]>();

      mappedMaterials.forEach(m => {
        if (!weekGroups.has(m.weekNumber)) {
          weekGroups.set(m.weekNumber, []);
        }
        weekGroups.get(m.weekNumber)!.push(m);
      });

      // Sort weeks and create nodes
      Array.from(weekGroups.entries())
        .sort((a, b) => a[0] - b[0])
        .forEach(([weekNum, weekMaterials]) => {
          const materialNodes: TreeNode[] = weekMaterials.map(m => {
            // Get LLOs for this material
            const lloNodes: TreeNode[] = (m.localOutcomes || []).map(llo => ({
              id: `llo-${llo.id}`,
              type: 'llo' as const,
              label: llo.description,
              children: [],
            }));

            return {
              id: `material-${m.id}`,
              type: 'material' as const,
              label: m.title,
              sublabel: m.type,
              children: lloNodes,
              metadata: { type: m.type, duration: m.durationMinutes },
            };
          });

          weekNodes.push({
            id: `week-${ulo.id}-${weekNum}`,
            type: 'week' as const,
            label: `${topicLabel} ${weekNum}`,
            children: materialNodes,
          });
        });

      // Get capabilities from state
      const capState = capStates.get(ulo.id);
      const currentCaps = capState?.current || [];
      const suggestedCaps = capState?.suggested || [];

      // Convert codes to GraduateCapability objects
      const savedCapabilities = currentCaps
        .map(code => getCapabilityByCode(code))
        .filter((gc): gc is GraduateCapability => gc !== undefined);

      const suggestedCapabilities = suggestedCaps
        .filter(code => !currentCaps.includes(code))
        .map(code => getCapabilityByCode(code))
        .filter((gc): gc is GraduateCapability => gc !== undefined);

      return {
        id: `ulo-${ulo.id}`,
        type: 'ulo' as const,
        label: ulo.code,
        sublabel: ulo.description,
        children: weekNodes,
        metadata: {
          bloomLevel: ulo.bloomLevel,
          materialCount: ulo.materialCount,
          assessmentCount: ulo.assessmentCount,
        },
        savedCapabilities,
        suggestedCapabilities,
        uloId: ulo.id,
      };
    });
  };

  // Toggle a capability for a ULO
  const toggleCapability = (uloId: string, code: GraduateCapabilityCode) => {
    setCapabilityStates(prev => {
      const newStates = new Map(prev);
      const state = newStates.get(uloId);
      if (state) {
        const current = [...state.current];
        const index = current.indexOf(code);
        if (index >= 0) {
          current.splice(index, 1);
        } else {
          current.push(code);
        }
        newStates.set(uloId, { ...state, current });

        // Update tree data to reflect changes
        setTreeData(prevTree =>
          prevTree.map(node => {
            if (node.uloId === uloId) {
              const savedCapabilities = current
                .map(c => getCapabilityByCode(c))
                .filter((gc): gc is GraduateCapability => gc !== undefined);
              const suggestedCapabilities = state.suggested
                .filter(c => !current.includes(c))
                .map(c => getCapabilityByCode(c))
                .filter((gc): gc is GraduateCapability => gc !== undefined);
              return { ...node, savedCapabilities, suggestedCapabilities };
            }
            return node;
          })
        );
      }
      return newStates;
    });
  };

  // Apply AI suggestions for a ULO
  const applySuggestions = (uloId: string) => {
    setCapabilityStates(prev => {
      const newStates = new Map(prev);
      const state = newStates.get(uloId);
      if (state) {
        // Add suggested capabilities to current (avoid duplicates)
        const current = [...state.current];
        state.suggested.forEach(code => {
          if (!current.includes(code)) {
            current.push(code);
          }
        });
        newStates.set(uloId, { ...state, current });

        // Update tree data
        setTreeData(prevTree =>
          prevTree.map(node => {
            if (node.uloId === uloId) {
              const savedCapabilities = current
                .map(c => getCapabilityByCode(c))
                .filter((gc): gc is GraduateCapability => gc !== undefined);
              return { ...node, savedCapabilities, suggestedCapabilities: [] };
            }
            return node;
          })
        );
      }
      return newStates;
    });
    setEditingUloId(null);
  };

  // Save all changes
  const handleSaveAll = async () => {
    setSaving(true);
    try {
      const promises: Promise<unknown>[] = [];

      for (const [uloId, state] of capabilityStates.entries()) {
        // Only save if there are changes
        if (
          state.saved.length !== state.current.length ||
          !state.saved.every(s => state.current.includes(s))
        ) {
          promises.push(
            accreditationApi.updateULOGraduateCapabilities(uloId, {
              capabilityCodes: state.current,
              isAiSuggested: false,
            })
          );
        }
      }

      await Promise.all(promises);

      // Update saved state
      setCapabilityStates(prev => {
        const newStates = new Map(prev);
        for (const [uloId, state] of newStates.entries()) {
          newStates.set(uloId, { ...state, saved: [...state.current] });
        }
        return newStates;
      });

      toast.success('Graduate Capability mappings saved');
    } catch (err) {
      console.error('Error saving GC mappings:', err);
      toast.error('Failed to save mappings');
    } finally {
      setSaving(false);
    }
  };

  const toggleNode = (nodeId: string) => {
    setExpandedNodes(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  const renderNode = (node: TreeNode, depth: number = 0): React.ReactNode => {
    const isExpanded = expandedNodes.has(node.id);
    const hasChildren = node.children.length > 0;
    const paddingLeft = depth * 20 + 12;

    const getIcon = () => {
      switch (node.type) {
        case 'ulo':
          return <Target className='w-4 h-4 text-purple-600' />;
        case 'week':
          return <BookOpen className='w-4 h-4 text-blue-600' />;
        case 'material':
          return <FileText className='w-4 h-4 text-green-600' />;
        case 'llo':
          return <div className='w-2 h-2 rounded-full bg-gray-400 ml-1 mr-1' />;
        default:
          return null;
      }
    };

    return (
      <div key={node.id}>
        <div
          className={`flex items-start gap-2 py-2 px-3 hover:bg-gray-50 cursor-pointer transition ${
            node.type === 'ulo' ? 'bg-purple-50' : ''
          }`}
          style={{ paddingLeft }}
          onClick={() => hasChildren && toggleNode(node.id)}
        >
          {hasChildren ? (
            <button className='mt-0.5 text-gray-400 hover:text-gray-600'>
              {isExpanded ? (
                <ChevronDown className='w-4 h-4' />
              ) : (
                <ChevronRight className='w-4 h-4' />
              )}
            </button>
          ) : (
            <div className='w-4' />
          )}

          {getIcon()}

          <div className='flex-1 min-w-0'>
            <div className='flex items-center gap-2'>
              <span
                className={`font-medium ${node.type === 'ulo' ? 'text-purple-900' : 'text-gray-900'}`}
              >
                {node.label}
              </span>

              {/* Bloom level badge for ULOs */}
              {node.type === 'ulo' &&
              node.metadata?.bloomLevel &&
              typeof node.metadata.bloomLevel === 'string' ? (
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    BLOOM_COLORS[
                      (node.metadata.bloomLevel as string).toLowerCase()
                    ] || 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {String(node.metadata.bloomLevel) === 'analyze'
                    ? 'Analyse'
                    : String(node.metadata.bloomLevel)}
                </span>
              ) : null}

              {/* Graduate Capability badges for ULOs */}
              {node.type === 'ulo' && node.uloId && (
                <div className='flex items-center gap-1 ml-1'>
                  {/* Saved/current capabilities */}
                  {node.savedCapabilities &&
                    node.savedCapabilities.length > 0 &&
                    node.savedCapabilities.map(gc => (
                      <span
                        key={gc.id}
                        className={`px-2 py-0.5 rounded-full text-xs font-medium border cursor-pointer ${gc.color} ${
                          editingUloId === node.uloId
                            ? 'ring-2 ring-offset-1 ring-purple-400'
                            : ''
                        }`}
                        onClick={e => {
                          e.stopPropagation();
                          if (editingUloId === node.uloId) {
                            toggleCapability(
                              node.uloId!,
                              gc.code as GraduateCapabilityCode
                            );
                          }
                        }}
                        onMouseEnter={e => {
                          const rect = e.currentTarget.getBoundingClientRect();
                          setTooltipPosition({
                            x: rect.left + rect.width / 2,
                            y: rect.bottom + 8,
                          });
                          setHoveredCapability(gc);
                        }}
                        onMouseLeave={() => setHoveredCapability(null)}
                      >
                        {gc.icon} {gc.code}
                      </span>
                    ))}

                  {/* AI suggested capabilities (not yet saved) */}
                  {node.suggestedCapabilities &&
                    node.suggestedCapabilities.length > 0 && (
                      <>
                        <Sparkles className='w-3 h-3 text-amber-500 ml-1' />
                        {node.suggestedCapabilities.map(gc => (
                          <span
                            key={gc.id}
                            className={`px-2 py-0.5 rounded-full text-xs font-medium border cursor-pointer opacity-60 hover:opacity-100 ${gc.color}`}
                            onClick={e => {
                              e.stopPropagation();
                              toggleCapability(
                                node.uloId!,
                                gc.code as GraduateCapabilityCode
                              );
                            }}
                            onMouseEnter={e => {
                              const rect =
                                e.currentTarget.getBoundingClientRect();
                              setTooltipPosition({
                                x: rect.left + rect.width / 2,
                                y: rect.bottom + 8,
                              });
                              setHoveredCapability(gc);
                            }}
                            onMouseLeave={() => setHoveredCapability(null)}
                          >
                            {gc.icon} {gc.code}
                          </span>
                        ))}
                      </>
                    )}

                  {/* Edit button */}
                  {editingUloId !== node.uloId ? (
                    <button
                      className='ml-1 p-1 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded'
                      onClick={e => {
                        e.stopPropagation();
                        setEditingUloId(node.uloId!);
                      }}
                      title='Edit Graduate Capabilities'
                    >
                      <Edit3 className='w-3 h-3' />
                    </button>
                  ) : (
                    <button
                      className='ml-1 p-1 text-green-600 hover:bg-green-50 rounded'
                      onClick={e => {
                        e.stopPropagation();
                        setEditingUloId(null);
                      }}
                      title='Done editing'
                    >
                      <Check className='w-3 h-3' />
                    </button>
                  )}
                </div>
              )}

              {/* Material type badge */}
              {node.type === 'material' && node.sublabel ? (
                <span className='px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600'>
                  {node.sublabel}
                </span>
              ) : null}
            </div>

            {/* Sublabel (description) */}
            {node.sublabel && node.type === 'ulo' && (
              <p className='text-sm text-gray-600 mt-0.5 line-clamp-2'>
                {node.sublabel}
              </p>
            )}

            {/* Stats for ULOs */}
            {node.type === 'ulo' && node.metadata && (
              <div className='flex items-center gap-3 mt-1 text-xs text-gray-500'>
                <span>{node.metadata.materialCount as number} materials</span>
                <span>
                  {node.metadata.assessmentCount as number} assessments
                </span>
              </div>
            )}

            {/* Inline edit panel for capabilities */}
            {node.type === 'ulo' &&
              node.uloId &&
              editingUloId === node.uloId && (
                <div className='mt-2 p-2 bg-purple-50 rounded-lg border border-purple-200'>
                  <p className='text-xs text-purple-700 mb-2'>
                    Click to toggle Graduate Capabilities:
                  </p>
                  <div className='flex flex-wrap gap-1'>
                    {GRADUATE_CAPABILITIES.map(gc => {
                      const state = capabilityStates.get(node.uloId!);
                      const isSelected = state?.current.includes(
                        gc.code as GraduateCapabilityCode
                      );
                      const isSuggested = state?.suggested.includes(
                        gc.code as GraduateCapabilityCode
                      );

                      return (
                        <button
                          key={gc.id}
                          onClick={e => {
                            e.stopPropagation();
                            toggleCapability(
                              node.uloId!,
                              gc.code as GraduateCapabilityCode
                            );
                          }}
                          className={`px-2 py-1 rounded text-xs font-medium border transition ${
                            isSelected
                              ? gc.color
                              : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
                          } ${isSuggested && !isSelected ? 'ring-1 ring-amber-300' : ''}`}
                          title={gc.name}
                        >
                          {gc.icon} {gc.code}
                          {isSuggested && !isSelected && (
                            <Sparkles className='w-2 h-2 inline ml-0.5 text-amber-500' />
                          )}
                        </button>
                      );
                    })}
                  </div>
                  {capabilityStates
                    .get(node.uloId!)
                    ?.suggested.some(
                      s =>
                        !capabilityStates.get(node.uloId!)?.current.includes(s)
                    ) && (
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        applySuggestions(node.uloId!);
                      }}
                      className='mt-2 text-xs text-amber-700 hover:text-amber-800 flex items-center gap-1'
                    >
                      <Sparkles className='w-3 h-3' />
                      Apply all AI suggestions
                    </button>
                  )}
                </div>
              )}
          </div>
        </div>

        {/* Children */}
        {isExpanded && hasChildren && (
          <div>{node.children.map(child => renderNode(child, depth + 1))}</div>
        )}
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className='fixed inset-0 z-50 overflow-y-auto'>
      {/* Backdrop */}
      <div
        className='fixed inset-0 bg-black bg-opacity-50 transition-opacity'
        onClick={onClose}
      />

      {/* Modal */}
      <div className='flex min-h-full items-center justify-center p-4'>
        <div className='relative bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col'>
          {/* Header */}
          <div className='flex items-center justify-between px-6 py-4 border-b border-gray-200'>
            <div>
              <h2 className='text-xl font-semibold text-gray-900'>
                Learning Outcome Hierarchy
              </h2>
              <p className='text-sm text-gray-500 mt-1'>
                ULOs &rarr; Weekly Content &rarr; Materials &rarr; Local
                Outcomes
              </p>
            </div>
            <button
              onClick={onClose}
              className='p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition'
            >
              <X className='w-5 h-5' />
            </button>
          </div>

          {/* Content */}
          <div className='flex-1 overflow-y-auto'>
            {loading ? (
              <div className='flex items-center justify-center py-12'>
                <Loader2 className='w-8 h-8 text-purple-600 animate-spin' />
                <span className='ml-3 text-gray-600'>Loading hierarchy...</span>
              </div>
            ) : error ? (
              <div className='flex flex-col items-center justify-center py-12 text-center'>
                <AlertCircle className='w-12 h-12 text-red-400 mb-3' />
                <p className='text-gray-900 font-medium'>{error}</p>
                <button
                  onClick={loadData}
                  className='mt-4 px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition'
                >
                  Try Again
                </button>
              </div>
            ) : treeData.length === 0 ? (
              <div className='flex flex-col items-center justify-center py-12 text-center'>
                <Target className='w-12 h-12 text-gray-300 mb-3' />
                <p className='text-gray-900 font-medium'>
                  No Learning Outcomes Defined
                </p>
                <p className='text-sm text-gray-500 mt-1'>
                  Add Unit Learning Outcomes (ULOs) to see the hierarchy map.
                </p>
              </div>
            ) : (
              <div className='py-2'>
                {treeData.map(node => renderNode(node))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className='px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-xl'>
            <div className='flex flex-col gap-3'>
              {/* Tree legend */}
              <div className='flex items-center gap-4 text-xs text-gray-500'>
                <span className='flex items-center gap-1'>
                  <Target className='w-3 h-3 text-purple-600' />
                  Unit Learning Outcome
                </span>
                <span className='flex items-center gap-1'>
                  <BookOpen className='w-3 h-3 text-blue-600' />
                  {topicLabel}
                </span>
                <span className='flex items-center gap-1'>
                  <FileText className='w-3 h-3 text-green-600' />
                  Material
                </span>
                <span className='flex items-center gap-1'>
                  <div className='w-2 h-2 rounded-full bg-gray-400' />
                  Local Outcome
                </span>
              </div>

              {/* Graduate Capabilities legend */}
              <div className='flex items-center justify-between'>
                <div className='flex items-center gap-2 text-xs text-gray-500'>
                  <span className='font-medium text-gray-600'>
                    Graduate Capabilities:
                  </span>
                  <span className='flex items-center gap-1'>
                    <span className='px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-300'>
                      GC1-6
                    </span>
                    Saved
                  </span>
                  <span className='flex items-center gap-1'>
                    <Sparkles className='w-3 h-3 text-amber-500' />
                    <span className='px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 border border-gray-300 opacity-60'>
                      GC
                    </span>
                    AI Suggested
                  </span>
                  <span className='flex items-center gap-1'>
                    <Edit3 className='w-3 h-3 text-gray-400' />
                    Click to edit
                  </span>
                </div>
                <div className='flex items-center gap-2'>
                  {hasUnsavedChanges && (
                    <button
                      onClick={handleSaveAll}
                      disabled={saving}
                      className='flex items-center gap-1.5 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50'
                    >
                      {saving ? (
                        <Loader2 className='w-4 h-4 animate-spin' />
                      ) : (
                        <Save className='w-4 h-4' />
                      )}
                      Save Changes
                    </button>
                  )}
                  <button
                    onClick={onClose}
                    className='px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition'
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Capability Tooltip */}
      {hoveredCapability && (
        <div
          className='fixed z-[60] bg-white rounded-lg shadow-xl border border-gray-200 p-4 max-w-sm'
          style={{
            left: tooltipPosition.x,
            top: tooltipPosition.y,
            transform: 'translateX(-50%)',
          }}
        >
          <div className='flex items-center gap-2 mb-2'>
            <span className='text-2xl'>{hoveredCapability.icon}</span>
            <div>
              <span
                className={`px-2 py-0.5 rounded text-xs font-bold ${hoveredCapability.color}`}
              >
                {hoveredCapability.code}
              </span>
              <h4 className='font-semibold text-gray-900 mt-1'>
                {hoveredCapability.name}
              </h4>
            </div>
          </div>
          <p className='text-sm text-gray-600 leading-relaxed'>
            {hoveredCapability.description}
          </p>
          <div className='mt-2 pt-2 border-t border-gray-100'>
            <p className='text-xs text-amber-600 flex items-center gap-1'>
              <Sparkles className='w-3 h-3' />
              AI-suggested based on outcome keywords
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default LearningOutcomeMap;
