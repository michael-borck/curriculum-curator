import { useState, useEffect } from 'react';
import { Save, CheckCircle, AlertCircle, Eye, EyeOff } from 'lucide-react';
import toast from 'react-hot-toast';
import {
  getCurtinSettings,
  saveCurtinSettings,
} from '../../services/curtinApi';
import type { CurtinSettings as CurtinSettingsType } from '../../services/curtinApi';

const CurtinSettings = () => {
  const [curtinUsername, setCurtinUsername] = useState('');
  const [curtinPassword, setCurtinPassword] = useState('');
  const [litecUrl, setLitecUrl] = useState('');
  const [blackboardUrl, setBlackboardUrl] = useState('');
  const [campus, setCampus] = useState('');

  const [showPassword, setShowPassword] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCurtinSettings()
      .then(settings => {
        setCurtinUsername(settings.curtinUsername);
        setCurtinPassword(settings.curtinPassword);
        setLitecUrl(settings.litecUrl);
        setBlackboardUrl(settings.blackboardUrl);
        setCampus(settings.campus);
      })
      .catch(() => {
        // Settings may not exist yet — start with empty defaults
      });
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const settings: CurtinSettingsType = {
        curtinUsername,
        curtinPassword,
        litecUrl,
        blackboardUrl,
        campus,
      };
      await saveCurtinSettings(settings);
      setSaved(true);
      toast.success('Curtin settings saved');
      window.setTimeout(() => setSaved(false), 3000);
    } catch (e: unknown) {
      const msg =
        e instanceof Error ? e.message : 'Failed to save Curtin settings';
      setError(msg);
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className='bg-white rounded-lg shadow-md p-6'>
      <h2 className='text-xl font-semibold mb-2'>Curtin Settings</h2>
      <p className='text-sm text-gray-600 mb-6'>
        Configure your Curtin University credentials and system URLs for
        integration with LITEC and Blackboard.
      </p>

      {error && (
        <div className='mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2'>
          <AlertCircle className='w-5 h-5 text-red-600 mt-0.5 flex-shrink-0' />
          <span className='text-sm text-red-800'>{error}</span>
        </div>
      )}

      <div className='space-y-6'>
        {/* Credentials */}
        <div>
          <h3 className='font-medium mb-3'>Curtin Credentials</h3>
          <div className='space-y-4'>
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Curtin Username
              </label>
              <input
                type='text'
                value={curtinUsername}
                onChange={e => setCurtinUsername(e.target.value)}
                className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                placeholder='e.g. jsmith'
              />
            </div>

            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Curtin Password
              </label>
              <div className='relative'>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={curtinPassword}
                  onChange={e => setCurtinPassword(e.target.value)}
                  className='w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                  placeholder='Your Curtin password'
                />
                <button
                  type='button'
                  onClick={() => setShowPassword(prev => !prev)}
                  className='absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600'
                >
                  {showPassword ? (
                    <EyeOff className='w-4 h-4' />
                  ) : (
                    <Eye className='w-4 h-4' />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* System URLs */}
        <div>
          <h3 className='font-medium mb-3'>System URLs</h3>
          <div className='space-y-4'>
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                LITEC URL
              </label>
              <input
                type='text'
                value={litecUrl}
                onChange={e => setLitecUrl(e.target.value)}
                className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                placeholder='https://litec.curtin.edu.au'
              />
            </div>

            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Blackboard URL
              </label>
              <input
                type='text'
                value={blackboardUrl}
                onChange={e => setBlackboardUrl(e.target.value)}
                className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                placeholder='https://lms.curtin.edu.au'
              />
            </div>
          </div>
        </div>

        {/* Campus */}
        <div>
          <h3 className='font-medium mb-3'>Campus</h3>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              Campus
            </label>
            <input
              type='text'
              value={campus}
              onChange={e => setCampus(e.target.value)}
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
              placeholder='e.g. Bentley'
            />
          </div>
        </div>
      </div>

      <div className='mt-6 flex justify-end'>
        <button
          onClick={handleSave}
          disabled={saving}
          className='px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center'
        >
          {saved ? (
            <>
              <CheckCircle className='h-4 w-4 mr-2' />
              Saved
            </>
          ) : (
            <>
              <Save className='h-4 w-4 mr-2' />
              {saving ? 'Saving...' : 'Save Curtin Settings'}
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default CurtinSettings;
