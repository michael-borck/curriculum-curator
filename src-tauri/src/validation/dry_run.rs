use super::validators::*;
use super::remediation::{RemediationManager, RemediationSuggestion, RemediationFixType, ConfidenceLevel, RiskLevel};
use crate::validation::PersonalizationSettings;
use crate::content::GeneratedContent;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Dry run system for previewing validation changes before application
#[derive(Debug, Clone)]
pub struct DryRunManager {
    preview_cache: HashMap<Uuid, DryRunSession>,
    config: DryRunConfig,
}

/// Configuration for dry run behavior
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DryRunConfig {
    /// Maximum number of cached dry run sessions
    pub max_cached_sessions: usize,
    /// Whether to show technical diff details
    pub show_technical_diffs: bool,
    /// Whether to include confidence and risk assessments
    pub include_risk_assessment: bool,
    /// Whether to generate alternative preview options
    pub generate_alternatives: bool,
    /// Cache preview results for this duration (in minutes)
    pub cache_duration_minutes: u32,
}

impl Default for DryRunConfig {
    fn default() -> Self {
        Self {
            max_cached_sessions: 10,
            show_technical_diffs: true,
            include_risk_assessment: true,
            generate_alternatives: false,
            cache_duration_minutes: 30,
        }
    }
}

/// A dry run session containing all preview information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DryRunSession {
    pub session_id: Uuid,
    pub original_content: GeneratedContent,
    pub validation_results: Vec<ValidationResult>,
    pub preview_results: DryRunResults,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub expires_at: chrono::DateTime<chrono::Utc>,
    pub user_settings: Option<PersonalizationSettings>,
}

/// Complete dry run results with all preview information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DryRunResults {
    pub overall_summary: DryRunSummary,
    pub change_groups: Vec<ChangeGroup>,
    pub impact_analysis: ImpactAnalysis,
    pub preview_modes: Vec<PreviewMode>,
    pub user_guidance: UserGuidance,
    pub safety_assessment: SafetyAssessment,
}

/// High-level summary of all proposed changes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DryRunSummary {
    pub total_changes: usize,
    pub high_confidence_changes: usize,
    pub low_risk_changes: usize,
    pub estimated_improvement: QualityImprovement,
    pub time_estimate: TimeEstimate,
    pub recommendation: OverallRecommendation,
}

/// Grouped changes for better organization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChangeGroup {
    pub group_id: Uuid,
    pub category: ChangeCategory,
    pub title: String,
    pub description: String,
    pub changes: Vec<ProposedChange>,
    pub group_impact: GroupImpact,
    pub apply_together: bool, // Whether changes in this group should be applied as a unit
}

/// Categories of changes for organization
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum ChangeCategory {
    GrammarAndSpelling,
    ReadabilityImprovements,
    StructuralChanges,
    ContentAdditions,
    ContentRemovals,
    Formatting,
    Accessibility,
}

/// A specific proposed change with full preview information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProposedChange {
    pub change_id: Uuid,
    pub fix_type: RemediationFixType,
    pub title: String,
    pub description: String,
    pub before_preview: ContentPreview,
    pub after_preview: ContentPreview,
    pub diff_preview: DiffPreview,
    pub confidence: ConfidenceLevel,
    pub risk_level: RiskLevel,
    pub impact_score: f64, // 0.0 to 1.0
    pub reversible: bool,
    pub dependencies: Vec<Uuid>, // Other changes this depends on
    pub alternatives: Vec<AlternativeChange>,
}

/// Preview of content before or after a change
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentPreview {
    pub preview_text: String,
    pub context_before: String,
    pub context_after: String,
    pub affected_sections: Vec<String>,
    pub word_count_change: i32,
    pub readability_change: Option<f64>,
}

/// Detailed diff preview with highlighting
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiffPreview {
    pub unified_diff: String,
    pub highlighted_changes: Vec<HighlightedChange>,
    pub summary: String,
    pub change_type: DiffType,
}

/// Type of diff change
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum DiffType {
    Addition,
    Deletion,
    Modification,
    Replacement,
    Reordering,
}

/// Type of change for tracking purposes
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ChangeType {
    Addition,
    Deletion,
    Modification,
    Reordering,
}

/// Individual highlighted change in the diff
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HighlightedChange {
    pub change_type: DiffType,
    pub text: String,
    pub line_number: Option<usize>,
    pub character_position: Option<usize>,
    pub explanation: String,
}

/// Alternative way to apply a change
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlternativeChange {
    pub alternative_id: Uuid,
    pub title: String,
    pub description: String,
    pub preview: ContentPreview,
    pub confidence: ConfidenceLevel,
    pub trade_offs: Vec<String>,
}

/// Analysis of the overall impact of all changes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImpactAnalysis {
    pub quality_improvement: QualityImprovement,
    pub readability_impact: ReadabilityImpact,
    pub structural_impact: StructuralImpact,
    pub content_integrity: ContentIntegrityAssessment,
    pub potential_risks: Vec<RiskAssessment>,
    pub benefits: Vec<BenefitAssessment>,
}

/// Expected quality improvement metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QualityImprovement {
    pub overall_score_change: f64, // Expected change in overall quality score
    pub category_improvements: HashMap<String, f64>,
    pub improvement_confidence: ConfidenceLevel,
    pub improvement_areas: Vec<String>,
}

