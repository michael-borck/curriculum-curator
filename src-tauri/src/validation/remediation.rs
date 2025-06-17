use super::validators::*;
use crate::content::{GeneratedContent, ContentType};
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Remediation-specific user preferences
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RemediationPreferences {
    pub preferred_fix_types: Vec<RemediationFixType>,
    pub rejected_fix_types: Vec<RemediationFixType>,
    pub confidence_threshold: ConfidenceLevel,
    pub risk_tolerance: RiskLevel,
    pub auto_apply_preferences: HashMap<RemediationFixType, bool>,
    pub content_type_preferences: HashMap<ContentType, Vec<RemediationFixType>>,
}

impl Default for RemediationPreferences {
    fn default() -> Self {
        Self {
            preferred_fix_types: vec![
                RemediationFixType::FixTypos,
                RemediationFixType::CorrectCapitalization,
                RemediationFixType::RemoveDuplicates,
            ],
            rejected_fix_types: vec![],
            confidence_threshold: ConfidenceLevel::Medium,
            risk_tolerance: RiskLevel::Low,
            auto_apply_preferences: HashMap::new(),
            content_type_preferences: HashMap::new(),
        }
    }
}

/// Auto-remediation system with user approval workflow
#[derive(Debug, Clone)]
pub struct RemediationManager {
    pending_fixes: HashMap<Uuid, RemediationSession>,
    approved_fixes: HashMap<Uuid, RemediationSession>,
    config: RemediationConfig,
}

/// Configuration for the remediation system
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RemediationConfig {
    /// Enable automatic application of safe fixes
    pub auto_apply_safe_fixes: bool,
    /// Maximum number of fixes to suggest per session
    pub max_suggestions_per_session: usize,
    /// Severity threshold for auto-fix suggestions
    pub auto_fix_severity_threshold: IssueSeverity,
    /// Types of fixes that can be applied automatically
    pub auto_applicable_fix_types: Vec<RemediationFixType>,
    /// Require user approval for structural changes
    pub require_approval_for_structure: bool,
    /// Enable learning from user decisions
    pub enable_user_preference_learning: bool,
}

/// A remediation session tracking fixes for specific content
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RemediationSession {
    pub session_id: Uuid,
    pub content_id: String,
    pub content_type: ContentType,
    pub suggested_fixes: Vec<RemediationSuggestion>,
    pub applied_fixes: Vec<AppliedFix>,
    pub user_decisions: Vec<UserDecision>,
    pub status: SessionStatus,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub updated_at: chrono::DateTime<chrono::Utc>,
}

/// Status of a remediation session
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SessionStatus {
    Pending,           // Awaiting user review
    InProgress,        // User is reviewing fixes
    PartiallyApplied,  // Some fixes applied, others pending
    Completed,         // All decisions made
    Cancelled,         // User cancelled the session
}

/// A specific remediation suggestion with context
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RemediationSuggestion {
    pub suggestion_id: Uuid,
    pub issue: ValidationIssue,
    pub fix_type: RemediationFixType,
    pub description: String,
    pub preview: RemediationPreview,
    pub confidence: ConfidenceLevel,
    pub risk_level: RiskLevel,
    pub requires_approval: bool,
    pub estimated_impact: ImpactAssessment,
    pub alternatives: Vec<AlternativeFix>,
}

/// Types of automatic fixes available
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum RemediationFixType {
    // Content fixes
    AddMissingSection,
    FixGrammarError,
    StandardizeTerminology,
    ImproveReadability,
    
    // Structure fixes
    AddHeadings,
    ReorganizeContent,
    FixSectionOrder,
    
    // Alignment fixes
    AlignObjectives,
    AddMissingTopics,
    StandardizeAssessment,
    
    // Completeness fixes
    AddLearningObjectives,
    ExpandContent,
    AddExamples,
    
    // Safety fixes (can be auto-applied)
    FixTypos,
    CorrectCapitalization,
    RemoveDuplicates,
    FormatText,
}

/// Confidence level in the suggested fix
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, PartialOrd)]
pub enum ConfidenceLevel {
    VeryHigh,    // 90%+ confidence
    High,        // 80-90% confidence
    Medium,      // 60-80% confidence
    Low,         // 40-60% confidence
    VeryLow,     // <40% confidence
}

/// Risk level of applying the fix
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, PartialOrd)]
pub enum RiskLevel {
    Safe,        // No risk of breaking content
    Low,         // Minimal risk, easily reversible
    Medium,      // Some risk, requires careful review
    High,        // Significant risk, may change meaning
    Critical,    // High risk, could break content
}

/// Preview of what the fix will change
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RemediationPreview {
    pub before: String,
    pub after: String,
    pub diff_highlights: Vec<DiffHighlight>,
    pub affected_sections: Vec<String>,
    pub content_location: Option<ContentLocation>,
}

/// Highlighted differences in the preview
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiffHighlight {
    pub range: (usize, usize),
    pub change_type: ChangeType,
    pub description: String,
}

/// Type of change in a diff
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ChangeType {
    Addition,
    Deletion,
    Modification,
    Formatting,
}

