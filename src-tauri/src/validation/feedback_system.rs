use super::validators::*;
use super::smart_config::{UserExperienceLevel, NotificationLevel};
use super::remediation::ConfidenceLevel;
use crate::content::{GeneratedContent, ContentType};
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// User-friendly feedback system for validation results
#[derive(Debug, Clone)]
pub struct FeedbackSystem {
    templates: FeedbackTemplates,
    personalization: PersonalizationSettings,
}

/// Templates for different types of feedback messages
#[derive(Debug, Clone)]
pub struct FeedbackTemplates {
    issue_explanations: HashMap<IssueType, IssueExplanation>,
    suggestion_templates: HashMap<IssueType, Vec<SuggestionTemplate>>,
    encouragement_messages: Vec<String>,
    progress_messages: Vec<String>,
}

/// Personalization settings for feedback delivery
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PersonalizationSettings {
    pub experience_level: UserExperienceLevel,
    pub notification_level: NotificationLevel,
    pub show_technical_details: bool,
    pub use_encouraging_tone: bool,
    pub include_learning_tips: bool,
    pub group_similar_issues: bool,
    pub prioritize_actionable_feedback: bool,
}

/// Clear explanation of a validation issue
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IssueExplanation {
    pub simple_title: String,
    pub friendly_description: String,
    pub why_it_matters: String,
    pub learning_context: Option<String>,
    pub difficulty_impact: DifficultyImpact,
    pub examples: Vec<IssueExample>,
}

/// How an issue affects content difficulty
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum DifficultyImpact {
    MakesHarderToRead,
    MakesHarderToUnderstand,
    MakesLessEngaging,
    MakesLessAccessible,
    MakesLessProfessional,
    NoSignificantImpact,
}

/// Example of an issue with before/after demonstration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IssueExample {
    pub context: String,
    pub before_text: String,
    pub after_text: String,
    pub explanation: String,
}

/// Template for generating suggestions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SuggestionTemplate {
    pub action_verb: String,  // "simplify", "break up", "add", "remove"
    pub description_template: String,  // "Try {action} to make this easier to read"
    pub specific_guidance: String,  // What exactly to do
    pub confidence_level: ConfidenceLevel,
}

/// User-friendly feedback for validation results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserFriendlyFeedback {
    pub overall_summary: OverallSummary,
    pub issue_groups: Vec<IssueGroup>,
    pub positive_highlights: Vec<String>,
    pub next_steps: Vec<ActionableStep>,
    pub learning_opportunities: Vec<LearningTip>,
    pub progress_indicator: ProgressIndicator,
}

/// High-level summary of validation results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OverallSummary {
    pub status: OverallStatus,
    pub main_message: String,
    pub key_insights: Vec<String>,
    pub estimated_improvement_time: Option<String>,
}

/// Overall validation status
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum OverallStatus {
    Excellent,     // No significant issues
    Good,          // Minor issues only
    NeedsWork,     // Several issues to address
    NeedsRevision, // Major issues requiring attention
}

/// Grouped issues for better organization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IssueGroup {
    pub category: IssueCategory,
    pub title: String,
    pub description: String,
    pub issues: Vec<SimplifiedIssue>,
    pub priority: Priority,
    pub estimated_fix_time: String,
}

/// Simplified categories for users
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum IssueCategory {
    ReadabilityAndClarity,
    OrganizationAndStructure,
    CompletenessAndDetail,
    LanguageAndGrammar,
    ConsistencyAndAlignment,
    AccessibilityAndInclusion,
}

/// Priority level for issue groups
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum Priority {
    Critical,  // Must fix for content to be usable
    High,      // Should fix for best results
    Medium,    // Nice to fix for improvement
    Low,       // Optional enhancement
}

/// Simplified issue representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimplifiedIssue {
    pub title: String,
    pub explanation: String,
    pub location_description: String,
    pub suggestions: Vec<FriendlySuggestion>,
    pub impact_level: ImpactLevel,
    pub fix_difficulty: FixDifficulty,
}

/// How much an issue affects the content
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ImpactLevel {
    High,     // Significantly affects usability
    Medium,   // Noticeable but manageable
    Low,      // Minor improvement
}

