use serde::{Deserialize, Serialize};
use anyhow::Result;
use crate::content::{GeneratedContent, ContentType};
use std::collections::HashMap;

/// Core validation result containing all information about a validation check
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationResult {
    pub validator_name: String,
    pub passed: bool,
    pub score: f64,
    pub issues: Vec<ValidationIssue>,
    pub suggestions: Vec<String>,
    pub metadata: ValidationMetadata,
}

/// Individual validation issue with context and remediation hints
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationIssue {
    pub severity: IssueSeverity,
    pub issue_type: IssueType,
    pub message: String,
    pub location: Option<ContentLocation>,
    pub remediation_hint: Option<String>,
    pub auto_fixable: bool,
}

/// Severity levels for validation issues
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum IssueSeverity {
    Critical,  // Blocks export/use
    Error,     // Significant quality issue
    Warning,   // Quality concern
    Info,      // Informational suggestion
}

/// Categories of validation issues for filtering and prioritization
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum IssueType {
    // Content Quality
    Structure,
    Readability,
    Completeness,
    Consistency,
    
    // Educational Standards
    LearningObjectives,
    AgeAppropriateness,
    PedagogicalAlignment,
    
    // Language and Style
    Grammar,
    Spelling,
    Tone,
    Bias,
    
    // Safety and Accuracy
    ContentSafety,
    Factuality,
    References,
    
    // Format and Technical
    Format,
    Metadata,
    Export,
}

/// Location information for issues within content
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentLocation {
    pub section: Option<String>,
    pub line: Option<usize>,
    pub character_range: Option<(usize, usize)>,
    pub slide_number: Option<usize>,
    pub question_number: Option<usize>,
}

/// Metadata about the validation process and results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationMetadata {
    pub execution_time_ms: u64,
    pub content_analyzed: ContentAnalysis,
    pub validator_version: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

/// Analysis metadata about the content that was validated
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentAnalysis {
    pub word_count: usize,
    pub section_count: usize,
    pub slide_count: Option<usize>,
    pub question_count: Option<usize>,
    pub reading_level: Option<f64>,
}

/// Comprehensive validation configuration supporting plugin-specific settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationConfig {
    // Global settings
    pub enabled_validators: Vec<String>,
    pub severity_threshold: IssueSeverity,
    pub auto_fix_enabled: bool,
    pub content_type_specific: HashMap<ContentType, ContentTypeValidationConfig>,
    
    // Legacy settings (maintained for compatibility)
    pub readability_threshold: f64,
    pub max_word_count: Option<usize>,
    pub required_structure_elements: Vec<String>,
    
    // Plugin-specific configurations
    pub plugin_configs: HashMap<String, serde_json::Value>,
}

/// Content-type specific validation rules
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentTypeValidationConfig {
    pub required_sections: Vec<String>,
    pub min_word_count: Option<usize>,
    pub max_word_count: Option<usize>,
    pub required_elements: Vec<String>,
    pub educational_standards: Vec<String>,
}

impl Default for ValidationConfig {
    fn default() -> Self {
        let mut content_type_specific = HashMap::new();
        
        // Default configurations for each content type
        content_type_specific.insert(ContentType::Slides, ContentTypeValidationConfig {
            required_sections: vec!["title".to_string(), "content".to_string()],
            min_word_count: Some(50),
            max_word_count: Some(5000),
            required_elements: vec!["learning_objectives".to_string()],
            educational_standards: vec!["clear_structure".to_string(), "appropriate_pacing".to_string()],
        });
        
        content_type_specific.insert(ContentType::Quiz, ContentTypeValidationConfig {
            required_sections: vec!["questions".to_string(), "answers".to_string()],
            min_word_count: Some(20),
            max_word_count: Some(2000),
            required_elements: vec!["question_count".to_string(), "answer_key".to_string()],
            educational_standards: vec!["clear_questions".to_string(), "appropriate_difficulty".to_string()],
        });
        
        content_type_specific.insert(ContentType::Worksheet, ContentTypeValidationConfig {
            required_sections: vec!["instructions".to_string(), "exercises".to_string()],
            min_word_count: Some(100),
            max_word_count: Some(3000),
            required_elements: vec!["clear_instructions".to_string()],
            educational_standards: vec!["scaffolded_learning".to_string(), "practice_opportunities".to_string()],
        });
        
        content_type_specific.insert(ContentType::InstructorNotes, ContentTypeValidationConfig {
            required_sections: vec!["overview".to_string(), "key_points".to_string()],
            min_word_count: Some(50),
            max_word_count: Some(2000),
            required_elements: vec!["timing_guidance".to_string()],
            educational_standards: vec!["teaching_tips".to_string(), "common_misconceptions".to_string()],
        });
        
        content_type_specific.insert(ContentType::ActivityGuide, ContentTypeValidationConfig {
            required_sections: vec!["overview".to_string(), "steps".to_string(), "materials".to_string()],
            min_word_count: Some(100),
            max_word_count: Some(2500),
            required_elements: vec!["time_estimate".to_string(), "materials_list".to_string()],
            educational_standards: vec!["clear_steps".to_string(), "engagement_opportunities".to_string()],
        });

        Self {
            enabled_validators: vec![
                "structure".to_string(),
                "readability".to_string(),
                "completeness".to_string(),
            ],
            severity_threshold: IssueSeverity::Warning,
            auto_fix_enabled: false,
            content_type_specific,
            readability_threshold: 7.0,
            max_word_count: None,
            required_structure_elements: vec![],
            plugin_configs: HashMap::new(),
        }
    }
}

