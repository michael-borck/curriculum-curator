use super::*;
use anyhow::{Result, Context};
use std::path::Path;
use std::fs::File;
use std::io::Read;
use zip::ZipArchive;
use quick_xml::Reader;
use quick_xml::events::Event;
use chrono::Utc;

pub struct PowerPointParser;
pub struct WordParser;

impl PowerPointParser {
    pub async fn parse_file(file_path: &Path) -> Result<Vec<ImportedContent>> {
        let file = File::open(file_path)
            .context("Failed to open PowerPoint file")?;
        
        let mut archive = ZipArchive::new(file)
            .context("Failed to read PowerPoint archive")?;
        
        let mut slides = Vec::new();
        let mut speaker_notes = Vec::new();
        
        // Extract slide content
        let slide_count = Self::get_slide_count(&mut archive)?;
        
        for i in 1..=slide_count {
            let slide_name = format!("ppt/slides/slide{}.xml", i);
            if let Ok(mut slide_file) = archive.by_name(&slide_name) {
                let mut slide_content = String::new();
                slide_file.read_to_string(&mut slide_content)?;
                
                let (title, content) = Self::extract_slide_content(&slide_content)?;
                
                slides.push(ImportedContent {
                    content_type: "Slides".to_string(),
                    title: title.unwrap_or_else(|| format!("Slide {}", i)),
                    content,
                    metadata: ContentMetadata {
                        source_slide_number: Some(i as u32),
                        source_page_number: None,
                        has_images: Self::check_for_images(&slide_content),
                        has_tables: Self::check_for_tables(&slide_content),
                        has_animations: Self::check_for_animations(&slide_content),
                        word_count: Self::count_words(&content),
                        extracted_at: Utc::now(),
                    },
                    order: i as u32,
                });
            }
            
            // Extract speaker notes
            let notes_name = format!("ppt/notesSlides/notesSlide{}.xml", i);
            if let Ok(mut notes_file) = archive.by_name(&notes_name) {
                let mut notes_content = String::new();
                notes_file.read_to_string(&mut notes_content)?;
                
                if let Some(notes_text) = Self::extract_notes_content(&notes_content)? {
                    speaker_notes.push(ImportedContent {
                        content_type: "InstructorNotes".to_string(),
                        title: format!("Speaker Notes - Slide {}", i),
                        content: notes_text,
                        metadata: ContentMetadata {
                            source_slide_number: Some(i as u32),
                            source_page_number: None,
                            has_images: false,
                            has_tables: false,
                            has_animations: false,
                            word_count: Self::count_words(&notes_text),
                            extracted_at: Utc::now(),
                        },
                        order: i as u32 + 1000, // Offset to keep notes after slides
                    });
                }
            }
        }
        
        let mut all_content = slides;
        all_content.extend(speaker_notes);
        
        Ok(all_content)
    }
    
    fn get_slide_count(archive: &mut ZipArchive<File>) -> Result<usize> {
        // Read presentation.xml to get slide count
        if let Ok(mut presentation_file) = archive.by_name("ppt/presentation.xml") {
            let mut content = String::new();
            presentation_file.read_to_string(&mut content)?;
            
            // Count slide references in presentation.xml
            let slide_count = content.matches("p:sldId").count();
            return Ok(slide_count);
        }
        
        // Fallback: count slide files directly
        let mut count = 0;
        for i in 1..=100 { // reasonable upper limit
            let slide_name = format!("ppt/slides/slide{}.xml", i);
            if archive.by_name(&slide_name).is_ok() {
                count += 1;
            } else {
                break;
            }
        }
        
        Ok(count)
    }
    