/// Impact on content readability
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReadabilityImpact {
    pub flesch_score_change: Option<f64>,
    pub grade_level_change: Option<f64>,
    pub sentence_length_change: f64,
    pub word_complexity_change: f64,
    pub overall_readability_verdict: ReadabilityVerdict,
}

/// Verdict on readability changes
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ReadabilityVerdict {
    SignificantImprovement,
    ModerateImprovement,
    MinorImprovement,
    NoChange,
    MinorDegradation,
    SignificantConcern,
}

/// Impact on content structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StructuralImpact {
    pub organization_improvement: f64,
    pub flow_improvement: f64,
    pub section_changes: Vec<SectionChange>,
    pub heading_changes: Vec<HeadingChange>,
    pub overall_structure_verdict: StructureVerdict,
}

/// Verdict on structural changes
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum StructureVerdict {
    GreatlyImproved,
    Improved,
    NoChange,
    SlightlyWorsened,
    SignificantlyConcerning,
}

/// Changes to content sections
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SectionChange {
    pub section_name: String,
    pub change_type: SectionChangeType,
    pub impact_description: String,
}

/// Type of section change
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SectionChangeType {
    Added,
    Removed,
    Reordered,
    ContentModified,
    HeadingChanged,
}

/// Changes to headings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeadingChange {
    pub old_heading: Option<String>,
    pub new_heading: String,
    pub level_change: i32, // Change in heading level (h1, h2, etc.)
    pub impact_description: String,
}

/// Assessment of content integrity after changes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentIntegrityAssessment {
    pub meaning_preservation: f64, // 0.0 to 1.0
    pub factual_accuracy_risk: RiskLevel,
    pub context_preservation: f64,
    pub tone_consistency: f64,
    pub learning_objective_alignment: f64,
    pub integrity_verdict: IntegrityVerdict,
}

/// Verdict on content integrity
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum IntegrityVerdict {
    FullyPreserved,
    WellPreserved,
    MostlyPreserved,
    SomeRisk,
    HighRisk,
}

/// Assessment of potential risks
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskAssessment {
    pub risk_type: RiskType,
    pub severity: RiskLevel,
    pub description: String,
    pub mitigation: Option<String>,
    pub affected_areas: Vec<String>,
}

/// Types of risks from changes
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum RiskType {
    MeaningChange,
    FactualError,
    ToneShift,
    StructuralBreakage,
    FormattingIssues,
    AccessibilityReduction,
    LearningObjectiveMismatch,
}

/// Assessment of benefits
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BenefitAssessment {
    pub benefit_type: BenefitType,
    pub impact_level: ImpactLevel,
    pub description: String,
    pub measurable_improvement: Option<f64>,
}

/// Types of benefits from changes
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum BenefitType {
    ImprovedReadability,
    BetterOrganization,
    ClearerLanguage,
    EnhancedAccessibility,
    CorrectErrors,
    BetterFlow,
    IncreasedEngagement,
}

/// Impact level for benefits
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ImpactLevel {
    High,
    Medium,
    Low,
}

/// Different modes for previewing changes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PreviewMode {
    pub mode_name: String,
    pub description: String,
    pub preview_content: String,
    pub highlighted_changes: Vec<HighlightedChange>,
    pub best_for: Vec<String>, // What this preview mode is best for
}

/// User guidance for the dry run
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserGuidance {
    pub recommendation: OverallRecommendation,
    pub suggested_actions: Vec<SuggestedAction>,
    pub warnings: Vec<String>,
    pub tips: Vec<String>,
    pub next_steps: Vec<String>,
}

/// Overall recommendation for the changes
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum OverallRecommendation {
    ApplyAll,        // All changes look good
    ApplyMost,       // Most changes are good, review a few
    ReviewCarefully, // Many changes need careful review
    ApplySelectively,// Only apply certain types of changes
    DoNotApply,      // Too risky, don't apply
}

/// Suggested action for the user
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SuggestedAction {
    pub action_type: ActionType,
    pub title: String,
    pub description: String,
    pub priority: ActionPriority,
    pub estimated_time: String,
}

/// Type of suggested action
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ActionType {
    ApplyChanges,
    ReviewChanges,
    ModifyChanges,
    RejectChanges,
    GetMoreInfo,
    ConsultExpert,
}

/// Priority of suggested actions
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum ActionPriority {
    Critical,
    High,
    Medium,
    Low,
}

/// Safety assessment of all proposed changes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SafetyAssessment {
    pub overall_safety: SafetyLevel,
    pub automated_checks: Vec<SafetyCheck>,
    pub manual_review_needed: bool,
    pub backup_recommended: bool,
    pub rollback_plan: Option<RollbackPlan>,
}

/// Safety level assessment
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SafetyLevel {
    VerySafe,      // Minimal risk, can apply confidently
    Safe,          // Low risk, safe to apply
    Moderate,      // Some risk, review recommended
    Risky,         // Higher risk, careful review needed
    HighRisk,      // High risk, expert review recommended
}

/// Individual safety check result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SafetyCheck {
    pub check_name: String,
    pub passed: bool,
    pub details: String,
    pub recommendation: Option<String>,
}

/// Plan for rolling back changes if needed
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RollbackPlan {
    pub backup_location: String,
    pub rollback_instructions: Vec<String>,
    pub estimated_rollback_time: String,
    pub automation_available: bool,
}

/// Time estimates for applying changes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimeEstimate {
    pub total_time_minutes: u32,
    pub breakdown: HashMap<ChangeCategory, u32>,
    pub user_review_time: u32,
    pub automated_time: u32,
    pub confidence: ConfidenceLevel,
}

