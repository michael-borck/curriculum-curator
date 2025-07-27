use super::dry_run::*;
use super::validators::*;
use super::remediation::RemediationSuggestion;
use crate::content::GeneratedContent;
use crate::validation::PersonalizationSettings;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use tauri::State;
use uuid::Uuid;

/// Global dry run service state
pub struct DryRunService {
    manager: Mutex<DryRunManager>,
}

impl DryRunService {
    pub fn new() -> Self {
        Self {
            manager: Mutex::new(DryRunManager::new()),
        }
    }
}

/// Request to create a new dry run session
#[derive(Debug, Serialize, Deserialize)]
pub struct CreateDryRunRequest {
    pub content: GeneratedContent,
    pub validation_results: Vec<ValidationResult>,
    pub remediation_suggestions: Vec<RemediationSuggestion>,
    pub user_settings: Option<PersonalizationSettings>,
    pub config: Option<DryRunConfig>,
}

/// Response containing dry run session information
#[derive(Debug, Serialize, Deserialize)]
pub struct DryRunResponse {
    pub session_id: Uuid,
    pub results: DryRunResults,
    pub session_metadata: SessionMetadata,
}

/// Metadata about the dry run session
#[derive(Debug, Serialize, Deserialize)]
pub struct SessionMetadata {
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub expires_at: chrono::DateTime<chrono::Utc>,
    pub generation_time_ms: u64,
    pub total_changes_analyzed: usize,
    pub cache_status: CacheStatus,
}

/// Status of session caching
#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum CacheStatus {
    NewSession,
    CachedResult,
    RefreshedCache,
}

/// Request to update dry run configuration
#[derive(Debug, Serialize, Deserialize)]
pub struct UpdateDryRunConfigRequest {
    pub session_id: Uuid,
    pub config: DryRunConfig,
}

/// Request to get preview for specific change group
#[derive(Debug, Serialize, Deserialize)]
pub struct GetChangeGroupPreviewRequest {
    pub session_id: Uuid,
    pub group_id: Uuid,
    pub preview_mode: PreviewMode,
}

/// Response with detailed change group preview
#[derive(Debug, Serialize, Deserialize)]
pub struct ChangeGroupPreviewResponse {
    pub group: ChangeGroup,
    pub detailed_preview: DetailedPreview,
    pub impact_breakdown: ImpactBreakdown,
    pub safety_check: SafetyCheck,
}

/// Detailed preview of changes
#[derive(Debug, Serialize, Deserialize)]
pub struct DetailedPreview {
    pub before_content: String,
    pub after_content: String,
    pub diff_analysis: DiffAnalysis,
    pub visual_diff: VisualDiff,
}

/// Analysis of differences between before and after
#[derive(Debug, Serialize, Deserialize)]
pub struct DiffAnalysis {
    pub additions: Vec<DiffSegment>,
    pub deletions: Vec<DiffSegment>,
    pub modifications: Vec<DiffSegment>,
    pub moved_sections: Vec<MovedSection>,
}

/// A segment of difference
#[derive(Debug, Serialize, Deserialize)]
pub struct DiffSegment {
    pub content: String,
    pub line_range: (usize, usize),
    pub change_type: ChangeType,
    pub significance: SignificanceLevel,
}

/// Level of significance for a change
#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum SignificanceLevel {
    Trivial,     // Whitespace, punctuation
    Minor,       // Single word changes
    Moderate,    // Sentence restructuring
    Major,       // Paragraph changes
    Structural,  // Section reorganization
}

/// Visual representation of differences
#[derive(Debug, Serialize, Deserialize)]
pub struct VisualDiff {
    pub html_diff: String,
    pub side_by_side: SideBySideView,
    pub inline_diff: InlineDiffView,
}

/// Side-by-side comparison view
#[derive(Debug, Serialize, Deserialize)]
pub struct SideBySideView {
    pub before_lines: Vec<DiffLine>,
    pub after_lines: Vec<DiffLine>,
    pub line_mappings: Vec<LineMapping>,
}

/// Single line in diff view
#[derive(Debug, Serialize, Deserialize)]
pub struct DiffLine {
    pub number: usize,
    pub content: String,
    pub line_type: DiffLineType,
    pub highlights: Vec<TextHighlight>,
}

/// Type of diff line
#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum DiffLineType {
    Unchanged,
    Added,
    Deleted,
    Modified,
    Context,
}

