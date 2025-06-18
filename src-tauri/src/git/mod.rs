use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use chrono::{DateTime, Utc};

pub mod service;
pub mod commands;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitConfig {
    pub enabled: bool,
    pub auto_commit: bool,
    pub auto_commit_on_session_save: bool,
    pub auto_commit_on_content_generation: bool,
    pub commit_message_template: String,
    pub ignored_patterns: Vec<String>,
    pub repository_path: Option<PathBuf>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitStatus {
    pub is_repository: bool,
    pub is_initialized: bool,
    pub current_branch: Option<String>,
    pub has_remote: bool,
    pub remote_url: Option<String>,
    pub modified_files: Vec<String>,
    pub staged_files: Vec<String>,
    pub untracked_files: Vec<String>,
    pub commits_ahead: u32,
    pub commits_behind: u32,
    pub last_commit: Option<GitCommit>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitCommit {
    pub hash: String,
    pub short_hash: String,
    pub message: String,
    pub author: String,
    pub email: String,
    pub timestamp: DateTime<Utc>,
    pub files_changed: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitHistory {
    pub commits: Vec<GitCommit>,
    pub total_count: u32,
    pub page: u32,
    pub per_page: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitDiff {
    pub file_path: String,
    pub old_content: Option<String>,
    pub new_content: Option<String>,
    pub hunks: Vec<DiffHunk>,
    pub is_binary: bool,
    pub is_new_file: bool,
    pub is_deleted_file: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiffHunk {
    pub old_start: u32,
    pub old_lines: u32,
    pub new_start: u32,
    pub new_lines: u32,
    pub lines: Vec<DiffLine>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiffLine {
    pub line_type: DiffLineType,
    pub content: String,
    pub old_line_number: Option<u32>,
    pub new_line_number: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DiffLineType {
    Context,
    Added,
    Removed,
    Header,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitInitOptions {
    pub repository_path: PathBuf,
    pub initial_commit: bool,
    pub setup_gitignore: bool,
    pub setup_remote: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommitOptions {
    pub message: String,
    pub author_name: Option<String>,
    pub author_email: Option<String>,
    pub add_all: bool,
    pub specific_files: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitRemoteInfo {
    pub name: String,
    pub url: String,
    pub fetch_url: String,
    pub push_url: String,
}

impl Default for GitConfig {
    fn default() -> Self {
        Self {
            enabled: false, // Disabled by default - user must explicitly enable
            auto_commit: false,
            auto_commit_on_session_save: false,
            auto_commit_on_content_generation: false,
            commit_message_template: "Update session: {session_name} - {timestamp}".to_string(),
            ignored_patterns: vec![
                "target/".to_string(),
                "node_modules/".to_string(),
                "*.tmp".to_string(),
                "*.log".to_string(),
                ".env".to_string(),
                "curriculum_curator.db".to_string(),
            ],
            repository_path: None,
        }
    }
}

impl GitStatus {
    pub fn not_a_repository() -> Self {
        Self {
            is_repository: false,
            is_initialized: false,
            current_branch: None,
            has_remote: false,
            remote_url: None,
            modified_files: vec![],
            staged_files: vec![],
            untracked_files: vec![],
            commits_ahead: 0,
            commits_behind: 0,
            last_commit: None,
        }
    }

    pub fn has_changes(&self) -> bool {
        !self.modified_files.is_empty() || !self.staged_files.is_empty() || !self.untracked_files.is_empty()
    }

    pub fn is_clean(&self) -> bool {
        !self.has_changes()
    }

    pub fn can_commit(&self) -> bool {
        !self.staged_files.is_empty() || (!self.modified_files.is_empty() && !self.untracked_files.is_empty())
    }
}

impl GitCommit {
    pub fn format_message(&self, max_length: Option<usize>) -> String {
        match max_length {
            Some(len) if self.message.len() > len => {
                format!("{}...", &self.message[..len.saturating_sub(3)])
            }
            _ => self.message.clone(),
        }
    }

    pub fn get_relative_time(&self) -> String {
        let now = Utc::now();
        let duration = now.signed_duration_since(self.timestamp);

        if duration.num_days() > 0 {
            format!("{} days ago", duration.num_days())
        } else if duration.num_hours() > 0 {
            format!("{} hours ago", duration.num_hours())
        } else if duration.num_minutes() > 0 {
            format!("{} minutes ago", duration.num_minutes())
        } else {
            "Just now".to_string()
        }
    }
}

impl DiffLineType {
    pub fn symbol(&self) -> &'static str {
        match self {
            DiffLineType::Context => " ",
            DiffLineType::Added => "+",
            DiffLineType::Removed => "-",
            DiffLineType::Header => "@",
        }
    }

    pub fn color(&self) -> &'static str {
        match self {
            DiffLineType::Context => "#374151",
            DiffLineType::Added => "#059669",
            DiffLineType::Removed => "#dc2626",
            DiffLineType::Header => "#3b82f6",
        }
    }
}