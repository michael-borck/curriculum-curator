use super::*;
use crate::session::SessionManager;
use crate::backup::BackupService;
use anyhow::{Result, Context};
use std::path::Path;
use std::fs;
use std::sync::Arc;
use tokio::sync::Mutex;
use chrono::Utc;
use uuid::Uuid;

pub struct ImportService {
    session_manager: Arc<Mutex<SessionManager>>,
    backup_service: Option<Arc<BackupService>>,
    config: Arc<Mutex<ImportConfig>>,
}

impl ImportService {
    pub fn new(
        session_manager: Arc<Mutex<SessionManager>>,
        backup_service: Option<Arc<BackupService>>,
    ) -> Self {
        Self {
            session_manager,
            backup_service,
            config: Arc::new(Mutex::new(ImportConfig::default())),
        }
    }

    pub async fn get_config(&self) -> ImportConfig {
        self.config.lock().await.clone()
    }

    pub async fn update_config(&self, new_config: ImportConfig) -> Result<()> {
        *self.config.lock().await = new_config;
        Ok(())
    }

    pub async fn preview_import(&self, file_path: &Path) -> Result<ImportPreview> {
        let start_time = std::time::Instant::now();
        
        // Validate file
        self.validate_file(file_path).await?;
        
        // Get file info
        let file_info = self.extract_file_info(file_path).await?;
        
        // Parse document for preview (lightweight)
        let (detected_content_types, session_structure, warnings) = match file_info.file_type {
            SupportedFileType::PowerPoint => {
                self.preview_powerpoint(file_path).await?
            },
            SupportedFileType::Word => {
                self.preview_word_document(file_path).await?
            },
            SupportedFileType::Pdf => {
                return Err(anyhow::anyhow!("PDF import not yet implemented"));
            },
        };

        Ok(ImportPreview {
            file_info,
            detected_content_types,
            estimated_session_structure: session_structure,
            processing_warnings: warnings,
        })
    }

    pub async fn import_file(
        &self,
        file_path: &Path,
        settings: Option<ImportSettings>,
        progress_callback: Option<Box<dyn Fn(ImportProgress) + Send + Sync>>,
    ) -> Result<ImportResult> {
        let start_time = std::time::Instant::now();
        let config = self.config.lock().await.clone();
        let import_settings = settings.unwrap_or(config.default_import_settings);

        // Report progress
        if let Some(ref callback) = progress_callback {
            callback(ImportProgress {
                current_step: ImportStep::Validating,
                progress_percentage: 0.0,
                current_item: "Validating file...".to_string(),
                estimated_time_remaining: None,
            });
        }

        // Validate file
        self.validate_file(file_path).await?;

        // Get file info
        let file_info = self.extract_file_info(file_path).await?;

        // Create backup if enabled
        if config.create_backup_before_import {
            // TODO: Create backup of current session if any
        }

        // Report progress
        if let Some(ref callback) = progress_callback {
            callback(ImportProgress {
                current_step: ImportStep::Parsing,
                progress_percentage: 10.0,
                current_item: format!("Parsing {}...", file_info.filename),
                estimated_time_remaining: Some(30),
            });
        }

        // Parse and extract content
        let imported_content = match file_info.file_type {
            SupportedFileType::PowerPoint => {
                self.import_powerpoint(file_path, &import_settings, progress_callback.as_ref()).await?
            },
            SupportedFileType::Word => {
                self.import_word_document(file_path, &import_settings, progress_callback.as_ref()).await?
            },
            SupportedFileType::Pdf => {
                return Err(anyhow::anyhow!("PDF import not yet implemented"));
            },
        };

        // Report progress
        if let Some(ref callback) = progress_callback {
            callback(ImportProgress {
                current_step: ImportStep::CreatingSession,
                progress_percentage: 90.0,
                current_item: "Creating session...".to_string(),
                estimated_time_remaining: Some(5),
            });
        }

        // Create session name
        let session_name = self.generate_session_name(&file_info, &import_settings).await;

        // Create session
        let session_manager = self.session_manager.lock().await;
        let session_id = session_manager.create_session(&session_name, serde_json::json!({})).await?;

        // Add content to session
        for content in &imported_content {
            session_manager.add_content_to_session(
                &session_id,
                &content.content_type,
                &content.title,
                &content.content,
                Some(serde_json::to_value(&content.metadata)?),
            ).await?;
        }

        // Report completion
        if let Some(ref callback) = progress_callback {
            callback(ImportProgress {
                current_step: ImportStep::Finalizing,
                progress_percentage: 100.0,
                current_item: "Import complete!".to_string(),
                estimated_time_remaining: Some(0),
            });
        }

        let processing_time = start_time.elapsed().as_millis() as u64;

        Ok(ImportResult {
            success: true,
            session_id: Some(session_id),
            session_name,
            imported_content,
            warnings: vec![], // TODO: Collect warnings during processing
            errors: vec![],
            processing_time_ms: processing_time,
            file_info,
        })
    }