    fn extract_slide_content(xml_content: &str) -> Result<(Option<String>, String)> {
        let mut reader = Reader::from_str(xml_content);
        reader.trim_text(true);
        
        let mut buf = Vec::new();
        let mut current_text = String::new();
        let mut title = None;
        let mut all_text = Vec::new();
        let mut in_text = false;
        let mut is_title = false;
        
        loop {
            match reader.read_event(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    match e.name() {
                        b"a:t" => in_text = true,
                        b"p:ph" => {
                            // Check if this is a title placeholder
                            if let Ok(attrs) = e.attributes().collect::<Result<Vec<_>, _>>() {
                                for attr in attrs {
                                    if attr.key == b"type" && attr.value == b"title" {
                                        is_title = true;
                                    }
                                }
                            }
                        }
                        _ => {}
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_text {
                        let text = e.unescape_and_decode(&reader)?;
                        current_text.push_str(&text);
                    }
                }
                Ok(Event::End(ref e)) => {
                    match e.name() {
                        b"a:t" => {
                            in_text = false;
                            if !current_text.trim().is_empty() {
                                if is_title && title.is_none() {
                                    title = Some(current_text.trim().to_string());
                                } else {
                                    all_text.push(current_text.trim().to_string());
                                }
                                current_text.clear();
                            }
                        }
                        b"a:p" => {
                            is_title = false; // Reset title flag after paragraph
                        }
                        _ => {}
                    }
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(anyhow::anyhow!("Error parsing XML: {}", e)),
                _ => {}
            }
            buf.clear();
        }
        
        let content = if all_text.is_empty() {
            title.clone().unwrap_or_default()
        } else {
            format!("# {}\n\n{}", 
                title.as_deref().unwrap_or("Slide Content"),
                all_text.join("\n\n• ")
            )
        };
        
        Ok((title, content))
    }
    
    fn extract_notes_content(xml_content: &str) -> Result<Option<String>> {
        let mut reader = Reader::from_str(xml_content);
        reader.trim_text(true);
        
        let mut buf = Vec::new();
        let mut text_parts = Vec::new();
        let mut in_text = false;
        
        loop {
            match reader.read_event(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    if e.name() == b"a:t" {
                        in_text = true;
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_text {
                        let text = e.unescape_and_decode(&reader)?;
                        if !text.trim().is_empty() {
                            text_parts.push(text.trim().to_string());
                        }
                    }
                }
                Ok(Event::End(ref e)) => {
                    if e.name() == b"a:t" {
                        in_text = false;
                    }
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(anyhow::anyhow!("Error parsing notes XML: {}", e)),
                _ => {}
            }
            buf.clear();
        }
        
        if text_parts.is_empty() {
            Ok(None)
        } else {
            Ok(Some(text_parts.join("\n\n")))
        }
    }
    
    fn check_for_images(xml_content: &str) -> bool {
        xml_content.contains("a:blip") || xml_content.contains("pic:pic")
    }
    
    fn check_for_tables(xml_content: &str) -> bool {
        xml_content.contains("a:tbl") || xml_content.contains("a:gridCol")
    }
    
    fn check_for_animations(xml_content: &str) -> bool {
        xml_content.contains("p:timing") || xml_content.contains("p:anim")
    }
    
    fn count_words(text: &str) -> u32 {
        text.split_whitespace().count() as u32
    }
}

impl WordParser {
    pub async fn parse_file(file_path: &Path) -> Result<Vec<ImportedContent>> {
        let file = File::open(file_path)
            .context("Failed to open Word file")?;
        
        let mut archive = ZipArchive::new(file)
            .context("Failed to read Word archive")?;
        
        // Extract main document content
        let mut document_file = archive.by_name("word/document.xml")
            .context("Failed to find document.xml in Word file")?;
        
        let mut document_content = String::new();
        document_file.read_to_string(&mut document_content)?;
        
        let sections = Self::extract_document_sections(&document_content)?;
        
        let mut imported_content = Vec::new();
        
        for (index, section) in sections.into_iter().enumerate() {
            if !section.content.trim().is_empty() {
                // Determine content type based on section characteristics
                let content_type = Self::classify_content_type(&section);
                
                imported_content.push(ImportedContent {
                    content_type,
                    title: section.title,
                    content: section.content,
                    metadata: ContentMetadata {
                        source_slide_number: None,
                        source_page_number: Some((index + 1) as u32),
                        has_images: section.has_images,
                        has_tables: section.has_tables,
                        has_animations: false,
                        word_count: Self::count_words(&section.content),
                        extracted_at: Utc::now(),
                    },
                    order: (index + 1) as u32,
                });
            }
        }
        
        Ok(imported_content)
    }
    
    fn extract_document_sections(xml_content: &str) -> Result<Vec<DocumentSection>> {
        let mut reader = Reader::from_str(xml_content);
        reader.trim_text(true);
        
        let mut buf = Vec::new();
        let mut sections = Vec::new();
        let mut current_section = DocumentSection::new();
        let mut current_paragraph = String::new();
        let mut in_text = false;
        let mut in_table = false;
        let mut table_content = Vec::new();
        
        loop {
            match reader.read_event(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    match e.name() {
                        b"w:t" => in_text = true,
                        b"w:tbl" => {
                            in_table = true;
                            table_content.clear();
                        }
                        b"w:drawing" => {
                            current_section.has_images = true;
                        }
                        _ => {}
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_text {
                        let text = e.unescape_and_decode(&reader)?;
                        current_paragraph.push_str(&text);
                    }
                }
                Ok(Event::End(ref e)) => {
                    match e.name() {
                        b"w:t" => {
                            in_text = false;
                        }
                        b"w:p" => {
                            // End of paragraph
                            if !current_paragraph.trim().is_empty() {
                                if in_table {
                                    table_content.push(current_paragraph.trim().to_string());
                                } else {
                                    // Check if this looks like a heading
                                    if Self::is_heading(&current_paragraph) && !current_section.content.is_empty() {
                                        // Start new section
                                        sections.push(current_section);
                                        current_section = DocumentSection::new();
                                        current_section.title = current_paragraph.trim().to_string();
                                    } else {
                                        if current_section.title.is_empty() {
                                            current_section.title = Self::generate_title(&current_paragraph);
                                        }
                                        if !current_section.content.is_empty() {
                                            current_section.content.push_str("\n\n");
                                        }
                                        current_section.content.push_str(current_paragraph.trim());
                                    }
                                }
                                current_paragraph.clear();
                            }
                        }
                        b"w:tbl" => {
                            // End of table
                            in_table = false;
                            current_section.has_tables = true;
                            if !table_content.is_empty() {
                                if !current_section.content.is_empty() {
                                    current_section.content.push_str("\n\n");
                                }
                                current_section.content.push_str("**Table:**\n");
                                current_section.content.push_str(&table_content.join(" | "));
                            }
                            table_content.clear();
                        }
                        _ => {}
                    }
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(anyhow::anyhow!("Error parsing Word XML: {}", e)),
                _ => {}
            }
            buf.clear();
        }
        
        // Add final section if it has content
        if !current_section.content.trim().is_empty() {
            sections.push(current_section);
        }
        
        // If no sections were created, create a single section with all content
        if sections.is_empty() && !current_paragraph.trim().is_empty() {
            let mut section = DocumentSection::new();
            section.title = "Document Content".to_string();
            section.content = current_paragraph;
            sections.push(section);
        }
        
        Ok(sections)
    }
    
    fn is_heading(text: &str) -> bool {
        let text = text.trim();
        
        // Check for typical heading patterns
        if text.len() < 3 || text.len() > 100 {
            return false;
        }
        
        // Check if it ends with a colon or period (common in headings)
        if text.ends_with(':') {
            return true;
        }
        
        // Check if it's all caps or title case
        let words: Vec<&str> = text.split_whitespace().collect();
        if words.len() <= 8 {
            let title_case_count = words.iter()
                .filter(|w| w.chars().next().map_or(false, |c| c.is_uppercase()))
                .count();
            
            if title_case_count == words.len() {
                return true;
            }
        }
        
        false
    }
    
    fn generate_title(content: &str) -> String {
        let first_line = content.lines().next().unwrap_or("").trim();
        if first_line.len() > 50 {
            format!("{}...", &first_line[..47])
        } else if first_line.is_empty() {
            "Document Section".to_string()
        } else {
            first_line.to_string()
        }
    }
    
    fn classify_content_type(section: &DocumentSection) -> String {
        let content = section.content.to_lowercase();
        let title = section.title.to_lowercase();
        
        // Check for quiz/assessment indicators
        if content.contains("question") && (content.contains("answer") || content.contains("choice")) {
            return "Quiz".to_string();
        }
        
        // Check for worksheet indicators
        if content.contains("exercise") || content.contains("activity") || content.contains("worksheet") {
            return "Worksheet".to_string();
        }
        
        // Check for instructor notes indicators
        if title.contains("note") || title.contains("instruction") || title.contains("teacher") {
            return "InstructorNotes".to_string();
        }
        
        // Check for lesson plan indicators
        if title.contains("lesson") || title.contains("plan") || content.contains("objective") {
            return "InstructorNotes".to_string();
        }
        
        // Default to instructor notes for most document content
        "InstructorNotes".to_string()
    }
    
    fn count_words(text: &str) -> u32 {
        text.split_whitespace().count() as u32
    }
}

#[derive(Debug)]
struct DocumentSection {
    title: String,
    content: String,
    has_images: bool,
    has_tables: bool,
}

impl DocumentSection {
    fn new() -> Self {
        Self {
            title: String::new(),
            content: String::new(),
            has_images: false,
            has_tables: false,
        }
    }
}