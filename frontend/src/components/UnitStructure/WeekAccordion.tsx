import { useCallback, useState, useEffect } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Clock,
  Presentation,
  Users,
  FlaskConical,
  BookOpen,
  FileText,
  MessageSquare,
  Map as MapIcon,
  Wrench,
  Building,
  Monitor,
  ClipboardCheck,
  Trash2,
  Copy,
  X,
  Sparkles,
  type LucideIcon,
} from 'lucide-react';
import { materialsApi, analyticsApi } from '../../services/unitStructureApi';
import { useConfirmDialog } from '../../components/ui';
import { MaterialResponse, WeekQualityScore } from '../../types/unitStructure';
import { getFormatMeta } from '../../constants/sessionFormats';
import StarRating from '../shared/StarRating';
import { WeeklyMaterialsManager } from './WeeklyMaterialsManager';
import toast from 'react-hot-toast';

interface WeekAccordionProps {
  unitId: string;
  durationWeeks: number;
  topicLabel?: string | undefined;
  expandedWeek: number | null;
  onWeekToggle: (weekNumber: number) => void;
  onAddWeek?: (() => void) | undefined;
  onDeleteWeek?: ((weekNumber: number) => void) | undefined;
  onApplyStructure?: ((mode: 'stubs' | 'categories') => void) | undefined;
  onOpenAI?: ((weekNumber: number) => void) | undefined;
}

interface WeekData {
  weekNumber: number;
  materials: MaterialResponse[];
  totalDuration: number;
  isLoading: boolean;
  isLoaded: boolean;
}

const ICON_MAP: Record<string, LucideIcon> = {
  Presentation,
  Users,
  FlaskConical,
  BookOpen,
  FileText,
  MessageSquare,
  Map: MapIcon,
  Wrench,
  Building,
  Monitor,
  ClipboardCheck,
};

function FormatIcon({
  iconName,
  className,
}: {
  iconName: string;
  className?: string | undefined;
}) {
  const Icon = ICON_MAP[iconName] ?? FileText;
  return <Icon className={className} />;
}

