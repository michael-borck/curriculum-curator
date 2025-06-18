use super::*;
use anyhow::{Result, Context};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::fs;
use chrono::{DateTime, Utc};
use regex::Regex;

pub struct GitService {
    config: GitConfig,
    repository_path: PathBuf,
}

impl GitService {
    pub fn new(repository_path: PathBuf, config: Option<GitConfig>) -> Self {
        Self {
            config: config.unwrap_or_default(),
            repository_path,
        }
    }

    pub fn get_config(&self) -> &GitConfig {
        &self.config
    }

    pub fn update_config(&mut self, new_config: GitConfig) -> Result<()> {
        self.config = new_config;
        // Save config to persistent storage if needed
        Ok(())
    }

    pub async fn detect_repository(&self) -> Result<GitStatus> {
        // Check if we're in a Git repository
        let is_repo = self.run_git_command(&["rev-parse", "--git-dir"]).is_ok();
        
        if !is_repo {
            return Ok(GitStatus::not_a_repository());
        }

        let mut status = GitStatus {
            is_repository: true,
            is_initialized: true,
            ..GitStatus::not_a_repository()
        };

        // Get current branch
        if let Ok(output) = self.run_git_command(&["branch", "--show-current"]) {
            status.current_branch = Some(output.trim().to_string());
        }

        // Check for remote
        if let Ok(output) = self.run_git_command(&["remote", "get-url", "origin"]) {
            status.has_remote = true;
            status.remote_url = Some(output.trim().to_string());
        }

        // Get status information
        self.update_status_info(&mut status).await?;

        // Get last commit
        status.last_commit = self.get_last_commit().await.ok();

        // Get ahead/behind info
        if status.has_remote {
            self.update_remote_tracking_info(&mut status).await?;
        }

        Ok(status)
    }

    pub async fn initialize_repository(&self, options: GitInitOptions) -> Result<()> {
        // Initialize git repository
        self.run_git_command(&["init"])?;

        // Setup gitignore if requested
        if options.setup_gitignore {
            self.create_gitignore().await?;
        }

        // Add remote if provided
        if let Some(remote_url) = options.setup_remote {
            self.run_git_command(&["remote", "add", "origin", &remote_url])?;
        }

        // Initial commit if requested
        if options.initial_commit {
            if options.setup_gitignore {
                self.run_git_command(&["add", ".gitignore"])?;
            }
            self.run_git_command(&["commit", "-m", "Initial commit", "--allow-empty"])?;
        }

        Ok(())
    }

    pub async fn commit_changes(&self, options: CommitOptions) -> Result<String> {
        if !self.config.enabled {
            return Err(anyhow::anyhow!("Git integration is disabled"));
        }

        // Add files
        if options.add_all {
            self.run_git_command(&["add", "."])?;
        } else if !options.specific_files.is_empty() {
            let mut args = vec!["add"];
            for file in &options.specific_files {
                args.push(file);
            }
            self.run_git_command(&args)?;
        }

        // Prepare commit command
        let mut commit_args = vec!["commit", "-m", &options.message];

        // Add author information if provided
        if let Some(author_name) = &options.author_name {
            commit_args.push("--author");
            if let Some(author_email) = &options.author_email {
                commit_args.push(&format!("{} <{}>", author_name, author_email));
            } else {
                commit_args.push(author_name);
            }
        }

        // Execute commit
        let output = self.run_git_command(&commit_args)?;
        
        // Extract commit hash from output
        let hash_regex = Regex::new(r"\[([a-f0-9]+)\]").unwrap();
        if let Some(captures) = hash_regex.captures(&output) {
            Ok(captures[1].to_string())
        } else {
            // Fallback to getting latest commit hash
            let hash = self.run_git_command(&["rev-parse", "HEAD"])?;
            Ok(hash.trim().to_string())
        }
    }

    pub async fn get_status(&self) -> Result<GitStatus> {
        if !self.config.enabled {
            return Ok(GitStatus::not_a_repository());
        }

        self.detect_repository().await
    }