/// How difficult it is to fix an issue
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum FixDifficulty {
    Easy,     // Quick fix, few minutes
    Medium,   // Moderate effort, 15-30 minutes
    Hard,     // Significant rework, 30+ minutes
}

/// User-friendly suggestion
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FriendlySuggestion {
    pub action: String,
    pub description: String,
    pub example: Option<String>,
    pub why_this_helps: String,
    pub auto_fixable: bool,
}

/// Actionable step for improvement
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionableStep {
    pub step_number: usize,
    pub title: String,
    pub description: String,
    pub estimated_time: String,
    pub tools_needed: Vec<String>,
    pub success_criteria: String,
}

/// Learning tip to help users improve
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LearningTip {
    pub title: String,
    pub content: String,
    pub category: LearningCategory,
    pub difficulty_level: LearningDifficulty,
    pub related_resources: Vec<String>,
}

/// Categories of learning tips
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum LearningCategory {
    WritingSkills,
    ContentStructure,
    EducationalDesign,
    AccessibilityPractices,
    TechnicalWriting,
}

/// Difficulty level of learning content
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum LearningDifficulty {
    Beginner,
    Intermediate, 
    Advanced,
}

/// Progress indicator for user motivation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProgressIndicator {
    pub overall_score: f64,  // 0.0 to 100.0
    pub category_scores: HashMap<IssueCategory, f64>,
    pub improvement_from_last: Option<f64>,
    pub achievements: Vec<Achievement>,
    pub next_milestone: Option<Milestone>,
}

/// Achievement badge for positive reinforcement
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Achievement {
    pub title: String,
    pub description: String,
    pub icon: String,
    pub earned_date: chrono::DateTime<chrono::Utc>,
}

/// Milestone to work towards
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Milestone {
    pub title: String,
    pub description: String,
    pub progress_percentage: f64,
    pub reward_description: String,
}

impl FeedbackSystem {
    /// Create a new feedback system with default templates
    pub fn new() -> Self {
        Self {
            templates: FeedbackTemplates::new(),
            personalization: PersonalizationSettings::default(),
        }
    }
    
    /// Create feedback system with specific personalization
    pub fn with_personalization(personalization: PersonalizationSettings) -> Self {
        Self {
            templates: FeedbackTemplates::new(),
            personalization,
        }
    }
    
    /// Generate user-friendly feedback from validation results
    pub fn generate_feedback(
        &self,
        results: &[ValidationResult],
        content: &GeneratedContent,
        previous_scores: Option<&HashMap<IssueCategory, f64>>,
    ) -> Result<UserFriendlyFeedback> {
        // Collect all issues
        let all_issues: Vec<&ValidationIssue> = results
            .iter()
            .flat_map(|r| &r.issues)
            .collect();
        
        // Generate overall summary
        let overall_summary = self.generate_overall_summary(&all_issues, content)?;
        
        // Group and simplify issues
        let issue_groups = self.group_and_simplify_issues(&all_issues)?;
        
        // Find positive aspects
        let positive_highlights = self.generate_positive_highlights(results, content);
        
        // Create actionable steps
        let next_steps = self.generate_next_steps(&issue_groups)?;
        
        // Generate learning tips
        let learning_opportunities = self.generate_learning_tips(&all_issues, &self.personalization.experience_level);
        
        // Calculate progress
        let progress_indicator = self.calculate_progress(&issue_groups, previous_scores)?;
        
        Ok(UserFriendlyFeedback {
            overall_summary,
            issue_groups,
            positive_highlights,
            next_steps,
            learning_opportunities,
            progress_indicator,
        })
    }
    
