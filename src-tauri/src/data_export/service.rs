use super::*;
use crate::session::SessionManager;
use crate::backup::service::BackupService;
use anyhow::{Result, Context};
use std::path::{Path, PathBuf};
use std::fs::{self, File};
use std::io::{Write, Read};
use std::sync::Arc;
use tokio::sync::Mutex;
use chrono::Utc;
use uuid::Uuid;
use zip::{ZipWriter, write::FileOptions, CompressionMethod};
use tar::{Builder as TarBuilder, Header};
use flate2::{Compression, write::GzEncoder};
use sha2::{Sha256, Digest};

pub struct DataExportService {
    session_manager: Arc<Mutex<SessionManager>>,
    backup_service: Option<Arc<BackupService>>,
    config: Arc<Mutex<DataExportConfig>>,
}

impl DataExportService {
    pub fn new(
        session_manager: Arc<Mutex<SessionManager>>,
        backup_service: Option<Arc<BackupService>>,
        config: Option<DataExportConfig>,
    ) -> Self {
        Self {
            session_manager,
            backup_service,
            config: Arc::new(Mutex::new(config.unwrap_or_default())),
        }
    }

    pub async fn get_config(&self) -> DataExportConfig {
        self.config.lock().await.clone()
    }

    pub async fn update_config(&self, new_config: DataExportConfig) -> Result<()> {
        *self.config.lock().await = new_config;
        Ok(())
    }

    pub async fn export_data(
        &self,
        request: ExportRequest,
        progress_callback: Option<Box<dyn Fn(ExportProgress) + Send + Sync>>,
    ) -> Result<ExportResult> {
        let start_time = std::time::Instant::now();
        let export_id = Uuid::new_v4().to_string();

        // Initialize progress
        if let Some(ref callback) = progress_callback {
            callback(ExportProgress {
                current_step: ExportStep::Initializing,
                progress_percentage: 0.0,
                current_item: "Starting export...".to_string(),
                items_processed: 0,
                total_items: 0,
                estimated_time_remaining: None,
                current_file_size: 0,
                total_size_estimate: 0,
            });
        }

        // Collect sessions to export
        let sessions = self.collect_sessions(&request.sessions, &progress_callback).await?;
        let total_sessions = sessions.len() as u32;

        // Process content based on format
        let export_result = match &request.format {
            ExportFormat::Archive(archive_format) => {
                self.create_archive_export(&request, &sessions, &export_id, &progress_callback).await?
            }
            ExportFormat::Database(db_format) => {
                self.create_database_export(&request, &sessions, &export_id, &progress_callback).await?
            }
            ExportFormat::Portable(portable_format) => {
                self.create_portable_export(&request, &sessions, &export_id, &progress_callback).await?
            }
        };

        // Final progress update
        if let Some(ref callback) = progress_callback {
            callback(ExportProgress {
                current_step: ExportStep::Complete,
                progress_percentage: 100.0,
                current_item: "Export completed successfully".to_string(),
                items_processed: export_result.content_items_exported,
                total_items: export_result.content_items_exported,
                estimated_time_remaining: Some(0),
                current_file_size: export_result.file_size,
                total_size_estimate: export_result.file_size,
            });
        }

        Ok(ExportResult {
            processing_time_ms: start_time.elapsed().as_millis() as u64,
            ..export_result
        })
    }