/// Assessment of the fix's impact
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImpactAssessment {
    pub educational_effectiveness: f64,  // 0.0 to 1.0
    pub readability_improvement: f64,
    pub structure_improvement: f64,
    pub consistency_improvement: f64,
    pub potential_drawbacks: Vec<String>,
    pub benefits: Vec<String>,
}

/// Alternative fix options
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlternativeFix {
    pub fix_id: Uuid,
    pub description: String,
    pub preview: RemediationPreview,
    pub confidence: ConfidenceLevel,
    pub risk_level: RiskLevel,
}

/// Record of an applied fix
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppliedFix {
    pub fix_id: Uuid,
    pub suggestion_id: Uuid,
    pub applied_at: chrono::DateTime<chrono::Utc>,
    pub before_content: String,
    pub after_content: String,
    pub user_approved: bool,
    pub auto_applied: bool,
    pub success: bool,
    pub error_message: Option<String>,
}

/// User decision on a remediation suggestion
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserDecision {
    pub suggestion_id: Uuid,
    pub decision: DecisionType,
    pub alternative_chosen: Option<Uuid>,
    pub user_feedback: Option<String>,
    pub decided_at: chrono::DateTime<chrono::Utc>,
}

/// Types of user decisions
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum DecisionType {
    Approve,
    Reject,
    ModifyAndApprove,
    RequestAlternatives,
    SkipForNow,
}


impl Default for RemediationConfig {
    fn default() -> Self {
        Self {
            auto_apply_safe_fixes: true,
            max_suggestions_per_session: 10,
            auto_fix_severity_threshold: IssueSeverity::Warning,
            auto_applicable_fix_types: vec![
                RemediationFixType::FixTypos,
                RemediationFixType::CorrectCapitalization,
                RemediationFixType::RemoveDuplicates,
                RemediationFixType::FormatText,
            ],
            require_approval_for_structure: true,
            enable_user_preference_learning: true,
        }
    }
}

impl RemediationManager {
    pub fn new() -> Self {
        Self::with_config(RemediationConfig::default())
    }
    
    pub fn with_config(config: RemediationConfig) -> Self {
        Self {
            pending_fixes: HashMap::new(),
            approved_fixes: HashMap::new(),
            config,
        }
    }
    
    /// Generate remediation suggestions from validation issues
    pub async fn generate_suggestions(
        &mut self,
        content: &GeneratedContent,
        issues: &[ValidationIssue],
        user_preferences: Option<&RemediationPreferences>,
    ) -> Result<RemediationSession> {
        let session_id = Uuid::new_v4();
        let mut suggested_fixes = Vec::new();
        
        // Process each validation issue
        for issue in issues {
            if let Some(suggestions) = self.create_fix_suggestions(content, issue, user_preferences).await? {
                suggested_fixes.extend(suggestions);
            }
        }
        
        // Limit the number of suggestions
        if suggested_fixes.len() > self.config.max_suggestions_per_session {
            suggested_fixes.truncate(self.config.max_suggestions_per_session);
        }
        
        // Sort by priority (confidence and severity)
        suggested_fixes.sort_by(|a, b| {
            let a_priority = self.calculate_priority(&a.issue.severity, &a.confidence);
            let b_priority = self.calculate_priority(&b.issue.severity, &b.confidence);
            b_priority.partial_cmp(&a_priority).unwrap_or(std::cmp::Ordering::Equal)
        });
        
        let session = RemediationSession {
            session_id,
            content_id: format!("{}_{}", content_type_to_string(&content.content_type), chrono::Utc::now().timestamp()),
            content_type: content.content_type.clone(),
            suggested_fixes,
            applied_fixes: Vec::new(),
            user_decisions: Vec::new(),
            status: SessionStatus::Pending,
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        };
        
        self.pending_fixes.insert(session_id, session.clone());
        Ok(session)
    }
    
    /// Create fix suggestions for a specific validation issue
    async fn create_fix_suggestions(
        &self,
        content: &GeneratedContent,
        issue: &ValidationIssue,
        user_preferences: Option<&RemediationPreferences>,
    ) -> Result<Option<Vec<RemediationSuggestion>>> {
        let mut suggestions = Vec::new();
        
        // Determine fix type based on issue type
        let fix_types = self.get_applicable_fix_types(&issue.issue_type, &issue.severity);
        
        for fix_type in fix_types {
            // Check user preferences
            if let Some(prefs) = user_preferences {
                if prefs.rejected_fix_types.contains(&fix_type) {
                    continue;
                }
            }
            
            if let Some(suggestion) = self.create_specific_suggestion(content, issue, fix_type).await? {
                suggestions.push(suggestion);
            }
        }
        
        if suggestions.is_empty() {
            Ok(None)
        } else {
            Ok(Some(suggestions))
        }
    }
    
