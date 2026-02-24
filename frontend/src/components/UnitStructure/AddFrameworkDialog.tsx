import { useState } from 'react';
import { X, Plus } from 'lucide-react';
import {
  FRAMEWORK_PRESETS,
  type FrameworkPreset,
} from '../../constants/frameworkPresets';
import { accreditationApi } from '../../services/unitStructureApi';
import type {
  CustomAlignmentFramework,
  FrameworkCreate,
} from '../../types/unitStructure';
import toast from 'react-hot-toast';

interface AddFrameworkDialogProps {
  unitId: string;
  onCreated: (framework: CustomAlignmentFramework) => void;
  onClose: () => void;
}

const COLOR_CLASSES: Record<string, string> = {
  indigo: 'border-indigo-200 hover:border-indigo-400 hover:bg-indigo-50',
  amber: 'border-amber-200 hover:border-amber-400 hover:bg-amber-50',
  emerald: 'border-emerald-200 hover:border-emerald-400 hover:bg-emerald-50',
  orange: 'border-orange-200 hover:border-orange-400 hover:bg-orange-50',
  purple: 'border-purple-200 hover:border-purple-400 hover:bg-purple-50',
  gray: 'border-gray-200 hover:border-gray-400 hover:bg-gray-50',
};

export const AddFrameworkDialog: React.FC<AddFrameworkDialogProps> = ({
  unitId,
  onCreated,
  onClose,
}) => {
  const [selectedPreset, setSelectedPreset] = useState<FrameworkPreset | null>(
    null
  );
  const [customName, setCustomName] = useState('');
  const [creating, setCreating] = useState(false);

  const handleSelectPreset = (preset: FrameworkPreset) => {
    setSelectedPreset(preset);
    setCustomName(preset.name);
  };

  const handleCreate = async () => {
    if (!selectedPreset || !customName.trim()) return;
    setCreating(true);
    try {
      const data: FrameworkCreate = {
        name: customName.trim(),
        description: selectedPreset.description,
        presetType: selectedPreset.type ?? undefined,
        iconHint: selectedPreset.icon,
        colorHint: selectedPreset.color,
        items: selectedPreset.items,
      };

      const created = await accreditationApi.createFramework(unitId, data);
      onCreated(created);
      toast.success(`${created.name} created`);
    } catch {
      toast.error('Failed to create framework');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/50'>
      <div className='bg-white rounded-xl shadow-xl w-full max-w-lg mx-4'>
        {/* Header */}
        <div className='flex items-center justify-between px-6 py-4 border-b border-gray-200'>
          <h2 className='text-lg font-semibold text-gray-900'>
            {selectedPreset ? 'Confirm Framework' : 'Add Alignment Framework'}
          </h2>
          <button
            onClick={onClose}
            className='p-1 text-gray-400 hover:text-gray-600 rounded'
          >
            <X className='w-5 h-5' />
          </button>
        </div>

        <div className='p-6'>
          {!selectedPreset ? (
            /* Preset Grid */
            <div className='grid grid-cols-2 gap-3'>
              {FRAMEWORK_PRESETS.map(preset => (
                <button
                  key={preset.id}
                  onClick={() => handleSelectPreset(preset)}
                  className={`text-left p-4 rounded-lg border-2 transition ${COLOR_CLASSES[preset.color] ?? COLOR_CLASSES.gray}`}
                >
                  <div className='text-2xl mb-2'>{preset.icon}</div>
                  <h3 className='font-medium text-gray-900 text-sm'>
                    {preset.name}
                  </h3>
                  <p className='text-xs text-gray-500 mt-1'>
                    {preset.description}
                  </p>
                  {preset.items.length > 0 && (
                    <p className='text-xs text-gray-400 mt-2'>
                      {preset.items.length} pre-filled items
                    </p>
                  )}
                </button>
              ))}
            </div>
          ) : (
            /* Confirm Step */
            <div className='space-y-4'>
              <div className='flex items-center gap-3 p-3 bg-gray-50 rounded-lg'>
                <span className='text-2xl'>{selectedPreset.icon}</span>
                <div>
                  <p className='text-sm font-medium text-gray-900'>
                    {selectedPreset.name}
                  </p>
                  <p className='text-xs text-gray-500'>{selectedPreset.hint}</p>
                </div>
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Framework Name
                </label>
                <input
                  type='text'
                  value={customName}
                  onChange={e => setCustomName(e.target.value)}
                  className='w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500'
                  placeholder='Enter a name for this framework'
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleCreate();
                  }}
                />
              </div>

              {selectedPreset.items.length > 0 && (
                <div>
                  <p className='text-sm font-medium text-gray-700 mb-2'>
                    Pre-filled Items
                  </p>
                  <div className='space-y-1'>
                    {selectedPreset.items.map((item, i) => (
                      <div
                        key={i}
                        className='flex items-center gap-2 text-sm text-gray-600'
                      >
                        <span className='font-bold text-gray-800'>
                          {item.code}
                        </span>
                        <span>{item.description}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className='flex items-center gap-3 pt-2'>
                <button
                  onClick={() => setSelectedPreset(null)}
                  className='px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition'
                >
                  Back
                </button>
                <button
                  onClick={handleCreate}
                  disabled={!customName.trim() || creating}
                  className='flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition disabled:opacity-50'
                >
                  <Plus className='w-4 h-4' />
                  {creating ? 'Creating...' : 'Create Framework'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AddFrameworkDialog;
