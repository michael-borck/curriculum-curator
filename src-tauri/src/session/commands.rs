use super::storage::{SessionManager, Session, SessionConfig};
use crate::content::{ContentRequest, GeneratedContent};
use anyhow::Result;
use serde::{Deserialize, Serialize};
use tokio::sync::Mutex;
use tauri::State;
use uuid::Uuid;
use chrono::{DateTime, Utc};

/// Global session service state
pub struct SessionService {
    manager: Mutex<SessionManager>,
}

impl SessionService {
    pub fn new(shared_db: crate::database::SharedDatabase) -> Self {
        let manager = SessionManager::new(shared_db);
        Self {
            manager: Mutex::new(manager),
        }
    }
}

/// Request to create a new session
#[derive(Debug, Serialize, Deserialize)]
pub struct CreateSessionRequest {
    pub name: String,
    pub config: Option<SessionConfig>,
}

/// Response containing session information
#[derive(Debug, Serialize, Deserialize)]
pub struct SessionResponse {
    pub session: Session,
    pub metadata: SessionMetadata,
}

/// Metadata about the session
#[derive(Debug, Serialize, Deserialize)]
pub struct SessionMetadata {
    pub content_count: usize,
    pub total_cost: Option<f64>,
    pub last_activity: DateTime<Utc>,
    pub size_mb: f64,
}

/// Request to update session information
#[derive(Debug, Serialize, Deserialize)]
pub struct UpdateSessionRequest {
    pub id: Uuid,
    pub name: Option<String>,
    pub content_request: Option<ContentRequest>,
    pub config: Option<SessionConfig>,
}

/// Request to add content to a session
#[derive(Debug, Serialize, Deserialize)]
pub struct AddContentRequest {
    pub session_id: Uuid,
    pub content: GeneratedContent,
}

/// Session list item for browsing
#[derive(Debug, Serialize, Deserialize)]
pub struct SessionListItem {
    pub id: Uuid,
    pub name: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub content_count: usize,
    pub has_content_request: bool,
    pub total_cost: Option<f64>,
    pub preview: Option<String>, // First few lines of content for preview
}

/// Session statistics
#[derive(Debug, Serialize, Deserialize)]
pub struct SessionStatistics {
    pub total_sessions: usize,
    pub total_content_items: usize,
    pub total_cost: f64,
    pub most_recent_session: Option<DateTime<Utc>>,
    pub average_content_per_session: f64,
    pub storage_used_mb: f64,
}

/// Session search and filter options
#[derive(Debug, Serialize, Deserialize)]
pub struct SessionFilter {
    pub name_contains: Option<String>,
    pub created_after: Option<DateTime<Utc>>,
    pub created_before: Option<DateTime<Utc>>,
    pub has_content: Option<bool>,
    pub limit: Option<usize>,
    pub offset: Option<usize>,
}

/// Tauri command to create a new session
#[tauri::command]
pub async fn create_session(
    request: CreateSessionRequest,
    service: State<'_, SessionService>,
) -> Result<SessionResponse, String> {
    let mut session = {
        let manager = service.manager.lock().await;
        manager.create_session(request.name).await.map_err(|e| e.to_string())?
    };
    
    // Apply custom config if provided
    if let Some(config) = request.config {
        session.config = config;
        let manager = service.manager.lock().await;
        manager.save_session(&session).await.map_err(|e| e.to_string())?;
    }
    
    let metadata = SessionMetadata {
        content_count: 0,
        total_cost: Some(0.0),
        last_activity: session.updated_at,
        size_mb: 0.0,
    };
    
    Ok(SessionResponse {
        session,
        metadata,
    })
}

/// Tauri command to load an existing session
#[tauri::command]
pub async fn load_session(
    session_id: String,
    service: State<'_, SessionService>,
) -> Result<Option<SessionResponse>, String> {
    let session_uuid = Uuid::parse_str(&session_id).map_err(|e| e.to_string())?;
    
    let (session_opt, total_cost) = {
        let manager = service.manager.lock().await;
        let session = manager.load_session(session_uuid).await.map_err(|e| e.to_string())?;
        let cost = if session.is_some() {
            manager.get_session_cost(session_uuid).await.unwrap_or(0.0)
        } else {
            0.0
        };
        (session, cost)
    };
    
    if let Some(session) = session_opt {
        let metadata = SessionMetadata {
            content_count: session.generated_content.len(),
            total_cost: Some(total_cost),
            last_activity: session.updated_at,
            size_mb: calculate_session_size(&session),
        };
        
        Ok(Some(SessionResponse {
            session,
            metadata,
        }))
    } else {
        Ok(None)
    }
}

