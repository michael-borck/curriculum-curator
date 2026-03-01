/**
 * Shared LLM provider fields used by both LLMSettings and AdminLLMSettings.
 *
 * Extracts the provider-specific connection fields (API key, URL, bearer token)
 * and model selector that are duplicated between user and admin settings.
 */

import { Key, Link, Shield, RefreshCw, Loader2 } from 'lucide-react';
import { LLMProvider, PROVIDER_DISPLAY_NAMES } from '../../types/llm';
import type { LLMConfig } from '../../types/llm';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface LLMProviderFieldsProps {
  formData: Partial<LLMConfig>;
  onChange: (updates: Partial<LLMConfig>) => void;
  availableModels: string[];
  onRefreshModels: () => void;
  loadingModels?: boolean | undefined;
  /** Whether to show all providers from PROVIDER_DISPLAY_NAMES or a hardcoded subset. */
  providerOptions?: 'all' | 'core';
  onProviderChange: (provider: LLMProvider) => void;
}

// ─── Component ───────────────────────────────────────────────────────────────

const CORE_PROVIDERS: { value: LLMProvider; label: string }[] = [
  { value: LLMProvider.OPENAI, label: 'OpenAI' },
  { value: LLMProvider.ANTHROPIC, label: 'Anthropic' },
  { value: LLMProvider.OLLAMA, label: 'Ollama' },
  { value: LLMProvider.GEMINI, label: 'Google Gemini' },
];

export function LLMProviderFields({
  formData,
  onChange,
  availableModels,
  onRefreshModels,
  loadingModels = false,
  providerOptions = 'all',
  onProviderChange,
}: LLMProviderFieldsProps) {
  const { provider } = formData;

  return (
    <>
      {/* Provider Selection */}
      <div>
        <label className='block text-sm font-medium text-gray-700 mb-1'>
          Provider
        </label>
        <select
          value={formData.provider}
          onChange={e => onProviderChange(e.target.value as LLMProvider)}
          className='block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
        >
          {providerOptions === 'all'
            ? Object.entries(PROVIDER_DISPLAY_NAMES).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))
            : CORE_PROVIDERS.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
        </select>
      </div>

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
              onChange={e => onChange({ api_key: e.target.value })}
              className='pl-10 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
              placeholder={`Enter your ${PROVIDER_DISPLAY_NAMES[formData.provider || LLMProvider.OPENAI] ?? 'provider'} API key`}
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
              onChange={e => onChange({ api_url: e.target.value })}
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
              onChange={e => onChange({ bearer_token: e.target.value })}
              className='pl-10 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
              placeholder='Bearer token for protected Ollama instances'
            />
          </div>
          <p className='mt-1 text-sm text-gray-500'>
            Only needed if your Ollama instance requires authentication
          </p>
        </div>
      )}

      {/* Model Selection */}
      <div>
        <label className='block text-sm font-medium text-gray-700 mb-1'>
          Model
        </label>
        <div className='flex gap-2'>
          {availableModels.length > 0 ? (
            <select
              value={formData.model_name || ''}
              onChange={e => onChange({ model_name: e.target.value })}
              className='flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
            >
              <option value=''>Select a model...</option>
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
              onChange={e => onChange({ model_name: e.target.value })}
              className='flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
              placeholder='Enter model name or test connection'
            />
          )}
          <button
            type='button'
            onClick={onRefreshModels}
            disabled={loadingModels}
            className='px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors'
            title='Refresh models'
          >
            {loadingModels ? (
              <Loader2 className='w-4 h-4 animate-spin' />
            ) : (
              <RefreshCw className='w-4 h-4' />
            )}
          </button>
        </div>
      </div>
    </>
  );
}