/// Impact at the group level
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GroupImpact {
    pub improvement_score: f64,
    pub risk_score: f64,
    pub user_effort_required: EffortLevel,
    pub reversibility: ReversibilityLevel,
}

/// Level of user effort required
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum EffortLevel {
    None,        // Fully automated
    Minimal,     // Just review and approve
    Low,         // Some manual adjustments
    Medium,      // Moderate manual work
    High,        // Significant manual work
}

/// How easily changes can be reversed
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ReversibilityLevel {
    FullyReversible,     // Can be undone perfectly
    MostlyReversible,    // Can be mostly undone
    PartiallyReversible, // Some aspects can be undone
    DifficultToReverse,  // Hard to undo
    Irreversible,        // Cannot be undone
}

/// Result of applying changes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApplyChangesResult {
    pub success: bool,
    pub applied_changes: Vec<AppliedChange>,
    pub failed_changes: Vec<FailedChange>,
    pub final_content: Option<GeneratedContent>,
    pub backup_location: Option<String>,
    pub quality_improvement: Option<f64>,
}

/// Successfully applied change
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppliedChange {
    pub change_id: Uuid,
    pub title: String,
    pub applied_at: chrono::DateTime<chrono::Utc>,
}

/// Failed change application
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FailedChange {
    pub change_id: Uuid,
    pub title: String,
    pub error_message: String,
}

/// Summary of a dry run session
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DryRunSessionSummary {
    pub session_id: Uuid,
    pub content_title: String,
    pub content_type: String,
    pub total_changes: usize,
    pub high_priority_changes: usize,
    pub estimated_improvement: f64,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub expires_at: chrono::DateTime<chrono::Utc>,
    pub status: DryRunSessionStatus,
}

/// Status of a dry run session
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum DryRunSessionStatus {
    Active,
    Expired,
    Applied,
    Cancelled,
}

/// Mode for applying changes
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ApplyMode {
    Immediate,    // Apply all at once
    Incremental,  // Apply one group at a time
    Preview,      // Just show what would be applied
}

impl DryRunManager {
    /// Create a new dry run manager with default configuration
    pub fn new() -> Self {
        Self {
            preview_cache: HashMap::new(),
            config: DryRunConfig::default(),
        }
    }
    
    /// Check if there's a cached session for similar content
    pub fn has_cached_session(&self, _content: &GeneratedContent) -> bool {
        // Simple implementation - in reality would check content similarity
        false
    }
    
    /// Get a session by ID
    pub fn get_session(&self, session_id: &Uuid) -> Option<&DryRunSession> {
        self.preview_cache.get(session_id)
    }
    
    /// Update session configuration
    pub fn update_session_config(&mut self, session_id: &Uuid, config: DryRunConfig) -> Result<()> {
        if let Some(_session) = self.preview_cache.get_mut(session_id) {
            // Update session would require regenerating some parts
            // For now, just update the global config
            self.config = config;
            Ok(())
        } else {
            Err(anyhow::anyhow!("Session not found"))
        }
    }
    
    /// Apply selected changes
    pub fn apply_changes(
        &mut self,
        _session_id: &Uuid,
        _selected_groups: &[Uuid],
        _selected_changes: &[Uuid],
        _apply_mode: ApplyMode,
        _backup_original: bool,
    ) -> Result<ApplyChangesResult> {
        // Simplified implementation
        Ok(ApplyChangesResult {
            success: true,
            applied_changes: vec![],
            failed_changes: vec![],
            final_content: None,
            backup_location: None,
            quality_improvement: Some(0.1),
        })
    }
    
    /// List active sessions
    pub fn list_active_sessions(&self) -> Vec<DryRunSessionSummary> {
        let now = chrono::Utc::now();
        self.preview_cache.iter()
            .filter(|(_, session)| session.expires_at > now)
            .map(|(session_id, session)| DryRunSessionSummary {
                session_id: *session_id,
                content_title: "Generated Content".to_string(), // metadata.title doesn't exist
                content_type: format!("{:?}", session.original_content.content_type),
                total_changes: session.preview_results.change_groups.iter()
                    .map(|g| g.changes.len())
                    .sum(),
                high_priority_changes: 0, // Would calculate based on priority
                estimated_improvement: session.preview_results.overall_summary.estimated_improvement.overall_score_change,
                created_at: session.created_at,
                expires_at: session.expires_at,
                status: if session.expires_at > now { 
                    DryRunSessionStatus::Active 
                } else { 
                    DryRunSessionStatus::Expired 
                },
            })
            .collect()
    }
    
    /// Cancel a session
    pub fn cancel_session(&mut self, session_id: &Uuid) -> Result<()> {
        if self.preview_cache.remove(session_id).is_some() {
            Ok(())
        } else {
            Err(anyhow::anyhow!("Session not found"))
        }
    }
    
