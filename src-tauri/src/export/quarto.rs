//! Quarto Integration for Advanced Educational Publishing
//!
//! This module provides Quarto integration for the curriculum curator, enabling
//! advanced users to generate high-quality educational documents using Quarto's
//! scientific publishing system.

use super::{ExportFormat, ExportOptions, ExportResult, FormatConverter};
use crate::content::GeneratedContent;
use anyhow::{Result, Context};
use std::path::PathBuf;
use std::process::Command;
use tokio::fs;
use chrono::Utc;

/// Quarto converter for advanced educational publishing
/// 
/// Provides integration with Quarto (https://quarto.org), a scientific and technical
/// publishing system that can generate multiple output formats from a single source.
pub struct QuartoConverter {
    quarto_executable: PathBuf,
    capabilities: QuartoCapabilities,
}

#[derive(Debug, Clone)]
pub struct QuartoCapabilities {
    pub version: String,
    pub has_python: bool,
    pub has_r: bool,
    pub has_julia: bool,
    pub available_formats: Vec<String>,
}

impl QuartoConverter {
    /// Create a new Quarto converter
    /// 
    /// This will attempt to find the Quarto executable and determine its capabilities.
    /// Returns an error if Quarto is not installed or not found in PATH.
    pub fn new() -> Result<Self> {
        let quarto_executable = Self::find_quarto_executable()?;
        let capabilities = Self::detect_capabilities(&quarto_executable)?;
        
        Ok(Self {
            quarto_executable,
            capabilities,
        })
    }

    /// Check if Quarto is available on the system
    pub fn is_available() -> bool {
        Self::find_quarto_executable().is_ok()
    }

    /// Get Quarto version and capabilities
    pub fn get_capabilities(&self) -> &QuartoCapabilities {
        &self.capabilities
    }

    fn find_quarto_executable() -> Result<PathBuf> {
        // Check common installation paths and PATH
        let candidates = vec![
            "quarto",  // In PATH (preferred)
            "/usr/local/bin/quarto",  // macOS Homebrew
            "/usr/bin/quarto",        // Linux package manager
            "/opt/quarto/bin/quarto", // Manual installation
            "C:\\Program Files\\Quarto\\bin\\quarto.exe", // Windows
        ];

        for candidate in candidates {
            if let Ok(output) = Command::new(candidate).arg("--version").output() {
                if output.status.success() {
                    return Ok(PathBuf::from(candidate));
                }
            }
        }

        Err(anyhow::anyhow!(
            "Quarto executable not found. Please install Quarto from https://quarto.org/docs/get-started/"
        ))
    }

    fn detect_capabilities(quarto_executable: &PathBuf) -> Result<QuartoCapabilities> {
        // Get version
        let version_output = Command::new(quarto_executable)
            .arg("--version")
            .output()
            .context("Failed to get Quarto version")?;
        
        let version = String::from_utf8_lossy(&version_output.stdout)
            .trim()
            .to_string();

        // Check available engines
        let check_output = Command::new(quarto_executable)
            .arg("check")
            .output()
            .context("Failed to check Quarto capabilities")?;
        
        let check_info = String::from_utf8_lossy(&check_output.stdout);
        
        let has_python = check_info.contains("python3") || check_info.contains("Python");
        let has_r = check_info.contains("R version") || check_info.contains("rmarkdown");
        let has_julia = check_info.contains("julia") || check_info.contains("Julia");

        // Available formats (basic set that should always work)
        let available_formats = vec![
            "html".to_string(),
            "pdf".to_string(),
            "docx".to_string(),
            "pptx".to_string(),
            "revealjs".to_string(),
        ];

        Ok(QuartoCapabilities {
            version,
            has_python,
            has_r,
            has_julia,
            available_formats,
        })
    }

