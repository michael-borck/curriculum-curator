// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// Allow warnings for features under development
#![allow(dead_code)]
#![allow(unused_imports)]
#![allow(unused_variables)]
#![allow(unused_mut)]

use tauri::Manager;
use session::SessionService;
use file_manager::FileService;
use backup::{BackupService, scheduler::BackupScheduler};
use import::{ImportService, ImportConfig};
use git::{GitService, GitConfig};
use std::sync::Arc;
use tokio::sync::Mutex;

mod backup;
mod commands;
mod content;
mod database;
mod export;
mod file_manager;
mod git;
mod import;
mod llm;
mod session;
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
            git::commands::validate_repository_path
        ])
        .setup(|app| {
            // Initialize session service
            let session_service = tauri::async_runtime::block_on(async {
                SessionService::new("./data/sessions.db").await
                    .expect("Failed to initialize session service")
            });
            
            // Initialize file service
            let file_service = tauri::async_runtime::block_on(async {
                FileService::new("./data/sessions.db", None).await
                    .expect("Failed to initialize file service")
            });
            
            // Initialize backup service
            let backup_service = Arc::new(BackupService::new(
                Arc::new(tokio::sync::Mutex::new(session_service.session_manager.clone())),
                Arc::new(tokio::sync::Mutex::new(file_service.clone()))
            ));
            
            // Initialize backup scheduler
            let backup_scheduler = Arc::new(BackupScheduler::new(Arc::clone(&backup_service)));
            
            // Start backup scheduler
            tauri::async_runtime::spawn(async move {
                if let Err(e) = backup_scheduler.start().await {
                    eprintln!("Failed to start backup scheduler: {}", e);
                }
            });
            
            // Initialize import service
            let import_service = Arc::new(Mutex::new(ImportService::new(
                Arc::new(Mutex::new(session_service.session_manager.clone())),
                Some(Arc::clone(&backup_service))
            )));
            
            // Initialize git service
            let current_dir = std::env::current_dir().unwrap_or_else(|_| std::path::PathBuf::from("."));
            let git_service = Arc::new(Mutex::new(GitService::new(current_dir, None)));
            
            app.manage(session_service);
            app.manage(file_service);
            app.manage(backup_service);
            app.manage(import_service);
            app.manage(git_service);
            
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