    /// Create a dry run session
    pub fn create_dry_run(
        &mut self,
        session_id: Uuid,
        content: GeneratedContent,
        validation_results: Vec<ValidationResult>,
        _remediation_suggestions: Vec<RemediationSuggestion>,
        user_settings: Option<PersonalizationSettings>,
        _config: DryRunConfig,
    ) -> Result<DryRunResults> {
        // Simplified implementation - create mock results
        let overall_summary = DryRunSummary {
            total_changes: 5,
            high_confidence_changes: 3,
            low_risk_changes: 4,
            estimated_improvement: QualityImprovement {
                overall_score_change: 0.15,
                category_improvements: HashMap::new(),
                improvement_confidence: ConfidenceLevel::Medium,
                improvement_areas: vec!["Readability".to_string()],
            },
            time_estimate: TimeEstimate {
                total_time_minutes: 15,
                breakdown: HashMap::new(),
                user_review_time: 5,
                automated_time: 10,
                confidence: ConfidenceLevel::Medium,
            },
            recommendation: OverallRecommendation::ApplyMost,
        };
        
        let results = DryRunResults {
            overall_summary,
            change_groups: vec![],
            impact_analysis: ImpactAnalysis {
                quality_improvement: QualityImprovement {
                    overall_score_change: 0.15,
                    category_improvements: HashMap::new(),
                    improvement_confidence: ConfidenceLevel::Medium,
                    improvement_areas: vec!["Readability".to_string()],
                },
                readability_impact: ReadabilityImpact {
                    flesch_score_change: Some(5.0),
                    grade_level_change: Some(-0.5),
                    sentence_length_change: -2.0,
                    word_complexity_change: -0.1,
                    overall_readability_verdict: ReadabilityVerdict::ModerateImprovement,
                },
                structural_impact: StructuralImpact {
                    organization_improvement: 0.2,
                    flow_improvement: 0.15,
                    section_changes: vec![],
                    heading_changes: vec![],
                    overall_structure_verdict: StructureVerdict::Improved,
                },
                content_integrity: ContentIntegrityAssessment {
                    meaning_preservation: 0.95,
                    factual_accuracy_risk: RiskLevel::Low,
                    context_preservation: 0.9,
                    tone_consistency: 0.85,
                    learning_objective_alignment: 0.9,
                    integrity_verdict: IntegrityVerdict::WellPreserved,
                },
                potential_risks: vec![],
                benefits: vec![],
            },
            preview_modes: vec![],
            user_guidance: UserGuidance {
                recommendation: OverallRecommendation::ApplyMost,
                suggested_actions: vec![],
                warnings: vec![],
                tips: vec![],
                next_steps: vec![],
            },
            safety_assessment: SafetyAssessment {
                overall_safety: SafetyLevel::Safe,
                automated_checks: vec![],
                manual_review_needed: false,
                backup_recommended: true,
                rollback_plan: None,
            },
        };
        
        let session = DryRunSession {
            session_id,
            original_content: content,
            validation_results,
            preview_results: results.clone(),
            created_at: chrono::Utc::now(),
            expires_at: chrono::Utc::now() + chrono::Duration::minutes(self.config.cache_duration_minutes as i64),
            user_settings,
        };
        
        // Cache the session
        self.preview_cache.insert(session_id, session);
        
        Ok(results)
    }
    
    /// Create a dry run manager with custom configuration
    pub fn with_config(config: DryRunConfig) -> Self {
        Self {
            preview_cache: HashMap::new(),
            config,
        }
    }
    
    /// Generate a comprehensive dry run preview
    pub async fn generate_dry_run(
        &mut self,
        content: &GeneratedContent,
        validation_results: &[ValidationResult],
        user_settings: Option<&PersonalizationSettings>,
    ) -> Result<DryRunSession> {
        let session_id = Uuid::new_v4();
        let created_at = chrono::Utc::now();
        let expires_at = created_at + chrono::Duration::minutes(self.config.cache_duration_minutes as i64);
        
        // Generate all proposed changes
        let proposed_changes = self.generate_proposed_changes(content, validation_results).await?;
        
        // Group changes by category
        let change_groups = self.group_changes(proposed_changes)?;
        
        // Analyze overall impact
        let impact_analysis = self.analyze_impact(content, &change_groups)?;
        
        // Generate different preview modes
        let preview_modes = self.generate_preview_modes(content, &change_groups)?;
        
        // Create user guidance
        let user_guidance = self.generate_user_guidance(&change_groups, &impact_analysis, user_settings)?;
        
        // Perform safety assessment
        let safety_assessment = self.assess_safety(&change_groups, &impact_analysis)?;
        
        // Create overall summary
        let overall_summary = self.create_summary(&change_groups, &impact_analysis)?;
        
        let preview_results = DryRunResults {
            overall_summary,
            change_groups,
            impact_analysis,
            preview_modes,
            user_guidance,
            safety_assessment,
        };
        
        let session = DryRunSession {
            session_id,
            original_content: content.clone(),
            validation_results: validation_results.to_vec(),
            preview_results,
            created_at,
            expires_at,
            user_settings: user_settings.cloned(),
        };
        
        // Cache the session
        self.cache_session(session.clone())?;
        
        Ok(session)
    }
    
