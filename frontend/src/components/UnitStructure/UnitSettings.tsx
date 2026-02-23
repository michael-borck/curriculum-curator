import { useState } from 'react';
import { updateUnit } from '../../services/api';
import { FormInput, FormSelect, FormTextarea, Button } from '../ui';
import toast from 'react-hot-toast';
import type { Unit, UnitFeatures } from '../../types';

interface UnitSettingsProps {
  unit: Unit;
  onSave: (updated: Unit) => void;
}

const semesterOptions = [
  { value: 'semester_1', label: 'Semester 1 (Feb-Jun)' },
  { value: 'semester_2', label: 'Semester 2 (Jul-Nov)' },
  { value: 'summer', label: 'Summer (Nov-Feb)' },
  { value: 'winter', label: 'Winter (Jun-Jul)' },
];

interface ToggleSwitchProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

const ToggleSwitch: React.FC<ToggleSwitchProps> = ({
  label,
  description,
  checked,
  onChange,
}) => (
  <div className='flex items-center justify-between py-3'>
    <div>
      <p className='text-sm font-medium text-gray-900'>{label}</p>
      <p className='text-sm text-gray-500'>{description}</p>
    </div>
    <button
      type='button'
      role='switch'
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`
        relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full
        border-2 border-transparent transition-colors duration-200 ease-in-out
        focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2
        ${checked ? 'bg-purple-600' : 'bg-gray-200'}
      `}
    >
      <span
        className={`
          pointer-events-none inline-block h-5 w-5 rounded-full bg-white
          shadow ring-0 transition duration-200 ease-in-out
          ${checked ? 'translate-x-5' : 'translate-x-0'}
        `}
      />
    </button>
  </div>
);

const UnitSettings: React.FC<UnitSettingsProps> = ({ unit, onSave }) => {
  const [year, setYear] = useState(unit.year);
  const [semester, setSemester] = useState(unit.semester);
  const [creditPoints, setCreditPoints] = useState(unit.creditPoints);
  const [learningHours, setLearningHours] = useState(unit.learningHours ?? 0);
  const [prerequisites, setPrerequisites] = useState(unit.prerequisites ?? '');
  const [saving, setSaving] = useState(false);

  const existingFeatures = unit.unitMetadata?.features ?? {};
  const [gradCaps, setGradCaps] = useState(
    existingFeatures.graduateCapabilities ?? true
  );
  const [aolMapping, setAolMapping] = useState(
    existingFeatures.aolMapping ?? true
  );
  const [sdgMapping, setSdgMapping] = useState(
    existingFeatures.sdgMapping ?? true
  );

  const handleSave = async () => {
    setSaving(true);
    try {
      const features: UnitFeatures = {
        graduateCapabilities: gradCaps,
        aolMapping: aolMapping,
        sdgMapping: sdgMapping,
      };

      // Merge features into existing unitMetadata to preserve other keys
      const mergedMetadata = {
        ...(unit.unitMetadata ?? {}),
        features,
      };

      const payload: Partial<Unit> = {
        year,
        semester,
        creditPoints,
        unitMetadata: mergedMetadata,
      };
      if (learningHours) payload.learningHours = learningHours;
      if (prerequisites) payload.prerequisites = prerequisites;

      const response = await updateUnit(unit.id, payload);
      toast.success('Settings saved');
      onSave(response.data);
    } catch {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className='max-w-2xl'>
      {/* Academic Details */}
      <div className='mb-8'>
        <h3 className='text-lg font-semibold text-gray-900 mb-4'>
          Academic Details
        </h3>
        <div className='space-y-4'>
          <div className='grid grid-cols-2 gap-4'>
            <FormInput
              label='Year'
              type='number'
              min={2020}
              max={2100}
              value={year}
              onChange={e => setYear(parseInt(e.target.value, 10))}
            />
            <FormSelect
              label='Semester'
              options={semesterOptions}
              value={semester}
              onChange={e => setSemester(e.target.value)}
            />
          </div>
          <div className='grid grid-cols-2 gap-4'>
            <FormInput
              label='Credit Points'
              type='number'
              min={0}
              max={500}
              value={creditPoints}
              onChange={e => setCreditPoints(parseInt(e.target.value, 10))}
            />
            <FormInput
              label='Learning Hours'
              type='number'
              min={0}
              max={10000}
              value={learningHours}
              onChange={e => setLearningHours(parseInt(e.target.value, 10))}
              hint='Total expected student learning hours'
            />
          </div>
          <FormTextarea
            label='Prerequisites'
            value={prerequisites}
            onChange={e => setPrerequisites(e.target.value)}
            rows={3}
            placeholder='e.g. COMP1001 Introduction to Programming or equivalent'
            hint='List any prerequisite units or assumed knowledge'
          />
        </div>
      </div>

      {/* Accreditation Panels */}
      <div className='mb-8'>
        <h3 className='text-lg font-semibold text-gray-900 mb-1'>
          Accreditation Panels
        </h3>
        <p className='text-sm text-gray-500 mb-4'>
          Toggle which accreditation mapping panels are shown on the Structure
          tab. Disable panels that are not relevant for this unit type.
        </p>
        <div className='divide-y divide-gray-100'>
          <ToggleSwitch
            label='Graduate Capabilities'
            description='Map unit outcomes to institutional graduate capabilities'
            checked={gradCaps}
            onChange={setGradCaps}
          />
          <ToggleSwitch
            label='AoL Mapping'
            description='Assurance of Learning mapping for AACSB/EQUIS accreditation'
            checked={aolMapping}
            onChange={setAolMapping}
          />
          <ToggleSwitch
            label='SDG Mapping'
            description='UN Sustainable Development Goals alignment'
            checked={sdgMapping}
            onChange={setSdgMapping}
          />
        </div>
      </div>

      {/* Save */}
      <Button onClick={handleSave} loading={saving}>
        Save Settings
      </Button>
    </div>
  );
};

export default UnitSettings;
