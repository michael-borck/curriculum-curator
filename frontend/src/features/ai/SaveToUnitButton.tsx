import { useState } from 'react';
import { Save, Plus, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { quickCreateUnit } from '../../services/api';
import { contentApi } from '../../services/contentApi';
import { useUnitsStore } from '../../stores/unitsStore';
import { useWorkingContextStore } from '../../stores/workingContextStore';
import { useModal } from '../../hooks/useModal';
import { Modal } from '../../components/ui/Modal';
import type { ContentType } from '../../types/index';

interface SaveToUnitButtonProps {
  messageContent: string;
  unitId?: string | undefined;
  unitTitle?: string | undefined;
}

const CONTENT_TYPE_OPTIONS: { value: ContentType; label: string }[] = [
  { value: 'notes', label: 'Notes' },
  { value: 'slides', label: 'Slides' },
  { value: 'activity', label: 'Activity' },
  { value: 'worksheet', label: 'Worksheet' },
  { value: 'quiz', label: 'Quiz' },
  { value: 'resource', label: 'Resource' },
  { value: 'handout', label: 'Handout' },
  { value: 'reading', label: 'Reading' },
];

function extractTitle(content: string): string {
  // Try first markdown heading
  const headingMatch = content.match(/^#{1,6}\s+(.+)$/m);
  if (headingMatch) {
    return headingMatch[1].trim().slice(0, 80);
  }

  // Fall back to first ~60 chars, truncated at word boundary
  const firstLine = content.split('\n').find(l => l.trim().length > 0) ?? '';
  const plain = firstLine.replace(/[#*_`[\]]/g, '').trim();
  if (plain.length <= 60) return plain || 'Untitled';
  const truncated = plain.slice(0, 60);
  const lastSpace = truncated.lastIndexOf(' ');
  return (lastSpace > 20 ? truncated.slice(0, lastSpace) : truncated) + '...';
}

const SaveToUnitButton = ({
  messageContent,
  unitId,
  unitTitle,
}: SaveToUnitButtonProps) => {
  const ctx = useWorkingContextStore();
  const effectiveUnitId = unitId ?? ctx.activeUnitId ?? undefined;
  const effectiveUnitTitle = unitTitle ?? ctx.activeUnitTitle ?? undefined;

  const [contentType, setContentType] = useState<ContentType>('notes');
  const [saving, setSaving] = useState(false);
  const [selectedUnitId, setSelectedUnitId] = useState('');
  const [quickCreateTitle, setQuickCreateTitle] = useState('');
  const [creatingUnit, setCreatingUnit] = useState(false);
  const modal = useModal();
  const { units, fetchUnits } = useUnitsStore();

  const saveToUnit = async (targetUnitId: string) => {
    setSaving(true);
    try {
      const title = extractTitle(messageContent);
      await contentApi.create(targetUnitId, {
        title,
        contentType,
        body: messageContent,
      });
      toast.success('Content saved');
      modal.close();
    } catch {
      toast.error('Failed to save content');
    } finally {
      setSaving(false);
    }
  };

  const handleClick = async () => {
    if (effectiveUnitId) {
      await saveToUnit(effectiveUnitId);
    } else {
      await fetchUnits();
      modal.open();
    }
  };

  const handleQuickCreate = async () => {
    if (!quickCreateTitle.trim()) return;
    setCreatingUnit(true);
    try {
      const response = await quickCreateUnit({
        contentType,
        title: quickCreateTitle.trim(),
      });
      const newUnitId = response.data.unitId;
      await fetchUnits();
      await saveToUnit(newUnitId);
    } catch {
      toast.error('Failed to create learning program');
    } finally {
      setCreatingUnit(false);
    }
  };

  return (
    <>
      <div className='flex items-center gap-2 mt-1'>
        <button
          onClick={handleClick}
          disabled={saving}
          className='flex items-center gap-1 px-2 py-1 text-xs text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors disabled:opacity-50'
        >
          {saving ? (
            <Loader2 className='h-3 w-3 animate-spin' />
          ) : (
            <Save className='h-3 w-3' />
          )}
          Save to{' '}
          {effectiveUnitTitle ?? (ctx.activeUnitLabel || 'Learning Program')}
        </button>
        <select
          value={contentType}
          onChange={e => setContentType(e.target.value as ContentType)}
          className='text-xs border border-gray-200 rounded px-1 py-0.5 text-gray-500 bg-transparent hover:border-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500'
        >
          {CONTENT_TYPE_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <Modal
        isOpen={modal.isOpen}
        onClose={modal.close}
        title={`Save to ${ctx.activeUnitLabel || 'Learning Program'}`}
        size='sm'
      >
        <div className='space-y-4'>
          {/* Select existing unit */}
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              Select a learning program
            </label>
            <select
              value={selectedUnitId}
              onChange={e => setSelectedUnitId(e.target.value)}
              className='w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            >
              <option value=''>Choose...</option>
              {units.map(unit => (
                <option key={unit.id} value={unit.id}>
                  {unit.code ? `${unit.code} - ` : ''}
                  {unit.title}
                </option>
              ))}
            </select>
            <button
              onClick={() => saveToUnit(selectedUnitId)}
              disabled={!selectedUnitId || saving}
              className='mt-2 w-full px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2'
            >
              {saving ? (
                <Loader2 className='h-4 w-4 animate-spin' />
              ) : (
                <Save className='h-4 w-4' />
              )}
              Save
            </button>
          </div>

          <div className='relative'>
            <div className='absolute inset-0 flex items-center'>
              <div className='w-full border-t border-gray-200' />
            </div>
            <div className='relative flex justify-center text-xs'>
              <span className='bg-white px-2 text-gray-400'>or</span>
            </div>
          </div>

          {/* Quick create new unit */}
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              Quick-create a new learning program
            </label>
            <input
              type='text'
              value={quickCreateTitle}
              onChange={e => setQuickCreateTitle(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleQuickCreate()}
              placeholder='Title...'
              className='w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            />
            <button
              onClick={handleQuickCreate}
              disabled={!quickCreateTitle.trim() || creatingUnit}
              className='mt-2 w-full px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2'
            >
              {creatingUnit ? (
                <Loader2 className='h-4 w-4 animate-spin' />
              ) : (
                <Plus className='h-4 w-4' />
              )}
              Create & Save
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
};

export default SaveToUnitButton;
