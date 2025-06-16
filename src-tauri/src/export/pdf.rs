use super::{ExportFormat, ExportOptions, ExportResult, FormatConverter, BrandingOptions};
use crate::content::GeneratedContent;
use anyhow::{Result, Context};
use std::fs;
use chrono::Utc;
use printpdf::*;

pub struct PdfConverter;

impl PdfConverter {
    pub fn new() -> Self {
        Self
    }

    fn content_to_pdf(&self, contents: &[GeneratedContent], options: &ExportOptions) -> Result<Vec<u8>> {
        // Create a new PDF document
        let (doc, page1, layer1) = PdfDocument::new(
            "Curriculum Content Export",
            Mm(210.0), // A4 width
            Mm(297.0), // A4 height
            "Layer 1"
        );
        
        let mut current_layer = doc.get_page(page1).get_layer(layer1);
        let mut current_page = page1;
        let mut y_position = Mm(280.0); // Start near top of page
        
        // Load fonts
        let font_regular = doc.add_builtin_font(BuiltinFont::Helvetica)?;
        let font_bold = doc.add_builtin_font(BuiltinFont::HelveticaBold)?;
        
        // Add title page with branding
        self.add_title_page(&mut current_layer, &font_bold, &font_regular, contents, &options.branding_options)?;
        
        // Add each content item
        for (i, content) in contents.iter().enumerate() {
            // Check if we need a new page
            if y_position < Mm(50.0) {
                let (new_page, new_layer) = doc.add_page(Mm(210.0), Mm(297.0), "Content Layer");
                current_layer = doc.get_page(new_page).get_layer(new_layer);
                current_page = new_page;
                y_position = Mm(280.0);
            }
            
            y_position = self.add_content_to_pdf(
                &mut current_layer,
                &font_bold,
                &font_regular,
                content,
                y_position,
                i + 1
            )?;
        }
        
        // Add footer with export info if metadata is included
        if options.include_metadata {
            self.add_footer(&mut current_layer, &font_regular, contents, options)?;
        }
        
        // Save PDF to bytes
        let mut pdf_bytes = Vec::new();
        {
            let mut buf_writer = std::io::BufWriter::new(&mut pdf_bytes);
            doc.save(&mut buf_writer)?;
        } // buf_writer is dropped here, releasing the borrow
        
        Ok(pdf_bytes)
    }
    
    fn add_title_page(
        &self,
        layer: &mut PdfLayerReference,
        font_bold: &IndirectFontRef,
        font_regular: &IndirectFontRef,
        contents: &[GeneratedContent],
        branding: &Option<BrandingOptions>
    ) -> Result<()> {
        // Main title
        layer.use_text("Curriculum Content Export", 24.0_f32, Mm(20.0), Mm(250.0), font_bold);
        
        // Institution name if provided
        let mut current_y = Mm(235.0);
        if let Some(branding) = branding {
            if let Some(institution) = &branding.institution_name {
                layer.use_text(
                    &format!("Prepared for {}", institution),
                    14.0_f32,
                    Mm(20.0),
                    current_y,
                    font_bold
                );
                current_y = current_y - Mm(15.0);
            }
        }
        
        // Subtitle with generation info
        let generation_time = Utc::now().format("%Y-%m-%d %H:%M:%S UTC").to_string();
        layer.use_text(
            &format!("Generated on {}", generation_time),
            12.0_f32,
            Mm(20.0),
            current_y,
            font_regular
        );
        current_y = current_y - Mm(15.0);
        
        // Content summary
        current_y = current_y - Mm(10.0);
        layer.use_text("Content Summary:", 16.0_f32, Mm(20.0), current_y, font_bold);
        
        let mut y_pos = current_y - Mm(15.0);
        for (i, content) in contents.iter().enumerate() {
            let summary_text = format!(
                "{}. {} ({})",
                i + 1,
                content.title,
                self.format_content_type(&content.content_type)
            );
            layer.use_text(&summary_text, 12.0, Mm(25.0), y_pos, font_regular);
            y_pos = y_pos - Mm(7.0);
            
            if y_pos < Mm(50.0) {
                break; // Prevent overflow on title page
            }
        }
        
        // Statistics
        let total_words: usize = contents.iter().map(|c| c.metadata.word_count).sum();
        let stats_y = y_pos - Mm(15.0);
        
        layer.use_text("Statistics:", 14.0_f32, Mm(20.0), stats_y, font_bold);
        layer.use_text(
            &format!("Total Content Items: {}", contents.len()),
            12.0_f32,
            Mm(25.0),
            stats_y - Mm(10.0),
            font_regular
        );
        layer.use_text(
            &format!("Total Word Count: {} words", total_words),
            12.0_f32,
            Mm(25.0),
            stats_y - Mm(20.0),
            font_regular
        );
        
        Ok(())
    }
    
