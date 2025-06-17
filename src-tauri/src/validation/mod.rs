pub mod validators;
pub mod manager;
pub mod built_in;
pub mod factory;
pub mod commands;
pub mod remediation;
pub mod remediation_commands;
pub mod smart_config;
pub mod smart_config_commands;

pub use validators::{
    Validator, ExportValidator, ValidationResult, ValidationConfig, ValidationIssue,
    IssueSeverity, IssueType, ValidationMetadata, ContentAnalysis, ValidatorPlugin
};
pub use manager::{ValidationManager, ValidationReport, ValidationSummary, ValidationProgress};
pub use factory::ValidatorFactory;
pub use built_in::{
    ReadabilityConfig, ComplexityLevel, AgeSpecificThresholds, ReadabilityThresholds,
    SentenceAnalysis, ReadabilityValidator, StructureValidator, CompletenessValidator, GrammarValidator,
    StructureConfig, PedagogicalPattern, StructureAnalysis, DetectedSection,
    ContentAlignmentValidator, AlignmentConfig, AlignmentAnalysis, TermInconsistency, 
    ObjectiveAlignment, TopicAnalysis
};
pub use commands::{
    ValidationService, validate_content_command, get_validation_progress_command,
    list_validators_command, get_validation_config_command, auto_fix_issues_command
};
pub use remediation::{
    RemediationManager, RemediationConfig, RemediationSession, RemediationSuggestion,
    SessionStatus, DecisionType, RemediationFixType, ConfidenceLevel, RiskLevel,
    RemediationPreview, UserDecision, AppliedFix, ImpactAssessment,
    AlternativeFix, DiffHighlight, ChangeType, RemediationPreferences
};
pub use remediation_commands::{
    RemediationService, GenerateRemediationRequest, RemediationResponse,
    ApplyFixRequest, UserDecisionRequest, SessionStatusResponse, RemediationStatistics
};
pub use smart_config::{
    SmartConfigManager, UserExperienceLevel, UserPreferences, ValidationFocus,
    ValidationFeature, NotificationLevel, UserAction, SmartRecommendations,
    ConfigCustomizations, AdaptiveSettings, ValidationPreset
};
pub use smart_config_commands::{
    SmartConfigService, UserProfile, UsageStatistics, GetSmartConfigRequest,
    SmartConfigResponse, UpdateExperienceLevelRequest, RecordDecisionRequest,
    CreateCustomConfigRequest, ExperienceLevelsResponse, ExperienceLevelInfo
};