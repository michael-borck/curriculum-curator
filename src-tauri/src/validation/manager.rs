use super::validators::{
    Validator, ExportValidator, ValidationResult, ValidationConfig, ValidationIssue, 
    IssueSeverity, IssueType, ValidatorPlugin, ValidationMetadata, ContentAnalysis
};
use crate::content::{GeneratedContent, ContentType};
use crate::export::ExportFormat;
use anyhow::{Result, Context};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::Instant;
use tokio::sync::mpsc;
use chrono::Utc;

/// Comprehensive validation result for multiple validators
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ValidationReport {
    pub content_id: Option<String>,
    pub content_type: ContentType,
    pub overall_passed: bool,
    pub overall_score: f64,
    pub validator_results: Vec<ValidationResult>,
    pub summary: ValidationSummary,
    pub recommendations: Vec<String>,
    pub auto_fix_available: bool,
    pub generated_at: chrono::DateTime<chrono::Utc>,
    pub execution_time_ms: u64,
}

/// Summary statistics for validation results
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ValidationSummary {
    pub total_validators_run: usize,
    pub validators_passed: usize,
    pub validators_failed: usize,
    pub total_issues: usize,
    pub issues_by_severity: HashMap<IssueSeverity, usize>,
    pub issues_by_type: HashMap<IssueType, usize>,
    pub auto_fixable_issues: usize,
}

/// Progress information for validation operations
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ValidationProgress {
    pub current_validator: String,
    pub completed_validators: usize,
    pub total_validators: usize,
    pub progress_percent: f32,
    pub current_operation: String,
    pub errors_encountered: usize,
}

/// Validation manager responsible for orchestrating multiple validators
pub struct ValidationManager {
    validators: HashMap<String, Arc<dyn Validator>>,
    export_validators: HashMap<String, Arc<dyn ExportValidator>>,
    progress_sender: Option<mpsc::UnboundedSender<ValidationProgress>>,
}

impl ValidationManager {
    /// Create a new validation manager
    pub fn new() -> Self {
        Self {
            validators: HashMap::new(),
            export_validators: HashMap::new(),
            progress_sender: None,
        }
    }

    /// Enable progress tracking for validation operations
    pub fn with_progress_tracking(mut self, sender: mpsc::UnboundedSender<ValidationProgress>) -> Self {
        self.progress_sender = Some(sender);
        self
    }

    /// Register a content validator
    pub fn register_validator(&mut self, validator: Box<dyn Validator>) -> Result<()> {
        // Validate the validator's dependencies
        validator.validate_dependencies()
            .context(format!("Validator '{}' failed dependency check", validator.name()))?;

        let name = validator.name().to_string();
        if self.validators.contains_key(&name) {
            return Err(anyhow::anyhow!("Validator '{}' is already registered", name));
        }

        self.validators.insert(name, Arc::from(validator));
        Ok(())
    }

    /// Register an export validator
    pub fn register_export_validator(&mut self, validator: Box<dyn ExportValidator>) -> Result<()> {
        let name = validator.name().to_string();
        if self.export_validators.contains_key(&name) {
            return Err(anyhow::anyhow!("Export validator '{}' is already registered", name));
        }

        self.export_validators.insert(name, Arc::from(validator));
        Ok(())
    }

    /// Get information about all registered validators
    pub fn get_registered_validators(&self) -> Vec<ValidatorPlugin> {
        self.validators
            .values()
            .map(|validator| ValidatorPlugin {
                name: validator.name().to_string(),
                description: validator.description().to_string(),
                version: validator.version().to_string(),
                categories: validator.categories(),
                supported_content_types: validator.supported_content_types(),
                dependencies: vec![], // TODO: Extract from validator if needed
                auto_fix_capable: true, // TODO: Check if validator supports auto-fix
                configuration_schema: None, // TODO: Extract schema if available
            })
            .collect()
    }

