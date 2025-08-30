import React, { useState, useEffect } from 'react';
import {
  FileText,
  Code,
  Save,
  Download,
  Trash2,
  Plus,
  ChevronDown,
} from 'lucide-react';
import { QuartoSettings } from './QuartoEditor';
import api from '../../services/api';

interface QuartoControlsProps {
  settings: QuartoSettings;
  onSettingsChange: (settings: QuartoSettings) => void;
}

interface QuartoPreset {
  id: string;
  name: string;
  yamlContent: string;
  isDefault: boolean;
}

const QuartoControls: React.FC<QuartoControlsProps> = ({
  settings,
  onSettingsChange,
}) => {
  const [activeTab, setActiveTab] = useState<'simple' | 'advanced'>(
    settings.activeMode
  );
  const [presets, setPresets] = useState<QuartoPreset[]>([]);
  const [themes, setThemes] = useState<{ html: string[]; revealjs: string[] }>({
    html: [],
    revealjs: [],
  });
  const [showSavePresetDialog, setShowSavePresetDialog] = useState(false);
  const [newPresetName, setNewPresetName] = useState('');

  useEffect(() => {
    loadPresets();
    loadThemes();
  }, []);

  const loadPresets = async () => {
    try {
      const response = await api.get('/presets');
      setPresets(response.data);
    } catch (error) {
      console.error('Failed to load presets:', error);
    }
  };

  const loadThemes = async () => {
    try {
      const response = await api.get('/themes');
      setThemes(response.data);
    } catch (error) {
      console.error('Failed to load themes:', error);
    }
  };

  const handleTabChange = (newTab: 'simple' | 'advanced') => {
    // If switching to advanced and it's empty, populate from simple
    if (
      newTab === 'advanced' &&
      !settings.advancedSettings.yaml &&
      settings.simpleSettings.formats.length > 0
    ) {
      const yaml = generateYamlFromSimple(settings.simpleSettings);
      onSettingsChange({
        ...settings,
        advancedSettings: {
          ...settings.advancedSettings,
          yaml,
        },
        activeMode: newTab,
      });
    } else {
      onSettingsChange({
        ...settings,
        activeMode: newTab,
      });
    }
    setActiveTab(newTab);
  };

  const generateYamlFromSimple = (simpleSettings: any): string => {
    const lines = [];
    
    if (simpleSettings.title) {
      lines.push(`title: "${simpleSettings.title}"`);
    }
    if (simpleSettings.subtitle) {
      lines.push(`subtitle: "${simpleSettings.subtitle}"`);
    }
    if (simpleSettings.author) {
      lines.push(`author: "${simpleSettings.author}"`);
    }
    
    if (simpleSettings.formats.length === 1) {
      const format = simpleSettings.formats[0];
      lines.push(`format:`);
      lines.push(`  ${format}:`);
      if (simpleSettings.theme && (format === 'html' || format === 'revealjs')) {
        lines.push(`    theme: ${simpleSettings.theme}`);
      }
      if (simpleSettings.toc && (format === 'html' || format === 'pdf')) {
        lines.push(`    toc: true`);
      }
    } else if (simpleSettings.formats.length > 1) {
      lines.push(`format:`);
      simpleSettings.formats.forEach((format: string) => {
        lines.push(`  ${format}:`);
        if (format === 'html' && simpleSettings.theme) {
          lines.push(`    theme: ${simpleSettings.theme}`);
        }
        if ((format === 'html' || format === 'pdf') && simpleSettings.toc) {
          lines.push(`    toc: true`);
        }
      });
    }
    
    return lines.join('\n');
  };

  const handlePresetSelect = async (presetValue: string) => {
    if (presetValue === 'from-simple') {
      const yaml = generateYamlFromSimple(settings.simpleSettings);
      onSettingsChange({
        ...settings,
        advancedSettings: {
          activePreset: 'from-simple',
          yaml,
        },
      });
    } else if (presetValue === 'clear') {
      if (confirm('Clear advanced settings?')) {
        onSettingsChange({
          ...settings,
          advancedSettings: {
            activePreset: undefined,
            yaml: '',
          },
        });
      }
    } else {
      // Load preset
      const preset = presets.find(p => p.id === presetValue);
      if (preset) {
        onSettingsChange({
          ...settings,
          advancedSettings: {
            activePreset: preset.name,
            yaml: preset.yamlContent,
          },
        });
      }
    }
  };

  const handleSavePreset = async () => {
    if (!newPresetName.trim()) return;
    
    try {
      await api.post('/presets', {
        name: newPresetName,
        yamlContent: settings.advancedSettings.yaml,
        isDefault: false,
      });
      await loadPresets();
      setShowSavePresetDialog(false);
      setNewPresetName('');
    } catch (error) {
      console.error('Failed to save preset:', error);
    }
  };

  const updateSimpleSetting = (key: string, value: any) => {
    onSettingsChange({
      ...settings,
      simpleSettings: {
        ...settings.simpleSettings,
        [key]: value,
      },
    });
  };

  const toggleFormat = (format: string) => {
    const formats = settings.simpleSettings.formats;
    if (formats.includes(format)) {
      updateSimpleSetting(
        'formats',
        formats.filter(f => f !== format)
      );
    } else {
      updateSimpleSetting('formats', [...formats, format]);
    }
  };

  return (
    <div className="p-4">
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-4">
        <button
          onClick={() => handleTabChange('simple')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'simple'
              ? 'text-blue-600 border-blue-600'
              : 'text-gray-500 border-transparent hover:text-gray-700'
          }`}
        >
          <FileText className="inline h-4 w-4 mr-1" />
          Simple
        </button>
        <button
          onClick={() => handleTabChange('advanced')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'advanced'
              ? 'text-blue-600 border-blue-600'
              : 'text-gray-500 border-transparent hover:text-gray-700'
          }`}
        >
          <Code className="inline h-4 w-4 mr-1" />
          Advanced
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'simple' ? (
        <div className="space-y-4">
          {/* Output Formats */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Output Formats
            </label>
            <div className="flex space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.simpleSettings.formats.includes('html')}
                  onChange={() => toggleFormat('html')}
                  className="mr-2"
                />
                HTML
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.simpleSettings.formats.includes('pdf')}
                  onChange={() => toggleFormat('pdf')}
                  className="mr-2"
                />
                PDF
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.simpleSettings.formats.includes('docx')}
                  onChange={() => toggleFormat('docx')}
                  className="mr-2"
                />
                Word
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.simpleSettings.formats.includes('revealjs')}
                  onChange={() => toggleFormat('revealjs')}
                  className="mr-2"
                />
                Slides
              </label>
            </div>
          </div>

          {/* Theme Selection */}
          {(settings.simpleSettings.formats.includes('html') ||
            settings.simpleSettings.formats.includes('revealjs')) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Theme
              </label>
              <select
                value={settings.simpleSettings.theme}
                onChange={e => updateSimpleSetting('theme', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="default">Default</option>
                {themes.html.map(theme => (
                  <option key={theme} value={theme}>
                    {theme.charAt(0).toUpperCase() + theme.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Table of Contents */}
          {(settings.simpleSettings.formats.includes('html') ||
            settings.simpleSettings.formats.includes('pdf')) && (
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.simpleSettings.toc}
                  onChange={e => updateSimpleSetting('toc', e.target.checked)}
                  className="mr-2"
                />
                Include Table of Contents
              </label>
            </div>
          )}

          {/* Author */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Author (optional)
            </label>
            <input
              type="text"
              value={settings.simpleSettings.author}
              onChange={e => updateSimpleSetting('author', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Your name"
            />
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title (optional - can use # in document)
            </label>
            <input
              type="text"
              value={settings.simpleSettings.title || ''}
              onChange={e => updateSimpleSetting('title', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Document title"
            />
          </div>

          {/* Subtitle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Subtitle (optional)
            </label>
            <input
              type="text"
              value={settings.simpleSettings.subtitle || ''}
              onChange={e => updateSimpleSetting('subtitle', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Document subtitle"
            />
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Preset Selection */}
          <div className="flex items-center space-x-2">
            <select
              value={settings.advancedSettings.activePreset || ''}
              onChange={e => handlePresetSelect(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a preset...</option>
              <option value="from-simple">From Simple Mode</option>
              {presets.map(preset => (
                <option key={preset.id} value={preset.id}>
                  {preset.name}
                </option>
              ))}
              <option value="clear">Clear</option>
            </select>
            <button
              onClick={() => setShowSavePresetDialog(true)}
              className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
            >
              <Save className="h-4 w-4 mr-1" />
              Save as...
            </button>
          </div>

          {/* YAML Editor */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              YAML Front Matter
            </label>
            <textarea
              value={settings.advancedSettings.yaml}
              onChange={e =>
                onSettingsChange({
                  ...settings,
                  advancedSettings: {
                    ...settings.advancedSettings,
                    yaml: e.target.value,
                  },
                })
              }
              className="w-full h-64 px-3 py-2 font-mono text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="---
title: 'My Document'
format:
  html:
    theme: cosmo
    toc: true
---"
            />
          </div>

          {/* Save Preset Dialog */}
          {showSavePresetDialog && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg p-6 w-96">
                <h3 className="text-lg font-semibold mb-4">Save Preset</h3>
                <input
                  type="text"
                  value={newPresetName}
                  onChange={e => setNewPresetName(e.target.value)}
                  placeholder="Preset name..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4"
                  autoFocus
                />
                <div className="flex justify-end space-x-2">
                  <button
                    onClick={() => {
                      setShowSavePresetDialog(false);
                      setNewPresetName('');
                    }}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSavePreset}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default QuartoControls;