    /// Get applicable fix types for an issue type and severity
    fn get_applicable_fix_types(&self, issue_type: &IssueType, severity: &IssueSeverity) -> Vec<RemediationFixType> {
        match issue_type {
            IssueType::Grammar => vec![
                RemediationFixType::FixGrammarError,
                RemediationFixType::FixTypos,
                RemediationFixType::CorrectCapitalization,
            ],
            IssueType::Spelling => vec![
                RemediationFixType::FixTypos,
                RemediationFixType::CorrectCapitalization,
            ],
            IssueType::Structure => vec![
                RemediationFixType::AddMissingSection,
                RemediationFixType::AddHeadings,
                RemediationFixType::ReorganizeContent,
                RemediationFixType::FixSectionOrder,
            ],
            IssueType::Readability => vec![
                RemediationFixType::ImproveReadability,
                RemediationFixType::AddHeadings,
                RemediationFixType::FormatText,
            ],
            IssueType::Completeness => vec![
                RemediationFixType::AddMissingSection,
                RemediationFixType::ExpandContent,
                RemediationFixType::AddExamples,
                RemediationFixType::AddLearningObjectives,
            ],
            IssueType::Consistency => vec![
                RemediationFixType::StandardizeTerminology,
                RemediationFixType::StandardizeAssessment,
            ],
            IssueType::LearningObjectives => vec![
                RemediationFixType::AddLearningObjectives,
                RemediationFixType::AlignObjectives,
            ],
            IssueType::PedagogicalAlignment => vec![
                RemediationFixType::AlignObjectives,
                RemediationFixType::ReorganizeContent,
                RemediationFixType::AddMissingTopics,
            ],
            _ => vec![],
        }
    }
    
    /// Create a specific remediation suggestion
    async fn create_specific_suggestion(
        &self,
        content: &GeneratedContent,
        issue: &ValidationIssue,
        fix_type: RemediationFixType,
    ) -> Result<Option<RemediationSuggestion>> {
        let suggestion_id = Uuid::new_v4();
        
        // Generate the fix based on type
        let (preview, confidence, risk_level, alternatives) = match fix_type {
            RemediationFixType::AddMissingSection => {
                self.generate_add_section_fix(content, issue).await?
            },
            RemediationFixType::FixGrammarError => {
                self.generate_grammar_fix(content, issue).await?
            },
            RemediationFixType::StandardizeTerminology => {
                self.generate_terminology_fix(content, issue).await?
            },
            RemediationFixType::ImproveReadability => {
                self.generate_readability_fix(content, issue).await?
            },
            RemediationFixType::AddHeadings => {
                self.generate_heading_fix(content, issue).await?
            },
            RemediationFixType::AddLearningObjectives => {
                self.generate_objectives_fix(content, issue).await?
            },
            RemediationFixType::FixTypos => {
                self.generate_typo_fix(content, issue).await?
            },
            RemediationFixType::CorrectCapitalization => {
                self.generate_capitalization_fix(content, issue).await?
            },
            RemediationFixType::RemoveDuplicates => {
                self.generate_duplicate_removal_fix(content, issue).await?
            },
            RemediationFixType::FormatText => {
                self.generate_formatting_fix(content, issue).await?
            },
            _ => {
                // For other fix types, create a generic suggestion
                self.generate_generic_fix(content, issue, &fix_type).await?
            }
        };
        
        let description = self.generate_fix_description(&fix_type, issue);
        let requires_approval = self.requires_user_approval(&fix_type, &risk_level);
        let impact_assessment = self.assess_fix_impact(content, issue, &fix_type, &preview);
        
        Ok(Some(RemediationSuggestion {
            suggestion_id,
            issue: issue.clone(),
            fix_type,
            description,
            preview,
            confidence,
            risk_level,
            requires_approval,
            estimated_impact: impact_assessment,
            alternatives,
        }))
    }
    
    /// Generate a fix for adding missing sections
    async fn generate_add_section_fix(
        &self,
        content: &GeneratedContent,
        issue: &ValidationIssue,
    ) -> Result<(RemediationPreview, ConfidenceLevel, RiskLevel, Vec<AlternativeFix>)> {
        // Extract section name from issue message
        let section_name = if let Some(section) = issue.message.strip_prefix("Missing required section: ") {
            section
        } else {
            "missing_section"
        };
        
        let template = self.generate_section_template(section_name, &content.content_type);
        let insertion_point = self.find_best_insertion_point(&content.content, section_name);
        
        let before = content.content.clone();
        let after = self.insert_content_at_position(&before, &template, insertion_point);
        
        let preview = RemediationPreview {
            before: self.get_context_around_position(&before, insertion_point, 100),
            after: self.get_context_around_position(&after, insertion_point, 100),
            diff_highlights: vec![
                DiffHighlight {
                    range: (insertion_point, insertion_point + template.len()),
                    change_type: ChangeType::Addition,
                    description: format!("Added {} section", section_name),
                }
            ],
            affected_sections: vec![section_name.to_string()],
            content_location: issue.location.clone(),
        };
        
        // Generate alternatives
        let alternatives = vec![
            AlternativeFix {
                fix_id: Uuid::new_v4(),
                description: format!("Add minimal {} section", section_name),
                preview: self.create_minimal_section_preview(section_name, &content.content_type),
                confidence: ConfidenceLevel::High,
                risk_level: RiskLevel::Safe,
            },
            AlternativeFix {
                fix_id: Uuid::new_v4(),
                description: format!("Add comprehensive {} section", section_name),
                preview: self.create_comprehensive_section_preview(section_name, &content.content_type),
                confidence: ConfidenceLevel::Medium,
                risk_level: RiskLevel::Low,
            }
        ];
        
        Ok((preview, ConfidenceLevel::High, RiskLevel::Low, alternatives))
    }
    
