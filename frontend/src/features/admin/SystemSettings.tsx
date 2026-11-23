import { useEffect, useState } from 'react';
import { Save, AlertCircle, CheckCircle, Loader2, Shield } from 'lucide-react';
import api from '../../services/api';

interface SystemSettingsData {
  passwordMinLength: number;
  passwordRequireUppercase: boolean;
  passwordRequireLowercase: boolean;
  passwordRequireNumbers: boolean;
  passwordRequireSpecial: boolean;
  maxLoginAttempts: number;
  lockoutDurationMinutes: number;
  sessionTimeoutMinutes: number;
  enableUserRegistration: boolean;
  enableEmailWhitelist: boolean;
  requireAdminTotp: boolean;
}

const DEFAULTS: SystemSettingsData = {
  passwordMinLength: 8,
  passwordRequireUppercase: true,
  passwordRequireLowercase: true,
  passwordRequireNumbers: true,
  passwordRequireSpecial: true,
  maxLoginAttempts: 5,
  lockoutDurationMinutes: 15,
  sessionTimeoutMinutes: 30,
  enableUserRegistration: true,
  enableEmailWhitelist: true,
  requireAdminTotp: false,
};

const SystemSettings = () => {
  const [settings, setSettings] = useState<SystemSettingsData>(DEFAULTS);
  const [original, setOriginal] = useState<SystemSettingsData>(DEFAULTS);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    api
      .get<SystemSettingsData>('/admin/settings')
      .then(res => {
        setSettings({ ...DEFAULTS, ...res.data });
        setOriginal({ ...DEFAULTS, ...res.data });
        setError('');
      })
      .catch(() => setError('Failed to load settings'))
      .finally(() => setIsLoading(false));
  }, []);

  const update = <K extends keyof SystemSettingsData>(
    key: K,
    value: SystemSettingsData[K]
  ) => setSettings(prev => ({ ...prev, [key]: value }));

  const save = async () => {
    setIsSaving(true);
    setError('');
    try {
      const res = await api.put<SystemSettingsData>(
        '/admin/settings',
        settings
      );
      setSettings({ ...DEFAULTS, ...res.data });
      setOriginal({ ...DEFAULTS, ...res.data });
      setSuccess('Settings saved');
      window.setTimeout(() => setSuccess(''), 3000);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail;
      setError(detail || 'Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const dirty = JSON.stringify(settings) !== JSON.stringify(original);

  if (isLoading) {
    return (
      <div className='flex items-center justify-center py-16 text-gray-500 gap-2'>
        <Loader2 className='w-5 h-5 animate-spin' /> Loading settings…
      </div>
    );
  }

  return (
    <div className='space-y-6 max-w-3xl'>
      <div>
        <h2 className='text-xl font-semibold text-gray-900'>System Settings</h2>
        <p className='text-sm text-gray-600 mt-1'>
          Security policy for this deployment. Changes apply to new requests
          immediately.
        </p>
      </div>

      {error && (
        <div className='flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800'>
          <AlertCircle className='w-4 h-4 mt-0.5 flex-shrink-0' />
          {error}
        </div>
      )}
      {success && (
        <div className='flex items-start gap-2 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-800'>
          <CheckCircle className='w-4 h-4 mt-0.5 flex-shrink-0' />
          {success}
        </div>
      )}

      <section className='bg-white rounded-lg border border-gray-200 p-5 space-y-4'>
        <h3 className='font-medium flex items-center gap-2'>
          <Shield className='w-4 h-4 text-purple-600' /> Access
        </h3>
        <Toggle
          label='Allow user registration'
          description='If off, only administrators can create accounts.'
          checked={settings.enableUserRegistration}
          onChange={v => update('enableUserRegistration', v)}
        />
        <Toggle
          label='Restrict registration to the email whitelist'
          description='Requires at least one @domain pattern; an empty list blocks new sign-ups.'
          checked={settings.enableEmailWhitelist}
          onChange={v => update('enableEmailWhitelist', v)}
        />
        <Toggle
          label='Require two-factor for administrators'
          description='Admins must enable TOTP or add a passkey before using admin tools.'
          checked={settings.requireAdminTotp}
          onChange={v => update('requireAdminTotp', v)}
        />
      </section>

      <section className='bg-white rounded-lg border border-gray-200 p-5 space-y-4'>
        <h3 className='font-medium'>Sessions and lockout</h3>
        <NumberField
          label='Session timeout (minutes)'
          value={settings.sessionTimeoutMinutes}
          min={15}
          max={1440}
          onChange={v => update('sessionTimeoutMinutes', v)}
        />
        <NumberField
          label='Failed attempts before lockout'
          value={settings.maxLoginAttempts}
          min={3}
          max={10}
          onChange={v => update('maxLoginAttempts', v)}
        />
        <NumberField
          label='Lockout duration (minutes)'
          value={settings.lockoutDurationMinutes}
          min={5}
          max={60}
          onChange={v => update('lockoutDurationMinutes', v)}
        />
      </section>

      <section className='bg-white rounded-lg border border-gray-200 p-5 space-y-4'>
        <h3 className='font-medium'>Password policy</h3>
        <NumberField
          label='Minimum length'
          value={settings.passwordMinLength}
          min={6}
          max={32}
          onChange={v => update('passwordMinLength', v)}
        />
        <Toggle
          label='Require an uppercase letter'
          checked={settings.passwordRequireUppercase}
          onChange={v => update('passwordRequireUppercase', v)}
        />
        <Toggle
          label='Require a lowercase letter'
          checked={settings.passwordRequireLowercase}
          onChange={v => update('passwordRequireLowercase', v)}
        />
        <Toggle
          label='Require a number'
          checked={settings.passwordRequireNumbers}
          onChange={v => update('passwordRequireNumbers', v)}
        />
        <Toggle
          label='Require a special character'
          checked={settings.passwordRequireSpecial}
          onChange={v => update('passwordRequireSpecial', v)}
        />
      </section>

      <div className='flex justify-end gap-3'>
        <button
          type='button'
          onClick={() => setSettings(original)}
          disabled={!dirty || isSaving}
          className='px-4 py-2 text-sm rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50'
        >
          Reset
        </button>
        <button
          type='button'
          onClick={() => void save()}
          disabled={!dirty || isSaving}
          className='inline-flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50'
        >
          {isSaving ? (
            <Loader2 className='w-4 h-4 animate-spin' />
          ) : (
            <Save className='w-4 h-4' />
          )}
          Save settings
        </button>
      </div>
    </div>
  );
};

function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className='flex items-start justify-between gap-4 cursor-pointer'>
      <span>
        <span className='block text-sm font-medium text-gray-700'>{label}</span>
        {description && (
          <span className='block text-xs text-gray-500'>{description}</span>
        )}
      </span>
      <input
        type='checkbox'
        checked={checked}
        onChange={e => onChange(e.target.checked)}
        className='mt-1 h-4 w-4'
      />
    </label>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className='flex items-center justify-between gap-4'>
      <span className='text-sm text-gray-700'>{label}</span>
      <input
        type='number'
        value={value}
        min={min}
        max={max}
        onChange={e =>
          onChange(Math.min(max, Math.max(min, Number(e.target.value) || min)))
        }
        className='w-24 px-2 py-1.5 border border-gray-300 rounded-md text-sm'
      />
    </label>
  );
}

export default SystemSettings;