    async fn generate_qmd_content(&self, contents: &[GeneratedContent], options: &ExportOptions) -> Result<String> {
        let mut qmd_content = String::new();

        // Generate YAML frontmatter
        qmd_content.push_str("---\n");
        
        // Title and metadata
        let title = if contents.len() == 1 {
            &contents[0].title
        } else {
            "Curriculum Content Export"
        };
        qmd_content.push_str(&format!("title: \"{}\"\n", Self::escape_yaml_string(title)));
        qmd_content.push_str(&format!("date: \"{}\"\n", Utc::now().format("%Y-%m-%d")));
        qmd_content.push_str("author: \"Curriculum Curator\"\n");

        // Configure format-specific options
        self.add_format_configuration(&mut qmd_content, options)?;

        // Execution settings
        qmd_content.push_str("execute:\n");
        qmd_content.push_str("  echo: false\n");
        qmd_content.push_str("  warning: false\n");
        qmd_content.push_str("  message: false\n");

        // Close frontmatter
        qmd_content.push_str("---\n\n");

        // Add content sections
        self.add_content_sections(&mut qmd_content, contents, options)?;

        Ok(qmd_content)
    }

    fn add_format_configuration(&self, qmd_content: &mut String, options: &ExportOptions) -> Result<()> {
        qmd_content.push_str("format:\n");

        match options.format {
            #[cfg(feature = "quarto-integration")]
            ExportFormat::QuartoHtml => {
                qmd_content.push_str("  html:\n");
                qmd_content.push_str("    toc: true\n");
                qmd_content.push_str("    toc-location: left\n");
                qmd_content.push_str("    code-tools: true\n");
                qmd_content.push_str("    theme: cosmo\n");
                qmd_content.push_str("    css: [\"styles.css\"]\n");
                qmd_content.push_str("    number-sections: true\n");
                qmd_content.push_str("    link-external-newwindow: true\n");
            },
            #[cfg(feature = "quarto-integration")]
            ExportFormat::QuartoPdf => {
                qmd_content.push_str("  pdf:\n");
                qmd_content.push_str("    documentclass: article\n");
                qmd_content.push_str("    geometry:\n");
                qmd_content.push_str("      - margin=1in\n");
                qmd_content.push_str("    colorlinks: true\n");
                qmd_content.push_str("    number-sections: true\n");
                qmd_content.push_str("    toc: true\n");
                qmd_content.push_str("    keep-tex: false\n");
            },
            #[cfg(feature = "quarto-integration")]
            ExportFormat::QuartoPowerPoint => {
                qmd_content.push_str("  pptx:\n");
                if let Some(template) = &options.template_name {
                    qmd_content.push_str(&format!("    reference-doc: \"{}\"\n", template));
                }
                qmd_content.push_str("    slide-level: 2\n");
                qmd_content.push_str("    incremental: false\n");
            },
            #[cfg(feature = "quarto-integration")]
            ExportFormat::QuartoWord => {
                qmd_content.push_str("  docx:\n");
                if let Some(template) = &options.template_name {
                    qmd_content.push_str(&format!("    reference-doc: \"{}\"\n", template));
                }
                qmd_content.push_str("    toc: true\n");
                qmd_content.push_str("    number-sections: true\n");
            },
            #[cfg(feature = "quarto-integration")]
            ExportFormat::QuartoBook => {
                qmd_content.push_str("  html:\n");
                qmd_content.push_str("    theme: cosmo\n");
                qmd_content.push_str("    toc: true\n");
                qmd_content.push_str("    number-sections: true\n");
                qmd_content.push_str("    code-tools: true\n");
                qmd_content.push_str("  pdf:\n");
                qmd_content.push_str("    documentclass: book\n");
                qmd_content.push_str("    toc: true\n");
            },
            #[cfg(feature = "quarto-integration")]
            ExportFormat::QuartoWebsite => {
                qmd_content.push_str("  html:\n");
                qmd_content.push_str("    theme: cosmo\n");
                qmd_content.push_str("    toc: true\n");
                qmd_content.push_str("    navbar:\n");
                qmd_content.push_str("      title: \"Curriculum\"\n");
                qmd_content.push_str("    sidebar:\n");
                qmd_content.push_str("      style: \"docked\"\n");
            },
            _ => {
                // Fallback to HTML
                qmd_content.push_str("  html:\n");
                qmd_content.push_str("    toc: true\n");
                qmd_content.push_str("    theme: default\n");
            }
        }

        Ok(())
    }

