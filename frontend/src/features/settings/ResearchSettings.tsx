import { useState } from 'react';
import { Save, CheckCircle, AlertCircle, Eye, EyeOff } from 'lucide-react';
import * as researchApi from '../../services/researchApi';
import type { ResearchSettings as ResearchSettingsType } from '../../types/research';

const ResearchSettings = () => {
  const [preferredTier, setPreferredTier] = useState(1);
  const [googleCseApiKey, setGoogleCseApiKey] = useState('');
  const [googleCseEngineId, setGoogleCseEngineId] = useState('');
  const [serperApiKey, setSerperApiKey] = useState('');
  const [braveSearchApiKey, setBraveSearchApiKey] = useState('');
  const [tavilyApiKey, setTavilyApiKey] = useState('');
  const [coreApiKey, setCoreApiKey] = useState('');
  const [searxngUrl, setSearxngUrl] = useState('');
  const [excludedDomainsText, setExcludedDomainsText] = useState('');

  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleShow = (key: string) => {
    setShowKeys(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const excludedDomains = excludedDomainsText
        .split(/[\n,]/)
        .map(s => s.trim().toLowerCase())
        .filter(s => s.length > 0);

      const settings: ResearchSettingsType = {
        preferredTier,
        searchApiKeys: {
          googleCseApiKey: googleCseApiKey || undefined,
          googleCseEngineId: googleCseEngineId || undefined,
          serperApiKey: serperApiKey || undefined,
          braveSearchApiKey: braveSearchApiKey || undefined,
          tavilyApiKey: tavilyApiKey || undefined,
          coreApiKey: coreApiKey || undefined,
        },
        searxngUrl: searxngUrl || undefined,
        excludedDomains:
          excludedDomains.length > 0 ? excludedDomains : undefined,
      };
      await researchApi.saveResearchSettings(settings);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 3000);
    } catch (e: unknown) {
      setError(
        e instanceof Error ? e.message : 'Failed to save research settings'
      );
    } finally {
      setSaving(false);
    }
  };

  const apiKeyField = (
    label: string,
    id: string,
    value: string,
    onChange: (v: string) => void,
    placeholder: string
  ) => (
    <div>
      <label className='block text-sm font-medium text-gray-700 mb-1'>
        {label}
      </label>
      <div className='relative'>
        <input
          type={showKeys[id] ? 'text' : 'password'}
          value={value}
          onChange={e => onChange(e.target.value)}
          className='w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
          placeholder={placeholder}
        />
        <button
          type='button'
          onClick={() => toggleShow(id)}
          className='absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600'
        >
          {showKeys[id] ? (
            <EyeOff className='w-4 h-4' />
          ) : (
            <Eye className='w-4 h-4' />
          )}
        </button>
      </div>
    </div>
  );

  return (
    <div className='bg-white rounded-lg shadow-md p-6'>
      <h2 className='text-xl font-semibold mb-2'>Research Settings</h2>
      <p className='text-sm text-gray-600 mb-6'>
        Configure your preferred search tier and API keys for web search
        providers.
      </p>

      {error && (
        <div className='mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2'>
          <AlertCircle className='w-5 h-5 text-red-600 mt-0.5 flex-shrink-0' />
          <span className='text-sm text-red-800'>{error}</span>
        </div>
      )}

      <div className='space-y-6'>
        {/* Preferred Tier */}
        <div>
          <label className='block text-sm font-medium text-gray-700 mb-1'>
            Preferred Search Tier
          </label>
          <select
            value={preferredTier}
            onChange={e => setPreferredTier(parseInt(e.target.value))}
            className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
          >
            <option value={1}>
              Tier 1: Academic (OpenAlex + Semantic Scholar + CrossRef + CORE)
            </option>
            <option value={3}>
              Tier 3: General Web (DuckDuckGo fallback, keys optional)
            </option>
            <option value={4}>Tier 4: SearXNG (requires instance URL)</option>
          </select>
          <p className='text-xs text-gray-500 mt-1'>
            Tier 1 searches OpenAlex, Semantic Scholar, and CrossRef (always
            available). Add a CORE API key below for broader coverage.
          </p>
        </div>

        {/* CORE API Key (Tier 1 enhancement) */}
        <div>
          <h3 className='font-medium mb-3'>CORE API Key (Tier 1)</h3>
          <p className='text-xs text-gray-500 mb-3'>
            Free with registration at{' '}
            <a
              href='https://core.ac.uk/services/api'
              target='_blank'
              rel='noopener noreferrer'
              className='text-blue-600 hover:underline'
            >
              core.ac.uk
            </a>
            . Adds 300M+ open access papers (theses, reports, institutional
            repositories).
          </p>
          <div className='space-y-4'>
            {apiKeyField(
              'CORE API Key',
              'coreApiKey',
              coreApiKey,
              setCoreApiKey,
              'abc123...'
            )}
          </div>
        </div>

        {/* API Keys */}
        <div>
          <h3 className='font-medium mb-3'>
            General Web Search API Keys (Tier 3)
          </h3>
          <p className='text-xs text-gray-500 mb-3'>
            All keys are optional. Keyed providers are tried in order (Google
            CSE → Serper → Brave → Tavily); DuckDuckGo is used as a free
            fallback when no provider returns results. Keys are stored on the
            server.
          </p>
          <div className='space-y-4'>
            {apiKeyField(
              'Google CSE API Key',
              'googleCseApiKey',
              googleCseApiKey,
              setGoogleCseApiKey,
              'AIza...'
            )}
            {apiKeyField(
              'Google CSE Engine ID',
              'googleCseEngineId',
              googleCseEngineId,
              setGoogleCseEngineId,
              'abc123...'
            )}
            {apiKeyField(
              'Serper API Key',
              'serperApiKey',
              serperApiKey,
              setSerperApiKey,
              'Single-key Google proxy — sign up at serper.dev'
            )}
            {apiKeyField(
              'Brave Search API Key',
              'braveSearchApiKey',
              braveSearchApiKey,
              setBraveSearchApiKey,
              'BSA...'
            )}
            {apiKeyField(
              'Tavily API Key',
              'tavilyApiKey',
              tavilyApiKey,
              setTavilyApiKey,
              'tvly-...'
            )}
          </div>
        </div>

        {/* Excluded Domains */}
        <div>
          <h3 className='font-medium mb-3'>Excluded Domains</h3>
          <p className='text-xs text-gray-500 mb-3'>
            Results from these domains are dropped from every tier. One per line
            or comma-separated. Matches apply to subdomains too (e.g.
            <code className='mx-1 px-1 bg-gray-100 rounded'>youtube.com</code>
            also blocks{' '}
            <code className='px-1 bg-gray-100 rounded'>m.youtube.com</code>).
          </p>
          <textarea
            value={excludedDomainsText}
            onChange={e => setExcludedDomainsText(e.target.value)}
            rows={4}
            className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm'
            placeholder={'youtube.com\npinterest.com\nquora.com'}
          />
        </div>

        {/* SearXNG */}
        <div>
          <h3 className='font-medium mb-3'>SearXNG Instance (Tier 4)</h3>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              SearXNG URL
            </label>
            <input
              type='text'
              value={searxngUrl}
              onChange={e => setSearxngUrl(e.target.value)}
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
              placeholder='https://searxng.example.com'
            />
            <p className='text-xs text-gray-500 mt-1'>
              URL of your self-hosted SearXNG instance with JSON format enabled.
            </p>
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
              {saving ? 'Saving...' : 'Save Research Settings'}
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default ResearchSettings;
