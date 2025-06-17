use super::validators::*;
use super::built_in::*;
use crate::content::ContentType;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Smart configuration manager for validation with intelligent defaults
#[derive(Debug, Clone)]
pub struct SmartConfigManager {
    presets: HashMap<UserExperienceLevel, ValidationPreset>,
    adaptive_settings: AdaptiveSettings,
}

/// User experience levels for determining appropriate validation strictness
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum UserExperienceLevel {
    Beginner,      // New to content creation, needs guidance
    Intermediate,  // Some experience, wants balanced validation
    Advanced,      // Experienced, wants detailed feedback
    Expert,        // Very experienced, minimal interference
    Custom,        // User-defined configuration
}

/// Adaptive settings that learn from user behavior
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AdaptiveSettings {
    pub learning_enabled: bool,
    pub user_preferences: UserPreferences,
    pub auto_adjust_severity: bool,
    pub track_user_decisions: bool,
}

/// User preferences learned from interaction patterns
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserPreferences {
    pub preferred_validators: Vec<String>,
    pub dismissed_issue_types: Vec<IssueType>,
    pub severity_adjustments: HashMap<IssueType, IssueSeverity>,
    pub auto_fix_preferences: HashMap<String, bool>,
    pub content_type_preferences: HashMap<ContentType, ContentTypePreferences>,
}

/// Content-type specific user preferences
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentTypePreferences {
    pub strictness_level: f64, // 0.0 (lenient) to 1.0 (strict)
    pub focus_areas: Vec<ValidationFocus>,
    pub auto_apply_safe_fixes: bool,
    pub require_approval_threshold: IssueSeverity,
}

/// Areas of validation focus
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ValidationFocus {
    Readability,
    Structure,
    Completeness,
    Grammar,
    Alignment,
    Accessibility,
    PedagogicalBestPractices,
}

/// Validation preset containing pre-configured settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationPreset {
    pub name: String,
    pub description: String,
    pub config: ValidationConfig,
    pub enabled_features: Vec<ValidationFeature>,
    pub ui_settings: UISettings,
}

/// Validation features that can be enabled/disabled
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ValidationFeature {
    RealTimeValidation,
    AutoFix,
    DetailedReports,
    ProgressiveDisclosure,
    ContextualHelp,
    ValidationTips,
    PerformanceOptimization,
}

/// UI-specific settings for the validation experience
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UISettings {
    pub show_confidence_levels: bool,
    pub show_technical_details: bool,
    pub group_similar_issues: bool,
    pub highlight_critical_issues: bool,
    pub show_learning_tips: bool,
    pub notification_level: NotificationLevel,
}

/// Notification intensity levels
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum NotificationLevel {
    Minimal,    // Only critical issues
    Standard,   // Standard notifications
    Detailed,   // All validation feedback
    Verbose,    // Include tips and suggestions
}

impl Default for UserPreferences {
    fn default() -> Self {
        Self {
            preferred_validators: vec![
                "structure".to_string(),
                "readability".to_string(),
                "completeness".to_string(),
            ],
            dismissed_issue_types: vec![],
            severity_adjustments: HashMap::new(),
            auto_fix_preferences: HashMap::new(),
            content_type_preferences: HashMap::new(),
        }
    }
}

impl Default for AdaptiveSettings {
    fn default() -> Self {
        Self {
            learning_enabled: true,
            user_preferences: UserPreferences::default(),
            auto_adjust_severity: true,
            track_user_decisions: true,
        }
    }
}

impl SmartConfigManager {
    /// Create a new smart configuration manager with default presets
    pub fn new() -> Self {
        let mut manager = Self {
            presets: HashMap::new(),
            adaptive_settings: AdaptiveSettings::default(),
        };
        
        manager.initialize_presets();
        manager
    }
    
