import { useState, useEffect } from 'react';
import {
  Save,
  AlertCircle,
  CheckCircle,
  Loader2,
  Brain,
  Upload,
  Shield,
  Database,
  Settings2,
} from 'lucide-react';
import api from '../../services/api';
import { llmApi } from '../../services/llmApi';
import type { LLMProvider } from '../../types/llm';

interface SystemSettingsData {
  // AI Features
  enable_ai_features: boolean;
  default_llm_provider: LLMProvider | '';

  // File Upload
  enable_file_upload: boolean;
  max_file_size_mb: number;
  allowed_file_types: string[];

  // Security
  session_timeout_minutes: number;
  max_login_attempts: number;
  password_min_length: number;
  require_email_verification: boolean;

  // Email Whitelist
  enable_whitelist: boolean;

  // Database
  backup_enabled: boolean;
  backup_schedule: 'daily' | 'weekly' | 'monthly';
}

interface ConfiguredProvider {
  provider: LLMProvider;
  name: string;
  configured: boolean;
  hasDefault: boolean;
}

const SystemSettings = () => {
  const [settings, setSettings] = useState<SystemSettingsData>({
    enable_ai_features: true,
    default_llm_provider: '',
    enable_file_upload: true,
    max_file_size_mb: 10,
    allowed_file_types: ['pdf', 'doc', 'docx', 'txt'],
    session_timeout_minutes: 30,
    max_login_attempts: 5,
    password_min_length: 8,
    require_email_verification: true,
    enable_whitelist: true,
    backup_enabled: false,
    backup_schedule: 'daily',
  });

  const [originalSettings, setOriginalSettings] =
    useState<SystemSettingsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const [configuredProviders, setConfiguredProviders] = useState<
    ConfiguredProvider[]
  >([]);

  useEffect(() => {
    fetchSettings();
    fetchConfiguredProviders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (originalSettings) {
      setHasChanges(
        JSON.stringify(settings) !== JSON.stringify(originalSettings)
      );
    }
  }, [settings, originalSettings]);

  const fetchConfiguredProviders = async () => {
    try {
      const configs = await llmApi.getSystemConfigurations();

      // Get unique providers that are configured
      const providerMap = new Map<LLMProvider, boolean>();
      configs.forEach(config => {
        if (config.api_key || config.provider === 'ollama') {
          providerMap.set(
            config.provider as LLMProvider,
            config.is_default || false
          );
        }
      });

      // Create provider list
      const allProviders: ConfiguredProvider[] = [
        {
          provider: 'openai' as LLMProvider,
          name: 'OpenAI',
          configured: false,
          hasDefault: false,
        },
        {
          provider: 'anthropic' as LLMProvider,
          name: 'Anthropic',
          configured: false,
          hasDefault: false,
        },
        {
          provider: 'gemini' as LLMProvider,
          name: 'Google Gemini',
          configured: false,
          hasDefault: false,
        },
        {
          provider: 'ollama' as LLMProvider,
          name: 'Ollama (Local)',
          configured: false,
          hasDefault: false,
        },
      ];

      // Mark configured providers
      allProviders.forEach(p => {
        if (providerMap.has(p.provider)) {
          p.configured = true;
          p.hasDefault = providerMap.get(p.provider) || false;
        }
      });

      setConfiguredProviders(allProviders);

      // Auto-select if only one configured
      const configured = allProviders.filter(p => p.configured);
      if (configured.length === 1 && !settings.default_llm_provider) {
        setSettings(prev => ({
          ...prev,
          default_llm_provider: configured[0].provider,
        }));
      } else if (configured.length > 0 && !settings.default_llm_provider) {
        // Select the one marked as default, or the first configured
        const defaultProvider =
          configured.find(p => p.hasDefault) || configured[0];
        setSettings(prev => ({
          ...prev,
          default_llm_provider: defaultProvider.provider,
        }));
      }
    } catch (error) {
      console.error('Failed to fetch configured providers:', error);
    }
  };

  const fetchSettings = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/api/admin/settings');
      // Merge with defaults to ensure all fields are present
      const mergedSettings = {
        ...settings, // Start with defaults
        ...response.data, // Override with API data
        // Ensure arrays are properly initialized
        allowed_file_types: response.data.allowed_file_types || [
          'pdf',
          'doc',
          'docx',
          'txt',
        ],
      };
      setSettings(mergedSettings);
      setOriginalSettings(mergedSettings);
      setError('');
    } catch (error: any) {
      setError('Failed to load settings');
      console.error('Error fetching settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError('');

    try {
      const response = await api.put('/api/admin/settings', settings);
      setSettings(response.data);
      setOriginalSettings(response.data);
      setSuccess('Settings saved successfully');
      setHasChanges(false);

      window.setTimeout(() => setSuccess(''), 3000);
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Failed to save settings');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (originalSettings) {
      setSettings(originalSettings);
      setHasChanges(false);
    }
  };

  const handleFileTypesChange = (value: string) => {
    const types = value
      .split(',')
      .map(type => type.trim())
      .filter(Boolean);
    setSettings({ ...settings, allowed_file_types: types });
  };

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <Loader2 className='w-8 h-8 animate-spin text-purple-600' />
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      <div className='flex justify-between items-center'>
        <h2 className='text-2xl font-semibold text-gray-900'>
          System Settings
        </h2>
        <div className='flex gap-3'>
          {hasChanges && (
            <button
              onClick={handleReset}
              className='px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors'
            >
              Reset
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
            className='px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2'
          >
            {isSaving ? (
              <>
                <Loader2 className='w-4 h-4 animate-spin' />
                Saving...
              </>
            ) : (
              <>
                <Save className='w-4 h-4' />
                Save Changes
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className='p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2'>
          <AlertCircle className='w-5 h-5 text-red-600 flex-shrink-0 mt-0.5' />
          <p className='text-sm text-red-600'>{error}</p>
        </div>
      )}

      {success && (
        <div className='p-3 bg-green-50 border border-green-200 rounded-md flex items-start gap-2'>
          <CheckCircle className='w-5 h-5 text-green-600 flex-shrink-0 mt-0.5' />
          <p className='text-sm text-green-600'>{success}</p>
        </div>
      )}

      {/* AI Features */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex items-center gap-3 mb-4'>
          <Brain className='w-5 h-5 text-purple-600' />
          <h3 className='text-lg font-semibold text-gray-900'>AI Features</h3>
        </div>

        <div className='space-y-4'>
          <div className='flex items-center justify-between'>
            <div>
              <div className='text-sm font-medium text-gray-700'>
                Enable AI Features
              </div>
              <p className='text-xs text-gray-500'>
                Allow content generation and enhancement
              </p>
            </div>
            <label
              className='relative inline-flex items-center cursor-pointer'
              aria-label='Enable AI Features'
            >
              <input
                type='checkbox'
                checked={settings.enable_ai_features}
                onChange={e =>
                  setSettings({
                    ...settings,
                    enable_ai_features: e.target.checked,
                  })
                }
                className='sr-only peer'
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          <div>
            <div className='flex items-center justify-between mb-1'>
              <label
                htmlFor='llm-provider'
                className='block text-sm font-medium text-gray-700'
              >
                Default LLM Provider
              </label>
              <button
                type='button'
                onClick={e => {
                  e.preventDefault();
                  // Navigate to LLM Configuration tab
                  const event = new CustomEvent('navigate-to-tab', {
                    detail: 'llm',
                  });
                  window.dispatchEvent(event);
                }}
                className='text-xs text-purple-600 hover:text-purple-700 flex items-center gap-1'
              >
                <Settings2 className='w-3 h-3' />
                Configure Providers
              </button>
            </div>
            {configuredProviders.filter(p => p.configured).length === 0 ? (
              <div className='p-3 bg-amber-50 border border-amber-200 rounded-md'>
                <p className='text-sm text-amber-700'>
                  No LLM providers configured. Please configure at least one
                  provider in the LLM Configuration section.
                </p>
              </div>
            ) : (
              <select
                id='llm-provider'
                value={settings.default_llm_provider}
                onChange={e =>
                  setSettings({
                    ...settings,
                    default_llm_provider: e.target.value as LLMProvider,
                  })
                }
                disabled={!settings.enable_ai_features}
                className='w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100'
              >
                <option value=''>Select a provider</option>
                {configuredProviders.map(provider => (
                  <option
                    key={provider.provider}
                    value={provider.provider}
                    disabled={!provider.configured}
                    className={!provider.configured ? 'text-gray-400' : ''}
                  >
                    {provider.name}
                    {provider.configured ? '' : ' (Not Configured)'}
                    {provider.hasDefault ? ' ★' : ''}
                  </option>
                ))}
              </select>
            )}
            {configuredProviders.filter(p => p.configured).length === 1 && (
              <p className='text-xs text-gray-500 mt-1'>
                Auto-selected as the only configured provider
              </p>
            )}
          </div>
        </div>
      </div>

      {/* File Upload */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex items-center gap-3 mb-4'>
          <Upload className='w-5 h-5 text-purple-600' />
          <h3 className='text-lg font-semibold text-gray-900'>File Upload</h3>
        </div>

        <div className='space-y-4'>
          <div className='flex items-center justify-between'>
            <div>
              <div className='text-sm font-medium text-gray-700'>
                Enable File Upload
              </div>
              <p className='text-xs text-gray-500'>
                Allow users to upload documents
              </p>
            </div>
            <label
              className='relative inline-flex items-center cursor-pointer'
              aria-label='Enable File Upload'
            >
              <input
                type='checkbox'
                checked={settings.enable_file_upload}
                onChange={e =>
                  setSettings({
                    ...settings,
                    enable_file_upload: e.target.checked,
                  })
                }
                className='sr-only peer'
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          <div>
            <label
              htmlFor='max-file-size'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Max File Size (MB)
            </label>
            <input
              id='max-file-size'
              type='number'
              value={settings.max_file_size_mb}
              onChange={e =>
                setSettings({
                  ...settings,
                  max_file_size_mb: parseInt(e.target.value) || 0,
                })
              }
              disabled={!settings.enable_file_upload}
              min={1}
              max={100}
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100'
            />
          </div>

          <div>
            <label
              htmlFor='file-types'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Allowed File Types
            </label>
            <input
              id='file-types'
              type='text'
              value={settings.allowed_file_types?.join(', ') || ''}
              onChange={e => handleFileTypesChange(e.target.value)}
              disabled={!settings.enable_file_upload}
              placeholder='pdf, doc, docx, txt'
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100'
            />
            <p className='mt-1 text-xs text-gray-500'>Separate with commas</p>
          </div>
        </div>
      </div>

      {/* Security Settings */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex items-center gap-3 mb-4'>
          <Shield className='w-5 h-5 text-purple-600' />
          <h3 className='text-lg font-semibold text-gray-900'>Security</h3>
        </div>

        <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
          <div>
            <label
              htmlFor='session-timeout'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Session Timeout (minutes)
            </label>
            <input
              id='session-timeout'
              type='number'
              value={settings.session_timeout_minutes}
              onChange={e =>
                setSettings({
                  ...settings,
                  session_timeout_minutes: parseInt(e.target.value) || 0,
                })
              }
              min={5}
              max={1440}
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
            />
          </div>

          <div>
            <label
              htmlFor='max-login'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Max Login Attempts
            </label>
            <input
              id='max-login'
              type='number'
              value={settings.max_login_attempts}
              onChange={e =>
                setSettings({
                  ...settings,
                  max_login_attempts: parseInt(e.target.value) || 0,
                })
              }
              min={3}
              max={10}
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
            />
          </div>

          <div>
            <label
              htmlFor='min-password'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Min Password Length
            </label>
            <input
              id='min-password'
              type='number'
              value={settings.password_min_length}
              onChange={e =>
                setSettings({
                  ...settings,
                  password_min_length: parseInt(e.target.value) || 0,
                })
              }
              min={6}
              max={20}
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500'
            />
          </div>

          <div className='flex items-center justify-between'>
            <div>
              <div className='text-sm font-medium text-gray-700'>
                Require Email Verification
              </div>
              <p className='text-xs text-gray-500'>
                New users must verify email
              </p>
            </div>
            <label
              className='relative inline-flex items-center cursor-pointer'
              aria-label='Require Email Verification'
            >
              <input
                type='checkbox'
                checked={settings.require_email_verification}
                onChange={e =>
                  setSettings({
                    ...settings,
                    require_email_verification: e.target.checked,
                  })
                }
                className='sr-only peer'
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          <div className='flex items-center justify-between'>
            <div>
              <div className='text-sm font-medium text-gray-700'>
                Enable Email Whitelist
              </div>
              <p className='text-xs text-gray-500'>
                Restrict registration to whitelist
              </p>
            </div>
            <label
              className='relative inline-flex items-center cursor-pointer'
              aria-label='Enable Email Whitelist'
            >
              <input
                type='checkbox'
                checked={settings.enable_whitelist}
                onChange={e =>
                  setSettings({
                    ...settings,
                    enable_whitelist: e.target.checked,
                  })
                }
                className='sr-only peer'
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Database */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex items-center gap-3 mb-4'>
          <Database className='w-5 h-5 text-purple-600' />
          <h3 className='text-lg font-semibold text-gray-900'>Database</h3>
        </div>

        <div className='space-y-4'>
          <div className='flex items-center justify-between'>
            <div>
              <div className='text-sm font-medium text-gray-700'>
                Enable Backups
              </div>
              <p className='text-xs text-gray-500'>
                Automatic database backups
              </p>
            </div>
            <label
              className='relative inline-flex items-center cursor-pointer'
              aria-label='Enable Backups'
            >
              <input
                type='checkbox'
                checked={settings.backup_enabled}
                onChange={e =>
                  setSettings({ ...settings, backup_enabled: e.target.checked })
                }
                className='sr-only peer'
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          <div>
            <label
              htmlFor='backup-schedule'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Backup Schedule
            </label>
            <select
              id='backup-schedule'
              value={settings.backup_schedule}
              onChange={e =>
                setSettings({
                  ...settings,
                  backup_schedule: e.target.value as any,
                })
              }
              disabled={!settings.backup_enabled}
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100'
            >
              <option value='daily'>Daily</option>
              <option value='weekly'>Weekly</option>
              <option value='monthly'>Monthly</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemSettings;
