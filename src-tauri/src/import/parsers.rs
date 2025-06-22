// Import parsers temporarily disabled due to quick-xml API compatibility issues
// This will be fixed in a future update

use super::*;
use anyhow::Result;

pub struct PowerPointParser;
pub struct WordDocumentParser;

impl PowerPointParser {
    pub fn parse(_file_path: &std::path::Path) -> Result<Vec<ImportedContent>> {
        Err(anyhow::anyhow!("PowerPoint import is temporarily disabled"))
    }

    fn count_words(text: &str) -> u32 {
        text.split_whitespace().count() as u32
    }

    fn check_for_images(_xml: &str) -> bool {
        false
    }

    fn check_for_tables(_xml: &str) -> bool {
        false
    }

    fn check_for_animations(_xml: &str) -> bool {
        false
    }

    fn extract_slide_content(_xml: &str) -> Result<(Option<String>, String)> {
        Ok((None, String::new()))
    }

    fn extract_notes_content(_xml: &str) -> Result<Option<String>> {
        Ok(None)
    }
}

impl WordDocumentParser {
    pub fn parse(_file_path: &std::path::Path) -> Result<Vec<ImportedContent>> {
        Err(anyhow::anyhow!("Word document import is temporarily disabled"))
    }

    fn extract_document_sections(_xml: &str) -> Result<Vec<DocumentSection>> {
        Ok(vec![])
    }

    fn classify_content_type(_section: &DocumentSection) -> String {
        "Unknown".to_string()
    }

    fn count_words(text: &str) -> u32 {
        text.split_whitespace().count() as u32
    }
}

#[derive(Debug, Clone)]
struct DocumentSection {
    title: String,
    content: String,
    has_images: bool,
    has_tables: bool,
}