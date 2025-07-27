use super::*;
use anyhow::Result;
use quick_xml::{Reader, events::Event};
use std::fs::File;
use std::io::BufReader;
use zip::ZipArchive;
use chrono::Utc;

pub struct PowerPointParser;
pub struct WordDocumentParser;

impl PowerPointParser {
    pub fn parse(file_path: &std::path::Path) -> Result<Vec<ImportedContent>> {
        let file = File::open(file_path)?;
        let mut archive = ZipArchive::new(file)?;
        
        // Extract presentation metadata
        let metadata = Self::extract_metadata(&mut archive)?;
        
        // Get slide files from relationships
        let slide_files = Self::get_slide_files(&mut archive)?;
        
        let mut imported_content = Vec::new();
        
        for (index, slide_file) in slide_files.iter().enumerate() {
            let slide_content = Self::parse_slide(&mut archive, slide_file, index as u32 + 1)?;
            imported_content.push(slide_content);
        }
        
        Ok(imported_content)
    }
    
    fn extract_metadata(archive: &mut ZipArchive<File>) -> Result<DocumentProperties> {
        // Try to read core properties
        let core_xml = Self::read_zip_file(archive, "docProps/core.xml").unwrap_or_default();
        
        let mut properties = DocumentProperties {
            title: None,
            author: None,
            subject: None,
            keywords: Vec::new(),
            created_date: None,
            modified_date: None,
            slide_count: None,
            page_count: None,
        };
        
        if !core_xml.is_empty() {
            let mut reader = Reader::from_str(&core_xml);
            let mut buf = Vec::new();
            let mut current_element = String::new();
            
            loop {
                match reader.read_event_into(&mut buf) {
                    Ok(Event::Start(ref e)) => {
                        current_element = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    }
                    Ok(Event::Text(e)) => {
                        let text = e.unescape()?.into_owned();
                        match current_element.as_str() {
                            "dc:title" => properties.title = Some(text),
                            "dc:creator" => properties.author = Some(text),
                            "dc:subject" => properties.subject = Some(text),
                            _ => {}
                        }
                    }
                    Ok(Event::Eof) => break,
                    Err(e) => return Err(anyhow::anyhow!("XML parse error: {}", e)),
                    _ => {}
                }
                buf.clear();
            }
        }
        
        Ok(properties)
    }
    
    fn get_slide_files(archive: &mut ZipArchive<File>) -> Result<Vec<String>> {
        let mut slide_files = Vec::new();
        
        // Simple approach: enumerate slide files directly
        for i in 0..archive.len() {
            let file = archive.by_index(i)?;
            let name = file.name();
            
            if name.starts_with("ppt/slides/slide") && name.ends_with(".xml") {
                slide_files.push(name.to_string());
            }
        }
        
        slide_files.sort();
        Ok(slide_files)
    }
    
    fn parse_slide(archive: &mut ZipArchive<File>, slide_path: &str, slide_number: u32) -> Result<ImportedContent> {
        let slide_xml = Self::read_zip_file(archive, slide_path)?;
        let (title, content) = Self::extract_slide_content(&slide_xml)?;
        
        let word_count = Self::count_words(&content);
        
        Ok(ImportedContent {
            content_type: "Slide".to_string(),
            title: title.unwrap_or_else(|| format!("Slide {}", slide_number)),
            content,
            metadata: ContentMetadata {
                source_slide_number: Some(slide_number),
                source_page_number: None,
                has_images: Self::check_for_images(&slide_xml),
                has_tables: Self::check_for_tables(&slide_xml),
                has_animations: Self::check_for_animations(&slide_xml),
                word_count,
                extracted_at: Utc::now(),
            },
            order: slide_number,
            word_count,
        })
    }
    
    fn read_zip_file(archive: &mut ZipArchive<File>, file_path: &str) -> Result<String> {
        let mut file = archive.by_name(file_path)?;
        let mut contents = String::new();
        std::io::Read::read_to_string(&mut file, &mut contents)?;
        Ok(contents)
    }

    fn count_words(text: &str) -> u32 {
        text.split_whitespace().count() as u32
    }

