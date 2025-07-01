// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// Allow warnings for features under development
#![allow(dead_code)]
#![allow(unused_imports)]
#![allow(unused_variables)]
#![allow(unused_mut)]

use tauri::{Manager, Emitter};
use session::SessionService;
use file_manager::FileService;
use backup::service::BackupService;
use backup::scheduler::BackupScheduler;
use import::service::ImportService;
use git::service::GitService;
use data_export::service::DataExportService;
use maintenance::service::MaintenanceService;
use llm::LLMManager;
use std::sync::Arc;
use tokio::sync::Mutex;

use crate::state::AppState;

mod backup;
mod commands;
mod content;
mod data_export;
mod database;
mod export;
mod file_manager;
mod git;
mod import;
mod llm;
mod maintenance;
mod session;
mod state;
mod validation;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            // Basic commands
            commands::health_check,
            commands::create_project_directory,
            
            // Session management (updated to use new session commands)
            session::commands::create_session,
            session::commands::load_session,
            session::commands::save_session,
            session::commands::update_session,
            session::commands::add_content_to_session,
            session::commands::list_sessions,
            session::commands::delete_session,
            session::commands::get_session_statistics,
            session::commands::duplicate_session,
            session::commands::get_session_content,
            
            // File management operations
            file_manager::commands::save_session_to_file,
            file_manager::commands::export_session_content,
            file_manager::commands::load_session_from_file,
            file_manager::commands::get_suggested_filename,
            file_manager::commands::validate_file_path,
            file_manager::commands::list_storage_files,
            file_manager::commands::get_storage_statistics,
            file_manager::commands::cleanup_storage,
            file_manager::commands::get_default_storage_paths,
            file_manager::commands::update_storage_config,
            file_manager::commands::get_storage_config,
            
            // Backup and recovery operations
            backup::commands::create_manual_backup,
            backup::commands::restore_from_backup,
            backup::commands::list_backups,
            backup::commands::delete_backup,
            backup::commands::get_backup_statistics,
            backup::commands::get_backup_config,
            backup::commands::update_backup_config,
            backup::commands::cleanup_old_backups,
            backup::commands::verify_backup_integrity,
            backup::commands::get_session_backups,
            
            // Content generation
            commands::generate_content,
            
            // Workflow commands
            content::workflow_commands::create_workflow,
            content::workflow_commands::execute_workflow_step,
            content::workflow_commands::get_workflow_status,
            content::workflow_commands::execute_quick_action,
            
            // Batch content generation commands
            content::batch_commands::create_batch_generation,
            content::batch_commands::execute_batch_generation,
            content::batch_commands::get_batch_status,
            content::batch_commands::cancel_batch_generation,
            content::batch_commands::list_batch_generations,
            content::batch_commands::export_batch_results,
            
            // Configuration
            commands::get_app_config,
            commands::set_app_config,
            
            // Validation
            commands::validate_content,
            
            // LLM provider management
            commands::get_available_providers,
            commands::get_ollama_models,
            commands::get_model_recommendations,
            commands::get_ollama_installation_instructions,
            commands::check_system_requirements,
            commands::test_llm_generation,
            
            // Cost tracking
            commands::get_session_cost,
            
            // Export
            commands::export_content,
            commands::get_supported_export_formats,
            commands::validate_export_path,
            
            // Batch Export
            commands::batch_export_content,
            commands::create_batch_export_job,
            
            // API Key management
            commands::store_api_key,
            commands::get_api_key_config,
            commands::remove_api_key,
            commands::list_configured_providers,
            commands::update_provider_config,
            commands::validate_api_key_format,
            commands::import_api_keys_from_env,
            commands::export_provider_config_template,
            commands::clear_all_api_keys,
            
            // External provider testing
            commands::test_external_provider,
            commands::get_external_provider_models,
            commands::estimate_external_provider_cost,
            commands::setup_provider_from_wizard,
            
            // Offline capability commands
            commands::check_connectivity_status,
            commands::get_provider_capabilities,
            commands::get_available_providers_by_connectivity,
            commands::get_offline_setup_recommendations,
            commands::get_embedded_model_recommendations,
            commands::get_ollama_setup_instructions,
            commands::refresh_provider_capabilities,
            commands::get_best_available_provider,
            commands::test_offline_generation,
            
            // Import functionality
            import::commands::get_import_config,
            import::commands::update_import_config,
            import::commands::preview_import_file,
            import::commands::import_file,
            import::commands::import_file_with_progress,
            import::commands::get_supported_file_types,
            import::commands::validate_import_file,
            
            // Git integration
            git::commands::get_git_config,
            git::commands::update_git_config,
            git::commands::detect_git_repository,
            git::commands::initialize_git_repository,
            git::commands::get_git_status,
            git::commands::commit_git_changes,
            git::commands::get_git_history,
            git::commands::get_git_diff,
            git::commands::auto_commit_session,
            git::commands::auto_commit_content_generation,
            git::commands::check_git_installation,
            git::commands::get_git_user_config,
            git::commands::set_git_user_config,
            git::commands::validate_repository_path,
            
            // Data export functionality
            data_export::commands::get_data_export_config,
            data_export::commands::update_data_export_config,
            data_export::commands::export_data,
            data_export::commands::export_data_with_progress,
            data_export::commands::get_export_formats,
            data_export::commands::validate_export_request,
            data_export::commands::preview_export_contents,
            data_export::commands::get_recent_exports,
            data_export::commands::cleanup_old_exports,
            
            // Maintenance functionality
            maintenance::commands::get_maintenance_config,
            maintenance::commands::update_maintenance_config,
            maintenance::commands::analyze_maintenance_issues,
            maintenance::commands::perform_maintenance,
            maintenance::commands::perform_maintenance_with_progress,
            maintenance::commands::get_available_maintenance_operations,
            maintenance::commands::get_maintenance_recommendations,
            maintenance::commands::estimate_maintenance_impact,
            maintenance::commands::get_system_health_summary,
            
            // Backup functionality
            backup::commands::create_manual_backup,
            backup::commands::restore_from_backup,
            backup::commands::list_backups,
            backup::commands::delete_backup,
            backup::commands::get_backup_statistics,
            backup::commands::get_backup_config,
            backup::commands::update_backup_config
        ])
        .setup(|app| {
            // Initialize shared database
            let shared_db = tauri::async_runtime::block_on(async {
                // Use app data directory for database
                let app_data_dir = app.path().app_data_dir().expect("Failed to get app data directory");
                std::fs::create_dir_all(&app_data_dir).expect("Failed to create app data directory");
                let db_path = app_data_dir.join("curriculum_curator.db");
                crate::database::Database::create_shared(db_path.to_str().unwrap()).await
                    .expect("Failed to initialize database")
            });
            
            // Initialize LLM manager and add providers
            let mut llm_manager = LLMManager::new();
            
            // Add Ollama provider (always available for local use)
            let ollama_provider = Arc::new(crate::llm::ollama::OllamaProvider::new(None));
            tauri::async_runtime::block_on(async {
                llm_manager.add_provider(ollama_provider).await;
            });
            
            // Check for stored API keys and initialize providers
            let secure_storage = crate::llm::SecureStorage::new();
            
            // Check OpenAI
            if let Ok(openai_config) = secure_storage.get_api_key_config(&crate::llm::ProviderType::OpenAI) {
                if openai_config.enabled && !openai_config.api_key.is_empty() {
                    let openai_provider = Arc::new(crate::llm::OpenAIProvider::new(
                        openai_config.api_key,
                        openai_config.base_url,
                    ));
                    tauri::async_runtime::block_on(async {
                        llm_manager.add_provider(openai_provider).await;
                    });
                }
            }
            
            // Check Claude
            if let Ok(claude_config) = secure_storage.get_api_key_config(&crate::llm::ProviderType::Claude) {
                if claude_config.enabled && !claude_config.api_key.is_empty() {
                    let claude_provider = Arc::new(crate::llm::ClaudeProvider::new(
                        claude_config.api_key,
                        claude_config.base_url,
                    ));
                    tauri::async_runtime::block_on(async {
                        llm_manager.add_provider(claude_provider).await;
                    });
                }
            }
            
            // Check Gemini
            if let Ok(gemini_config) = secure_storage.get_api_key_config(&crate::llm::ProviderType::Gemini) {
                if gemini_config.enabled && !gemini_config.api_key.is_empty() {
                    let gemini_provider = Arc::new(crate::llm::GeminiProvider::new(
                        gemini_config.api_key,
                        gemini_config.base_url,
                    ));
                    tauri::async_runtime::block_on(async {
                        llm_manager.add_provider(gemini_provider).await;
                    });
                }
            }
            
            // Create app state
            let app_state = AppState {
                llm_manager: Arc::new(Mutex::new(llm_manager)),
            };
            
            // Initialize session service
            let session_service = SessionService::new(Arc::clone(&shared_db));
            
            // Initialize file service
            let file_service = FileService::new(Arc::clone(&shared_db), None)
                .expect("Failed to initialize file service");
            let file_service_arc = Arc::new(Mutex::new(file_service));
            
            // Initialize backup service
            let backup_session_manager = crate::session::SessionManager::new(Arc::clone(&shared_db));
            let backup_service = Arc::new(crate::backup::service::BackupService::new(
                Arc::new(Mutex::new(backup_session_manager)),
                Arc::clone(&file_service_arc)
            ));
            
            // Initialize import service
            let session_manager = crate::session::SessionManager::new(Arc::clone(&shared_db));
            let import_service = Arc::new(Mutex::new(ImportService::new(
                Arc::new(Mutex::new(session_manager)),
                None
            )));
            
            // Initialize git service
            let current_dir = std::env::current_dir().unwrap_or_else(|_| std::path::PathBuf::from("."));
            let git_service = Arc::new(Mutex::new(GitService::new(current_dir, None)));
            
            // Initialize data export service
            let session_manager2 = crate::session::SessionManager::new(Arc::clone(&shared_db));
            let data_export_service = Arc::new(Mutex::new(DataExportService::new(
                Arc::new(Mutex::new(session_manager2)),
                None,
                None
            )));
            
            // Initialize maintenance service
            let session_manager3 = crate::session::SessionManager::new(Arc::clone(&shared_db));
            let maintenance_service = Arc::new(Mutex::new(MaintenanceService::new(
                Arc::clone(&shared_db),
                Arc::new(Mutex::new(session_manager3)),
                None
            )));
            
            app.manage(app_state);
            app.manage(session_service);
            app.manage(file_service_arc);
            app.manage(backup_service);
            app.manage(import_service);
            app.manage(git_service);
            app.manage(data_export_service);
            app.manage(maintenance_service);
            
            #[cfg(debug_assertions)] // only include this code on debug builds
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}