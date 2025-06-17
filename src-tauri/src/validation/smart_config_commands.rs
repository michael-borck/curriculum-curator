use super::smart_config::*;
use super::validators::*;
use crate::content::ContentType;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use tauri::State;

/// Global smart configuration service state
pub struct SmartConfigService {
    manager: Mutex<SmartConfigManager>,
    user_profiles: Mutex<std::collections::HashMap<String, UserProfile>>,
}

/// User profile containing experience level and preferences
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserProfile {
    pub user_id: String,
    pub experience_level: UserExperienceLevel,
    pub preferences: UserPreferences,
    pub usage_stats: UsageStatistics,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub updated_at: chrono::DateTime<chrono::Utc>,
}

/// Usage statistics for adaptive learning
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageStatistics {
    pub total_validations: usize,
    pub content_types_used: std::collections::HashMap<ContentType, usize>,
    pub issues_fixed: usize,
    pub issues_dismissed: usize,
    pub auto_fixes_accepted: usize,
    pub manual_fixes_applied: usize,
}

impl SmartConfigService {
    pub fn new() -> Self {
        Self {
            manager: Mutex::new(SmartConfigManager::new()),
            user_profiles: Mutex::new(std::collections::HashMap::new()),
        }
    }
}

impl Default for UsageStatistics {
    fn default() -> Self {
        Self {
            total_validations: 0,
            content_types_used: std::collections::HashMap::new(),
            issues_fixed: 0,
            issues_dismissed: 0,
            auto_fixes_accepted: 0,
            manual_fixes_applied: 0,
        }
    }
}

/// Request to get smart configuration for a user
#[derive(Debug, Serialize, Deserialize)]
pub struct GetSmartConfigRequest {
    pub user_id: Option<String>,
    pub content_type: ContentType,
    pub experience_level: Option<UserExperienceLevel>,
}

/// Response containing smart configuration
#[derive(Debug, Serialize, Deserialize)]
pub struct SmartConfigResponse {
    pub config: ValidationConfig,
    pub preset: ValidationPreset,
    pub recommendations: SmartRecommendations,
    pub applied_customizations: Vec<String>,
}

/// Request to update user experience level
#[derive(Debug, Serialize, Deserialize)]
pub struct UpdateExperienceLevelRequest {
    pub user_id: String,
    pub experience_level: UserExperienceLevel,
}

/// Request to record user validation decision for learning
#[derive(Debug, Serialize, Deserialize)]
pub struct RecordDecisionRequest {
    pub user_id: Option<String>,
    pub issue_type: IssueType,
    pub user_action: UserAction,
    pub content_type: ContentType,
}

/// Request to create custom configuration
#[derive(Debug, Serialize, Deserialize)]
pub struct CreateCustomConfigRequest {
    pub user_id: String,
    pub base_level: UserExperienceLevel,
    pub customizations: ConfigCustomizations,
    pub name: Option<String>,
}

/// Response containing available experience levels
#[derive(Debug, Serialize, Deserialize)]
pub struct ExperienceLevelsResponse {
    pub levels: Vec<ExperienceLevelInfo>,
}

/// Information about an experience level
#[derive(Debug, Serialize, Deserialize)]
pub struct ExperienceLevelInfo {
    pub level: UserExperienceLevel,
    pub name: String,
    pub description: String,
    pub features: Vec<String>,
    pub recommended_for: Vec<String>,
}

/// Tauri command to get smart configuration for a user and content type
#[tauri::command]
pub fn get_smart_config(
    request: GetSmartConfigRequest,
    service: State<'_, SmartConfigService>,
) -> Result<SmartConfigResponse, String> {
    let manager = service.manager.lock().unwrap();
    let profiles = service.user_profiles.lock().unwrap();
    
    // Determine experience level
    let experience_level = if let Some(level) = request.experience_level {
        level
    } else if let Some(user_id) = &request.user_id {
        profiles.get(user_id)
            .map(|p| p.experience_level.clone())
            .unwrap_or(UserExperienceLevel::Intermediate)
    } else {
        UserExperienceLevel::Intermediate // Default for anonymous users
    };
    
    // Get base configuration for the experience level
    let preset = manager.get_preset_for_level(&experience_level)
        .map_err(|e| e.to_string())?;
    
    // Get user preferences if available
    let user_preferences = request.user_id
        .as_ref()
        .and_then(|user_id| profiles.get(user_id))
        .map(|profile| &profile.preferences);
    
    // Adapt configuration for content type and user preferences
    let config = manager.adapt_config_for_content(
        preset.config.clone(),
        &request.content_type,
        user_preferences,
    );
    
    // Get smart recommendations
    let recommendations = manager.get_smart_recommendations(&request.content_type);
    
    let applied_customizations = vec![
        format!("Optimized for {:?} content", request.content_type),
        format!("Configured for {:?} experience level", experience_level),
    ];
    
    Ok(SmartConfigResponse {
        config,
        preset,
        recommendations,
        applied_customizations,
    })
}