export const WeekAccordion: React.FC<WeekAccordionProps> = ({
  unitId,
  durationWeeks,
  topicLabel = 'Week',
  expandedWeek,
  onWeekToggle,
  onAddWeek,
  onDeleteWeek,
  onApplyStructure,
  onOpenAI,
}) => {
  const confirm = useConfirmDialog();
  const [weeksData, setWeeksData] = useState<Map<number, WeekData>>(new Map());
  const [allMaterialsLoaded, setAllMaterialsLoaded] = useState(false);
  const [showApplyPopover, setShowApplyPopover] = useState(false);
  const week1HasMaterials = (weeksData.get(1)?.materials.length ?? 0) > 0;
  const [weeklyQuality, setWeeklyQuality] = useState<
    Map<number, WeekQualityScore>
  >(new Map());

  // Load weekly quality scores
  useEffect(() => {
    const loadQuality = async () => {
      try {
        const data = await analyticsApi.getWeeklyQuality(unitId, durationWeeks);
        const map = new Map<number, WeekQualityScore>();
        for (const w of data) {
          map.set(w.weekNumber, w);
        }
        setWeeklyQuality(map);
      } catch {
        // Non-critical
      }
    };
    loadQuality();
  }, [unitId, durationWeeks]);

  // Load all materials for the unit to show per-week counts in the collapsed
  // header. Exposed as a callback so the manager can trigger a refresh after
  // mutations, keeping the summary badges in sync with inline edits.
  const loadAllMaterials = useCallback(async () => {
    try {
      const materials = await materialsApi.getMaterialsByUnit(unitId);

      const weekMap = new Map<number, WeekData>();
      for (let i = 1; i <= durationWeeks; i++) {
        const weekMaterials = materials.filter(m => m.weekNumber === i);
        const totalDuration = weekMaterials.reduce(
          (sum, m) => sum + (m.durationMinutes || 0),
          0
        );
        weekMap.set(i, {
          weekNumber: i,
          materials: weekMaterials,
          totalDuration,
          isLoading: false,
          isLoaded: true,
        });
      }
      setWeeksData(weekMap);
      setAllMaterialsLoaded(true);
    } catch (error) {
      console.error('Error loading materials:', error);
      toast.error('Failed to load materials');
    }
  }, [unitId, durationWeeks]);

  useEffect(() => {
    loadAllMaterials();
  }, [loadAllMaterials]);

  const formatDuration = (minutes: number): string => {
    if (minutes === 0) return '';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours === 0) return `${mins}min`;
    if (mins === 0) return `${hours}h`;
    return `${hours}h ${mins}m`;
  };

  const getWeekSummary = (weekData: WeekData | undefined) => {
    if (!weekData || weekData.materials.length === 0) {
      return { count: 0, types: [], duration: 0 };
    }

    const typeCounts = new Map<string, number>();
    weekData.materials.forEach(m => {
      typeCounts.set(m.type, (typeCounts.get(m.type) || 0) + 1);
    });

    return {
      count: weekData.materials.length,
      types: Array.from(typeCounts.entries()),
      duration: weekData.totalDuration,
    };
  };

  const handleDeleteWeekClick = async (
    e: React.MouseEvent,
    weekNumber: number,
    hasContent: boolean
  ) => {
    e.stopPropagation();
    if (!onDeleteWeek) return;

    if (hasContent) {
      const ok = await confirm({
        title: `Delete ${topicLabel} ${weekNumber}?`,
        message: `${topicLabel} ${weekNumber} has materials that will be permanently deleted. Continue?`,
        confirmLabel: 'Delete',
        variant: 'danger',
      });
      if (!ok) return;
    }

    onDeleteWeek(weekNumber);
  };

  if (!allMaterialsLoaded) {
    return (
      <div className='space-y-2'>
        {Array.from({ length: durationWeeks }, (_, i) => (
          <div
            key={i}
            className='bg-white border border-gray-200 rounded-lg p-4 animate-pulse'
          >
            <div className='h-5 bg-gray-200 rounded w-1/4'></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className='space-y-2'>
      {Array.from({ length: durationWeeks }, (_, i) => i + 1).map(
        weekNumber => {
          const weekData = weeksData.get(weekNumber);
          const summary = getWeekSummary(weekData);
          const isExpanded = expandedWeek === weekNumber;
          const isEmpty = summary.count === 0;

          return (
            <div
              key={weekNumber}
              className={`bg-white border rounded-lg overflow-hidden transition-all ${
                isEmpty
                  ? 'border-gray-200 bg-gray-50'
                  : 'border-gray-200 hover:border-purple-300'
              }`}
            >
              {/* Week Header */}
              <div
                className={`flex items-center justify-between p-4 transition ${
                  isExpanded ? 'bg-purple-50' : 'hover:bg-gray-50'
                }`}
              >
                <button
                  onClick={() => onWeekToggle(weekNumber)}
                  className='flex items-center gap-3 flex-1 text-left'
                >
                  {isExpanded ? (
                    <ChevronDown className='w-5 h-5 text-gray-500' />
                  ) : (
                    <ChevronRight className='w-5 h-5 text-gray-400' />
                  )}
                  <span
                    className={`font-medium ${isEmpty ? 'text-gray-400' : 'text-gray-900'}`}
                  >
                    {topicLabel || 'Week'} {weekNumber}
                  </span>

                  {/* Material type badges (collapsed view) */}
                  {!isExpanded && summary.types.length > 0 && (
                    <div className='flex items-center gap-1 ml-2'>
                      {summary.types.slice(0, 4).map(([type, count]) => {
                        const meta = getFormatMeta(type);
                        return (
                          <span
                            key={type}
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${meta.color}`}
                            title={`${count} ${meta.label}${count > 1 ? 's' : ''}`}
                          >
                            <FormatIcon
                              iconName={meta.icon}
                              className='w-3.5 h-3.5'
                            />
                            {count > 1 && <span>{count}</span>}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </button>

                <div className='flex items-center gap-4'>
                  {/* Week quality star */}
                  {weeklyQuality.get(weekNumber)?.hasContent && (
                    <StarRating
                      rating={weeklyQuality.get(weekNumber)?.starRating ?? 0}
                      size='sm'
                      tooltipContent={`${weeklyQuality.get(weekNumber)?.materialCount ?? 0} materials, ${formatDuration(weeklyQuality.get(weekNumber)?.totalDurationMinutes ?? 0)}`}
                    />
                  )}

                  {/* Duration */}
                  {summary.duration > 0 && (
                    <span className='text-sm text-gray-500 flex items-center gap-1'>
                      <Clock className='w-4 h-4' />
                      {formatDuration(summary.duration)}
                    </span>
                  )}

                  {/* Material count */}
                  <span
                    className={`text-sm ${
                      isEmpty ? 'text-gray-400' : 'text-gray-600'
                    }`}
                  >
                    {isEmpty
                      ? 'No content'
                      : `${summary.count} material${summary.count !== 1 ? 's' : ''}`}
                  </span>

                  {/* Create with AI button */}
                  {onOpenAI && (
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        onOpenAI(weekNumber);
                      }}
                      className='p-1 text-gray-300 hover:text-purple-500 transition'
                      title={`Create with AI for ${topicLabel} ${weekNumber}`}
                    >
                      <Sparkles className='w-4 h-4' />
                    </button>
                  )}

                  {/* Delete week button */}
                  {onDeleteWeek && durationWeeks > 1 && (
                    <button
                      onClick={e =>
                        handleDeleteWeekClick(e, weekNumber, !isEmpty)
                      }
                      className='p-1 text-gray-300 hover:text-red-500 transition'
                      title={`Delete ${topicLabel} ${weekNumber}`}
                    >
                      <Trash2 className='w-4 h-4' />
                    </button>
                  )}
                </div>
              </div>

              {/* Expanded Content — full inline materials manager */}
              {isExpanded && (
                <div className='border-t border-gray-200 p-4 bg-white'>
                  <WeeklyMaterialsManager
                    unitId={unitId}
                    weekNumber={weekNumber}
                    topicLabel={topicLabel}
                    onMaterialsChanged={loadAllMaterials}
                  />
                </div>
              )}
            </div>
          );
        }
      )}

      {/* Bottom actions: Add Week + Apply Structure */}
      {(onAddWeek || onApplyStructure) && (
        <div className='flex items-center gap-3'>
          {onAddWeek && (
            <button
              onClick={onAddWeek}
              className='flex-1 flex items-center justify-center gap-2 p-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-purple-400 hover:text-purple-600 transition'
            >
              <Plus className='w-4 h-4' />
              Add {topicLabel}
            </button>
          )}
          {onApplyStructure && week1HasMaterials && (
            <div className='relative'>
              <button
                onClick={() => setShowApplyPopover(!showApplyPopover)}
                className='flex items-center gap-2 px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-purple-400 hover:text-purple-600 transition'
              >
                <Copy className='w-4 h-4' />
                Apply {topicLabel} 1 Structure
              </button>
              {showApplyPopover && (
                <div className='absolute bottom-full right-0 mb-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50 p-4'>
                  <div className='flex items-center justify-between mb-3'>
                    <h4 className='font-semibold text-gray-900 text-sm'>
                      Apply {topicLabel} 1 Structure
                    </h4>
                    <button
                      onClick={() => setShowApplyPopover(false)}
                      className='text-gray-400 hover:text-gray-600'
                    >
                      <X className='w-4 h-4' />
                    </button>
                  </div>
                  <p className='text-xs text-gray-500 mb-3'>
                    How should the structure be copied?
                  </p>
                  <div className='space-y-2'>
                    <button
                      onClick={() => {
                        setShowApplyPopover(false);
                        onApplyStructure('stubs');
                      }}
                      className='w-full text-left p-3 border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition'
                    >
                      <span className='font-medium text-sm text-gray-900'>
                        Copy material stubs
                      </span>
                      <p className='text-xs text-gray-500 mt-0.5'>
                        Mirrors {topicLabel} 1&apos;s materials (title, type,
                        category) as empty placeholders
                      </p>
                    </button>
                    <button
                      onClick={() => {
                        setShowApplyPopover(false);
                        onApplyStructure('categories');
                      }}
                      className='w-full text-left p-3 border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition'
                    >
                      <span className='font-medium text-sm text-gray-900'>
                        Categories only
                      </span>
                      <p className='text-xs text-gray-500 mt-0.5'>
                        One placeholder per category used in {topicLabel} 1
                      </p>
                    </button>
                  </div>
                  <p className='text-xs text-gray-400 mt-3'>
                    Only applies to {topicLabel.toLowerCase()}s with no existing
                    content.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WeekAccordion;
