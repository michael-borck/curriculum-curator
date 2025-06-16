use super::validators::*;
use super::manager::ValidationManager;
use super::built_in::*;
use crate::content::ContentType;
use anyhow::Result;

/// Factory for creating and registering built-in validators
pub struct ValidatorFactory;

impl ValidatorFactory {
    /// Create a validation manager with all built-in validators registered
    pub fn create_default_manager() -> Result<ValidationManager> {
        let mut manager = ValidationManager::new();
        
        // Register all built-in validators
        manager.register_validator(Box::new(StructureValidator::new()) as Box<dyn Validator>)?;
        manager.register_validator(Box::new(ReadabilityValidator::new()) as Box<dyn Validator>)?;
        manager.register_validator(Box::new(CompletenessValidator::new()) as Box<dyn Validator>)?;
        manager.register_validator(Box::new(GrammarValidator::new()) as Box<dyn Validator>)?;
        
        Ok(manager)
    }
    
    /// Create a validation manager with specific validators
    pub fn create_custom_manager(validator_names: &[&str]) -> Result<ValidationManager> {
        let mut manager = ValidationManager::new();
        
        for &name in validator_names {
            match name {
                "structure" => manager.register_validator(Box::new(StructureValidator::new()) as Box<dyn Validator>)?,
                "readability" => manager.register_validator(Box::new(ReadabilityValidator::new()) as Box<dyn Validator>)?,
                "completeness" => manager.register_validator(Box::new(CompletenessValidator::new()) as Box<dyn Validator>)?,
                "grammar" => manager.register_validator(Box::new(GrammarValidator::new()) as Box<dyn Validator>)?,
                _ => return Err(anyhow::anyhow!("Unknown validator: {}", name)),
            }
        }
        
        Ok(manager)
    }
    