    fn add_content_to_pdf(
        &self,
        layer: &mut PdfLayerReference,
        font_bold: &IndirectFontRef,
        font_regular: &IndirectFontRef,
        content: &GeneratedContent,
        mut y_position: Mm,
        section_number: usize
    ) -> Result<Mm> {
        // Content header
        let header_text = format!("{}. {}", section_number, content.title);
        layer.use_text(&header_text, 18.0_f32, Mm(20.0), y_position, font_bold);
        y_position = y_position - Mm(8.0);
        
        // Content type and metadata
        let meta_text = format!(
            "{} | Duration: {} | Difficulty: {} | Words: {}",
            self.format_content_type(&content.content_type),
            content.metadata.estimated_duration,
            content.metadata.difficulty_level,
            content.metadata.word_count
        );
        layer.use_text(&meta_text, 10.0_f32, Mm(20.0), y_position, font_regular);
        y_position = y_position - Mm(15.0);
        
        // Content body
        y_position = self.add_formatted_content(
            layer,
            font_regular,
            font_bold,
            &content.content,
            &content.content_type,
            y_position
        )?;
        
        y_position = y_position - Mm(20.0); // Space between sections
        
        Ok(y_position)
    }
    
    fn add_formatted_content(
        &self,
        layer: &mut PdfLayerReference,
        font_regular: &IndirectFontRef,
        font_bold: &IndirectFontRef,
        content: &str,
        content_type: &crate::content::ContentType,
        mut y_position: Mm
    ) -> Result<Mm> {
        match content_type {
            crate::content::ContentType::Slides => {
                y_position = self.format_slides_pdf(layer, font_regular, font_bold, content, y_position)?;
            }
            crate::content::ContentType::Quiz => {
                y_position = self.format_quiz_pdf(layer, font_regular, font_bold, content, y_position)?;
            }
            crate::content::ContentType::Worksheet => {
                y_position = self.format_worksheet_pdf(layer, font_regular, font_bold, content, y_position)?;
            }
            crate::content::ContentType::InstructorNotes => {
                y_position = self.format_instructor_notes_pdf(layer, font_regular, font_bold, content, y_position)?;
            }
            crate::content::ContentType::ActivityGuide => {
                y_position = self.format_activity_guide_pdf(layer, font_regular, font_bold, content, y_position)?;
            }
        }
        
        Ok(y_position)
    }
    
