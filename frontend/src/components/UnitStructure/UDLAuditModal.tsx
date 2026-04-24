import { useState, useEffect, useCallback } from 'react';
import {
  X,
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

interface UDLAuditModalProps {
  unitId: string;
  assessmentId: string;
  assessmentTitle: string;
  assessmentCategory: string;
  onClose: () => void;
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

export const UDLAuditModal: React.FC<UDLAuditModalProps> = ({
  unitId,
  assessmentId,
  assessmentTitle,
  assessmentCategory,
  onClose,
}) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [suggesting, setSuggesting] = useState(false);

  const [profiles, setProfiles] = useState<UDLProfile[]>([]);
  const [guidelines, setGuidelines] = useState<UDLGuidelinesData | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState<string>('');
  const [responses, setResponses] = useState<
    Map<string, UDLAuditResponseValue>
  >(new Map());
  const [expandedCheckpoints, setExpandedCheckpoints] = useState<Set<string>>(
    new Set()
  );
  const [aiSuggestions, setAiSuggestions] = useState<UDLAuditAISuggestion[]>(
    []
  );

  const selectedProfile =
    profiles.find(p => p.id === selectedProfileId) ?? null;

  // Filter checkpoints to those tagged for this assessment category
  const relevantCheckpoints: UDLProfileCheckpoint[] = selectedProfile
    ? selectedProfile.checkpoints.filter(
        cp =>
          cp.assessmentTypes.length === 0 ||
          cp.assessmentTypes.includes(assessmentCategory)
      )
    : [];

  // Fall back to all checkpoints if none match the category
  const checkpointsToShow: UDLProfileCheckpoint[] =
    relevantCheckpoints.length > 0
      ? relevantCheckpoints
      : (selectedProfile?.checkpoints ?? []);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [ps, gl] = await Promise.all([
        udlAuditApi.listProfiles(),
        udlAuditApi.listGuidelines(),
      ]);
      setProfiles(ps);
      setGuidelines(gl);
      const firstId = ps[0]?.id ?? '';
      setSelectedProfileId(firstId);
      if (firstId) {
        const saved = await udlAuditApi.getResponses(
          unitId,
          firstId,
          assessmentId
        );
        const map = new Map<string, UDLAuditResponseValue>();
        for (const r of saved) map.set(r.checkpointId, r.response);
        setResponses(map);
      }
    } catch {
      toast.error('Failed to load audit data');
    } finally {
      setLoading(false);
    }
  }, [unitId, assessmentId]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const setResponse = (checkpointId: string, value: UDLAuditResponseValue) => {
    setResponses(prev => new Map(prev).set(checkpointId, value));
  };

  const saveAll = async () => {
    if (!selectedProfile) return;
    setSaving(true);
    try {
      await udlAuditApi.upsertResponses(unitId, {
        profileId: selectedProfileId,
        assessmentId,
        responses: checkpointsToShow.map(cp => ({
          checkpointId: cp.checkpointId,
          response: responses.get(cp.checkpointId) ?? 'skipped',
        })),
      });
      toast.success('Audit saved');
      onClose();
    } catch {
      toast.error('Failed to save audit');
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
        assessmentId
      );
      setAiSuggestions(result.suggestions);
      if (result.suggestions.length === 0) {
        toast('No needs-work checkpoints — nothing to suggest!');
      } else {
        toast.success(
          `${result.suggestions.length} suggestion${result.suggestions.length !== 1 ? 's' : ''} generated`
        );
      }
    } catch {
      toast.error('Failed to get AI suggestions');
    } finally {
      setSuggesting(false);
    }
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

  const needsWorkCount = checkpointsToShow.filter(
    cp => responses.get(cp.checkpointId) === 'needs_work'
  ).length;

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40'>
      <div className='bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col mx-4'>
        {/* Header */}
        <div className='flex items-center justify-between px-5 py-4 border-b border-gray-100'>
          <div className='flex items-center gap-3'>
            <ClipboardCheck className='h-5 w-5 text-teal-600' />
            <div>
              <h2 className='font-semibold text-gray-900 text-base'>
                UDL Audit
              </h2>
              <p className='text-xs text-gray-500'>{assessmentTitle}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className='p-1.5 text-gray-400 hover:text-gray-600 rounded'
          >
            <X className='h-5 w-5' />
          </button>
        </div>

        {/* Profile selector */}
        {profiles.length > 1 && (
          <div className='px-5 py-3 border-b border-gray-100 flex items-center gap-3'>
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
        )}

        {/* Body */}
        <div className='flex-1 overflow-y-auto px-5 py-4 space-y-3'>
          {loading ? (
            <div className='flex items-center justify-center py-12'>
              <Loader2 className='w-6 h-6 text-teal-600 animate-spin' />
              <span className='ml-2 text-sm text-gray-500'>Loading...</span>
            </div>
          ) : checkpointsToShow.length === 0 ? (
            <p className='text-sm text-gray-400 py-8 text-center'>
              No checkpoints match this assessment type.
            </p>
          ) : (
            checkpointsToShow.map((cp: UDLProfileCheckpoint) => {
              const currentResponse =
                responses.get(cp.checkpointId) ?? 'skipped';
              const principleId = getPrincipleForCheckpoint(cp.checkpointId);
              const guidelineName = getGuidelineForCheckpoint(cp.checkpointId);
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
                  <div className='px-3 py-2.5'>
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
                      >
                        <ChevronRight
                          className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-90' : ''}`}
                        />
                      </button>
                    </div>

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
            })
          )}
        </div>

        {/* Footer */}
        <div className='px-5 py-3 border-t border-gray-100 flex items-center justify-between'>
          <div className='flex items-center gap-3 text-xs text-gray-500'>
            {needsWorkCount > 0 && (
              <button
                onClick={handleAISuggest}
                disabled={suggesting}
                className='flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50'
              >
                {suggesting ? (
                  <Loader2 className='h-3.5 w-3.5 animate-spin' />
                ) : (
                  <Sparkles className='h-3.5 w-3.5' />
                )}
                AI Suggestions
              </button>
            )}
          </div>
          <div className='flex items-center gap-2'>
            <button
              onClick={onClose}
              className='px-4 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50'
            >
              Cancel
            </button>
            <button
              onClick={saveAll}
              disabled={saving}
              className='flex items-center gap-1.5 px-4 py-1.5 text-sm bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50'
            >
              {saving ? <Loader2 className='h-3.5 w-3.5 animate-spin' /> : null}
              Save & Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UDLAuditModal;