    /// Initialize built-in validation presets for different user levels
    fn initialize_presets(&mut self) {
        // Beginner preset - focused on essential validation with guidance
        let beginner_preset = ValidationPreset {
            name: "Beginner".to_string(),
            description: "Essential validation with helpful guidance for new content creators".to_string(),
            config: self.create_beginner_config(),
            enabled_features: vec![
                ValidationFeature::RealTimeValidation,
                ValidationFeature::AutoFix,
                ValidationFeature::ContextualHelp,
                ValidationFeature::ValidationTips,
                ValidationFeature::ProgressiveDisclosure,
            ],
            ui_settings: UISettings {
                show_confidence_levels: false,
                show_technical_details: false,
                group_similar_issues: true,
                highlight_critical_issues: true,
                show_learning_tips: true,
                notification_level: NotificationLevel::Standard,
            },
        };
        
        // Intermediate preset - balanced validation with moderate detail
        let intermediate_preset = ValidationPreset {
            name: "Intermediate".to_string(),
            description: "Balanced validation with detailed feedback for experienced users".to_string(),
            config: self.create_intermediate_config(),
            enabled_features: vec![
                ValidationFeature::RealTimeValidation,
                ValidationFeature::AutoFix,
                ValidationFeature::DetailedReports,
                ValidationFeature::ContextualHelp,
            ],
            ui_settings: UISettings {
                show_confidence_levels: true,
                show_technical_details: false,
                group_similar_issues: true,
                highlight_critical_issues: true,
                show_learning_tips: false,
                notification_level: NotificationLevel::Standard,
            },
        };
        
        // Advanced preset - comprehensive validation with full details
        let advanced_preset = ValidationPreset {
            name: "Advanced".to_string(),
            description: "Comprehensive validation with detailed analysis and technical insights".to_string(),
            config: self.create_advanced_config(),
            enabled_features: vec![
                ValidationFeature::RealTimeValidation,
                ValidationFeature::AutoFix,
                ValidationFeature::DetailedReports,
                ValidationFeature::ContextualHelp,
                ValidationFeature::ValidationTips,
            ],
            ui_settings: UISettings {
                show_confidence_levels: true,
                show_technical_details: true,
                group_similar_issues: false,
                highlight_critical_issues: true,
                show_learning_tips: false,
                notification_level: NotificationLevel::Detailed,
            },
        };
        
        // Expert preset - minimal interference, maximum control
        let expert_preset = ValidationPreset {
            name: "Expert".to_string(),
            description: "Minimal validation interference with maximum configurability for experts".to_string(),
            config: self.create_expert_config(),
            enabled_features: vec![
                ValidationFeature::DetailedReports,
                ValidationFeature::PerformanceOptimization,
            ],
            ui_settings: UISettings {
                show_confidence_levels: true,
                show_technical_details: true,
                group_similar_issues: false,
                highlight_critical_issues: false,
                show_learning_tips: false,
                notification_level: NotificationLevel::Minimal,
            },
        };
        
        self.presets.insert(UserExperienceLevel::Beginner, beginner_preset);
        self.presets.insert(UserExperienceLevel::Intermediate, intermediate_preset);
        self.presets.insert(UserExperienceLevel::Advanced, advanced_preset);
        self.presets.insert(UserExperienceLevel::Expert, expert_preset);
    }
    
    /// Create a beginner-friendly validation configuration
    fn create_beginner_config(&self) -> ValidationConfig {
        let mut config = ValidationConfig::default();
        
        // Enable only essential validators
        config.enabled_validators = vec![
            "structure".to_string(),
            "readability".to_string(),
            "completeness".to_string(),
        ];
        
        // Use lenient thresholds
        config.severity_threshold = IssueSeverity::Warning;
        config.auto_fix_enabled = true;
        config.readability_threshold = 8.0; // Easier reading level
        
        // Add readability config optimized for beginners
        let readability_config = ReadabilityConfig {
            complexity_level: ComplexityLevel::MiddleSchool,
            min_flesch_score: 70.0, // Very readable
            max_sentence_length: 15,
            max_paragraph_length: 80,
            max_syllables_per_word: 1.4,
            target_grade_level: Some(8.0),
            age_specific_thresholds: AgeSpecificThresholds::default(),
        };
        
        config.plugin_configs.insert(
            "readability".to_string(),
            serde_json::to_value(readability_config).unwrap()
        );
        
        config
    }
    
    /// Create an intermediate validation configuration
    fn create_intermediate_config(&self) -> ValidationConfig {
        let mut config = ValidationConfig::default();
        
        config.enabled_validators = vec![
            "structure".to_string(),
            "readability".to_string(),
            "completeness".to_string(),
            "grammar".to_string(),
        ];
        
        config.severity_threshold = IssueSeverity::Info;
        config.auto_fix_enabled = true;
        config.readability_threshold = 6.0;
        
        let readability_config = ReadabilityConfig {
            complexity_level: ComplexityLevel::HighSchool,
            min_flesch_score: 60.0,
            max_sentence_length: 20,
            max_paragraph_length: 120,
            max_syllables_per_word: 1.6,
            target_grade_level: Some(10.0),
            age_specific_thresholds: AgeSpecificThresholds::default(),
        };
        
        config.plugin_configs.insert(
            "readability".to_string(),
            serde_json::to_value(readability_config).unwrap()
        );
        
        config
    }
    