    /// Apply selected changes from a dry run session
    pub async fn apply_selected_changes(
        &self,
        session_id: Uuid,
        selected_change_ids: &[Uuid],
        content: &mut GeneratedContent,
    ) -> Result<ApplicationResult> {
        let session = self.get_cached_session(session_id)?;
        
        // Validate that changes are still applicable
        self.validate_changes_applicability(&session, content)?;
        
        // Sort changes by dependencies
        let ordered_changes = self.resolve_dependencies(&session, selected_change_ids)?;
        
        let mut application_results = Vec::new();
        let mut successful_changes = 0;
        let original_content = content.content.clone();
        
        // Apply changes in order
        for change_id in ordered_changes {
            let change = self.find_change_in_session(&session, change_id)?;
            
            match self.apply_single_change(content, &change).await {
                Ok(result) => {
                    application_results.push(result);
                    successful_changes += 1;
                },
                Err(e) => {
                    // Log error and continue with other changes
                    application_results.push(ChangeApplicationResult {
                        change_id,
                        success: false,
                        error_message: Some(e.to_string()),
                        applied_content: None,
                        rollback_info: None,
                    });
                }
            }
        }
        
        Ok(ApplicationResult {
            session_id,
            total_changes_requested: selected_change_ids.len(),
            successful_changes,
            failed_changes: selected_change_ids.len() - successful_changes,
            original_content,
            final_content: content.content.clone(),
            individual_results: application_results,
            overall_success: successful_changes > 0,
            rollback_available: true,
        })
    }
    
    /// Get a cached dry run session
    pub fn get_cached_session(&self, session_id: Uuid) -> Result<&DryRunSession> {
        let session = self.preview_cache.get(&session_id)
            .ok_or_else(|| anyhow::anyhow!("Dry run session not found or expired"))?;
        
        // Check if session has expired
        if chrono::Utc::now() > session.expires_at {
            return Err(anyhow::anyhow!("Dry run session has expired"));
        }
        
        Ok(session)
    }
    
    /// Update dry run settings and regenerate if needed
    pub async fn update_settings(
        &mut self,
        session_id: Uuid,
        new_settings: PersonalizationSettings,
    ) -> Result<DryRunSession> {
        let mut session = self.get_cached_session(session_id)?.clone();
        session.user_settings = Some(new_settings.clone());
        
        // Regenerate user guidance and safety assessment with new settings
        session.preview_results.user_guidance = self.generate_user_guidance(
            &session.preview_results.change_groups,
            &session.preview_results.impact_analysis,
            Some(&new_settings),
        )?;
        
        // Update cached session
        self.preview_cache.insert(session_id, session.clone());
        
        Ok(session)
    }
    
    /// Clean up expired sessions
    pub fn cleanup_expired_sessions(&mut self) {
        let now = chrono::Utc::now();
        self.preview_cache.retain(|_, session| session.expires_at > now);
    }
    
    // Private helper methods
    
    async fn generate_proposed_changes(
        &self,
        content: &GeneratedContent,
        validation_results: &[ValidationResult],
    ) -> Result<Vec<ProposedChange>> {
        let mut changes = Vec::new();
        
        // Use remediation manager to generate suggestions
        let mut remediation_manager = RemediationManager::new();
        
        // Extract all issues from validation results
        let issues: Vec<ValidationIssue> = validation_results
            .iter()
            .flat_map(|r| &r.issues)
            .cloned()
            .collect();
        
        // Generate remediation session
        let session = remediation_manager.generate_suggestions(content, &issues, None).await?;
        
        // Convert remediation suggestions to proposed changes
        for suggestion in &session.suggested_fixes {
            let proposed_change = self.convert_suggestion_to_change(content, suggestion)?;
            changes.push(proposed_change);
        }
        
        Ok(changes)
    }
    
    fn convert_suggestion_to_change(
        &self,
        content: &GeneratedContent,
        suggestion: &RemediationSuggestion,
    ) -> Result<ProposedChange> {
        // Create before and after previews
        let before_preview = ContentPreview {
            preview_text: suggestion.preview.before.clone(),
            context_before: self.extract_context(&content.content, &suggestion.preview.before, true)?,
            context_after: self.extract_context(&content.content, &suggestion.preview.before, false)?,
            affected_sections: suggestion.preview.affected_sections.clone(),
            word_count_change: 0, // Will be calculated
            readability_change: None,
        };
        
        let after_preview = ContentPreview {
            preview_text: suggestion.preview.after.clone(),
            context_before: self.extract_context(&suggestion.preview.after, &suggestion.preview.after, true)?,
            context_after: self.extract_context(&suggestion.preview.after, &suggestion.preview.after, false)?,
            affected_sections: suggestion.preview.affected_sections.clone(),
            word_count_change: self.calculate_word_count_change(&suggestion.preview.before, &suggestion.preview.after),
            readability_change: None, // Would be calculated with readability analysis
        };
        
        // Create diff preview
        let diff_preview = self.generate_diff_preview(&suggestion.preview.before, &suggestion.preview.after)?;
        
        Ok(ProposedChange {
            change_id: Uuid::new_v4(),
            fix_type: suggestion.fix_type.clone(),
            title: format!("{:?}", suggestion.fix_type).replace('_', " "),
            description: suggestion.description.clone(),
            before_preview,
            after_preview,
            diff_preview,
            confidence: suggestion.confidence.clone(),
            risk_level: suggestion.risk_level.clone(),
            impact_score: self.calculate_impact_score(&suggestion.confidence, &suggestion.risk_level),
            reversible: self.is_change_reversible(&suggestion.fix_type),
            dependencies: vec![], // Would be calculated based on change relationships
            alternatives: vec![], // Would be generated from suggestion alternatives
        })
    }
    