    async fn validate_file(&self, file_path: &Path) -> Result<()> {
        if !file_path.exists() {
            return Err(anyhow::anyhow!("File does not exist"));
        }

        if !file_path.is_file() {
            return Err(anyhow::anyhow!("Path is not a file"));
        }

        let metadata = fs::metadata(file_path)
            .context("Failed to read file metadata")?;

        let config = self.config.lock().await;
        let max_size = config.default_import_settings.processing_options.max_file_size_mb as u64 * 1024 * 1024;

        if metadata.len() > max_size {
            return Err(anyhow::anyhow!(
                "File size ({} MB) exceeds maximum allowed size ({} MB)",
                metadata.len() / (1024 * 1024),
                config.default_import_settings.processing_options.max_file_size_mb
            ));
        }

        // Check file extension
        let extension = file_path
            .extension()
            .and_then(|ext| ext.to_str())
            .ok_or_else(|| anyhow::anyhow!("File has no extension"))?;

        if SupportedFileType::from_extension(extension).is_none() {
            return Err(anyhow::anyhow!(
                "Unsupported file type: .{}. Supported types: .pptx, .docx",
                extension
            ));
        }

        Ok(())
    }

    async fn extract_file_info(&self, file_path: &Path) -> Result<FileInfo> {
        let metadata = fs::metadata(file_path)?;
        let filename = file_path
            .file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("unknown")
            .to_string();

        let extension = file_path
            .extension()
            .and_then(|ext| ext.to_str())
            .unwrap_or("");

        let file_type = SupportedFileType::from_extension(extension)
            .ok_or_else(|| anyhow::anyhow!("Unsupported file type"))?;

        let last_modified = metadata.modified()
            .ok()
            .map(|time| chrono::DateTime::<Utc>::from(time));

        // Extract document properties (simplified for now)
        let document_properties = DocumentProperties {
            title: Some(filename.clone()),
            author: None,
            subject: None,
            keywords: vec![],
            created_date: None,
            modified_date: last_modified,
            slide_count: None,
            page_count: None,
        };

        Ok(FileInfo {
            filename,
            file_size: metadata.len(),
            file_type,
            last_modified,
            document_properties,
        })
    }

    async fn preview_powerpoint(&self, _file_path: &Path) -> Result<(Vec<DetectedContentType>, SessionStructure, Vec<String>)> {
        // Simplified preview implementation
        // In a real implementation, this would parse the PPTX file structure
        
        let detected_content_types = vec![
            DetectedContentType {
                content_type: "Slides".to_string(),
                confidence: 0.95,
                sample_content: "Introduction to Topic\n\n• Key Point 1\n• Key Point 2".to_string(),
                count: 10,
            },
            DetectedContentType {
                content_type: "InstructorNotes".to_string(),
                confidence: 0.8,
                sample_content: "Remember to emphasize the importance of...".to_string(),
                count: 5,
            },
        ];

        let session_structure = SessionStructure {
            suggested_name: "Imported PowerPoint Presentation".to_string(),
            learning_objectives: vec![
                "Students will understand the main concepts".to_string(),
                "Students will be able to apply the knowledge".to_string(),
            ],
            content_outline: vec![
                ContentOutlineItem {
                    title: "Introduction".to_string(),
                    content_type: "Slides".to_string(),
                    description: "Overview and objectives".to_string(),
                    order: 1,
                },
                ContentOutlineItem {
                    title: "Main Content".to_string(),
                    content_type: "Slides".to_string(),
                    description: "Core lesson material".to_string(),
                    order: 2,
                },
            ],
            estimated_duration: "50 minutes".to_string(),
        };

        let warnings = vec![
            "Some animations may not be preserved".to_string(),
            "Complex slide layouts may be simplified".to_string(),
        ];

        Ok((detected_content_types, session_structure, warnings))
    }

