import { useEffect, useState } from 'react';
import { Monitor, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

const DesktopSettings = () => {
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    window.api
      ?.getAutoUpdate?.()
      .then(value => setEnabled(value))
      .catch(() => undefined)
      .finally(() => setLoading(false));
  }, []);

  const toggle = async (next: boolean) => {
    setEnabled(next);
    try {
      await window.api?.setAutoUpdate?.(next);
      toast.success(
        next
          ? 'Automatic update checks enabled'
          : 'Automatic update checks disabled'
      );
    } catch {
      setEnabled(!next);
      toast.error('Could not save this preference');
    }
  };

  const checkNow = async () => {
    setChecking(true);
    try {
      await window.api?.checkForUpdates?.();
      toast.success('Checked for updates');
    } catch {
      toast.error('Update check failed');
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className='bg-white rounded-lg shadow-md p-6 space-y-4'>
      <div className='flex items-center gap-2'>
        <Monitor className='w-5 h-5 text-purple-600' />
        <h2 className='text-xl font-semibold'>Desktop App</h2>
      </div>

      <label className='flex items-start gap-3 cursor-pointer'>
        <input
          type='checkbox'
          checked={enabled}
          disabled={loading}
          onChange={e => void toggle(e.target.checked)}
          className='mt-1'
        />
        <span>
          <span className='block text-sm font-medium text-gray-800'>
            Check for updates automatically
          </span>
          <span className='block text-sm text-gray-500'>
            When enabled, the app asks GitHub for a new release shortly after
            launch. Turn this off to avoid that request; you can still check
            manually below.
          </span>
        </span>
      </label>

      <button
        type='button'
        onClick={() => void checkNow()}
        disabled={checking}
        className='inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50'
      >
        <RefreshCw className={`w-4 h-4 ${checking ? 'animate-spin' : ''}`} />
        Check now
      </button>
    </div>
  );
};

export default DesktopSettings;
