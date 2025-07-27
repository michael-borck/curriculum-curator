import React, { useState } from 'react';
import { useImport } from '../hooks/useImport';
import { useStatusFeedback } from './StatusFeedback';
import type { ImportedContent, FileValidationResult, ImportPreview } from '../hooks/useImport';

interface ImportWizardProps {
  onImportComplete?: (content: ImportedContent[]) => void;
}

export function ImportWizard({ onImportComplete }: ImportWizardProps) {
  const importHook = useImport();
  const statusFeedback = useStatusFeedback();
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileValidation, setFileValidation] = useState<FileValidationResult | null>(null);
  const [importPreview, setImportPreview] = useState<ImportPreview | null>(null);
  const [isImporting, setIsImporting] = useState(false);

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
      } else {
        statusFeedback.showError('Invalid File', validation.error_message || 'Unknown validation error');
      }
    }
  };

  const handleImport = async () => {
    if (!selectedFile || !importHook.config) return;
    
    setIsImporting(true);
    
    try {
      const result = await importHook.importFile(
        selectedFile, 
        importHook.config.default_import_settings, 
        false // No progress tracking for simplified version
      );
      
      if (result && result.success) {
        statusFeedback.showSuccess(
          'Import Complete!',
          `Successfully imported ${result.imported_content.length} content items`
        );
        
        onImportComplete?.(result.imported_content);
      } else {
        statusFeedback.showError(
          'Import Failed',
          result?.errors.join(', ') || 'Unknown import error'
        );
      }
    } finally {
      setIsImporting(false);
    }
  };

  React.useEffect(() => {
    importHook.loadConfig();
    importHook.loadSupportedTypes();
  }, []);

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      border: '1px solid #e5e7eb',
      padding: '24px'
    }}>
      <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
        📁 Import Content
      </h3>
      
      {!selectedFile ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📁</div>
          <p style={{ color: '#6b7280', marginBottom: '24px' }}>
            Choose a PowerPoint (.pptx) or Word (.docx) file to import
          </p>
          <button
            onClick={handleFileSelect}
            style={{
              padding: '12px 24px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer'
            }}
          >
            Select File
          </button>
        </div>
      ) : (
        <div>
          {/* File Info */}
          {fileValidation?.file_info && (
            <div style={{
              backgroundColor: '#f9fafb',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              padding: '12px',
              marginBottom: '16px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '24px' }}>
                  {importHook.getFileTypeIcon(fileValidation.file_info.file_type)}
                </span>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: '500' }}>
                    {fileValidation.file_info.filename}
                  </div>
                  <div style={{ fontSize: '12px', color: '#6b7280' }}>
                    {importHook.formatFileSize(fileValidation.file_info.file_size)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Preview */}
          {importPreview && (
            <div style={{ marginBottom: '16px' }}>
              <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                Content Preview
              </h4>
              <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '8px' }}>
                • {importPreview.total_content_items} content items detected<br />
                • Estimated duration: {importPreview.estimated_session_structure.estimated_duration}
              </div>
              
              {/* Content Types */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
                {importPreview.detected_content_types.map((type, index) => (
                  <span key={index} style={{
                    fontSize: '12px',
                    padding: '4px 8px',
                    backgroundColor: '#e0e7ff',
                    color: '#3730a3',
                    borderRadius: '12px'
                  }}>
                    {type.content_type} ({type.count})
                  </span>
                ))}
              </div>

              {/* Warnings */}
              {importPreview.processing_warnings.length > 0 && (
                <div style={{
                  backgroundColor: '#fef3c7',
                  border: '1px solid #f59e0b',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  fontSize: '12px',
                  color: '#92400e'
                }}>
                  ⚠️ {importPreview.processing_warnings.length} warnings
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <button
              onClick={() => {
                setSelectedFile(null);
                setFileValidation(null);
                setImportPreview(null);
              }}
              disabled={isImporting}
              style={{
                padding: '8px 16px',
                backgroundColor: 'white',
                color: '#6b7280',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                fontSize: '14px',
                cursor: isImporting ? 'not-allowed' : 'pointer',
                opacity: isImporting ? 0.6 : 1
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleImport}
              disabled={!fileValidation?.is_valid || isImporting}
              style={{
                padding: '8px 16px',
                backgroundColor: fileValidation?.is_valid && !isImporting ? '#10b981' : '#9ca3af',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: fileValidation?.is_valid && !isImporting ? 'pointer' : 'not-allowed'
              }}
            >
              {isImporting ? 'Importing...' : 'Import File'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
