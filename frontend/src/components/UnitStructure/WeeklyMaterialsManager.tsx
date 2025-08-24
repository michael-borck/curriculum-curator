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
  GripVertical,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { materialsApi } from '../../services/unitStructureApi';
import {
  MaterialResponse,
  MaterialCreate,
  MaterialUpdate,
  MaterialType,
  MaterialStatus,
  WeekMaterials,
} from '../../types/unitStructure';
import toast from 'react-hot-toast';

interface WeeklyMaterialsManagerProps {
  unitId: string;
  weekNumber: number;
}

interface MaterialFormData {
  title: string;
  type: MaterialType;
  description: string;
  durationMinutes: number;
  status: MaterialStatus;
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
  [MaterialType.LECTURE]: 'bg-blue-100 text-blue-800',
  [MaterialType.TUTORIAL]: 'bg-green-100 text-green-800',
  [MaterialType.LAB]: 'bg-purple-100 text-purple-800',
  [MaterialType.WORKSHOP]: 'bg-yellow-100 text-yellow-800',
  [MaterialType.READING]: 'bg-gray-100 text-gray-800',
  [MaterialType.VIDEO]: 'bg-red-100 text-red-800',
  [MaterialType.ASSIGNMENT]: 'bg-indigo-100 text-indigo-800',
  [MaterialType.OTHER]: 'bg-gray-100 text-gray-800',
};

const SortableMaterialItem: React.FC<{
  material: MaterialResponse;
  onEdit: (material: MaterialResponse) => void;
  onDelete: (id: string) => void;
  onDuplicate: (material: MaterialResponse) => void;
}> = ({ material, onEdit, onDelete, onDuplicate }) => {
  const [isExpanded, setIsExpanded] = useState(false);
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
}) => {
  const [weekMaterials, setWeekMaterials] = useState<WeekMaterials | null>(
    null
  );
  const [materials, setMaterials] = useState<MaterialResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingMaterial, setEditingMaterial] =
    useState<MaterialResponse | null>(null);
  const [formData, setFormData] = useState<MaterialFormData>({
    title: '',
    type: MaterialType.LECTURE,
    description: '',
    durationMinutes: 60,
    status: MaterialStatus.DRAFT,
  });

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    fetchMaterials();
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
      description: material.description || '',
      durationMinutes: material.durationMinutes || 60,
      status: material.status,
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this material?')) return;

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
      `Duplicate to which week? (Current: Week ${weekNumber})`,
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
      toast.success(`Material duplicated to Week ${weekNum}`);
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
      description: '',
      durationMinutes: 60,
      status: MaterialStatus.DRAFT,
    });
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

  if (loading) {
    return <div className='animate-pulse'>Loading materials...</div>;
  }

  return (
    <div className='space-y-6'>
      <div className='flex justify-between items-center'>
        <div>
          <h3 className='text-lg font-semibold text-gray-900'>
            Week {weekNumber} Materials
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
                required
              />
            </div>

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
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={e =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={3}
                className='mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
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
                className='px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700'
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
              <div className='text-center py-8 text-gray-500'>
                No materials added for this week yet.
              </div>
            ) : (
              materials.map(material => (
                <SortableMaterialItem
                  key={material.id}
                  material={material}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onDuplicate={handleDuplicate}
                />
              ))
            )}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  );
};
