use super::{ExportFormat, ExportOptions, ExportResult, FormatConverter};
use crate::content::GeneratedContent;
use anyhow::{Result, Context};
use std::fs;
use chrono::Utc;

pub struct MarkdownConverter;

impl MarkdownConverter {
    pub fn new() -> Self {
        Self
    }

    fn content_to_markdown(&self, content: &GeneratedContent) -> Result<String> {
        let mut markdown = String::new();
        
        // Add frontmatter with metadata
        markdown.push_str("---\n");
        markdown.push_str(&format!("title: {}\n", content.title));
        markdown.push_str(&format!("content_type: {}\n", content.content_type));
        markdown.push_str(&format!("word_count: {}\n", content.metadata.word_count));
        markdown.push_str(&format!("estimated_duration: {}\n", content.metadata.estimated_duration));
        markdown.push_str(&format!("difficulty_level: {}\n", content.metadata.difficulty_level));
        markdown.push_str(&format!("generated_at: {}\n", Utc::now().to_rfc3339()));
        markdown.push_str("---\n\n");

        // Add title
        markdown.push_str(&format!("# {}\n\n", content.title));

        // Add content type badge
        markdown.push_str(&format!("**Content Type:** {}\n\n", self.format_content_type(&content.content_type)));

        // Add metadata section
        markdown.push_str("## Overview\n\n");
        markdown.push_str(&format!("- **Estimated Duration:** {}\n", content.metadata.estimated_duration));
        markdown.push_str(&format!("- **Difficulty Level:** {}\n", content.metadata.difficulty_level));
        markdown.push_str(&format!("- **Word Count:** {} words\n\n", content.metadata.word_count));

        // Add main content
        markdown.push_str("## Content\n\n");
        markdown.push_str(&self.format_content_body(&content.content, &content.content_type)?);

        Ok(markdown)
    }