    /// Generate an encouraging overall summary
    fn generate_overall_summary(
        &self,
        issues: &[&ValidationIssue],
        content: &GeneratedContent,
    ) -> Result<OverallSummary> {
        let critical_count = issues.iter().filter(|i| i.severity == IssueSeverity::Critical).count();
        let error_count = issues.iter().filter(|i| i.severity == IssueSeverity::Error).count();
        let warning_count = issues.iter().filter(|i| i.severity == IssueSeverity::Warning).count();
        
        let (status, main_message) = match (critical_count, error_count, warning_count) {
            (0, 0, 0) => (
                OverallStatus::Excellent,
                "🎉 Great work! Your content looks excellent and ready to use.".to_string()
            ),
            (0, 0, w) if w <= 2 => (
                OverallStatus::Good,
                format!("✨ Your content looks good! Just {} small {} to polish it up.", w, if w == 1 { "suggestion" } else { "suggestions" })
            ),
            (0, e, w) if e + w <= 5 => (
                OverallStatus::NeedsWork,
                "📝 Your content has potential! Let's work together to make it even better.".to_string()
            ),
            _ => (
                OverallStatus::NeedsRevision,
                "🔧 Your content needs some attention, but don't worry - we'll help you improve it step by step!".to_string()
            ),
        };
        
        let mut key_insights = Vec::new();
        
        // Add content-type specific insights
        match content.content_type {
            ContentType::Slides => {
                if issues.iter().any(|i| matches!(i.issue_type, IssueType::Readability)) {
                    key_insights.push("Slides work best with short, clear sentences that are easy to read quickly.".to_string());
                }
            },
            ContentType::Quiz => {
                if issues.iter().any(|i| matches!(i.issue_type, IssueType::Grammar | IssueType::Spelling)) {
                    key_insights.push("Clear question wording helps students focus on demonstrating their knowledge.".to_string());
                }
            },
            ContentType::Worksheet => {
                if issues.iter().any(|i| matches!(i.issue_type, IssueType::Structure)) {
                    key_insights.push("Well-organized worksheets guide students through learning step by step.".to_string());
                }
            },
            _ => {}
        }
        
        // Estimate improvement time
        let estimated_improvement_time = match issues.len() {
            0 => None,
            1..=3 => Some("5-10 minutes".to_string()),
            4..=8 => Some("15-25 minutes".to_string()),
            _ => Some("30-45 minutes".to_string()),
        };
        
        Ok(OverallSummary {
            status,
            main_message,
            key_insights,
            estimated_improvement_time,
        })
    }
    
    /// Group issues by category and create simplified representations
    fn group_and_simplify_issues(&self, issues: &[&ValidationIssue]) -> Result<Vec<IssueGroup>> {
        let mut groups: HashMap<IssueCategory, Vec<SimplifiedIssue>> = HashMap::new();
        
        for issue in issues {
            let category = self.map_issue_to_category(&issue.issue_type);
            let simplified = self.simplify_issue(issue)?;
            groups.entry(category).or_insert_with(Vec::new).push(simplified);
        }
        
        let mut result = Vec::new();
        for (category, issues) in groups {
            if issues.is_empty() { continue; }
            
            let priority = self.determine_group_priority(&issues);
            let estimated_fix_time = self.estimate_group_fix_time(&issues);
            
            let group = IssueGroup {
                title: self.get_category_title(&category),
                description: self.get_category_description(&category),
                category,
                issues,
                priority,
                estimated_fix_time,
            };
            result.push(group);
        }
        
        // Sort by priority
        result.sort_by(|a, b| a.priority.cmp(&b.priority));
        
        Ok(result)
    }
    
    /// Map technical issue types to user-friendly categories
    fn map_issue_to_category(&self, issue_type: &IssueType) -> IssueCategory {
        match issue_type {
            IssueType::Readability => IssueCategory::ReadabilityAndClarity,
            IssueType::Structure | IssueType::Format => IssueCategory::OrganizationAndStructure,
            IssueType::Completeness | IssueType::LearningObjectives => IssueCategory::CompletenessAndDetail,
            IssueType::Grammar | IssueType::Spelling | IssueType::Tone => IssueCategory::LanguageAndGrammar,
            IssueType::Consistency | IssueType::PedagogicalAlignment => IssueCategory::ConsistencyAndAlignment,
            IssueType::AgeAppropriateness | IssueType::Bias => IssueCategory::AccessibilityAndInclusion,
            _ => IssueCategory::ReadabilityAndClarity, // Default fallback
        }
    }
    
