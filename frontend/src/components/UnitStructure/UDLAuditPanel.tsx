import { useState, useEffect, useCallback } from 'react';
import {
  ChevronDown,
  ChevronUp,
  ClipboardCheck,
  Loader2,
  Sparkles,
  ChevronRight,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { udlAuditApi } from '../../services/udlAuditApi';
import type {
  UDLAuditAISuggestion,
  UDLAuditResponseValue,
  UDLGuidelinesData,
  UDLProfile,
  UDLProfileCheckpoint,
} from '../../types/unitStructure';

interface UDLAuditPanelProps {
  unitId: string;
}

const RESPONSE_OPTIONS: {
  value: UDLAuditResponseValue;
  label: string;
  color: string;
}[] = [
  {
    value: 'doing_well',
    label: 'Doing well',
    color: 'bg-green-100 text-green-800 border-green-300',
  },
  {
    value: 'needs_work',
    label: 'Needs work',
    color: 'bg-amber-100 text-amber-800 border-amber-300',
  },
  {
    value: 'not_applicable',
    label: 'N/A',
    color: 'bg-gray-100 text-gray-600 border-gray-300',
  },
];

const PRINCIPLE_COLORS: Record<string, string> = {
  representation: 'bg-blue-100 text-blue-700',
  action_expression: 'bg-purple-100 text-purple-700',
  engagement: 'bg-green-100 text-green-700',
};

export const UDLAuditPanel: React.FC<UDLAuditPanelProps> = ({ unitId }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [suggesting, setSuggesting] = useState(false);

  const [profiles, setProfiles] = useState<UDLProfile[]>([]);
  const [guidelines, setGuidelines] = useState<UDLGuidelinesData | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState<string>('');
  // checkpointId → response
  const [responses, setResponses] = useState<
    Map<string, UDLAuditResponseValue>
  >(new Map());
  // checkpointId → notes
  const [notes, setNotes] = useState<Map<string, string>>(new Map());
  const [expandedCheckpoints, setExpandedCheckpoints] = useState<Set<string>>(
    new Set()
  );
  const [aiSuggestions, setAiSuggestions] = useState<UDLAuditAISuggestion[]>(
    []
  );

  const selectedProfile =
    profiles.find(p => p.id === selectedProfileId) ?? null;

  const loadStaticData = useCallback(async () => {
    try {
      const [ps, gl] = await Promise.all([
        udlAuditApi.listProfiles(),
        udlAuditApi.listGuidelines(),
      ]);
      setProfiles(ps);
      setGuidelines(gl);
      if (ps.length > 0 && !selectedProfileId) {
        setSelectedProfileId(ps[0].id);
      }
    } catch {
      toast.error('Failed to load UDL profiles');
    }
  }, [selectedProfileId]);

  const loadResponses = useCallback(
    async (profileId: string) => {
      if (!profileId) return;
      setLoading(true);
      try {
        const saved = await udlAuditApi.getResponses(unitId, profileId, '');
        const map = new Map<string, UDLAuditResponseValue>();
        const notesMap = new Map<string, string>();
        for (const r of saved) {
          map.set(r.checkpointId, r.response);
          if (r.notes) notesMap.set(r.checkpointId, r.notes);
        }
        setResponses(map);
        setNotes(notesMap);
      } catch {
        toast.error('Failed to load audit responses');
      } finally {
        setLoading(false);
      }
    },
    [unitId]
  );

  useEffect(() => {
    if (isExpanded) {
      loadStaticData();
    }
  }, [isExpanded, loadStaticData]);

  useEffect(() => {
    if (isExpanded && selectedProfileId) {
      loadResponses(selectedProfileId);
      setAiSuggestions([]);
    }
  }, [isExpanded, selectedProfileId, loadResponses]);

  const setResponse = (checkpointId: string, value: UDLAuditResponseValue) => {
    setResponses(prev => new Map(prev).set(checkpointId, value));
  };

  const saveAll = async () => {
    if (!selectedProfile) return;
    setSaving(true);
    try {
      await udlAuditApi.upsertResponses(unitId, {
        profileId: selectedProfileId,
        assessmentId: '',
        responses: selectedProfile.checkpoints.map(cp => ({
          checkpointId: cp.checkpointId,
          response: responses.get(cp.checkpointId) ?? 'skipped',
          ...(notes.get(cp.checkpointId)
            ? { notes: notes.get(cp.checkpointId) }
            : {}),
        })),
      });
      toast.success('Audit responses saved');
    } catch {
      toast.error('Failed to save responses');
    } finally {
      setSaving(false);
    }
  };

  const handleAISuggest = async () => {
    setSuggesting(true);
    try {
      const result = await udlAuditApi.getAISuggestions(
        unitId,
        selectedProfileId,
        ''
      );
      setAiSuggestions(result.suggestions);
      if (result.suggestions.length === 0) {
        toast('No needs-work checkpoints — nothing to suggest!');
      } else {
        toast.success(
          `${result.suggestions.length} AI suggestion${result.suggestions.length !== 1 ? 's' : ''} generated`
        );
      }
    } catch {
      toast.error('Failed to get AI suggestions');
    } finally {
      setSuggesting(false);
    }
  };

  const needsWorkCount = selectedProfile
    ? selectedProfile.checkpoints.filter(
        cp => responses.get(cp.checkpointId) === 'needs_work'
      ).length
    : 0;

  const doingWellCount = selectedProfile
    ? selectedProfile.checkpoints.filter(
        cp => responses.get(cp.checkpointId) === 'doing_well'
      ).length
    : 0;

  const reviewedCount = selectedProfile
    ? selectedProfile.checkpoints.filter(cp => {
        const r = responses.get(cp.checkpointId);
        return r && r !== 'skipped';
      }).length
    : 0;

  const totalCount = selectedProfile?.checkpoints.length ?? 0;

  const getPrincipleForCheckpoint = (cpId: string): string => {
    if (!guidelines) return '';
    for (const p of guidelines.principles) {
      for (const g of p.guidelines) {
        if (g.checkpoints.some(c => c.id === cpId)) return p.id;
      }
    }
    return '';
  };

  const getGuidelineForCheckpoint = (cpId: string): string => {
    if (!guidelines) return '';
    for (const p of guidelines.principles) {
      for (const g of p.guidelines) {
        if (g.checkpoints.some(c => c.id === cpId)) return g.name;
      }
    }
    return '';
  };

  const getCheckpointName = (cpId: string): string => {
    if (!guidelines) return cpId;
    for (const p of guidelines.principles) {
      for (const g of p.guidelines) {
        const cp = g.checkpoints.find(c => c.id === cpId);
        if (cp) return cp.name;
      }
    }
    return cpId;
  };

  return (
    <div className='bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden'>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className='w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition'
      >
        <div className='flex items-center gap-3'>
          <ClipboardCheck className='w-5 h-5 text-teal-600' />
          <div className='text-left'>
            <h3 className='font-semibold text-gray-900'>UDL Audit</h3>
            <p className='text-xs text-gray-500'>
              Reflect on UDL checkpoints and identify areas for improvement
            </p>
          </div>
        </div>
        <div className='flex items-center gap-3'>
          {totalCount > 0 && (
            <span className='px-2 py-1 bg-teal-100 text-teal-700 text-xs font-medium rounded-full'>
              {reviewedCount} of {totalCount} reviewed
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
          {/* Profile selector */}
          <div className='flex items-center gap-3'>
            <label className='text-sm font-medium text-gray-700 shrink-0'>
              Profile:
            </label>
            <select
              value={selectedProfileId}
              onChange={e => setSelectedProfileId(e.target.value)}
              className='flex-1 border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500'
            >
              {profiles.map(p => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {selectedProfile && (
            <p className='text-xs text-gray-500'>
              {selectedProfile.description}
            </p>
          )}

          {loading ? (
            <div className='flex items-center justify-center py-8'>
              <Loader2 className='w-5 h-5 text-teal-600 animate-spin' />
              <span className='ml-2 text-sm text-gray-500'>Loading...</span>
            </div>
          ) : selectedProfile ? (
            <>
              {/* Checkpoint list */}
              <div className='space-y-3'>
                {selectedProfile.checkpoints.map((cp: UDLProfileCheckpoint) => {
                  const currentResponse =
                    responses.get(cp.checkpointId) ?? 'skipped';
                  const principleId = getPrincipleForCheckpoint(
                    cp.checkpointId
                  );
                  const guidelineName = getGuidelineForCheckpoint(
                    cp.checkpointId
                  );
                  const cpName = getCheckpointName(cp.checkpointId);
                  const isOpen = expandedCheckpoints.has(cp.checkpointId);
                  const aiSuggestion = aiSuggestions.find(
                    s => s.checkpointId === cp.checkpointId
                  );

                  return (
                    <div
                      key={cp.checkpointId}
                      className='border border-gray-100 rounded-lg overflow-hidden'
                    >
                      <div className='px-3 py-2.5 bg-white'>
                        <div className='flex items-start gap-3'>
                          <span className='font-mono text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded shrink-0 mt-0.5'>
                            {cp.checkpointId}
                          </span>
                          <div className='flex-1 min-w-0'>
                            <div className='flex items-center gap-2 mb-1 flex-wrap'>
                              {principleId && (
                                <span
                                  className={`text-xs px-1.5 py-0.5 rounded ${PRINCIPLE_COLORS[principleId] ?? 'bg-gray-100 text-gray-600'}`}
                                >
                                  {principleId === 'action_expression'
                                    ? 'Action & Expression'
                                    : principleId.charAt(0).toUpperCase() +
                                      principleId.slice(1)}
                                </span>
                              )}
                              {guidelineName && (
                                <span className='text-xs text-gray-400'>
                                  {guidelineName}
                                </span>
                              )}
                            </div>
                            <p className='text-sm text-gray-800 font-medium'>
                              {cpName}
                            </p>
                            {cp.contextNote && (
                              <p className='text-xs text-gray-500 mt-0.5'>
                                {cp.contextNote}
                              </p>
                            )}
                          </div>
                          <button
                            onClick={() =>
                              setExpandedCheckpoints(prev => {
                                const next = new Set(prev);
                                if (next.has(cp.checkpointId))
                                  next.delete(cp.checkpointId);
                                else next.add(cp.checkpointId);
                                return next;
                              })
                            }
                            className='text-gray-400 hover:text-gray-600 shrink-0'
                            title={isOpen ? 'Hide examples' : 'Show examples'}
                          >
                            <ChevronRight
                              className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-90' : ''}`}
                            />
                          </button>
                        </div>

                        {/* Harmful / helpful examples (expandable) */}
                        {isOpen && (
                          <div className='mt-2 ml-9 space-y-2'>
                            <div className='text-xs bg-red-50 border border-red-100 rounded p-2'>
                              <span className='font-semibold text-red-700'>
                                Harmful practice:{' '}
                              </span>
                              <span className='text-red-800'>
                                {cp.harmfulPractice}
                              </span>
                            </div>
                            <div className='text-xs bg-green-50 border border-green-100 rounded p-2'>
                              <span className='font-semibold text-green-700'>
                                Helpful practice:{' '}
                              </span>
                              <span className='text-green-800'>
                                {cp.helpfulPractice}
                              </span>
                            </div>
                          </div>
                        )}

                        {/* Response buttons */}
                        <div className='mt-2 ml-9 flex items-center gap-2 flex-wrap'>
                          {RESPONSE_OPTIONS.map(opt => (
                            <button
                              key={opt.value}
                              onClick={() =>
                                setResponse(cp.checkpointId, opt.value)
                              }
                              className={`px-2.5 py-1 text-xs rounded border transition ${
                                currentResponse === opt.value
                                  ? opt.color + ' font-semibold'
                                  : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
                              }`}
                            >
                              {opt.label}
                            </button>
                          ))}
                        </div>

                        {/* AI suggestion */}
                        {aiSuggestion && (
                          <div className='mt-2 ml-9 text-xs bg-purple-50 border border-purple-200 rounded p-2 flex gap-2'>
                            <Sparkles className='h-3.5 w-3.5 text-purple-500 shrink-0 mt-0.5' />
                            <span className='text-purple-800'>
                              {aiSuggestion.suggestion}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Summary + action bar */}
              <div className='flex items-center justify-between pt-2 border-t border-gray-100'>
                <div className='flex items-center gap-4 text-xs text-gray-500'>
                  <span className='text-green-600 font-medium'>
                    {doingWellCount} doing well
                  </span>
                  <span className='text-amber-600 font-medium'>
                    {needsWorkCount} needs work
                  </span>
                </div>
                <div className='flex items-center gap-2'>
                  {needsWorkCount > 0 && (
                    <button
                      onClick={handleAISuggest}
                      disabled={suggesting}
                      className='flex items-center gap-1.5 text-xs px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50'
                    >
                      {suggesting ? (
                        <Loader2 className='h-3.5 w-3.5 animate-spin' />
                      ) : (
                        <Sparkles className='h-3.5 w-3.5' />
                      )}
                      AI Suggestions
                    </button>
                  )}
                  <button
                    onClick={saveAll}
                    disabled={saving}
                    className='flex items-center gap-1.5 text-xs px-3 py-1.5 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50'
                  >
                    {saving ? (
                      <Loader2 className='h-3.5 w-3.5 animate-spin' />
                    ) : (
                      <ClipboardCheck className='h-3.5 w-3.5' />
                    )}
                    Save
                  </button>
                </div>
              </div>
            </>
          ) : (
            <p className='text-sm text-gray-400 py-4 text-center'>
              No profiles available.
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default UDLAuditPanel;