    fn format_content_type(&self, content_type: &crate::content::ContentType) -> &'static str {
        match content_type {
            crate::content::ContentType::Slides => "📊 Presentation Slides",
            crate::content::ContentType::InstructorNotes => "📝 Instructor Notes",
            crate::content::ContentType::Worksheet => "📋 Worksheet",
            crate::content::ContentType::Quiz => "❓ Quiz",
            crate::content::ContentType::ActivityGuide => "🎯 Activity Guide",
        }
    }

    fn format_content_body(&self, content: &str, content_type: &crate::content::ContentType) -> Result<String> {
        match content_type {
            crate::content::ContentType::Slides => self.format_slides_content(content),
            crate::content::ContentType::Quiz => self.format_quiz_content(content),
            crate::content::ContentType::Worksheet => self.format_worksheet_content(content),
            crate::content::ContentType::InstructorNotes => self.format_instructor_notes_content(content),
            crate::content::ContentType::ActivityGuide => self.format_activity_guide_content(content),
        }
    }

    fn format_slides_content(&self, content: &str) -> Result<String> {
        let mut formatted = String::new();
        
        // Split content into slides (assuming slides are separated by slide markers)
        let slides: Vec<&str> = content.split("---SLIDE---").collect();
        
        for (i, slide) in slides.iter().enumerate() {
            if slide.trim().is_empty() {
                continue;
            }
            
            formatted.push_str(&format!("### Slide {}\n\n", i + 1));
            formatted.push_str(&slide.trim());
            formatted.push_str("\n\n");
            
            // Add speaker notes section if present
            if slide.contains("SPEAKER_NOTES:") {
                let parts: Vec<&str> = slide.split("SPEAKER_NOTES:").collect();
                if parts.len() > 1 {
                    formatted.push_str("#### Speaker Notes\n\n");
                    formatted.push_str("> ");
                    formatted.push_str(&parts[1].trim().replace("\n", "\n> "));
                    formatted.push_str("\n\n");
                }
            }
        }
        
        Ok(formatted)
    }

    fn format_quiz_content(&self, content: &str) -> Result<String> {
        let mut formatted = String::new();
        
        // Split content into questions (assuming questions are separated by question markers)
        let questions: Vec<&str> = content.split("---QUESTION---").collect();
        
        for (i, question) in questions.iter().enumerate() {
            if question.trim().is_empty() {
                continue;
            }
            
            formatted.push_str(&format!("### Question {}\n\n", i + 1));
            
            // Parse question components
            let lines: Vec<&str> = question.trim().lines().collect();
            for line in lines {
                if line.starts_with("Q:") {
                    formatted.push_str(&format!("**Question:** {}\n\n", &line[2..].trim()));
                } else if line.starts_with("A)") || line.starts_with("B)") || line.starts_with("C)") || line.starts_with("D)") {
                    formatted.push_str(&format!("- {}\n", line.trim()));
                } else if line.starts_with("ANSWER:") {
                    formatted.push_str(&format!("\n**Answer:** {}\n", &line[7..].trim()));
                } else if line.starts_with("EXPLANATION:") {
                    formatted.push_str(&format!("**Explanation:** {}\n", &line[12..].trim()));
                } else if !line.trim().is_empty() {
                    formatted.push_str(&format!("{}\n", line.trim()));
                }
            }
            formatted.push_str("\n");
        }
        
        Ok(formatted)
    }

    fn format_worksheet_content(&self, content: &str) -> Result<String> {
        let mut formatted = String::new();
        
        // Split content into sections (assuming sections are separated by section markers)
        let sections: Vec<&str> = content.split("---SECTION---").collect();
        
        for (i, section) in sections.iter().enumerate() {
            if section.trim().is_empty() {
                continue;
            }
            
            if i > 0 {
                formatted.push_str(&format!("### Section {}\n\n", i));
            }
            
            // Process worksheet content with proper formatting
            let lines: Vec<&str> = section.trim().lines().collect();
            for line in lines {
                if line.starts_with("EXERCISE:") {
                    formatted.push_str(&format!("#### Exercise\n\n{}\n\n", &line[9..].trim()));
                } else if line.starts_with("ANSWER_SPACE:") {
                    let space_size = line[13..].trim().parse::<usize>().unwrap_or(3);
                    formatted.push_str("**Answer:**\n\n");
                    for _ in 0..space_size {
                        formatted.push_str("_".repeat(50).as_str());
                        formatted.push_str("\n\n");
                    }
                } else if !line.trim().is_empty() {
                    formatted.push_str(&format!("{}\n", line.trim()));
                }
            }
            formatted.push_str("\n");
        }
        
        Ok(formatted)
    }

    fn format_instructor_notes_content(&self, content: &str) -> Result<String> {
        let mut formatted = String::new();
        
        // Parse instructor notes with structured sections
        let lines: Vec<&str> = content.lines().collect();
        let mut current_section = String::new();
        
        for line in lines {
            if line.starts_with("TIMING:") {
                formatted.push_str(&format!("### ⏰ Timing\n\n{}\n\n", &line[7..].trim()));
            } else if line.starts_with("OBJECTIVES:") {
                formatted.push_str("### 🎯 Learning Objectives\n\n");
                current_section = "objectives".to_string();
            } else if line.starts_with("PREPARATION:") {
                formatted.push_str("### 📋 Preparation\n\n");
                current_section = "preparation".to_string();
            } else if line.starts_with("KEY_POINTS:") {
                formatted.push_str("### 🔑 Key Points\n\n");
                current_section = "key_points".to_string();
            } else if line.starts_with("ACTIVITIES:") {
                formatted.push_str("### 🎯 Activities\n\n");
                current_section = "activities".to_string();
            } else if line.starts_with("ASSESSMENT:") {
                formatted.push_str("### ✅ Assessment\n\n");
                current_section = "assessment".to_string();
            } else if line.starts_with("NOTES:") {
                formatted.push_str("### 📝 Additional Notes\n\n");
                current_section = "notes".to_string();
            } else if !line.trim().is_empty() {
                if current_section == "objectives" || current_section == "key_points" {
                    formatted.push_str(&format!("- {}\n", line.trim()));
                } else {
                    formatted.push_str(&format!("{}\n", line.trim()));
                }
            } else if !current_section.is_empty() {
                formatted.push_str("\n");
            }
        }
        
        Ok(formatted)
    }

    fn format_activity_guide_content(&self, content: &str) -> Result<String> {
        let mut formatted = String::new();
        
        // Parse activity guide with structured sections
        let activities: Vec<&str> = content.split("---ACTIVITY---").collect();
        
        for (i, activity) in activities.iter().enumerate() {
            if activity.trim().is_empty() {
                continue;
            }
            
            formatted.push_str(&format!("### Activity {}\n\n", i + 1));
            
            let lines: Vec<&str> = activity.trim().lines().collect();
            for line in lines {
                if line.starts_with("TITLE:") {
                    formatted.push_str(&format!("**{} **\n\n", &line[6..].trim()));
                } else if line.starts_with("DURATION:") {
                    formatted.push_str(&format!("**Duration:** {}\n\n", &line[9..].trim()));
                } else if line.starts_with("MATERIALS:") {
                    formatted.push_str("**Materials:**\n");
                } else if line.starts_with("INSTRUCTIONS:") {
                    formatted.push_str("**Instructions:**\n\n");
                } else if line.starts_with("DEBRIEF:") {
                    formatted.push_str("**Debrief Questions:**\n\n");
                } else if !line.trim().is_empty() {
                    if line.starts_with("- ") || line.starts_with("* ") || line.starts_with("1. ") {
                        formatted.push_str(&format!("{}\n", line.trim()));
                    } else {
                        formatted.push_str(&format!("{}\n", line.trim()));
                    }
                }
            }
            formatted.push_str("\n");
        }
        
        Ok(formatted)
    }

    fn create_combined_markdown(&self, contents: &[GeneratedContent], options: &ExportOptions) -> Result<String> {
        let mut combined = String::new();
        
        // Add document header
        combined.push_str("# Curriculum Content Export\n\n");
        combined.push_str(&format!("**Generated:** {}\n", Utc::now().format("%Y-%m-%d %H:%M:%S UTC")));
        combined.push_str(&format!("**Content Types:** {}\n\n", 
            contents.iter()
                .map(|c| format!("{}", c.content_type))
                .collect::<Vec<_>>()
                .join(", ")
        ));

        // Add table of contents
        combined.push_str("## Table of Contents\n\n");
        for (i, content) in contents.iter().enumerate() {
            combined.push_str(&format!("{}. [{}](#{})\n", 
                i + 1, 
                content.title,
                content.title.to_lowercase().replace(" ", "-").replace("'", "")
            ));
        }
        combined.push_str("\n---\n\n");

        // Add each content section
        for (i, content) in contents.iter().enumerate() {
            if i > 0 {
                combined.push_str("\n---\n\n");
            }
            
            let content_md = self.content_to_markdown(content)
                .context(format!("Failed to convert {} to markdown", content.title))?;
            combined.push_str(&content_md);
        }

        // Add footer if metadata is included
        if options.include_metadata {
            combined.push_str("\n---\n\n");
            combined.push_str("## Export Information\n\n");
            combined.push_str(&format!("- **Export Format:** Markdown\n"));
            combined.push_str(&format!("- **Total Content Items:** {}\n", contents.len()));
            combined.push_str(&format!("- **Total Word Count:** {} words\n", 
                contents.iter().map(|c| c.metadata.word_count).sum::<usize>()
            ));
            combined.push_str(&format!("- **Export Path:** {}\n", options.output_path.display()));
        }

        Ok(combined)
    }
}

