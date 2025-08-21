import { useState } from 'react';
import {
  User,
  Bell,
  Shield,
  Palette,
  Key,
  Save,
  CheckCircle,
  Brain,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import api from '../../services/api';
import LLMSettings from './LLMSettings';

const Settings = () => {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('profile');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    institution: '',
    department: '',
    bio: '',
  });

  const [preferences, setPreferences] = useState({
    emailNotifications: true,
    browserNotifications: false,
    weeklyReports: true,
    contentSuggestions: true,
    language: 'en-AU',
    timezone: 'Australia/Sydney',
    theme: 'light',
  });

  const [security, setSecurity] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
    twoFactorEnabled: false,
  });

  const [llmSettings, setLlmSettings] = useState({
    provider: user?.llm_config?.provider || 'system',
    openaiApiKey: '',
    anthropicApiKey: '',
    geminiApiKey: '',
    modelPreference: user?.llm_config?.model || '',
    useSystemDefault: true,
  });

  const saveProfile = async () => {
    try {
      setSaving(true);
      await api.patch('/auth/profile', profileData);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Error saving profile:', error);
    } finally {
      setSaving(false);
    }
  };

  const savePreferences = async () => {
    try {
      setSaving(true);
      // Save preferences to backend
      setSaved(true);
      window.setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Error saving preferences:', error);
    } finally {
      setSaving(false);
    }
  };

  const updatePassword = async () => {
    if (security.newPassword !== security.confirmPassword) {
      window.alert('Passwords do not match');
      return;
    }

    try {
      setSaving(true);
      await api.post('/auth/change-password', {
        current_password: security.currentPassword,
        new_password: security.newPassword,
      });
      setSecurity({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
        twoFactorEnabled: security.twoFactorEnabled,
      });
      setSaved(true);
      window.setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Error updating password:', error);
    } finally {
      setSaving(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'preferences', label: 'Preferences', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'llm', label: 'AI/LLM Settings', icon: Brain },
  ];

  return (
    <div className='p-6 max-w-6xl mx-auto'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>Settings</h1>
        <p className='text-gray-600'>
          Manage your account and application preferences
        </p>
      </div>

      <div className='flex gap-6'>
        {/* Sidebar */}
        <div className='w-64'>
          <nav className='space-y-1'>
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition ${
                    activeTab === tab.id
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Icon className='h-5 w-5' />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content */}
        <div className='flex-1'>
          {activeTab === 'profile' && (
            <div className='bg-white rounded-lg shadow-md p-6'>
              <h2 className='text-xl font-semibold mb-6'>
                Profile Information
              </h2>

              <div className='space-y-4'>
                <div className='grid grid-cols-2 gap-4'>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Full Name
                    </label>
                    <input
                      type='text'
                      value={profileData.name}
                      onChange={e =>
                        setProfileData({ ...profileData, name: e.target.value })
                      }
                      className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                    />
                  </div>

                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Email Address
                    </label>
                    <input
                      type='email'
                      value={profileData.email}
                      onChange={e =>
                        setProfileData({
                          ...profileData,
                          email: e.target.value,
                        })
                      }
                      className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                      disabled
                    />
                  </div>
                </div>

                <div className='grid grid-cols-2 gap-4'>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Institution
                    </label>
                    <input
                      type='text'
                      value={profileData.institution}
                      onChange={e =>
                        setProfileData({
                          ...profileData,
                          institution: e.target.value,
                        })
                      }
                      className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                      placeholder='e.g., University Name'
                    />
                  </div>

                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Department
                    </label>
                    <input
                      type='text'
                      value={profileData.department}
                      onChange={e =>
                        setProfileData({
                          ...profileData,
                          department: e.target.value,
                        })
                      }
                      className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                      placeholder='e.g., Computer Science'
                    />
                  </div>
                </div>

                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Bio
                  </label>
                  <textarea
                    value={profileData.bio}
                    onChange={e =>
                      setProfileData({ ...profileData, bio: e.target.value })
                    }
                    className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                    rows={4}
                    placeholder='Tell us about yourself...'
                  />
                </div>
              </div>

              <div className='mt-6 flex justify-end'>
                <button
                  onClick={saveProfile}
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
                      {saving ? 'Saving...' : 'Save Changes'}
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'preferences' && (
            <div className='bg-white rounded-lg shadow-md p-6'>
              <h2 className='text-xl font-semibold mb-6'>
                Notification Preferences
              </h2>

              <div className='space-y-6'>
                <div>
                  <h3 className='font-medium mb-3'>Email Notifications</h3>
                  <div className='space-y-3'>
                    <label className='flex items-center'>
                      <input
                        type='checkbox'
                        checked={preferences.emailNotifications}
                        onChange={e =>
                          setPreferences({
                            ...preferences,
                            emailNotifications: e.target.checked,
                          })
                        }
                        className='mr-3 h-4 w-4 text-blue-600 rounded border-gray-300'
                      />
                      <span>Email notifications for important updates</span>
                    </label>

                    <label className='flex items-center'>
                      <input
                        type='checkbox'
                        checked={preferences.weeklyReports}
                        onChange={e =>
                          setPreferences({
                            ...preferences,
                            weeklyReports: e.target.checked,
                          })
                        }
                        className='mr-3 h-4 w-4 text-blue-600 rounded border-gray-300'
                      />
                      <span>Weekly progress reports</span>
                    </label>

                    <label className='flex items-center'>
                      <input
                        type='checkbox'
                        checked={preferences.contentSuggestions}
                        onChange={e =>
                          setPreferences({
                            ...preferences,
                            contentSuggestions: e.target.checked,
                          })
                        }
                        className='mr-3 h-4 w-4 text-blue-600 rounded border-gray-300'
                      />
                      <span>Content improvement suggestions</span>
                    </label>
                  </div>
                </div>

                <div>
                  <h3 className='font-medium mb-3'>Language & Region</h3>
                  <div className='grid grid-cols-2 gap-4'>
                    <div>
                      <label className='block text-sm font-medium text-gray-700 mb-1'>
                        Language
                      </label>
                      <select
                        value={preferences.language}
                        onChange={e =>
                          setPreferences({
                            ...preferences,
                            language: e.target.value,
                          })
                        }
                        className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                      >
                        <option value='en-US'>English (US)</option>
                        <option value='en-GB'>English (UK)</option>
                        <option value='en-AU'>English (AU)</option>
                      </select>
                    </div>

                    <div>
                      <label className='block text-sm font-medium text-gray-700 mb-1'>
                        Timezone
                      </label>
                      <select
                        value={preferences.timezone}
                        onChange={e =>
                          setPreferences({
                            ...preferences,
                            timezone: e.target.value,
                          })
                        }
                        className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                      >
                        <option value='Australia/Sydney'>Sydney</option>
                        <option value='Australia/Melbourne'>Melbourne</option>
                        <option value='Australia/Perth'>Perth</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              <div className='mt-6 flex justify-end'>
                <button
                  onClick={savePreferences}
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
                      {saving ? 'Saving...' : 'Save Preferences'}
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className='bg-white rounded-lg shadow-md p-6'>
              <h2 className='text-xl font-semibold mb-6'>Security Settings</h2>

              <div className='space-y-6'>
                <div>
                  <h3 className='font-medium mb-3'>Change Password</h3>
                  <div className='space-y-4'>
                    <div>
                      <label className='block text-sm font-medium text-gray-700 mb-1'>
                        Current Password
                      </label>
                      <input
                        type='password'
                        value={security.currentPassword}
                        onChange={e =>
                          setSecurity({
                            ...security,
                            currentPassword: e.target.value,
                          })
                        }
                        className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                      />
                    </div>

                    <div className='grid grid-cols-2 gap-4'>
                      <div>
                        <label className='block text-sm font-medium text-gray-700 mb-1'>
                          New Password
                        </label>
                        <input
                          type='password'
                          value={security.newPassword}
                          onChange={e =>
                            setSecurity({
                              ...security,
                              newPassword: e.target.value,
                            })
                          }
                          className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                        />
                      </div>

                      <div>
                        <label className='block text-sm font-medium text-gray-700 mb-1'>
                          Confirm Password
                        </label>
                        <input
                          type='password'
                          value={security.confirmPassword}
                          onChange={e =>
                            setSecurity({
                              ...security,
                              confirmPassword: e.target.value,
                            })
                          }
                          className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                        />
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={updatePassword}
                    disabled={
                      saving ||
                      !security.currentPassword ||
                      !security.newPassword
                    }
                    className='mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center'
                  >
                    <Key className='h-4 w-4 mr-2' />
                    Update Password
                  </button>
                </div>

                <div>
                  <h3 className='font-medium mb-3'>
                    Two-Factor Authentication
                  </h3>
                  <label className='flex items-center'>
                    <input
                      type='checkbox'
                      checked={security.twoFactorEnabled}
                      onChange={e =>
                        setSecurity({
                          ...security,
                          twoFactorEnabled: e.target.checked,
                        })
                      }
                      className='mr-3 h-4 w-4 text-blue-600 rounded border-gray-300'
                    />
                    <span>Enable two-factor authentication</span>
                  </label>
                  <p className='text-sm text-gray-600 mt-2'>
                    Add an extra layer of security to your account
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'llm' && <LLMSettings />}

          {activeTab === 'llm-old' && (
            <div className='bg-white rounded-lg shadow-md p-6'>
              <h2 className='text-xl font-semibold mb-6'>AI/LLM Settings</h2>

              <div className='space-y-6'>
                {/* Provider Selection */}
                <div>
                  <h3 className='font-medium mb-3'>LLM Provider</h3>
                  <div className='space-y-3'>
                    <label className='flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50'>
                      <input
                        type='radio'
                        name='llmProvider'
                        value='system'
                        checked={llmSettings.provider === 'system'}
                        onChange={e =>
                          setLlmSettings({
                            ...llmSettings,
                            provider: e.target.value,
                          })
                        }
                        className='mr-3'
                      />
                      <div>
                        <span className='font-medium'>Use System Default</span>
                        <p className='text-sm text-gray-600'>
                          Use the institution&apos;s configured LLM provider
                        </p>
                      </div>
                    </label>

                    <label className='flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50'>
                      <input
                        type='radio'
                        name='llmProvider'
                        value='openai'
                        checked={llmSettings.provider === 'openai'}
                        onChange={e =>
                          setLlmSettings({
                            ...llmSettings,
                            provider: e.target.value,
                          })
                        }
                        className='mr-3'
                      />
                      <div>
                        <span className='font-medium'>OpenAI (GPT-4)</span>
                        <p className='text-sm text-gray-600'>
                          Use your own OpenAI API key
                        </p>
                      </div>
                    </label>

                    <label className='flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50'>
                      <input
                        type='radio'
                        name='llmProvider'
                        value='anthropic'
                        checked={llmSettings.provider === 'anthropic'}
                        onChange={e =>
                          setLlmSettings({
                            ...llmSettings,
                            provider: e.target.value,
                          })
                        }
                        className='mr-3'
                      />
                      <div>
                        <span className='font-medium'>Anthropic (Claude)</span>
                        <p className='text-sm text-gray-600'>
                          Use your own Anthropic API key
                        </p>
                      </div>
                    </label>

                    <label className='flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50'>
                      <input
                        type='radio'
                        name='llmProvider'
                        value='gemini'
                        checked={llmSettings.provider === 'gemini'}
                        onChange={e =>
                          setLlmSettings({
                            ...llmSettings,
                            provider: e.target.value,
                          })
                        }
                        className='mr-3'
                      />
                      <div>
                        <span className='font-medium'>Google Gemini</span>
                        <p className='text-sm text-gray-600'>
                          Use your own Google Gemini API key
                        </p>
                      </div>
                    </label>
                  </div>
                </div>

                {/* API Keys */}
                {llmSettings.provider !== 'system' && (
                  <div>
                    <h3 className='font-medium mb-3'>API Configuration</h3>

                    {llmSettings.provider === 'openai' && (
                      <div>
                        <label className='block text-sm font-medium text-gray-700 mb-1'>
                          OpenAI API Key
                        </label>
                        <input
                          type='password'
                          value={llmSettings.openaiApiKey}
                          onChange={e =>
                            setLlmSettings({
                              ...llmSettings,
                              openaiApiKey: e.target.value,
                            })
                          }
                          className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                          placeholder='sk-...'
                        />
                        <p className='text-sm text-gray-600 mt-1'>
                          Get your API key from{' '}
                          <a
                            href='https://platform.openai.com/api-keys'
                            target='_blank'
                            className='text-blue-600 hover:underline'
                            rel='noreferrer'
                          >
                            OpenAI Platform
                          </a>
                        </p>
                      </div>
                    )}

                    {llmSettings.provider === 'anthropic' && (
                      <div>
                        <label className='block text-sm font-medium text-gray-700 mb-1'>
                          Anthropic API Key
                        </label>
                        <input
                          type='password'
                          value={llmSettings.anthropicApiKey}
                          onChange={e =>
                            setLlmSettings({
                              ...llmSettings,
                              anthropicApiKey: e.target.value,
                            })
                          }
                          className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                          placeholder='sk-ant-...'
                        />
                        <p className='text-sm text-gray-600 mt-1'>
                          Get your API key from{' '}
                          <a
                            href='https://console.anthropic.com/'
                            target='_blank'
                            className='text-blue-600 hover:underline'
                            rel='noreferrer'
                          >
                            Anthropic Console
                          </a>
                        </p>
                      </div>
                    )}

                    {llmSettings.provider === 'gemini' && (
                      <div>
                        <label className='block text-sm font-medium text-gray-700 mb-1'>
                          Google Gemini API Key
                        </label>
                        <input
                          type='password'
                          value={llmSettings.geminiApiKey}
                          onChange={e =>
                            setLlmSettings({
                              ...llmSettings,
                              geminiApiKey: e.target.value,
                            })
                          }
                          className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                          placeholder='AIza...'
                        />
                        <p className='text-sm text-gray-600 mt-1'>
                          Get your API key from{' '}
                          <a
                            href='https://makersuite.google.com/app/apikey'
                            target='_blank'
                            className='text-blue-600 hover:underline'
                            rel='noreferrer'
                          >
                            Google AI Studio
                          </a>
                        </p>
                      </div>
                    )}

                    {/* Model Selection */}
                    <div className='mt-4'>
                      <label className='block text-sm font-medium text-gray-700 mb-1'>
                        Preferred Model
                      </label>
                      <select
                        value={llmSettings.modelPreference}
                        onChange={e =>
                          setLlmSettings({
                            ...llmSettings,
                            modelPreference: e.target.value,
                          })
                        }
                        className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                      >
                        <option value=''>Default</option>
                        {llmSettings.provider === 'openai' && (
                          <>
                            <option value='gpt-4'>GPT-4</option>
                            <option value='gpt-4-turbo'>GPT-4 Turbo</option>
                            <option value='gpt-3.5-turbo'>GPT-3.5 Turbo</option>
                          </>
                        )}
                        {llmSettings.provider === 'anthropic' && (
                          <>
                            <option value='claude-3-opus'>Claude 3 Opus</option>
                            <option value='claude-3-sonnet'>
                              Claude 3 Sonnet
                            </option>
                            <option value='claude-3-haiku'>
                              Claude 3 Haiku
                            </option>
                          </>
                        )}
                        {llmSettings.provider === 'gemini' && (
                          <>
                            <option value='gemini-pro'>Gemini Pro</option>
                            <option value='gemini-pro-vision'>
                              Gemini Pro Vision
                            </option>
                          </>
                        )}
                      </select>
                    </div>
                  </div>
                )}

                {/* System Default Info */}
                {llmSettings.provider === 'system' && (
                  <div className='bg-blue-50 rounded-lg p-4'>
                    <h3 className='font-medium text-blue-900 mb-2'>
                      System Default Provider
                    </h3>
                    <p className='text-sm text-blue-800'>
                      You are using the institution&apos;s configured LLM
                      provider. Contact your administrator for details about the
                      current provider and model being used.
                    </p>
                  </div>
                )}

                {/* Save Button */}
                <div className='flex justify-end'>
                  <button
                    onClick={async () => {
                      try {
                        setSaving(true);
                        // Save LLM config
                        const llmConfig: any = {
                          provider: llmSettings.provider,
                          model: llmSettings.modelPreference,
                        };

                        // Only include API keys if provider is selected and key is provided
                        if (
                          llmSettings.provider === 'openai' &&
                          llmSettings.openaiApiKey
                        ) {
                          llmConfig.openai_api_key = llmSettings.openaiApiKey;
                        }
                        if (
                          llmSettings.provider === 'anthropic' &&
                          llmSettings.anthropicApiKey
                        ) {
                          llmConfig.anthropic_api_key =
                            llmSettings.anthropicApiKey;
                        }
                        if (
                          llmSettings.provider === 'gemini' &&
                          llmSettings.geminiApiKey
                        ) {
                          llmConfig.gemini_api_key = llmSettings.geminiApiKey;
                        }

                        await api.patch('/auth/profile', {
                          llm_config: llmConfig,
                        });

                        setSaved(true);
                        window.setTimeout(() => setSaved(false), 3000);
                      } catch (error) {
                        console.error('Error saving LLM settings:', error);
                      } finally {
                        setSaving(false);
                      }
                    }}
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
                        {saving ? 'Saving...' : 'Save LLM Settings'}
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className='bg-white rounded-lg shadow-md p-6'>
              <h2 className='text-xl font-semibold mb-6'>Appearance</h2>

              <div className='space-y-6'>
                <div>
                  <h3 className='font-medium mb-3'>Theme</h3>
                  <div className='grid grid-cols-3 gap-4'>
                    <label className='cursor-pointer'>
                      <input
                        type='radio'
                        name='theme'
                        value='light'
                        checked={preferences.theme === 'light'}
                        onChange={e =>
                          setPreferences({
                            ...preferences,
                            theme: e.target.value,
                          })
                        }
                        className='sr-only'
                      />
                      <div
                        className={`p-4 border-2 rounded-lg text-center ${
                          preferences.theme === 'light'
                            ? 'border-blue-500'
                            : 'border-gray-200'
                        }`}
                      >
                        <div className='w-full h-20 bg-white border border-gray-300 rounded mb-2'></div>
                        <span className='text-sm'>Light</span>
                      </div>
                    </label>

                    <label className='cursor-pointer'>
                      <input
                        type='radio'
                        name='theme'
                        value='dark'
                        checked={preferences.theme === 'dark'}
                        onChange={e =>
                          setPreferences({
                            ...preferences,
                            theme: e.target.value,
                          })
                        }
                        className='sr-only'
                      />
                      <div
                        className={`p-4 border-2 rounded-lg text-center ${
                          preferences.theme === 'dark'
                            ? 'border-blue-500'
                            : 'border-gray-200'
                        }`}
                      >
                        <div className='w-full h-20 bg-gray-900 rounded mb-2'></div>
                        <span className='text-sm'>Dark</span>
                      </div>
                    </label>

                    <label className='cursor-pointer'>
                      <input
                        type='radio'
                        name='theme'
                        value='auto'
                        checked={preferences.theme === 'auto'}
                        onChange={e =>
                          setPreferences({
                            ...preferences,
                            theme: e.target.value,
                          })
                        }
                        className='sr-only'
                      />
                      <div
                        className={`p-4 border-2 rounded-lg text-center ${
                          preferences.theme === 'auto'
                            ? 'border-blue-500'
                            : 'border-gray-200'
                        }`}
                      >
                        <div className='w-full h-20 bg-gradient-to-r from-white to-gray-900 rounded mb-2'></div>
                        <span className='text-sm'>Auto</span>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
