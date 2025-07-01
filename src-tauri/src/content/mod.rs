pub mod generator;
pub mod templates;
pub mod workflow;
pub mod workflow_steps;
pub mod workflow_commands;
pub mod batch_generator;
pub mod batch_commands;
pub mod prompt_templates;
pub mod pedagogical;
pub mod module_generator;
pub mod learning_objectives;
pub mod context_manager;
pub mod progress_tracker;

pub use generator::{ContentGenerator, ContentRequest, GeneratedContent, ContentType};
pub use templates::{TemplateManager, ContentTemplate};
pub use batch_generator::{
    BatchContentGenerator, BatchGenerationRequest, BatchContentItem, BatchGenerationOptions,
    BatchPriority, BatchGenerationProgress, BatchGenerationResult, BatchItemResult,
    BatchError, BatchErrorType
};
pub use workflow::{
    WorkflowEngine, WorkflowInstance, WorkflowStepInstance, WorkflowStatus, StepStatus,
    WorkflowContext, WorkflowProgress, StepExecutionResult, WorkflowStep, StepMetadata,
    StepCategory, WorkflowStepDefinition
};
pub use workflow_steps::{
    InputValidationStep, LearningObjectiveGenerationStep, ContentGenerationStep,
    ContentValidationStep, OutputFinalizationStep, ContentValidationResult, WorkflowSummary
};
pub use prompt_templates::{
    PromptTemplateEngine, PromptTemplate, PedagogicalApproach, DifficultyLevel,
    TemplateContext, PedagogicalMetadata, ContentGenerationMetadata, TimeAllocation,
    ReadingLevel, AccessibilityFeature, TemplateValidationResult
};
pub use pedagogical::{
    PedagogicalFramework, PedagogicalMethod, MethodologyMetadata, ContentStructure,
    ContentSection, LearningFlow, InteractionPoint, AssessmentPoint, TimeAllocationSuggestion,
    SequenceType, InteractionLevel, CognitiveLevel, MethodologyContext, MethodologyValidation
};
pub use module_generator::{
    ModuleGenerator, ContentModule, ContentItem, ModuleStructure, ContentTypeSelection,
    ContentTypeConfig, ContentPriority, ContentCustomization, GenerationPreferences,
    ModuleOptions, ModuleOrganizationType, ModuleSizePreference, AssessmentItem,
    LengthPreference, ComplexityAdjustment, ReviewPoint
};
pub use learning_objectives::{
    LearningObjectiveGenerator, LearningObjective, BloomLevel, ObjectiveType,
    ObjectiveGenerationRequest, ObjectiveCount, ComplexityPreference,
    VerificationStatus, UserFeedback, ObjectiveRating, VerificationWorkflow,
    VerificationWorkflowManager, ReviewSession, ApprovalStatus
};
pub use context_manager::{
    ContentContextManager, GenerationContext, SessionMetadata, SessionStatus,
    GeneratedContentState, GenerationStatus, PedagogicalContext, WorkflowState,
    UserPreferences, GenerationStep, StepError, ErrorRecoveryState, ContextStore,
    InMemoryContextStore, BlockingIssue, RecoveryStrategy
};
pub use progress_tracker::{
    ProgressTracker, TrackingSession, ProgressEvent, UserFeedbackEvent,
    GenerationPhase, ProgressInfo, Milestone, InteractionType, UserResponse,
    FeedbackType, QualityRating, ProgressUpdate
};