    async fn preview_word_document(&self, _file_path: &Path) -> Result<(Vec<DetectedContentType>, SessionStructure, Vec<String>)> {
        // Simplified preview implementation
        // In a real implementation, this would parse the DOCX file structure
        
        let detected_content_types = vec![
            DetectedContentType {
                content_type: "InstructorNotes".to_string(),
                confidence: 0.9,
                sample_content: "Lesson Plan Overview\n\nObjectives:\n1. Students will...".to_string(),
                count: 1,
            },
            DetectedContentType {
                content_type: "Worksheet".to_string(),
                confidence: 0.7,
                sample_content: "Exercise 1: Complete the following...".to_string(),
                count: 3,
            },
        ];

        let session_structure = SessionStructure {
            suggested_name: "Imported Word Document".to_string(),
            learning_objectives: vec![
                "Students will understand the document content".to_string(),
            ],
            content_outline: vec![
                ContentOutlineItem {
                    title: "Document Content".to_string(),
                    content_type: "InstructorNotes".to_string(),
                    description: "Imported document text".to_string(),
                    order: 1,
                },
            ],
            estimated_duration: "30 minutes".to_string(),
        };

        let warnings = vec![
            "Complex formatting may be simplified".to_string(),
        ];

        Ok((detected_content_types, session_structure, warnings))
    }

    async fn import_powerpoint(
        &self,
        file_path: &Path,
        settings: &ImportSettings,
        progress_callback: Option<&Box<dyn Fn(ImportProgress) + Send + Sync>>,
    ) -> Result<Vec<ImportedContent>> {
        use crate::import::parsers::PowerPointParser;
        
        if let Some(ref callback) = progress_callback {
            callback(ImportProgress {
                current_step: ImportStep::ExtractingContent,
                progress_percentage: 20.0,
                current_item: "Parsing PowerPoint slides...".to_string(),
                estimated_time_remaining: Some(15),
            });
        }
        
        let mut content = PowerPointParser::parse_file(file_path).await?;
        
        // Apply import settings
        if !settings.content_mapping.extract_speaker_notes {
            content.retain(|item| item.content_type != "InstructorNotes");
        }
        
        // Map content types based on settings
        for item in &mut content {
            if item.content_type == "Slides" {
                item.content_type = settings.content_mapping.map_slides_to_content_type.clone();
            }
        }
        
        if let Some(ref callback) = progress_callback {
            callback(ImportProgress {
                current_step: ImportStep::MappingContent,
                progress_percentage: 70.0,
                current_item: format!("Processed {} content items", content.len()),
                estimated_time_remaining: Some(5),
            });
        }
        
        Ok(content)
    }

    async fn import_word_document(
        &self,
        file_path: &Path,
        settings: &ImportSettings,
        progress_callback: Option<&Box<dyn Fn(ImportProgress) + Send + Sync>>,
    ) -> Result<Vec<ImportedContent>> {
        use crate::import::parsers::WordParser;
        
        if let Some(ref callback) = progress_callback {
            callback(ImportProgress {
                current_step: ImportStep::ExtractingContent,
                progress_percentage: 30.0,
                current_item: "Parsing Word document...".to_string(),
                estimated_time_remaining: Some(10),
            });
        }
        
        let mut content = WordParser::parse_file(file_path).await?;
        
        // Apply content mapping settings
        if settings.content_mapping.create_worksheets_from_exercises {
            // Convert sections that look like exercises to worksheets
            for item in &mut content {
                let content_lower = item.content.to_lowercase();
                if content_lower.contains("exercise") || content_lower.contains("activity") {
                    item.content_type = "Worksheet".to_string();
                }
            }
        }
        
        if settings.content_mapping.detect_quiz_questions {
            // Convert sections that look like quizzes
            for item in &mut content {
                let content_lower = item.content.to_lowercase();
                if content_lower.contains("question") && 
                   (content_lower.contains("answer") || content_lower.contains("choice")) {
                    item.content_type = "Quiz".to_string();
                }
            }
        }
        
        if let Some(ref callback) = progress_callback {
            callback(ImportProgress {
                current_step: ImportStep::MappingContent,
                progress_percentage: 75.0,
                current_item: format!("Processed {} content sections", content.len()),
                estimated_time_remaining: Some(3),
            });
        }
        
        Ok(content)
    }

    async fn generate_session_name(&self, file_info: &FileInfo, settings: &ImportSettings) -> String {
        let now = Utc::now();
        let date_str = now.format("%Y-%m-%d").to_string();
        
        let name = settings.session_name_template
            .replace("{filename}", &file_info.filename.replace(".pptx", "").replace(".docx", ""))
            .replace("{date}", &date_str)
            .replace("{time}", &now.format("%H:%M").to_string());

        // Ensure name is not too long
        if name.len() > 100 {
            format!("{}...", &name[..97])
        } else {
            name
        }
    }
}