    async fn collect_sessions(
        &self,
        filter: &ExportSessionFilter,
        progress_callback: &Option<Box<dyn Fn(ExportProgress) + Send + Sync>>,
    ) -> Result<Vec<SessionSummary>> {
        if let Some(ref callback) = progress_callback {
            callback(ExportProgress {
                current_step: ExportStep::CollectingSessions,
                progress_percentage: 5.0,
                current_item: "Collecting session information...".to_string(),
                items_processed: 0,
                total_items: 0,
                estimated_time_remaining: None,
                current_file_size: 0,
                total_size_estimate: 0,
            });
        }

        let session_manager = self.session_manager.lock().await;
        
        // Get all sessions first
        let all_sessions = session_manager.list_sessions().await?;
        
        // Filter based on criteria
        let filtered_sessions = match filter {
            ExportSessionFilter::All => all_sessions,
            ExportSessionFilter::SelectedSessions(session_ids) => {
                all_sessions.into_iter()
                    .filter(|session| session_ids.contains(&session.id.to_string()))
                    .collect()
            }
            ExportSessionFilter::DateRange { start, end } => {
                all_sessions.into_iter()
                    .filter(|session| {
                        session.created_at >= *start && session.created_at <= *end
                    })
                    .collect()
            }
            ExportSessionFilter::RecentSessions(count) => {
                let mut sessions = all_sessions;
                sessions.sort_by(|a, b| b.created_at.cmp(&a.created_at));
                sessions.into_iter().take(*count as usize).collect()
            }
        };

        // Convert to session summaries
        let mut summaries = Vec::new();
        for session in filtered_sessions {
            let content = session_manager.get_session_content(session.id).await?;
            let content_types: Vec<String> = content.iter()
                .map(|c| c.content_type.to_string())
                .collect::<std::collections::HashSet<_>>()
                .into_iter()
                .collect();

            // Estimate size (simplified)
            let size_bytes = content.iter()
                .map(|c| c.content.len() as u64)
                .sum();

            summaries.push(SessionSummary {
                id: session.id.to_string(),
                name: session.name,
                created_at: session.created_at,
                content_count: content.len() as u32,
                content_types,
                size_bytes,
            });
        }

        if let Some(ref callback) = progress_callback {
            callback(ExportProgress {
                current_step: ExportStep::CollectingSessions,
                progress_percentage: 15.0,
                current_item: format!("Found {} sessions to export", summaries.len()),
                items_processed: summaries.len() as u32,
                total_items: summaries.len() as u32,
                estimated_time_remaining: None,
                current_file_size: 0,
                total_size_estimate: summaries.iter().map(|s| s.size_bytes).sum(),
            });
        }

        Ok(summaries)
    }

    async fn create_archive_export(
        &self,
        request: &ExportRequest,
        sessions: &[SessionSummary],
        export_id: &str,
        progress_callback: &Option<Box<dyn Fn(ExportProgress) + Send + Sync>>,
    ) -> Result<ExportResult> {
        let output_file = self.generate_output_path(request, export_id)?;
        
        match request.format {
            ExportFormat::Archive(ArchiveFormat::Zip) => {
                self.create_zip_export(request, sessions, export_id, &output_file, progress_callback).await
            }
            ExportFormat::Archive(ArchiveFormat::Tar) => {
                self.create_tar_export(request, sessions, export_id, &output_file, false, progress_callback).await
            }
            ExportFormat::Archive(ArchiveFormat::TarGz) => {
                self.create_tar_export(request, sessions, export_id, &output_file, true, progress_callback).await
            }
            _ => Err(anyhow::anyhow!("Unsupported archive format")),
        }
    }