/// Enhanced validator trait with plugin capabilities
#[async_trait::async_trait]
pub trait Validator: Send + Sync {
    /// Unique identifier for the validator
    fn name(&self) -> &str;
    
    /// Human-readable description of what this validator checks
    fn description(&self) -> &str;
    
    /// Version of the validator for compatibility tracking
    fn version(&self) -> &str;
    
    /// Categories of validation this validator performs
    fn categories(&self) -> Vec<IssueType>;
    
    /// Content types this validator can handle
    fn supported_content_types(&self) -> Vec<ContentType>;
    
    /// Main validation method
    async fn validate(&self, content: &GeneratedContent, config: &ValidationConfig) -> Result<ValidationResult>;
    
    /// Check if the validator is properly configured and ready to run
    fn is_enabled(&self, config: &ValidationConfig) -> bool {
        config.enabled_validators.contains(&self.name().to_string())
    }
    
    /// Get validator-specific configuration from the global config as raw JSON
    fn get_plugin_config_raw<'a>(&self, config: &'a ValidationConfig) -> Option<&'a serde_json::Value> {
        config.plugin_configs.get(self.name())
    }
    
    /// Provide auto-fix suggestions for issues that can be automatically resolved
    async fn auto_fix(&self, _content: &GeneratedContent, _issue: &ValidationIssue) -> Result<Option<String>> {
        // Default implementation: no auto-fix capability
        Ok(None)
    }
    
    /// Validate that the validator's dependencies are available
    fn validate_dependencies(&self) -> Result<()> {
        Ok(())
    }
}

/// Trait for validators that can validate export formats
#[async_trait::async_trait]
pub trait ExportValidator: Send + Sync {
    fn name(&self) -> &str;
    fn supported_formats(&self) -> Vec<crate::export::ExportFormat>;
    async fn validate_export(&self, content: &[u8], format: &crate::export::ExportFormat, config: &ValidationConfig) -> Result<ValidationResult>;
}

/// Plugin information for validator discovery and management
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidatorPlugin {
    pub name: String,
    pub description: String,
    pub version: String,
    pub categories: Vec<IssueType>,
    pub supported_content_types: Vec<ContentType>,
    pub dependencies: Vec<String>,
    pub auto_fix_capable: bool,
    pub configuration_schema: Option<serde_json::Value>,
}

impl ValidationResult {
    /// Create a new successful validation result
    pub fn success(validator_name: String, score: f64, metadata: ValidationMetadata) -> Self {
        Self {
            validator_name,
            passed: true,
            score,
            issues: vec![],
            suggestions: vec![],
            metadata,
        }
    }
    
    /// Create a new failed validation result
    pub fn failure(validator_name: String, score: f64, issues: Vec<ValidationIssue>, metadata: ValidationMetadata) -> Self {
        Self {
            validator_name,
            passed: issues.iter().all(|i| i.severity > IssueSeverity::Error),
            score,
            issues,
            suggestions: vec![],
            metadata,
        }
    }
    
    /// Check if the result has any critical or error issues
    pub fn has_blocking_issues(&self) -> bool {
        self.issues.iter().any(|i| i.severity <= IssueSeverity::Error)
    }
    
    /// Get issues filtered by severity
    pub fn issues_by_severity(&self, severity: IssueSeverity) -> Vec<&ValidationIssue> {
        self.issues.iter().filter(|i| i.severity == severity).collect()
    }
    
    /// Get issues filtered by type
    pub fn issues_by_type(&self, issue_type: IssueType) -> Vec<&ValidationIssue> {
        self.issues.iter().filter(|i| i.issue_type == issue_type).collect()
    }
}

impl ValidationIssue {
    /// Create a new validation issue
    pub fn new(
        severity: IssueSeverity,
        issue_type: IssueType,
        message: String,
        location: Option<ContentLocation>,
    ) -> Self {
        Self {
            severity,
            issue_type,
            message,
            location,
            remediation_hint: None,
            auto_fixable: false,
        }
    }
    
    /// Add a remediation hint to the issue
    pub fn with_remediation_hint(mut self, hint: String) -> Self {
        self.remediation_hint = Some(hint);
        self
    }
    
    /// Mark the issue as auto-fixable
    pub fn with_auto_fix(mut self) -> Self {
        self.auto_fixable = true;
        self
    }
}

impl ContentLocation {
    /// Create a simple location with just a section name
    pub fn section(section: String) -> Self {
        Self {
            section: Some(section),
            line: None,
            character_range: None,
            slide_number: None,
            question_number: None,
        }
    }
    
    /// Create a location for a specific slide
    pub fn slide(slide_number: usize) -> Self {
        Self {
            section: None,
            line: None,
            character_range: None,
            slide_number: Some(slide_number),
            question_number: None,
        }
    }
    
    /// Create a location for a specific question
    pub fn question(question_number: usize) -> Self {
        Self {
            section: None,
            line: None,
            character_range: None,
            slide_number: None,
            question_number: Some(question_number),
        }
    }
}