    /// Create a simplified, user-friendly version of an issue
    fn simplify_issue(&self, issue: &ValidationIssue) -> Result<SimplifiedIssue> {
        let explanation = self.templates.issue_explanations
            .get(&issue.issue_type)
            .map(|e| e.friendly_description.clone())
            .unwrap_or_else(|| self.generate_fallback_explanation(&issue.issue_type));
        
        let title = self.templates.issue_explanations
            .get(&issue.issue_type)
            .map(|e| e.simple_title.clone())
            .unwrap_or_else(|| format!("{:?}", issue.issue_type));
        
        let location_description = match &issue.location {
            Some(loc) => self.describe_location(loc),
            None => "Throughout the content".to_string(),
        };
        
        let suggestions = self.generate_friendly_suggestions(issue)?;
        
        let impact_level = self.determine_impact_level(&issue.severity);
        let fix_difficulty = self.estimate_fix_difficulty(issue);
        
        Ok(SimplifiedIssue {
            title,
            explanation,
            location_description,
            suggestions,
            impact_level,
            fix_difficulty,
        })
    }
    
    /// Generate user-friendly suggestions for an issue
    fn generate_friendly_suggestions(&self, issue: &ValidationIssue) -> Result<Vec<FriendlySuggestion>> {
        let templates = self.templates.suggestion_templates
            .get(&issue.issue_type)
            .cloned()
            .unwrap_or_else(|| vec![self.create_default_suggestion_template()]);
        
        let mut suggestions = Vec::new();
        
        for template in templates {
            let suggestion = FriendlySuggestion {
                action: template.action_verb.clone(),
                description: template.description_template
                    .replace("{action}", &template.action_verb),
                example: self.generate_example_for_issue(issue),
                why_this_helps: self.explain_why_suggestion_helps(&issue.issue_type),
                auto_fixable: self.is_auto_fixable(&issue.issue_type),
            };
            suggestions.push(suggestion);
        }
        
        Ok(suggestions)
    }
    
    /// Generate positive highlights from validation results
    fn generate_positive_highlights(
        &self,
        results: &[ValidationResult],
        content: &GeneratedContent,
    ) -> Vec<String> {
        let mut highlights = Vec::new();
        
        // Check for good scores
        for result in results {
            if result.score >= 0.8 {
                match result.validator_name.as_str() {
                    "readability" => highlights.push("📖 Your content is easy to read and understand!".to_string()),
                    "structure" => highlights.push("🏗️ Great job organizing your content clearly!".to_string()),
                    "completeness" => highlights.push("✅ Your content covers all the important points!".to_string()),
                    "grammar" => highlights.push("📝 Your writing is clear and well-written!".to_string()),
                    _ => {}
                }
            }
        }
        
        // Content-type specific positives
        match content.content_type {
            ContentType::Slides => {
                highlights.push("🎯 Slide content is focused and presentation-ready!".to_string());
            },
            ContentType::Quiz => {
                highlights.push("🧠 Questions are well-crafted for assessing learning!".to_string());
            },
            _ => {}
        }
        
        // Default positive message if no specific highlights
        if highlights.is_empty() {
            highlights.push("💪 You're on the right track - keep up the good work!".to_string());
        }
        
        highlights
    }
    
    /// Generate actionable next steps
    fn generate_next_steps(&self, issue_groups: &[IssueGroup]) -> Result<Vec<ActionableStep>> {
        let mut steps = Vec::new();
        let mut step_number = 1;
        
        // Prioritize critical and high priority groups
        for group in issue_groups.iter().take(3) { // Limit to top 3 for focus
            if matches!(group.priority, Priority::Critical | Priority::High) {
                let step = ActionableStep {
                    step_number,
                    title: format!("Address {}", group.title),
                    description: self.generate_step_description(group),
                    estimated_time: group.estimated_fix_time.clone(),
                    tools_needed: vec!["Text editor".to_string()],
                    success_criteria: self.generate_success_criteria(group),
                };
                steps.push(step);
                step_number += 1;
            }
        }
        
        // Add a review step
        if !steps.is_empty() {
            steps.push(ActionableStep {
                step_number,
                title: "Review Your Changes".to_string(),
                description: "Read through your content once more to ensure it flows well and makes sense.".to_string(),
                estimated_time: "5 minutes".to_string(),
                tools_needed: vec![],
                success_criteria: "Content reads smoothly and achieves your learning goals.".to_string(),
            });
        }
        
        Ok(steps)
    }
    