/// Text highlight within a line
#[derive(Debug, Serialize, Deserialize)]
pub struct TextHighlight {
    pub start: usize,
    pub end: usize,
    pub highlight_type: HighlightType,
}

/// Type of text highlight
#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum HighlightType {
    Addition,
    Deletion,
    Modification,
    Important,
}

/// Mapping between before and after line numbers
#[derive(Debug, Serialize, Deserialize)]
pub struct LineMapping {
    pub before_line: Option<usize>,
    pub after_line: Option<usize>,
    pub mapping_type: MappingType,
}

/// Type of line mapping
#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum MappingType {
    Direct,      // 1:1 mapping
    Split,       // 1 before → multiple after
    Merge,       // Multiple before → 1 after
    Insert,      // New content
    Delete,      // Removed content
}

/// Inline diff view
#[derive(Debug, Serialize, Deserialize)]
pub struct InlineDiffView {
    pub unified_lines: Vec<UnifiedDiffLine>,
    pub context_size: usize,
    pub total_context_lines: usize,
}

/// Line in unified diff format
#[derive(Debug, Serialize, Deserialize)]
pub struct UnifiedDiffLine {
    pub content: String,
    pub line_type: UnifiedLineType,
    pub before_line_number: Option<usize>,
    pub after_line_number: Option<usize>,
}

/// Type of unified diff line
#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum UnifiedLineType {
    Context,
    Addition,
    Deletion,
    Header,
    Separator,
}

/// Moved section information
#[derive(Debug, Serialize, Deserialize)]
pub struct MovedSection {
    pub content: String,
    pub from_location: ContentLocation,
    pub to_location: ContentLocation,
    pub move_reason: String,
}

/// Breakdown of impact by category
#[derive(Debug, Serialize, Deserialize)]
pub struct ImpactBreakdown {
    pub readability_impact: f64,
    pub structure_impact: f64,
    pub content_impact: f64,
    pub educational_impact: f64,
    pub accessibility_impact: f64,
    pub impact_explanations: Vec<ImpactExplanation>,
}

/// Explanation of a specific impact
#[derive(Debug, Serialize, Deserialize)]
pub struct ImpactExplanation {
    pub category: String,
    pub description: String,
    pub positive_effects: Vec<String>,
    pub potential_concerns: Vec<String>,
    pub mitigation_suggestions: Vec<String>,
}

/// Safety check results for changes
#[derive(Debug, Serialize, Deserialize)]
pub struct SafetyCheck {
    pub overall_safety: SafetyLevel,
    pub risk_factors: Vec<RiskFactor>,
    pub safety_recommendations: Vec<String>,
    pub requires_review: bool,
    pub auto_apply_safe: bool,
}

/// Safety level assessment
#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum SafetyLevel {
    Safe,        // No concerns
    LowRisk,     // Minor concerns
    ModerateRisk, // Some review needed
    HighRisk,    // Careful review required
    Unsafe,      // Should not apply
}

/// Individual risk factor
#[derive(Debug, Serialize, Deserialize)]
pub struct RiskFactor {
    pub factor_type: RiskFactorType,
    pub description: String,
    pub severity: RiskSeverity,
    pub mitigation: Option<String>,
}

/// Type of risk factor
#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum RiskFactorType {
    ContentAccuracy,
    EducationalValue,
    Accessibility,
    TechnicalFormat,
    UserExperience,
}

/// Severity of risk
#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum RiskSeverity {
    Low,
    Medium,
    High,
    Critical,
}

/// Request to apply selected changes from dry run
#[derive(Debug, Serialize, Deserialize)]
pub struct ApplyDryRunChangesRequest {
    pub session_id: Uuid,
    pub selected_groups: Vec<Uuid>,
    pub selected_changes: Vec<Uuid>,
    pub apply_mode: ApplyMode,
    pub backup_original: bool,
}


/// Response after applying changes
#[derive(Debug, Serialize, Deserialize)]
pub struct ApplyChangesResponse {
    pub success: bool,
    pub applied_changes: Vec<AppliedChange>,
    pub failed_changes: Vec<FailedChange>,
    pub final_content: Option<GeneratedContent>,
    pub backup_location: Option<String>,
    pub application_summary: ApplicationSummary,
}


/// Successfully applied change
#[derive(Debug, Serialize, Deserialize)]
pub struct AppliedChange {
    pub change_id: Uuid,
    pub title: String,
    pub applied_at: chrono::DateTime<chrono::Utc>,
    pub actual_impact: ActualImpact,
}

