import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Edit,
  Trash2,
  Copy,
  X,
} from 'lucide-react';
import { materialsApi, analyticsApi } from '../../services/unitStructureApi';
import {
  MaterialResponse,
  SessionFormat,
  MaterialCategory,
  WeekQualityScore,
} from '../../types/unitStructure';
import StarRating from '../shared/StarRating';
import toast from 'react-hot-toast';

interface WeekAccordionProps {
  unitId: string;
  durationWeeks: number;
  topicLabel?: string | undefined;
  expandedWeek: number | null;
  onWeekToggle: (weekNumber: number) => void;
  onAddMaterial: (weekNumber: number) => void;
  onAddWeek?: (() => void) | undefined;
  onDeleteWeek?: ((weekNumber: number) => void) | undefined;
  onApplyStructure?: ((mode: 'stubs' | 'categories') => void) | undefined;
}

interface WeekData {
  weekNumber: number;
  materials: MaterialResponse[];
  totalDuration: number;
  isLoading: boolean;
  isLoaded: boolean;
}

const sessionFormatIcons: Record<SessionFormat, React.ReactElement> = {
  [SessionFormat.LECTURE]: <Presentation className='w-4 h-4' />,
  [SessionFormat.TUTORIAL]: <Users className='w-4 h-4' />,
  [SessionFormat.LAB]: <FlaskConical className='w-4 h-4' />,
  [SessionFormat.WORKSHOP]: <Users className='w-4 h-4' />,
  [SessionFormat.SEMINAR]: <MessageSquare className='w-4 h-4' />,
  [SessionFormat.INDEPENDENT]: <BookOpen className='w-4 h-4' />,
  [SessionFormat.OTHER]: <FileText className='w-4 h-4' />,
};

const sessionFormatColors: Record<SessionFormat, string> = {
  [SessionFormat.LECTURE]: 'bg-blue-100 text-blue-700',
  [SessionFormat.TUTORIAL]: 'bg-green-100 text-green-700',
  [SessionFormat.LAB]: 'bg-purple-100 text-purple-700',
  [SessionFormat.WORKSHOP]: 'bg-yellow-100 text-yellow-700',
  [SessionFormat.SEMINAR]: 'bg-teal-100 text-teal-700',
  [SessionFormat.INDEPENDENT]: 'bg-orange-100 text-orange-700',
  [SessionFormat.OTHER]: 'bg-gray-100 text-gray-700',
};

const CATEGORY_ORDER: MaterialCategory[] = [
  MaterialCategory.PRE_CLASS,
  MaterialCategory.IN_CLASS,
  MaterialCategory.POST_CLASS,
  MaterialCategory.RESOURCES,
];

const CATEGORY_LABELS: Record<MaterialCategory, string> = {
  [MaterialCategory.PRE_CLASS]: 'Pre-class',
  [MaterialCategory.IN_CLASS]: 'In-class',
  [MaterialCategory.POST_CLASS]: 'Post-class',
  [MaterialCategory.RESOURCES]: 'Resources',
  [MaterialCategory.GENERAL]: 'General',
};

const CATEGORY_COLORS: Record<MaterialCategory, string> = {
  [MaterialCategory.PRE_CLASS]: 'text-amber-700 bg-amber-50 border-amber-200',
  [MaterialCategory.IN_CLASS]: 'text-blue-700 bg-blue-50 border-blue-200',
  [MaterialCategory.POST_CLASS]: 'text-green-700 bg-green-50 border-green-200',
  [MaterialCategory.RESOURCES]: 'text-gray-600 bg-gray-50 border-gray-200',
  [MaterialCategory.GENERAL]: 'text-gray-600 bg-gray-50 border-gray-200',
};

function groupByCategory(materials: MaterialResponse[]) {
  const general: MaterialResponse[] = [];
  const grouped = new Map<MaterialCategory, MaterialResponse[]>();

  for (const m of materials) {
    const cat = m.category;
    if (!cat || cat === MaterialCategory.GENERAL) {
      general.push(m);
    } else {
      const list = grouped.get(cat) || [];
      list.push(m);
      grouped.set(cat, list);
    }
  }

  return { general, grouped };
}