    /// Generate learning tips based on issues and user level
    fn generate_learning_tips(
        &self,
        issues: &[&ValidationIssue],
        experience_level: &UserExperienceLevel,
    ) -> Vec<LearningTip> {
        let mut tips = Vec::new();
        
        // Analyze common issue patterns
        let readability_issues = issues.iter().filter(|i| matches!(i.issue_type, IssueType::Readability)).count();
        let structure_issues = issues.iter().filter(|i| matches!(i.issue_type, IssueType::Structure)).count();
        
        if readability_issues > 0 {
            let difficulty = match experience_level {
                UserExperienceLevel::Beginner => LearningDifficulty::Beginner,
                UserExperienceLevel::Intermediate => LearningDifficulty::Intermediate,
                _ => LearningDifficulty::Advanced,
            };
            
            tips.push(LearningTip {
                title: "Writing for Your Audience".to_string(),
                content: "Consider who will be reading your content. Use shorter sentences and simpler words when writing for beginners, and provide clear examples to illustrate complex concepts.".to_string(),
                category: LearningCategory::WritingSkills,
                difficulty_level: difficulty,
                related_resources: vec![
                    "Plain Language Guidelines".to_string(),
                    "Writing for Web Accessibility".to_string(),
                ],
            });
        }
        
        if structure_issues > 0 {
            tips.push(LearningTip {
                title: "Organizing Educational Content".to_string(),
                content: "Start with learning objectives, introduce concepts step-by-step, provide examples, and end with a summary. This helps learners follow your thinking and retain information better.".to_string(),
                category: LearningCategory::ContentStructure,
                difficulty_level: LearningDifficulty::Beginner,
                related_resources: vec![
                    "Instructional Design Basics".to_string(),
                    "Content Organization Patterns".to_string(),
                ],
            });
        }
        
        tips
    }
    
    /// Calculate progress and scores
    fn calculate_progress(
        &self,
        issue_groups: &[IssueGroup],
        previous_scores: Option<&HashMap<IssueCategory, f64>>,
    ) -> Result<ProgressIndicator> {
        let mut category_scores = HashMap::new();
        
        // Calculate scores for each category (100 - penalty for issues)
        for category in [
            IssueCategory::ReadabilityAndClarity,
            IssueCategory::OrganizationAndStructure,
            IssueCategory::CompletenessAndDetail,
            IssueCategory::LanguageAndGrammar,
            IssueCategory::ConsistencyAndAlignment,
            IssueCategory::AccessibilityAndInclusion,
        ] {
            let issues_in_category = issue_groups.iter()
                .filter(|g| g.category == category)
                .map(|g| g.issues.len())
                .sum::<usize>();
            
            // Score decreases with more issues
            let score = (100.0 - (issues_in_category as f64 * 10.0)).max(0.0);
            category_scores.insert(category, score);
        }
        
        // Overall score is the average
        let overall_score = category_scores.values().sum::<f64>() / category_scores.len() as f64;
        
        // Calculate improvement
        let improvement_from_last = if let Some(prev_scores) = previous_scores {
            let prev_overall = prev_scores.values().sum::<f64>() / prev_scores.len() as f64;
            Some(overall_score - prev_overall)
        } else {
            None
        };
        
        // Generate achievements
        let achievements = self.generate_achievements(overall_score, &improvement_from_last);
        
        // Generate next milestone
        let next_milestone = self.generate_next_milestone(overall_score);
        
        Ok(ProgressIndicator {
            overall_score,
            category_scores,
            improvement_from_last,
            achievements,
            next_milestone,
        })
    }
    
    /// Helper methods for implementation details
    fn determine_group_priority(&self, issues: &[SimplifiedIssue]) -> Priority {
        if issues.iter().any(|i| i.impact_level == ImpactLevel::High) {
            Priority::Critical
        } else if issues.iter().any(|i| i.impact_level == ImpactLevel::Medium) {
            Priority::High
        } else {
            Priority::Medium
        }
    }
    