    /// Create an advanced validation configuration
    fn create_advanced_config(&self) -> ValidationConfig {
        let mut config = ValidationConfig::default();
        
        config.enabled_validators = vec![
            "structure".to_string(),
            "readability".to_string(),
            "completeness".to_string(),
            "grammar".to_string(),
            "content_alignment".to_string(),
        ];
        
        config.severity_threshold = IssueSeverity::Info;
        config.auto_fix_enabled = false; // Let advanced users decide
        config.readability_threshold = 5.0;
        
        let readability_config = ReadabilityConfig {
            complexity_level: ComplexityLevel::College,
            min_flesch_score: 50.0,
            max_sentence_length: 25,
            max_paragraph_length: 150,
            max_syllables_per_word: 1.8,
            target_grade_level: Some(12.0),
            age_specific_thresholds: AgeSpecificThresholds::default(),
        };
        
        config.plugin_configs.insert(
            "readability".to_string(),
            serde_json::to_value(readability_config).unwrap()
        );
        
        config
    }
    
    /// Create an expert validation configuration
    fn create_expert_config(&self) -> ValidationConfig {
        let mut config = ValidationConfig::default();
        
        // Enable all validators but with minimal interference
        config.enabled_validators = vec![
            "structure".to_string(),
            "readability".to_string(),
            "completeness".to_string(),
            "grammar".to_string(),
            "content_alignment".to_string(),
        ];
        
        config.severity_threshold = IssueSeverity::Error; // Only show important issues
        config.auto_fix_enabled = false;
        config.readability_threshold = 3.0; // More complex content allowed
        
        let readability_config = ReadabilityConfig {
            complexity_level: ComplexityLevel::Professional,
            min_flesch_score: 30.0,
            max_sentence_length: 35,
            max_paragraph_length: 200,
            max_syllables_per_word: 2.2,
            target_grade_level: Some(16.0),
            age_specific_thresholds: AgeSpecificThresholds::default(),
        };
        
        config.plugin_configs.insert(
            "readability".to_string(),
            serde_json::to_value(readability_config).unwrap()
        );
        
        config
    }
    
    /// Get validation configuration for a specific user experience level
    pub fn get_config_for_level(&self, level: &UserExperienceLevel) -> Result<ValidationConfig> {
        let preset = self.presets.get(level)
            .ok_or_else(|| anyhow::anyhow!("No preset found for experience level: {:?}", level))?;
        Ok(preset.config.clone())
    }
    
    /// Get validation preset for a specific user experience level
    pub fn get_preset_for_level(&self, level: &UserExperienceLevel) -> Result<ValidationPreset> {
        self.presets.get(level)
            .cloned()
            .ok_or_else(|| anyhow::anyhow!("No preset found for experience level: {:?}", level))
    }
    