    /// Generate a fix for grammar errors
    async fn generate_grammar_fix(
        &self,
        content: &GeneratedContent,
        issue: &ValidationIssue,
    ) -> Result<(RemediationPreview, ConfidenceLevel, RiskLevel, Vec<AlternativeFix>)> {
        // Simple grammar fixes based on issue message
        let (before_text, after_text, confidence) = if issue.message.contains("Repeated word") {
            let repeated_text = content.content.clone();
            let fixed_text = self.remove_repeated_words(&repeated_text);
            (repeated_text, fixed_text, ConfidenceLevel::VeryHigh)
        } else if issue.message.contains("should start with capital letter") {
            let original = content.content.clone();
            let fixed = self.fix_capitalization(&original);
            (original, fixed, ConfidenceLevel::High)
        } else {
            // Generic grammar fix
            (content.content.clone(), content.content.clone(), ConfidenceLevel::Medium)
        };
        
        let preview = RemediationPreview {
            before: before_text.clone(),
            after: after_text.clone(),
            diff_highlights: self.calculate_diff_highlights(&before_text, &after_text),
            affected_sections: vec!["grammar".to_string()],
            content_location: issue.location.clone(),
        };
        
        Ok((preview, confidence, RiskLevel::Safe, vec![]))
    }
    
    /// Generate other types of fixes (placeholder implementations)
    async fn generate_terminology_fix(&self, content: &GeneratedContent, issue: &ValidationIssue) -> Result<(RemediationPreview, ConfidenceLevel, RiskLevel, Vec<AlternativeFix>)> {
        let preview = RemediationPreview {
            before: content.content.clone(),
            after: content.content.clone(), // TODO: Implement terminology standardization
            diff_highlights: vec![],
            affected_sections: vec!["terminology".to_string()],
            content_location: issue.location.clone(),
        };
        Ok((preview, ConfidenceLevel::Medium, RiskLevel::Low, vec![]))
    }
    
    async fn generate_readability_fix(&self, content: &GeneratedContent, issue: &ValidationIssue) -> Result<(RemediationPreview, ConfidenceLevel, RiskLevel, Vec<AlternativeFix>)> {
        let preview = RemediationPreview {
            before: content.content.clone(),
            after: content.content.clone(), // TODO: Implement readability improvements
            diff_highlights: vec![],
            affected_sections: vec!["readability".to_string()],
            content_location: issue.location.clone(),
        };
        Ok((preview, ConfidenceLevel::Medium, RiskLevel::Low, vec![]))
    }
    
    async fn generate_heading_fix(&self, content: &GeneratedContent, issue: &ValidationIssue) -> Result<(RemediationPreview, ConfidenceLevel, RiskLevel, Vec<AlternativeFix>)> {
        let before = content.content.clone();
        let after = self.add_structure_headings(&before);
        
        let preview = RemediationPreview {
            before,
            after: after.clone(),
            diff_highlights: vec![], // TODO: Calculate actual diff
            affected_sections: vec!["structure".to_string()],
            content_location: issue.location.clone(),
        };
        Ok((preview, ConfidenceLevel::High, RiskLevel::Low, vec![]))
    }
    
    async fn generate_objectives_fix(&self, content: &GeneratedContent, issue: &ValidationIssue) -> Result<(RemediationPreview, ConfidenceLevel, RiskLevel, Vec<AlternativeFix>)> {
        let objectives_template = self.generate_learning_objectives_template(&content.content_type);
        let insertion_point = self.find_objectives_insertion_point(&content.content);
        
        let before = content.content.clone();
        let after = self.insert_content_at_position(&before, &objectives_template, insertion_point);
        
        let preview = RemediationPreview {
            before,
            after,
            diff_highlights: vec![
                DiffHighlight {
                    range: (insertion_point, insertion_point + objectives_template.len()),
                    change_type: ChangeType::Addition,
                    description: "Added learning objectives section".to_string(),
                }
            ],
            affected_sections: vec!["learning_objectives".to_string()],
            content_location: issue.location.clone(),
        };
        Ok((preview, ConfidenceLevel::High, RiskLevel::Low, vec![]))
    }
    
    async fn generate_typo_fix(&self, content: &GeneratedContent, issue: &ValidationIssue) -> Result<(RemediationPreview, ConfidenceLevel, RiskLevel, Vec<AlternativeFix>)> {
        let before = content.content.clone();
        let after = self.fix_common_typos(&before);
        
        let preview = RemediationPreview {
            before,
            after: after.clone(),
            diff_highlights: self.calculate_diff_highlights(&content.content, &after),
            affected_sections: vec!["spelling".to_string()],
            content_location: issue.location.clone(),
        };
        Ok((preview, ConfidenceLevel::High, RiskLevel::Safe, vec![]))
    }
    