/// Tauri command to get all available experience levels
#[tauri::command]
pub fn get_experience_levels() -> Result<ExperienceLevelsResponse, String> {
    let levels = SmartConfigManager::get_experience_levels()
        .into_iter()
        .map(|(level, description)| {
            let (features, recommended_for) = match level {
                UserExperienceLevel::Beginner => (
                    vec![
                        "Auto-fix enabled".to_string(),
                        "Contextual help".to_string(),
                        "Learning tips".to_string(),
                        "Progressive disclosure".to_string(),
                    ],
                    vec![
                        "First-time content creators".to_string(),
                        "Users new to educational content".to_string(),
                        "Those who want guided validation".to_string(),
                    ]
                ),
                UserExperienceLevel::Intermediate => (
                    vec![
                        "Balanced validation".to_string(),
                        "Detailed reports".to_string(),
                        "Real-time feedback".to_string(),
                        "Confidence levels".to_string(),
                    ],
                    vec![
                        "Teachers with some content creation experience".to_string(),
                        "Users familiar with educational best practices".to_string(),
                        "Those who want comprehensive but not overwhelming feedback".to_string(),
                    ]
                ),
                UserExperienceLevel::Advanced => (
                    vec![
                        "Comprehensive validation".to_string(),
                        "Technical details".to_string(),
                        "All validation categories".to_string(),
                        "Detailed analysis".to_string(),
                    ],
                    vec![
                        "Experienced educators".to_string(),
                        "Instructional designers".to_string(),
                        "Users who want thorough content analysis".to_string(),
                    ]
                ),
                UserExperienceLevel::Expert => (
                    vec![
                        "Minimal interference".to_string(),
                        "Maximum configurability".to_string(),
                        "Performance optimization".to_string(),
                        "Critical issues only".to_string(),
                    ],
                    vec![
                        "Curriculum specialists".to_string(),
                        "Content creation professionals".to_string(),
                        "Users who prefer full control".to_string(),
                    ]
                ),
                UserExperienceLevel::Custom => (
                    vec![
                        "Fully customizable".to_string(),
                        "User-defined rules".to_string(),
                        "Flexible validation".to_string(),
                    ],
                    vec![
                        "Users with specific requirements".to_string(),
                        "Organizations with custom standards".to_string(),
                    ]
                ),
            };
            
            ExperienceLevelInfo {
                level: level.clone(),
                name: format!("{:?}", level),
                description: description.to_string(),
                features,
                recommended_for,
            }
        })
        .collect();
    
    Ok(ExperienceLevelsResponse { levels })
}

/// Tauri command to update user's experience level
#[tauri::command]
pub fn update_user_experience_level(
    request: UpdateExperienceLevelRequest,
    service: State<'_, SmartConfigService>,
) -> Result<(), String> {
    let mut profiles = service.user_profiles.lock().unwrap();
    
    if let Some(profile) = profiles.get_mut(&request.user_id) {
        profile.experience_level = request.experience_level;
        profile.updated_at = chrono::Utc::now();
    } else {
        // Create new profile
        let profile = UserProfile {
            user_id: request.user_id.clone(),
            experience_level: request.experience_level,
            preferences: UserPreferences::default(),
            usage_stats: UsageStatistics::default(),
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        };
        profiles.insert(request.user_id, profile);
    }
    
    Ok(())
}

/// Tauri command to record user decision for adaptive learning
#[tauri::command]
pub fn record_validation_decision(
    request: RecordDecisionRequest,
    service: State<'_, SmartConfigService>,
) -> Result<(), String> {
    let mut manager = service.manager.lock().unwrap();
    let mut profiles = service.user_profiles.lock().unwrap();
    
    // Update the smart config manager
    manager.learn_from_user_decision(
        &request.issue_type,
        request.user_action.clone(),
        &request.content_type,
    );
    
    // Update user statistics if user ID provided
    if let Some(user_id) = &request.user_id {
        if let Some(profile) = profiles.get_mut(user_id) {
            match request.user_action {
                UserAction::Dismissed => profile.usage_stats.issues_dismissed += 1,
                UserAction::AcceptedFix => profile.usage_stats.auto_fixes_accepted += 1,
                UserAction::RejectedFix => {}, // No specific counter for this
                UserAction::ModifiedSuggestion => profile.usage_stats.manual_fixes_applied += 1,
            }
            profile.updated_at = chrono::Utc::now();
        }
    }
    
    Ok(())
}