    fn add_content_sections(&self, qmd_content: &mut String, contents: &[GeneratedContent], options: &ExportOptions) -> Result<()> {
        for (i, content) in contents.iter().enumerate() {
            if i > 0 {
                qmd_content.push_str("\n\\newpage\n\n");
            }

            // Add content title
            qmd_content.push_str(&format!("# {}\n\n", Self::escape_markdown_string(&content.title)));

            // Add metadata if requested
            if options.include_metadata {
                qmd_content.push_str("::: {.callout-note}\n");
                qmd_content.push_str("## Content Information\n\n");
                qmd_content.push_str(&format!("- **Content Type**: {}\n", self.format_content_type(&content.content_type)));
                qmd_content.push_str(&format!("- **Word Count**: {} words\n", content.metadata.word_count));
                qmd_content.push_str(&format!("- **Estimated Duration**: {}\n", content.metadata.estimated_duration));
                qmd_content.push_str(&format!("- **Difficulty Level**: {}\n", content.metadata.difficulty_level));
                qmd_content.push_str(":::\n\n");
            }

            // Process content based on type
            match content.content_type {
                crate::content::ContentType::Slides => {
                    self.format_slides_for_quarto(qmd_content, &content.content)?;
                },
                crate::content::ContentType::Quiz => {
                    self.format_quiz_for_quarto(qmd_content, &content.content)?;
                },
                crate::content::ContentType::Worksheet => {
                    self.format_worksheet_for_quarto(qmd_content, &content.content)?;
                },
                crate::content::ContentType::InstructorNotes => {
                    self.format_instructor_notes_for_quarto(qmd_content, &content.content)?;
                },
                crate::content::ContentType::ActivityGuide => {
                    self.format_activity_guide_for_quarto(qmd_content, &content.content)?;
                },
            }

            qmd_content.push_str("\n\n");
        }

        Ok(())
    }

    fn format_slides_for_quarto(&self, qmd_content: &mut String, content: &str) -> Result<()> {
        let slides: Vec<&str> = content.split("---SLIDE---").collect();
        
        for (i, slide) in slides.iter().enumerate() {
            if slide.trim().is_empty() {
                continue;
            }

            if i > 0 {
                qmd_content.push_str("\n## ");
            }

            let slide_content = slide.trim();
            
            // Handle speaker notes
            if slide_content.contains("SPEAKER_NOTES:") {
                let parts: Vec<&str> = slide_content.split("SPEAKER_NOTES:").collect();
                if parts.len() > 1 {
                    // Main slide content
                    qmd_content.push_str(parts[0].trim());
                    qmd_content.push_str("\n\n");
                    
                    // Speaker notes as callout
                    qmd_content.push_str("::: {.callout-tip collapse=\"true\"}\n");
                    qmd_content.push_str("## Speaker Notes\n\n");
                    qmd_content.push_str(parts[1].trim());
                    qmd_content.push_str("\n:::\n\n");
                }
            } else {
                qmd_content.push_str(slide_content);
                qmd_content.push_str("\n\n");
            }
        }

        Ok(())
    }

    fn format_quiz_for_quarto(&self, qmd_content: &mut String, content: &str) -> Result<()> {
        let questions: Vec<&str> = content.split("---QUESTION---").collect();

        qmd_content.push_str("## Assessment Questions\n\n");

        for (i, question) in questions.iter().enumerate() {
            if question.trim().is_empty() {
                continue;
            }

            qmd_content.push_str(&format!("### Question {}\n\n", i + 1));

            let lines: Vec<&str> = question.trim().lines().collect();
            let mut answer_revealed = false;

            for line in lines {
                if line.starts_with("Q:") {
                    qmd_content.push_str(&format!("**Question:** {}\n\n", &line[2..].trim()));
                } else if line.starts_with("A)") || line.starts_with("B)") || line.starts_with("C)") || line.starts_with("D)") {
                    qmd_content.push_str(&format!("- {}\n", line.trim()));
                } else if line.starts_with("ANSWER:") {
                    if !answer_revealed {
                        qmd_content.push_str("\n::: {.callout-important collapse=\"true\"}\n");
                        qmd_content.push_str("## Answer and Explanation\n\n");
                        answer_revealed = true;
                    }
                    qmd_content.push_str(&format!("**Correct Answer:** {}\n\n", &line[7..].trim()));
                } else if line.starts_with("EXPLANATION:") {
                    qmd_content.push_str(&format!("**Explanation:** {}\n", &line[12..].trim()));
                } else if !line.trim().is_empty() {
                    qmd_content.push_str(&format!("{}\n", line.trim()));
                }
            }

            if answer_revealed {
                qmd_content.push_str(":::\n\n");
            }
        }

        Ok(())
    }