    async fn generate_capitalization_fix(&self, content: &GeneratedContent, issue: &ValidationIssue) -> Result<(RemediationPreview, ConfidenceLevel, RiskLevel, Vec<AlternativeFix>)> {
        let before = content.content.clone();
        let after = self.fix_capitalization(&before);
        
        let preview = RemediationPreview {
            before,
            after: after.clone(),
            diff_highlights: self.calculate_diff_highlights(&content.content, &after),
            affected_sections: vec!["capitalization".to_string()],
            content_location: issue.location.clone(),
        };
        Ok((preview, ConfidenceLevel::VeryHigh, RiskLevel::Safe, vec![]))
    }
    
    async fn generate_duplicate_removal_fix(&self, content: &GeneratedContent, issue: &ValidationIssue) -> Result<(RemediationPreview, ConfidenceLevel, RiskLevel, Vec<AlternativeFix>)> {
        let before = content.content.clone();
        let after = self.remove_repeated_words(&before);
        
        let preview = RemediationPreview {
            before,
            after: after.clone(),
            diff_highlights: self.calculate_diff_highlights(&content.content, &after),
            affected_sections: vec!["duplicates".to_string()],
            content_location: issue.location.clone(),
        };
        Ok((preview, ConfidenceLevel::VeryHigh, RiskLevel::Safe, vec![]))
    }
    
    async fn generate_formatting_fix(&self, content: &GeneratedContent, issue: &ValidationIssue) -> Result<(RemediationPreview, ConfidenceLevel, RiskLevel, Vec<AlternativeFix>)> {
        let before = content.content.clone();
        let after = self.improve_formatting(&before);
        
        let preview = RemediationPreview {
            before,
            after,
            diff_highlights: vec![], // TODO: Calculate formatting diff
            affected_sections: vec!["formatting".to_string()],
            content_location: issue.location.clone(),
        };
        Ok((preview, ConfidenceLevel::High, RiskLevel::Safe, vec![]))
    }
    
    async fn generate_generic_fix(&self, content: &GeneratedContent, issue: &ValidationIssue, fix_type: &RemediationFixType) -> Result<(RemediationPreview, ConfidenceLevel, RiskLevel, Vec<AlternativeFix>)> {
        let preview = RemediationPreview {
            before: content.content.clone(),
            after: content.content.clone(),
            diff_highlights: vec![],
            affected_sections: vec![format!("{:?}", fix_type)],
            content_location: issue.location.clone(),
        };
        Ok((preview, ConfidenceLevel::Low, RiskLevel::Medium, vec![]))
    }
    
    /// Helper methods for content manipulation
    fn generate_section_template(&self, section_name: &str, content_type: &ContentType) -> String {
        match section_name {
            "learning_objectives" => format!(
                "\n## Learning Objectives\n\nBy the end of this {}, students will be able to:\n- [Add specific learning objective]\n- [Add another objective]\n\n",
                match content_type {
                    ContentType::Slides => "lesson",
                    ContentType::Worksheet => "worksheet", 
                    ContentType::ActivityGuide => "activity",
                    _ => "content"
                }
            ),
            "summary" => "\n## Summary\n\n[Summarize key points and takeaways]\n\n".to_string(),
            "instructions" => "\n## Instructions\n\n[Provide clear step-by-step instructions]\n\n".to_string(),
            _ => format!("\n## {}\n\n[Add {} content here]\n\n", 
                        section_name.replace('_', " ").to_title_case(), 
                        section_name.replace('_', " "))
        }
    }
    
    fn find_best_insertion_point(&self, content: &str, section_name: &str) -> usize {
        // Simple heuristic: insert before the last section or at the end
        let lines: Vec<&str> = content.lines().collect();
        
        // Look for the last heading
        for (i, line) in lines.iter().enumerate().rev() {
            if line.starts_with('#') {
                // Insert after this heading's content
                let remaining_lines = &lines[i..];
                let mut end_of_section = i + 1;
                
                for (j, remaining_line) in remaining_lines.iter().enumerate().skip(1) {
                    if remaining_line.starts_with('#') {
                        break;
                    }
                    end_of_section = i + j + 1;
                }
                
                return lines[..end_of_section].join("\n").len();
            }
        }
        
        // If no headings found, insert at the end
        content.len()
    }
    
    fn find_objectives_insertion_point(&self, content: &str) -> usize {
        // Insert learning objectives after title but before main content
        let lines: Vec<&str> = content.lines().collect();
        
        for (i, line) in lines.iter().enumerate() {
            if line.starts_with('#') && i > 0 {
                // Insert before the second heading
                return lines[..i].join("\n").len();
            }
        }
        
        // Insert at the beginning if no structure found
        0
    }
    
    fn insert_content_at_position(&self, original: &str, content_to_insert: &str, position: usize) -> String {
        let mut result = String::new();
        result.push_str(&original[..position]);
        result.push_str(content_to_insert);
        result.push_str(&original[position..]);
        result
    }
    
    fn get_context_around_position(&self, content: &str, position: usize, context_size: usize) -> String {
        let start = position.saturating_sub(context_size);
        let end = (position + context_size).min(content.len());
        content[start..end].to_string()
    }
    