    /// Adapt configuration based on content type and user preferences
    pub fn adapt_config_for_content(
        &self,
        base_config: ValidationConfig,
        content_type: &ContentType,
        user_preferences: Option<&UserPreferences>,
    ) -> ValidationConfig {
        let mut config = base_config;
        
        // Apply content-type specific adjustments
        match content_type {
            ContentType::Slides => {
                // Slides need clear, concise content
                if let Some(readability_config) = config.plugin_configs.get_mut("readability") {
                    if let Ok(mut rc) = serde_json::from_value::<ReadabilityConfig>(readability_config.clone()) {
                        rc.max_sentence_length = rc.max_sentence_length.min(18);
                        rc.max_paragraph_length = rc.max_paragraph_length.min(100);
                        *readability_config = serde_json::to_value(rc).unwrap();
                    }
                }
            },
            ContentType::Quiz => {
                // Quizzes need very clear questions
                config.enabled_validators.retain(|v| v != "content_alignment");
                if let Some(readability_config) = config.plugin_configs.get_mut("readability") {
                    if let Ok(mut rc) = serde_json::from_value::<ReadabilityConfig>(readability_config.clone()) {
                        rc.min_flesch_score = rc.min_flesch_score.max(70.0);
                        rc.max_sentence_length = rc.max_sentence_length.min(15);
                        *readability_config = serde_json::to_value(rc).unwrap();
                    }
                }
            },
            ContentType::InstructorNotes => {
                // Instructor notes can be more complex
                if let Some(readability_config) = config.plugin_configs.get_mut("readability") {
                    if let Ok(mut rc) = serde_json::from_value::<ReadabilityConfig>(readability_config.clone()) {
                        rc.complexity_level = ComplexityLevel::Professional;
                        rc.min_flesch_score = rc.min_flesch_score.min(40.0);
                        *readability_config = serde_json::to_value(rc).unwrap();
                    }
                }
            },
            _ => {} // Use default settings for other types
        }
        
        // Apply user preferences if provided
        if let Some(prefs) = user_preferences {
            // Adjust enabled validators based on preferences
            config.enabled_validators.retain(|v| prefs.preferred_validators.contains(v));
            
            // Apply severity adjustments
            // Note: This would require extending ValidationConfig to support per-type severity
            
            // Apply content-type specific preferences
            if let Some(ct_prefs) = prefs.content_type_preferences.get(content_type) {
                // Adjust auto-fix settings
                config.auto_fix_enabled = ct_prefs.auto_apply_safe_fixes;
                
                // Adjust severity threshold based on strictness level
                let adjusted_threshold = match ct_prefs.strictness_level {
                    level if level < 0.3 => IssueSeverity::Error,
                    level if level < 0.7 => IssueSeverity::Warning,
                    _ => IssueSeverity::Info,
                };
                config.severity_threshold = adjusted_threshold;
            }
        }
        
        config
    }
    
    /// Learn from user decisions to improve future configurations
    pub fn learn_from_user_decision(
        &mut self,
        issue_type: &IssueType,
        user_action: UserAction,
        content_type: &ContentType,
    ) {
        if !self.adaptive_settings.learning_enabled {
            return;
        }
        
        let prefs = &mut self.adaptive_settings.user_preferences;
        
        match user_action {
            UserAction::Dismissed => {
                if !prefs.dismissed_issue_types.contains(issue_type) {
                    prefs.dismissed_issue_types.push(issue_type.clone());
                }
            },
            UserAction::AcceptedFix => {
                // This suggests the user finds this type of validation valuable
                // Could increase priority for this issue type
            },
            UserAction::RejectedFix => {
                // This suggests the validation might be too strict
                // Could adjust severity or disable auto-fix for this type
            },
            UserAction::ModifiedSuggestion => {
                // User engaged with the suggestion but made changes
                // This is positive engagement
            },
        }
    }
    
    /// Get smart configuration recommendations based on user history
    pub fn get_smart_recommendations(&self, content_type: &ContentType) -> SmartRecommendations {
        let prefs = &self.adaptive_settings.user_preferences;
        
        let mut recommendations = SmartRecommendations {
            suggested_validators: prefs.preferred_validators.clone(),
            suggested_features: vec![],
            ui_customizations: vec![],
            configuration_tips: vec![],
        };
        
        // Analyze user patterns and suggest improvements
        if prefs.dismissed_issue_types.len() > 3 {
            recommendations.configuration_tips.push(
                "Consider adjusting validation strictness - you've dismissed several issue types recently.".to_string()
            );
        }
        
        // Content-type specific recommendations
        match content_type {
            ContentType::Slides => {
                recommendations.suggested_features.push(ValidationFeature::RealTimeValidation);
                recommendations.configuration_tips.push(
                    "For slides, focus on readability and structure validation for better presentations.".to_string()
                );
            },
            ContentType::Quiz => {
                recommendations.suggested_validators.push("grammar".to_string());
                recommendations.configuration_tips.push(
                    "Quiz questions benefit from grammar and clarity validation.".to_string()
                );
            },
            _ => {}
        }
        
        recommendations
    }
    
    /// Create a custom configuration based on user's specific needs
    pub fn create_custom_config(
        &self,
        base_level: &UserExperienceLevel,
        customizations: ConfigCustomizations,
    ) -> Result<ValidationConfig> {
        let mut config = self.get_config_for_level(base_level)?;
        
        // Apply customizations
        if let Some(validators) = customizations.enabled_validators {
            config.enabled_validators = validators;
        }
        
        if let Some(threshold) = customizations.severity_threshold {
            config.severity_threshold = threshold;
        }
        
        if let Some(auto_fix) = customizations.auto_fix_enabled {
            config.auto_fix_enabled = auto_fix;
        }
        
        if let Some(readability_threshold) = customizations.readability_threshold {
            config.readability_threshold = readability_threshold;
        }
        
        // Apply plugin configurations
        for (plugin, plugin_config) in customizations.plugin_configs {
            config.plugin_configs.insert(plugin, plugin_config);
        }
        
        Ok(config)
    }
    