    pub async fn get_history(&self, page: u32, per_page: u32) -> Result<GitHistory> {
        if !self.config.enabled {
            return Err(anyhow::anyhow!("Git integration is disabled"));
        }

        let skip = page * per_page;
        let output = self.run_git_command(&[
            "log",
            "--pretty=format:%H|%h|%s|%an|%ae|%at",
            &format!("--skip={}", skip),
            &format!("--max-count={}", per_page),
        ])?;

        let mut commits = Vec::new();
        for line in output.lines() {
            if let Some(commit) = self.parse_commit_line(line).await? {
                commits.push(commit);
            }
        }

        // Get total count
        let total_output = self.run_git_command(&["rev-list", "--count", "HEAD"])?;
        let total_count = total_output.trim().parse::<u32>().unwrap_or(0);

        Ok(GitHistory {
            commits,
            total_count,
            page,
            per_page,
        })
    }

    pub async fn get_diff(&self, commit_hash: Option<&str>, file_path: Option<&str>) -> Result<Vec<GitDiff>> {
        if !self.config.enabled {
            return Err(anyhow::anyhow!("Git integration is disabled"));
        }

        let mut args = vec!["diff"];
        
        if let Some(hash) = commit_hash {
            args.push(hash);
        } else {
            args.push("HEAD");
        }

        if let Some(file) = file_path {
            args.push("--");
            args.push(file);
        }

        let output = self.run_git_command(&args)?;
        self.parse_diff_output(&output).await
    }

    pub async fn auto_commit_session(&self, session_name: &str) -> Result<Option<String>> {
        if !self.config.enabled || !self.config.auto_commit_on_session_save {
            return Ok(None);
        }

        let status = self.get_status().await?;
        if !status.has_changes() {
            return Ok(None);
        }

        let message = self.config.commit_message_template
            .replace("{session_name}", session_name)
            .replace("{timestamp}", &Utc::now().format("%Y-%m-%d %H:%M:%S UTC").to_string());

        let commit_hash = self.commit_changes(CommitOptions {
            message,
            author_name: None,
            author_email: None,
            add_all: true,
            specific_files: vec![],
        }).await?;

        Ok(Some(commit_hash))
    }

    pub async fn auto_commit_content_generation(&self, content_types: &[String]) -> Result<Option<String>> {
        if !self.config.enabled || !self.config.auto_commit_on_content_generation {
            return Ok(None);
        }

        let status = self.get_status().await?;
        if !status.has_changes() {
            return Ok(None);
        }

        let message = format!(
            "Generated content: {} - {}",
            content_types.join(", "),
            Utc::now().format("%Y-%m-%d %H:%M:%S UTC")
        );

        let commit_hash = self.commit_changes(CommitOptions {
            message,
            author_name: None,
            author_email: None,
            add_all: true,
            specific_files: vec![],
        }).await?;

        Ok(Some(commit_hash))
    }

    // Private helper methods
    fn run_git_command(&self, args: &[&str]) -> Result<String> {
        let output = Command::new("git")
            .args(args)
            .current_dir(&self.repository_path)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .context("Failed to execute git command")?;

        if output.status.success() {
            Ok(String::from_utf8_lossy(&output.stdout).to_string())
        } else {
            let error = String::from_utf8_lossy(&output.stderr);
            Err(anyhow::anyhow!("Git command failed: {}", error))
        }
    }

    async fn update_status_info(&self, status: &mut GitStatus) -> Result<()> {
        // Get porcelain status
        let output = self.run_git_command(&["status", "--porcelain"])?;
        
        for line in output.lines() {
            if line.len() < 3 {
                continue;
            }
            
            let file_path = line[3..].to_string();
            let status_code = &line[..2];
            
            match status_code {
                s if s.starts_with('M') || s.starts_with('A') || s.starts_with('D') || s.starts_with('R') => {
                    status.staged_files.push(file_path.clone());
                }
                s if s.ends_with('M') || s.ends_with('A') || s.ends_with('D') => {
                    status.modified_files.push(file_path.clone());
                }
                "??" => {
                    status.untracked_files.push(file_path);
                }
                _ => {}
            }
        }

        Ok(())
    }

    async fn get_last_commit(&self) -> Result<GitCommit> {
        let output = self.run_git_command(&[
            "log",
            "-1",
            "--pretty=format:%H|%h|%s|%an|%ae|%at",
        ])?;

        if let Some(commit) = self.parse_commit_line(&output).await? {
            Ok(commit)
        } else {
            Err(anyhow::anyhow!("No commits found"))
        }
    }

