import React, { useState, useEffect } from 'react';
import {
  FileText,
  Settings,
  Download,
  Eye,
  Save,
  Code,
  Layout,
  ChevronDown,
} from 'lucide-react';
import RichTextEditor from './RichTextEditor';
import QuartoControls from './QuartoControls';
import api from '../../services/api';

interface QuartoEditorProps {
  contentId?: string;
  content: string;
  onChange: (content: string) => void;
  onExport?: (formats: string[]) => void;
}

export interface QuartoSettings {
  simpleSettings: {
    formats: string[];
    theme: string;
    toc: boolean;
    author: string;
    title?: string;
    subtitle?: string;
  };
  advancedSettings: {
    activePreset?: string;
    yaml: string;
  };
  activeMode: 'simple' | 'advanced';
}

const QuartoEditor: React.FC<QuartoEditorProps> = ({
  contentId,
  content,
  onChange,
  onExport,
}) => {
  const [quartoSettings, setQuartoSettings] = useState<QuartoSettings>({
    simpleSettings: {
      formats: ['html'],
      theme: 'default',
      toc: true,
      author: '',
      title: '',
      subtitle: '',
    },
    advancedSettings: {
      activePreset: undefined,
      yaml: '',
    },
    activeMode: 'simple',
  });

  const [isExporting, setIsExporting] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [previewHtml, setPreviewHtml] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Load settings from backend if contentId is provided
  useEffect(() => {
    if (contentId) {
      loadQuartoSettings();
    }
  }, [contentId]);

  const loadQuartoSettings = async () => {
    if (!contentId) return;
    
    try {
      const response = await api.get(`/content/${contentId}/quarto-settings`);
      setQuartoSettings({
        simpleSettings: response.data.simple_settings || quartoSettings.simpleSettings,
        advancedSettings: {
          activePreset: response.data.active_preset,
          yaml: response.data.advanced_yaml || '',
        },
        activeMode: response.data.active_mode || 'simple',
      });
    } catch (error) {
      console.error('Failed to load Quarto settings:', error);
    }
  };

  const saveQuartoSettings = async () => {
    if (!contentId) return;
    
    setIsSaving(true);
    try {
      await api.put(`/content/${contentId}/quarto-settings`, {
        simpleSettings: quartoSettings.simpleSettings,
        advancedYaml: quartoSettings.advancedSettings.yaml,
        activeMode: quartoSettings.activeMode,
        activePreset: quartoSettings.advancedSettings.activePreset,
      });
    } catch (error) {
      console.error('Failed to save Quarto settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleExport = async () => {
    if (!contentId) {
      alert('Please save the content first before exporting');
      return;
    }

    setIsExporting(true);
    try {
      const response = await api.post(`/content/${contentId}/export`, {
        mode: quartoSettings.activeMode,
        settings:
          quartoSettings.activeMode === 'simple'
            ? quartoSettings.simpleSettings
            : { yaml: quartoSettings.advancedSettings.yaml },
      });

      if (response.data.success) {
        // Download each output file
        for (const output of response.data.outputs) {
          const downloadUrl = `/api/content/${contentId}/export/${response.data.renderId}/${output.filename}`;
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = output.filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }

        if (onExport) {
          onExport(response.data.outputs.map((o: any) => o.format));
        }
      }
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please check your settings and try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const handlePreview = async () => {
    setShowPreview(true);
    try {
      const response = await api.post(`/content/${contentId}/preview`, {
        content: content,
        settings: quartoSettings.simpleSettings,
      });
      setPreviewHtml(response.data.html);
    } catch (error) {
      console.error('Preview failed:', error);
      setPreviewHtml('<p>Preview generation failed</p>');
    }
  };

  const getActiveFormats = () => {
    if (quartoSettings.activeMode === 'simple') {
      return quartoSettings.simpleSettings.formats;
    } else {
      // Parse YAML to extract formats (simplified)
      const yamlContent = quartoSettings.advancedSettings.yaml;
      if (yamlContent.includes('format:')) {
        // This is a simplified extraction - in production, use a YAML parser
        const formats = [];
        if (yamlContent.includes('html:')) formats.push('html');
        if (yamlContent.includes('pdf:')) formats.push('pdf');
        if (yamlContent.includes('docx:')) formats.push('docx');
        if (yamlContent.includes('revealjs:')) formats.push('revealjs');
        return formats.length > 0 ? formats : ['html'];
      }
      return ['html'];
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header Bar */}
      <div className="border-b border-gray-200 bg-white px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Quarto Editor
            </h2>
            <span className="text-sm text-gray-500">
              Mode: {quartoSettings.activeMode === 'simple' ? 'Simple' : 'Advanced'}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handlePreview}
              className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center"
            >
              <Eye className="h-4 w-4 mr-1" />
              Preview
            </button>

            <button
              onClick={saveQuartoSettings}
              disabled={isSaving}
              className="px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 flex items-center disabled:opacity-50"
            >
              <Save className="h-4 w-4 mr-1" />
              {isSaving ? 'Saving...' : 'Save Settings'}
            </button>

            <button
              onClick={handleExport}
              disabled={isExporting}
              className="px-4 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center disabled:opacity-50"
            >
              <Download className="h-4 w-4 mr-1" />
              {isExporting
                ? 'Exporting...'
                : `Export (${getActiveFormats().join(', ')})`}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex">
        {/* Editor Section */}
        <div className="flex-1 flex flex-col">
          {/* Quarto Controls */}
          <div className="border-b border-gray-200 bg-gray-50">
            <QuartoControls
              settings={quartoSettings}
              onSettingsChange={setQuartoSettings}
            />
          </div>

          {/* Content Editor */}
          <div className="flex-1 overflow-auto">
            <RichTextEditor content={content} onChange={onChange} />
          </div>
        </div>

        {/* Preview Panel (if shown) */}
        {showPreview && (
          <div className="w-1/2 border-l border-gray-200 flex flex-col">
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-2 flex items-center justify-between">
              <h3 className="font-medium text-gray-900">Preview</h3>
              <button
                onClick={() => setShowPreview(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ×
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4 bg-white">
              <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuartoEditor;