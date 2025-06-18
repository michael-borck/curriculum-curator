use super::*;
use crate::git::service::GitService;
use tauri::State;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::path::PathBuf;
use anyhow::Result;

#[tauri::command]
pub async fn get_git_config(
    git_service: State<'_, Arc<Mutex<GitService>>>,
) -> Result<GitConfig, String> {
    let service = git_service.lock().await;
    Ok(service.get_config().clone())
}

#[tauri::command]
pub async fn update_git_config(
    git_service: State<'_, Arc<Mutex<GitService>>>,
    config: GitConfig,
) -> Result<(), String> {
    let mut service = git_service.lock().await;
    service.update_config(config)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn detect_git_repository(
    git_service: State<'_, Arc<Mutex<GitService>>>,
) -> Result<GitStatus, String> {
    let service = git_service.lock().await;
    service.detect_repository().await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn initialize_git_repository(
    git_service: State<'_, Arc<Mutex<GitService>>>,
    options: GitInitOptions,
) -> Result<(), String> {
    let service = git_service.lock().await;
    service.initialize_repository(options).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_git_status(
    git_service: State<'_, Arc<Mutex<GitService>>>,
) -> Result<GitStatus, String> {
    let service = git_service.lock().await;
    service.get_status().await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn commit_git_changes(
    git_service: State<'_, Arc<Mutex<GitService>>>,
    options: CommitOptions,
) -> Result<String, String> {
    let service = git_service.lock().await;
    service.commit_changes(options).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_git_history(
    git_service: State<'_, Arc<Mutex<GitService>>>,
    page: u32,
    per_page: u32,
) -> Result<GitHistory, String> {
    let service = git_service.lock().await;
    service.get_history(page, per_page).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_git_diff(
    git_service: State<'_, Arc<Mutex<GitService>>>,
    commit_hash: Option<String>,
    file_path: Option<String>,
) -> Result<Vec<GitDiff>, String> {
    let service = git_service.lock().await;
    service.get_diff(
        commit_hash.as_deref(),
        file_path.as_deref()
    ).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn auto_commit_session(
    git_service: State<'_, Arc<Mutex<GitService>>>,
    session_name: String,
) -> Result<Option<String>, String> {
    let service = git_service.lock().await;
    service.auto_commit_session(&session_name).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn auto_commit_content_generation(
    git_service: State<'_, Arc<Mutex<GitService>>>,
    content_types: Vec<String>,
) -> Result<Option<String>, String> {
    let service = git_service.lock().await;
    service.auto_commit_content_generation(&content_types).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn check_git_installation() -> Result<GitInstallationInfo, String> {
    // Check if git is installed and get version
    let output = std::process::Command::new("git")
        .args(&["--version"])
        .output();

    match output {
        Ok(output) if output.status.success() => {
            let version_str = String::from_utf8_lossy(&output.stdout);
            let version = version_str.trim().strip_prefix("git version ")
                .unwrap_or("unknown")
                .to_string();

            Ok(GitInstallationInfo {
                is_installed: true,
                version: Some(version),
                path: which_git().await.ok(),
                error: None,
            })
        }
        Ok(output) => {
            let error = String::from_utf8_lossy(&output.stderr);
            Ok(GitInstallationInfo {
                is_installed: false,
                version: None,
                path: None,
                error: Some(error.to_string()),
            })
        }
        Err(e) => {
            Ok(GitInstallationInfo {
                is_installed: false,
                version: None,
                path: None,
                error: Some(e.to_string()),
            })
        }
    }
}

#[tauri::command]
pub async fn get_git_user_config() -> Result<GitUserConfig, String> {
    let name_result = std::process::Command::new("git")
        .args(&["config", "--global", "user.name"])
        .output();

    let email_result = std::process::Command::new("git")
        .args(&["config", "--global", "user.email"])
        .output();

    let name = if let Ok(output) = name_result {
        if output.status.success() {
            Some(String::from_utf8_lossy(&output.stdout).trim().to_string())
        } else {
            None
        }
    } else {
        None
    };

    let email = if let Ok(output) = email_result {
        if output.status.success() {
            Some(String::from_utf8_lossy(&output.stdout).trim().to_string())
        } else {
            None
        }
    } else {
        None
    };

    Ok(GitUserConfig { name, email })
}

#[tauri::command]
pub async fn set_git_user_config(
    name: Option<String>,
    email: Option<String>,
) -> Result<(), String> {
    if let Some(name) = name {
        let output = std::process::Command::new("git")
            .args(&["config", "--global", "user.name", &name])
            .output()
            .map_err(|e| format!("Failed to set git user name: {}", e))?;

        if !output.status.success() {
            return Err(format!("Failed to set git user name: {}", 
                String::from_utf8_lossy(&output.stderr)));
        }
    }

    if let Some(email) = email {
        let output = std::process::Command::new("git")
            .args(&["config", "--global", "user.email", &email])
            .output()
            .map_err(|e| format!("Failed to set git user email: {}", e))?;

        if !output.status.success() {
            return Err(format!("Failed to set git user email: {}", 
                String::from_utf8_lossy(&output.stderr)));
        }
    }

    Ok(())
}

#[tauri::command]
pub async fn validate_repository_path(
    path: String,
) -> Result<RepositoryValidation, String> {
    let path_buf = PathBuf::from(&path);
    
    if !path_buf.exists() {
        return Ok(RepositoryValidation {
            is_valid: false,
            is_git_repository: false,
            can_initialize: path_buf.parent().map(|p| p.exists()).unwrap_or(false),
            error_message: Some("Path does not exist".to_string()),
        });
    }

    if !path_buf.is_dir() {
        return Ok(RepositoryValidation {
            is_valid: false,
            is_git_repository: false,
            can_initialize: false,
            error_message: Some("Path is not a directory".to_string()),
        });
    }

    // Check if it's already a git repository
    let git_dir = path_buf.join(".git");
    let is_git_repo = git_dir.exists();

    Ok(RepositoryValidation {
        is_valid: true,
        is_git_repository: is_git_repo,
        can_initialize: !is_git_repo,
        error_message: None,
    })
}

// Helper function to find git executable
async fn which_git() -> Result<PathBuf> {
    let output = std::process::Command::new("which")
        .args(&["git"])
        .output()?;

    if output.status.success() {
        let path_str = String::from_utf8_lossy(&output.stdout);
        Ok(PathBuf::from(path_str.trim()))
    } else {
        Err(anyhow::anyhow!("Git executable not found in PATH"))
    }
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct GitInstallationInfo {
    pub is_installed: bool,
    pub version: Option<String>,
    pub path: Option<PathBuf>,
    pub error: Option<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct GitUserConfig {
    pub name: Option<String>,
    pub email: Option<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct RepositoryValidation {
    pub is_valid: bool,
    pub is_git_repository: bool,
    pub can_initialize: bool,
    pub error_message: Option<String>,
}