    fn check_for_images(xml: &str) -> bool {
        xml.contains("<a:blip") || xml.contains("<p:pic")
    }

    fn check_for_tables(xml: &str) -> bool {
        xml.contains("<a:tbl") || xml.contains("<a:gridCol")
    }

    fn check_for_animations(xml: &str) -> bool {
        xml.contains("<p:animLst") || xml.contains("<p:timing")
    }

    fn extract_slide_content(xml: &str) -> Result<(Option<String>, String)> {
        let mut reader = Reader::from_str(xml);
        let mut buf = Vec::new();
        let mut title: Option<String> = None;
        let mut content_parts = Vec::new();
        let mut current_text = String::new();
        let mut in_text_element = false;
        
        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    match e.name().as_ref() {
                        b"a:t" => {
                            in_text_element = true;
                            current_text.clear();
                        }
                        _ => {}
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_text_element {
                        let text = e.unescape()?.into_owned();
                        current_text.push_str(&text);
                    }
                }
                Ok(Event::End(ref e)) => {
                    if e.name().as_ref() == b"a:t" && in_text_element {
                        in_text_element = false;
                        if !current_text.trim().is_empty() {
                            if title.is_none() && Self::is_likely_title(&current_text) {
                                title = Some(current_text.clone());
                            } else {
                                content_parts.push(current_text.clone());
                            }
                        }
                    }
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(anyhow::anyhow!("XML parse error: {}", e)),
                _ => {}
            }
            buf.clear();
        }
        
        let content = content_parts.join("\n");
        Ok((title, content))
    }
    
    fn is_likely_title(text: &str) -> bool {
        let text = text.trim();
        text.len() < 100 && !text.contains('\n') && !text.contains('.')
    }

    fn extract_notes_content(_xml: &str) -> Result<Option<String>> {
        // Notes parsing would be similar to slide content parsing
        // For now, return None as this is a future enhancement
        Ok(None)
    }
}

impl WordDocumentParser {
    pub fn parse(file_path: &std::path::Path) -> Result<Vec<ImportedContent>> {
        let file = File::open(file_path)?;
        let mut archive = ZipArchive::new(file)?;
        
        // Extract document XML
        let document_xml = Self::read_zip_file(&mut archive, "word/document.xml")?;
        
        // Extract metadata
        let metadata = Self::extract_metadata(&mut archive)?;
        
        // Parse document sections
        let sections = Self::extract_document_sections(&document_xml)?;
        
        let mut imported_content = Vec::new();
        
        for (index, section) in sections.iter().enumerate() {
            let content_type = Self::classify_content_type(section);
            let word_count = Self::count_words(&section.content);
            
            imported_content.push(ImportedContent {
                content_type,
                title: if section.title.is_empty() {
                    format!("Section {}", index + 1)
                } else {
                    section.title.clone()
                },
                content: section.content.clone(),
                metadata: ContentMetadata {
                    source_slide_number: None,
                    source_page_number: Some(index as u32 + 1),
                    has_images: section.has_images,
                    has_tables: section.has_tables,
                    has_animations: false,
                    word_count,
                    extracted_at: Utc::now(),
                },
                order: index as u32 + 1,
                word_count,
            });
        }
        
        Ok(imported_content)
    }
    
    fn read_zip_file(archive: &mut ZipArchive<File>, file_path: &str) -> Result<String> {
        let mut file = archive.by_name(file_path)?;
        let mut contents = String::new();
        std::io::Read::read_to_string(&mut file, &mut contents)?;
        Ok(contents)
    }
    
