import { useState } from 'react';
import { Save, CheckCircle } from 'lucide-react';
import api from '../../services/api';
import { useAuthStore } from '../../stores/authStore';
import toast from 'react-hot-toast';

type RatingMethod = 'weighted_average' | 'lowest_dimension' | 'threshold_based';

const methodDescriptions: Record<RatingMethod, string> = {
  weighted_average:
    'Star rating is calculated as a weighted average across all 6 quality dimensions. Best for a balanced overall view.',
  lowest_dimension:
    'Star rating is determined by your weakest dimension. Encourages addressing all areas before the rating improves.',
  threshold_based:
    'Each star requires all dimensions to meet a minimum threshold. Stars are earned progressively.',
};

const QualityRatingSettings = () => {
  const { user } = useAuthStore();
  const prefs = (user?.teachingPreferences ?? {}) as Record<string, unknown>;
  const existing = (prefs.qualityRating ?? {}) as Record<string, unknown>;

  const [method, setMethod] = useState<RatingMethod>(
    (existing.method as RatingMethod) || 'weighted_average'
  );
  const [thresholds, setThresholds] = useState<number[]>(
    (existing.thresholds as number[]) || [20, 40, 60, 80, 90]
  );
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    try {
      setSaving(true);
      const qualityRating: Record<string, unknown> = { method };
      if (method === 'threshold_based') {
        qualityRating.thresholds = thresholds;
      }
      await api.patch('/auth/profile', {
        teachingPreferences: { ...prefs, qualityRating },
      });
      setSaved(true);
      toast.success('Quality rating settings saved');
      window.setTimeout(() => setSaved(false), 3000);
    } catch {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className='bg-white rounded-lg shadow-md p-6'>
      <h2 className='text-xl font-semibold mb-2'>Quality Rating Method</h2>
      <p className='text-sm text-gray-600 mb-6'>
        Choose how the star rating for your units is calculated.
      </p>

      <div className='space-y-4'>
        {(
          [
            { value: 'weighted_average', label: 'Weighted Average' },
            { value: 'lowest_dimension', label: 'Lowest Dimension' },
            { value: 'threshold_based', label: 'Threshold-Based' },
          ] as const
        ).map(option => (
          <label
            key={option.value}
            className={`flex items-start gap-3 p-4 border rounded-lg cursor-pointer transition ${
              method === option.value
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-200 hover:bg-gray-50'
            }`}
          >
            <input
              type='radio'
              name='ratingMethod'
              value={option.value}
              checked={method === option.value}
              onChange={() => setMethod(option.value)}
              className='mt-1'
            />
            <div>
              <span className='font-medium text-gray-900'>{option.label}</span>
              <p className='text-sm text-gray-600 mt-0.5'>
                {methodDescriptions[option.value]}
              </p>
            </div>
          </label>
        ))}
      </div>

      {/* Threshold sliders */}
      {method === 'threshold_based' && (
        <div className='mt-6 p-4 bg-gray-50 rounded-lg'>
          <h3 className='font-medium text-gray-800 mb-3'>Star Thresholds</h3>
          <p className='text-sm text-gray-500 mb-4'>
            Set the minimum score all dimensions must reach to earn each star.
          </p>
          <div className='space-y-3'>
            {thresholds.map((threshold, idx) => (
              <div key={idx} className='flex items-center gap-3'>
                <span className='text-sm font-medium text-gray-700 w-16'>
                  {idx + 1} star{idx > 0 ? 's' : ''}
                </span>
                <input
                  type='range'
                  min={0}
                  max={100}
                  value={threshold}
                  onChange={e => {
                    const next = [...thresholds];
                    next[idx] = parseInt(e.target.value);
                    setThresholds(next);
                  }}
                  className='flex-1'
                />
                <span className='text-sm text-gray-600 w-10 text-right'>
                  {threshold}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className='mt-6 flex justify-end'>
        <button
          onClick={handleSave}
          disabled={saving}
          className='px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center'
        >
          {saved ? (
            <>
              <CheckCircle className='h-4 w-4 mr-2' />
              Saved
            </>
          ) : (
            <>
              <Save className='h-4 w-4 mr-2' />
              {saving ? 'Saving...' : 'Save Settings'}
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default QualityRatingSettings;
