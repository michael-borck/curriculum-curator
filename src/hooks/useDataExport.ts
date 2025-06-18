import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { save } from '@tauri-apps/api/dialog';

export interface DataExportConfig {
  default_format: ExportFormat;
  compression_level: number;
  include_metadata: boolean;
  include_generated_files: boolean;
  include_backups: boolean;
  max_archive_size_mb: number;
  encrypt_exports: boolean;
  encryption_password?: string;
}

export interface ExportFormat {
  Archive?: ArchiveFormat;
  Database?: DatabaseFormat;
  Portable?: PortableFormat;
}

export type ArchiveFormat = 'Zip' | 'Tar' | 'TarGz' | 'SevenZip';
export type DatabaseFormat = 'SqliteBackup' | 'JsonExport' | 'CsvExport';
export type PortableFormat = 'CurriculumPack' | 'EducatorBundle' | 'MinimalExport';

export interface ExportRequest {
  format: ExportFormat;
  sessions: ExportSessionFilter;
  content_types: string[];
  include_attachments: boolean;
  include_history: boolean;
  output_path: string;
  filename?: string;
  options: ExportOptions;
}

export interface ExportSessionFilter {
  All?: null;
  SelectedSessions?: string[];
  DateRange?: { start: string; end: string };
  RecentSessions?: number;
}

export interface ExportOptions {
  compress: boolean;
  compression_level?: number;
  encrypt: boolean;
  password?: string;
  split_large_files: boolean;
  max_file_size_mb?: number;
  include_thumbnails: boolean;
  generate_index: boolean;
}

export interface ExportResult {
  success: boolean;
  export_id: string;
  output_path: string;
  file_size: number;
  sessions_exported: number;
  content_items_exported: number;
  processing_time_ms: number;
  warnings: string[];
  errors: string[];
  manifest: ExportManifest;
}

export interface ExportManifest {
  export_id: string;
  created_at: string;
  format: ExportFormat;
  source_info: SourceInfo;
  content_summary: ContentSummary;
  file_structure: FileEntry[];
  metadata: Record<string, any>;
}

export interface SourceInfo {
  application_version: string;
  database_version: string;
  export_version: string;
  platform: string;
  total_sessions: number;
  export_timestamp: string;
}

export interface ContentSummary {
  sessions: SessionSummary[];
  content_types: Record<string, number>;
  total_files: number;
  total_size_bytes: number;
}

export interface SessionSummary {
  id: string;
  name: string;
  created_at: string;
  content_count: number;
  content_types: string[];
  size_bytes: number;
}

export interface FileEntry {
  path: string;
  file_type: FileType;
  size_bytes: number;
  checksum?: string;
  created_at: string;
  metadata: Record<string, any>;
}

export type FileType = 'SessionData' | 'ContentFile' | 'Attachment' | 'Metadata' | 'Index' | 'Backup';

export interface ExportProgress {
  current_step: ExportStep;
  progress_percentage: number;
  current_item: string;
  items_processed: number;
  total_items: number;
  estimated_time_remaining?: number;
  current_file_size: number;
  total_size_estimate: number;
}

export type ExportStep = 
  | 'Initializing'
  | 'CollectingSessions'
  | 'ProcessingContent'
  | 'CreatingArchive'
  | 'CompressingFiles'
  | 'GeneratingManifest'
  | 'Finalizing'
  | 'Complete';

export interface ExportFormatInfo {
  format: ExportFormat;
  display_name: string;
  description: string;
  extension: string;
  supports_compression: boolean;
  supports_encryption: boolean;
  recommended_for: string[];
}

export interface ExportValidation {
  is_valid: boolean;
  warnings: string[];
  errors: string[];
  estimated_size_mb: number;
  estimated_time_minutes: number;
}

export interface ExportPreview {
  session_count: number;
  content_types: string[];
  estimated_files: number;
  estimated_size_bytes: number;
  sessions_summary: SessionSummary[];
}

