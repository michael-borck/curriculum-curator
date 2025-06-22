import React, { useState, useEffect } from 'react';
import { useFileOperations } from '../hooks/useFileOperations';
import { useStatusFeedback } from './StatusFeedback';

interface FileOperationsProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId?: string;
  mode?: 'save' | 'export' | 'both';
}

export function FileOperations({ 
  isOpen, 
  onClose, 
  sessionId,
  mode = 'both' 
}: FileOperationsProps) {
  const fileOps = useFileOperations();
  const statusFeedback = useStatusFeedback();
  const [activeTab, setActiveTab] = useState<'save' | 'export'>('save');
  const [supportedFormats, setSupportedFormats] = useState<string[]>([]);
  const [selectedFormat, setSelectedFormat] = useState('Markdown');
  const [selectedTemplate, setSelectedTemplate] = useState('default');
  const [exportOptions, setExportOptions] = useState({
    includeMetadata: true,
    includeBranding: false,
    compress: false
  });

  useEffect(() => {
    if (isOpen) {
      fileOps.getSupportedFormats().then(setSupportedFormats);
    }
  }, [isOpen, fileOps]);

  useEffect(() => {
    if (mode === 'save') setActiveTab('save');
    else if (mode === 'export') setActiveTab('export');
  }, [mode]);

  const handleSaveSession = async () => {
    if (!sessionId) {
      statusFeedback.showError('No Session', 'No active session to save');
      return;
    }

    const result = await fileOps.saveSession(sessionId, {
      include_content: true,
      include_metadata: exportOptions.includeMetadata,
      compress: exportOptions.compress
    });

    if (result.success) {
      statusFeedback.showSuccess(
        'Session Saved',
        `Session saved to ${result.output_path}`,
        4000
      );
      onClose();
    } else {
      statusFeedback.showError(
        'Save Failed',
        result.error || 'Failed to save session'
      );
    }
  };

  const handleExportContent = async () => {
    if (!sessionId) {
      statusFeedback.showError('No Session', 'No active session to export');
      return;
    }

    const result = await fileOps.exportContent(sessionId, {
      format: selectedFormat,
      include_metadata: exportOptions.includeMetadata,
      template_name: selectedTemplate !== 'default' ? selectedTemplate : undefined,
      ...(exportOptions.includeBranding && {
        branding: {
          color_primary: '#3b82f6',
          color_secondary: '#1e40af'
        }
      })
    });

    if (result.success) {
      statusFeedback.showSuccess(
        'Export Complete',
        `Content exported to ${result.output_path}`,
        5000
      );
      onClose();
    } else {
      statusFeedback.showError(
        'Export Failed',
        result.error || 'Failed to export content'
      );
    }
  };

  const handleLoadSession = async () => {
    const result = await fileOps.loadSession();

    if (result.success) {
      statusFeedback.showSuccess(
        'Session Loaded',
        `Loaded session ${result.sessionId}`,
        3000
      );
      onClose();
      // TODO: Navigate to loaded session
    } else {
      statusFeedback.showError(
        'Load Failed',
        result.error || 'Failed to load session'
      );
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '24px',
        maxWidth: '500px',
        width: '90%',
        maxHeight: '80vh',
        overflow: 'auto',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px'
        }}>
          <h2 style={{ margin: 0, fontSize: '20px', color: '#1e293b' }}>
            File Operations
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#6b7280'
            }}
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        {mode === 'both' && (
          <div style={{
            display: 'flex',
            gap: '4px',
            backgroundColor: '#f1f5f9',
            padding: '4px',
            borderRadius: '8px',
            marginBottom: '20px'
          }}>
            <button
              onClick={() => setActiveTab('save')}
              style={{
                flex: 1,
                padding: '8px 16px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: activeTab === 'save' ? 'white' : 'transparent',
                color: activeTab === 'save' ? '#3b82f6' : '#64748b',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              💾 Save Session
            </button>
            <button
              onClick={() => setActiveTab('export')}
              style={{
                flex: 1,
                padding: '8px 16px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: activeTab === 'export' ? 'white' : 'transparent',
                color: activeTab === 'export' ? '#3b82f6' : '#64748b',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              📤 Export Content
            </button>
          </div>
        )}

        {/* Content */}
        {(activeTab === 'save' || mode === 'save') && (
          <div>
            <h3 style={{ fontSize: '16px', marginBottom: '16px', color: '#1e293b' }}>
              Save Current Session
            </h3>
            <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '20px' }}>
              Save your current session including all content and settings for later use.
            </p>

            {/* Save Options */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '8px',
                cursor: 'pointer'
              }}>
                <input
                  type="checkbox"
                  checked={exportOptions.includeMetadata}
                  onChange={(e) => setExportOptions(prev => ({
                    ...prev,
                    includeMetadata: e.target.checked
                  }))}
                />
                <span style={{ fontSize: '14px' }}>Include metadata and settings</span>
              </label>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer'
              }}>
                <input
                  type="checkbox"
                  checked={exportOptions.compress}
                  onChange={(e) => setExportOptions(prev => ({
                    ...prev,
                    compress: e.target.checked
                  }))}
                />
                <span style={{ fontSize: '14px' }}>Compress file for smaller size</span>
              </label>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={handleLoadSession}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  backgroundColor: '#f3f4f6',
                  color: '#374151',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                📁 Load Session
              </button>
              <button
                onClick={handleSaveSession}
                disabled={fileOps.isOperating || !sessionId}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: 'none',
                  backgroundColor: fileOps.isOperating || !sessionId ? '#9ca3af' : '#3b82f6',
                  color: 'white',
                  borderRadius: '8px',
                  cursor: fileOps.isOperating || !sessionId ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                {fileOps.isOperating ? '💾 Saving...' : '💾 Save Session'}
              </button>
            </div>
          </div>
        )}

        {(activeTab === 'export' || mode === 'export') && (
          <div>
            <h3 style={{ fontSize: '16px', marginBottom: '16px', color: '#1e293b' }}>
              Export Content
            </h3>
            <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '20px' }}>
              Export your generated content in various formats for sharing or printing.
            </p>

            {/* Format Selection */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{
                display: 'block',
                fontSize: '14px',
                fontWeight: '500',
                marginBottom: '4px'
              }}>
                Export Format:
              </label>
              <select
                value={selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              >
                {supportedFormats.map(format => (
                  <option key={format} value={format}>
                    {format}
                  </option>
                ))}
              </select>
            </div>

            {/* Template Selection for HTML */}
            {selectedFormat === 'HTML' && (
              <div style={{ marginBottom: '16px' }}>
                <label style={{
                  display: 'block',
                  fontSize: '14px',
                  fontWeight: '500',
                  marginBottom: '4px'
                }}>
                  Template:
                </label>
                <select
                  value={selectedTemplate}
                  onChange={(e) => setSelectedTemplate(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                >
                  <option value="default">Default</option>
                  <option value="professional">Professional</option>
                  <option value="academic">Academic</option>
                  <option value="minimal">Minimal</option>
                  <option value="presentation">Presentation</option>
                </select>
              </div>
            )}

            {/* Export Options */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '8px',
                cursor: 'pointer'
              }}>
                <input
                  type="checkbox"
                  checked={exportOptions.includeMetadata}
                  onChange={(e) => setExportOptions(prev => ({
                    ...prev,
                    includeMetadata: e.target.checked
                  }))}
                />
                <span style={{ fontSize: '14px' }}>Include metadata and timestamps</span>
              </label>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer'
              }}>
                <input
                  type="checkbox"
                  checked={exportOptions.includeBranding}
                  onChange={(e) => setExportOptions(prev => ({
                    ...prev,
                    includeBranding: e.target.checked
                  }))}
                />
                <span style={{ fontSize: '14px' }}>Apply custom branding and colors</span>
              </label>
            </div>

            {/* Export Action */}
            <button
              onClick={handleExportContent}
              disabled={fileOps.isOperating || !sessionId}
              style={{
                width: '100%',
                padding: '12px',
                border: 'none',
                backgroundColor: fileOps.isOperating || !sessionId ? '#9ca3af' : '#059669',
                color: 'white',
                borderRadius: '8px',
                cursor: fileOps.isOperating || !sessionId ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              {fileOps.isOperating ? '📤 Exporting...' : `📤 Export as ${selectedFormat}`}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}