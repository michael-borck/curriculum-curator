import { useState, useEffect } from 'react';
import {
  User,
  Shield,
  Key,
  Save,
  CheckCircle,
  Brain,
  Sparkles,
  Plug,
  Loader2,
  Star,
  Search,
  Download,
  HardDriveDownload,
  GraduationCap,
  Building2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuthStore } from '../../stores/authStore';
import api from '../../services/api';
import { getPlugins, updatePluginConfig } from '../../services/api';
import type { PluginInfo } from '../../services/api';
import LLMSettings from './LLMSettings';
import TeachingStyleSettings from './TeachingStyleSettings';
import { SECTOR_PROFILES } from '../../constants/sectorProfiles';
import type { SectorId } from '../../constants/sectorProfiles';
import QualityRatingSettings from './QualityRatingSettings';
import ResearchSettings from './ResearchSettings';
import ExportTemplates from './ExportTemplates';
import CurtinSettings from './CurtinSettings';
import CLOSetManager from './CLOSetManager';

const Settings = () => {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('profile');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    institution: user?.institution || '',
    department: user?.department || '',
    educationSector: user?.educationSector || '',
  });

  const [security, setSecurity] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [downloading, setDownloading] = useState(false);

  const [pluginList, setPluginList] = useState<PluginInfo[]>([]);
  const [pluginsLoading, setPluginsLoading] = useState(false);
  const [pluginsLoaded, setPluginsLoaded] = useState(false);

  // Load plugins when tab is selected
  const loadPlugins = async () => {
    if (pluginsLoaded) return;
    setPluginsLoading(true);
    try {
      const response = await getPlugins();
      setPluginList(response.data.plugins);
      setPluginsLoaded(true);
    } catch (error) {
      console.error('Failed to load plugins:', error);
      toast.error('Failed to load quality plugins');
    } finally {
      setPluginsLoading(false);
    }
  };

  const handlePluginToggle = async (name: string, enabled: boolean) => {
    try {
      await updatePluginConfig(name, { enabled });
      setPluginList(prev =>
        prev.map(p => (p.name === name ? { ...p, enabled } : p))
      );
    } catch (error) {
      console.error('Failed to update plugin:', error);
      toast.error('Failed to update plugin');
    }
  };

  const handleDownloadData = async () => {
    setDownloading(true);
    try {
      const response = await api.get('/user/export/data', {
        params: { export_format: 'zip' },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(response.data as Blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `curriculum-curator-export-${new Date().toISOString().slice(0, 10)}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Data exported successfully');
    } catch {
      toast.error('Failed to download data');
    } finally {
      setDownloading(false);
    }
  };

  const saveProfile = async () => {
    try {
      setSaving(true);
      const response = await api.patch('/auth/profile', profileData);
      // Update auth store from the API response so all fields persist
      if (user && response.data) {
        useAuthStore.setState({
          user: {
            ...user,
            ...response.data,
          },
        });
      }
      setSaved(true);
      window.setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Error saving profile:', error);
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
    { id: 'teaching-style', label: 'Teaching Style', icon: Sparkles },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'llm', label: 'AI/LLM Settings', icon: Brain },
    { id: 'quality-rating', label: 'Quality Rating', icon: Star },
    { id: 'research', label: 'Research', icon: Search },
    { id: 'export', label: 'Export', icon: Download },
    { id: 'clo-sets', label: 'CLO Sets', icon: GraduationCap },
    { id: 'curtin', label: 'Curtin', icon: Building2 },
    { id: 'plugins', label: 'Quality Plugins', icon: Plug },
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
                    Education Sector
                  </label>
                  <select
                    value={profileData.educationSector}
                    onChange={e =>
                      setProfileData({
                        ...profileData,
                        educationSector: e.target.value,
                      })
                    }
                    className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
                  >
                    <option value=''>Not set</option>
                    {(Object.keys(SECTOR_PROFILES) as SectorId[]).map(id => (
                      <option key={id} value={id}>
                        {SECTOR_PROFILES[id].label}
                      </option>
                    ))}
                  </select>
                  <p className='text-xs text-gray-500 mt-1'>
                    Controls default labels and presets for new units
                  </p>
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

              <hr className='my-8 border-gray-200' />

              <div>
                <h3 className='text-lg font-semibold text-gray-900 mb-1'>
                  Data Export
                </h3>
                <p className='text-sm text-gray-600 mb-4'>
                  Download all your units and content as a ZIP archive.
                </p>
                <button
                  onClick={handleDownloadData}
                  disabled={downloading}
                  className='px-5 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 flex items-center gap-2 transition'
                >
                  {downloading ? (
                    <Loader2 className='h-4 w-4 animate-spin' />
                  ) : (
                    <HardDriveDownload className='h-4 w-4' />
                  )}
                  {downloading ? 'Downloading...' : 'Download My Data'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'teaching-style' && <TeachingStyleSettings />}

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
              </div>
            </div>
          )}

          {activeTab === 'llm' && <LLMSettings />}

          {activeTab === 'quality-rating' && <QualityRatingSettings />}

          {activeTab === 'research' && <ResearchSettings />}

          {activeTab === 'export' && <ExportTemplates />}

          {activeTab === 'clo-sets' && (
            <div className='bg-white rounded-lg shadow-md p-6'>
              <CLOSetManager />
            </div>
          )}

          {activeTab === 'curtin' && <CurtinSettings />}

          {activeTab === 'plugins' && (
            <PluginsTab
              plugins={pluginList}
              loading={pluginsLoading}
              onLoad={loadPlugins}
              onToggle={handlePluginToggle}
            />
          )}
        </div>
      </div>
    </div>
  );
};

const PluginsTab: React.FC<{
  plugins: PluginInfo[];
  loading: boolean;
  onLoad: () => void;
  onToggle: (name: string, enabled: boolean) => void;
}> = ({ plugins, loading, onLoad, onToggle }) => {
  useEffect(() => {
    onLoad();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const validators = plugins.filter(p => p.pluginType === 'validator');
  const remediators = plugins.filter(p => p.pluginType === 'remediator');

  if (loading && plugins.length === 0) {
    return (
      <div className='bg-white rounded-lg shadow-md p-6 flex items-center justify-center h-40'>
        <Loader2 className='animate-spin text-teal-600' size={32} />
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      <div className='bg-white rounded-lg shadow-md p-6'>
        <h2 className='text-xl font-semibold mb-2'>Quality Plugins</h2>
        <p className='text-sm text-gray-600 mb-6'>
          Rule-based checks that run on your content without using AI. Toggle
          plugins on or off to customise which checks run.
        </p>

        {/* Validators */}
        <h3 className='font-medium text-gray-800 mb-3'>Validators</h3>
        <div className='space-y-3 mb-6'>
          {validators.map(plugin => (
            <div
              key={plugin.name}
              className='flex items-center justify-between p-3 border border-gray-200 rounded-lg'
            >
              <div className='flex-1'>
                <span className='font-medium text-sm'>
                  {plugin.name
                    .replace(/_/g, ' ')
                    .replace(/\b\w/g, c => c.toUpperCase())}
                </span>
                <p className='text-xs text-gray-500'>{plugin.description}</p>
              </div>
              <label className='relative inline-flex items-center cursor-pointer'>
                <input
                  type='checkbox'
                  checked={plugin.enabled}
                  onChange={e => onToggle(plugin.name, e.target.checked)}
                  className='sr-only peer'
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-teal-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-teal-600"></div>
              </label>
            </div>
          ))}
          {validators.length === 0 && (
            <p className='text-sm text-gray-400'>No validators available</p>
          )}
        </div>

        {/* Remediators */}
        <h3 className='font-medium text-gray-800 mb-3'>Auto-fix Plugins</h3>
        <div className='space-y-3'>
          {remediators.map(plugin => (
            <div
              key={plugin.name}
              className='flex items-center justify-between p-3 border border-gray-200 rounded-lg'
            >
              <div className='flex-1'>
                <span className='font-medium text-sm'>
                  {plugin.name
                    .replace(/_/g, ' ')
                    .replace(/\b\w/g, c => c.toUpperCase())}
                </span>
                <p className='text-xs text-gray-500'>{plugin.description}</p>
              </div>
              <label className='relative inline-flex items-center cursor-pointer'>
                <input
                  type='checkbox'
                  checked={plugin.enabled}
                  onChange={e => onToggle(plugin.name, e.target.checked)}
                  className='sr-only peer'
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-teal-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-teal-600"></div>
              </label>
            </div>
          ))}
          {remediators.length === 0 && (
            <p className='text-sm text-gray-400'>
              No auto-fix plugins available
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