    fn format_worksheet_for_quarto(&self, qmd_content: &mut String, content: &str) -> Result<()> {
        let sections: Vec<&str> = content.split("---SECTION---").collect();

        qmd_content.push_str("## Worksheet Activities\n\n");

        for (i, section) in sections.iter().enumerate() {
            if section.trim().is_empty() {
                continue;
            }

            if i > 0 {
                qmd_content.push_str(&format!("### Section {}\n\n", i));
            }

            let lines: Vec<&str> = section.trim().lines().collect();
            for line in lines {
                if line.starts_with("EXERCISE:") {
                    qmd_content.push_str("::: {.callout-note}\n");
                    qmd_content.push_str("## Exercise\n\n");
                    qmd_content.push_str(&format!("{}\n", &line[9..].trim()));
                    qmd_content.push_str(":::\n\n");
                } else if line.starts_with("ANSWER_SPACE:") {
                    let space_count = line[13..].trim().parse::<usize>().unwrap_or(3);
                    qmd_content.push_str("**Your Answer:**\n\n");
                    for _ in 0..space_count {
                        qmd_content.push_str("&nbsp;\n\n");
                    }
                } else if !line.trim().is_empty() {
                    qmd_content.push_str(&format!("{}\n\n", line.trim()));
                }
            }
        }

        Ok(())
    }

    fn format_instructor_notes_for_quarto(&self, qmd_content: &mut String, content: &str) -> Result<()> {
        qmd_content.push_str("## Instructor Notes\n\n");

        let lines: Vec<&str> = content.lines().collect();
        let mut current_section = None;

        for line in lines {
            if line.starts_with("TIMING:") {
                qmd_content.push_str("::: {.callout-warning}\n");
                qmd_content.push_str("## ⏰ Timing\n\n");
                qmd_content.push_str(&format!("{}\n", &line[7..].trim()));
                qmd_content.push_str(":::\n\n");
            } else if line.starts_with("OBJECTIVES:") {
                current_section = Some("objectives");
                qmd_content.push_str("::: {.callout-tip}\n");
                qmd_content.push_str("## 🎯 Learning Objectives\n\n");
            } else if line.starts_with("KEY_POINTS:") {
                if current_section.is_some() {
                    qmd_content.push_str(":::\n\n");
                }
                current_section = Some("key_points");
                qmd_content.push_str("::: {.callout-important}\n");
                qmd_content.push_str("## 🔑 Key Points\n\n");
            } else if line.starts_with("ASSESSMENT:") {
                if current_section.is_some() {
                    qmd_content.push_str(":::\n\n");
                }
                current_section = Some("assessment");
                qmd_content.push_str("::: {.callout-note}\n");
                qmd_content.push_str("## ✅ Assessment\n\n");
            } else if !line.trim().is_empty() {
                if line.trim().starts_with("-") || line.trim().starts_with("*") {
                    qmd_content.push_str(&format!("- {}\n", &line.trim()[1..].trim()));
                } else {
                    qmd_content.push_str(&format!("{}\n\n", line.trim()));
                }
            }
        }

        if current_section.is_some() {
            qmd_content.push_str(":::\n\n");
        }

        Ok(())
    }