    fn remove_repeated_words(&self, content: &str) -> String {
        let words: Vec<&str> = content.split_whitespace().collect();
        let mut result = Vec::new();
        let mut prev_word = "";
        
        for word in words {
            if word.to_lowercase() != prev_word.to_lowercase() {
                result.push(word);
                prev_word = word;
            }
        }
        
        result.join(" ")
    }
    
    fn fix_capitalization(&self, content: &str) -> String {
        let lines: Vec<&str> = content.lines().collect();
        let mut result = Vec::new();
        
        for line in lines {
            if !line.trim().is_empty() {
                let mut chars: Vec<char> = line.chars().collect();
                if let Some(first_char) = chars.get_mut(0) {
                    if first_char.is_alphabetic() {
                        *first_char = first_char.to_uppercase().next().unwrap_or(*first_char);
                    }
                }
                result.push(chars.into_iter().collect::<String>());
            } else {
                result.push(line.to_string());
            }
        }
        
        result.join("\n")
    }
    
    fn fix_common_typos(&self, content: &str) -> String {
        let typo_fixes = [
            ("teh", "the"),
            ("adn", "and"),
            ("recieve", "receive"),
            ("seperate", "separate"),
            ("occured", "occurred"),
            ("definately", "definitely"),
        ];
        
        let mut result = content.to_string();
        for (typo, fix) in typo_fixes.iter() {
            result = result.replace(typo, fix);
            result = result.replace(&typo.to_title_case(), &fix.to_title_case());
        }
        
        result
    }
    
    fn add_structure_headings(&self, content: &str) -> String {
        let lines: Vec<&str> = content.lines().collect();
        let mut result = Vec::new();
        let mut paragraph_count = 0;
        
        for line in lines {
            if line.trim().is_empty() {
                result.push(line.to_string());
            } else if !line.starts_with('#') {
                if paragraph_count > 0 && paragraph_count % 3 == 0 {
                    result.push(format!("## Section {}", (paragraph_count / 3) + 1));
                }
                result.push(line.to_string());
                paragraph_count += 1;
            } else {
                result.push(line.to_string());
            }
        }
        
        result.join("\n")
    }
    
    fn improve_formatting(&self, content: &str) -> String {
        // Simple formatting improvements
        content
            .replace("\n\n\n", "\n\n")  // Remove extra blank lines
            .replace("  ", " ")          // Remove double spaces
            .replace("\t", "    ")       // Convert tabs to spaces
    }
    
    fn generate_learning_objectives_template(&self, content_type: &ContentType) -> String {
        format!(
            "\n## Learning Objectives\n\nBy the end of this {}, students will be able to:\n- Identify key concepts\n- Apply learned principles\n- Evaluate different approaches\n\n",
            match content_type {
                ContentType::Slides => "lesson",
                ContentType::Worksheet => "worksheet",
                ContentType::Quiz => "quiz",
                ContentType::ActivityGuide => "activity",
                ContentType::InstructorNotes => "session",
            }
        )
    }
    
    fn calculate_diff_highlights(&self, before: &str, after: &str) -> Vec<DiffHighlight> {
        // Simple diff calculation (in practice, you'd use a proper diff library)
        if before != after {
            vec![
                DiffHighlight {
                    range: (0, after.len()),
                    change_type: ChangeType::Modification,
                    description: "Content modified".to_string(),
                }
            ]
        } else {
            vec![]
        }
    }
    
    fn create_minimal_section_preview(&self, section_name: &str, content_type: &ContentType) -> RemediationPreview {
        let minimal_content = format!("## {}\n\n[Content to be added]\n", section_name.replace('_', " ").to_title_case());
        RemediationPreview {
            before: "".to_string(),
            after: minimal_content.clone(),
            diff_highlights: vec![
                DiffHighlight {
                    range: (0, minimal_content.len()),
                    change_type: ChangeType::Addition,
                    description: format!("Minimal {} section", section_name),
                }
            ],
            affected_sections: vec![section_name.to_string()],
            content_location: None,
        }
    }
    
    fn create_comprehensive_section_preview(&self, section_name: &str, content_type: &ContentType) -> RemediationPreview {
        let comprehensive_content = self.generate_section_template(section_name, content_type);
        RemediationPreview {
            before: "".to_string(),
            after: comprehensive_content.clone(),
            diff_highlights: vec![
                DiffHighlight {
                    range: (0, comprehensive_content.len()),
                    change_type: ChangeType::Addition,
                    description: format!("Comprehensive {} section", section_name),
                }
            ],
            affected_sections: vec![section_name.to_string()],
            content_location: None,
        }
    }
    
