// Allow warnings for features under development
#![allow(dead_code)]
#![allow(unused_imports)]
#![allow(unused_variables)]
#![allow(unused_mut)]

pub mod llm;
pub mod content;
pub mod validation;
pub mod export;
pub mod session;
pub mod commands;
pub mod database;
pub mod import;

use commands::*;
use validation::{
    validate_content_command, get_validation_progress_command, list_validators_command,
    get_validation_config_command, auto_fix_issues_command
};
use import::commands::{
    get_import_config, update_import_config, preview_import_file, import_file,
    import_file_with_progress, get_supported_file_types, validate_import_file
};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .manage(validation::ValidationService::new())
        .invoke_handler(tauri::generate_handler![
            health_check,
            create_project_directory,
            check_file_exists,
            test_llm_connection,
            create_new_session,
            generate_content,
            get_app_config,
            set_app_config,
            validate_content,
            validate_content_command,
            get_validation_progress_command,
            list_validators_command,
            get_validation_config_command,
            auto_fix_issues_command,
            get_available_providers,
            get_ollama_models,
            get_model_recommendations,
            get_ollama_installation_instructions,
            check_system_requirements,
            test_llm_generation,
            get_session_cost,
            export_content,
            get_supported_export_formats,
            validate_export_path,
            store_api_key,
            get_api_key_config,
            remove_api_key,
            list_configured_providers,
            update_provider_config,
            validate_api_key_format,
            import_api_keys_from_env,
            export_provider_config_template,
            clear_all_api_keys,
            test_external_provider,
            get_external_provider_models,
            estimate_external_provider_cost,
            setup_provider_from_wizard,
            get_import_config,
            update_import_config,
            preview_import_file,
            import_file,
            import_file_with_progress,
            get_supported_file_types,
            validate_import_file
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}