    fn extract_metadata(archive: &mut ZipArchive<File>) -> Result<DocumentProperties> {
        let core_xml = Self::read_zip_file(archive, "docProps/core.xml").unwrap_or_default();
        
        let mut properties = DocumentProperties {
            title: None,
            author: None,
            subject: None,
            keywords: Vec::new(),
            created_date: None,
            modified_date: None,
            slide_count: None,
            page_count: None,
        };
        
        if !core_xml.is_empty() {
            let mut reader = Reader::from_str(&core_xml);
            let mut buf = Vec::new();
            let mut current_element = String::new();
            
            loop {
                match reader.read_event_into(&mut buf) {
                    Ok(Event::Start(ref e)) => {
                        current_element = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    }
                    Ok(Event::Text(e)) => {
                        let text = e.unescape()?.into_owned();
                        match current_element.as_str() {
                            "dc:title" => properties.title = Some(text),
                            "dc:creator" => properties.author = Some(text),
                            "dc:subject" => properties.subject = Some(text),
                            _ => {}
                        }
                    }
                    Ok(Event::Eof) => break,
                    Err(e) => return Err(anyhow::anyhow!("XML parse error: {}", e)),
                    _ => {}
                }
                buf.clear();
            }
        }
        
        Ok(properties)
    }

    fn extract_document_sections(xml: &str) -> Result<Vec<DocumentSection>> {
        let mut reader = Reader::from_str(xml);
        let mut buf = Vec::new();
        let mut sections = Vec::new();
        let mut current_paragraph = String::new();
        let mut in_text_element = false;
        let mut current_style = String::new();
        
        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    match e.name().as_ref() {
                        b"w:t" => {
                            in_text_element = true;
                        }
                        b"w:pStyle" => {
                            // Extract style information for header detection
                            if let Ok(val_attr) = e.try_get_attribute("w:val") {
                                if let Some(val) = val_attr {
                                    current_style = String::from_utf8_lossy(&val.value).to_string();
                                }
                            }
                        }
                        _ => {}
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_text_element {
                        let text = e.unescape()?.into_owned();
                        current_paragraph.push_str(&text);
                    }
                }
                Ok(Event::End(ref e)) => {
                    match e.name().as_ref() {
                        b"w:t" => {
                            in_text_element = false;
                        }
                        b"w:p" => {
                            // End of paragraph
                            if !current_paragraph.trim().is_empty() {
                                let is_header = Self::is_header_style(&current_style) || Self::is_likely_header(&current_paragraph);
                                
                                if is_header {
                                    // Start new section with this as title
                                    sections.push(DocumentSection {
                                        title: current_paragraph.trim().to_string(),
                                        content: String::new(),
                                        has_images: false,
                                        has_tables: false,
                                    });
                                } else if let Some(last_section) = sections.last_mut() {
                                    // Add to current section
                                    if !last_section.content.is_empty() {
                                        last_section.content.push('\n');
                                    }
                                    last_section.content.push_str(&current_paragraph);
                                } else {
                                    // First content without header
                                    sections.push(DocumentSection {
                                        title: "Introduction".to_string(),
                                        content: current_paragraph.clone(),
                                        has_images: false,
                                        has_tables: false,
                                    });
                                }
                            }
                            current_paragraph.clear();
                            current_style.clear();
                        }
                        _ => {}
                    }
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(anyhow::anyhow!("XML parse error: {}", e)),
                _ => {}
            }
            buf.clear();
        }
        
        Ok(sections)
    }
    
    fn is_header_style(style: &str) -> bool {
        style.contains("Heading") || style.contains("Title") || style.contains("heading")
    }
    
    fn is_likely_header(text: &str) -> bool {
        let text = text.trim();
        text.len() < 100 && 
        !text.contains('.') && 
        !text.contains(',') && 
        text.chars().filter(|c| c.is_uppercase()).count() > text.len() / 3
    }

    fn classify_content_type(section: &DocumentSection) -> String {
        let title_lower = section.title.to_lowercase();
        let content_lower = section.content.to_lowercase();
        
        if title_lower.contains("objective") || content_lower.contains("students will") {
            "Learning Objectives".to_string()
        } else if title_lower.contains("outline") || title_lower.contains("agenda") {
            "Content Outline".to_string()
        } else if title_lower.contains("assessment") || title_lower.contains("quiz") || title_lower.contains("test") {
            "Assessment".to_string()
        } else if title_lower.contains("activity") || title_lower.contains("exercise") {
            "Activity".to_string()
        } else if title_lower.contains("instruction") {
            "Instructions".to_string()
        } else {
            "Content".to_string()
        }
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