    async fn create_zip_export(
        &self,
        request: &ExportRequest,
        sessions: &[SessionSummary],
        export_id: &str,
        output_file: &Path,
        progress_callback: &Option<Box<dyn Fn(ExportProgress) + Send + Sync>>,
    ) -> Result<ExportResult> {
        if let Some(ref callback) = progress_callback {
            callback(ExportProgress {
                current_step: ExportStep::CreatingArchive,
                progress_percentage: 20.0,
                current_item: "Creating ZIP archive...".to_string(),
                items_processed: 0,
                total_items: sessions.len() as u32,
                estimated_time_remaining: Some(60),
                current_file_size: 0,
                total_size_estimate: sessions.iter().map(|s| s.size_bytes).sum(),
            });
        }

        let file = File::create(output_file)?;
        let mut zip = ZipWriter::new(file);
        
        let options = FileOptions::default()
            .compression_method(if request.options.compress {
                CompressionMethod::Deflated
            } else {
                CompressionMethod::Stored
            })
            .unix_permissions(0o755);

        let mut content_items_exported = 0;
        let mut file_entries = Vec::new();
        let session_manager = self.session_manager.lock().await;

        for (session_idx, session) in sessions.iter().enumerate() {
            let session_folder = format!("sessions/{}/", session.name.replace("/", "_"));
            
            // Add session metadata
            let session_metadata = serde_json::json!({
                "id": session.id.to_string(),
                "name": session.name,
                "created_at": session.created_at,
                "content_count": session.content_count,
                "content_types": session.content_types
            });
            
            let metadata_path = format!("{}metadata.json", session_folder);
            zip.start_file(&metadata_path, options)?;
            zip.write_all(serde_json::to_string_pretty(&session_metadata)?.as_bytes())?;
            
            file_entries.push(FileEntry {
                path: metadata_path,
                file_type: FileType::Metadata,
                size_bytes: session_metadata.to_string().len() as u64,
                checksum: None,
                created_at: Utc::now(),
                metadata: HashMap::new(),
            });

            // Add session content
            let session_uuid = Uuid::parse_str(&session.id)?;
            let content = session_manager.get_session_content(session_uuid).await?;
            for (content_idx, content_item) in content.iter().enumerate() {
                let content_file = format!("{}content_{:03}_{}.md", 
                    session_folder, content_idx, content_item.content_type.to_string());
                
                zip.start_file(&content_file, options)?;
                zip.write_all(content_item.content.as_bytes())?;
                
                file_entries.push(FileEntry {
                    path: content_file,
                    file_type: FileType::ContentFile,
                    size_bytes: content_item.content.len() as u64,
                    checksum: Some(format!("{:x}", Sha256::digest(content_item.content.as_bytes()))),
                    created_at: Utc::now(), // Use current time since created_at field doesn't exist
                    metadata: {
                        let mut meta = HashMap::new();
                        meta.insert("content_type".to_string(), 
                            serde_json::Value::String(content_item.content_type.to_string()));
                        meta.insert("title".to_string(), 
                            serde_json::Value::String(content_item.title.clone()));
                        meta
                    },
                });
                
                content_items_exported += 1;
            }

            // Update progress
            if let Some(ref callback) = progress_callback {
                let progress = 20.0 + (session_idx as f32 / sessions.len() as f32) * 50.0;
                callback(ExportProgress {
                    current_step: ExportStep::ProcessingContent,
                    progress_percentage: progress,
                    current_item: format!("Processing session: {}", session.name),
                    items_processed: session_idx as u32 + 1,
                    total_items: sessions.len() as u32,
                    estimated_time_remaining: Some(((sessions.len() - session_idx - 1) * 2) as u32),
                    current_file_size: 0,
                    total_size_estimate: sessions.iter().map(|s| s.size_bytes).sum(),
                });
            }
        }

        // Generate and add manifest
        let manifest = self.create_manifest(export_id, &request.format, sessions, &file_entries).await?;
        zip.start_file("manifest.json", options)?;
        zip.write_all(serde_json::to_string_pretty(&manifest)?.as_bytes())?;

        if let Some(ref callback) = progress_callback {
            callback(ExportProgress {
                current_step: ExportStep::Finalizing,
                progress_percentage: 95.0,
                current_item: "Finalizing archive...".to_string(),
                items_processed: sessions.len() as u32,
                total_items: sessions.len() as u32,
                estimated_time_remaining: Some(5),
                current_file_size: 0,
                total_size_estimate: sessions.iter().map(|s| s.size_bytes).sum(),
            });
        }

        zip.finish()?;
        
        let file_size = fs::metadata(output_file)?.len();

        Ok(ExportResult {
            success: true,
            export_id: export_id.to_string(),
            output_path: output_file.to_path_buf(),
            file_size,
            sessions_exported: sessions.len() as u32,
            content_items_exported,
            processing_time_ms: 0, // Will be set by caller
            warnings: vec![],
            errors: vec![],
            manifest,
        })
    }