    /// Validate content using all enabled validators
    pub async fn validate_content(
        &self,
        content: &GeneratedContent,
        config: &ValidationConfig,
    ) -> Result<ValidationReport> {
        let start_time = Instant::now();
        
        // Filter validators based on configuration and content type
        let applicable_validators = self.get_applicable_validators(content, config);
        let total_validators = applicable_validators.len();

        self.send_progress(ValidationProgress {
            current_validator: "Starting validation".to_string(),
            completed_validators: 0,
            total_validators,
            progress_percent: 0.0,
            current_operation: "Preparing validators".to_string(),
            errors_encountered: 0,
        });

        let mut validator_results = Vec::new();
        let mut errors_encountered = 0;

        // Run validators sequentially for now (could be parallelized)
        for (index, (name, validator)) in applicable_validators.iter().enumerate() {
            self.send_progress(ValidationProgress {
                current_validator: name.clone(),
                completed_validators: index,
                total_validators,
                progress_percent: (index as f32 / total_validators as f32) * 100.0,
                current_operation: format!("Running {} validator", name),
                errors_encountered,
            });

            match validator.validate(content, config).await {
                Ok(result) => {
                    validator_results.push(result);
                }
                Err(e) => {
                    errors_encountered += 1;
                    // Create a failed validation result for the error
                    let error_result = ValidationResult {
                        validator_name: name.clone(),
                        passed: false,
                        score: 0.0,
                        issues: vec![ValidationIssue::new(
                            IssueSeverity::Error,
                            IssueType::Format,
                            format!("Validator failed to execute: {}", e),
                            None,
                        )],
                        suggestions: vec![format!("Check validator '{}' configuration", name)],
                        metadata: ValidationMetadata {
                            execution_time_ms: 0,
                            content_analyzed: ContentAnalysis {
                                word_count: content.metadata.word_count,
                                section_count: 1,
                                slide_count: None,
                                question_count: None,
                                reading_level: None,
                            },
                            validator_version: "unknown".to_string(),
                            timestamp: Utc::now(),
                        },
                    };
                    validator_results.push(error_result);
                }
            }
        }

        let execution_time = start_time.elapsed();

        // Generate comprehensive report
        let report = self.generate_report(content, validator_results, execution_time);

        self.send_progress(ValidationProgress {
            current_validator: "Complete".to_string(),
            completed_validators: total_validators,
            total_validators,
            progress_percent: 100.0,
            current_operation: "Validation complete".to_string(),
            errors_encountered,
        });

        Ok(report)
    }

    /// Validate exported content
    pub async fn validate_export(
        &self,
        content: &[u8],
        format: &ExportFormat,
        config: &ValidationConfig,
    ) -> Result<ValidationReport> {
        let start_time = Instant::now();
        
        // Get applicable export validators
        let applicable_validators: Vec<_> = self.export_validators
            .iter()
            .filter(|(name, validator)| {
                config.enabled_validators.contains(*name) &&
                validator.supported_formats().contains(format)
            })
            .collect();

        let mut validator_results = Vec::new();

        for (name, validator) in applicable_validators {
            match validator.validate_export(content, format, config).await {
                Ok(result) => validator_results.push(result),
                Err(e) => {
                    // Create error result for failed export validator
                    let error_result = ValidationResult {
                        validator_name: name.clone(),
                        passed: false,
                        score: 0.0,
                        issues: vec![ValidationIssue::new(
                            IssueSeverity::Error,
                            IssueType::Export,
                            format!("Export validator failed: {}", e),
                            None,
                        )],
                        suggestions: vec![],
                        metadata: ValidationMetadata {
                            execution_time_ms: 0,
                            content_analyzed: ContentAnalysis {
                                word_count: 0,
                                section_count: 0,
                                slide_count: None,
                                question_count: None,
                                reading_level: None,
                            },
                            validator_version: "unknown".to_string(),
                            timestamp: Utc::now(),
                        },
                    };
                    validator_results.push(error_result);
                }
            }
        }

        let execution_time = start_time.elapsed();

        // Create a dummy content for report generation
        let dummy_content = GeneratedContent {
            content_type: ContentType::Slides, // Default
            title: "Export Validation".to_string(),
            content: String::new(),
            metadata: crate::content::generator::ContentMetadata {
                word_count: 0,
                estimated_duration: "0 minutes".to_string(),
                difficulty_level: "Unknown".to_string(),
            },
        };

        Ok(self.generate_report(&dummy_content, validator_results, execution_time))
    }