    fn format_slides_pdf(
        &self,
        layer: &mut PdfLayerReference,
        font_regular: &IndirectFontRef,
        font_bold: &IndirectFontRef,
        content: &str,
        mut y_position: Mm
    ) -> Result<Mm> {
        let slides: Vec<&str> = content.split("---SLIDE---").collect();
        let mut slide_count = 0;
        
        for slide in slides.iter() {
            if slide.trim().is_empty() {
                continue;
            }
            
            slide_count += 1;
            
            // Slide header
            let slide_title = format!("Slide {}", slide_count);
            layer.use_text(&slide_title, 14.0_f32, Mm(25.0), y_position, font_bold);
            y_position = y_position - Mm(8.0);
            
            // Slide content
            let lines = slide.trim().lines();
            for line in lines {
                if line.trim().is_empty() {
                    continue;
                }
                
                if line.starts_with("SPEAKER_NOTES:") {
                    layer.use_text("Speaker Notes:", 12.0, Mm(30.0), y_position, font_bold);
                    y_position = y_position - Mm(6.0);
                    
                    let notes = &line[14..].trim();
                    y_position = self.add_wrapped_text(layer, font_regular, notes, Mm(35.0), y_position, 10.0_f32)?;
                } else {
                    y_position = self.add_wrapped_text(layer, font_regular, line.trim(), Mm(30.0), y_position, 11.0_f32)?;
                }
                
                y_position = y_position - Mm(3.0);
            }
            
            y_position = y_position - Mm(8.0); // Space between slides
        }
        
        Ok(y_position)
    }
    
    fn format_quiz_pdf(
        &self,
        layer: &mut PdfLayerReference,
        font_regular: &IndirectFontRef,
        font_bold: &IndirectFontRef,
        content: &str,
        mut y_position: Mm
    ) -> Result<Mm> {
        let questions: Vec<&str> = content.split("---QUESTION---").collect();
        let mut question_count = 0;
        
        for question in questions.iter() {
            if question.trim().is_empty() {
                continue;
            }
            
            question_count += 1;
            
            // Question header
            let question_title = format!("Question {}", question_count);
            layer.use_text(&question_title, 14.0_f32, Mm(25.0), y_position, font_bold);
            y_position = y_position - Mm(8.0);
            
            let lines: Vec<&str> = question.trim().lines().collect();
            for line in lines {
                if line.starts_with("Q:") {
                    let question_text = format!("Question: {}", &line[2..].trim());
                    y_position = self.add_wrapped_text(layer, font_bold, &question_text, Mm(30.0), y_position, 11.0_f32)?;
                } else if line.starts_with("A)") || line.starts_with("B)") || line.starts_with("C)") || line.starts_with("D)") {
                    y_position = self.add_wrapped_text(layer, font_regular, line.trim(), Mm(35.0), y_position, 10.0_f32)?;
                } else if line.starts_with("ANSWER:") {
                    let answer_text = format!("Correct Answer: {}", &line[7..].trim());
                    y_position = self.add_wrapped_text(layer, font_bold, &answer_text, Mm(30.0), y_position, 10.0_f32)?;
                } else if line.starts_with("EXPLANATION:") {
                    let explanation_text = format!("Explanation: {}", &line[12..].trim());
                    y_position = self.add_wrapped_text(layer, font_regular, &explanation_text, Mm(30.0), y_position, 10.0_f32)?;
                } else if !line.trim().is_empty() {
                    y_position = self.add_wrapped_text(layer, font_regular, line.trim(), Mm(30.0), y_position, 10.0_f32)?;
                }
                y_position = y_position - Mm(2.0);
            }
            
            y_position = y_position - Mm(8.0); // Space between questions
        }
        
        Ok(y_position)
    }
    
