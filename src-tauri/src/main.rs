// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

mod commands;
mod content;
mod database;
mod export;
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
            
            // Session management
            commands::create_new_session,
            commands::list_sessions,
            commands::get_session_content,
            
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
            commands::test_offline_generation
        ])
        .setup(|app| {
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