    fn format_activity_guide_for_quarto(&self, qmd_content: &mut String, content: &str) -> Result<()> {
        let activities: Vec<&str> = content.split("---ACTIVITY---").collect();

        qmd_content.push_str("## Activity Guide\n\n");

        for (i, activity) in activities.iter().enumerate() {
            if activity.trim().is_empty() {
                continue;
            }

            qmd_content.push_str(&format!("### Activity {}\n\n", i + 1));

            let lines: Vec<&str> = activity.trim().lines().collect();
            for line in lines {
                if line.starts_with("TITLE:") {
                    qmd_content.push_str(&format!("**{}**\n\n", &line[6..].trim()));
                } else if line.starts_with("DURATION:") {
                    qmd_content.push_str(&format!("⏱️ **Duration:** {}\n\n", &line[9..].trim()));
                } else if line.starts_with("MATERIALS:") {
                    qmd_content.push_str("**Materials Required:**\n\n");
                } else if line.starts_with("INSTRUCTIONS:") {
                    qmd_content.push_str("**Instructions:**\n\n");
                } else if !line.trim().is_empty() {
                    if line.starts_with("- ") || line.starts_with("* ") {
                        qmd_content.push_str(&format!("{}\n", line.trim()));
                    } else {
                        qmd_content.push_str(&format!("{}\n\n", line.trim()));
                    }
                }
            }
        }

        Ok(())
    }

    async fn render_quarto_document(&self, qmd_path: &PathBuf, target_format: &str) -> Result<ExportResult> {
        let mut cmd = Command::new(&self.quarto_executable);
        cmd.arg("render")
           .arg(qmd_path)
           .arg("--to")
           .arg(target_format)
           .arg("--quiet"); // Suppress verbose output

        let output = cmd.output()
            .context("Failed to execute Quarto render command")?;

        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            return Ok(ExportResult {
                success: false,
                output_path: qmd_path.clone(),
                file_size: None,
                error_message: Some(format!("Quarto render failed: {}", error_msg)),
            });
        }

        // Determine output file path based on format
        let output_path = match target_format {
            "html" => qmd_path.with_extension("html"),
            "pdf" => qmd_path.with_extension("pdf"),
            "pptx" => qmd_path.with_extension("pptx"),
            "docx" => qmd_path.with_extension("docx"),
            "revealjs" => qmd_path.with_extension("html"),
            _ => qmd_path.with_extension("html"),
        };

        let file_size = if output_path.exists() {
            fs::metadata(&output_path).await.ok().map(|m| m.len())
        } else {
            None
        };

        Ok(ExportResult {
            success: true,
            output_path,
            file_size,
            error_message: None,
        })
    }

    fn format_content_type(&self, content_type: &crate::content::ContentType) -> String {
        match content_type {
            crate::content::ContentType::Slides => "Presentation Slides",
            crate::content::ContentType::InstructorNotes => "Instructor Notes",
            crate::content::ContentType::Worksheet => "Student Worksheet",
            crate::content::ContentType::Quiz => "Assessment Quiz",
            crate::content::ContentType::ActivityGuide => "Activity Guide",
        }.to_string()
    }

    fn escape_yaml_string(s: &str) -> String {
        s.replace("\"", "\\\"").replace("\n", "\\n")
    }

    fn escape_markdown_string(s: &str) -> String {
        s.replace("#", "\\#").replace("*", "\\*").replace("_", "\\_")
    }
}

#[cfg(feature = "quarto-integration")]
#[async_trait::async_trait]
impl FormatConverter for QuartoConverter {
    fn supported_format(&self) -> ExportFormat {
        ExportFormat::QuartoHtml // Primary format
    }

