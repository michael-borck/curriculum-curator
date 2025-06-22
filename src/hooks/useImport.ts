import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';

export interface ImportConfig {
  auto_detect_content_types: boolean;
  preserve_formatting: boolean;
  extract_images: boolean;
  create_backup_before_import: boolean;
  default_import_settings: ImportSettings;
}

export interface ImportSettings {
  session_name_template: string;
  content_mapping: ContentMappingSettings;
  processing_options: ProcessingOptions;
}

export interface ContentMappingSettings {
  map_slides_to_content_type: string;
  extract_speaker_notes: boolean;
  create_worksheets_from_exercises: boolean;
  detect_quiz_questions: boolean;
  split_by_sections: boolean;
}

export interface ProcessingOptions {
  max_file_size_mb: number;
  timeout_seconds: number;
  preserve_slide_order: boolean;
  extract_embedded_media: boolean;
  convert_tables_to_structured_data: boolean;
}

export interface ImportResult {
  success: boolean;
  session_id?: string;
  session_name: string;
  imported_content: ImportedContent[];
  warnings: string[];
  errors: string[];
  processing_time_ms: number;
  file_info: FileInfo;
}

export interface ImportedContent {
  content_type: string;
  title: string;
  content: string;
  metadata: ContentMetadata;
  order: number;
}

export interface ContentMetadata {
  source_slide_number?: number;
  source_page_number?: number;
  has_images: boolean;
  has_tables: boolean;
  has_animations: boolean;
  word_count: number;
  extracted_at: string;
}

export interface FileInfo {
  filename: string;
  file_size: number;
  file_type: SupportedFileType;
  last_modified?: string;
  document_properties: DocumentProperties;
}

export interface DocumentProperties {
  title?: string;
  author?: string;
  subject?: string;
  keywords: string[];
  created_date?: string;
  modified_date?: string;
  slide_count?: number;
  page_count?: number;
}

export enum SupportedFileType {
  PowerPoint = 'PowerPoint',
  Word = 'Word',
  Pdf = 'Pdf',
}

export interface ImportPreview {
  file_info: FileInfo;
  detected_content_types: DetectedContentType[];
  estimated_session_structure: SessionStructure;
  processing_warnings: string[];
}

export interface DetectedContentType {
  content_type: string;
  confidence: number;
  sample_content: string;
  count: number;
}

export interface SessionStructure {
  suggested_name: string;
  learning_objectives: string[];
  content_outline: ContentOutlineItem[];
  estimated_duration: string;
}

export interface ContentOutlineItem {
  title: string;
  content_type: string;
  description: string;
  order: number;
}

export interface ImportProgress {
  current_step: ImportStep;
  progress_percentage: number;
  current_item: string;
  estimated_time_remaining?: number;
}

export enum ImportStep {
  Validating = 'Validating',
  Parsing = 'Parsing',
  ExtractingContent = 'ExtractingContent',
  ProcessingImages = 'ProcessingImages',
  MappingContent = 'MappingContent',
  CreatingSession = 'CreatingSession',
  Finalizing = 'Finalizing',
}

export interface SupportedFileTypeInfo {
  file_type: SupportedFileType;
  display_name: string;
  extensions: string[];
  icon: string;
  description: string;
}

export interface FileValidationResult {
  is_valid: boolean;
  error_message?: string;
  file_info?: BasicFileInfo;
}

export interface BasicFileInfo {
  filename: string;
  file_size: number;
  file_type: SupportedFileType;
  last_modified?: string;
}