    /// Run auto-fix for all fixable issues in a validation report
    pub async fn auto_fix_issues(
        &self,
        content: &GeneratedContent,
        report: &ValidationReport,
        config: &ValidationConfig,
    ) -> Result<Vec<String>> {
        if !config.auto_fix_enabled {
            return Ok(vec![]);
        }

        let mut fixes = Vec::new();

        for result in &report.validator_results {
            if let Some(validator) = self.validators.get(&result.validator_name) {
                for issue in &result.issues {
                    if issue.auto_fixable {
                        if let Ok(Some(fix)) = validator.auto_fix(content, issue).await {
                            fixes.push(fix);
                        }
                    }
                }
            }
        }

        Ok(fixes)
    }

    /// Get validators applicable to the given content and configuration
    fn get_applicable_validators(
        &self,
        content: &GeneratedContent,
        config: &ValidationConfig,
    ) -> Vec<(String, Arc<dyn Validator>)> {
        self.validators
            .iter()
            .filter(|(name, validator)| {
                // Check if validator is enabled in config
                if !validator.is_enabled(config) {
                    return false;
                }

                // Check if validator supports this content type
                let supported_types = validator.supported_content_types();
                supported_types.is_empty() || supported_types.contains(&content.content_type)
            })
            .map(|(name, validator)| (name.clone(), Arc::clone(validator)))
            .collect()
    }

    /// Generate a comprehensive validation report
    fn generate_report(
        &self,
        content: &GeneratedContent,
        validator_results: Vec<ValidationResult>,
        execution_time: std::time::Duration,
    ) -> ValidationReport {
        let total_validators_run = validator_results.len();
        let validators_passed = validator_results.iter().filter(|r| r.passed).count();
        let validators_failed = total_validators_run - validators_passed;

        // Collect all issues
        let all_issues: Vec<&ValidationIssue> = validator_results
            .iter()
            .flat_map(|r| &r.issues)
            .collect();

        let total_issues = all_issues.len();
        let auto_fixable_issues = all_issues.iter().filter(|i| i.auto_fixable).count();

        // Count issues by severity
        let mut issues_by_severity = HashMap::new();
        let mut issues_by_type = HashMap::new();

        for issue in &all_issues {
            *issues_by_severity.entry(issue.severity.clone()).or_insert(0) += 1;
            *issues_by_type.entry(issue.issue_type.clone()).or_insert(0) += 1;
        }

        // Calculate overall score (average of validator scores)
        let overall_score = if total_validators_run > 0 {
            validator_results.iter().map(|r| r.score).sum::<f64>() / total_validators_run as f64
        } else {
            0.0
        };

        // Determine if validation passed overall
        let overall_passed = validators_failed == 0 && 
            !all_issues.iter().any(|i| i.severity <= IssueSeverity::Error);

        // Generate recommendations
        let recommendations = self.generate_recommendations(&all_issues);

        ValidationReport {
            content_id: None, // Could be set by caller if needed
            content_type: content.content_type.clone(),
            overall_passed,
            overall_score,
            validator_results,
            summary: ValidationSummary {
                total_validators_run,
                validators_passed,
                validators_failed,
                total_issues,
                issues_by_severity,
                issues_by_type,
                auto_fixable_issues,
            },
            recommendations,
            auto_fix_available: auto_fixable_issues > 0,
            generated_at: Utc::now(),
            execution_time_ms: execution_time.as_millis() as u64,
        }
    }

    /// Generate actionable recommendations based on validation issues
    fn generate_recommendations(&self, issues: &[&ValidationIssue]) -> Vec<String> {
        let mut recommendations = Vec::new();

        // Group issues by type and generate specific recommendations
        let mut issue_types = HashMap::new();
        for issue in issues {
            issue_types.entry(&issue.issue_type).or_insert(Vec::new()).push(issue);
        }

        for (issue_type, type_issues) in issue_types {
            let count = type_issues.len();
            match issue_type {
                IssueType::Structure => {
                    recommendations.push(format!(
                        "Address {} structural issues by reviewing content organization and required sections",
                        count
                    ));
                }
                IssueType::Readability => {
                    recommendations.push(format!(
                        "Improve readability by simplifying {} sentences or paragraphs",
                        count
                    ));
                }
                IssueType::Completeness => {
                    recommendations.push(format!(
                        "Complete {} missing content elements for better educational value",
                        count
                    ));
                }
                IssueType::LearningObjectives => {
                    recommendations.push(format!(
                        "Review and align {} learning objectives with content",
                        count
                    ));
                }
                IssueType::Grammar | IssueType::Spelling => {
                    recommendations.push(format!(
                        "Correct {} language issues for professional presentation",
                        count
                    ));
                }
                _ => {
                    recommendations.push(format!(
                        "Address {} {:?} issues for improved quality",
                        count, issue_type
                    ));
                }
            }
        }

        // Add auto-fix recommendation if applicable
        let auto_fixable_count = issues.iter().filter(|i| i.auto_fixable).count();
        if auto_fixable_count > 0 {
            recommendations.push(format!(
                "Consider using auto-fix for {} automatically correctable issues",
                auto_fixable_count
            ));
        }

        recommendations
    }

