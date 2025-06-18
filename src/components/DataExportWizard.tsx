import React, { useState, useEffect } from 'react';
import { useDataExport } from '../hooks/useDataExport';
import { useStatusFeedback } from './StatusFeedback';
import type { 
  ExportFormat, 
  ExportRequest, 
  ExportSessionFilter, 
  ExportOptions,
  ExportValidation 
} from '../hooks/useDataExport';

interface DataExportWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onExportComplete?: (result: any) => void;
}

export function DataExportWizard({ isOpen, onClose, onExportComplete }: DataExportWizardProps) {
  const dataExport = useDataExport();
  const statusFeedback = useStatusFeedback();
  
  const [currentStep, setCurrentStep] = useState<'format' | 'sessions' | 'options' | 'export'>('format');
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat | null>(null);
  const [sessionFilter, setSessionFilter] = useState<ExportSessionFilter>({ All: null });
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    compress: true,
    encrypt: false,
    split_large_files: true,
    max_file_size_mb: 100,
    include_thumbnails: true,
    generate_index: true,
  });
  const [outputPath, setOutputPath] = useState<string>('');
  const [validation, setValidation] = useState<ExportValidation | null>(null);
  const [selectedSessions, setSelectedSessions] = useState<string[]>([]);
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [recentCount, setRecentCount] = useState(10);

  useEffect(() => {
    if (isOpen) {
      dataExport.loadConfig();
      dataExport.loadAvailableFormats();
      setCurrentStep('format');
      setSelectedFormat(null);
      setSessionFilter({ All: null });
      setOutputPath('');
      setValidation(null);
    }
  }, [isOpen, dataExport]);

  const handleFormatSelect = (format: ExportFormat) => {
    setSelectedFormat(format);
    setCurrentStep('sessions');
  };

  const handleSessionFilterChange = (filter: ExportSessionFilter) => {
    setSessionFilter(filter);
  };

  const handleNextToOptions = () => {
    setCurrentStep('options');
  };

  const handleValidateAndExport = async () => {
    if (!selectedFormat || !outputPath) {
      statusFeedback.showWarning('Missing Information', 'Please select format and output path');
      return;
    }

    const request: ExportRequest = {
      format: selectedFormat,
      sessions: sessionFilter,
      content_types: [],
      include_attachments: true,
      include_history: true,
      output_path: outputPath,
      options: exportOptions,
    };

    // Validate request
    const validationResult = await dataExport.validateExportRequest(request);
    setValidation(validationResult);

    if (validationResult && !validationResult.is_valid) {
      statusFeedback.showError('Validation Failed', validationResult.errors.join(', '));
      return;
    }

    if (validationResult && validationResult.warnings.length > 0) {
      statusFeedback.showWarning('Export Warnings', validationResult.warnings.join(', '));
    }

    setCurrentStep('export');
    
    // Start export
    const result = await dataExport.exportData(request, true);
    
    if (result && result.success) {
      statusFeedback.showSuccess(
        'Export Complete!',
        `Successfully exported ${result.sessions_exported} sessions to ${result.output_path}`,
        5000
      );
      
      if (onExportComplete) {
        onExportComplete(result);
      }
      
      onClose();
    } else {
      statusFeedback.showError(
        'Export Failed',
        result?.errors.join(', ') || 'Unknown export error'
      );
      setCurrentStep('options');
    }
  };

  const handleSelectOutputPath = async () => {
    const extension = selectedFormat ? getFormatExtension(selectedFormat) : 'zip';
    const defaultFilename = `curriculum_export_${new Date().toISOString().split('T')[0]}.${extension}`;
    
    const path = await dataExport.selectOutputPath(defaultFilename);
    if (path) {
      setOutputPath(path);
    }
  };

  const getFormatExtension = (format: ExportFormat): string => {
    if (format.Archive) {
      switch (format.Archive) {
        case 'Zip': return 'zip';
        case 'Tar': return 'tar';
        case 'TarGz': return 'tar.gz';
        case 'SevenZip': return '7z';
        default: return 'zip';
      }
    } else if (format.Database) {
      switch (format.Database) {
        case 'JsonExport': return 'json';
        case 'SqliteBackup': return 'db';
        case 'CsvExport': return 'csv';
        default: return 'json';
      }
    } else if (format.Portable) {
      switch (format.Portable) {
        case 'CurriculumPack': return 'ccpack';
        case 'EducatorBundle': return 'edubundle';
        case 'MinimalExport': return 'ccmin';
        default: return 'ccpack';
      }
    }
    return 'zip';
  };

  const getStepProgress = () => {
    const steps = ['format', 'sessions', 'options', 'export'];
    const currentIndex = steps.indexOf(currentStep);
    return ((currentIndex + 1) / steps.length) * 100;
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
              📤 Data Export
            </h2>
            <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '14px' }}>
              Export your curriculum data for sharing and backup
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

        {/* Progress Bar */}
        <div style={{
          padding: '16px 24px',
          backgroundColor: '#f8fafc',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <div style={{
            width: '100%',
            height: '8px',
            backgroundColor: '#e5e7eb',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${getStepProgress()}%`,
              height: '100%',
              backgroundColor: '#3b82f6',
              transition: 'width 0.3s ease'
            }} />
          </div>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '8px',
            fontSize: '12px',
            color: '#64748b'
          }}>
            <span style={{ color: currentStep === 'format' ? '#3b82f6' : '#64748b' }}>
              1. Format
            </span>
            <span style={{ color: currentStep === 'sessions' ? '#3b82f6' : '#64748b' }}>
              2. Sessions
            </span>
            <span style={{ color: currentStep === 'options' ? '#3b82f6' : '#64748b' }}>
              3. Options
            </span>
            <span style={{ color: currentStep === 'export' ? '#3b82f6' : '#64748b' }}>
              4. Export
            </span>
          </div>
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflow: 'auto', padding: '24px' }}>
          {currentStep === 'format' && (
            <div>
              <h3 style={{ fontSize: '18px', marginBottom: '16px', color: '#1e293b' }}>
                Choose Export Format
              </h3>
              <p style={{ color: '#64748b', marginBottom: '24px' }}>
                Select the format that best suits your needs for sharing or backup.
              </p>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
                {dataExport.availableFormats.map((formatInfo, index) => (
                  <div
                    key={index}
                    onClick={() => handleFormatSelect(formatInfo.format)}
                    style={{
                      border: '2px solid #e5e7eb',
                      borderRadius: '8px',
                      padding: '16px',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      backgroundColor: 'white'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = '#3b82f6';
                      e.currentTarget.style.backgroundColor = '#f0f9ff';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = '#e5e7eb';
                      e.currentTarget.style.backgroundColor = 'white';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '24px' }}>
                        {dataExport.getFormatIcon(formatInfo.format)}
                      </span>
                      <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#1e293b' }}>
                        {formatInfo.display_name}
                      </h4>
                    </div>
                    <p style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#64748b' }}>
                      {formatInfo.description}
                    </p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {formatInfo.recommended_for.map((use, idx) => (
                        <span
                          key={idx}
                          style={{
                            fontSize: '11px',
                            padding: '2px 6px',
                            backgroundColor: '#e0e7ff',
                            color: '#3730a3',
                            borderRadius: '10px'
                          }}
                        >
                          {use}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {currentStep === 'sessions' && (
            <div>
              <h3 style={{ fontSize: '18px', marginBottom: '16px', color: '#1e293b' }}>
                Select Sessions to Export
              </h3>
              <p style={{ color: '#64748b', marginBottom: '24px' }}>
                Choose which sessions you want to include in the export.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {/* Export All Sessions */}
                <label style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '16px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  cursor: 'pointer'
                }}>
                  <input
                    type="radio"
                    name="sessionFilter"
                    checked={sessionFilter.All !== undefined}
                    onChange={() => handleSessionFilterChange({ All: null })}
                    style={{ marginTop: '2px' }}
                  />
                  <div>
                    <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', fontWeight: '600' }}>
                      All Sessions
                    </h4>
                    <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
                      Export all sessions in your curriculum database
                    </p>
                  </div>
                </label>

                {/* Recent Sessions */}
                <label style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '16px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  cursor: 'pointer'
                }}>
                  <input
                    type="radio"
                    name="sessionFilter"
                    checked={sessionFilter.RecentSessions !== undefined}
                    onChange={() => handleSessionFilterChange({ RecentSessions: recentCount })}
                    style={{ marginTop: '2px' }}
                  />
                  <div style={{ flex: 1 }}>
                    <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', fontWeight: '600' }}>
                      Recent Sessions
                    </h4>
                    <p style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#64748b' }}>
                      Export the most recently created sessions
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '14px' }}>Export last</span>
                      <input
                        type="number"
                        min="1"
                        max="100"
                        value={recentCount}
                        onChange={(e) => {
                          setRecentCount(parseInt(e.target.value) || 10);
                          if (sessionFilter.RecentSessions !== undefined) {
                            handleSessionFilterChange({ RecentSessions: parseInt(e.target.value) || 10 });
                          }
                        }}
                        style={{
                          width: '60px',
                          padding: '4px 8px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          fontSize: '14px'
                        }}
                      />
                      <span style={{ fontSize: '14px' }}>sessions</span>
                    </div>
                  </div>
                </label>

                {/* Date Range */}
                <label style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '16px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  cursor: 'pointer'
                }}>
                  <input
                    type="radio"
                    name="sessionFilter"
                    checked={sessionFilter.DateRange !== undefined}
                    onChange={() => handleSessionFilterChange({ 
                      DateRange: { start: dateRange.start, end: dateRange.end } 
                    })}
                    style={{ marginTop: '2px' }}
                  />
                  <div style={{ flex: 1 }}>
                    <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', fontWeight: '600' }}>
                      Date Range
                    </h4>
                    <p style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#64748b' }}>
                      Export sessions created within a specific date range
                    </p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px' }}>From</label>
                        <input
                          type="date"
                          value={dateRange.start}
                          onChange={(e) => {
                            setDateRange(prev => ({ ...prev, start: e.target.value }));
                            if (sessionFilter.DateRange !== undefined) {
                              handleSessionFilterChange({ 
                                DateRange: { start: e.target.value, end: dateRange.end } 
                              });
                            }
                          }}
                          style={{
                            width: '100%',
                            padding: '6px 8px',
                            border: '1px solid #d1d5db',
                            borderRadius: '4px',
                            fontSize: '14px'
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px' }}>To</label>
                        <input
                          type="date"
                          value={dateRange.end}
                          onChange={(e) => {
                            setDateRange(prev => ({ ...prev, end: e.target.value }));
                            if (sessionFilter.DateRange !== undefined) {
                              handleSessionFilterChange({ 
                                DateRange: { start: dateRange.start, end: e.target.value } 
                              });
                            }
                          }}
                          style={{
                            width: '100%',
                            padding: '6px 8px',
                            border: '1px solid #d1d5db',
                            borderRadius: '4px',
                            fontSize: '14px'
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </label>
              </div>
            </div>
          )}

          {currentStep === 'options' && (
            <div>
              <h3 style={{ fontSize: '18px', marginBottom: '16px', color: '#1e293b' }}>
                Export Options
              </h3>
              <p style={{ color: '#64748b', marginBottom: '24px' }}>
                Configure how your data will be exported and packaged.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                {/* Output Path */}
                <div>
                  <label style={{ display: 'block', fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>
                    Output Location
                  </label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      type="text"
                      value={outputPath}
                      onChange={(e) => setOutputPath(e.target.value)}
                      placeholder="Choose where to save the export..."
                      style={{
                        flex: 1,
                        padding: '8px 12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        fontSize: '14px'
                      }}
                    />
                    <button
                      onClick={handleSelectOutputPath}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '14px'
                      }}
                    >
                      Browse
                    </button>
                  </div>
                </div>

                {/* Compression Options */}
                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
                    Compression
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={exportOptions.compress}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          compress: e.target.checked
                        }))}
                      />
                      <span style={{ fontSize: '14px' }}>Enable compression</span>
                    </label>
                    
                    {exportOptions.compress && (
                      <div style={{ marginLeft: '24px' }}>
                        <label style={{ display: 'block', fontSize: '14px', marginBottom: '4px' }}>
                          Compression Level
                        </label>
                        <input
                          type="range"
                          min="1"
                          max="9"
                          value={exportOptions.compression_level || 6}
                          onChange={(e) => setExportOptions(prev => ({
                            ...prev,
                            compression_level: parseInt(e.target.value)
                          }))}
                          style={{ width: '200px' }}
                        />
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '200px', fontSize: '12px', color: '#64748b' }}>
                          <span>Fast</span>
                          <span>Balanced</span>
                          <span>Best</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Security Options */}
                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
                    Security
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={exportOptions.encrypt}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          encrypt: e.target.checked
                        }))}
                      />
                      <span style={{ fontSize: '14px' }}>Password protect export</span>
                    </label>
                    
                    {exportOptions.encrypt && (
                      <div style={{ marginLeft: '24px' }}>
                        <label style={{ display: 'block', fontSize: '14px', marginBottom: '4px' }}>
                          Password
                        </label>
                        <input
                          type="password"
                          value={exportOptions.password || ''}
                          onChange={(e) => setExportOptions(prev => ({
                            ...prev,
                            password: e.target.value
                          }))}
                          placeholder="Enter password..."
                          style={{
                            width: '200px',
                            padding: '6px 8px',
                            border: '1px solid #d1d5db',
                            borderRadius: '4px',
                            fontSize: '14px'
                          }}
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Additional Options */}
                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
                    Content Options
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={exportOptions.include_thumbnails}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          include_thumbnails: e.target.checked
                        }))}
                      />
                      <span style={{ fontSize: '14px' }}>Include thumbnails and previews</span>
                    </label>
                    
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={exportOptions.generate_index}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          generate_index: e.target.checked
                        }))}
                      />
                      <span style={{ fontSize: '14px' }}>Generate content index</span>
                    </label>
                    
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={exportOptions.split_large_files}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          split_large_files: e.target.checked
                        }))}
                      />
                      <span style={{ fontSize: '14px' }}>Split large files for better compatibility</span>
                    </label>
                  </div>
                </div>

                {/* Validation Results */}
                {validation && (
                  <div style={{
                    padding: '16px',
                    backgroundColor: validation.is_valid ? '#f0f9ff' : '#fef2f2',
                    border: `1px solid ${validation.is_valid ? '#3b82f6' : '#ef4444'}`,
                    borderRadius: '8px'
                  }}>
                    <h4 style={{ 
                      margin: '0 0 8px 0', 
                      color: validation.is_valid ? '#1e40af' : '#dc2626',
                      fontSize: '14px',
                      fontWeight: '600'
                    }}>
                      Export Validation
                    </h4>
                    
                    {validation.errors.length > 0 && (
                      <div style={{ marginBottom: '8px' }}>
                        <strong style={{ color: '#dc2626', fontSize: '12px' }}>Errors:</strong>
                        <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                          {validation.errors.map((error, idx) => (
                            <li key={idx} style={{ fontSize: '12px', color: '#dc2626' }}>{error}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {validation.warnings.length > 0 && (
                      <div style={{ marginBottom: '8px' }}>
                        <strong style={{ color: '#d97706', fontSize: '12px' }}>Warnings:</strong>
                        <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                          {validation.warnings.map((warning, idx) => (
                            <li key={idx} style={{ fontSize: '12px', color: '#d97706' }}>{warning}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    <div style={{ fontSize: '12px', color: '#64748b' }}>
                      Estimated size: {validation.estimated_size_mb} MB • 
                      Estimated time: {validation.estimated_time_minutes} minutes
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {currentStep === 'export' && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '64px', marginBottom: '20px' }}>
                {dataExport.isExporting ? '⏳' : '✅'}
              </div>
              
              <h3 style={{ fontSize: '18px', marginBottom: '12px', color: '#1e293b' }}>
                {dataExport.isExporting ? 'Exporting Data...' : 'Export Complete!'}
              </h3>
              
              {dataExport.exportProgress && (
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ marginBottom: '8px', fontSize: '14px', color: '#64748b' }}>
                    {dataExport.getStepDisplayName(dataExport.exportProgress.current_step)}
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
                      width: `${dataExport.exportProgress.progress_percentage}%`,
                      height: '100%',
                      backgroundColor: '#3b82f6',
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>
                    {dataExport.exportProgress.current_item}
                    {dataExport.exportProgress.estimated_time_remaining && (
                      <span> • ~{dataExport.exportProgress.estimated_time_remaining}s remaining</span>
                    )}
                  </div>
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px' }}>
                    {dataExport.exportProgress.items_processed} / {dataExport.exportProgress.total_items} items processed
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
            disabled={dataExport.isExporting}
            style={{
              padding: '8px 16px',
              border: '1px solid #d1d5db',
              backgroundColor: 'white',
              color: '#374151',
              borderRadius: '6px',
              cursor: dataExport.isExporting ? 'not-allowed' : 'pointer',
              opacity: dataExport.isExporting ? 0.7 : 1
            }}
          >
            {currentStep === 'export' && !dataExport.isExporting ? 'Close' : 'Cancel'}
          </button>

          <div style={{ display: 'flex', gap: '8px' }}>
            {currentStep === 'sessions' && (
              <>
                <button
                  onClick={() => setCurrentStep('format')}
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
                  onClick={handleNextToOptions}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                >
                  Next →
                </button>
              </>
            )}
            
            {currentStep === 'options' && (
              <>
                <button
                  onClick={() => setCurrentStep('sessions')}
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
                  onClick={handleValidateAndExport}
                  disabled={!selectedFormat || !outputPath}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: (!selectedFormat || !outputPath) ? '#9ca3af' : '#059669',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: (!selectedFormat || !outputPath) ? 'not-allowed' : 'pointer'
                  }}
                >
                  📤 Start Export
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}