    fn generate_fix_description(&self, fix_type: &RemediationFixType, issue: &ValidationIssue) -> String {
        match fix_type {
            RemediationFixType::AddMissingSection => {
                format!("Add the missing section to improve content structure: {}", issue.message)
            },
            RemediationFixType::FixGrammarError => {
                format!("Fix grammar issue: {}", issue.message)
            },
            RemediationFixType::StandardizeTerminology => {
                "Standardize terminology for consistency across content".to_string()
            },
            RemediationFixType::ImproveReadability => {
                "Improve content readability by simplifying sentences and structure".to_string()
            },
            RemediationFixType::AddHeadings => {
                "Add section headings to improve content organization".to_string()
            },
            RemediationFixType::AddLearningObjectives => {
                "Add learning objectives to clarify educational goals".to_string()
            },
            RemediationFixType::FixTypos => {
                "Fix spelling errors and typos".to_string()
            },
            RemediationFixType::CorrectCapitalization => {
                "Correct capitalization issues".to_string()
            },
            RemediationFixType::RemoveDuplicates => {
                "Remove duplicate words and phrases".to_string()
            },
            RemediationFixType::FormatText => {
                "Improve text formatting and spacing".to_string()
            },
            _ => format!("Apply {} fix for: {}", format!("{:?}", fix_type).replace('_', " "), issue.message),
        }
    }
    
    fn requires_user_approval(&self, fix_type: &RemediationFixType, risk_level: &RiskLevel) -> bool {
        // Safe fixes can be auto-applied
        if matches!(risk_level, RiskLevel::Safe) && self.config.auto_applicable_fix_types.contains(fix_type) {
            return false;
        }
        
        // Structural changes always require approval if configured
        if self.config.require_approval_for_structure {
            match fix_type {
                RemediationFixType::AddMissingSection |
                RemediationFixType::ReorganizeContent |
                RemediationFixType::FixSectionOrder => return true,
                _ => {}
            }
        }
        
        // Medium+ risk always requires approval
        matches!(risk_level, RiskLevel::Medium | RiskLevel::High | RiskLevel::Critical)
    }
    
    fn assess_fix_impact(&self, content: &GeneratedContent, issue: &ValidationIssue, fix_type: &RemediationFixType, preview: &RemediationPreview) -> ImpactAssessment {
        let educational_effectiveness = match fix_type {
            RemediationFixType::AddLearningObjectives => 0.9,
            RemediationFixType::AddMissingSection => 0.8,
            RemediationFixType::ImproveReadability => 0.7,
            RemediationFixType::StandardizeTerminology => 0.6,
            _ => 0.5,
        };
        
        let readability_improvement = match fix_type {
            RemediationFixType::ImproveReadability => 0.8,
            RemediationFixType::AddHeadings => 0.7,
            RemediationFixType::FormatText => 0.6,
            _ => 0.3,
        };
        
        let structure_improvement = match fix_type {
            RemediationFixType::AddMissingSection => 0.9,
            RemediationFixType::AddHeadings => 0.8,
            RemediationFixType::ReorganizeContent => 0.9,
            _ => 0.2,
        };
        
        let consistency_improvement = match fix_type {
            RemediationFixType::StandardizeTerminology => 0.9,
            RemediationFixType::StandardizeAssessment => 0.8,
            _ => 0.4,
        };
        
        let benefits = match fix_type {
            RemediationFixType::AddLearningObjectives => vec![
                "Clarifies educational goals".to_string(),
                "Improves student understanding".to_string(),
                "Aligns with pedagogical best practices".to_string(),
            ],
            RemediationFixType::AddMissingSection => vec![
                "Completes content structure".to_string(),
                "Improves content organization".to_string(),
            ],
            _ => vec!["Improves content quality".to_string()],
        };
        
        let potential_drawbacks = match fix_type {
            RemediationFixType::ReorganizeContent => vec![
                "May change intended content flow".to_string(),
                "Could affect existing references".to_string(),
            ],
            RemediationFixType::AddMissingSection => vec![
                "Increases content length".to_string(),
                "May require additional customization".to_string(),
            ],
            _ => vec![],
        };
        
        ImpactAssessment {
            educational_effectiveness,
            readability_improvement,
            structure_improvement,
            consistency_improvement,
            potential_drawbacks,
            benefits,
        }
    }
    
    fn calculate_priority(&self, severity: &IssueSeverity, confidence: &ConfidenceLevel) -> f64 {
        let severity_weight = match severity {
            IssueSeverity::Critical => 10.0,
            IssueSeverity::Error => 8.0,
            IssueSeverity::Warning => 6.0,
            IssueSeverity::Info => 4.0,
        };
        
        let confidence_weight = match confidence {
            ConfidenceLevel::VeryHigh => 1.0,
            ConfidenceLevel::High => 0.8,
            ConfidenceLevel::Medium => 0.6,
            ConfidenceLevel::Low => 0.4,
            ConfidenceLevel::VeryLow => 0.2,
        };
        
        severity_weight * confidence_weight
    }
    