export function useDataExport() {
  const [config, setConfig] = useState<DataExportConfig | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState<ExportProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [availableFormats, setAvailableFormats] = useState<ExportFormatInfo[]>([]);

  const loadConfig = useCallback(async () => {
    try {
      const result = await invoke<DataExportConfig>('get_data_export_config');
      setConfig(result);
      setError(null);
    } catch (err) {
      setError(err as string);
    }
  }, []);

  const updateConfig = useCallback(async (newConfig: DataExportConfig) => {
    try {
      await invoke('update_data_export_config', { config: newConfig });
      setConfig(newConfig);
      setError(null);
    } catch (err) {
      setError(err as string);
    }
  }, []);

  const loadAvailableFormats = useCallback(async () => {
    try {
      const result = await invoke<ExportFormatInfo[]>('get_export_formats');
      setAvailableFormats(result);
      setError(null);
    } catch (err) {
      setError(err as string);
    }
  }, []);

  const selectOutputPath = useCallback(async (defaultFilename?: string): Promise<string | null> => {
    try {
      const result = await save({
        defaultPath: defaultFilename,
        filters: [
          {
            name: 'Export Files',
            extensions: ['zip', 'tar', 'gz', 'json', 'ccpack', 'edubundle', 'ccmin']
          }
        ]
      });
      
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    }
  }, []);

  const validateExportRequest = useCallback(async (request: ExportRequest): Promise<ExportValidation | null> => {
    try {
      const result = await invoke<ExportValidation>('validate_export_request', { request });
      setError(null);
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    }
  }, []);

  const previewExport = useCallback(async (sessionFilter: ExportSessionFilter): Promise<ExportPreview | null> => {
    try {
      const result = await invoke<ExportPreview>('preview_export_contents', {
        sessionFilter
      });
      setError(null);
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    }
  }, []);

  const exportData = useCallback(async (
    request: ExportRequest,
    withProgress: boolean = false
  ): Promise<ExportResult | null> => {
    setIsExporting(true);
    setExportProgress(null);
    setError(null);

    try {
      let result: ExportResult;
      
      if (withProgress) {
        // Set up progress listener
        const unlisten = await window.__TAURI__.event.listen('export-progress', (event) => {
          setExportProgress(event.payload as ExportProgress);
        });

        try {
          result = await invoke<ExportResult>('export_data_with_progress', {
            request
          });
        } finally {
          unlisten();
        }
      } else {
        result = await invoke<ExportResult>('export_data', {
          request
        });
      }

      setExportProgress(null);
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    } finally {
      setIsExporting(false);
    }
  }, []);

  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }, []);

  const getFormatIcon = useCallback((format: ExportFormat): string => {
    if (format.Archive) {
      switch (format.Archive) {
        case 'Zip': return '📦';
        case 'Tar': return '📋';
        case 'TarGz': return '🗜️';
        case 'SevenZip': return '📦';
        default: return '📦';
      }
    } else if (format.Database) {
      switch (format.Database) {
        case 'JsonExport': return '📄';
        case 'SqliteBackup': return '🗃️';
        case 'CsvExport': return '📊';
        default: return '📄';
      }
    } else if (format.Portable) {
      switch (format.Portable) {
        case 'CurriculumPack': return '🎓';
        case 'EducatorBundle': return '👨‍🏫';
        case 'MinimalExport': return '📝';
        default: return '📦';
      }
    }
    return '📦';
  }, []);

  const getStepDisplayName = useCallback((step: ExportStep): string => {
    switch (step) {
      case 'Initializing': return 'Initializing export';
      case 'CollectingSessions': return 'Collecting session data';
      case 'ProcessingContent': return 'Processing content files';
      case 'CreatingArchive': return 'Creating archive';
      case 'CompressingFiles': return 'Compressing files';
      case 'GeneratingManifest': return 'Generating manifest';
      case 'Finalizing': return 'Finalizing export';
      case 'Complete': return 'Export complete';
      default: return 'Processing...';
    }
  }, []);

  const createExportRequest = useCallback((
    format: ExportFormat,
    sessions: ExportSessionFilter,
    outputPath: string,
    options: Partial<ExportOptions> = {}
  ): ExportRequest => {
    const defaultOptions: ExportOptions = {
      compress: true,
      encrypt: false,
      split_large_files: true,
      max_file_size_mb: 100,
      include_thumbnails: true,
      generate_index: true,
      ...options
    };

    return {
      format,
      sessions,
      content_types: [],
      include_attachments: true,
      include_history: true,
      output_path: outputPath,
      options: defaultOptions,
    };
  }, []);

  return {
    // State
    config,
    isExporting,
    exportProgress,
    error,
    availableFormats,

    // Actions
    loadConfig,
    updateConfig,
    loadAvailableFormats,
    selectOutputPath,
    validateExportRequest,
    previewExport,
    exportData,

    // Utilities
    formatFileSize,
    getFormatIcon,
    getStepDisplayName,
    createExportRequest,
  };
}