    fn group_changes(&self, changes: Vec<ProposedChange>) -> Result<Vec<ChangeGroup>> {
        let mut groups: HashMap<ChangeCategory, Vec<ProposedChange>> = HashMap::new();
        
        // Categorize changes
        for change in changes {
            let category = self.categorize_change(&change.fix_type);
            groups.entry(category).or_insert_with(Vec::new).push(change);
        }
        
        // Convert to ChangeGroup structs
        let mut change_groups = Vec::new();
        for (category, changes) in groups {
            let group_impact = self.calculate_group_impact(&changes);
            
            let group = ChangeGroup {
                group_id: Uuid::new_v4(),
                category: category.clone(),
                title: self.get_category_title(&category),
                description: self.get_category_description(&category),
                changes,
                group_impact,
                apply_together: self.should_apply_together(&category),
            };
            
            change_groups.push(group);
        }
        
        // Sort by impact score (highest first)
        change_groups.sort_by(|a, b| {
            b.group_impact.improvement_score.partial_cmp(&a.group_impact.improvement_score)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        
        Ok(change_groups)
    }
    
    fn categorize_change(&self, fix_type: &RemediationFixType) -> ChangeCategory {
        use RemediationFixType::*;
        
        match fix_type {
            FixTypos | CorrectCapitalization | FixGrammarError => ChangeCategory::GrammarAndSpelling,
            ImproveReadability => ChangeCategory::ReadabilityImprovements,
            AddHeadings | ReorganizeContent | FixSectionOrder => ChangeCategory::StructuralChanges,
            AddMissingSection | AddLearningObjectives | AddExamples | ExpandContent => ChangeCategory::ContentAdditions,
            RemoveDuplicates => ChangeCategory::ContentRemovals,
            FormatText => ChangeCategory::Formatting,
            _ => ChangeCategory::ReadabilityImprovements, // Default fallback
        }
    }
    
    fn analyze_impact(&self, content: &GeneratedContent, change_groups: &[ChangeGroup]) -> Result<ImpactAnalysis> {
        // Calculate overall quality improvement
        let total_impact: f64 = change_groups.iter()
            .map(|g| g.group_impact.improvement_score)
            .sum();
        
        let quality_improvement = QualityImprovement {
            overall_score_change: (total_impact / change_groups.len() as f64).min(1.0),
            category_improvements: change_groups.iter()
                .map(|g| (format!("{:?}", g.category), g.group_impact.improvement_score))
                .collect(),
            improvement_confidence: self.calculate_overall_confidence(change_groups),
            improvement_areas: change_groups.iter()
                .map(|g| g.title.clone())
                .collect(),
        };
        
        // Analyze readability impact
        let readability_impact = self.analyze_readability_impact(content, change_groups)?;
        
        // Analyze structural impact
        let structural_impact = self.analyze_structural_impact(change_groups)?;
        
        // Assess content integrity
        let content_integrity = self.assess_content_integrity(change_groups)?;
        
        // Identify risks and benefits
        let potential_risks = self.identify_risks(change_groups)?;
        let benefits = self.identify_benefits(change_groups)?;
        
        Ok(ImpactAnalysis {
            quality_improvement,
            readability_impact,
            structural_impact,
            content_integrity,
            potential_risks,
            benefits,
        })
    }
    
    // Helper methods for calculating various metrics
    
    fn calculate_impact_score(&self, confidence: &ConfidenceLevel, risk: &RiskLevel) -> f64 {
        let confidence_score: f64 = match confidence {
            ConfidenceLevel::VeryHigh => 1.0,
            ConfidenceLevel::High => 0.8,
            ConfidenceLevel::Medium => 0.6,
            ConfidenceLevel::Low => 0.4,
            ConfidenceLevel::VeryLow => 0.2,
        };
        
        let risk_penalty: f64 = match risk {
            RiskLevel::Safe => 0.0,
            RiskLevel::Low => 0.1,
            RiskLevel::Medium => 0.3,
            RiskLevel::High => 0.5,
            RiskLevel::Critical => 0.8,
        };
        
        (confidence_score - risk_penalty).max(0.0)
    }
    
    fn is_change_reversible(&self, fix_type: &RemediationFixType) -> bool {
        use RemediationFixType::*;
        
        match fix_type {
            FixTypos | CorrectCapitalization | FormatText => true,
            RemoveDuplicates => false, // Hard to reverse which duplicates were removed
            ReorganizeContent => false, // Hard to reverse structural changes
            _ => true, // Most changes are reversible
        }
    }
    
    fn extract_context(&self, full_content: &str, target_text: &str, before: bool) -> Result<String> {
        // Find the target text in the full content and extract surrounding context
        if let Some(pos) = full_content.find(target_text) {
            let context_size = 100; // Characters of context
            
            if before {
                let start = pos.saturating_sub(context_size);
                Ok(full_content[start..pos].to_string())
            } else {
                let end = (pos + target_text.len() + context_size).min(full_content.len());
                Ok(full_content[pos + target_text.len()..end].to_string())
            }
        } else {
            Ok("".to_string())
        }
    }
    
    fn calculate_word_count_change(&self, before: &str, after: &str) -> i32 {
        let before_words = before.split_whitespace().count() as i32;
        let after_words = after.split_whitespace().count() as i32;
        after_words - before_words
    }
    
    fn generate_diff_preview(&self, before: &str, after: &str) -> Result<DiffPreview> {
        // Simple diff generation - in a real implementation, you'd use a proper diff library
        let summary = if before == after {
            "No changes".to_string()
        } else if before.len() > after.len() {
            "Content shortened".to_string()
        } else {
            "Content modified".to_string()
        };
        
        let change_type = if before.is_empty() {
            DiffType::Addition
        } else if after.is_empty() {
            DiffType::Deletion
        } else {
            DiffType::Modification
        };
        
        Ok(DiffPreview {
            unified_diff: format!("- {}\n+ {}", before, after),
            highlighted_changes: vec![
                HighlightedChange {
                    change_type: change_type.clone(),
                    text: if change_type == DiffType::Addition { after.to_string() } else { before.to_string() },
                    line_number: Some(1),
                    character_position: Some(0),
                    explanation: "Text modification".to_string(),
                }
            ],
            summary,
            change_type,
        })
    }
    
    // Additional helper methods would be implemented here...
    
    fn cache_session(&mut self, session: DryRunSession) -> Result<()> {
        // Clean up old sessions if cache is full
        if self.preview_cache.len() >= self.config.max_cached_sessions {
            self.cleanup_expired_sessions();
            
            // If still full, remove oldest session
            if self.preview_cache.len() >= self.config.max_cached_sessions {
                if let Some(oldest_id) = self.preview_cache.iter()
                    .min_by_key(|(_, s)| s.created_at)
                    .map(|(id, _)| *id) {
                    self.preview_cache.remove(&oldest_id);
                }
            }
        }
        
        self.preview_cache.insert(session.session_id, session);
        Ok(())
    }
    
    // Placeholder implementations for remaining methods
    fn generate_preview_modes(&self, _content: &GeneratedContent, _change_groups: &[ChangeGroup]) -> Result<Vec<PreviewMode>> {
        Ok(vec![
            PreviewMode {
                mode_name: "Side-by-side".to_string(),
                description: "Shows before and after content side by side".to_string(),
                preview_content: "".to_string(),
                highlighted_changes: vec![],
                best_for: vec!["Detailed review".to_string(), "Precise changes".to_string()],
            }
        ])
    }
    
    fn generate_user_guidance(&self, _change_groups: &[ChangeGroup], impact_analysis: &ImpactAnalysis, _user_settings: Option<&PersonalizationSettings>) -> Result<UserGuidance> {
        let recommendation = if impact_analysis.quality_improvement.overall_score_change > 0.8 {
            OverallRecommendation::ApplyAll
        } else if impact_analysis.quality_improvement.overall_score_change > 0.5 {
            OverallRecommendation::ApplyMost
        } else {
            OverallRecommendation::ReviewCarefully
        };
        
        Ok(UserGuidance {
            recommendation,
            suggested_actions: vec![],
            warnings: vec![],
            tips: vec!["Review changes carefully before applying".to_string()],
            next_steps: vec!["Apply selected changes".to_string()],
        })
    }
    
    fn assess_safety(&self, _change_groups: &[ChangeGroup], _impact_analysis: &ImpactAnalysis) -> Result<SafetyAssessment> {
        Ok(SafetyAssessment {
            overall_safety: SafetyLevel::Safe,
            automated_checks: vec![],
            manual_review_needed: false,
            backup_recommended: true,
            rollback_plan: None,
        })
    }
    
    fn create_summary(&self, change_groups: &[ChangeGroup], _impact_analysis: &ImpactAnalysis) -> Result<DryRunSummary> {
        let total_changes = change_groups.iter().map(|g| g.changes.len()).sum();
        
        Ok(DryRunSummary {
            total_changes,
            high_confidence_changes: 0,
            low_risk_changes: 0,
            estimated_improvement: QualityImprovement {
                overall_score_change: 0.0,
                category_improvements: HashMap::new(),
                improvement_confidence: ConfidenceLevel::Medium,
                improvement_areas: vec![],
            },
            time_estimate: TimeEstimate {
                total_time_minutes: 10,
                breakdown: HashMap::new(),
                user_review_time: 5,
                automated_time: 5,
                confidence: ConfidenceLevel::Medium,
            },
            recommendation: OverallRecommendation::ReviewCarefully,
        })
    }
    
    // Additional placeholder methods
    fn calculate_group_impact(&self, _changes: &[ProposedChange]) -> GroupImpact {
        GroupImpact {
            improvement_score: 0.5,
            risk_score: 0.2,
            user_effort_required: EffortLevel::Low,
            reversibility: ReversibilityLevel::MostlyReversible,
        }
    }
    
    fn get_category_title(&self, category: &ChangeCategory) -> String {
        match category {
            ChangeCategory::GrammarAndSpelling => "Grammar & Spelling",
            ChangeCategory::ReadabilityImprovements => "Readability Improvements",
            ChangeCategory::StructuralChanges => "Structural Changes",
            ChangeCategory::ContentAdditions => "Content Additions",
            ChangeCategory::ContentRemovals => "Content Removals",
            ChangeCategory::Formatting => "Formatting",
            ChangeCategory::Accessibility => "Accessibility",
        }.to_string()
    }
    
    fn get_category_description(&self, category: &ChangeCategory) -> String {
        match category {
            ChangeCategory::GrammarAndSpelling => "Fixes for grammar, spelling, and language errors",
            ChangeCategory::ReadabilityImprovements => "Changes to make content easier to read and understand",
            ChangeCategory::StructuralChanges => "Modifications to content organization and structure",
            ChangeCategory::ContentAdditions => "New content being added to improve completeness",
            ChangeCategory::ContentRemovals => "Content being removed to eliminate redundancy",
            ChangeCategory::Formatting => "Formatting and presentation improvements",
            ChangeCategory::Accessibility => "Changes to improve accessibility for all learners",
        }.to_string()
    }
    
    fn should_apply_together(&self, category: &ChangeCategory) -> bool {
        matches!(category, ChangeCategory::StructuralChanges | ChangeCategory::Formatting)
    }
    
    fn calculate_overall_confidence(&self, _change_groups: &[ChangeGroup]) -> ConfidenceLevel {
        ConfidenceLevel::Medium // Simplified calculation
    }
    
    fn analyze_readability_impact(&self, _content: &GeneratedContent, _change_groups: &[ChangeGroup]) -> Result<ReadabilityImpact> {
        Ok(ReadabilityImpact {
            flesch_score_change: Some(5.0),
            grade_level_change: Some(-0.5),
            sentence_length_change: -2.0,
            word_complexity_change: -0.1,
            overall_readability_verdict: ReadabilityVerdict::ModerateImprovement,
        })
    }
    
    fn analyze_structural_impact(&self, _change_groups: &[ChangeGroup]) -> Result<StructuralImpact> {
        Ok(StructuralImpact {
            organization_improvement: 0.3,
            flow_improvement: 0.2,
            section_changes: vec![],
            heading_changes: vec![],
            overall_structure_verdict: StructureVerdict::Improved,
        })
    }
    
    fn assess_content_integrity(&self, _change_groups: &[ChangeGroup]) -> Result<ContentIntegrityAssessment> {
        Ok(ContentIntegrityAssessment {
            meaning_preservation: 0.95,
            factual_accuracy_risk: RiskLevel::Low,
            context_preservation: 0.90,
            tone_consistency: 0.85,
            learning_objective_alignment: 0.90,
            integrity_verdict: IntegrityVerdict::WellPreserved,
        })
    }
    
    fn identify_risks(&self, _change_groups: &[ChangeGroup]) -> Result<Vec<RiskAssessment>> {
        Ok(vec![])
    }
    
    fn identify_benefits(&self, _change_groups: &[ChangeGroup]) -> Result<Vec<BenefitAssessment>> {
        Ok(vec![
            BenefitAssessment {
                benefit_type: BenefitType::ImprovedReadability,
                impact_level: ImpactLevel::Medium,
                description: "Content will be easier to read".to_string(),
                measurable_improvement: Some(0.15),
            }
        ])
    }
    
    fn validate_changes_applicability(&self, _session: &DryRunSession, _content: &GeneratedContent) -> Result<()> {
        Ok(()) // Would check if content has changed since dry run was generated
    }
    
    fn resolve_dependencies(&self, _session: &DryRunSession, change_ids: &[Uuid]) -> Result<Vec<Uuid>> {
        Ok(change_ids.to_vec()) // Would implement dependency resolution
    }
    
    fn find_change_in_session<'a>(&self, session: &'a DryRunSession, change_id: Uuid) -> Result<&'a ProposedChange> {
        for group in &session.preview_results.change_groups {
            for change in &group.changes {
                if change.change_id == change_id {
                    return Ok(change);
                }
            }
        }
        Err(anyhow::anyhow!("Change not found in session"))
    }
    