export function useImport() {
  const [config, setConfig] = useState<ImportConfig | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importProgress, setImportProgress] = useState<ImportProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [supportedTypes, setSupportedTypes] = useState<SupportedFileTypeInfo[]>([]);

  const loadConfig = useCallback(async () => {
    try {
      const result = await invoke<ImportConfig>('get_import_config');
      setConfig(result);
      setError(null);
    } catch (err) {
      setError(err as string);
    }
  }, []);

  const updateConfig = useCallback(async (newConfig: ImportConfig) => {
    try {
      await invoke('update_import_config', { config: newConfig });
      setConfig(newConfig);
      setError(null);
    } catch (err) {
      setError(err as string);
    }
  }, []);

  const loadSupportedTypes = useCallback(async () => {
    try {
      const result = await invoke<SupportedFileTypeInfo[]>('get_supported_file_types');
      setSupportedTypes(result);
      setError(null);
    } catch (err) {
      setError(err as string);
    }
  }, []);

  const selectFile = useCallback(async (): Promise<string | null> => {
    try {
      const result = await open({
        multiple: false,
        filters: [
          {
            name: 'Supported Documents',
            extensions: ['pptx', 'docx']
          },
          {
            name: 'PowerPoint Presentations',
            extensions: ['pptx']
          },
          {
            name: 'Word Documents',
            extensions: ['docx']
          }
        ]
      });
      
      return Array.isArray(result) ? result[0] : result;
    } catch (err) {
      setError(err as string);
      return null;
    }
  }, []);

  const validateFile = useCallback(async (filePath: string): Promise<FileValidationResult> => {
    try {
      const result = await invoke<FileValidationResult>('validate_import_file', {
        filePath
      });
      setError(null);
      return result;
    } catch (err) {
      setError(err as string);
      return {
        is_valid: false,
        error_message: err as string
      };
    }
  }, []);

  const previewImport = useCallback(async (filePath: string): Promise<ImportPreview | null> => {
    try {
      const result = await invoke<ImportPreview>('preview_import_file', {
        filePath
      });
      setError(null);
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    }
  }, []);

  const importFile = useCallback(async (
    filePath: string,
    settings?: ImportSettings,
    withProgress: boolean = false
  ): Promise<ImportResult | null> => {
    setIsImporting(true);
    setImportProgress(null);
    setError(null);

    try {
      let result: ImportResult;
      
      if (withProgress) {
        // Set up progress listener
        const unlisten = await window.__TAURI__.event.listen('import-progress', (event) => {
          setImportProgress(event.payload as ImportProgress);
        });

        try {
          result = await invoke<ImportResult>('import_file_with_progress', {
            filePath,
            settings
          });
        } finally {
          unlisten();
        }
      } else {
        result = await invoke<ImportResult>('import_file', {
          filePath,
          settings
        });
      }

      setImportProgress(null);
      return result;
    } catch (err) {
      setError(err as string);
      return null;
    } finally {
      setIsImporting(false);
    }
  }, []);

  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }, []);

  const getFileTypeIcon = useCallback((fileType: SupportedFileType): string => {
    switch (fileType) {
      case SupportedFileType.PowerPoint:
        return '📊';
      case SupportedFileType.Word:
        return '📝';
      case SupportedFileType.Pdf:
        return '📄';
      default:
        return '📄';
    }
  }, []);

  const getImportStepName = useCallback((step: ImportStep): string => {
    switch (step) {
      case ImportStep.Validating:
        return 'Validating file';
      case ImportStep.Parsing:
        return 'Parsing document structure';
      case ImportStep.ExtractingContent:
        return 'Extracting content';
      case ImportStep.ProcessingImages:
        return 'Processing images';
      case ImportStep.MappingContent:
        return 'Mapping to content types';
      case ImportStep.CreatingSession:
        return 'Creating session';
      case ImportStep.Finalizing:
        return 'Finalizing import';
      default:
        return 'Processing...';
    }
  }, []);

  return {
    // State
    config,
    isImporting,
    importProgress,
    error,
    supportedTypes,

    // Actions
    loadConfig,
    updateConfig,
    loadSupportedTypes,
    selectFile,
    validateFile,
    previewImport,
    importFile,

    // Utilities
    formatFileSize,
    getFileTypeIcon,
    getImportStepName,
  };
}