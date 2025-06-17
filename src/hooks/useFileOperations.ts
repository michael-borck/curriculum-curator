import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { save, open } from '@tauri-apps/api/dialog';

interface ExportOptions {
  format: string;
  output_path?: string;
  include_metadata?: boolean;
  template_name?: string;
  branding?: {
    logo_path?: string;
    color_primary?: string;
    color_secondary?: string;
  };
}

interface SaveSessionOptions {
  format?: string;
  include_content?: boolean;
  include_metadata?: boolean;
  compress?: boolean;
}

interface FileOperationResult {
  success: boolean;
  output_path?: string;
  message?: string;
  error?: string;
}

export function useFileOperations() {
  const [isOperating, setIsOperating] = useState(false);
  const [lastOperation, setLastOperation] = useState<string | null>(null);

  const saveSession = useCallback(async (
    sessionId: string,
    options: SaveSessionOptions = {}
  ): Promise<FileOperationResult> => {
    setIsOperating(true);
    setLastOperation('save');
    
    try {
      // Get suggested filename
      const suggestedFilename = await invoke<string>('get_suggested_filename', {
        sessionId,
        format: options.format || 'json'
      });

      // Show save dialog
      const filePath = await save({
        title: 'Save Session',
        defaultPath: suggestedFilename,
        filters: [
          {
            name: 'Session Files',
            extensions: ['json', 'ccur'] // .ccur for Curriculum Curator files
          },
          {
            name: 'All Files',
            extensions: ['*']
          }
        ]
      });

      if (!filePath) {
        return { success: false, message: 'Save cancelled by user' };
      }

      // Save the session
      const result = await invoke<FileOperationResult>('save_session_to_file', {
        sessionId,
        filePath,
        options
      });

      return result;
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    } finally {
      setIsOperating(false);
      setLastOperation(null);
    }
  }, []);

  const loadSession = useCallback(async (): Promise<{
    success: boolean;
    sessionId?: string;
    error?: string;
  }> => {
    setIsOperating(true);
    setLastOperation('load');

    try {
      // Show open dialog
      const filePath = await open({
        title: 'Open Session',
        multiple: false,
        filters: [
          {
            name: 'Session Files',
            extensions: ['json', 'ccur']
          },
          {
            name: 'All Files',
            extensions: ['*']
          }
        ]
      });

      if (!filePath || Array.isArray(filePath)) {
        return { success: false, error: 'No file selected or invalid selection' };
      }

      // Load the session
      const result = await invoke<{ session_id: string }>('load_session_from_file', {
        filePath
      });

      return {
        success: true,
        sessionId: result.session_id
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to load session'
      };
    } finally {
      setIsOperating(false);
      setLastOperation(null);
    }
  }, []);

  const exportContent = useCallback(async (
    sessionId: string,
    options: ExportOptions
  ): Promise<FileOperationResult> => {
    setIsOperating(true);
    setLastOperation('export');

    try {
      // Get suggested filename based on format
      const suggestedFilename = await invoke<string>('get_suggested_filename', {
        sessionId,
        format: options.format.toLowerCase()
      });

      // Determine file extension based on format
      const getExtension = (format: string): string => {
        switch (format.toLowerCase()) {
          case 'markdown': return 'md';
          case 'html': return 'html';
          case 'pdf': return 'pdf';
          case 'powerpoint': return 'pptx';
          case 'word': return 'docx';
          default: return 'txt';
        }
      };

      const extension = getExtension(options.format);
      
      // Show save dialog if no output path provided
      let outputPath = options.output_path;
      if (!outputPath) {
        outputPath = await save({
          title: `Export as ${options.format}`,
          defaultPath: suggestedFilename,
          filters: [
            {
              name: `${options.format} Files`,
              extensions: [extension]
            },
            {
              name: 'All Files',
              extensions: ['*']
            }
          ]
        });

        if (!outputPath) {
          return { success: false, message: 'Export cancelled by user' };
        }
      }

      // Export the content
      const result = await invoke<FileOperationResult>('export_session_content', {
        sessionId,
        options: {
          ...options,
          output_path: outputPath
        }
      });

      return result;
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Export failed'
      };
    } finally {
      setIsOperating(false);
      setLastOperation(null);
    }
  }, []);

  const getSupportedFormats = useCallback(async (): Promise<string[]> => {
    try {
      return await invoke<string[]>('get_supported_export_formats');
    } catch (error) {
      console.error('Failed to get supported formats:', error);
      return ['Markdown', 'HTML', 'PDF']; // fallback
    }
  }, []);

  const getStorageInfo = useCallback(async () => {
    try {
      return await invoke('get_storage_statistics');
    } catch (error) {
      console.error('Failed to get storage info:', error);
      return null;
    }
  }, []);

  const listStorageFiles = useCallback(async (filter?: {
    file_type?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) => {
    try {
      return await invoke('list_storage_files', { filter });
    } catch (error) {
      console.error('Failed to list storage files:', error);
      return [];
    }
  }, []);

  return {
    // State
    isOperating,
    lastOperation,
    
    // Core operations
    saveSession,
    loadSession,
    exportContent,
    
    // Utility functions
    getSupportedFormats,
    getStorageInfo,
    listStorageFiles,
  };
}