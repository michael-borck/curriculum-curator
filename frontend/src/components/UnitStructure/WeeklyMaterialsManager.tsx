import React, { useState, useEffect } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  Plus,
  Edit2,
  Trash2,
  Clock,
  FileText,
  Video,
  Book,
  Users,
  FlaskConical,
  Presentation,
  Copy,
  Clipboard,
  GripVertical,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Loader2,
  Lightbulb,
  Download,
  History,
  X,
} from 'lucide-react';
import axios from 'axios';
import { materialsApi } from '../../services/unitStructureApi';
import { materialVersionApi } from '../../services/materialVersionApi';
import VersionHistory from '../../features/materials/VersionHistory';
import type { VersionHistoryApi } from '../../features/materials/VersionHistory';
import { generateContent } from '../../services/api';
import {
  MaterialResponse,
  MaterialCreate,
  MaterialUpdate,
  MaterialType,
  MaterialStatus,
  MaterialCategory,
  WeekMaterials,
} from '../../types/unitStructure';
import {
  useTeachingStyleStore,
  pedagogyOptions,
  getPedagogyHint,
  getPedagogyStaticGuidance,
} from '../../stores/teachingStyleStore';
import { useAILevel } from '../../hooks/useAILevel';
import type { PedagogyType } from '../../types';
import toast from 'react-hot-toast';

interface WeeklyMaterialsManagerProps {
  unitId: string;
  weekNumber: number;
  topicLabel?: string | undefined;
}

interface MaterialFormData {
  title: string;
  type: MaterialType;
  category: MaterialCategory;
  description: string;
  durationMinutes: number;
  status: MaterialStatus;
  topic: string;
  useAI: boolean;
  overrideStyle: PedagogyType | null;
}

const CATEGORY_OPTIONS: { value: MaterialCategory; label: string }[] = [
  { value: MaterialCategory.GENERAL, label: 'General' },
  { value: MaterialCategory.PRE_CLASS, label: 'Pre-class' },
  { value: MaterialCategory.IN_CLASS, label: 'In-class' },
  { value: MaterialCategory.POST_CLASS, label: 'Post-class' },
  { value: MaterialCategory.RESOURCES, label: 'Resources' },
];