    async fn apply_single_change(&self, content: &mut GeneratedContent, change: &ProposedChange) -> Result<ChangeApplicationResult> {
        // Apply the change to the content
        content.content = content.content.replace(&change.before_preview.preview_text, &change.after_preview.preview_text);
        
        Ok(ChangeApplicationResult {
            change_id: change.change_id,
            success: true,
            error_message: None,
            applied_content: Some(change.after_preview.preview_text.clone()),
            rollback_info: Some(change.before_preview.preview_text.clone()),
        })
    }
}


/// Result of applying changes from a dry run
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApplicationResult {
    pub session_id: Uuid,
    pub total_changes_requested: usize,
    pub successful_changes: usize,
    pub failed_changes: usize,
    pub original_content: String,
    pub final_content: String,
    pub individual_results: Vec<ChangeApplicationResult>,
    pub overall_success: bool,
    pub rollback_available: bool,
}

/// Result of applying a single change
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChangeApplicationResult {
    pub change_id: Uuid,
    pub success: bool,
    pub error_message: Option<String>,
    pub applied_content: Option<String>,
    pub rollback_info: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dry_run_manager_creation() {
        let manager = DryRunManager::new();
        assert_eq!(manager.config.max_cached_sessions, 10);
        assert_eq!(manager.config.cache_duration_minutes, 30);
    }
    
    #[test]
    fn test_change_categorization() {
        let manager = DryRunManager::new();
        
        assert_eq!(
            manager.categorize_change(&RemediationFixType::FixTypos),
            ChangeCategory::GrammarAndSpelling
        );
        
        assert_eq!(
            manager.categorize_change(&RemediationFixType::AddHeadings),
            ChangeCategory::StructuralChanges
        );
        
        assert_eq!(
            manager.categorize_change(&RemediationFixType::ImproveReadability),
            ChangeCategory::ReadabilityImprovements
        );
    }
    
    #[test]
    fn test_impact_score_calculation() {
        let manager = DryRunManager::new();
        
        let high_confidence_low_risk = manager.calculate_impact_score(
            &ConfidenceLevel::High,
            &RiskLevel::Low
        );
        assert!(high_confidence_low_risk > 0.6);
        
        let low_confidence_high_risk = manager.calculate_impact_score(
            &ConfidenceLevel::Low,
            &RiskLevel::High
        );
        assert!(low_confidence_high_risk < 0.2);
    }
}