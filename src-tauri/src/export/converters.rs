use serde::{Deserialize, Serialize};
use anyhow::Result;
use crate::content::GeneratedContent;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize, Eq, Hash, PartialEq)]
pub enum ExportFormat {
    Markdown,
    Html,
    Pdf,
    PowerPoint,
    Word,
    // Quarto formats for advanced users
    #[cfg(feature = "quarto-integration")]
    QuartoHtml,
    #[cfg(feature = "quarto-integration")]
    QuartoPdf,
    #[cfg(feature = "quarto-integration")]
    QuartoPowerPoint,
    #[cfg(feature = "quarto-integration")]
    QuartoWord,
    #[cfg(feature = "quarto-integration")]
    QuartoBook,
    #[cfg(feature = "quarto-integration")]
    QuartoWebsite,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BrandingOptions {
    pub institution_name: Option<String>,
    pub logo_path: Option<String>,
    pub colors: BrandColors,
    pub fonts: BrandFonts,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BrandColors {
    pub primary: String,
    pub secondary: String,
    pub accent: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BrandFonts {
    pub heading: String,
    pub body: String,
}

impl Default for BrandingOptions {
    fn default() -> Self {
        Self {
            institution_name: None,
            logo_path: None,
            colors: BrandColors {
                primary: "#2563eb".to_string(),    // Blue
                secondary: "#64748b".to_string(),  // Slate
                accent: "#0ea5e9".to_string(),     // Sky
            },
            fonts: BrandFonts {
                heading: "Inter, sans-serif".to_string(),
                body: "Inter, sans-serif".to_string(),
            },
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportOptions {
    pub format: ExportFormat,
    pub output_path: PathBuf,
    pub template_name: Option<String>,
    pub include_metadata: bool,
    pub branding_options: Option<BrandingOptions>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportResult {
    pub success: bool,
    pub output_path: PathBuf,
    pub file_size: Option<u64>,
    pub error_message: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchExportJob {
    pub job_id: String,
    pub session_ids: Vec<String>,
    pub formats: Vec<ExportFormat>,
    pub output_directory: PathBuf,
    pub naming_strategy: NamingStrategy,
    pub merge_sessions: bool,
    pub template_name: Option<String>,
    pub include_metadata: bool,
    pub branding_options: Option<BrandingOptions>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum NamingStrategy {
    SessionBased,    // Use session names/IDs
    ContentBased,    // Use content titles
    Sequential,      // Use sequential numbers
    Custom(String),  // Custom pattern with placeholders
}

impl Default for NamingStrategy {
    fn default() -> Self {
        NamingStrategy::SessionBased
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchExportOptions {
    pub parallel_exports: bool,
    pub max_concurrent_jobs: usize,
    pub continue_on_error: bool,
    pub create_manifest: bool,
    pub compress_output: bool,
}

impl Default for BatchExportOptions {
    fn default() -> Self {
        Self {
            parallel_exports: true,
            max_concurrent_jobs: 4,
            continue_on_error: true,
            create_manifest: true,
            compress_output: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchExportResult {
    pub total_jobs: usize,
    pub successful_jobs: usize,
    pub failed_jobs: usize,
    pub job_results: Vec<JobResult>,
    pub total_files_created: usize,
    pub total_size: u64,
    pub elapsed_time: std::time::Duration,
    pub manifest_path: Option<PathBuf>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobResult {
    pub job_id: String,
    pub success: bool,
    pub export_results: Vec<ExportResult>,
    pub error_message: Option<String>,
    pub files_created: usize,
    pub total_size: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchProgress {
    pub total_jobs: usize,
    pub completed_jobs: usize,
    pub current_job_id: Option<String>,
    pub current_operation: String,
    pub progress_percent: f32,
    pub estimated_completion: Option<String>,
    pub errors_encountered: usize,
}

#[async_trait::async_trait]
pub trait FormatConverter: Send + Sync {
    fn supported_format(&self) -> ExportFormat;
    async fn convert(&self, content: &[GeneratedContent], options: &ExportOptions) -> Result<ExportResult>;
}