const QualityBadge: React.FC<{ score: number }> = ({ score }) => {
  let grade: string;
  let colorClass: string;

  if (score >= 90) {
    grade = 'A';
    colorClass = 'bg-green-100 text-green-800';
  } else if (score >= 70) {
    grade = 'B';
    colorClass = 'bg-blue-100 text-blue-800';
  } else if (score >= 50) {
    grade = 'C';
    colorClass = 'bg-yellow-100 text-yellow-800';
  } else {
    grade = 'D';
    colorClass = 'bg-red-100 text-red-800';
  }

  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-semibold ${colorClass}`}
      title={`Quality score: ${score}/100`}
    >
      {grade}
    </span>
  );
};

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
  [MaterialType.LECTURE]: 'bg-blue-100 text-blue-800',
  [MaterialType.TUTORIAL]: 'bg-green-100 text-green-800',
  [MaterialType.LAB]: 'bg-purple-100 text-purple-800',
  [MaterialType.WORKSHOP]: 'bg-yellow-100 text-yellow-800',
  [MaterialType.READING]: 'bg-gray-100 text-gray-800',
  [MaterialType.VIDEO]: 'bg-red-100 text-red-800',
  [MaterialType.ASSIGNMENT]: 'bg-indigo-100 text-indigo-800',
  [MaterialType.OTHER]: 'bg-gray-100 text-gray-800',
};

const exportFormats = [
  { value: 'html', label: 'HTML' },
  { value: 'pdf', label: 'PDF' },
  { value: 'docx', label: 'DOCX' },
  { value: 'pptx', label: 'PPTX' },
] as const;

type ExportFormatValue = (typeof exportFormats)[number]['value'];

const handleMaterialDownload = async (
  materialId: string,
  format: ExportFormatValue
) => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get(
      `/api/materials/${materialId}/export?format=${format}`,
      {
        responseType: 'blob',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }
    );
    const disposition = response.headers['content-disposition'] as
      | string
      | undefined;
    const filenameMatch = disposition?.match(/filename="?([^"]+)"?/);
    const filename = filenameMatch?.[1] ?? `material.${format}`;
    const url = URL.createObjectURL(response.data as Blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
    a.remove();
    toast.success(`Exported as ${format.toUpperCase()}`);
  } catch {
    toast.error('Failed to export material');
  }
};

const SortableMaterialItem: React.FC<{
  material: MaterialResponse;
  onEdit: (material: MaterialResponse) => void;
  onDelete: (id: string) => void;
  onDuplicate: (material: MaterialResponse) => void;
  onHistory: (material: MaterialResponse) => void;
}> = ({ material, onEdit, onDelete, onDuplicate, onHistory }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const exportRef = React.useRef<HTMLDivElement>(null);

  // Close export menu on click outside
  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (exportRef.current && !exportRef.current.contains(e.target as Node)) {
        setShowExportMenu(false);
      }
    };
    if (showExportMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showExportMenu]);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: material.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white border rounded-lg p-4 ${
        isDragging ? 'shadow-lg' : 'shadow-sm'
      }`}
    >
      <div className='flex items-start justify-between'>
        <div className='flex items-start space-x-3 flex-1'>
          <button
            {...attributes}
            {...listeners}
            className='mt-1 text-gray-400 hover:text-gray-600 cursor-move'
          >
            <GripVertical className='w-5 h-5' />
          </button>

          <div className='flex-1'>
            <div className='flex items-center space-x-2'>
              <span
                className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${materialTypeColors[material.type]}`}
              >
                {materialTypeIcons[material.type]}
                <span className='ml-1'>{material.type}</span>
              </span>

              <h4 className='font-medium text-gray-900'>{material.title}</h4>

              {material.qualityScore != null && (
                <QualityBadge score={material.qualityScore} />
              )}

              {material.durationMinutes && (
                <span className='inline-flex items-center text-xs text-gray-500'>
                  <Clock className='w-3 h-3 mr-1' />
                  {material.durationMinutes} min
                </span>
              )}

              {material.status === MaterialStatus.DRAFT && (
                <span className='px-2 py-1 text-xs font-medium text-yellow-800 bg-yellow-100 rounded-full'>
                  Draft
                </span>
              )}
            </div>

            {material.description && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className='mt-2 text-sm text-gray-600 hover:text-gray-800 flex items-center'
              >
                {isExpanded ? (
                  <ChevronUp className='w-4 h-4 mr-1' />
                ) : (
                  <ChevronDown className='w-4 h-4 mr-1' />
                )}
                Description
              </button>
            )}

            {isExpanded && material.description && (
              <p className='mt-2 text-sm text-gray-600'>
                {material.description}
              </p>
            )}
          </div>
        </div>

        <div className='flex items-center space-x-2 ml-4'>
          {material.description && (
            <div className='relative' ref={exportRef}>
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                className='p-1 text-gray-400 hover:text-emerald-600'
                title='Download material'
              >
                <Download className='w-4 h-4' />
              </button>
              {showExportMenu && (
                <div className='absolute right-0 mt-1 w-36 bg-white border border-gray-200 rounded-lg shadow-lg z-50'>
                  {exportFormats.map(fmt => (
                    <button
                      key={fmt.value}
                      className='w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg'
                      onClick={() => {
                        setShowExportMenu(false);
                        handleMaterialDownload(material.id, fmt.value);
                      }}
                    >
                      {fmt.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          {material.description && (
            <button
              onClick={() => {
                const wrapper = `<div style="font-family: system-ui, sans-serif; line-height: 1.6;">${material.description}</div>`;
                navigator.clipboard.writeText(wrapper).then(
                  () => toast.success('Content copied to clipboard'),
                  () => toast.error('Failed to copy to clipboard')
                );
              }}
              className='p-1 text-gray-400 hover:text-green-600'
              title='Copy HTML to clipboard'
            >
              <Clipboard className='w-4 h-4' />
            </button>
          )}
          {material.description && (
            <button
              onClick={() => onHistory(material)}
              className='p-1 text-gray-400 hover:text-indigo-600'
              title='Version history'
            >
              <History className='w-4 h-4' />
            </button>
          )}
          <button
            onClick={() => onDuplicate(material)}
            className='p-1 text-gray-400 hover:text-blue-600'
            title='Duplicate'
          >
            <Copy className='w-4 h-4' />
          </button>
          <button
            onClick={() => onEdit(material)}
            className='p-1 text-gray-400 hover:text-blue-600'
            title='Edit'
          >
            <Edit2 className='w-4 h-4' />
          </button>
          <button
            onClick={() => onDelete(material.id)}
            className='p-1 text-gray-400 hover:text-red-600'
            title='Delete'
          >
            <Trash2 className='w-4 h-4' />
          </button>
        </div>
      </div>
    </div>
  );
};

export const WeeklyMaterialsManager: React.FC<WeeklyMaterialsManagerProps> = ({
  unitId,
  weekNumber,
  topicLabel = 'Week',
}) => {
  const { globalStyle } = useTeachingStyleStore();
  const { canGenerate } = useAILevel();
  const [weekMaterials, setWeekMaterials] = useState<WeekMaterials | null>(
    null
  );
  const [materials, setMaterials] = useState<MaterialResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingMaterial, setEditingMaterial] =
    useState<MaterialResponse | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [historyMaterial, setHistoryMaterial] =
    useState<MaterialResponse | null>(null);
  const [formData, setFormData] = useState<MaterialFormData>({
    title: '',
    type: MaterialType.LECTURE,
    category: MaterialCategory.GENERAL,
    description: '',
    durationMinutes: 60,
    status: MaterialStatus.DRAFT,
    topic: '',
    useAI: false,
    overrideStyle: null,
  });

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    fetchMaterials();
    // TECH-DEBT: Missing dependency 'fetchMaterials' - needs refactoring to useCallback
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unitId, weekNumber]);

  const fetchMaterials = async () => {
    try {
      setLoading(true);
      const data = await materialsApi.getMaterialsByWeek(unitId, weekNumber);
      setWeekMaterials(data);
      setMaterials(data.materials);
    } catch (error) {
      toast.error('Failed to fetch materials');
      console.error('Error fetching materials:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (editingMaterial) {
        const updateData: MaterialUpdate = {
          title: formData.title,
          type: formData.type,
          category: formData.category,
          ...(formData.description && { description: formData.description }),
          ...(formData.durationMinutes && {
            durationMinutes: formData.durationMinutes,
          }),
          status: formData.status,
        };

        await materialsApi.updateMaterial(editingMaterial.id, updateData);
        toast.success('Material updated successfully');
      } else {
        const createData: MaterialCreate = {
          weekNumber,
          title: formData.title,
          type: formData.type,
          category: formData.category,
          ...(formData.description && { description: formData.description }),
          ...(formData.durationMinutes && {
            durationMinutes: formData.durationMinutes,
          }),
          status: formData.status,
        };

        await materialsApi.createMaterial(unitId, createData);
        toast.success('Material created successfully');
      }

      await fetchMaterials();
      handleCancel();
    } catch (error) {
      toast.error(
        editingMaterial
          ? 'Failed to update material'
          : 'Failed to create material'
      );
      console.error('Error saving material:', error);
    }
  };

  const handleEdit = (material: MaterialResponse) => {
    setEditingMaterial(material);
    setFormData({
      title: material.title,
      type: material.type,
      category: material.category || MaterialCategory.GENERAL,
      description: material.description || '',
      durationMinutes: material.durationMinutes || 60,
      status: material.status,
      topic: '',
      useAI: false,
      overrideStyle: null,
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this material?'))
      return;

    try {
      await materialsApi.deleteMaterial(id);
      toast.success('Material deleted successfully');
      await fetchMaterials();
    } catch (error) {
      toast.error('Failed to delete material');
      console.error('Error deleting material:', error);
    }
  };

  const handleDuplicate = async (material: MaterialResponse) => {
    const targetWeek = window.prompt(
      `Duplicate to which ${topicLabel.toLowerCase()}? (Current: ${topicLabel} ${weekNumber})`,
      String(weekNumber)
    );
    if (!targetWeek) return;

    const weekNum = parseInt(targetWeek);
    if (isNaN(weekNum) || weekNum < 1 || weekNum > 52) {
      toast.error('Invalid week number');
      return;
    }

    try {
      await materialsApi.duplicateMaterial(material.id, weekNum);
      toast.success(`Material duplicated to ${topicLabel} ${weekNum}`);
      if (weekNum === weekNumber) {
        await fetchMaterials();
      }
    } catch (error) {
      toast.error('Failed to duplicate material');
      console.error('Error duplicating material:', error);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingMaterial(null);
    setFormData({
      title: '',
      type: MaterialType.LECTURE,
      category: MaterialCategory.GENERAL,
      description: '',
      durationMinutes: 60,
      status: MaterialStatus.DRAFT,
      topic: '',
      useAI: false,
      overrideStyle: null,
    });
  };

  const handleGenerateAI = async () => {
    if (!formData.topic.trim()) {
      toast.error('Please enter a topic for AI generation');
      return;
    }

    setIsGenerating(true);
    try {
      const style = formData.overrideStyle || globalStyle;
      // Map material type to content type for API
      const contentType =
        formData.type === MaterialType.LECTURE
          ? 'lecture'
          : formData.type === MaterialType.ASSIGNMENT
            ? 'assignment'
            : formData.type === MaterialType.LAB
              ? 'project'
              : 'lecture';

      const response = await generateContent(
        contentType,
        style,
        formData.topic
      );
      const generatedContent = response.data?.content || '';

      // Set the generated content as description
      setFormData(prev => ({
        ...prev,
        description: generatedContent,
        title: prev.title || formData.topic,
      }));

      toast.success('Content generated! Review and save when ready.');
    } catch (error) {
      console.error('Error generating content:', error);
      toast.error('Failed to generate content. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = materials.findIndex(m => m.id === active.id);
      const newIndex = materials.findIndex(m => m.id === over.id);

      const newOrder = arrayMove(materials, oldIndex, newIndex);
      setMaterials(newOrder);

      try {
        await materialsApi.reorderMaterials(
          unitId,
          weekNumber,
          newOrder.map(m => m.id)
        );
        toast.success('Materials reordered successfully');
      } catch (error) {
        toast.error('Failed to reorder materials');
        console.error('Error reordering materials:', error);
        await fetchMaterials();
      }
    }
  };

  const historyApi: VersionHistoryApi | null = React.useMemo(() => {
    if (!historyMaterial) return null;
    const mid = historyMaterial.id;
    return {
      history: (limit?: number) => materialVersionApi.history(mid, limit),
      versionBody: (commit: string) =>
        materialVersionApi.versionBody(mid, commit),
      diff: (oldCommit: string, newCommit?: string) =>
        materialVersionApi.diff(mid, oldCommit, newCommit),
      revert: (commit: string) => materialVersionApi.revert(mid, commit),
    };
  }, [historyMaterial]);

  if (loading) {
    return <div className='animate-pulse'>Loading materials...</div>;
  }

  return (
    <div className='space-y-6'>
      <div className='flex justify-between items-center'>
        <div>
          <h3 className='text-lg font-semibold text-gray-900'>
            {topicLabel} {weekNumber} Materials
          </h3>
          {weekMaterials && (
            <div className='mt-1 flex items-center space-x-4 text-sm text-gray-600'>
              <span>{weekMaterials.materialCount} materials</span>
              {weekMaterials.totalDurationMinutes > 0 && (
                <span className='flex items-center'>
                  <Clock className='w-4 h-4 mr-1' />
                  {Math.floor(weekMaterials.totalDurationMinutes / 60)}h{' '}
                  {weekMaterials.totalDurationMinutes % 60}m total
                </span>
              )}
            </div>
          )}
        </div>

        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className='inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700'
          >
            <Plus className='w-4 h-4 mr-2' />
            Add Material
          </button>
        )}
      </div>

      {showForm && (
        <div className='bg-white border rounded-lg p-6'>
          <h4 className='text-lg font-medium mb-4'>
            {editingMaterial ? 'Edit Material' : 'Add New Material'}
          </h4>

          <form onSubmit={handleSubmit} className='space-y-4'>
            <div className='grid grid-cols-2 gap-4'>
              <div>
                <label className='block text-sm font-medium text-gray-700'>
                  Type *
                </label>
                <select
                  value={formData.type}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      type: e.target.value as MaterialType,
                    })
                  }
                  className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                >
                  {Object.values(MaterialType).map(type => (
                    <option key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700'>
                  Duration (minutes)
                </label>
                <input
                  type='number'
                  value={formData.durationMinutes}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      durationMinutes: parseInt(e.target.value) || 0,
                    })
                  }
                  className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                  min='0'
                />
              </div>
            </div>

            <div>
              <label className='block text-sm font-medium text-gray-700'>
                Category
              </label>
              <select
                value={formData.category}
                onChange={e =>
                  setFormData({
                    ...formData,
                    category: e.target.value as MaterialCategory,
                  })
                }
                className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
              >
                {CATEGORY_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className='block text-sm font-medium text-gray-700'>
                Title *
              </label>
              <input
                type='text'
                value={formData.title}
                onChange={e =>
                  setFormData({ ...formData, title: e.target.value })
                }
                className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                placeholder='e.g., Introduction to Machine Learning'
                required
              />
            </div>

            {/* AI Generation Section — only shown when canGenerate */}
            {canGenerate ? (
              <div className='border border-purple-200 rounded-lg p-4 bg-purple-50'>
                <div className='flex items-center justify-between mb-3'>
                  <div className='flex items-center gap-2'>
                    <Sparkles className='w-5 h-5 text-purple-600' />
                    <span className='font-medium text-purple-900'>
                      AI Content Generation
                    </span>
                  </div>
                  <label className='flex items-center gap-2 cursor-pointer'>
                    <input
                      type='checkbox'
                      checked={formData.useAI}
                      onChange={e =>
                        setFormData({ ...formData, useAI: e.target.checked })
                      }
                      className='rounded border-gray-300 text-purple-600 focus:ring-purple-500'
                    />
                    <span className='text-sm text-gray-700'>Enable AI</span>
                  </label>
                </div>

                {formData.useAI && (
                  <div className='space-y-3'>
                    <div>
                      <label className='block text-sm font-medium text-gray-700'>
                        Topic for AI Generation
                      </label>
                      <input
                        type='text'
                        value={formData.topic}
                        onChange={e =>
                          setFormData({ ...formData, topic: e.target.value })
                        }
                        className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500'
                        placeholder='e.g., Supervised vs unsupervised learning algorithms'
                      />
                      <p className='text-xs text-gray-500 mt-1'>
                        Describe what you want the AI to generate content about
                      </p>
                    </div>

                    <div>
                      <label className='block text-sm font-medium text-gray-700'>
                        Teaching Style
                      </label>
                      <div className='flex items-center gap-2 mt-1'>
                        <select
                          value={formData.overrideStyle || ''}
                          onChange={e =>
                            setFormData({
                              ...formData,
                              overrideStyle: e.target.value
                                ? (e.target.value as PedagogyType)
                                : null,
                            })
                          }
                          className='block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500'
                        >
                          <option value=''>
                            Use Global (
                            {pedagogyOptions.find(p => p.id === globalStyle)
                              ?.name || globalStyle}
                            )
                          </option>
                          {pedagogyOptions.map(option => (
                            <option key={option.id} value={option.id}>
                              {option.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      <p className='text-xs text-purple-600 mt-1'>
                        {getPedagogyHint(formData.overrideStyle || globalStyle)}
                      </p>
                    </div>

                    <button
                      type='button'
                      onClick={handleGenerateAI}
                      disabled={isGenerating || !formData.topic.trim()}
                      className='w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed'
                    >
                      {isGenerating ? (
                        <>
                          <Loader2 className='w-4 h-4 animate-spin' />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Sparkles className='w-4 h-4' />
                          Generate Content
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className='border border-blue-200 rounded-lg p-4 bg-blue-50'>
                <div className='flex items-center gap-2 mb-3'>
                  <Lightbulb className='w-5 h-5 text-blue-600' />
                  <span className='font-medium text-blue-900'>
                    Pedagogy Guidance
                  </span>
                </div>
                <ul className='space-y-2 text-sm text-gray-700'>
                  {getPedagogyStaticGuidance(globalStyle).map((tip, i) => (
                    <li key={i} className='flex items-start gap-2'>
                      <span className='text-blue-600 font-medium shrink-0'>
                        {i + 1}.
                      </span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <label className='block text-sm font-medium text-gray-700'>
                Description / Content
              </label>
              <textarea
                value={formData.description}
                onChange={e =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={formData.useAI ? 10 : 3}
                className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 font-mono text-sm'
                placeholder={
                  formData.useAI
                    ? 'AI-generated content will appear here...'
                    : 'Enter a description for this material...'
                }
              />
            </div>

            <div>
              <label className='block text-sm font-medium text-gray-700'>
                Status
              </label>
              <select
                value={formData.status}
                onChange={e =>
                  setFormData({
                    ...formData,
                    status: e.target.value as MaterialStatus,
                  })
                }
                className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
              >
                {Object.values(MaterialStatus).map(status => (
                  <option key={status} value={status}>
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div className='flex justify-end space-x-3'>
              <button
                type='button'
                onClick={handleCancel}
                className='px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50'
              >
                Cancel
              </button>
              <button
                type='submit'
                disabled={isGenerating}
                className='px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50'
              >
                {editingMaterial ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      )}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={materials.map(m => m.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className='space-y-3'>
            {materials.length === 0 ? (
              <div className='bg-white border border-gray-200 rounded-lg p-8'>
                <div className='text-center'>
                  <FileText className='w-10 h-10 text-gray-400 mx-auto mb-3' />
                  <h4 className='text-gray-900 font-medium mb-1'>
                    No materials for {topicLabel} {weekNumber}
                  </h4>
                  <p className='text-gray-500 text-sm mb-4'>
                    Add your first material to start building this week&apos;s
                    content.
                  </p>
                  <button
                    onClick={() => setShowForm(true)}
                    className='inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700'
                  >
                    <Plus className='w-4 h-4 mr-2' />
                    Add Material
                  </button>
                </div>

                {/* Contextual Tips */}
                <div className='mt-6 bg-purple-50 rounded-lg p-4'>
                  <div className='flex items-center gap-2 mb-3'>
                    <Lightbulb className='w-4 h-4 text-purple-600' />
                    <span className='text-sm font-medium text-purple-900'>
                      Tips for {topicLabel} {weekNumber}
                    </span>
                  </div>
                  <ul className='space-y-2 text-sm'>
                    <li className='flex items-start gap-2'>
                      <span className='text-purple-600 font-medium'>1.</span>
                      <span className='text-gray-700'>
                        <strong>Start with a lecture</strong> to introduce the
                        week&apos;s concepts
                      </span>
                    </li>
                    <li className='flex items-start gap-2'>
                      <span className='text-purple-600 font-medium'>2.</span>
                      <span className='text-gray-700'>
                        <strong>Use AI generation</strong> to quickly draft
                        content aligned with your teaching style
                      </span>
                    </li>
                    <li className='flex items-start gap-2'>
                      <span className='text-purple-600 font-medium'>3.</span>
                      <span className='text-gray-700'>
                        <strong>Drag to reorder</strong> materials once you have
                        multiple items
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
            ) : (
              materials.map(material => (
                <SortableMaterialItem
                  key={material.id}
                  material={material}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onDuplicate={handleDuplicate}
                  onHistory={setHistoryMaterial}
                />
              ))
            )}
          </div>
        </SortableContext>
      </DndContext>

      {/* Version History Modal */}
      {historyMaterial && historyApi && (
        <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40'>
          <div className='bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[80vh] overflow-y-auto m-4'>
            <div className='flex items-center justify-between p-4 border-b'>
              <h3 className='text-lg font-semibold text-gray-900'>
                History: {historyMaterial.title}
              </h3>
              <button
                onClick={() => setHistoryMaterial(null)}
                className='p-1 text-gray-400 hover:text-gray-600'
              >
                <X className='w-5 h-5' />
              </button>
            </div>
            <div className='p-4'>
              <VersionHistory
                api={historyApi}
                onVersionRestore={() => {
                  fetchMaterials();
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