    async fn create_tar_export(
        &self,
        request: &ExportRequest,
        sessions: &[SessionSummary],
        export_id: &str,
        output_file: &Path,
        compress: bool,
        progress_callback: &Option<Box<dyn Fn(ExportProgress) + Send + Sync>>,
    ) -> Result<ExportResult> {
        if let Some(ref callback) = progress_callback {
            callback(ExportProgress {
                current_step: ExportStep::CreatingArchive,
                progress_percentage: 20.0,
                current_item: if compress { "Creating TAR.GZ archive..." } else { "Creating TAR archive..." }.to_string(),
                items_processed: 0,
                total_items: sessions.len() as u32,
                estimated_time_remaining: Some(90),
                current_file_size: 0,
                total_size_estimate: sessions.iter().map(|s| s.size_bytes).sum(),
            });
        }

        let file = File::create(output_file)?;
        let mut tar_builder = if compress {
            let encoder = GzEncoder::new(file, Compression::default());
            TarBuilder::new(encoder)
        } else {
            TarBuilder::new(file)
        };

        let mut content_items_exported = 0;
        let mut file_entries = Vec::new();
        let session_manager = self.session_manager.lock().await;

        for (session_idx, session) in sessions.iter().enumerate() {
            let session_folder = format!("sessions/{}/", session.name.replace("/", "_"));
            
            // Add session metadata
            let session_metadata = serde_json::json!({
                "id": session.id.to_string(),
                "name": session.name,
                "created_at": session.created_at,
                "content_count": session.content_count,
                "content_types": session.content_types
            });
            
            let metadata_json = serde_json::to_string_pretty(&session_metadata)?;
            let metadata_path = format!("{}metadata.json", session_folder);
            
            let mut header = Header::new_gnu();
            header.set_size(metadata_json.len() as u64);
            header.set_cksum();
            tar_builder.append_data(&mut header, &metadata_path, metadata_json.as_bytes())?;

            // Add session content
            let session_uuid = Uuid::parse_str(&session.id)?;
            let content = session_manager.get_session_content(session_uuid).await?;
            for (content_idx, content_item) in content.iter().enumerate() {
                let content_file = format!("{}content_{:03}_{}.md", 
                    session_folder, content_idx, content_item.content_type.to_string());
                
                let mut header = Header::new_gnu();
                header.set_size(content_item.content.len() as u64);
                header.set_cksum();
                tar_builder.append_data(&mut header, &content_file, content_item.content.as_bytes())?;
                
                content_items_exported += 1;
            }

            // Update progress
            if let Some(ref callback) = progress_callback {
                let progress = 20.0 + (session_idx as f32 / sessions.len() as f32) * 50.0;
                callback(ExportProgress {
                    current_step: ExportStep::ProcessingContent,
                    progress_percentage: progress,
                    current_item: format!("Processing session: {}", session.name),
                    items_processed: session_idx as u32 + 1,
                    total_items: sessions.len() as u32,
                    estimated_time_remaining: Some(((sessions.len() - session_idx - 1) * 3) as u32),
                    current_file_size: 0,
                    total_size_estimate: sessions.iter().map(|s| s.size_bytes).sum(),
                });
            }
        }

        // Generate and add manifest
        let manifest = self.create_manifest(export_id, &request.format, sessions, &file_entries).await?;
        let manifest_json = serde_json::to_string_pretty(&manifest)?;
        let mut header = Header::new_gnu();
        header.set_size(manifest_json.len() as u64);
        header.set_cksum();
        tar_builder.append_data(&mut header, "manifest.json", manifest_json.as_bytes())?;

        tar_builder.finish()?;
        
        let file_size = fs::metadata(output_file)?.len();

        Ok(ExportResult {
            success: true,
            export_id: export_id.to_string(),
            output_path: output_file.to_path_buf(),
            file_size,
            sessions_exported: sessions.len() as u32,
            content_items_exported,
            processing_time_ms: 0,
            warnings: vec![],
            errors: vec![],
            manifest,
        })
    }

    async fn create_database_export(
        &self,
        request: &ExportRequest,
        sessions: &[SessionSummary],
        export_id: &str,
        progress_callback: &Option<Box<dyn Fn(ExportProgress) + Send + Sync>>,
    ) -> Result<ExportResult> {
        // Implementation for database exports (JSON, CSV, SQLite backup)
        // This is a simplified version - would need full implementation
        
        let output_file = self.generate_output_path(request, export_id)?;
        
        match request.format {
            ExportFormat::Database(DatabaseFormat::JsonExport) => {
                self.create_json_export(request, sessions, export_id, &output_file, progress_callback).await
            }
            _ => Err(anyhow::anyhow!("Database export format not implemented")),
        }
    }