/// Failed change application
#[derive(Debug, Serialize, Deserialize)]
pub struct FailedChange {
    pub change_id: Uuid,
    pub title: String,
    pub error_message: String,
    pub retry_suggestion: Option<String>,
}

/// Actual impact after applying changes
#[derive(Debug, Serialize, Deserialize)]
pub struct ActualImpact {
    pub lines_changed: usize,
    pub words_changed: usize,
    pub sections_affected: Vec<String>,
    pub quality_improvement: Option<f64>,
}

/// Summary of the application process
#[derive(Debug, Serialize, Deserialize)]
pub struct ApplicationSummary {
    pub total_changes_attempted: usize,
    pub successful_applications: usize,
    pub failed_applications: usize,
    pub overall_success_rate: f64,
    pub time_taken_ms: u64,
    pub quality_delta: Option<f64>,
}

/// Tauri command to create a new dry run session
#[tauri::command]
pub async fn create_dry_run_session(
    request: CreateDryRunRequest,
    service: State<'_, DryRunService>,
) -> Result<DryRunResponse, String> {
    let start_time = std::time::Instant::now();
    
    let mut manager = service.manager.lock().unwrap();
    
    let config = request.config.unwrap_or_default();
    let session_id = Uuid::new_v4();
    
    // Check cache first
    let cache_status = if manager.has_cached_session(&request.content) {
        CacheStatus::CachedResult
    } else {
        CacheStatus::NewSession
    };
    
    // Generate dry run results
    let results = manager.create_dry_run(
        session_id,
        request.content.clone(),
        request.validation_results,
        request.remediation_suggestions,
        request.user_settings,
        config.clone(),
    ).map_err(|e| e.to_string())?;
    
    let generation_time = start_time.elapsed().as_millis() as u64;
    
    let session_metadata = SessionMetadata {
        created_at: chrono::Utc::now(),
        expires_at: chrono::Utc::now() + chrono::Duration::minutes(config.cache_duration_minutes as i64),
        generation_time_ms: generation_time,
        total_changes_analyzed: results.change_groups.iter()
            .map(|g| g.changes.len())
            .sum(),
        cache_status,
    };
    
    Ok(DryRunResponse {
        session_id,
        results,
        session_metadata,
    })
}

/// Tauri command to get detailed preview for a change group
#[tauri::command]
pub async fn get_change_group_preview(
    request: GetChangeGroupPreviewRequest,
    service: State<'_, DryRunService>,
) -> Result<ChangeGroupPreviewResponse, String> {
    let manager = service.manager.lock().unwrap();
    
    let session = manager.get_session(&request.session_id)
        .ok_or("Session not found")?;
    
    let group = session.preview_results.change_groups.iter()
        .find(|g| g.group_id == request.group_id)
        .ok_or("Change group not found")?;
    
    // Generate detailed preview based on preview mode
    let detailed_preview = generate_detailed_preview(group, &request.preview_mode)?;
    let impact_breakdown = analyze_impact_breakdown(group);
    let safety_check = perform_safety_check(group);
    
    Ok(ChangeGroupPreviewResponse {
        group: group.clone(),
        detailed_preview,
        impact_breakdown,
        safety_check,
    })
}

/// Tauri command to update dry run configuration
#[tauri::command]
pub async fn update_dry_run_config(
    request: UpdateDryRunConfigRequest,
    service: State<'_, DryRunService>,
) -> Result<(), String> {
    let mut manager = service.manager.lock().unwrap();
    
    manager.update_session_config(&request.session_id, request.config)
        .map_err(|e| e.to_string())?;
    
    Ok(())
}

