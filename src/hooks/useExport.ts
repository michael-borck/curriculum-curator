// React Hook for Export Operations
// Bridges frontend UI to Tauri backend export commands

import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface ExportFormat {
  format: string;
  display_name: string;
  extension: string;
  available: boolean;
}

export interface ExportOptions {
  format: string;
  output_path: string;
  include_metadata?: boolean;
  template_name?: string;
}

export interface ExportResult {
  success: boolean;
  output_path: string;
  file_size?: number;
  format: string;
  message: string;
}

export interface ExportHookState {
  supportedFormats: ExportFormat[];
  isExporting: boolean;
  error: string | null;
  lastExport: ExportResult | null;
}

export function useExport() {
  const [state, setState] = useState<ExportHookState>({
    supportedFormats: [],
    isExporting: false,
    error: null,
    lastExport: null,
  });

  const updateState = useCallback((updates: Partial<ExportHookState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // Load supported export formats
  const loadSupportedFormats = useCallback(async (): Promise<void> => {
    try {
      const formats: ExportFormat[] = await invoke('get_supported_export_formats');
      updateState({ supportedFormats: formats, error: null });
    } catch (error) {
      updateState({ 
        error: `Failed to load export formats: ${error}`,
        supportedFormats: []
      });
    }
  }, [updateState]);

  // Validate export path
  const validateExportPath = useCallback(async (path: string, format: string): Promise<boolean> => {
    try {
      return await invoke('validate_export_path', { path, format });
    } catch (error) {
      updateState({ error: `Path validation failed: ${error}` });
      return false;
    }
  }, [updateState]);

  // Export content from a session
  const exportContent = useCallback(async (
    sessionId: string,
    options: ExportOptions
  ): Promise<ExportResult | null> => {
    updateState({ isExporting: true, error: null });

    try {
      const result: ExportResult = await invoke('export_content', {
        session_id: sessionId,
        format: options.format,
        output_path: options.output_path,
        include_metadata: options.include_metadata ?? true,
        template_name: options.template_name,
      });

      updateState({ 
        lastExport: result, 
        isExporting: false 
      });

      return result;
    } catch (error) {
      const errorMessage = `Export failed: ${error}`;
      updateState({ 
        error: errorMessage, 
        isExporting: false 
      });
      return null;
    }
  }, [updateState]);

  // Get default file extension for a format
  const getDefaultExtension = useCallback((format: string): string => {
    const formatInfo = state.supportedFormats.find(f => 
      f.format.toLowerCase() === format.toLowerCase()
    );
    return formatInfo?.extension || 'txt';
  }, [state.supportedFormats]);

  // Generate a suggested filename based on session and format
  const suggestFileName = useCallback((
    sessionName: string, 
    format: string,
    timestamp?: Date
  ): string => {
    const extension = getDefaultExtension(format);
    const sanitizedName = sessionName.replace(/[^a-zA-Z0-9-_]/g, '_');
    const dateStr = timestamp ? 
      timestamp.toISOString().split('T')[0] : 
      new Date().toISOString().split('T')[0];
    
    return `${sanitizedName}_${dateStr}.${extension}`;
  }, [getDefaultExtension]);

  // Get available formats (only those that are implemented)
  const getAvailableFormats = useCallback((): ExportFormat[] => {
    return state.supportedFormats.filter(format => format.available);
  }, [state.supportedFormats]);

  // Quick export with default settings (Markdown format)
  const quickExport = useCallback(async (
    sessionId: string,
    outputDir: string,
    sessionName?: string
  ): Promise<ExportResult | null> => {
    const fileName = suggestFileName(sessionName || 'curriculum_export', 'Markdown');
    const outputPath = `${outputDir}/${fileName}`;

    return exportContent(sessionId, {
      format: 'Markdown',
      output_path: outputPath,
      include_metadata: true,
    });
  }, [exportContent, suggestFileName]);

  // Batch export multiple sessions
  const batchExport = useCallback(async (
    sessionIds: string[],
    outputDir: string,
    format: string = 'Markdown'
  ): Promise<(ExportResult | null)[]> => {
    const results: (ExportResult | null)[] = [];

    for (let i = 0; i < sessionIds.length; i++) {
      const sessionId = sessionIds[i];
      const fileName = suggestFileName(`session_${i + 1}`, format);
      const outputPath = `${outputDir}/${fileName}`;

      const result = await exportContent(sessionId, {
        format,
        output_path: outputPath,
        include_metadata: true,
      });

      results.push(result);
    }

    return results;
  }, [exportContent, suggestFileName]);

  // Clear any errors
  const clearError = useCallback(() => {
    updateState({ error: null });
  }, [updateState]);

  // Reset state
  const reset = useCallback(() => {
    setState({
      supportedFormats: [],
      isExporting: false,
      error: null,
      lastExport: null,
    });
  }, []);

  return {
    // State
    ...state,
    
    // Actions
    loadSupportedFormats,
    validateExportPath,
    exportContent,
    quickExport,
    batchExport,
    clearError,
    reset,
    
    // Utilities
    getDefaultExtension,
    suggestFileName,
    getAvailableFormats,
    
    // Computed properties
    hasAvailableFormats: state.supportedFormats.some(f => f.available),
    isMarkdownSupported: state.supportedFormats.some(f => 
      f.format === 'Markdown' && f.available
    ),
  };
}