    fn estimate_group_fix_time(&self, issues: &[SimplifiedIssue]) -> String {
        let total_minutes: usize = issues.iter().map(|i| match i.fix_difficulty {
            FixDifficulty::Easy => 5,
            FixDifficulty::Medium => 20,
            FixDifficulty::Hard => 40,
        }).sum();
        
        if total_minutes < 10 {
            "5-10 minutes".to_string()
        } else if total_minutes < 30 {
            "15-25 minutes".to_string()
        } else {
            "30+ minutes".to_string()
        }
    }
    
    fn get_category_title(&self, category: &IssueCategory) -> String {
        match category {
            IssueCategory::ReadabilityAndClarity => "Readability & Clarity",
            IssueCategory::OrganizationAndStructure => "Organization & Structure",
            IssueCategory::CompletenessAndDetail => "Completeness & Detail",
            IssueCategory::LanguageAndGrammar => "Language & Grammar",
            IssueCategory::ConsistencyAndAlignment => "Consistency & Alignment",
            IssueCategory::AccessibilityAndInclusion => "Accessibility & Inclusion",
        }.to_string()
    }
    
    fn get_category_description(&self, category: &IssueCategory) -> String {
        match category {
            IssueCategory::ReadabilityAndClarity => "How easy your content is to read and understand",
            IssueCategory::OrganizationAndStructure => "How well your content is organized and flows",
            IssueCategory::CompletenessAndDetail => "Whether your content covers everything it should",
            IssueCategory::LanguageAndGrammar => "The quality of writing and language use",
            IssueCategory::ConsistencyAndAlignment => "How well different parts work together",
            IssueCategory::AccessibilityAndInclusion => "How accessible your content is to all learners",
        }.to_string()
    }
    
    // Additional helper methods would be implemented here...
    fn generate_fallback_explanation(&self, _issue_type: &IssueType) -> String {
        "This area could be improved to make your content more effective.".to_string()
    }
    
    fn describe_location(&self, location: &ContentLocation) -> String {
        if let Some(section) = &location.section {
            format!("In the '{}' section", section)
        } else if let Some(line) = location.line {
            format!("Around line {}", line)
        } else {
            "Throughout the content".to_string()
        }
    }
    
    fn determine_impact_level(&self, severity: &IssueSeverity) -> ImpactLevel {
        match severity {
            IssueSeverity::Critical | IssueSeverity::Error => ImpactLevel::High,
            IssueSeverity::Warning => ImpactLevel::Medium,
            IssueSeverity::Info => ImpactLevel::Low,
        }
    }
    
    fn estimate_fix_difficulty(&self, _issue: &ValidationIssue) -> FixDifficulty {
        FixDifficulty::Medium // Simplified for now
    }
    
    fn create_default_suggestion_template(&self) -> SuggestionTemplate {
        SuggestionTemplate {
            action_verb: "improve".to_string(),
            description_template: "Consider improving this area".to_string(),
            specific_guidance: "Review and revise as needed".to_string(),
            confidence_level: ConfidenceLevel::Medium,
        }
    }
    
    fn generate_example_for_issue(&self, _issue: &ValidationIssue) -> Option<String> {
        None // Would be implemented with specific examples
    }
    
    fn explain_why_suggestion_helps(&self, issue_type: &IssueType) -> String {
        match issue_type {
            IssueType::Readability => "This makes your content easier to read and understand".to_string(),
            IssueType::Structure => "This helps organize your content more clearly".to_string(),
            IssueType::Grammar => "This improves the professional quality of your writing".to_string(),
            _ => "This enhances the overall quality of your content".to_string(),
        }
    }
    
    fn is_auto_fixable(&self, issue_type: &IssueType) -> bool {
        matches!(issue_type, IssueType::Grammar | IssueType::Spelling)
    }
    
    fn generate_step_description(&self, group: &IssueGroup) -> String {
        format!("Focus on the {} issues in your content. {}", group.title.to_lowercase(), group.description)
    }
    
    fn generate_success_criteria(&self, group: &IssueGroup) -> String {
        match group.category {
            IssueCategory::ReadabilityAndClarity => "Content is easy to read and understand".to_string(),
            IssueCategory::OrganizationAndStructure => "Content flows logically from start to finish".to_string(),
            _ => "Issues in this area are resolved".to_string(),
        }
    }
    