    fn format_worksheet_pdf(
        &self,
        layer: &mut PdfLayerReference,
        font_regular: &IndirectFontRef,
        font_bold: &IndirectFontRef,
        content: &str,
        mut y_position: Mm
    ) -> Result<Mm> {
        let sections: Vec<&str> = content.split("---SECTION---").collect();
        let mut section_count = 0;
        
        for section in sections.iter() {
            if section.trim().is_empty() {
                continue;
            }
            
            if section_count > 0 {
                let section_title = format!("Section {}", section_count);
                layer.use_text(&section_title, 14.0_f32, Mm(25.0), y_position, font_bold);
                y_position = y_position - Mm(8.0);
            }
            section_count += 1;
            
            let lines: Vec<&str> = section.trim().lines().collect();
            for line in lines {
                if line.starts_with("EXERCISE:") {
                    layer.use_text("Exercise", 12.0, Mm(30.0), y_position, font_bold);
                    y_position = y_position - Mm(6.0);
                    y_position = self.add_wrapped_text(layer, font_regular, &line[9..].trim(), Mm(35.0), y_position, 11.0_f32)?;
                } else if line.starts_with("ANSWER_SPACE:") {
                    layer.use_text("Answer:", 12.0, Mm(30.0), y_position, font_bold);
                    y_position = y_position - Mm(6.0);
                    
                    let space_size = line[13..].trim().parse::<usize>().unwrap_or(3);
                    for _ in 0..space_size {
                        layer.use_text("_".repeat(60).as_str(), 10.0_f32, Mm(35.0), y_position, font_regular);
                        y_position = y_position - Mm(8.0);
                    }
                } else if !line.trim().is_empty() {
                    y_position = self.add_wrapped_text(layer, font_regular, line.trim(), Mm(30.0), y_position, 11.0_f32)?;
                }
                y_position = y_position - Mm(2.0);
            }
            
            y_position = y_position - Mm(8.0); // Space between sections
        }
        
        Ok(y_position)
    }
    
    fn format_instructor_notes_pdf(
        &self,
        layer: &mut PdfLayerReference,
        font_regular: &IndirectFontRef,
        font_bold: &IndirectFontRef,
        content: &str,
        mut y_position: Mm
    ) -> Result<Mm> {
        let lines: Vec<&str> = content.lines().collect();
        
        for line in lines {
            if line.starts_with("TIMING:") {
                layer.use_text("⏰ Timing", 12.0, Mm(25.0), y_position, font_bold);
                y_position = y_position - Mm(6.0);
                y_position = self.add_wrapped_text(layer, font_regular, &line[7..].trim(), Mm(30.0), y_position, 11.0_f32)?;
            } else if line.starts_with("OBJECTIVES:") {
                layer.use_text("🎯 Learning Objectives", 12.0, Mm(25.0), y_position, font_bold);
                y_position = y_position - Mm(6.0);
            } else if line.starts_with("PREPARATION:") {
                layer.use_text("📋 Preparation", 12.0, Mm(25.0), y_position, font_bold);
                y_position = y_position - Mm(6.0);
            } else if line.starts_with("KEY_POINTS:") {
                layer.use_text("🔑 Key Points", 12.0, Mm(25.0), y_position, font_bold);
                y_position = y_position - Mm(6.0);
            } else if line.starts_with("ACTIVITIES:") {
                layer.use_text("🎯 Activities", 12.0, Mm(25.0), y_position, font_bold);
                y_position = y_position - Mm(6.0);
            } else if line.starts_with("ASSESSMENT:") {
                layer.use_text("✅ Assessment", 12.0, Mm(25.0), y_position, font_bold);
                y_position = y_position - Mm(6.0);
            } else if line.starts_with("NOTES:") {
                layer.use_text("📝 Additional Notes", 12.0, Mm(25.0), y_position, font_bold);
                y_position = y_position - Mm(6.0);
            } else if !line.trim().is_empty() {
                if line.trim().starts_with("-") || line.trim().starts_with("*") {
                    let bullet_text = format!("• {}", &line.trim()[1..].trim());
                    y_position = self.add_wrapped_text(layer, font_regular, &bullet_text, Mm(30.0), y_position, 10.0_f32)?;
                } else {
                    y_position = self.add_wrapped_text(layer, font_regular, line.trim(), Mm(30.0), y_position, 11.0_f32)?;
                }
            }
            y_position = y_position - Mm(3.0);
        }
        
        Ok(y_position)
    }
    