/// Tauri command to create custom configuration
#[tauri::command]
pub fn create_custom_config(
    request: CreateCustomConfigRequest,
    service: State<'_, SmartConfigService>,
) -> Result<ValidationConfig, String> {
    let manager = service.manager.lock().unwrap();
    
    let config = manager.create_custom_config(
        &request.base_level,
        request.customizations,
    ).map_err(|e| e.to_string())?;
    
    // Optionally save the custom config to user profile
    // This would require extending the UserProfile structure
    
    Ok(config)
}

/// Tauri command to get user's current profile
#[tauri::command]
pub fn get_user_profile(
    user_id: String,
    service: State<'_, SmartConfigService>,
) -> Result<Option<UserProfile>, String> {
    let profiles = service.user_profiles.lock().unwrap();
    Ok(profiles.get(&user_id).cloned())
}

/// Tauri command to export user's configuration
#[tauri::command]
pub fn export_user_config(
    user_id: String,
    service: State<'_, SmartConfigService>,
) -> Result<String, String> {
    let manager = service.manager.lock().unwrap();
    manager.export_user_config().map_err(|e| e.to_string())
}

/// Tauri command to import user's configuration
#[tauri::command]
pub fn import_user_config(
    user_id: String,
    config_json: String,
    service: State<'_, SmartConfigService>,
) -> Result<(), String> {
    let mut manager = service.manager.lock().unwrap();
    manager.import_user_config(&config_json).map_err(|e| e.to_string())
}

/// Tauri command to get validation recommendations for content type
#[tauri::command]
pub fn get_validation_recommendations(
    content_type: ContentType,
    user_id: Option<String>,
    service: State<'_, SmartConfigService>,
) -> Result<SmartRecommendations, String> {
    let manager = service.manager.lock().unwrap();
    let recommendations = manager.get_smart_recommendations(&content_type);
    Ok(recommendations)
}

/// Tauri command to reset user's adaptive settings
#[tauri::command]
pub fn reset_user_adaptive_settings(
    user_id: String,
    service: State<'_, SmartConfigService>,
) -> Result<(), String> {
    let mut profiles = service.user_profiles.lock().unwrap();
    
    if let Some(profile) = profiles.get_mut(&user_id) {
        profile.preferences = UserPreferences::default();
        profile.usage_stats = UsageStatistics::default();
        profile.updated_at = chrono::Utc::now();
    }
    
    Ok(())
}

/// Tauri command to get usage statistics for a user
#[tauri::command]
pub fn get_user_usage_stats(
    user_id: String,
    service: State<'_, SmartConfigService>,
) -> Result<Option<UsageStatistics>, String> {
    let profiles = service.user_profiles.lock().unwrap();
    Ok(profiles.get(&user_id).map(|p| p.usage_stats.clone()))
}

/// Tauri command to update usage statistics
#[tauri::command]
pub fn update_usage_stats(
    user_id: String,
    content_type: ContentType,
    validation_completed: bool,
    service: State<'_, SmartConfigService>,
) -> Result<(), String> {
    let mut profiles = service.user_profiles.lock().unwrap();
    
    if let Some(profile) = profiles.get_mut(&user_id) {
        if validation_completed {
            profile.usage_stats.total_validations += 1;
            *profile.usage_stats.content_types_used.entry(content_type).or_insert(0) += 1;
        }
        profile.updated_at = chrono::Utc::now();
    }
    
    Ok(())
}

/// Export smart configuration command names for registration
pub fn get_smart_config_command_names() -> Vec<&'static str> {
    vec![
        "get_smart_config",
        "get_experience_levels",
        "update_user_experience_level",
        "record_validation_decision",
        "create_custom_config",
        "get_user_profile",
        "export_user_config",
        "import_user_config",
        "get_validation_recommendations",
        "reset_user_adaptive_settings",
        "get_user_usage_stats",
        "update_usage_stats",
    ]
}