    fn generate_achievements(&self, overall_score: f64, improvement: &Option<f64>) -> Vec<Achievement> {
        let mut achievements = Vec::new();
        
        if overall_score >= 90.0 {
            achievements.push(Achievement {
                title: "Excellence Badge".to_string(),
                description: "Your content scored 90% or higher!".to_string(),
                icon: "🏆".to_string(),
                earned_date: chrono::Utc::now(),
            });
        }
        
        if let Some(imp) = improvement {
            if *imp >= 10.0 {
                achievements.push(Achievement {
                    title: "Great Improvement".to_string(),
                    description: "You improved your score by 10+ points!".to_string(),
                    icon: "📈".to_string(),
                    earned_date: chrono::Utc::now(),
                });
            }
        }
        
        achievements
    }
    
    fn generate_next_milestone(&self, overall_score: f64) -> Option<Milestone> {
        if overall_score < 80.0 {
            Some(Milestone {
                title: "Quality Content".to_string(),
                description: "Reach 80% overall score".to_string(),
                progress_percentage: (overall_score / 80.0) * 100.0,
                reward_description: "Unlock advanced content features".to_string(),
            })
        } else if overall_score < 90.0 {
            Some(Milestone {
                title: "Excellence".to_string(),
                description: "Reach 90% overall score".to_string(),
                progress_percentage: ((overall_score - 80.0) / 10.0) * 100.0,
                reward_description: "Earn the Excellence Badge".to_string(),
            })
        } else {
            None
        }
    }
}

impl FeedbackTemplates {
    fn new() -> Self {
        let mut templates = Self {
            issue_explanations: HashMap::new(),
            suggestion_templates: HashMap::new(),
            encouragement_messages: Vec::new(),
            progress_messages: Vec::new(),
        };
        
        templates.initialize_issue_explanations();
        templates.initialize_suggestion_templates();
        templates.initialize_encouragement_messages();
        templates.initialize_progress_messages();
        
        templates
    }
    
    fn initialize_issue_explanations(&mut self) {
        // Readability issues
        self.issue_explanations.insert(IssueType::Readability, IssueExplanation {
            simple_title: "Hard to Read".to_string(),
            friendly_description: "Some parts of your content might be challenging for readers to understand quickly.".to_string(),
            why_it_matters: "When content is easy to read, learners can focus on understanding concepts rather than struggling with complex sentences.".to_string(),
            learning_context: Some("Clear, simple writing helps all learners succeed, regardless of their reading level.".to_string()),
            difficulty_impact: DifficultyImpact::MakesHarderToRead,
            examples: vec![
                IssueExample {
                    context: "Complex sentence".to_string(),
                    before_text: "The methodology utilized in this pedagogical approach facilitates comprehension.".to_string(),
                    after_text: "This teaching method helps students understand better.".to_string(),
                    explanation: "Shorter sentences with common words are easier to follow.".to_string(),
                }
            ],
        });
        
        // Structure issues
        self.issue_explanations.insert(IssueType::Structure, IssueExplanation {
            simple_title: "Needs Better Organization".to_string(),
            friendly_description: "Your content could be organized more clearly to help readers follow along.".to_string(),
            why_it_matters: "Good organization helps learners build understanding step by step, like following a clear path to learning.".to_string(),
            learning_context: Some("Well-structured content mimics how our brains naturally organize information.".to_string()),
            difficulty_impact: DifficultyImpact::MakesHarderToUnderstand,
            examples: vec![],
        });
        
        // Grammar issues
        self.issue_explanations.insert(IssueType::Grammar, IssueExplanation {
            simple_title: "Grammar Check Needed".to_string(),
            friendly_description: "There are some grammar or language issues that could be cleaned up.".to_string(),
            why_it_matters: "Correct grammar makes your content look professional and helps readers focus on learning.".to_string(),
            learning_context: Some("Good grammar is like clear pronunciation - it helps your message come through clearly.".to_string()),
            difficulty_impact: DifficultyImpact::MakesLessProfessional,
            examples: vec![],
        });
    }
    