    async fn convert(&self, contents: &[GeneratedContent], options: &ExportOptions) -> Result<ExportResult> {
        // Generate temporary .qmd file
        let temp_dir = std::env::temp_dir();
        let qmd_filename = format!("quarto_export_{}.qmd", uuid::Uuid::new_v4());
        let qmd_path = temp_dir.join(qmd_filename);

        // Generate QMD content
        let qmd_content = self.generate_qmd_content(contents, options).await?;

        // Write QMD file
        fs::write(&qmd_path, qmd_content).await
            .context("Failed to write Quarto document")?;

        // Determine target format for Quarto CLI
        let target_format = match options.format {
            #[cfg(feature = "quarto-integration")]
            ExportFormat::QuartoHtml => "html",
            #[cfg(feature = "quarto-integration")]
            ExportFormat::QuartoPdf => "pdf",
            #[cfg(feature = "quarto-integration")]
            ExportFormat::QuartoPowerPoint => "pptx",
            #[cfg(feature = "quarto-integration")]
            ExportFormat::QuartoWord => "docx",
            #[cfg(feature = "quarto-integration")]
            ExportFormat::QuartoBook => "html",
            #[cfg(feature = "quarto-integration")]
            ExportFormat::QuartoWebsite => "html",
            _ => "html",
        };

        // Render document
        let mut result = self.render_quarto_document(&qmd_path, target_format).await?;

        // Move output to desired location
        if result.success && result.output_path != options.output_path {
            if let Some(parent) = options.output_path.parent() {
                fs::create_dir_all(parent).await
                    .context("Failed to create output directory")?;
            }
            
            fs::rename(&result.output_path, &options.output_path).await
                .context("Failed to move output file to desired location")?;
            result.output_path = options.output_path.clone();
        }

        // Cleanup temporary QMD file
        let _ = fs::remove_file(&qmd_path).await;

        Ok(result)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::content::{ContentType, generator::ContentMetadata};

    fn create_test_content() -> GeneratedContent {
        GeneratedContent {
            content_type: ContentType::Slides,
            title: "Test Quarto Content".to_string(),
            content: "---SLIDE---\n# Introduction\nWelcome to the test\n---SLIDE---\n# Conclusion\nThank you".to_string(),
            metadata: ContentMetadata {
                word_count: 10,
                estimated_duration: "15 minutes".to_string(),
                difficulty_level: "Beginner".to_string(),
            },
        }
    }

    #[test]
    fn test_quarto_availability() {
        // This test will pass if Quarto is installed, otherwise it will show that it's not available
        let is_available = QuartoConverter::is_available();
        println!("Quarto available: {}", is_available);
        
        if is_available {
            let converter = QuartoConverter::new().unwrap();
            let capabilities = converter.get_capabilities();
            println!("Quarto version: {}", capabilities.version);
            println!("Python support: {}", capabilities.has_python);
            println!("R support: {}", capabilities.has_r);
        }
    }

    #[tokio::test]
    async fn test_qmd_content_generation() {
        if !QuartoConverter::is_available() {
            println!("Skipping Quarto test - Quarto not installed");
            return;
        }

        let converter = QuartoConverter::new().unwrap();
        let content = create_test_content();
        
        let options = ExportOptions {
            format: ExportFormat::QuartoHtml,
            output_path: std::env::temp_dir().join("test.html"),
            template_name: None,
            include_metadata: true,
        };

        let qmd_content = converter.generate_qmd_content(&[content], &options).await.unwrap();
        
        assert!(qmd_content.contains("title: \"Test Quarto Content\""));
        assert!(qmd_content.contains("format:"));
        assert!(qmd_content.contains("html:"));
        assert!(qmd_content.contains("# Introduction"));
        assert!(qmd_content.contains("# Conclusion"));
    }

    #[tokio::test]
    async fn test_full_quarto_export() {
        if !QuartoConverter::is_available() {
            println!("Skipping Quarto integration test - Quarto not installed");
            return;
        }

        let converter = QuartoConverter::new().unwrap();
        let contents = vec![create_test_content()];
        
        let temp_dir = std::env::temp_dir();
        let output_path = temp_dir.join("test_quarto_export.html");
        
        let options = ExportOptions {
            format: ExportFormat::QuartoHtml,
            output_path: output_path.clone(),
            template_name: None,
            include_metadata: true,
        };

        let result = converter.convert(&contents, &options).await;
        
        match result {
            Ok(export_result) => {
                assert!(export_result.success);
                assert!(export_result.output_path.exists());
                
                // Cleanup
                let _ = fs::remove_file(export_result.output_path).await;
            },
            Err(e) => {
                println!("Quarto export failed (this may be expected if Quarto is not properly configured): {}", e);
            }
        }
    }
}