export const WeekAccordion: React.FC<WeekAccordionProps> = ({
  unitId,
  durationWeeks,
  topicLabel = 'Week',
  expandedWeek,
  onWeekToggle,
  onAddMaterial,
  onAddWeek,
  onDeleteWeek,
  onApplyStructure,
}) => {
  const navigate = useNavigate();
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

  // Load all materials for the unit on mount to show counts
  useEffect(() => {
    const loadAllMaterials = async () => {
      try {
        const materials = await materialsApi.getMaterialsByUnit(unitId);

        // Group by week
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
    };

    loadAllMaterials();
  }, [unitId, durationWeeks]);

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

    const typeCounts = new Map<SessionFormat, number>();
    weekData.materials.forEach(m => {
      typeCounts.set(m.type, (typeCounts.get(m.type) || 0) + 1);
    });

    return {
      count: weekData.materials.length,
      types: Array.from(typeCounts.entries()),
      duration: weekData.totalDuration,
    };
  };

  const handleMaterialClick = (materialId: string) => {
    navigate(`/units/${unitId}/materials/${materialId}`);
  };

  const handleDeleteWeekClick = (
    e: React.MouseEvent,
    weekNumber: number,
    hasContent: boolean
  ) => {
    e.stopPropagation();
    if (!onDeleteWeek) return;

    if (hasContent) {
      const confirmed = window.confirm(
        `${topicLabel} ${weekNumber} has materials that will be permanently deleted. Continue?`
      );
      if (!confirmed) return;
    }

    onDeleteWeek(weekNumber);
  };

  const renderMaterialRow = (material: MaterialResponse) => (
    <div
      key={material.id}
      className='flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition cursor-pointer group'
      onClick={() => handleMaterialClick(material.id)}
    >
      <div className='flex items-center gap-3'>
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${sessionFormatColors[material.type]}`}
        >
          {sessionFormatIcons[material.type]}
          {material.type}
        </span>
        <span className='font-medium text-gray-900'>{material.title}</span>
        {material.durationMinutes && (
          <span className='text-sm text-gray-500 flex items-center gap-1'>
            <Clock className='w-3 h-3' />
            {material.durationMinutes}min
          </span>
        )}
      </div>
      <button
        className='p-1.5 text-gray-400 hover:text-purple-600 opacity-0 group-hover:opacity-100 transition'
        onClick={e => {
          e.stopPropagation();
          handleMaterialClick(material.id);
        }}
      >
        <Edit className='w-4 h-4' />
      </button>
    </div>
  );

  const renderCategorizedMaterials = (materials: MaterialResponse[]) => {
    const { general, grouped } = groupByCategory(materials);
    const hasCategories = grouped.size > 0;

    if (!hasCategories) {
      // No categorized materials — render flat list
      return materials.map(renderMaterialRow);
    }

    return (
      <>
        {/* Ungrouped (general) materials at the top */}
        {general.map(renderMaterialRow)}

        {/* Categorized sections */}
        {CATEGORY_ORDER.filter(cat => grouped.has(cat)).map(cat => (
          <div key={cat} className='mt-1'>
            <div
              className={`text-xs font-semibold uppercase tracking-wider px-3 py-1.5 rounded-t-md border-b ${CATEGORY_COLORS[cat]}`}
            >
              {CATEGORY_LABELS[cat]}
            </div>
            <div className='space-y-1 pt-1'>
              {grouped.get(cat)!.map(renderMaterialRow)}
            </div>
          </div>
        ))}
      </>
    );
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
                      {summary.types.slice(0, 4).map(([type, count]) => (
                        <span
                          key={type}
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${sessionFormatColors[type]}`}
                          title={`${count} ${type}${count > 1 ? 's' : ''}`}
                        >
                          {sessionFormatIcons[type]}
                          {count > 1 && <span>{count}</span>}
                        </span>
                      ))}
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

              {/* Expanded Content */}
              {isExpanded && (
                <div className='border-t border-gray-200 p-4 bg-white'>
                  {isEmpty ? (
                    <div className='text-center py-6'>
                      <p className='text-gray-500 mb-4'>
                        No materials added for this week yet.
                      </p>
                      <button
                        onClick={() => onAddMaterial(weekNumber)}
                        className='inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition'
                      >
                        <Plus className='w-4 h-4' />
                        Add Material
                      </button>
                    </div>
                  ) : (
                    <div className='space-y-2'>
                      {renderCategorizedMaterials(weekData?.materials ?? [])}

                      {/* Add more materials button */}
                      <button
                        onClick={() => onAddMaterial(weekNumber)}
                        className='w-full flex items-center justify-center gap-2 p-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-purple-400 hover:text-purple-600 transition'
                      >
                        <Plus className='w-4 h-4' />
                        Add Material
                      </button>
                    </div>
                  )}
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
