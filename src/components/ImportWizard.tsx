import React, { useState, useEffect } from 'react';
import { useImport } from '../hooks/useImport';
import { useStatusFeedback } from './StatusFeedback';
import type { 
  ImportConfig, 
  ImportSettings, 
  ImportPreview, 
  FileValidationResult,
  SupportedFileType 
} from '../hooks/useImport';

interface ImportWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onImportComplete?: (sessionId: string, sessionName: string) => void;
}

export function ImportWizard({ isOpen, onClose, onImportComplete }: ImportWizardProps) {
  const importHook = useImport();
  const statusFeedback = useStatusFeedback();
  
  const [currentStep, setCurrentStep] = useState<'select' | 'preview' | 'settings' | 'import'>('select');
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileValidation, setFileValidation] = useState<FileValidationResult | null>(null);
  const [importPreview, setImportPreview] = useState<ImportPreview | null>(null);
  const [importSettings, setImportSettings] = useState<ImportSettings | null>(null);
  const [customSessionName, setCustomSessionName] = useState<string>('');
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);

  useEffect(() => {
    if (isOpen) {
      importHook.loadConfig();
      importHook.loadSupportedTypes();
      setCurrentStep('select');
      setSelectedFile(null);
      setFileValidation(null);
      setImportPreview(null);
      setCustomSessionName('');
      setShowAdvancedSettings(false);
    }
  }, [isOpen, importHook]);

  useEffect(() => {
    if (importHook.config) {
      setImportSettings(importHook.config.default_import_settings);
    }
  }, [importHook.config]);

  const handleFileSelect = async () => {
    const filePath = await importHook.selectFile();
    if (filePath) {
      setSelectedFile(filePath);
      
      // Validate the selected file
      const validation = await importHook.validateFile(filePath);
      setFileValidation(validation);
      
      if (validation.is_valid) {
        // Generate preview
        const preview = await importHook.previewImport(filePath);
        setImportPreview(preview);
        
        if (preview) {
          setCustomSessionName(preview.estimated_session_structure.suggested_name);
          setCurrentStep('preview');
        }
      } else {
        statusFeedback.showError('Invalid File', validation.error_message || 'Unknown validation error');
      }
    }
  };

  const handleImport = async () => {
    if (!selectedFile || !importSettings) return;
    
    setCurrentStep('import');
    
    // Update session name template if custom name is provided
    const finalSettings: ImportSettings = {
      ...importSettings,
      session_name_template: customSessionName || importSettings.session_name_template
    };
    
    const result = await importHook.importFile(selectedFile, finalSettings, true);
    
    if (result && result.success) {
      statusFeedback.showSuccess(
        'Import Complete!',
        `Successfully imported ${result.imported_content.length} content items`,
        4000
      );
      
      if (onImportComplete && result.session_id) {
        onImportComplete(result.session_id, result.session_name);
      }
      
      onClose();
    } else {
      statusFeedback.showError(
        'Import Failed',
        result?.errors.join(', ') || 'Unknown import error'
      );
      setCurrentStep('preview');
    }
  };

  const getFileTypeDisplay = (fileType: SupportedFileType): string => {
    switch (fileType) {
      case SupportedFileType.PowerPoint:
        return 'PowerPoint Presentation';
      case SupportedFileType.Word:
        return 'Word Document';
      default:
        return 'Document';
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
        width: '90vw',
        height: '85vh',
        maxWidth: '900px',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '20px', color: '#1e293b' }}>
              📁 Import Content
            </h2>
            <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '14px' }}>
              Import existing PowerPoint and Word files into your curriculum
            </p>
          </div>
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

        {/* Progress Indicator */}
        <div style={{
          padding: '16px 24px',
          backgroundColor: '#f8fafc',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {['select', 'preview', 'import'].map((step, index) => (
              <React.Fragment key={step}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: currentStep === step ? '#3b82f6' : 
                                  ['select', 'preview'].indexOf(currentStep) > ['select', 'preview'].indexOf(step) ? '#10b981' : '#e5e7eb',
                  color: currentStep === step || ['select', 'preview'].indexOf(currentStep) > ['select', 'preview'].indexOf(step) ? 'white' : '#6b7280',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '14px',
                  fontWeight: '600'
                }}>
                  {step === 'select' ? '1' : step === 'preview' ? '2' : '3'}
                </div>
                {index < 2 && (
                  <div style={{
                    flex: 1,
                    height: '2px',
                    backgroundColor: ['select', 'preview'].indexOf(currentStep) > index ? '#10b981' : '#e5e7eb'
                  }} />
                )}
              </React.Fragment>
            ))}
          </div>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '8px',
            fontSize: '12px',
            color: '#64748b'
          }}>
            <span>Select File</span>
            <span>Preview Content</span>
            <span>Import</span>
          </div>
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflow: 'auto', padding: '24px' }}>
          {currentStep === 'select' && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '64px', marginBottom: '20px' }}>📁</div>
              <h3 style={{ fontSize: '18px', marginBottom: '12px', color: '#1e293b' }}>
                Select a File to Import
              </h3>
              <p style={{ color: '#64748b', marginBottom: '24px', maxWidth: '400px', margin: '0 auto 24px' }}>
                Choose a PowerPoint presentation (.pptx) or Word document (.docx) to import into your curriculum.
              </p>
              
              <button
                onClick={handleFileSelect}
                disabled={importHook.isImporting}
                style={{
                  padding: '12px 24px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: importHook.isImporting ? 'not-allowed' : 'pointer',
                  fontSize: '16px',
                  fontWeight: '500',
                  opacity: importHook.isImporting ? 0.7 : 1
                }}
              >
                {importHook.isImporting ? 'Processing...' : '📁 Choose File'}
              </button>

              {/* Supported File Types */}
              <div style={{ marginTop: '32px' }}>
                <h4 style={{ fontSize: '14px', color: '#374151', marginBottom: '16px' }}>
                  Supported File Types
                </h4>
                <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
                  {importHook.supportedTypes.map((type) => (
                    <div key={type.file_type} style={{
                      padding: '12px',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      textAlign: 'center',
                      minWidth: '120px'
                    }}>
                      <div style={{ fontSize: '24px', marginBottom: '4px' }}>{type.icon}</div>
                      <div style={{ fontSize: '12px', fontWeight: '500', color: '#374151' }}>
                        {type.display_name}
                      </div>
                      <div style={{ fontSize: '10px', color: '#6b7280' }}>
                        .{type.extensions.join(', .')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {currentStep === 'preview' && importPreview && fileValidation?.file_info && (
            <div>
              <h3 style={{ fontSize: '18px', marginBottom: '20px', color: '#1e293b' }}>
                📋 Import Preview
              </h3>

              {/* File Info */}
              <div style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '16px',
                marginBottom: '20px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                  <span style={{ fontSize: '24px' }}>
                    {importHook.getFileTypeIcon(fileValidation.file_info.file_type)}
                  </span>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '16px', color: '#1e293b' }}>
                      {fileValidation.file_info.filename}
                    </h4>
                    <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: '#64748b' }}>
                      {getFileTypeDisplay(fileValidation.file_info.file_type)} • {importHook.formatFileSize(fileValidation.file_info.file_size)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Session Name */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
                  Session Name
                </label>
                <input
                  type="text"
                  value={customSessionName}
                  onChange={(e) => setCustomSessionName(e.target.value)}
                  placeholder="Enter session name..."
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                />
              </div>

              {/* Detected Content */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '16px', marginBottom: '12px', color: '#1e293b' }}>
                  Detected Content Types
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {importPreview.detected_content_types.map((contentType, index) => (
                    <div key={index} style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      backgroundColor: '#f1f5f9',
                      borderRadius: '6px'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: '500', color: '#1e293b' }}>
                          {contentType.content_type}
                        </span>
                        <span style={{
                          fontSize: '11px',
                          padding: '2px 6px',
                          backgroundColor: contentType.confidence > 0.8 ? '#dcfce7' : '#fef3c7',
                          color: contentType.confidence > 0.8 ? '#166534' : '#92400e',
                          borderRadius: '10px'
                        }}>
                          {Math.round(contentType.confidence * 100)}% confident
                        </span>
                      </div>
                      <span style={{ fontSize: '12px', color: '#64748b' }}>
                        {contentType.count} items
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Content Outline */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '16px', marginBottom: '12px', color: '#1e293b' }}>
                  Content Structure
                </h4>
                <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '8px' }}>
                  Estimated Duration: {importPreview.estimated_session_structure.estimated_duration}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {importPreview.estimated_session_structure.content_outline.map((item, index) => (
                    <div key={index} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '6px 0'
                    }}>
                      <div style={{
                        width: '24px',
                        height: '24px',
                        backgroundColor: '#e2e8f0',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '10px',
                        color: '#64748b'
                      }}>
                        {item.order}
                      </div>
                      <div>
                        <div style={{ fontSize: '14px', fontWeight: '500', color: '#1e293b' }}>
                          {item.title}
                        </div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>
                          {item.content_type} • {item.description}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Warnings */}
              {importPreview.processing_warnings.length > 0 && (
                <div style={{
                  backgroundColor: '#fef3c7',
                  border: '1px solid #f59e0b',
                  borderRadius: '6px',
                  padding: '12px',
                  marginBottom: '20px'
                }}>
                  <h5 style={{ margin: '0 0 8px 0', color: '#92400e', fontSize: '14px' }}>
                    ⚠️ Import Warnings
                  </h5>
                  <ul style={{ margin: 0, paddingLeft: '16px', color: '#92400e', fontSize: '12px' }}>
                    {importPreview.processing_warnings.map((warning, index) => (
                      <li key={index}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Advanced Settings Toggle */}
              <div style={{ marginBottom: '20px' }}>
                <button
                  onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#3b82f6',
                    cursor: 'pointer',
                    fontSize: '14px',
                    textDecoration: 'underline'
                  }}
                >
                  {showAdvancedSettings ? '🔽' : '▶️'} Advanced Import Settings
                </button>

                {showAdvancedSettings && importSettings && (
                  <div style={{
                    marginTop: '12px',
                    padding: '16px',
                    backgroundColor: '#f8fafc',
                    borderRadius: '6px',
                    border: '1px solid #e2e8f0'
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <input
                          type="checkbox"
                          checked={importSettings.content_mapping.extract_speaker_notes}
                          onChange={(e) => setImportSettings({
                            ...importSettings,
                            content_mapping: {
                              ...importSettings.content_mapping,
                              extract_speaker_notes: e.target.checked
                            }
                          })}
                        />
                        <span style={{ fontSize: '14px' }}>Extract speaker notes</span>
                      </label>
                      
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <input
                          type="checkbox"
                          checked={importSettings.content_mapping.create_worksheets_from_exercises}
                          onChange={(e) => setImportSettings({
                            ...importSettings,
                            content_mapping: {
                              ...importSettings.content_mapping,
                              create_worksheets_from_exercises: e.target.checked
                            }
                          })}
                        />
                        <span style={{ fontSize: '14px' }}>Create worksheets from exercises</span>
                      </label>
                      
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <input
                          type="checkbox"
                          checked={importSettings.content_mapping.detect_quiz_questions}
                          onChange={(e) => setImportSettings({
                            ...importSettings,
                            content_mapping: {
                              ...importSettings.content_mapping,
                              detect_quiz_questions: e.target.checked
                            }
                          })}
                        />
                        <span style={{ fontSize: '14px' }}>Detect quiz questions</span>
                      </label>
                      
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <input
                          type="checkbox"
                          checked={importSettings.processing_options.preserve_slide_order}
                          onChange={(e) => setImportSettings({
                            ...importSettings,
                            processing_options: {
                              ...importSettings.processing_options,
                              preserve_slide_order: e.target.checked
                            }
                          })}
                        />
                        <span style={{ fontSize: '14px' }}>Preserve slide order</span>
                      </label>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {currentStep === 'import' && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '64px', marginBottom: '20px' }}>
                {importHook.isImporting ? '⏳' : '✅'}
              </div>
              
              <h3 style={{ fontSize: '18px', marginBottom: '12px', color: '#1e293b' }}>
                {importHook.isImporting ? 'Importing Content...' : 'Import Complete!'}
              </h3>
              
              {importHook.importProgress && (
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ marginBottom: '8px', fontSize: '14px', color: '#64748b' }}>
                    {importHook.getImportStepName(importHook.importProgress.current_step)}
                  </div>
                  <div style={{
                    width: '100%',
                    height: '8px',
                    backgroundColor: '#e5e7eb',
                    borderRadius: '4px',
                    overflow: 'hidden',
                    marginBottom: '8px'
                  }}>
                    <div style={{
                      width: `${importHook.importProgress.progress_percentage}%`,
                      height: '100%',
                      backgroundColor: '#3b82f6',
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>
                    {importHook.importProgress.current_item}
                    {importHook.importProgress.estimated_time_remaining && (
                      <span> • ~{importHook.importProgress.estimated_time_remaining}s remaining</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <button
            onClick={onClose}
            disabled={importHook.isImporting}
            style={{
              padding: '8px 16px',
              border: '1px solid #d1d5db',
              backgroundColor: 'white',
              color: '#374151',
              borderRadius: '6px',
              cursor: importHook.isImporting ? 'not-allowed' : 'pointer',
              opacity: importHook.isImporting ? 0.7 : 1
            }}
          >
            {currentStep === 'import' && !importHook.isImporting ? 'Close' : 'Cancel'}
          </button>

          <div style={{ display: 'flex', gap: '8px' }}>
            {currentStep === 'preview' && (
              <>
                <button
                  onClick={() => setCurrentStep('select')}
                  style={{
                    padding: '8px 16px',
                    border: '1px solid #d1d5db',
                    backgroundColor: 'white',
                    color: '#374151',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                >
                  ← Back
                </button>
                <button
                  onClick={handleImport}
                  disabled={!customSessionName.trim()}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: !customSessionName.trim() ? '#9ca3af' : '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: !customSessionName.trim() ? 'not-allowed' : 'pointer'
                  }}
                >
                  📁 Import Content
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}