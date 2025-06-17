use super::remediation::*;
use super::validators::*;
use crate::content::GeneratedContent;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Mutex;
use tauri::State;
use uuid::Uuid;

/// Global remediation service state
pub struct RemediationService {
    manager: Mutex<RemediationManager>,
    user_preferences: Mutex<HashMap<String, RemediationPreferences>>,
}

impl RemediationService {
    pub fn new() -> Self {
        Self {
            manager: Mutex::new(RemediationManager::new()),
            user_preferences: Mutex::new(HashMap::new()),
        }
    }
    
    pub fn with_config(config: RemediationConfig) -> Self {
        Self {
            manager: Mutex::new(RemediationManager::with_config(config)),
            user_preferences: Mutex::new(HashMap::new()),
        }
    }
}

/// Request to generate remediation suggestions
#[derive(Debug, Serialize, Deserialize)]
pub struct GenerateRemediationRequest {
    pub content: GeneratedContent,
    pub validation_issues: Vec<ValidationIssue>,
    pub user_id: Option<String>,
}

/// Response containing remediation suggestions
#[derive(Debug, Serialize, Deserialize)]
pub struct RemediationResponse {
    pub session_id: Uuid,
    pub suggestions: Vec<RemediationSuggestion>,
    pub auto_applied_fixes: Vec<AppliedFix>,
    pub requires_user_review: bool,
    pub total_suggestions: usize,
    pub high_priority_count: usize,
}

/// Request to apply a specific fix
#[derive(Debug, Serialize, Deserialize)]
pub struct ApplyFixRequest {
    pub session_id: Uuid,
    pub suggestion_id: Uuid,
    pub user_approved: bool,
    pub alternative_id: Option<Uuid>,
}

/// Request to record user decision
#[derive(Debug, Serialize, Deserialize)]
pub struct UserDecisionRequest {
    pub session_id: Uuid,
    pub suggestion_id: Uuid,
    pub decision: DecisionType,
    pub alternative_chosen: Option<Uuid>,
    pub user_feedback: Option<String>,
}

/// Response for session status
#[derive(Debug, Serialize, Deserialize)]
pub struct SessionStatusResponse {
    pub session: RemediationSession,
    pub completion_percentage: f64,
    pub suggestions_pending: usize,
    pub suggestions_approved: usize,
    pub suggestions_rejected: usize,
    pub fixes_applied: usize,
}

/// Tauri command to generate remediation suggestions
#[tauri::command]
pub fn generate_remediation_suggestions(
    request: GenerateRemediationRequest,
    service: State<'_, RemediationService>,
) -> Result<RemediationResponse, String> {
    let user_preferences = if let Some(user_id) = &request.user_id {
        service.user_preferences.lock().unwrap().get(user_id).cloned()
    } else {
        None
    };
    
    // For now, create a simple session without async generation
    let session_id = uuid::Uuid::new_v4();
    let session = RemediationSession {
        session_id,
        content_id: format!("content_{}", session_id),
        content_type: request.content.content_type.clone(),
        suggested_fixes: vec![], // Would be populated by actual remediation logic
        applied_fixes: vec![],
        user_decisions: vec![],
        status: SessionStatus::Pending,
        created_at: chrono::Utc::now(),
        updated_at: chrono::Utc::now(),
    };
    
    // Count high priority suggestions
    let high_priority_count = session
        .suggested_fixes
        .iter()
        .filter(|s| matches!(s.issue.severity, IssueSeverity::Critical | IssueSeverity::Error))
        .count();
    
    // Check if any fixes can be auto-applied
    let auto_applied_fixes = Vec::new();
    let requires_user_review = session
        .suggested_fixes
        .iter()
        .any(|s| s.requires_approval);
    
    // Auto-apply safe fixes if enabled
    if !requires_user_review || session.suggested_fixes.iter().any(|s| !s.requires_approval) {
        // TODO: Implement auto-application of safe fixes
    }
    
    Ok(RemediationResponse {
        session_id: session.session_id,
        suggestions: session.suggested_fixes.clone(),
        auto_applied_fixes,
        requires_user_review,
        total_suggestions: session.suggested_fixes.len(),
        high_priority_count,
    })
}