#[async_trait::async_trait]
impl FormatConverter for MarkdownConverter {
    fn supported_format(&self) -> ExportFormat {
        ExportFormat::Markdown
    }

    async fn convert(&self, contents: &[GeneratedContent], options: &ExportOptions) -> Result<ExportResult> {
        // Generate the combined markdown content
        let markdown_content = self.create_combined_markdown(contents, options)
            .context("Failed to create combined markdown document")?;

        // Ensure the output directory exists
        if let Some(parent) = options.output_path.parent() {
            fs::create_dir_all(parent)
                .context("Failed to create output directory")?;
        }

        // Write the markdown file
        fs::write(&options.output_path, &markdown_content)
            .context("Failed to write markdown file")?;

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
    use crate::content::{ContentType, ContentMetadata};
    use std::path::PathBuf;

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
    async fn test_markdown_conversion() {
        let converter = MarkdownConverter::new();
        let content = create_test_content();
        
        let result = converter.content_to_markdown(&content);
        assert!(result.is_ok());
        
        let markdown = result.unwrap();
        assert!(markdown.contains("# Test Lesson"));
        assert!(markdown.contains("📊 Presentation Slides"));
        assert!(markdown.contains("### Slide 1"));
        assert!(markdown.contains("### Slide 2"));
    }

    #[tokio::test]
    async fn test_full_export() {
        let converter = MarkdownConverter::new();
        let contents = vec![create_test_content()];
        
        let temp_dir = std::env::temp_dir();
        let output_path = temp_dir.join("test_export.md");
        
        let options = ExportOptions {
            format: ExportFormat::Markdown,
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
        
        // Cleanup
        if output_path.exists() {
            let _ = fs::remove_file(output_path);
        }
    }
}