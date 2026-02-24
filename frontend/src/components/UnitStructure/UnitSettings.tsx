import { useState } from 'react';
import { updateUnit } from '../../services/api';
import { FormInput, FormSelect, FormTextarea, Button } from '../ui';
import toast from 'react-hot-toast';
import type {
  Unit,
  UnitFeatures,
  QualityMetricVisibility,
  UDLMetricVisibility,
} from '../../types';

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

const targetLevelOptions = [
  { value: 'elementary', label: 'Elementary' },
  { value: 'middle_school', label: 'Middle School' },
  { value: 'high_school', label: 'High School' },
  { value: 'university', label: 'University' },
  { value: 'postgraduate', label: 'Postgraduate' },
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
  const [customFrameworks, setCustomFrameworks] = useState(
    existingFeatures.customFrameworks ?? true
  );

  // Quality metric visibility
  const existingQualityMetrics = existingFeatures.qualityMetrics ?? {};
  const [qCompleteness, setQCompleteness] = useState(
    existingQualityMetrics.completeness ?? true
  );
  const [qContentQuality, setQContentQuality] = useState(
    existingQualityMetrics.contentQuality ?? true
  );
  const [qUloAlignment, setQUloAlignment] = useState(
    existingQualityMetrics.uloAlignment ?? true
  );
  const [qWorkloadBalance, setQWorkloadBalance] = useState(
    existingQualityMetrics.workloadBalance ?? true
  );
  const [qMaterialDiversity, setQMaterialDiversity] = useState(
    existingQualityMetrics.materialDiversity ?? true
  );
  const [qAssessmentDistribution, setQAssessmentDistribution] = useState(
    existingQualityMetrics.assessmentDistribution ?? true
  );

  // UDL metric visibility
  const existingUdlMetrics = existingFeatures.udlMetrics ?? {};
  const [udlRepresentation, setUdlRepresentation] = useState(
    existingUdlMetrics.representation ?? true
  );
  const [udlEngagement, setUdlEngagement] = useState(
    existingUdlMetrics.engagement ?? true
  );
  const [udlExpression, setUdlExpression] = useState(
    existingUdlMetrics.expression ?? true
  );
  const [udlAccessibility, setUdlAccessibility] = useState(
    existingUdlMetrics.accessibility ?? true
  );

  // Target audience level for readability scoring
  const existingTargetLevel =
    (unit.unitMetadata?.targetAudienceLevel as string | undefined) ??
    'university';
  const [targetLevel, setTargetLevel] = useState(existingTargetLevel);

  const handleSave = async () => {
    setSaving(true);
    try {
      const qualityMetrics: QualityMetricVisibility = {
        completeness: qCompleteness,
        contentQuality: qContentQuality,
        uloAlignment: qUloAlignment,
        workloadBalance: qWorkloadBalance,
        materialDiversity: qMaterialDiversity,
        assessmentDistribution: qAssessmentDistribution,
      };

      const udlMetrics: UDLMetricVisibility = {
        representation: udlRepresentation,
        engagement: udlEngagement,
        expression: udlExpression,
        accessibility: udlAccessibility,
      };

      const features: UnitFeatures = {
        graduateCapabilities: gradCaps,
        aolMapping: aolMapping,
        sdgMapping: sdgMapping,
        customFrameworks: customFrameworks,
        qualityMetrics,
        udlMetrics,
      };

      // Merge features into existing unitMetadata to preserve other keys
      const mergedMetadata = {
        ...(unit.unitMetadata ?? {}),
        features,
        targetAudienceLevel: targetLevel,
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

      {/* Alignment & Accreditation */}
      <div className='mb-8'>
        <h3 className='text-lg font-semibold text-gray-900 mb-1'>
          Alignment & Accreditation
        </h3>
        <p className='text-sm text-gray-500 mb-4'>
          Toggle which alignment and accreditation panels appear on the Outcomes
          tab. Disable panels not relevant for this unit.
        </p>
        <div className='divide-y divide-gray-100'>
          <ToggleSwitch
            label='Custom Alignment Frameworks'
            description='Create custom frameworks (PLOs, GRIT, ethics, etc.) and map ULOs to them'
            checked={customFrameworks}
            onChange={setCustomFrameworks}
          />
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

      {/* Quality & UDL Metrics */}
      <div className='mb-8'>
        <h3 className='text-lg font-semibold text-gray-900 mb-1'>
          Quality & UDL Metrics
        </h3>
        <p className='text-sm text-gray-500 mb-4'>
          Choose which quality and UDL dimensions are visible on the Quality
          tab. Hidden metrics are still calculated but not displayed.
        </p>

        {/* Structural Quality */}
        <h4 className='text-sm font-semibold text-gray-700 mb-2 mt-4'>
          Structural Quality Dimensions
        </h4>
        <div className='divide-y divide-gray-100'>
          <ToggleSwitch
            label='Completeness'
            description='Week coverage and material descriptions'
            checked={qCompleteness}
            onChange={setQCompleteness}
          />
          <ToggleSwitch
            label='Content Quality'
            description='Average plugin quality score across materials'
            checked={qContentQuality}
            onChange={setQContentQuality}
          />
          <ToggleSwitch
            label='ULO Alignment'
            description='How well materials and assessments cover learning outcomes'
            checked={qUloAlignment}
            onChange={setQUloAlignment}
          />
          <ToggleSwitch
            label='Workload Balance'
            description='Evenness of weekly workload distribution'
            checked={qWorkloadBalance}
            onChange={setQWorkloadBalance}
          />
          <ToggleSwitch
            label='Material Diversity'
            description='Variety of session formats used'
            checked={qMaterialDiversity}
            onChange={setQMaterialDiversity}
          />
          <ToggleSwitch
            label='Assessment Distribution'
            description='Spread of assessments across the semester'
            checked={qAssessmentDistribution}
            onChange={setQAssessmentDistribution}
          />
        </div>

        {/* UDL Inclusivity */}
        <h4 className='text-sm font-semibold text-gray-700 mb-2 mt-6'>
          UDL Inclusivity Dimensions
        </h4>
        <div className='divide-y divide-gray-100'>
          <ToggleSwitch
            label='Representation'
            description='Multiple means of representation (content categories, format variety)'
            checked={udlRepresentation}
            onChange={setUdlRepresentation}
          />
          <ToggleSwitch
            label='Engagement'
            description='Multiple means of engagement (interactive vs passive activities)'
            checked={udlEngagement}
            onChange={setUdlEngagement}
          />
          <ToggleSwitch
            label='Action & Expression'
            description='Multiple means of action and expression (assessment diversity)'
            checked={udlExpression}
            onChange={setUdlExpression}
          />
          <ToggleSwitch
            label='Accessibility'
            description='Readability and WCAG compliance of content'
            checked={udlAccessibility}
            onChange={setUdlAccessibility}
          />
        </div>

        {/* Target Audience Level */}
        <div className='mt-6'>
          <FormSelect
            label='Target Audience Level'
            options={targetLevelOptions}
            value={targetLevel}
            onChange={e => setTargetLevel(e.target.value)}
            hint='Contextualises readability scoring for the intended audience'
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