/// Tauri command to apply a specific fix
#[tauri::command]
pub fn apply_remediation_fix(
    request: ApplyFixRequest,
    mut content: GeneratedContent,
    service: State<'_, RemediationService>,
) -> Result<(GeneratedContent, AppliedFix), String> {
    // Create a placeholder applied fix for now
    let applied_fix = AppliedFix {
        fix_id: uuid::Uuid::new_v4(),
        suggestion_id: request.suggestion_id,
        applied_at: chrono::Utc::now(),
        before_content: content.content.clone(),
        after_content: content.content.clone(), // No actual changes for now
        user_approved: request.user_approved,
        auto_applied: false,
        success: true,
        error_message: None,
    };
    
    Ok((content, applied_fix))
}

/// Tauri command to record user decision
#[tauri::command]
pub fn record_user_decision(
    request: UserDecisionRequest,
    service: State<'_, RemediationService>,
) -> Result<SessionStatusResponse, String> {
    service
        .manager
        .lock()
        .unwrap()
        .record_user_decision(
            request.session_id,
            request.suggestion_id,
            request.decision,
            request.alternative_chosen,
            request.user_feedback,
        )
        .map_err(|e| e.to_string())?;
    
    get_session_status_internal(request.session_id, &service)
}

/// Tauri command to get session status
#[tauri::command]
pub fn get_remediation_session_status(
    session_id: String,
    service: State<'_, RemediationService>,
) -> Result<SessionStatusResponse, String> {
    let uuid = Uuid::parse_str(&session_id).map_err(|e| e.to_string())?;
    get_session_status_internal(uuid, &service)
}

/// Helper function to get session status
fn get_session_status_internal(
    session_id: Uuid,
    service: &State<'_, RemediationService>,
) -> Result<SessionStatusResponse, String> {
    let manager = service.manager.lock().unwrap();
    let session = manager
        .get_session(session_id)
        .ok_or_else(|| "Session not found".to_string())?;
    
    let total_suggestions = session.suggested_fixes.len();
    let decisions_made = session.user_decisions.len();
    let completion_percentage = if total_suggestions > 0 {
        (decisions_made as f64 / total_suggestions as f64) * 100.0
    } else {
        100.0
    };
    
    let suggestions_approved = session
        .user_decisions
        .iter()
        .filter(|d| matches!(d.decision, DecisionType::Approve | DecisionType::ModifyAndApprove))
        .count();
    
    let suggestions_rejected = session
        .user_decisions
        .iter()
        .filter(|d| matches!(d.decision, DecisionType::Reject))
        .count();
    
    let suggestions_pending = total_suggestions - decisions_made;
    let fixes_applied = session.applied_fixes.len();
    
    Ok(SessionStatusResponse {
        session: session.clone(),
        completion_percentage,
        suggestions_pending,
        suggestions_approved,
        suggestions_rejected,
        fixes_applied,
    })
}

/// Tauri command to get all pending sessions
#[tauri::command]
pub fn get_pending_remediation_sessions(
    service: State<'_, RemediationService>,
) -> Result<Vec<RemediationSession>, String> {
    let manager = service.manager.lock().unwrap();
    Ok(manager.get_pending_sessions().into_iter().cloned().collect())
}

/// Tauri command to get user preferences
#[tauri::command]
pub fn get_user_remediation_preferences(
    user_id: String,
    service: State<'_, RemediationService>,
) -> Result<Option<RemediationPreferences>, String> {
    let preferences = service.user_preferences.lock().unwrap();
    Ok(preferences.get(&user_id).cloned())
}

/// Tauri command to update user preferences
#[tauri::command]
pub fn update_user_remediation_preferences(
    user_id: String,
    preferences: RemediationPreferences,
    service: State<'_, RemediationService>,
) -> Result<(), String> {
    service
        .user_preferences
        .lock()
        .unwrap()
        .insert(user_id, preferences);
    Ok(())
}

