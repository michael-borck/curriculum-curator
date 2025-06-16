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
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportOptions {
    pub format: ExportFormat,
    pub output_path: PathBuf,
    pub template_name: Option<String>,
    pub include_metadata: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportResult {
    pub success: bool,
    pub output_path: PathBuf,
    pub file_size: Option<u64>,
    pub error_message: Option<String>,
}

#[async_trait::async_trait]
pub trait FormatConverter: Send + Sync {
    fn supported_format(&self) -> ExportFormat;
    async fn convert(&self, content: &[GeneratedContent], options: &ExportOptions) -> Result<ExportResult>;
}