    fn format_activity_guide_pdf(
        &self,
        layer: &mut PdfLayerReference,
        font_regular: &IndirectFontRef,
        font_bold: &IndirectFontRef,
        content: &str,
        mut y_position: Mm
    ) -> Result<Mm> {
        let activities: Vec<&str> = content.split("---ACTIVITY---").collect();
        let mut activity_count = 0;
        
        for activity in activities.iter() {
            if activity.trim().is_empty() {
                continue;
            }
            
            activity_count += 1;
            
            let activity_title = format!("Activity {}", activity_count);
            layer.use_text(&activity_title, 14.0_f32, Mm(25.0), y_position, font_bold);
            y_position = y_position - Mm(8.0);
            
            let lines: Vec<&str> = activity.trim().lines().collect();
            for line in lines {
                if line.starts_with("TITLE:") {
                    y_position = self.add_wrapped_text(layer, font_bold, &line[6..].trim(), Mm(30.0), y_position, 12.0_f32)?;
                } else if line.starts_with("DURATION:") {
                    let duration_text = format!("Duration: {}", &line[9..].trim());
                    y_position = self.add_wrapped_text(layer, font_bold, &duration_text, Mm(30.0), y_position, 10.0_f32)?;
                } else if line.starts_with("MATERIALS:") {
                    layer.use_text("Materials:", 11.0_f32, Mm(30.0), y_position, font_bold);
                    y_position = y_position - Mm(6.0);
                } else if line.starts_with("INSTRUCTIONS:") {
                    layer.use_text("Instructions:", 11.0_f32, Mm(30.0), y_position, font_bold);
                    y_position = y_position - Mm(6.0);
                } else if line.starts_with("DEBRIEF:") {
                    layer.use_text("Debrief Questions:", 11.0_f32, Mm(30.0), y_position, font_bold);
                    y_position = y_position - Mm(6.0);
                } else if !line.trim().is_empty() {
                    if line.starts_with("- ") || line.starts_with("* ") || line.starts_with("1. ") {
                        y_position = self.add_wrapped_text(layer, font_regular, line.trim(), Mm(35.0), y_position, 10.0_f32)?;
                    } else {
                        y_position = self.add_wrapped_text(layer, font_regular, line.trim(), Mm(30.0), y_position, 10.0_f32)?;
                    }
                }
                y_position = y_position - Mm(2.0);
            }
            
            y_position = y_position - Mm(8.0); // Space between activities
        }
        
        Ok(y_position)
    }
    
    fn add_wrapped_text(
        &self,
        layer: &mut PdfLayerReference,
        font: &IndirectFontRef,
        text: &str,
        x_position: Mm,
        mut y_position: Mm,
        font_size: f32
    ) -> Result<Mm> {
        // Simple text wrapping - split long lines
        let max_width = 60; // characters per line
        
        if text.len() <= max_width {
            layer.use_text(text, font_size, x_position, y_position, font);
            y_position = y_position - Mm(font_size * 0.4_f32);
        } else {
            let words: Vec<&str> = text.split_whitespace().collect();
            let mut current_line = String::new();
            
            for word in words {
                if current_line.len() + word.len() + 1 <= max_width {
                    if !current_line.is_empty() {
                        current_line.push(' ');
                    }
                    current_line.push_str(word);
                } else {
                    if !current_line.is_empty() {
                        layer.use_text(&current_line, font_size, x_position, y_position, font);
                        y_position = y_position - Mm(font_size * 0.4_f32);
                    }
                    current_line = word.to_string();
                }
            }
            
            if !current_line.is_empty() {
                layer.use_text(&current_line, font_size, x_position, y_position, font);
                y_position = y_position - Mm(font_size * 0.4_f32);
            }
        }
        
        Ok(y_position)
    }
    
    fn add_footer(
        &self,
        layer: &mut PdfLayerReference,
        font_regular: &IndirectFontRef,
        contents: &[GeneratedContent],
        options: &ExportOptions
    ) -> Result<()> {
        let footer_y = Mm(20.0);
        
        layer.use_text("Export Information", 12.0, Mm(20.0), footer_y, font_regular);
        layer.use_text(
            &format!("Export Format: PDF • Total Items: {} • Path: {}", 
                contents.len(), 
                options.output_path.display()
            ),
            8.0_f32,
            Mm(20.0),
            footer_y - Mm(8.0),
            font_regular
        );
        
        Ok(())
    }
    
