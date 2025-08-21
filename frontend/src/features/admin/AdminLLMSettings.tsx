import React, { useState, useEffect } from 'react';
import {
  AlertCircle,
  Check,
  ChevronDown,
  ChevronUp,
  Download,
  Key,
  Loader2,
  Plus,
  RefreshCw,
  Save,
  Server,
  Settings2,
  TestTube,
  Trash2,
  TrendingUp,
  User,
  X,
} from 'lucide-react';
import { llmApi } from '../../services/llmApi';
import type { LLMConfig, LLMProvider, TokenStats } from '../../types/llm';

interface AdminLLMSettingsProps {
  onClose?: () => void;
}

export const AdminLLMSettings: React.FC<AdminLLMSettingsProps> = ({
  onClose,
}) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  // System configurations
  const [systemConfigs, setSystemConfigs] = useState<LLMConfig[]>([]);
  const [userConfigs, setUserConfigs] = useState<LLMConfig[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<LLMConfig | null>(null);
  const [isNewConfig, setIsNewConfig] = useState(false);

  // Form data
  const [formData, setFormData] = useState<Partial<LLMConfig>>({
    provider: 'openai',
    is_default: false,
    temperature: 0.7,
    max_tokens: 4096,
  });

  // Model selection
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);

  // Token usage stats
  const [tokenStats, setTokenStats] = useState<TokenStats[]>([]);
  const [showStats, setShowStats] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);

  // Testing
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [testing, setTesting] = useState(false);

  // Expanded sections
  const [expandedSections, setExpandedSections] = useState({
    system: true,
    users: false,
    stats: false,
  });

  useEffect(() => {
    loadConfigurations();
  }, []);

  const loadConfigurations = async () => {
    setLoading(true);
    try {
      const [systemData, userData] = await Promise.all([
        llmApi.getSystemConfigurations(),
        llmApi.getAllUserConfigurations(),
      ]);
      setSystemConfigs(systemData);
      setUserConfigs(userData);
    } catch (error) {
      console.error('Failed to load configurations:', error);
      setMessage({ type: 'error', text: 'Failed to load configurations' });
    } finally {
      setLoading(false);
    }
  };

  const loadTokenStats = async () => {
    setStatsLoading(true);
    try {
      const stats = await llmApi.getAllUsersTokenStats();
      setTokenStats(stats);
      setShowStats(true);
    } catch (error) {
      console.error('Failed to load token stats:', error);
      setMessage({ type: 'error', text: 'Failed to load usage statistics' });
    } finally {
      setStatsLoading(false);
    }
  };

  const handleProviderChange = async (provider: LLMProvider) => {
    setFormData({ ...formData, provider, model_name: undefined });
    setAvailableModels([]);

    if (formData.api_key || provider === 'ollama') {
      await loadModels(provider);
    }
  };

  const loadModels = async (provider: LLMProvider) => {
    setLoadingModels(true);
    try {
      const models = await llmApi.listModels(
        provider,
        formData.api_key,
        formData.api_url,
        formData.bearer_token
      );
      setAvailableModels(models);
      if (models.length > 0 && !formData.model_name) {
        setFormData(prev => ({ ...prev, model_name: models[0] }));
      }
    } catch (error) {
      console.error('Failed to load models:', error);
      setAvailableModels([]);
    } finally {
      setLoadingModels(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const result = await llmApi.testConnection({
        provider: formData.provider!,
        api_key: formData.api_key,
        api_url: formData.api_url,
        bearer_token: formData.bearer_token,
        model_name: formData.model_name,
      });

      setTestResult({
        success: result.success,
        message:
          result.message ||
          (result.success ? 'Connection successful!' : 'Connection failed'),
      });

      if (result.available_models && result.available_models.length > 0) {
        setAvailableModels(result.available_models);
        if (!formData.model_name) {
          setFormData(prev => ({
            ...prev,
            model_name: result.available_models![0],
          }));
        }
      }
    } catch (_error) {
      setTestResult({
        success: false,
        message: 'Failed to test connection',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!formData.provider) {
      setMessage({ type: 'error', text: 'Please select a provider' });
      return;
    }

    setSaving(true);
    try {
      if (isNewConfig) {
        await llmApi.createSystemConfiguration(formData);
        setMessage({
          type: 'success',
          text: 'Configuration created successfully',
        });
      } else if (selectedConfig) {
        await llmApi.updateConfiguration(selectedConfig.id, formData);
        setMessage({
          type: 'success',
          text: 'Configuration updated successfully',
        });
      }
      await loadConfigurations();
      setSelectedConfig(null);
      setIsNewConfig(false);
      setFormData({
        provider: 'openai',
        is_default: false,
        temperature: 0.7,
        max_tokens: 4096,
      });
    } catch (error) {
      console.error('Failed to save configuration:', error);
      setMessage({ type: 'error', text: 'Failed to save configuration' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (configId: string) => {
    if (
      !window.confirm('Are you sure you want to delete this configuration?')
    ) {
      return;
    }

    try {
      await llmApi.deleteConfiguration(configId);
      setMessage({
        type: 'success',
        text: 'Configuration deleted successfully',
      });
      await loadConfigurations();
      if (selectedConfig?.id === configId) {
        setSelectedConfig(null);
        setFormData({
          provider: 'openai',
          is_default: false,
          temperature: 0.7,
          max_tokens: 4096,
        });
      }
    } catch (error) {
      console.error('Failed to delete configuration:', error);
      setMessage({ type: 'error', text: 'Failed to delete configuration' });
    }
  };

  const selectConfig = (config: LLMConfig) => {
    setSelectedConfig(config);
    setIsNewConfig(false);
    setFormData({
      provider: config.provider,
      api_key: config.api_key,
      api_url: config.api_url,
      bearer_token: config.bearer_token,
      model_name: config.model_name,
      temperature: config.temperature,
      max_tokens: config.max_tokens,
      is_default: config.is_default,
    });
    if (config.model_name) {
      setAvailableModels([config.model_name]);
    }
  };

  const startNewConfig = () => {
    setSelectedConfig(null);
    setIsNewConfig(true);
    setFormData({
      provider: 'openai',
      is_default: false,
      temperature: 0.7,
      max_tokens: 4096,
    });
    setAvailableModels([]);
  };

  const exportStats = () => {
    const csv = [
      [
        'User ID',
        'User Email',
        'Provider',
        'Total Tokens',
        'Total Cost',
        'Request Count',
      ],
      ...tokenStats.map(stat => [
        stat.user_id,
        stat.user_email || 'N/A',
        stat.provider,
        stat.total_tokens.toString(),
        `$${stat.total_cost.toFixed(4)}`,
        stat.request_count.toString(),
      ]),
    ]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `token-usage-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <Loader2 className='h-8 w-8 animate-spin text-blue-600' />
      </div>
    );
  }

  return (
    <div className='max-w-6xl mx-auto p-6'>
      <div className='bg-white rounded-lg shadow-lg'>
        <div className='p-6 border-b border-gray-200'>
          <div className='flex items-center justify-between'>
            <div className='flex items-center space-x-3'>
              <Settings2 className='h-6 w-6 text-blue-600' />
              <h2 className='text-xl font-semibold text-gray-900'>
                Admin LLM Configuration
              </h2>
            </div>
            {onClose && (
              <button
                onClick={onClose}
                className='text-gray-400 hover:text-gray-600 transition-colors'
              >
                <X className='h-5 w-5' />
              </button>
            )}
          </div>
        </div>

        {message && (
          <div className='mx-6 mt-4'>
            <div
              className={`p-4 rounded-lg flex items-start space-x-3 ${
                message.type === 'success'
                  ? 'bg-green-50 text-green-800'
                  : 'bg-red-50 text-red-800'
              }`}
            >
              {message.type === 'success' ? (
                <Check className='h-5 w-5 mt-0.5' />
              ) : (
                <AlertCircle className='h-5 w-5 mt-0.5' />
              )}
              <span>{message.text}</span>
            </div>
          </div>
        )}

        <div className='p-6 space-y-6'>
          {/* System Configurations Section */}
          <div className='border rounded-lg'>
            <button
              onClick={() => toggleSection('system')}
              className='w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors'
            >
              <div className='flex items-center space-x-2'>
                <Server className='h-5 w-5 text-gray-600' />
                <span className='font-medium'>System Configurations</span>
                <span className='text-sm text-gray-500'>
                  ({systemConfigs.length})
                </span>
              </div>
              {expandedSections.system ? (
                <ChevronUp className='h-5 w-5 text-gray-400' />
              ) : (
                <ChevronDown className='h-5 w-5 text-gray-400' />
              )}
            </button>

            {expandedSections.system && (
              <div className='p-4'>
                <div className='flex justify-between items-center mb-4'>
                  <h3 className='font-medium text-gray-700'>
                    Manage System-wide LLM Settings
                  </h3>
                  <button
                    onClick={startNewConfig}
                    className='flex items-center space-x-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700'
                  >
                    <Plus className='h-4 w-4' />
                    <span>New Configuration</span>
                  </button>
                </div>

                {systemConfigs.length === 0 && !isNewConfig ? (
                  <p className='text-gray-500 text-center py-8'>
                    No system configurations yet
                  </p>
                ) : (
                  <div className='space-y-2'>
                    {systemConfigs.map(config => (
                      <div
                        key={config.id}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          selectedConfig?.id === config.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'hover:bg-gray-50'
                        }`}
                        onClick={() => selectConfig(config)}
                      >
                        <div className='flex items-center justify-between'>
                          <div className='flex items-center space-x-3'>
                            <Key className='h-4 w-4 text-gray-400' />
                            <div>
                              <span className='font-medium'>
                                {config.provider.toUpperCase()}
                              </span>
                              {config.model_name && (
                                <span className='ml-2 text-sm text-gray-500'>
                                  ({config.model_name})
                                </span>
                              )}
                              {config.is_default && (
                                <span className='ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded'>
                                  Default
                                </span>
                              )}
                            </div>
                          </div>
                          <button
                            onClick={e => {
                              e.stopPropagation();
                              handleDelete(config.id);
                            }}
                            className='text-red-500 hover:text-red-700'
                          >
                            <Trash2 className='h-4 w-4' />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {(selectedConfig || isNewConfig) && (
                  <div className='mt-4 p-4 border-t'>
                    <h4 className='font-medium text-gray-700 mb-4'>
                      {isNewConfig ? 'New Configuration' : 'Edit Configuration'}
                    </h4>

                    <div className='space-y-4'>
                      <div>
                        <label className='block text-sm font-medium text-gray-700 mb-1'>
                          Provider
                        </label>
                        <select
                          value={formData.provider}
                          onChange={e =>
                            handleProviderChange(e.target.value as LLMProvider)
                          }
                          className='w-full px-3 py-2 border rounded-lg'
                        >
                          <option value='openai'>OpenAI</option>
                          <option value='anthropic'>Anthropic</option>
                          <option value='ollama'>Ollama</option>
                          <option value='gemini'>Google Gemini</option>
                        </select>
                      </div>

                      {formData.provider !== 'ollama' && (
                        <div>
                          <label className='block text-sm font-medium text-gray-700 mb-1'>
                            API Key
                          </label>
                          <input
                            type='password'
                            value={formData.api_key || ''}
                            onChange={e =>
                              setFormData({
                                ...formData,
                                api_key: e.target.value,
                              })
                            }
                            className='w-full px-3 py-2 border rounded-lg'
                            placeholder='Enter API key'
                          />
                        </div>
                      )}

                      {formData.provider === 'ollama' && (
                        <>
                          <div>
                            <label className='block text-sm font-medium text-gray-700 mb-1'>
                              API URL
                            </label>
                            <input
                              type='text'
                              value={formData.api_url || ''}
                              onChange={e =>
                                setFormData({
                                  ...formData,
                                  api_url: e.target.value,
                                })
                              }
                              className='w-full px-3 py-2 border rounded-lg'
                              placeholder='http://localhost:11434'
                            />
                          </div>

                          <div>
                            <label className='block text-sm font-medium text-gray-700 mb-1'>
                              Bearer Token (Optional)
                            </label>
                            <input
                              type='password'
                              value={formData.bearer_token || ''}
                              onChange={e =>
                                setFormData({
                                  ...formData,
                                  bearer_token: e.target.value,
                                })
                              }
                              className='w-full px-3 py-2 border rounded-lg'
                              placeholder='Optional authentication token'
                            />
                          </div>
                        </>
                      )}

                      <div className='flex items-end space-x-2'>
                        <div className='flex-1'>
                          <label className='block text-sm font-medium text-gray-700 mb-1'>
                            Model
                          </label>
                          {availableModels.length > 0 ? (
                            <select
                              value={formData.model_name || ''}
                              onChange={e =>
                                setFormData({
                                  ...formData,
                                  model_name: e.target.value,
                                })
                              }
                              className='w-full px-3 py-2 border rounded-lg'
                            >
                              {availableModels.map(model => (
                                <option key={model} value={model}>
                                  {model}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <input
                              type='text'
                              value={formData.model_name || ''}
                              onChange={e =>
                                setFormData({
                                  ...formData,
                                  model_name: e.target.value,
                                })
                              }
                              className='w-full px-3 py-2 border rounded-lg'
                              placeholder='Enter model name or test connection'
                            />
                          )}
                        </div>
                        <button
                          onClick={() =>
                            loadModels(formData.provider as LLMProvider)
                          }
                          disabled={loadingModels}
                          className='px-3 py-2 text-blue-600 hover:bg-blue-50 rounded-lg'
                        >
                          {loadingModels ? (
                            <Loader2 className='h-5 w-5 animate-spin' />
                          ) : (
                            <RefreshCw className='h-5 w-5' />
                          )}
                        </button>
                      </div>

                      <div className='grid grid-cols-2 gap-4'>
                        <div>
                          <label className='block text-sm font-medium text-gray-700 mb-1'>
                            Temperature
                          </label>
                          <input
                            type='number'
                            value={formData.temperature || 0.7}
                            onChange={e =>
                              setFormData({
                                ...formData,
                                temperature: parseFloat(e.target.value),
                              })
                            }
                            className='w-full px-3 py-2 border rounded-lg'
                            min='0'
                            max='2'
                            step='0.1'
                          />
                        </div>

                        <div>
                          <label className='block text-sm font-medium text-gray-700 mb-1'>
                            Max Tokens
                          </label>
                          <input
                            type='number'
                            value={formData.max_tokens || 4096}
                            onChange={e =>
                              setFormData({
                                ...formData,
                                max_tokens: parseInt(e.target.value),
                              })
                            }
                            className='w-full px-3 py-2 border rounded-lg'
                            min='1'
                            max='32000'
                          />
                        </div>
                      </div>

                      <div className='flex items-center space-x-2'>
                        <input
                          type='checkbox'
                          id='is-default'
                          checked={formData.is_default || false}
                          onChange={e =>
                            setFormData({
                              ...formData,
                              is_default: e.target.checked,
                            })
                          }
                          className='rounded border-gray-300'
                        />
                        <label
                          htmlFor='is-default'
                          className='text-sm text-gray-700'
                        >
                          Set as default configuration
                        </label>
                      </div>

                      {testResult && (
                        <div
                          className={`p-3 rounded-lg flex items-start space-x-2 ${
                            testResult.success
                              ? 'bg-green-50 text-green-700'
                              : 'bg-red-50 text-red-700'
                          }`}
                        >
                          {testResult.success ? (
                            <Check className='h-5 w-5 mt-0.5' />
                          ) : (
                            <X className='h-5 w-5 mt-0.5' />
                          )}
                          <span className='text-sm'>{testResult.message}</span>
                        </div>
                      )}

                      <div className='flex space-x-3'>
                        <button
                          onClick={handleTestConnection}
                          disabled={testing || !formData.provider}
                          className='flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50'
                        >
                          {testing ? (
                            <Loader2 className='h-4 w-4 animate-spin' />
                          ) : (
                            <TestTube className='h-4 w-4' />
                          )}
                          <span>Test Connection</span>
                        </button>

                        <button
                          onClick={handleSave}
                          disabled={saving || !formData.provider}
                          className='flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50'
                        >
                          {saving ? (
                            <Loader2 className='h-4 w-4 animate-spin' />
                          ) : (
                            <Save className='h-4 w-4' />
                          )}
                          <span>{isNewConfig ? 'Create' : 'Update'}</span>
                        </button>

                        <button
                          onClick={() => {
                            setSelectedConfig(null);
                            setIsNewConfig(false);
                            setFormData({
                              provider: 'openai',
                              is_default: false,
                              temperature: 0.7,
                              max_tokens: 4096,
                            });
                          }}
                          className='px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg'
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* User Configurations Section */}
          <div className='border rounded-lg'>
            <button
              onClick={() => toggleSection('users')}
              className='w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors'
            >
              <div className='flex items-center space-x-2'>
                <User className='h-5 w-5 text-gray-600' />
                <span className='font-medium'>User Configurations</span>
                <span className='text-sm text-gray-500'>
                  ({userConfigs.length})
                </span>
              </div>
              {expandedSections.users ? (
                <ChevronUp className='h-5 w-5 text-gray-400' />
              ) : (
                <ChevronDown className='h-5 w-5 text-gray-400' />
              )}
            </button>

            {expandedSections.users && (
              <div className='p-4'>
                <h3 className='font-medium text-gray-700 mb-4'>
                  User-specific Configurations
                </h3>
                {userConfigs.length === 0 ? (
                  <p className='text-gray-500 text-center py-8'>
                    No user configurations yet
                  </p>
                ) : (
                  <div className='space-y-2'>
                    {userConfigs.map(config => (
                      <div
                        key={config.id}
                        className='p-3 border rounded-lg flex items-center justify-between'
                      >
                        <div className='flex items-center space-x-3'>
                          <Key className='h-4 w-4 text-gray-400' />
                          <div>
                            <span className='font-medium'>
                              {config.provider.toUpperCase()}
                            </span>
                            {config.model_name && (
                              <span className='ml-2 text-sm text-gray-500'>
                                ({config.model_name})
                              </span>
                            )}
                            <span className='ml-2 text-sm text-gray-400'>
                              User: {config.user_email || config.user_id}
                            </span>
                            {config.is_default && (
                              <span className='ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded'>
                                User Default
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Token Usage Statistics Section */}
          <div className='border rounded-lg'>
            <button
              onClick={() => {
                toggleSection('stats');
                if (!showStats && !expandedSections.stats) {
                  loadTokenStats();
                }
              }}
              className='w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors'
            >
              <div className='flex items-center space-x-2'>
                <TrendingUp className='h-5 w-5 text-gray-600' />
                <span className='font-medium'>Token Usage Statistics</span>
              </div>
              {expandedSections.stats ? (
                <ChevronUp className='h-5 w-5 text-gray-400' />
              ) : (
                <ChevronDown className='h-5 w-5 text-gray-400' />
              )}
            </button>

            {expandedSections.stats && (
              <div className='p-4'>
                <div className='flex justify-between items-center mb-4'>
                  <h3 className='font-medium text-gray-700'>
                    30-Day Usage Summary
                  </h3>
                  <div className='flex space-x-2'>
                    <button
                      onClick={loadTokenStats}
                      disabled={statsLoading}
                      className='flex items-center space-x-2 px-3 py-1.5 text-blue-600 hover:bg-blue-50 rounded-lg'
                    >
                      {statsLoading ? (
                        <Loader2 className='h-4 w-4 animate-spin' />
                      ) : (
                        <RefreshCw className='h-4 w-4' />
                      )}
                      <span>Refresh</span>
                    </button>
                    {tokenStats.length > 0 && (
                      <button
                        onClick={exportStats}
                        className='flex items-center space-x-2 px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded-lg'
                      >
                        <Download className='h-4 w-4' />
                        <span>Export CSV</span>
                      </button>
                    )}
                  </div>
                </div>

                {statsLoading ? (
                  <div className='flex justify-center py-8'>
                    <Loader2 className='h-6 w-6 animate-spin text-blue-600' />
                  </div>
                ) : tokenStats.length === 0 ? (
                  <p className='text-gray-500 text-center py-8'>
                    No usage data available
                  </p>
                ) : (
                  <div className='overflow-x-auto'>
                    <table className='w-full text-sm'>
                      <thead>
                        <tr className='border-b'>
                          <th className='text-left py-2'>User</th>
                          <th className='text-left py-2'>Provider</th>
                          <th className='text-right py-2'>Requests</th>
                          <th className='text-right py-2'>Tokens</th>
                          <th className='text-right py-2'>Cost</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tokenStats.map(stat => (
                          <tr
                            key={`${stat.user_id}-${stat.provider}`}
                            className='border-b'
                          >
                            <td className='py-2'>
                              {stat.user_email || stat.user_id}
                            </td>
                            <td className='py-2'>
                              {stat.provider.toUpperCase()}
                            </td>
                            <td className='text-right py-2'>
                              {stat.request_count}
                            </td>
                            <td className='text-right py-2'>
                              {stat.total_tokens.toLocaleString()}
                            </td>
                            <td className='text-right py-2'>
                              ${stat.total_cost.toFixed(4)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr className='font-medium'>
                          <td colSpan={2} className='py-2'>
                            Total
                          </td>
                          <td className='text-right py-2'>
                            {tokenStats.reduce(
                              (sum, s) => sum + s.request_count,
                              0
                            )}
                          </td>
                          <td className='text-right py-2'>
                            {tokenStats
                              .reduce((sum, s) => sum + s.total_tokens, 0)
                              .toLocaleString()}
                          </td>
                          <td className='text-right py-2'>
                            $
                            {tokenStats
                              .reduce((sum, s) => sum + s.total_cost, 0)
                              .toFixed(2)}
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
