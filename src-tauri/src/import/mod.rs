use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use chrono::{DateTime, Utc};

pub mod service;
pub mod parsers;
pub mod commands;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportConfig {
    pub auto_detect_content_types: bool,
    pub preserve_formatting: bool,
    pub extract_images: bool,
    pub create_backup_before_import: bool,
    pub default_import_settings: ImportSettings,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportSettings {
    pub session_name_template: String, // e.g., "Imported from {filename} - {date}"
    pub content_mapping: ContentMappingSettings,
    pub processing_options: ProcessingOptions,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentMappingSettings {
    pub map_slides_to_content_type: String, // "Slides" or "InstructorNotes"
    pub extract_speaker_notes: bool,
    pub create_worksheets_from_exercises: bool,
    pub detect_quiz_questions: bool,
    pub split_by_sections: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessingOptions {
    pub max_file_size_mb: u32,
    pub timeout_seconds: u32,
    pub preserve_slide_order: bool,
    pub extract_embedded_media: bool,
    pub convert_tables_to_structured_data: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportResult {
    pub success: bool,
    pub session_id: Option<String>,
    pub session_name: String,
    pub imported_content: Vec<ImportedContent>,
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
    pub processing_time_ms: u64,
    pub file_info: FileInfo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportedContent {
    pub content_type: String,
    pub title: String,
    pub content: String,
    pub metadata: ContentMetadata,
    pub order: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentMetadata {
    pub source_slide_number: Option<u32>,
    pub source_page_number: Option<u32>,
    pub has_images: bool,
    pub has_tables: bool,
    pub has_animations: bool,
    pub word_count: u32,
    pub extracted_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileInfo {
    pub filename: String,
    pub file_size: u64,
    pub file_type: SupportedFileType,
    pub last_modified: Option<DateTime<Utc>>,
    pub document_properties: DocumentProperties,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentProperties {
    pub title: Option<String>,
    pub author: Option<String>,
    pub subject: Option<String>,
    pub keywords: Vec<String>,
    pub created_date: Option<DateTime<Utc>>,
    pub modified_date: Option<DateTime<Utc>>,
    pub slide_count: Option<u32>,
    pub page_count: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SupportedFileType {
    PowerPoint, // .pptx
    Word,       // .docx
    Pdf,        // .pdf (future)
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportPreview {
    pub file_info: FileInfo,
    pub detected_content_types: Vec<DetectedContentType>,
    pub estimated_session_structure: SessionStructure,
    pub processing_warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetectedContentType {
    pub content_type: String,
    pub confidence: f32, // 0.0 to 1.0
    pub sample_content: String,
    pub count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionStructure {
    pub suggested_name: String,
    pub learning_objectives: Vec<String>,
    pub content_outline: Vec<ContentOutlineItem>,
    pub estimated_duration: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentOutlineItem {
    pub title: String,
    pub content_type: String,
    pub description: String,
    pub order: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportProgress {
    pub current_step: ImportStep,
    pub progress_percentage: f32,
    pub current_item: String,
    pub estimated_time_remaining: Option<u32>, // seconds
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ImportStep {
    Validating,
    Parsing,
    ExtractingContent,
    ProcessingImages,
    MappingContent,
    CreatingSession,
    Finalizing,
}

impl Default for ImportConfig {
    fn default() -> Self {
        Self {
            auto_detect_content_types: true,
            preserve_formatting: true,
            extract_images: false, // Can be resource intensive
            create_backup_before_import: true,
            default_import_settings: ImportSettings::default(),
        }
    }
}

impl Default for ImportSettings {
    fn default() -> Self {
        Self {
            session_name_template: "Imported from {filename}".to_string(),
            content_mapping: ContentMappingSettings::default(),
            processing_options: ProcessingOptions::default(),
        }
    }
}

impl Default for ContentMappingSettings {
    fn default() -> Self {
        Self {
            map_slides_to_content_type: "Slides".to_string(),
            extract_speaker_notes: true,
            create_worksheets_from_exercises: true,
            detect_quiz_questions: true,
            split_by_sections: true,
        }
    }
}

impl Default for ProcessingOptions {
    fn default() -> Self {
        Self {
            max_file_size_mb: 50,
            timeout_seconds: 300, // 5 minutes
            preserve_slide_order: true,
            extract_embedded_media: false,
            convert_tables_to_structured_data: true,
        }
    }
}

impl SupportedFileType {
    pub fn from_extension(ext: &str) -> Option<Self> {
        match ext.to_lowercase().as_str() {
            "pptx" => Some(SupportedFileType::PowerPoint),
            "docx" => Some(SupportedFileType::Word),
            "pdf" => Some(SupportedFileType::Pdf),
            _ => None,
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            SupportedFileType::PowerPoint => "PowerPoint Presentation",
            SupportedFileType::Word => "Word Document",
            SupportedFileType::Pdf => "PDF Document",
        }
    }

    pub fn icon(&self) -> &'static str {
        match self {
            SupportedFileType::PowerPoint => "📊",
            SupportedFileType::Word => "📝",
            SupportedFileType::Pdf => "📄",
        }
    }
}

impl ImportStep {
    pub fn display_name(&self) -> &'static str {
        match self {
            ImportStep::Validating => "Validating file",
            ImportStep::Parsing => "Parsing document structure",
            ImportStep::ExtractingContent => "Extracting content",
            ImportStep::ProcessingImages => "Processing images",
            ImportStep::MappingContent => "Mapping to content types",
            ImportStep::CreatingSession => "Creating session",
            ImportStep::Finalizing => "Finalizing import",
        }
    }

    pub fn progress_weight(&self) -> f32 {
        match self {
            ImportStep::Validating => 0.1,
            ImportStep::Parsing => 0.2,
            ImportStep::ExtractingContent => 0.3,
            ImportStep::ProcessingImages => 0.1,
            ImportStep::MappingContent => 0.15,
            ImportStep::CreatingSession => 0.1,
            ImportStep::Finalizing => 0.05,
        }
    }
}