/// Tauri command to save session changes
#[tauri::command]
pub async fn save_session(
    session: Session,
    service: State<'_, SessionService>,
) -> Result<(), String> {
    let mut updated_session = session;
    updated_session.updated_at = Utc::now();
    
    let manager = service.manager.lock().await;
    manager.save_session(&updated_session).await.map_err(|e| e.to_string())?;
    
    Ok(())
}

/// Tauri command to update session information
#[tauri::command]
pub async fn update_session(
    request: UpdateSessionRequest,
    service: State<'_, SessionService>,
) -> Result<SessionResponse, String> {
    let (mut session, total_cost) = {
        let manager = service.manager.lock().await;
        if let Some(mut session) = manager.load_session(request.id).await.map_err(|e| e.to_string())? {
            // Update fields if provided
            if let Some(name) = request.name {
                session.name = name;
            }
            if let Some(content_request) = request.content_request {
                session.content_request = Some(content_request);
            }
            if let Some(config) = request.config {
                session.config = config;
            }
            
            session.updated_at = Utc::now();
            
            manager.save_session(&session).await.map_err(|e| e.to_string())?;
            
            let total_cost = manager.get_session_cost(request.id).await.unwrap_or(0.0);
            (session, total_cost)
        } else {
            return Err("Session not found".to_string());
        }
    };
    
    let metadata = SessionMetadata {
        content_count: session.generated_content.len(),
        total_cost: Some(total_cost),
        last_activity: session.updated_at,
        size_mb: calculate_session_size(&session),
    };
    
    Ok(SessionResponse {
        session,
        metadata,
    })
}

/// Tauri command to add content to a session
#[tauri::command]
pub async fn add_content_to_session(
    request: AddContentRequest,
    service: State<'_, SessionService>,
) -> Result<String, String> {
    let manager = service.manager.lock().await;
    
    let content_id = manager
        .add_content_to_session(request.session_id, &request.content)
        .await
        .map_err(|e| e.to_string())?;
    
    Ok(content_id)
}

/// Tauri command to list all sessions with filtering
#[tauri::command]
pub async fn list_sessions(
    filter: Option<SessionFilter>,
    service: State<'_, SessionService>,
) -> Result<Vec<SessionListItem>, String> {
    let sessions = {
        let manager = service.manager.lock().await;
        manager.list_sessions().await.map_err(|e| e.to_string())?
    };
    
    let mut session_items = Vec::new();
    
    for session in sessions {
        // Apply filtering if provided
        if let Some(ref filter) = filter {
            if let Some(ref name_filter) = filter.name_contains {
                if !session.name.to_lowercase().contains(&name_filter.to_lowercase()) {
                    continue;
                }
            }
            
            if let Some(after) = filter.created_after {
                if session.created_at < after {
                    continue;
                }
            }
            
            if let Some(before) = filter.created_before {
                if session.created_at > before {
                    continue;
                }
            }
        }
        
        let (content, total_cost) = {
            let manager = service.manager.lock().await;
            let content = manager.get_session_content(session.id).await.unwrap_or_default();
            let total_cost = manager.get_session_cost(session.id).await.ok();
            (content, total_cost)
        };
        
        // Generate preview from first content item
        let preview = content.first().map(|c| {
            let preview_text = &c.content;
            if preview_text.len() > 100 {
                format!("{}...", &preview_text[..100])
            } else {
                preview_text.clone()
            }
        });
        
        session_items.push(SessionListItem {
            id: session.id,
            name: session.name,
            created_at: session.created_at,
            updated_at: session.updated_at,
            content_count: content.len(),
            has_content_request: session.content_request.is_some(),
            total_cost,
            preview,
        });
    }
    
    // Apply limit and offset if provided
    if let Some(filter) = filter {
        if let Some(offset) = filter.offset {
            if offset < session_items.len() {
                session_items = session_items.into_iter().skip(offset).collect();
            } else {
                session_items = vec![];
            }
        }
        
        if let Some(limit) = filter.limit {
            session_items.truncate(limit);
        }
    }
    
    // Sort by updated_at descending (most recent first)
    session_items.sort_by(|a, b| b.updated_at.cmp(&a.updated_at));
    
    Ok(session_items)
}