    /// Get information about all available built-in validators
    pub fn get_available_validators() -> Vec<ValidatorPlugin> {
        vec![
            ValidatorPlugin {
                name: "structure".to_string(),
                description: "Validates content structure and required sections".to_string(),
                version: "1.0.0".to_string(),
                categories: vec![IssueType::Structure, IssueType::Completeness],
                supported_content_types: vec![
                    ContentType::Slides,
                    ContentType::Quiz,
                    ContentType::Worksheet,
                    ContentType::InstructorNotes,
                    ContentType::ActivityGuide,
                ],
                dependencies: vec![],
                auto_fix_capable: true,
                configuration_schema: Some(serde_json::json!({
                    "type": "object",
                    "properties": {
                        "required_sections": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "array",
                                "items": { "type": "string" }
                            }
                        }
                    }
                })),
            },
            ValidatorPlugin {
                name: "readability".to_string(),
                description: "Validates content readability and complexity".to_string(),
                version: "1.0.0".to_string(),
                categories: vec![IssueType::Readability, IssueType::AgeAppropriateness],
                supported_content_types: vec![
                    ContentType::Slides,
                    ContentType::Quiz,
                    ContentType::Worksheet,
                    ContentType::InstructorNotes,
                    ContentType::ActivityGuide,
                ],
                dependencies: vec![],
                auto_fix_capable: false,
                configuration_schema: Some(serde_json::json!({
                    "type": "object",
                    "properties": {
                        "max_sentence_length": { "type": "integer", "default": 25 },
                        "max_paragraph_length": { "type": "integer", "default": 150 },
                        "target_reading_level": { "type": "number", "default": 70.0 }
                    }
                })),
            },
            ValidatorPlugin {
                name: "completeness".to_string(),
                description: "Validates content completeness and required elements".to_string(),
                version: "1.0.0".to_string(),
                categories: vec![IssueType::Completeness, IssueType::LearningObjectives],
                supported_content_types: vec![
                    ContentType::Slides,
                    ContentType::Quiz,
                    ContentType::Worksheet,
                    ContentType::InstructorNotes,
                    ContentType::ActivityGuide,
                ],
                dependencies: vec![],
                auto_fix_capable: false,
                configuration_schema: Some(serde_json::json!({
                    "type": "object",
                    "properties": {
                        "min_word_counts": {
                            "type": "object",
                            "additionalProperties": { "type": "integer" }
                        },
                        "require_learning_objectives": { "type": "boolean", "default": true },
                        "require_examples": { "type": "boolean", "default": false }
                    }
                })),
            },
            ValidatorPlugin {
                name: "grammar".to_string(),
                description: "Validates basic grammar and spelling".to_string(),
                version: "1.0.0".to_string(),
                categories: vec![IssueType::Grammar, IssueType::Spelling],
                supported_content_types: vec![
                    ContentType::Slides,
                    ContentType::Quiz,
                    ContentType::Worksheet,
                    ContentType::InstructorNotes,
                    ContentType::ActivityGuide,
                ],
                dependencies: vec![],
                auto_fix_capable: true,
                configuration_schema: Some(serde_json::json!({
                    "type": "object",
                    "properties": {
                        "check_repeated_words": { "type": "boolean", "default": true },
                        "check_capitalization": { "type": "boolean", "default": true },
                        "custom_error_patterns": {
                            "type": "object",
                            "additionalProperties": { "type": "string" }
                        }
                    }
                })),
            },
        ]
    }
    
    /// Create a validation config optimized for specific content types
    pub fn create_content_type_config(content_type: ContentType) -> ValidationConfig {
        let mut config = ValidationConfig::default();
        
        // Customize based on content type
        match content_type {
            ContentType::Slides => {
                config.enabled_validators = vec![
                    "structure".to_string(),
                    "readability".to_string(),
                    "completeness".to_string(),
                ];
                config.readability_threshold = 6.0; // Slightly more complex for slides
            },
            ContentType::Quiz => {
                config.enabled_validators = vec![
                    "structure".to_string(),
                    "completeness".to_string(),
                    "grammar".to_string(),
                ];
                config.readability_threshold = 8.0; // Simpler for quiz questions
            },
            ContentType::Worksheet => {
                config.enabled_validators = vec![
                    "structure".to_string(),
                    "readability".to_string(),
                    "completeness".to_string(),
                    "grammar".to_string(),
                ];
                config.readability_threshold = 7.0; // Moderate complexity
            },
            ContentType::InstructorNotes => {
                config.enabled_validators = vec![
                    "completeness".to_string(),
                    "grammar".to_string(),
                ];
                config.readability_threshold = 5.0; // Can be more complex
            },
            ContentType::ActivityGuide => {
                config.enabled_validators = vec![
                    "structure".to_string(),
                    "readability".to_string(),
                    "completeness".to_string(),
                ];
                config.readability_threshold = 7.5; // Clear instructions needed
            },
        }
        
        config
    }
    
    /// Create a minimal validation config for fast validation
    pub fn create_minimal_config() -> ValidationConfig {
        let mut config = ValidationConfig::default();
        config.enabled_validators = vec!["structure".to_string()];
        config.severity_threshold = IssueSeverity::Warning;
        config.auto_fix_enabled = false;
        config
    }
    
    /// Create a comprehensive validation config for thorough checking
    pub fn create_comprehensive_config() -> ValidationConfig {
        let mut config = ValidationConfig::default();
        config.enabled_validators = vec![
            "structure".to_string(),
            "readability".to_string(),
            "completeness".to_string(),
            "grammar".to_string(),
        ];
        config.severity_threshold = IssueSeverity::Info;
        config.auto_fix_enabled = true;
        config
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::content::generator::ContentMetadata;

    #[tokio::test]
    async fn test_factory_creates_manager() {
        let manager = ValidatorFactory::create_default_manager().unwrap();
        let validators = manager.get_registered_validators();
        
        assert_eq!(validators.len(), 4);
        assert!(validators.iter().any(|v| v.name == "structure"));
        assert!(validators.iter().any(|v| v.name == "readability"));
        assert!(validators.iter().any(|v| v.name == "completeness"));
        assert!(validators.iter().any(|v| v.name == "grammar"));
    }

    #[tokio::test]
    async fn test_custom_manager_creation() {
        let manager = ValidatorFactory::create_custom_manager(&["structure", "grammar"]).unwrap();
        let validators = manager.get_registered_validators();
        
        assert_eq!(validators.len(), 2);
        assert!(validators.iter().any(|v| v.name == "structure"));
        assert!(validators.iter().any(|v| v.name == "grammar"));
    }

    #[tokio::test]
    async fn test_content_type_configs() {
        let slides_config = ValidatorFactory::create_content_type_config(ContentType::Slides);
        let quiz_config = ValidatorFactory::create_content_type_config(ContentType::Quiz);
        
        assert!(slides_config.enabled_validators.contains(&"readability".to_string()));
        assert!(!quiz_config.enabled_validators.contains(&"readability".to_string()));
        assert!(quiz_config.readability_threshold > slides_config.readability_threshold);
    }

    #[tokio::test]
    async fn test_validation_with_factory() {
        let manager = ValidatorFactory::create_default_manager().unwrap();
        let config = ValidatorFactory::create_minimal_config();
        
        let content = crate::content::GeneratedContent {
            content_type: ContentType::Slides,
            title: "Test Content".to_string(),
            content: "# Title\n## Learning Objectives\n- Learn something\n## Content\nSome content here\n## Summary\nSummary".to_string(),
            metadata: ContentMetadata {
                word_count: 15,
                estimated_duration: "5 minutes".to_string(),
                difficulty_level: "Beginner".to_string(),
            },
        };
        
        let report = manager.validate_content(&content, &config).await.unwrap();
        
        assert!(!report.validator_results.is_empty());
        assert_eq!(report.content_type, ContentType::Slides);
    }
}