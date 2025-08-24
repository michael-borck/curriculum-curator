import React, { useState, useEffect } from 'react';
import {
  Plus,
  Edit2,
  Trash2,
  GripVertical,
  AlertCircle,
  CheckCircle,
  BookOpen,
  FileText,
} from 'lucide-react';
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
import { learningOutcomesApi } from '../../services/unitStructureApi';
import {
  ULOWithMappings,
  ULOCreate,
  ULOUpdate,
} from '../../types/unitStructure';

interface ULOManagerProps {
  unitId: string;
  onULOsChange?: () => void;
}

// Sortable ULO Item Component
interface SortableULOItemProps {
  ulo: ULOWithMappings;
  editingId: string | null;
  formData: ULOCreate;
  bloomLevels: Array<{ value: string; label: string; color: string }>;
  onEdit: (ulo: ULOWithMappings) => void;
  onUpdate: (uloId: string) => void;
  onDelete: (uloId: string) => void;
  onCancelEdit: () => void;
  onFormChange: (data: ULOCreate) => void;
  getBloomColor: (level: string) => string;
  getCoverageIcon: (ulo: ULOWithMappings) => React.ReactNode;
}

const SortableULOItem: React.FC<SortableULOItemProps> = ({
  ulo,
  editingId,
  formData,
  bloomLevels,
  onEdit,
  onUpdate,
  onDelete,
  onCancelEdit,
  onFormChange,
  getBloomColor,
  getCoverageIcon,
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: ulo.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`p-4 ${isDragging ? 'bg-gray-50 shadow-lg' : 'bg-white'}`}
    >
      {editingId === ulo.id ? (
        // Edit Mode
        <div className='grid grid-cols-12 gap-4'>
          <div className='col-span-2'>
            <input
              type='text'
              value={formData.code || ulo.code}
              onChange={e =>
                onFormChange({ ...formData, code: e.target.value })
              }
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
            />
          </div>
          <div className='col-span-6'>
            <input
              type='text'
              value={formData.description || ulo.description}
              onChange={e =>
                onFormChange({ ...formData, description: e.target.value })
              }
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
            />
          </div>
          <div className='col-span-2'>
            <select
              value={formData.bloomLevel || ulo.bloomLevel}
              onChange={e =>
                onFormChange({ ...formData, bloomLevel: e.target.value })
              }
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
            >
              {bloomLevels.map(level => (
                <option key={level.value} value={level.value}>
                  {level.label}
                </option>
              ))}
            </select>
          </div>
          <div className='col-span-2 flex gap-2'>
            <button
              onClick={() => onUpdate(ulo.id)}
              className='flex-1 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700'
            >
              Save
            </button>
            <button
              onClick={onCancelEdit}
              className='flex-1 px-3 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400'
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        // View Mode
        <div className='flex items-center justify-between'>
          <div className='flex items-center space-x-4'>
            <div {...attributes} {...listeners} className='cursor-move'>
              <GripVertical className='w-5 h-5 text-gray-400' />
            </div>
            <div className='flex items-center space-x-3'>
              <span className='font-semibold text-gray-900'>{ulo.code}</span>
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${getBloomColor(ulo.bloomLevel)}`}
              >
                {bloomLevels.find(b => b.value === ulo.bloomLevel)?.label}
              </span>
              {getCoverageIcon(ulo)}
            </div>
            <span className='text-gray-700'>{ulo.description}</span>
          </div>
          <div className='flex items-center space-x-2'>
            <div className='flex items-center space-x-2 text-sm text-gray-500'>
              <BookOpen className='w-4 h-4' />
              <span>{ulo.materialCount}</span>
              <FileText className='w-4 h-4 ml-2' />
              <span>{ulo.assessmentCount}</span>
            </div>
            <button
              onClick={() => onEdit(ulo)}
              className='p-1 text-gray-500 hover:text-indigo-600'
            >
              <Edit2 className='w-4 h-4' />
            </button>
            <button
              onClick={() => onDelete(ulo.id)}
              className='p-1 text-gray-500 hover:text-red-600'
            >
              <Trash2 className='w-4 h-4' />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const ULOManager: React.FC<ULOManagerProps> = ({ unitId, onULOsChange }) => {
  const [ulos, setUlos] = useState<ULOWithMappings[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [coverage, setCoverage] = useState<any>(null);

  // Form state
  const [formData, setFormData] = useState<ULOCreate>({
    code: '',
    description: '',
    bloomLevel: 'understand',
  });

  // Bloom's Taxonomy levels
  const bloomLevels = [
    {
      value: 'remember',
      label: 'Remember',
      color: 'bg-blue-100 text-blue-700',
    },
    {
      value: 'understand',
      label: 'Understand',
      color: 'bg-green-100 text-green-700',
    },
    { value: 'apply', label: 'Apply', color: 'bg-yellow-100 text-yellow-700' },
    {
      value: 'analyze',
      label: 'Analyze',
      color: 'bg-orange-100 text-orange-700',
    },
    {
      value: 'evaluate',
      label: 'Evaluate',
      color: 'bg-purple-100 text-purple-700',
    },
    { value: 'create', label: 'Create', color: 'bg-red-100 text-red-700' },
  ];

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    loadULOs();
    loadCoverage();
  }, [unitId]);

  const loadULOs = async () => {
    try {
      setLoading(true);
      const data = await learningOutcomesApi.getULOsByUnit(unitId, true);
      setUlos(data);
      setError(null);
    } catch (err) {
      setError('Failed to load learning outcomes');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadCoverage = async () => {
    try {
      const data = await learningOutcomesApi.getULOCoverage(unitId);
      setCoverage(data);
    } catch (err) {
      console.error('Failed to load coverage data:', err);
    }
  };

  const handleCreate = async () => {
    if (!formData.code || !formData.description) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      await learningOutcomesApi.createULO(unitId, formData);
      setIsAddingNew(false);
      setFormData({ code: '', description: '', bloomLevel: 'understand' });
      loadULOs();
      loadCoverage();
      onULOsChange?.();
    } catch (err) {
      setError('Failed to create learning outcome');
      console.error(err);
    }
  };

  const handleUpdate = async (uloId: string) => {
    const ulo = ulos.find(u => u.id === uloId);
    if (!ulo) return;

    const updateData: ULOUpdate = {
      code: formData.code || ulo.code,
      description: formData.description || ulo.description,
      bloomLevel: formData.bloomLevel || ulo.bloomLevel,
    };

    try {
      await learningOutcomesApi.updateULO(uloId, updateData);
      setEditingId(null);
      setFormData({ code: '', description: '', bloomLevel: 'understand' });
      loadULOs();
      onULOsChange?.();
    } catch (err) {
      setError('Failed to update learning outcome');
      console.error(err);
    }
  };

  const handleDelete = async (uloId: string) => {
    if (!window.confirm('Are you sure you want to delete this learning outcome?')) {
      return;
    }

    try {
      await learningOutcomesApi.deleteULO(uloId);
      loadULOs();
      loadCoverage();
      onULOsChange?.();
    } catch (err) {
      setError(
        'Failed to delete learning outcome. It may have existing mappings.'
      );
      console.error(err);
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    const oldIndex = ulos.findIndex(ulo => ulo.id === active.id);
    const newIndex = ulos.findIndex(ulo => ulo.id === over.id);

    const newUlos = arrayMove(ulos, oldIndex, newIndex);
    setUlos(newUlos);

    try {
      const outcomeIds = newUlos.map(ulo => ulo.id);
      await learningOutcomesApi.reorderULOs(unitId, outcomeIds);
      onULOsChange?.();
    } catch {
      setError('Failed to reorder learning outcomes');
      loadULOs(); // Reload to restore original order
    }
  };

  const getBloomColor = (level: string) => {
    const bloom = bloomLevels.find(b => b.value === level);
    return bloom?.color || 'bg-gray-100 text-gray-700';
  };

  const getCoverageIcon = (ulo: ULOWithMappings) => {
    if (ulo.materialCount > 0 && ulo.assessmentCount > 0) {
      return <CheckCircle className='w-5 h-5 text-green-500' />;
    } else if (ulo.materialCount > 0 || ulo.assessmentCount > 0) {
      return <AlertCircle className='w-5 h-5 text-yellow-500' />;
    } else {
      return <AlertCircle className='w-5 h-5 text-red-500' />;
    }
  };

  const handleEdit = (ulo: ULOWithMappings) => {
    setEditingId(ulo.id);
    setFormData({
      code: ulo.code,
      description: ulo.description,
      bloomLevel: ulo.bloomLevel,
    });
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setFormData({ code: '', description: '', bloomLevel: 'understand' });
  };

  if (loading) {
    return (
      <div className='flex justify-center items-center h-64'>
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600'></div>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Header with Coverage Stats */}
      <div className='bg-white rounded-lg shadow p-6'>
        <div className='flex justify-between items-center mb-4'>
          <h2 className='text-xl font-semibold text-gray-900'>
            Unit Learning Outcomes (ULOs)
          </h2>
          <button
            onClick={() => setIsAddingNew(true)}
            className='inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700'
          >
            <Plus className='w-4 h-4 mr-2' />
            Add ULO
          </button>
        </div>

        {coverage && (
          <div className='grid grid-cols-4 gap-4 mb-6'>
            <div className='bg-gray-50 p-3 rounded'>
              <p className='text-sm text-gray-600'>Total ULOs</p>
              <p className='text-2xl font-bold text-gray-900'>
                {coverage.total_ulos}
              </p>
            </div>
            <div className='bg-green-50 p-3 rounded'>
              <p className='text-sm text-gray-600'>Fully Covered</p>
              <p className='text-2xl font-bold text-green-700'>
                {coverage.fully_covered}
              </p>
              <p className='text-xs text-gray-500'>
                {coverage.full_coverage_percentage.toFixed(0)}%
              </p>
            </div>
            <div className='bg-yellow-50 p-3 rounded'>
              <p className='text-sm text-gray-600'>Materials Only</p>
              <p className='text-2xl font-bold text-yellow-700'>
                {coverage.covered_by_materials}
              </p>
            </div>
            <div className='bg-orange-50 p-3 rounded'>
              <p className='text-sm text-gray-600'>Assessments Only</p>
              <p className='text-2xl font-bold text-orange-700'>
                {coverage.covered_by_assessments}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className='bg-red-50 border border-red-200 rounded-md p-4'>
          <p className='text-red-800'>{error}</p>
        </div>
      )}

      {/* Add New Form */}
      {isAddingNew && (
        <div className='bg-white rounded-lg shadow p-6'>
          <h3 className='text-lg font-medium mb-4'>Add New Learning Outcome</h3>
          <div className='grid grid-cols-12 gap-4'>
            <div className='col-span-2'>
              <input
                type='text'
                placeholder='Code (e.g., ULO1)'
                value={formData.code}
                onChange={e =>
                  setFormData({ ...formData, code: e.target.value })
                }
                className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
              />
            </div>
            <div className='col-span-6'>
              <input
                type='text'
                placeholder='Description'
                value={formData.description}
                onChange={e =>
                  setFormData({ ...formData, description: e.target.value })
                }
                className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
              />
            </div>
            <div className='col-span-2'>
              <select
                value={formData.bloomLevel}
                onChange={e =>
                  setFormData({ ...formData, bloomLevel: e.target.value })
                }
                className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
              >
                {bloomLevels.map(level => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </select>
            </div>
            <div className='col-span-2 flex gap-2'>
              <button
                onClick={handleCreate}
                className='flex-1 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700'
              >
                Save
              </button>
              <button
                onClick={() => {
                  setIsAddingNew(false);
                  setFormData({
                    code: '',
                    description: '',
                    bloomLevel: 'understand',
                  });
                }}
                className='flex-1 px-3 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400'
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ULOs List */}
      <div className='bg-white rounded-lg shadow'>
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={ulos.map(u => u.id)}
            strategy={verticalListSortingStrategy}
          >
            <div className='divide-y divide-gray-200'>
              {ulos.map(ulo => (
                <SortableULOItem
                  key={ulo.id}
                  ulo={ulo}
                  editingId={editingId}
                  formData={formData}
                  bloomLevels={bloomLevels}
                  onEdit={handleEdit}
                  onUpdate={handleUpdate}
                  onDelete={handleDelete}
                  onCancelEdit={handleCancelEdit}
                  onFormChange={setFormData}
                  getBloomColor={getBloomColor}
                  getCoverageIcon={getCoverageIcon}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>

        {ulos.length === 0 && (
          <div className='p-8 text-center text-gray-500'>
            <BookOpen className='w-12 h-12 mx-auto mb-4 text-gray-300' />
            <p>No learning outcomes defined yet.</p>
            <p className='text-sm mt-2'>
              Click &quot;Add ULO&quot; to create your first learning outcome.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ULOManager;