    async fn update_remote_tracking_info(&self, status: &mut GitStatus) -> Result<()> {
        // Get ahead/behind info
        if let Ok(output) = self.run_git_command(&["rev-list", "--count", "--left-right", "HEAD...origin/main"]) {
            let parts: Vec<&str> = output.trim().split('\t').collect();
            if parts.len() == 2 {
                status.commits_ahead = parts[0].parse().unwrap_or(0);
                status.commits_behind = parts[1].parse().unwrap_or(0);
            }
        }

        Ok(())
    }

    async fn parse_commit_line(&self, line: &str) -> Result<Option<GitCommit>> {
        let parts: Vec<&str> = line.split('|').collect();
        if parts.len() != 6 {
            return Ok(None);
        }

        let timestamp = parts[5].parse::<i64>()
            .context("Failed to parse timestamp")?;
        let timestamp = DateTime::from_timestamp(timestamp, 0)
            .ok_or_else(|| anyhow::anyhow!("Invalid timestamp"))?;

        // Get changed files for this commit
        let files_output = self.run_git_command(&[
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            parts[0],
        ])?;
        let files_changed: Vec<String> = files_output
            .lines()
            .map(|s| s.to_string())
            .collect();

        Ok(Some(GitCommit {
            hash: parts[0].to_string(),
            short_hash: parts[1].to_string(),
            message: parts[2].to_string(),
            author: parts[3].to_string(),
            email: parts[4].to_string(),
            timestamp,
            files_changed,
        }))
    }

    async fn parse_diff_output(&self, output: &str) -> Result<Vec<GitDiff>> {
        // This is a simplified diff parser
        // In a real implementation, you'd want a more robust parser
        let mut diffs = Vec::new();
        let mut current_diff: Option<GitDiff> = None;
        let mut current_hunk: Option<DiffHunk> = None;

        for line in output.lines() {
            if line.starts_with("diff --git") {
                // Save previous diff
                if let Some(mut diff) = current_diff.take() {
                    if let Some(hunk) = current_hunk.take() {
                        diff.hunks.push(hunk);
                    }
                    diffs.push(diff);
                }

                // Start new diff
                let file_path = line.split_whitespace().nth(2)
                    .unwrap_or("unknown")
                    .trim_start_matches("a/")
                    .trim_start_matches("b/")
                    .to_string();

                current_diff = Some(GitDiff {
                    file_path,
                    old_content: None,
                    new_content: None,
                    hunks: vec![],
                    is_binary: false,
                    is_new_file: false,
                    is_deleted_file: false,
                });
            } else if line.starts_with("@@") {
                // Save previous hunk
                if let Some(hunk) = current_hunk.take() {
                    if let Some(ref mut diff) = current_diff {
                        diff.hunks.push(hunk);
                    }
                }

                // Parse hunk header
                let hunk_regex = Regex::new(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@").unwrap();
                if let Some(captures) = hunk_regex.captures(line) {
                    current_hunk = Some(DiffHunk {
                        old_start: captures[1].parse().unwrap_or(0),
                        old_lines: captures[2].parse().unwrap_or(0),
                        new_start: captures[3].parse().unwrap_or(0),
                        new_lines: captures[4].parse().unwrap_or(0),
                        lines: vec![],
                    });
                }
            } else if let Some(ref mut hunk) = current_hunk {
                // Parse diff line
                let line_type = if line.starts_with('+') {
                    DiffLineType::Added
                } else if line.starts_with('-') {
                    DiffLineType::Removed
                } else {
                    DiffLineType::Context
                };

                hunk.lines.push(DiffLine {
                    line_type,
                    content: line[1..].to_string(),
                    old_line_number: None, // Would need more complex tracking
                    new_line_number: None,
                });
            }
        }

        // Save final diff and hunk
        if let Some(mut diff) = current_diff {
            if let Some(hunk) = current_hunk {
                diff.hunks.push(hunk);
            }
            diffs.push(diff);
        }

        Ok(diffs)
    }

    async fn create_gitignore(&self) -> Result<()> {
        let gitignore_content = format!(
            "# Curriculum Curator
# Generated by Curriculum Curator application

{}

# Application-specific
*.tmp
*.log
.env
curriculum_curator.db
curriculum_curator.db-*

# OS-specific
.DS_Store
Thumbs.db

# IDE-specific
.vscode/
.idea/
*.swp
*.swo

# Backup files
*.bak
*~
",
            self.config.ignored_patterns.join("\n")
        );

        let gitignore_path = self.repository_path.join(".gitignore");
        fs::write(gitignore_path, gitignore_content)
            .context("Failed to create .gitignore file")?;

        Ok(())
    }
}