    /// Apply an approved fix to content
    pub async fn apply_fix(
        &mut self,
        session_id: Uuid,
        suggestion_id: Uuid,
        content: &mut GeneratedContent,
        user_approved: bool,
    ) -> Result<AppliedFix> {
        // Get suggestion details first
        let suggestion = {
            let session = self.pending_fixes.get(&session_id)
                .ok_or_else(|| anyhow::anyhow!("Session not found"))?;
            
            session.suggested_fixes.iter()
                .find(|s| s.suggestion_id == suggestion_id)
                .ok_or_else(|| anyhow::anyhow!("Suggestion not found"))?
                .clone()
        };
        
        let before_content = content.content.clone();
        let success = match self.apply_specific_fix(content, &suggestion).await {
            Ok(_) => true,
            Err(e) => {
                eprintln!("Failed to apply fix: {}", e);
                false
            }
        };
        
        let applied_fix = AppliedFix {
            fix_id: Uuid::new_v4(),
            suggestion_id,
            applied_at: chrono::Utc::now(),
            before_content,
            after_content: content.content.clone(),
            user_approved,
            auto_applied: !suggestion.requires_approval,
            success,
            error_message: if success { None } else { Some("Fix application failed".to_string()) },
        };
        
        // Update session after applying fix
        if let Some(session) = self.pending_fixes.get_mut(&session_id) {
            session.applied_fixes.push(applied_fix.clone());
            session.updated_at = chrono::Utc::now();
        }
        
        Ok(applied_fix)
    }
    
    /// Apply a specific fix to content
    async fn apply_specific_fix(&self, content: &mut GeneratedContent, suggestion: &RemediationSuggestion) -> Result<()> {
        // Apply the fix based on the preview
        content.content = suggestion.preview.after.clone();
        
        // Update metadata if needed
        content.metadata.word_count = content.content.split_whitespace().count();
        
        Ok(())
    }
    
    /// Record a user decision
    pub fn record_user_decision(
        &mut self,
        session_id: Uuid,
        suggestion_id: Uuid,
        decision: DecisionType,
        alternative_chosen: Option<Uuid>,
        user_feedback: Option<String>,
    ) -> Result<()> {
        let session = self.pending_fixes.get_mut(&session_id)
            .ok_or_else(|| anyhow::anyhow!("Session not found"))?;
        
        let user_decision = UserDecision {
            suggestion_id,
            decision,
            alternative_chosen,
            user_feedback,
            decided_at: chrono::Utc::now(),
        };
        
        session.user_decisions.push(user_decision);
        session.updated_at = chrono::Utc::now();
        
        // Update session status based on decisions
        self.update_session_status(session_id)?;
        
        Ok(())
    }
    
    /// Update session status based on user decisions
    fn update_session_status(&mut self, session_id: Uuid) -> Result<()> {
        let session = self.pending_fixes.get_mut(&session_id)
            .ok_or_else(|| anyhow::anyhow!("Session not found"))?;
        
        let total_suggestions = session.suggested_fixes.len();
        let decisions_made = session.user_decisions.len();
        let fixes_applied = session.applied_fixes.len();
        
        session.status = if decisions_made == total_suggestions {
            if fixes_applied > 0 {
                SessionStatus::Completed
            } else {
                SessionStatus::Completed // All decisions made, even if no fixes applied
            }
        } else if fixes_applied > 0 {
            SessionStatus::PartiallyApplied
        } else if decisions_made > 0 {
            SessionStatus::InProgress
        } else {
            SessionStatus::Pending
        };
        
        Ok(())
    }
    
    /// Get pending sessions
    pub fn get_pending_sessions(&self) -> Vec<&RemediationSession> {
        self.pending_fixes.values().collect()
    }
    
    /// Get session by ID
    pub fn get_session(&self, session_id: Uuid) -> Option<&RemediationSession> {
        self.pending_fixes.get(&session_id)
    }
    
    /// Learn from user preferences
    pub fn update_user_preferences(&mut self, _user_id: &str, session: &RemediationSession) -> RemediationPreferences {
        let mut preferences = RemediationPreferences::default();
        
        // Analyze user decisions to learn preferences
        for decision in &session.user_decisions {
            if let Some(suggestion) = session.suggested_fixes.iter().find(|s| s.suggestion_id == decision.suggestion_id) {
                match decision.decision {
                    DecisionType::Approve => {
                        if !preferences.preferred_fix_types.contains(&suggestion.fix_type) {
                            preferences.preferred_fix_types.push(suggestion.fix_type.clone());
                        }
                    },
                    DecisionType::Reject => {
                        if !preferences.rejected_fix_types.contains(&suggestion.fix_type) {
                            preferences.rejected_fix_types.push(suggestion.fix_type.clone());
                        }
                    },
                    _ => {}
                }
            }
        }
        
        preferences
    }
}

// Helper trait for string formatting
trait StringFormatting {
    fn to_title_case(&self) -> String;
}

impl StringFormatting for str {
    fn to_title_case(&self) -> String {
        self.split_whitespace()
            .map(|word| {
                let mut chars = word.chars();
                match chars.next() {
                    None => String::new(),
                    Some(first) => first.to_uppercase().collect::<String>() + &chars.as_str().to_lowercase(),
                }
            })
            .collect::<Vec<String>>()
            .join(" ")
    }
}

// Helper function for ContentType to string conversion
fn content_type_to_string(content_type: &ContentType) -> String {
    match content_type {
        ContentType::Slides => "slides".to_string(),
        ContentType::Quiz => "quiz".to_string(),
        ContentType::Worksheet => "worksheet".to_string(),
        ContentType::InstructorNotes => "instructor_notes".to_string(),
        ContentType::ActivityGuide => "activity_guide".to_string(),
    }
}