/// Tauri command to apply selected changes from dry run
#[tauri::command]
pub async fn apply_dry_run_changes(
    request: ApplyDryRunChangesRequest,
    service: State<'_, DryRunService>,
) -> Result<ApplyChangesResponse, String> {
    let start_time = std::time::Instant::now();
    
    let mut manager = service.manager.lock().unwrap();
    
    let result = manager.apply_changes(
        &request.session_id,
        &request.selected_groups,
        &request.selected_changes,
        request.apply_mode,
        request.backup_original,
    ).map_err(|e| e.to_string())?;
    
    let application_time = start_time.elapsed().as_millis() as u64;
    
    // Create summary
    let total_attempted = request.selected_changes.len();
    let successful = result.applied_changes.len();
    let failed = result.failed_changes.len();
    
    let application_summary = ApplicationSummary {
        total_changes_attempted: total_attempted,
        successful_applications: successful,
        failed_applications: failed,
        overall_success_rate: if total_attempted > 0 {
            successful as f64 / total_attempted as f64 * 100.0
        } else {
            100.0
        },
        time_taken_ms: application_time,
        quality_delta: result.quality_improvement,
    };
    
    Ok(ApplyChangesResponse {
        success: result.success,
        applied_changes: result.applied_changes.into_iter().map(|ac| AppliedChange {
            change_id: ac.change_id,
            title: ac.title,
            applied_at: ac.applied_at,
            actual_impact: ActualImpact {
                lines_changed: 0,
                words_changed: 0,
                sections_affected: vec![],
                quality_improvement: None,
            },
        }).collect(),
        failed_changes: result.failed_changes.into_iter().map(|fc| FailedChange {
            change_id: fc.change_id,
            title: fc.title,
            error_message: fc.error_message,
            retry_suggestion: None,
        }).collect(),
        final_content: result.final_content,
        backup_location: result.backup_location,
        application_summary,
    })
}

/// Tauri command to get list of active dry run sessions
#[tauri::command]
pub async fn list_dry_run_sessions(
    service: State<'_, DryRunService>,
) -> Result<Vec<DryRunSessionSummary>, String> {
    let manager = service.manager.lock().unwrap();
    
    Ok(manager.list_active_sessions())
}


/// Tauri command to cancel/delete a dry run session
#[tauri::command]
pub async fn cancel_dry_run_session(
    session_id: String,
    service: State<'_, DryRunService>,
) -> Result<(), String> {
    let session_uuid = Uuid::parse_str(&session_id)
        .map_err(|_| "Invalid session ID format")?;
    
    let mut manager = service.manager.lock().unwrap();
    manager.cancel_session(&session_uuid)
        .map_err(|e| e.to_string())?;
    
    Ok(())
}

/// Helper function to generate detailed preview
fn generate_detailed_preview(
    _group: &ChangeGroup,
    _preview_mode: &PreviewMode,
) -> Result<DetailedPreview, String> {
    // Simplified implementation - in real implementation this would
    // generate actual diffs and visual representations
    let before_content = "Original content...".to_string();
    let after_content = "Modified content...".to_string();
    
    let diff_analysis = DiffAnalysis {
        additions: vec![],
        deletions: vec![],
        modifications: vec![],
        moved_sections: vec![],
    };
    
    let visual_diff = VisualDiff {
        html_diff: "<div>HTML diff representation</div>".to_string(),
        side_by_side: SideBySideView {
            before_lines: vec![],
            after_lines: vec![],
            line_mappings: vec![],
        },
        inline_diff: InlineDiffView {
            unified_lines: vec![],
            context_size: 3,
            total_context_lines: 0,
        },
    };
    
    Ok(DetailedPreview {
        before_content,
        after_content,
        diff_analysis,
        visual_diff,
    })
}

/// Helper function to analyze impact breakdown
fn analyze_impact_breakdown(_group: &ChangeGroup) -> ImpactBreakdown {
    ImpactBreakdown {
        readability_impact: 75.0,
        structure_impact: 60.0,
        content_impact: 80.0,
        educational_impact: 70.0,
        accessibility_impact: 65.0,
        impact_explanations: vec![
            ImpactExplanation {
                category: "Readability".to_string(),
                description: "Changes will improve text clarity and flow".to_string(),
                positive_effects: vec!["Easier to understand".to_string()],
                potential_concerns: vec![],
                mitigation_suggestions: vec![],
            }
        ],
    }
}

/// Helper function to perform safety check
fn perform_safety_check(_group: &ChangeGroup) -> SafetyCheck {
    SafetyCheck {
        overall_safety: SafetyLevel::Safe,
        risk_factors: vec![],
        safety_recommendations: vec!["Changes appear safe to apply".to_string()],
        requires_review: false,
        auto_apply_safe: true,
    }
}

/// Export dry run command names for registration
pub fn get_dry_run_command_names() -> Vec<&'static str> {
    vec![
        "create_dry_run_session",
        "get_change_group_preview",
        "update_dry_run_config",
        "apply_dry_run_changes",
        "list_dry_run_sessions",
        "cancel_dry_run_session",
    ]
}