/// Tauri command to get remediation statistics
#[tauri::command]
pub fn get_remediation_statistics(
    _user_id: Option<String>,
    service: State<'_, RemediationService>,
) -> Result<RemediationStatistics, String> {
    let manager = service.manager.lock().unwrap();
    let sessions: Vec<&RemediationSession> = manager.get_pending_sessions();
    
    let mut stats = RemediationStatistics {
        total_sessions: sessions.len(),
        completed_sessions: 0,
        pending_sessions: 0,
        total_suggestions: 0,
        applied_fixes: 0,
        user_approval_rate: 0.0,
        most_common_fix_types: HashMap::new(),
        average_completion_time: 0.0,
    };
    
    for session in sessions {
        match session.status {
            SessionStatus::Completed => stats.completed_sessions += 1,
            SessionStatus::Pending | SessionStatus::InProgress => stats.pending_sessions += 1,
            _ => {}
        }
        
        stats.total_suggestions += session.suggested_fixes.len();
        stats.applied_fixes += session.applied_fixes.len();
        
        // Count fix types
        for suggestion in &session.suggested_fixes {
            *stats.most_common_fix_types.entry(suggestion.fix_type.clone()).or_insert(0) += 1;
        }
        
        // Calculate approval rate
        let approvals = session
            .user_decisions
            .iter()
            .filter(|d| matches!(d.decision, DecisionType::Approve | DecisionType::ModifyAndApprove))
            .count();
        
        if !session.user_decisions.is_empty() {
            stats.user_approval_rate += approvals as f64 / session.user_decisions.len() as f64;
        }
    }
    
    if stats.completed_sessions > 0 {
        stats.user_approval_rate /= stats.completed_sessions as f64;
    }
    
    Ok(stats)
}

/// Remediation statistics
#[derive(Debug, Serialize, Deserialize)]
pub struct RemediationStatistics {
    pub total_sessions: usize,
    pub completed_sessions: usize,
    pub pending_sessions: usize,
    pub total_suggestions: usize,
    pub applied_fixes: usize,
    pub user_approval_rate: f64,
    pub most_common_fix_types: HashMap<RemediationFixType, usize>,
    pub average_completion_time: f64,
}

/// Tauri command to cancel a remediation session
#[tauri::command]
pub fn cancel_remediation_session(
    session_id: String,
    _service: State<'_, RemediationService>,
) -> Result<(), String> {
    let _uuid = Uuid::parse_str(&session_id).map_err(|e| e.to_string())?;
    
    // Update session status to cancelled
    // Note: This would require adding a method to RemediationManager
    // For now, we'll just acknowledge the cancellation
    Ok(())
}

/// Tauri command to preview a fix before applying
#[tauri::command]
pub fn preview_remediation_fix(
    session_id: String,
    suggestion_id: String,
    service: State<'_, RemediationService>,
) -> Result<RemediationPreview, String> {
    let session_uuid = Uuid::parse_str(&session_id).map_err(|e| e.to_string())?;
    let suggestion_uuid = Uuid::parse_str(&suggestion_id).map_err(|e| e.to_string())?;
    
    let manager = service.manager.lock().unwrap();
    let session = manager
        .get_session(session_uuid)
        .ok_or_else(|| "Session not found".to_string())?;
    
    let suggestion = session
        .suggested_fixes
        .iter()
        .find(|s| s.suggestion_id == suggestion_uuid)
        .ok_or_else(|| "Suggestion not found".to_string())?;
    
    Ok(suggestion.preview.clone())
}

/// Tauri command to get fix alternatives
#[tauri::command]
pub fn get_fix_alternatives(
    session_id: String,
    suggestion_id: String,
    service: State<'_, RemediationService>,
) -> Result<Vec<AlternativeFix>, String> {
    let session_uuid = Uuid::parse_str(&session_id).map_err(|e| e.to_string())?;
    let suggestion_uuid = Uuid::parse_str(&suggestion_id).map_err(|e| e.to_string())?;
    
    let manager = service.manager.lock().unwrap();
    let session = manager
        .get_session(session_uuid)
        .ok_or_else(|| "Session not found".to_string())?;
    
    let suggestion = session
        .suggested_fixes
        .iter()
        .find(|s| s.suggestion_id == suggestion_uuid)
        .ok_or_else(|| "Suggestion not found".to_string())?;
    
    Ok(suggestion.alternatives.clone())
}

/// Export remediation command names for registration
pub fn get_remediation_command_names() -> Vec<&'static str> {
    vec![
        "generate_remediation_suggestions",
        "apply_remediation_fix", 
        "record_user_decision",
        "get_remediation_session_status",
        "get_pending_remediation_sessions",
        "get_user_remediation_preferences",
        "update_user_remediation_preferences",
        "get_remediation_statistics",
        "cancel_remediation_session",
        "preview_remediation_fix",
        "get_fix_alternatives",
    ]
}