    /// Export user's configuration for backup or sharing
    pub fn export_user_config(&self) -> Result<String> {
        serde_json::to_string_pretty(&self.adaptive_settings.user_preferences)
            .map_err(|e| anyhow::anyhow!("Failed to export config: {}", e))
    }
    
    /// Import user's configuration from backup
    pub fn import_user_config(&mut self, config_json: &str) -> Result<()> {
        let preferences: UserPreferences = serde_json::from_str(config_json)
            .map_err(|e| anyhow::anyhow!("Failed to import config: {}", e))?;
        
        self.adaptive_settings.user_preferences = preferences;
        Ok(())
    }
    
    /// Get all available experience levels with descriptions
    pub fn get_experience_levels() -> Vec<(UserExperienceLevel, &'static str)> {
        vec![
            (UserExperienceLevel::Beginner, "New to content creation, needs guidance and simple validation"),
            (UserExperienceLevel::Intermediate, "Some experience, wants balanced validation with helpful feedback"),
            (UserExperienceLevel::Advanced, "Experienced user, wants comprehensive validation and detailed analysis"),
            (UserExperienceLevel::Expert, "Very experienced, prefers minimal interference and maximum control"),
            (UserExperienceLevel::Custom, "Fully customizable validation settings"),
        ]
    }
}

/// User actions for learning from behavior
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum UserAction {
    Dismissed,
    AcceptedFix,
    RejectedFix,
    ModifiedSuggestion,
}

/// Smart recommendations based on user behavior analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SmartRecommendations {
    pub suggested_validators: Vec<String>,
    pub suggested_features: Vec<ValidationFeature>,
    pub ui_customizations: Vec<String>,
    pub configuration_tips: Vec<String>,
}

/// Configuration customizations for creating custom configs
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfigCustomizations {
    pub enabled_validators: Option<Vec<String>>,
    pub severity_threshold: Option<IssueSeverity>,
    pub auto_fix_enabled: Option<bool>,
    pub readability_threshold: Option<f64>,
    pub plugin_configs: HashMap<String, serde_json::Value>,
}

impl Default for SmartConfigManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_smart_config_creation() {
        let manager = SmartConfigManager::new();
        
        // Test that all experience levels have presets
        for level in [UserExperienceLevel::Beginner, UserExperienceLevel::Intermediate, 
                     UserExperienceLevel::Advanced, UserExperienceLevel::Expert] {
            let config = manager.get_config_for_level(&level).unwrap();
            assert!(!config.enabled_validators.is_empty());
        }
    }
    
    #[test]
    fn test_content_type_adaptation() {
        let manager = SmartConfigManager::new();
        let base_config = manager.get_config_for_level(&UserExperienceLevel::Intermediate).unwrap();
        
        let slides_config = manager.adapt_config_for_content(
            base_config.clone(),
            &ContentType::Slides,
            None
        );
        
        let quiz_config = manager.adapt_config_for_content(
            base_config,
            &ContentType::Quiz,
            None
        );
        
        // Quiz config should be more strict about readability
        assert_ne!(slides_config.plugin_configs, quiz_config.plugin_configs);
    }
    
    #[test]
    fn test_learning_from_user_decisions() {
        let mut manager = SmartConfigManager::new();
        
        manager.learn_from_user_decision(
            &IssueType::Grammar,
            UserAction::Dismissed,
            &ContentType::Slides
        );
        
        let prefs = &manager.adaptive_settings.user_preferences;
        assert!(prefs.dismissed_issue_types.contains(&IssueType::Grammar));
    }
    
    #[test]
    fn test_config_export_import() {
        let manager = SmartConfigManager::new();
        
        let exported = manager.export_user_config().unwrap();
        let mut new_manager = SmartConfigManager::new();
        
        new_manager.import_user_config(&exported).unwrap();
        
        assert_eq!(
            manager.adaptive_settings.user_preferences.preferred_validators,
            new_manager.adaptive_settings.user_preferences.preferred_validators
        );
    }
}