    fn initialize_suggestion_templates(&mut self) {
        // Readability suggestions
        self.suggestion_templates.insert(IssueType::Readability, vec![
            SuggestionTemplate {
                action_verb: "simplify".to_string(),
                description_template: "Try breaking long sentences into shorter ones".to_string(),
                specific_guidance: "Aim for 15-20 words per sentence".to_string(),
                confidence_level: ConfidenceLevel::High,
            },
            SuggestionTemplate {
                action_verb: "replace".to_string(),
                description_template: "Use simpler words where possible".to_string(),
                specific_guidance: "Choose common words that most people know".to_string(),
                confidence_level: ConfidenceLevel::Medium,
            },
        ]);
    }
    
    fn initialize_encouragement_messages(&mut self) {
        self.encouragement_messages = vec![
            "You're doing great! Every improvement makes your content better.".to_string(),
            "Keep going! Small changes can make a big difference.".to_string(),
            "Nice work! Your learners will appreciate these improvements.".to_string(),
            "Excellent! You're creating more accessible content.".to_string(),
        ];
    }
    
    fn initialize_progress_messages(&mut self) {
        self.progress_messages = vec![
            "Your content is getting clearer and more engaging!".to_string(),
            "Great progress! You're building better learning experiences.".to_string(),
            "Fantastic improvement! Your writing skills are developing well.".to_string(),
        ];
    }
}

impl Default for PersonalizationSettings {
    fn default() -> Self {
        Self {
            experience_level: UserExperienceLevel::Intermediate,
            notification_level: NotificationLevel::Standard,
            show_technical_details: false,
            use_encouraging_tone: true,
            include_learning_tips: true,
            group_similar_issues: true,
            prioritize_actionable_feedback: true,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_feedback_generation() {
        let feedback_system = FeedbackSystem::new();
        
        // Create mock validation results
        let validation_result = ValidationResult {
            validator_name: "readability".to_string(),
            score: 0.7,
            issues: vec![
                ValidationIssue {
                    issue_type: IssueType::Readability,
                    severity: IssueSeverity::Warning,
                    message: "Sentence too long".to_string(),
                    description: Some("Consider breaking this into shorter sentences".to_string()),
                    location: ContentLocation {
                        section: Some("Introduction".to_string()),
                        line: Some(5),
                        character_range: None,
                        slide_number: None,
                        question_number: None,
                    },
                    suggestions: vec!["Break into shorter sentences".to_string()],
                    auto_fixable: false,
                }
            ],
            metadata: ValidationMetadata {
                execution_time_ms: 100,
                content_analyzed: ContentAnalysis {
                    word_count: 500,
                    section_count: 3,
                    slide_count: None,
                    question_count: None,
                    reading_level: Some(8.5),
                },
                validator_version: "1.0.0".to_string(),
                timestamp: chrono::Utc::now(),
            },
        };
        
        let content = GeneratedContent {
            content_type: ContentType::Slides,
            title: "Test Content".to_string(),
            content: "This is test content.".to_string(),
            metadata: crate::content::generator::ContentMetadata {
                word_count: 500,
                estimated_duration: "10 minutes".to_string(),
                difficulty_level: "Intermediate".to_string(),
            },
        };
        
        let feedback = feedback_system.generate_feedback(
            &[validation_result],
            &content,
            None,
        ).unwrap();
        
        assert!(!feedback.issue_groups.is_empty());
        assert!(!feedback.positive_highlights.is_empty());
        assert!(feedback.overall_summary.overall_score > 0.0);
    }
    
    #[test]
    fn test_issue_categorization() {
        let feedback_system = FeedbackSystem::new();
        
        assert_eq!(
            feedback_system.map_issue_to_category(&IssueType::Readability),
            IssueCategory::ReadabilityAndClarity
        );
        
        assert_eq!(
            feedback_system.map_issue_to_category(&IssueType::Structure),
            IssueCategory::OrganizationAndStructure
        );
        
        assert_eq!(
            feedback_system.map_issue_to_category(&IssueType::Grammar),
            IssueCategory::LanguageAndGrammar
        );
    }
}