    /// Send progress update if progress tracking is enabled
    fn send_progress(&self, progress: ValidationProgress) {
        if let Some(sender) = &self.progress_sender {
            let _ = sender.send(progress);
        }
    }
}

impl Default for ValidationManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::content::generator::ContentMetadata;

    // Mock validator for testing
    struct MockValidator {
        name: String,
        should_pass: bool,
    }

    #[async_trait::async_trait]
    impl Validator for MockValidator {
        fn name(&self) -> &str {
            &self.name
        }

        fn description(&self) -> &str {
            "Mock validator for testing"
        }

        fn version(&self) -> &str {
            "1.0.0"
        }

        fn categories(&self) -> Vec<IssueType> {
            vec![IssueType::Structure]
        }

        fn supported_content_types(&self) -> Vec<ContentType> {
            vec![ContentType::Slides]
        }

        async fn validate(&self, content: &GeneratedContent, _config: &ValidationConfig) -> Result<ValidationResult> {
            let metadata = ValidationMetadata {
                execution_time_ms: 10,
                content_analyzed: ContentAnalysis {
                    word_count: content.metadata.word_count,
                    section_count: 1,
                    slide_count: None,
                    question_count: None,
                    reading_level: None,
                },
                validator_version: self.version().to_string(),
                timestamp: Utc::now(),
            };

            if self.should_pass {
                Ok(ValidationResult::success(self.name.clone(), 0.9, metadata))
            } else {
                let issues = vec![ValidationIssue::new(
                    IssueSeverity::Warning,
                    IssueType::Structure,
                    "Test issue".to_string(),
                    None,
                )];
                Ok(ValidationResult::failure(self.name.clone(), 0.5, issues, metadata))
            }
        }
    }

    fn create_test_content() -> GeneratedContent {
        GeneratedContent {
            content_type: ContentType::Slides,
            title: "Test Content".to_string(),
            content: "Test content body".to_string(),
            metadata: ContentMetadata {
                word_count: 50,
                estimated_duration: "10 minutes".to_string(),
                difficulty_level: "Beginner".to_string(),
            },
        }
    }

    #[tokio::test]
    async fn test_validation_manager_basic() {
        let mut manager = ValidationManager::new();
        
        // Register a mock validator
        let validator = MockValidator {
            name: "test_validator".to_string(),
            should_pass: true,
        };
        manager.register_validator(Box::new(validator)).unwrap();

        // Test validation
        let content = create_test_content();
        let config = ValidationConfig::default();
        
        let report = manager.validate_content(&content, &config).await.unwrap();
        
        assert_eq!(report.validator_results.len(), 1);
        assert!(report.overall_passed);
        assert!(report.overall_score > 0.0);
    }

    #[tokio::test]
    async fn test_validation_manager_multiple_validators() {
        let mut manager = ValidationManager::new();
        
        // Register multiple validators
        manager.register_validator(Box::new(MockValidator {
            name: "passing_validator".to_string(),
            should_pass: true,
        })).unwrap();
        
        manager.register_validator(Box::new(MockValidator {
            name: "failing_validator".to_string(),
            should_pass: false,
        })).unwrap();

        let content = create_test_content();
        let mut config = ValidationConfig::default();
        config.enabled_validators = vec![
            "passing_validator".to_string(),
            "failing_validator".to_string(),
        ];
        
        let report = manager.validate_content(&content, &config).await.unwrap();
        
        assert_eq!(report.validator_results.len(), 2);
        assert_eq!(report.summary.validators_passed, 1);
        assert_eq!(report.summary.validators_failed, 1);
    }
}