    async fn create_json_export(
        &self,
        request: &ExportRequest,
        sessions: &[SessionSummary],
        export_id: &str,
        output_file: &Path,
        progress_callback: &Option<Box<dyn Fn(ExportProgress) + Send + Sync>>,
    ) -> Result<ExportResult> {
        if let Some(ref callback) = progress_callback {
            callback(ExportProgress {
                current_step: ExportStep::ProcessingContent,
                progress_percentage: 25.0,
                current_item: "Creating JSON export...".to_string(),
                items_processed: 0,
                total_items: sessions.len() as u32,
                estimated_time_remaining: Some(30),
                current_file_size: 0,
                total_size_estimate: sessions.iter().map(|s| s.size_bytes).sum(),
            });
        }

        let session_manager = self.session_manager.lock().await;
        let mut export_data = serde_json::json!({
            "export_id": export_id,
            "created_at": Utc::now(),
            "format": "json",
            "sessions": []
        });

        let mut content_items_exported = 0;

        for (session_idx, session) in sessions.iter().enumerate() {
            let content = session_manager.get_session_content(session.id).await?;
            
            let session_data = serde_json::json!({
                "id": session.id.to_string(),
                "name": session.name,
                "created_at": session.created_at,
                "content": content
            });
            
            export_data["sessions"].as_array_mut().unwrap().push(session_data);
            content_items_exported += content.len() as u32;

            if let Some(ref callback) = progress_callback {
                let progress = 25.0 + (session_idx as f32 / sessions.len() as f32) * 60.0;
                callback(ExportProgress {
                    current_step: ExportStep::ProcessingContent,
                    progress_percentage: progress,
                    current_item: format!("Processing session: {}", session.name),
                    items_processed: session_idx as u32 + 1,
                    total_items: sessions.len() as u32,
                    estimated_time_remaining: Some(((sessions.len() - session_idx - 1) * 1) as u32),
                    current_file_size: 0,
                    total_size_estimate: sessions.iter().map(|s| s.size_bytes).sum(),
                });
            }
        }

        // Write JSON file
        let json_string = serde_json::to_string_pretty(&export_data)?;
        fs::write(output_file, &json_string)?;
        
        let file_size = json_string.len() as u64;
        let manifest = self.create_manifest(export_id, &request.format, sessions, &[]).await?;

        Ok(ExportResult {
            success: true,
            export_id: export_id.to_string(),
            output_path: output_file.to_path_buf(),
            file_size,
            sessions_exported: sessions.len() as u32,
            content_items_exported,
            processing_time_ms: 0,
            warnings: vec![],
            errors: vec![],
            manifest,
        })
    }

    async fn create_portable_export(
        &self,
        request: &ExportRequest,
        sessions: &[SessionSummary],
        export_id: &str,
        progress_callback: &Option<Box<dyn Fn(ExportProgress) + Send + Sync>>,
    ) -> Result<ExportResult> {
        // Create a specialized portable format
        // This would create a self-contained package with documentation
        
        // For now, fall back to ZIP format with additional documentation
        let mut zip_request = request.clone();
        zip_request.format = ExportFormat::Archive(ArchiveFormat::Zip);
        
        self.create_archive_export(&zip_request, sessions, export_id, progress_callback).await
    }

    async fn create_manifest(
        &self,
        export_id: &str,
        format: &ExportFormat,
        sessions: &[SessionSummary],
        file_entries: &[FileEntry],
    ) -> Result<ExportManifest> {
        let content_types: HashMap<String, u32> = sessions.iter()
            .flat_map(|s| &s.content_types)
            .fold(HashMap::new(), |mut acc, content_type| {
                *acc.entry(content_type.clone()).or_insert(0) += 1;
                acc
            });

        let total_size = sessions.iter().map(|s| s.size_bytes).sum();

        Ok(ExportManifest {
            export_id: export_id.to_string(),
            created_at: Utc::now(),
            format: format.clone(),
            source_info: SourceInfo {
                application_version: env!("CARGO_PKG_VERSION").to_string(),
                database_version: "1.0".to_string(),
                export_version: "1.0".to_string(),
                platform: std::env::consts::OS.to_string(),
                total_sessions: sessions.len() as u32,
                export_timestamp: Utc::now(),
            },
            content_summary: ContentSummary {
                sessions: sessions.to_vec(),
                content_types,
                total_files: file_entries.len() as u32,
                total_size_bytes: total_size,
            },
            file_structure: file_entries.to_vec(),
            metadata: HashMap::new(),
        })
    }

    fn generate_output_path(&self, request: &ExportRequest, export_id: &str) -> Result<PathBuf> {
        let filename = if let Some(ref custom_filename) = request.filename {
            format!("{}.{}", custom_filename, request.format.extension())
        } else {
            let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
            format!("curriculum_export_{}_{}.{}", timestamp, &export_id[..8], request.format.extension())
        };

        Ok(request.output_path.join(filename))
    }
}