    fn format_content_type(&self, content_type: &crate::content::ContentType) -> &'static str {
        match content_type {
            crate::content::ContentType::Slides => "Presentation Slides",
            crate::content::ContentType::InstructorNotes => "Instructor Notes",
            crate::content::ContentType::Worksheet => "Worksheet",
            crate::content::ContentType::Quiz => "Quiz",
            crate::content::ContentType::ActivityGuide => "Activity Guide",
        }
    }
}

#[async_trait::async_trait]
impl FormatConverter for PdfConverter {
    fn supported_format(&self) -> ExportFormat {
        ExportFormat::Pdf
    }

    async fn convert(&self, contents: &[GeneratedContent], options: &ExportOptions) -> Result<ExportResult> {
        // Generate the PDF content
        let pdf_bytes = self.content_to_pdf(contents, options)
            .context("Failed to create PDF document")?;

        // Ensure the output directory exists
        if let Some(parent) = options.output_path.parent() {
            fs::create_dir_all(parent)
                .context("Failed to create output directory")?;
        }

        // Write the PDF file
        fs::write(&options.output_path, &pdf_bytes)
            .context("Failed to write PDF file")?;

        // Get file size
        let file_size = fs::metadata(&options.output_path)
            .map(|m| m.len())
            .unwrap_or(0);

        Ok(ExportResult {
            success: true,
            output_path: options.output_path.clone(),
            file_size: Some(file_size),
            error_message: None,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::content::{ContentType, generator::ContentMetadata};

    fn create_test_content() -> GeneratedContent {
        GeneratedContent {
            content_type: ContentType::Slides,
            title: "Test Lesson".to_string(),
            content: "---SLIDE---\n# Introduction\nThis is slide 1\n---SLIDE---\n# Main Content\nThis is slide 2".to_string(),
            metadata: ContentMetadata {
                word_count: 15,
                estimated_duration: "30 minutes".to_string(),
                difficulty_level: "Intermediate".to_string(),
            },
        }
    }

    #[tokio::test]
    async fn test_pdf_conversion() {
        let converter = PdfConverter::new();
        let content = create_test_content();
        
        let result = converter.content_to_pdf(&[content], &ExportOptions {
            format: ExportFormat::Pdf,
            output_path: std::path::PathBuf::from("/tmp/test.pdf"),
            template_name: None,
            include_metadata: true,
        });
        
        assert!(result.is_ok());
        let pdf_bytes = result.unwrap();
        assert!(!pdf_bytes.is_empty());
        
        // Check that it starts with PDF header
        let pdf_header = &pdf_bytes[0..4];
        assert_eq!(pdf_header, b"%PDF");
    }

    #[tokio::test]
    async fn test_full_pdf_export() {
        let converter = PdfConverter::new();
        let contents = vec![create_test_content()];
        
        let temp_dir = std::env::temp_dir();
        let output_path = temp_dir.join("test_export.pdf");
        
        let options = ExportOptions {
            format: ExportFormat::Pdf,
            output_path: output_path.clone(),
            template_name: None,
            include_metadata: true,
        };

        let result = converter.convert(&contents, &options).await;
        assert!(result.is_ok());
        
        let export_result = result.unwrap();
        assert!(export_result.success);
        assert!(export_result.file_size.is_some());
        assert!(export_result.file_size.unwrap() > 0);
        
        // Verify file exists and has PDF header
        assert!(output_path.exists());
        let file_content = std::fs::read(&output_path).unwrap();
        assert!(file_content.starts_with(b"%PDF"));
        
        // Cleanup
        if output_path.exists() {
            let _ = std::fs::remove_file(output_path);
        }
    }
}