use super::{ExportFormat, ExportOptions, ExportResult, FormatConverter, MarkdownConverter, HtmlConverter, PdfConverter, PowerPointConverter};
use crate::content::GeneratedContent;
use anyhow::{Result, Context};
use std::collections::HashMap;

pub struct ExportManager {
    converters: HashMap<ExportFormat, Box<dyn FormatConverter>>,
}

impl ExportManager {
    pub fn new() -> Self {
        let mut converters: HashMap<ExportFormat, Box<dyn FormatConverter>> = HashMap::new();
        
        // Register available converters
        converters.insert(ExportFormat::Markdown, Box::new(MarkdownConverter::new()));
        converters.insert(ExportFormat::Html, Box::new(HtmlConverter::new()));
        converters.insert(ExportFormat::Pdf, Box::new(PdfConverter::new()));
        converters.insert(ExportFormat::PowerPoint, Box::new(PowerPointConverter::new()));
        
        Self { converters }
    }

    pub fn supported_formats(&self) -> Vec<ExportFormat> {
        self.converters.keys().cloned().collect()
    }

    pub async fn export_content(
        &self,
        contents: &[GeneratedContent],
        options: &ExportOptions,
    ) -> Result<ExportResult> {
        let converter = self.converters.get(&options.format)
            .ok_or_else(|| anyhow::anyhow!("Unsupported export format: {:?}", options.format))?;

        converter.convert(contents, options)
            .await
            .context("Export conversion failed")
    }

    pub fn get_default_extension(&self, format: &ExportFormat) -> &'static str {
        match format {
            ExportFormat::Markdown => "md",
            ExportFormat::Html => "html",
            ExportFormat::Pdf => "pdf",
            ExportFormat::PowerPoint => "pptx",
            ExportFormat::Word => "docx",
        }
    }

    pub fn validate_export_path(&self, path: &std::path::Path, format: &ExportFormat) -> Result<()> {
        let expected_extension = self.get_default_extension(format);
        
        if let Some(extension) = path.extension() {
            if extension != expected_extension {
                return Err(anyhow::anyhow!(
                    "File extension '{}' does not match format {:?} (expected '{}')",
                    extension.to_string_lossy(),
                    format,
                    expected_extension
                ));
            }
        }

        // Check if parent directory exists or can be created
        if let Some(parent) = path.parent() {
            if !parent.exists() {
                std::fs::create_dir_all(parent)
                    .context("Failed to create parent directory for export")?;
            }
        }

        Ok(())
    }
}

impl Default for ExportManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::content::{ContentType, generator::ContentMetadata};
    use std::path::PathBuf;

    fn create_test_content() -> GeneratedContent {
        GeneratedContent {
            content_type: ContentType::Slides,
            title: "Test Content".to_string(),
            content: "Test content body".to_string(),
            metadata: ContentMetadata {
                word_count: 3,
                estimated_duration: "5 minutes".to_string(),
                difficulty_level: "Easy".to_string(),
            },
        }
    }

    #[tokio::test]
    async fn test_export_manager_creation() {
        let manager = ExportManager::new();
        let supported = manager.supported_formats();
        assert!(supported.contains(&ExportFormat::Markdown));
    }

    #[tokio::test]
    async fn test_markdown_export() {
        let manager = ExportManager::new();
        let contents = vec![create_test_content()];
        
        let temp_dir = std::env::temp_dir();
        let output_path = temp_dir.join("test_manager_export.md");
        
        let options = ExportOptions {
            format: ExportFormat::Markdown,
            output_path: output_path.clone(),
            template_name: None,
            include_metadata: true,
        };

        let result = manager.export_content(&contents, &options).await;
        assert!(result.is_ok());
        
        let export_result = result.unwrap();
        assert!(export_result.success);
        assert!(output_path.exists());
        
        // Cleanup
        if output_path.exists() {
            let _ = std::fs::remove_file(output_path);
        }
    }

    #[test]
    fn test_extension_validation() {
        let manager = ExportManager::new();
        
        let md_path = PathBuf::from("/tmp/test.md");
        assert!(manager.validate_export_path(&md_path, &ExportFormat::Markdown).is_ok());
        
        let wrong_path = PathBuf::from("/tmp/test.txt");
        assert!(manager.validate_export_path(&wrong_path, &ExportFormat::Markdown).is_err());
    }

    #[test]
    fn test_default_extensions() {
        let manager = ExportManager::new();
        
        assert_eq!(manager.get_default_extension(&ExportFormat::Markdown), "md");
        assert_eq!(manager.get_default_extension(&ExportFormat::Html), "html");
        assert_eq!(manager.get_default_extension(&ExportFormat::Pdf), "pdf");
        assert_eq!(manager.get_default_extension(&ExportFormat::PowerPoint), "pptx");
        assert_eq!(manager.get_default_extension(&ExportFormat::Word), "docx");
    }
}