/// Tauri command to delete a session
#[tauri::command]
pub async fn delete_session(
    session_id: String,
    service: State<'_, SessionService>,
) -> Result<(), String> {
    let session_uuid = Uuid::parse_str(&session_id).map_err(|e| e.to_string())?;
    let manager = service.manager.lock().await;
    
    manager.delete_session(session_uuid).await.map_err(|e| e.to_string())?;
    
    Ok(())
}

/// Tauri command to get session statistics
#[tauri::command]
pub async fn get_session_statistics(
    service: State<'_, SessionService>,
) -> Result<SessionStatistics, String> {
    let sessions = {
        let manager = service.manager.lock().await;
        manager.list_sessions().await.map_err(|e| e.to_string())?
    };
    let total_sessions = sessions.len();
    
    let mut total_content_items = 0;
    let mut total_cost = 0.0;
    let mut storage_used_mb = 0.0;
    let most_recent_session = sessions.iter().map(|s| s.updated_at).max();
    
    for session in &sessions {
        let (content, cost) = {
            let manager = service.manager.lock().await;
            let content = manager.get_session_content(session.id).await.unwrap_or_default();
            let cost = manager.get_session_cost(session.id).await.unwrap_or(0.0);
            (content, cost)
        };
        
        total_content_items += content.len();
        total_cost += cost;
        storage_used_mb += calculate_session_size(session);
    }
    
    let average_content_per_session = if total_sessions > 0 {
        total_content_items as f64 / total_sessions as f64
    } else {
        0.0
    };
    
    Ok(SessionStatistics {
        total_sessions,
        total_content_items,
        total_cost,
        most_recent_session,
        average_content_per_session,
        storage_used_mb,
    })
}

/// Tauri command to duplicate a session
#[tauri::command]
pub async fn duplicate_session(
    session_id: String,
    new_name: String,
    service: State<'_, SessionService>,
) -> Result<SessionResponse, String> {
    let session_uuid = Uuid::parse_str(&session_id).map_err(|e| e.to_string())?;
    
    let final_session = {
        let manager = service.manager.lock().await;
        
        if let Some(original_session) = manager.load_session(session_uuid).await.map_err(|e| e.to_string())? {
            // Create new session with copied data
            let mut new_session = manager.create_session(new_name).await.map_err(|e| e.to_string())?;
            new_session.content_request = original_session.content_request;
            new_session.config = original_session.config;
            
            manager.save_session(&new_session).await.map_err(|e| e.to_string())?;
            
            // Copy all content to new session
            for content in &original_session.generated_content {
                manager.add_content_to_session(new_session.id, content).await.map_err(|e| e.to_string())?;
            }
            
            // Reload session with content
            manager.load_session(new_session.id).await.map_err(|e| e.to_string())?
                .ok_or("Failed to reload duplicated session".to_string())?
        } else {
            return Err("Original session not found".to_string());
        }
    };
    
    let metadata = SessionMetadata {
        content_count: final_session.generated_content.len(),
        total_cost: Some(0.0), // New session, no cost yet
        last_activity: final_session.updated_at,
        size_mb: calculate_session_size(&final_session),
    };
    
    Ok(SessionResponse {
        session: final_session,
        metadata,
    })
}

/// Tauri command to get content for a specific session
#[tauri::command]
pub async fn get_session_content(
    session_id: String,
    service: State<'_, SessionService>,
) -> Result<Vec<GeneratedContent>, String> {
    let session_uuid = Uuid::parse_str(&session_id).map_err(|e| e.to_string())?;
    let manager = service.manager.lock().await;
    
    let content = manager.get_session_content(session_uuid).await.map_err(|e| e.to_string())?;
    
    Ok(content)
}

/// Helper function to calculate session size in MB
fn calculate_session_size(session: &Session) -> f64 {
    let session_json = serde_json::to_string(session).unwrap_or_default();
    let content_size: usize = session.generated_content.iter()
        .map(|c| c.content.len())
        .sum();
    
    (session_json.len() + content_size) as f64 / (1024.0 * 1024.0)
}

/// Export session command names for registration
pub fn get_session_command_names() -> Vec<&'static str> {
    vec![
        "create_session",
        "load_session", 
        "save_session",
        "update_session",
        "add_content_to_session",
        "list_sessions",
        "delete_session",
        "get_session_statistics",
        "duplicate_session",
        "get_session_content",
    ]
}