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
  Book,
  Video,
  FileText,
  Edit,
} from 'lucide-react';
import { materialsApi, analyticsApi } from '../../services/unitStructureApi';
import {
  MaterialResponse,
  MaterialType,
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
}

interface WeekData {
  weekNumber: number;
  materials: MaterialResponse[];
  totalDuration: number;
  isLoading: boolean;
  isLoaded: boolean;
}

const materialTypeIcons: Record<MaterialType, React.ReactElement> = {
  [MaterialType.LECTURE]: <Presentation className='w-4 h-4' />,
  [MaterialType.TUTORIAL]: <Users className='w-4 h-4' />,
  [MaterialType.LAB]: <FlaskConical className='w-4 h-4' />,
  [MaterialType.WORKSHOP]: <Users className='w-4 h-4' />,
  [MaterialType.READING]: <Book className='w-4 h-4' />,
  [MaterialType.VIDEO]: <Video className='w-4 h-4' />,
  [MaterialType.ASSIGNMENT]: <FileText className='w-4 h-4' />,
  [MaterialType.OTHER]: <FileText className='w-4 h-4' />,
};

const materialTypeColors: Record<MaterialType, string> = {
  [MaterialType.LECTURE]: 'bg-blue-100 text-blue-700',
  [MaterialType.TUTORIAL]: 'bg-green-100 text-green-700',
  [MaterialType.LAB]: 'bg-purple-100 text-purple-700',
  [MaterialType.WORKSHOP]: 'bg-yellow-100 text-yellow-700',
  [MaterialType.READING]: 'bg-gray-100 text-gray-700',
  [MaterialType.VIDEO]: 'bg-red-100 text-red-700',
  [MaterialType.ASSIGNMENT]: 'bg-indigo-100 text-indigo-700',
  [MaterialType.OTHER]: 'bg-gray-100 text-gray-700',
};

export const WeekAccordion: React.FC<WeekAccordionProps> = ({
  unitId,
  durationWeeks,
  topicLabel = 'Week',
  expandedWeek,
  onWeekToggle,
  onAddMaterial,
}) => {
  const navigate = useNavigate();
  const [weeksData, setWeeksData] = useState<Map<number, WeekData>>(new Map());
  const [allMaterialsLoaded, setAllMaterialsLoaded] = useState(false);
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

    const typeCounts = new Map<MaterialType, number>();
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
              <button
                onClick={() => onWeekToggle(weekNumber)}
                className={`w-full flex items-center justify-between p-4 text-left transition ${
                  isExpanded ? 'bg-purple-50' : 'hover:bg-gray-50'
                }`}
              >
                <div className='flex items-center gap-3'>
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
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${materialTypeColors[type]}`}
                          title={`${count} ${type}${count > 1 ? 's' : ''}`}
                        >
                          {materialTypeIcons[type]}
                          {count > 1 && <span>{count}</span>}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

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
                </div>
              </button>

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
                      {weekData?.materials.map(material => (
                        <div
                          key={material.id}
                          className='flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition cursor-pointer group'
                          onClick={() => handleMaterialClick(material.id)}
                        >
                          <div className='flex items-center gap-3'>
                            <span
                              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${materialTypeColors[material.type]}`}
                            >
                              {materialTypeIcons[material.type]}
                              {material.type}
                            </span>
                            <span className='font-medium text-gray-900'>
                              {material.title}
                            </span>
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
                      ))}

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
    </div>
  );
};

export default WeekAccordion;
