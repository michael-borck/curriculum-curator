import React, { useState, useEffect } from 'react';
import {
  Brain,
  Plus,
  Save,
  Trash2,
  TestTube,
  AlertCircle,
  CheckCircle,
  Loader2,
  Key,
  Link,
  Shield,
  BarChart3,
  Settings,
  RefreshCw,
} from 'lucide-react';
import llmApi from '../../services/llmApi';
// import { useAuthStore } from '../../stores/authStore';
import { LLMProvider } from '../../types/llm';
import type {
  LLMConfig,
  LLMTestResponse,
  TokenUsageStats,
} from '../../types/llm';
import { PROVIDER_DISPLAY_NAMES, DEFAULT_MODELS } from '../../types/llm';

const LLMSettings: React.FC = () => {
  const [configurations, setConfigurations] = useState<LLMConfig[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<LLMConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<LLMTestResponse | null>(null);
  const [tokenStats, setTokenStats] = useState<TokenUsageStats | null>(null);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState<'configurations' | 'usage'>(
    'configurations'
  );

  // const user = useAuthStore(state => state.user);
  // const isAdmin = user?.role === 'admin'; // Reserved for future admin features

  // Form state for new/edit configuration
  const [formData, setFormData] = useState<Partial<LLMConfig>>({
    provider: LLMProvider.OPENAI,
    api_key: '',
    api_url: '',
    bearer_token: '',
    model_name: '',
    temperature: 0.7,
    max_tokens: 4096,
    is_default: false,
  });

  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    loadConfigurations();
    loadTokenStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadConfigurations = async () => {
    try {
      setIsLoading(true);
      const configs = await llmApi.getUserConfigurations();
      setConfigurations(configs);

      // Set the default config as selected
      const defaultConfig = configs.find(c => c.is_default);
      if (defaultConfig) {
        setSelectedConfig(defaultConfig);
      }
    } catch {
      setError('Failed to load configurations');
      console.error('Error loading configurations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadTokenStats = async () => {
    try {
      const stats = await llmApi.getTokenStats(30);
      setTokenStats(stats);
    } catch {
      console.error('Error loading token stats:', error);
    }
  };

  const handleProviderChange = async (provider: LLMProvider) => {
    setFormData({ ...formData, provider });

    // Load default models for the provider
    if (DEFAULT_MODELS[provider]) {
      setAvailableModels(DEFAULT_MODELS[provider]);
    }

    // Reset provider-specific fields
    if (provider !== 'ollama' && provider !== 'custom') {
      setFormData(prev => ({ ...prev, api_url: '', bearer_token: '' }));
    }
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    setError('');

    try {
      const result = await llmApi.testConnection({
        provider: formData.provider!,
        api_key: formData.api_key || '',
        api_url: formData.api_url || '',
        bearer_token: formData.bearer_token || '',
        model_name: formData.model_name || '',
      });

      setTestResult(result);

      if (result.success && result.available_models) {
        setAvailableModels(result.available_models);

        // Auto-select first model if none selected
        if (!formData.model_name && result.available_models.length > 0) {
          setFormData(prev => ({
            ...prev,
            model_name: result.available_models![0],
          }));
        }
      }
    } catch (error: any) {
      setError('Connection test failed');
      setTestResult({
        success: false,
        message: 'Connection test failed',
        error:
          error?.response?.data?.detail || error?.message || 'Unknown error',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleLoadModels = async () => {
    if (!formData.provider) return;

    try {
      const models = await llmApi.listModels(
        formData.provider,
        formData.api_key,
        formData.api_url,
        formData.bearer_token
      );
      setAvailableModels(models);
      setSuccess('Models loaded successfully');
    } catch {
      setError('Failed to load models');
    }
  };

  const handleSaveConfiguration = async () => {
    if (!formData.provider) {
      setError('Please select a provider');
      return;
    }

    setIsSaving(true);
    setError('');
    setSuccess('');

    try {
      if (isEditing && selectedConfig?.id) {
        const updated = await llmApi.updateConfiguration(
          selectedConfig.id,
          formData
        );
        setConfigurations(configs =>
          configs.map(c => (c.id === updated.id ? updated : c))
        );
        setSelectedConfig(updated);
        setSuccess('Configuration updated successfully');
      } else {
        const newConfig = await llmApi.createConfiguration(
          formData as Omit<LLMConfig, 'id'>
        );
        setConfigurations([...configurations, newConfig]);
        setSelectedConfig(newConfig);
        setSuccess('Configuration created successfully');
      }

      setIsEditing(false);
      resetForm();
    } catch (error: any) {
      setError(error?.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteConfiguration = async (config: LLMConfig) => {
    if (!config.id) return;

    if (
      !window.confirm('Are you sure you want to delete this configuration?')
    ) {
      return;
    }

    try {
      await llmApi.deleteConfiguration(config.id);
      setConfigurations(configs => configs.filter(c => c.id !== config.id));
      if (selectedConfig?.id === config.id) {
        setSelectedConfig(null);
      }
      setSuccess('Configuration deleted successfully');
    } catch {
      setError('Failed to delete configuration');
    }
  };

  const handleEditConfiguration = (config: LLMConfig) => {
    setSelectedConfig(config);
    setFormData(config);
    setIsEditing(true);
  };

  const handleSetDefault = async (config: LLMConfig) => {
    if (!config.id) return;

    try {
      const updated = await llmApi.updateConfiguration(config.id, {
        is_default: true,
      });

      // Update all configurations to reflect new default
      setConfigurations(configs =>
        configs.map(c => ({
          ...c,
          is_default: c.id === updated.id,
        }))
      );

      setSuccess('Default configuration updated');
    } catch {
      setError('Failed to set default configuration');
    }
  };

  const resetForm = () => {
    setFormData({
      provider: LLMProvider.OPENAI,
      api_key: '',
      api_url: '',
      bearer_token: '',
      model_name: '',
      temperature: 0.7,
      max_tokens: 4096,
      is_default: false,
    });
    setTestResult(null);
    setAvailableModels([]);
  };

  const renderProviderFields = () => {
    const { provider } = formData;

    return (
      <>
        {/* API Key - for most providers */}
        {provider !== 'ollama' && (
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              API Key
            </label>
            <div className='relative'>
              <Key className='absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400' />
              <input
                type='password'
                value={formData.api_key || ''}
                onChange={e =>
                  setFormData({ ...formData, api_key: e.target.value })
                }
                className='pl-10 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
                placeholder={`Enter your ${PROVIDER_DISPLAY_NAMES[formData.provider || LLMProvider.OPENAI]} API key`}
              />
            </div>
          </div>
        )}

        {/* API URL - for Ollama and Custom */}
        {(provider === 'ollama' || provider === 'custom') && (
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              API URL
            </label>
            <div className='relative'>
              <Link className='absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400' />
              <input
                type='url'
                value={formData.api_url || ''}
                onChange={e =>
                  setFormData({ ...formData, api_url: e.target.value })
                }
                className='pl-10 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
                placeholder={
                  provider === 'ollama'
                    ? 'http://localhost:11434'
                    : 'https://api.example.com'
                }
              />
            </div>
            <p className='mt-1 text-sm text-gray-500'>
              {provider === 'ollama'
                ? 'Leave empty for local Ollama (localhost:11434)'
                : 'Full URL to your custom LLM API endpoint'}
            </p>
          </div>
        )}

        {/* Bearer Token - for Ollama with auth */}
        {provider === 'ollama' && (
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              Bearer Token (Optional)
            </label>
            <div className='relative'>
              <Shield className='absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400' />
              <input
                type='password'
                value={formData.bearer_token || ''}
                onChange={e =>
                  setFormData({ ...formData, bearer_token: e.target.value })
                }
                className='pl-10 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
                placeholder='Bearer token for protected Ollama instances'
              />
            </div>
            <p className='mt-1 text-sm text-gray-500'>
              Only needed if your Ollama instance requires authentication
            </p>
          </div>
        )}
      </>
    );
  };

  if (isLoading) {
    return (
      <div className='flex justify-center items-center h-64'>
        <Loader2 className='w-8 h-8 animate-spin text-blue-600' />
      </div>
    );
  }

  return (
    <div className='max-w-6xl mx-auto p-6'>
      <div className='mb-6'>
        <h2 className='text-2xl font-bold text-gray-900 flex items-center gap-2'>
          <Brain className='w-6 h-6' />
          LLM Configuration
        </h2>
        <p className='text-gray-600 mt-1'>
          Configure your AI language model providers and settings
        </p>
      </div>

      {/* Tabs */}
      <div className='border-b border-gray-200 mb-6'>
        <nav className='flex gap-4'>
          <button
            onClick={() => setActiveTab('configurations')}
            className={`pb-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'configurations'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Settings className='w-4 h-4 inline mr-2' />
            Configurations
          </button>
          <button
            onClick={() => setActiveTab('usage')}
            className={`pb-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'usage'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <BarChart3 className='w-4 h-4 inline mr-2' />
            Usage & Billing
          </button>
        </nav>
      </div>

      {error && (
        <div className='mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2'>
          <AlertCircle className='w-5 h-5 text-red-600 mt-0.5' />
          <div className='text-sm text-red-800'>{error}</div>
        </div>
      )}

      {success && (
        <div className='mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-2'>
          <CheckCircle className='w-5 h-5 text-green-600 mt-0.5' />
          <div className='text-sm text-green-800'>{success}</div>
        </div>
      )}

      {activeTab === 'configurations' && (
        <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
          {/* Configuration Form */}
          <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
            <h3 className='text-lg font-semibold mb-4'>
              {isEditing ? 'Edit Configuration' : 'New Configuration'}
            </h3>

            <div className='space-y-4'>
              {/* Provider Selection */}
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Provider
                </label>
                <select
                  value={formData.provider}
                  onChange={e =>
                    handleProviderChange(e.target.value as LLMProvider)
                  }
                  className='block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
                >
                  {Object.entries(PROVIDER_DISPLAY_NAMES).map(
                    ([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    )
                  )}
                </select>
              </div>

              {/* Provider-specific fields */}
              {renderProviderFields()}

              {/* Model Selection */}
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Model
                </label>
                <div className='flex gap-2'>
                  <select
                    value={formData.model_name || ''}
                    onChange={e =>
                      setFormData({ ...formData, model_name: e.target.value })
                    }
                    className='flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
                  >
                    <option value=''>Select a model...</option>
                    {availableModels.map(model => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={handleLoadModels}
                    className='px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors'
                    title='Refresh models'
                  >
                    <RefreshCw className='w-4 h-4' />
                  </button>
                </div>
              </div>

              {/* Temperature */}
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Temperature: {formData.temperature}
                </label>
                <input
                  type='range'
                  min='0'
                  max='2'
                  step='0.1'
                  value={formData.temperature}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      temperature: parseFloat(e.target.value),
                    })
                  }
                  className='w-full'
                />
                <div className='flex justify-between text-xs text-gray-500'>
                  <span>Precise</span>
                  <span>Balanced</span>
                  <span>Creative</span>
                </div>
              </div>

              {/* Max Tokens */}
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Max Tokens (Optional)
                </label>
                <input
                  type='number'
                  value={formData.max_tokens || ''}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      max_tokens: e.target.value
                        ? parseInt(e.target.value)
                        : 4096,
                    })
                  }
                  className='block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
                  placeholder='Leave empty for default'
                />
              </div>

              {/* Default Configuration */}
              <div className='flex items-center'>
                <input
                  type='checkbox'
                  id='is_default'
                  checked={formData.is_default}
                  onChange={e =>
                    setFormData({ ...formData, is_default: e.target.checked })
                  }
                  className='h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
                />
                <label
                  htmlFor='is_default'
                  className='ml-2 text-sm text-gray-700'
                >
                  Set as default configuration
                </label>
              </div>

              {/* Test Connection */}
              {testResult && (
                <div
                  className={`p-4 rounded-lg ${
                    testResult.success
                      ? 'bg-green-50 border border-green-200'
                      : 'bg-red-50 border border-red-200'
                  }`}
                >
                  <div className='flex items-start gap-2'>
                    {testResult.success ? (
                      <CheckCircle className='w-5 h-5 text-green-600 mt-0.5' />
                    ) : (
                      <AlertCircle className='w-5 h-5 text-red-600 mt-0.5' />
                    )}
                    <div className='flex-1'>
                      <p
                        className={`text-sm font-medium ${
                          testResult.success ? 'text-green-800' : 'text-red-800'
                        }`}
                      >
                        {testResult.message}
                      </p>
                      {testResult.response_text && (
                        <p className='text-sm text-gray-600 mt-1'>
                          Response: {testResult.response_text}
                        </p>
                      )}
                      {testResult.error && (
                        <p className='text-sm text-red-600 mt-1'>
                          Error: {testResult.error}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className='flex gap-2'>
                <button
                  onClick={handleTestConnection}
                  disabled={isTesting}
                  className='flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2'
                >
                  {isTesting ? (
                    <Loader2 className='w-4 h-4 animate-spin' />
                  ) : (
                    <TestTube className='w-4 h-4' />
                  )}
                  Test Connection
                </button>
                <button
                  onClick={handleSaveConfiguration}
                  disabled={isSaving}
                  className='flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2'
                >
                  {isSaving ? (
                    <Loader2 className='w-4 h-4 animate-spin' />
                  ) : (
                    <Save className='w-4 h-4' />
                  )}
                  {isEditing ? 'Update' : 'Save'}
                </button>
                {isEditing && (
                  <button
                    onClick={() => {
                      setIsEditing(false);
                      resetForm();
                    }}
                    className='px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors'
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Saved Configurations */}
          <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
            <div className='flex justify-between items-center mb-4'>
              <h3 className='text-lg font-semibold'>Saved Configurations</h3>
              <button
                onClick={resetForm}
                className='text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1'
              >
                <Plus className='w-4 h-4' />
                New
              </button>
            </div>

            {configurations.length === 0 ? (
              <p className='text-gray-500 text-center py-8'>
                No configurations saved yet
              </p>
            ) : (
              <div className='space-y-3'>
                {configurations.map(config => (
                  <div
                    key={config.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedConfig?.id === config.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedConfig(config)}
                  >
                    <div className='flex justify-between items-start'>
                      <div className='flex-1'>
                        <div className='flex items-center gap-2'>
                          <span className='font-medium'>
                            {PROVIDER_DISPLAY_NAMES[config.provider]}
                          </span>
                          {config.is_default && (
                            <span className='px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full'>
                              Default
                            </span>
                          )}
                        </div>
                        <p className='text-sm text-gray-600 mt-1'>
                          Model: {config.model_name || 'Not selected'}
                        </p>
                        <p className='text-xs text-gray-500 mt-1'>
                          Temperature: {config.temperature}
                        </p>
                      </div>
                      <div className='flex gap-1'>
                        {!config.is_default && (
                          <button
                            onClick={e => {
                              e.stopPropagation();
                              handleSetDefault(config);
                            }}
                            className='p-1 text-gray-400 hover:text-blue-600'
                            title='Set as default'
                          >
                            <CheckCircle className='w-4 h-4' />
                          </button>
                        )}
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            handleEditConfiguration(config);
                          }}
                          className='p-1 text-gray-400 hover:text-blue-600'
                          title='Edit'
                        >
                          <Settings className='w-4 h-4' />
                        </button>
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            handleDeleteConfiguration(config);
                          }}
                          className='p-1 text-gray-400 hover:text-red-600'
                          title='Delete'
                        >
                          <Trash2 className='w-4 h-4' />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'usage' && (
        <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
          <h3 className='text-lg font-semibold mb-4'>Token Usage Statistics</h3>

          {tokenStats ? (
            <div className='space-y-6'>
              <div className='grid grid-cols-3 gap-4'>
                <div className='bg-gray-50 p-4 rounded-lg'>
                  <p className='text-sm text-gray-600'>Total Tokens</p>
                  <p className='text-2xl font-bold text-gray-900'>
                    {tokenStats.total_tokens.toLocaleString()}
                  </p>
                </div>
                <div className='bg-gray-50 p-4 rounded-lg'>
                  <p className='text-sm text-gray-600'>Estimated Cost</p>
                  <p className='text-2xl font-bold text-gray-900'>
                    ${tokenStats.total_cost.toFixed(2)}
                  </p>
                </div>
                <div className='bg-gray-50 p-4 rounded-lg'>
                  <p className='text-sm text-gray-600'>Period</p>
                  <p className='text-sm font-medium text-gray-900'>
                    Last 30 days
                  </p>
                </div>
              </div>

              {/* Usage by Provider */}
              <div>
                <h4 className='font-medium text-gray-900 mb-2'>
                  Usage by Provider
                </h4>
                <div className='space-y-2'>
                  {Object.entries(tokenStats.by_provider).map(
                    ([provider, tokens]) => (
                      <div
                        key={provider}
                        className='flex justify-between items-center'
                      >
                        <span className='text-sm text-gray-600'>
                          {PROVIDER_DISPLAY_NAMES[provider as LLMProvider] ||
                            provider}
                        </span>
                        <span className='text-sm font-medium'>
                          {(tokens as number).toLocaleString()} tokens
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>

              {/* Usage by Model */}
              <div>
                <h4 className='font-medium text-gray-900 mb-2'>
                  Usage by Model
                </h4>
                <div className='space-y-2'>
                  {Object.entries(tokenStats.by_model).map(
                    ([model, tokens]) => (
                      <div
                        key={model}
                        className='flex justify-between items-center'
                      >
                        <span className='text-sm text-gray-600'>{model}</span>
                        <span className='text-sm font-medium'>
                          {(tokens as number).toLocaleString()} tokens
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>
            </div>
          ) : (
            <p className='text-gray-500 text-center py-8'>
              No usage data available
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default LLMSettings;
