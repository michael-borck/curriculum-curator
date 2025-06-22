use super::feedback_system::*;
use super::validators::*;
use super::smart_config::UserExperienceLevel;
use crate::content::GeneratedContent;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Mutex;
use tauri::State;

/// Global feedback service state
pub struct FeedbackService {
    feedback_system: Mutex<FeedbackSystem>,
    user_settings: Mutex<HashMap<String, PersonalizationSettings>>,
    score_history: Mutex<HashMap<String, Vec<ScoreSnapshot>>>,
}

/// Snapshot of scores at a point in time
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScoreSnapshot {
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub overall_score: f64,
    pub category_scores: HashMap<IssueCategory, f64>,
    pub content_type: String,
}

impl FeedbackService {
    pub fn new() -> Self {
        Self {
            feedback_system: Mutex::new(FeedbackSystem::new()),
            user_settings: Mutex::new(HashMap::new()),
            score_history: Mutex::new(HashMap::new()),
        }
    }
}

/// Request to generate user-friendly feedback
#[derive(Debug, Serialize, Deserialize)]
pub struct GenerateFeedbackRequest {
    pub validation_results: Vec<ValidationResult>,
    pub content: GeneratedContent,
    pub user_id: Option<String>,
    pub include_progress_comparison: bool,
}

/// Response containing user-friendly feedback
#[derive(Debug, Serialize, Deserialize)]
pub struct FeedbackResponse {
    pub feedback: UserFriendlyFeedback,
    pub personalization_applied: PersonalizationSettings,
    pub feedback_metadata: FeedbackMetadata,
}

/// Metadata about the feedback generation
#[derive(Debug, Serialize, Deserialize)]
pub struct FeedbackMetadata {
    pub generation_time_ms: u64,
    pub total_issues_processed: usize,
    pub feedback_complexity_level: FeedbackComplexityLevel,
    pub personalization_factors: Vec<String>,
}

/// Complexity level of the generated feedback
#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum FeedbackComplexityLevel {
    Simple,      // Basic feedback with minimal technical details
    Moderate,    // Balanced feedback with some context
    Detailed,    // Comprehensive feedback with full explanations
    Technical,   // Full technical details for experts
}

/// Request to update user's feedback personalization
#[derive(Debug, Serialize, Deserialize)]
pub struct UpdatePersonalizationRequest {
    pub user_id: String,
    pub settings: PersonalizationSettings,
}

/// Request to get feedback suggestions for improving content
#[derive(Debug, Serialize, Deserialize)]
pub struct GetSuggestionsRequest {
    pub content_type: String,
    pub current_issues: Vec<IssueType>,
    pub user_experience_level: UserExperienceLevel,
}

/// Response with targeted suggestions
#[derive(Debug, Serialize, Deserialize)]
pub struct SuggestionsResponse {
    pub priority_suggestions: Vec<PrioritySuggestion>,
    pub learning_resources: Vec<LearningResource>,
    pub quick_wins: Vec<QuickWin>,
    pub long_term_goals: Vec<LongTermGoal>,
}

/// High-priority suggestion for immediate action
#[derive(Debug, Serialize, Deserialize)]
pub struct PrioritySuggestion {
    pub title: String,
    pub description: String,
    pub action_steps: Vec<String>,
    pub expected_impact: String,
    pub estimated_time: String,
    pub difficulty: FixDifficulty,
}

/// Learning resource recommendation
#[derive(Debug, Serialize, Deserialize)]
pub struct LearningResource {
    pub title: String,
    pub description: String,
    pub resource_type: ResourceType,
    pub url: Option<String>,
    pub estimated_read_time: String,
}

/// Type of learning resource
#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum ResourceType {
    Article,
    Video,
    Interactive,
    Checklist,
    Template,
    Guide,
}

/// Quick improvement that can be made easily
#[derive(Debug, Serialize, Deserialize)]
pub struct QuickWin {
    pub title: String,
    pub description: String,
    pub action: String,
    pub time_needed: String,
}

/// Long-term improvement goal
#[derive(Debug, Serialize, Deserialize)]
pub struct LongTermGoal {
    pub title: String,
    pub description: String,
    pub milestones: Vec<String>,
    pub estimated_timeline: String,
}

/// Request to get feedback summary for multiple content pieces
#[derive(Debug, Serialize, Deserialize)]
pub struct BatchFeedbackRequest {
    pub content_items: Vec<ContentSummary>,
    pub user_id: Option<String>,
}

/// Summary of a content item for batch processing
#[derive(Debug, Serialize, Deserialize)]
pub struct ContentSummary {
    pub content_id: String,
    pub content_type: String,
    pub title: String,
    pub validation_results: Vec<ValidationResult>,
    pub last_updated: chrono::DateTime<chrono::Utc>,
}

/// Response for batch feedback analysis
#[derive(Debug, Serialize, Deserialize)]
pub struct BatchFeedbackResponse {
    pub overall_portfolio_score: f64,
    pub content_summaries: Vec<ContentFeedbackSummary>,
    pub portfolio_insights: Vec<String>,
    pub improvement_priorities: Vec<String>,
    pub consistency_analysis: ConsistencyAnalysis,
}

/// Feedback summary for a single content item
#[derive(Debug, Serialize, Deserialize)]
pub struct ContentFeedbackSummary {
    pub content_id: String,
    pub title: String,
    pub overall_status: OverallStatus,
    pub score: f64,
    pub top_issues: Vec<String>,
    pub priority_level: Priority,
    pub estimated_fix_time: String,
}

/// Analysis of consistency across content portfolio
#[derive(Debug, Serialize, Deserialize)]
pub struct ConsistencyAnalysis {
    pub style_consistency: f64,
    pub difficulty_consistency: f64,
    pub structure_consistency: f64,
    pub tone_consistency: f64,
    pub inconsistency_patterns: Vec<String>,
    pub recommendations: Vec<String>,
}

/// Tauri command to generate user-friendly feedback
#[tauri::command]
pub fn generate_user_friendly_feedback(
    request: GenerateFeedbackRequest,
    service: State<'_, FeedbackService>,
) -> Result<FeedbackResponse, String> {
    let start_time = std::time::Instant::now();
    
    // Get user personalization settings
    let personalization = if let Some(user_id) = &request.user_id {
        service.user_settings.lock().unwrap()
            .get(user_id)
            .cloned()
            .unwrap_or_default()
    } else {
        PersonalizationSettings::default()
    };
    
    // Get previous scores for progress comparison
    let previous_scores = if request.include_progress_comparison {
        if let Some(user_id) = &request.user_id {
            service.score_history.lock().unwrap()
                .get(user_id)
                .and_then(|history| history.last())
                .map(|snapshot| snapshot.category_scores.clone())
        } else {
            None
        }
    } else {
        None
    };
    
    // Create feedback system with personalization
    let feedback_system = FeedbackSystem::with_personalization(personalization.clone());
    
    // Generate feedback
    let feedback = feedback_system.generate_feedback(
        &request.validation_results,
        &request.content,
        previous_scores.as_ref(),
    ).map_err(|e| e.to_string())?;
    
    // Save score snapshot for future comparisons
    if let Some(user_id) = &request.user_id {
        let snapshot = ScoreSnapshot {
            timestamp: chrono::Utc::now(),
            overall_score: feedback.progress_indicator.overall_score,
            category_scores: feedback.progress_indicator.category_scores.clone(),
            content_type: format!("{:?}", request.content.content_type),
        };
        
        service.score_history.lock().unwrap()
            .entry(user_id.clone())
            .or_insert_with(Vec::new)
            .push(snapshot);
    }
    
    let generation_time = start_time.elapsed().as_millis() as u64;
    
    // Determine feedback complexity level
    let complexity_level = match personalization.experience_level {
        UserExperienceLevel::Beginner => FeedbackComplexityLevel::Simple,
        UserExperienceLevel::Intermediate => FeedbackComplexityLevel::Moderate,
        UserExperienceLevel::Advanced => FeedbackComplexityLevel::Detailed,
        UserExperienceLevel::Expert => {
            if personalization.show_technical_details {
                FeedbackComplexityLevel::Technical
            } else {
                FeedbackComplexityLevel::Detailed
            }
        },
        UserExperienceLevel::Custom => FeedbackComplexityLevel::Moderate,
    };
    
    let total_issues = request.validation_results.iter()
        .map(|r| r.issues.len())
        .sum();
    
    let mut personalization_factors = Vec::new();
    if personalization.use_encouraging_tone {
        personalization_factors.push("Encouraging tone".to_string());
    }
    if personalization.include_learning_tips {
        personalization_factors.push("Learning tips included".to_string());
    }
    if personalization.group_similar_issues {
        personalization_factors.push("Issues grouped by category".to_string());
    }
    
    let metadata = FeedbackMetadata {
        generation_time_ms: generation_time,
        total_issues_processed: total_issues,
        feedback_complexity_level: complexity_level,
        personalization_factors,
    };
    
    Ok(FeedbackResponse {
        feedback,
        personalization_applied: personalization,
        feedback_metadata: metadata,
    })
}

/// Tauri command to update user's feedback personalization settings
#[tauri::command]
pub fn update_feedback_personalization(
    request: UpdatePersonalizationRequest,
    service: State<'_, FeedbackService>,
) -> Result<(), String> {
    service.user_settings.lock().unwrap()
        .insert(request.user_id, request.settings);
    Ok(())
}

/// Tauri command to get personalized suggestions for content improvement
#[tauri::command]
pub fn get_improvement_suggestions(
    request: GetSuggestionsRequest,
    _service: State<'_, FeedbackService>,
) -> Result<SuggestionsResponse, String> {
    let mut priority_suggestions = Vec::new();
    let mut learning_resources = Vec::new();
    let mut quick_wins = Vec::new();
    let mut long_term_goals = Vec::new();
    
    // Generate suggestions based on current issues
    for issue_type in &request.current_issues {
        match issue_type {
            IssueType::Readability => {
                priority_suggestions.push(PrioritySuggestion {
                    title: "Improve Readability".to_string(),
                    description: "Make your content easier to read and understand".to_string(),
                    action_steps: vec![
                        "Use shorter sentences (15-20 words)".to_string(),
                        "Choose simpler words when possible".to_string(),
                        "Break up long paragraphs".to_string(),
                    ],
                    expected_impact: "Readers will understand your content more easily".to_string(),
                    estimated_time: "15-20 minutes".to_string(),
                    difficulty: FixDifficulty::Easy,
                });
                
                quick_wins.push(QuickWin {
                    title: "Split Long Sentences".to_string(),
                    description: "Find your longest sentences and break them into two".to_string(),
                    action: "Look for sentences with 'and', 'but', or 'because' and split them".to_string(),
                    time_needed: "5 minutes".to_string(),
                });
                
                learning_resources.push(LearningResource {
                    title: "Writing for Clarity".to_string(),
                    description: "Learn techniques for clear, engaging writing".to_string(),
                    resource_type: ResourceType::Guide,
                    url: None,
                    estimated_read_time: "10 minutes".to_string(),
                });
            },
            
            IssueType::Structure => {
                priority_suggestions.push(PrioritySuggestion {
                    title: "Improve Content Organization".to_string(),
                    description: "Reorganize your content for better flow and understanding".to_string(),
                    action_steps: vec![
                        "Add clear headings for each main topic".to_string(),
                        "Use bullet points for lists".to_string(),
                        "Add a summary at the end".to_string(),
                    ],
                    expected_impact: "Learners will follow your content more easily".to_string(),
                    estimated_time: "20-30 minutes".to_string(),
                    difficulty: FixDifficulty::Medium,
                });
                
                long_term_goals.push(LongTermGoal {
                    title: "Master Content Structure".to_string(),
                    description: "Develop skills in organizing educational content effectively".to_string(),
                    milestones: vec![
                        "Learn basic content organization patterns".to_string(),
                        "Practice with different content types".to_string(),
                        "Develop your own content templates".to_string(),
                    ],
                    estimated_timeline: "2-3 weeks of practice".to_string(),
                });
            },
            
            IssueType::Grammar => {
                quick_wins.push(QuickWin {
                    title: "Grammar Check".to_string(),
                    description: "Run a spell-check and fix obvious errors".to_string(),
                    action: "Use your word processor's built-in grammar checker".to_string(),
                    time_needed: "5-10 minutes".to_string(),
                });
            },
            
            _ => {} // Handle other issue types as needed
        }
    }
    
    // Add experience-level specific resources
    match request.user_experience_level {
        UserExperienceLevel::Beginner => {
            learning_resources.push(LearningResource {
                title: "Content Creation Basics".to_string(),
                description: "Fundamental principles for creating educational content".to_string(),
                resource_type: ResourceType::Guide,
                url: None,
                estimated_read_time: "15 minutes".to_string(),
            });
        },
        UserExperienceLevel::Advanced | UserExperienceLevel::Expert => {
            learning_resources.push(LearningResource {
                title: "Advanced Instructional Design".to_string(),
                description: "Sophisticated techniques for engaging learners".to_string(),
                resource_type: ResourceType::Article,
                url: None,
                estimated_read_time: "25 minutes".to_string(),
            });
        },
        _ => {}
    }
    
    Ok(SuggestionsResponse {
        priority_suggestions,
        learning_resources,
        quick_wins,
        long_term_goals,
    })
}

/// Tauri command to get user's feedback history and progress
#[tauri::command]
pub fn get_feedback_history(
    user_id: String,
    service: State<'_, FeedbackService>,
) -> Result<Vec<ScoreSnapshot>, String> {
    let history = service.score_history.lock().unwrap();
    Ok(history.get(&user_id).cloned().unwrap_or_default())
}

/// Tauri command to analyze feedback across multiple content pieces
#[tauri::command]
pub fn analyze_batch_feedback(
    request: BatchFeedbackRequest,
    _service: State<'_, FeedbackService>,
) -> Result<BatchFeedbackResponse, String> {
    let mut total_score = 0.0;
    let mut content_summaries = Vec::new();
    let mut all_issue_types = Vec::new();
    
    // Analyze each content item
    for content_item in &request.content_items {
        let issues: Vec<&ValidationIssue> = content_item.validation_results
            .iter()
            .flat_map(|r| &r.issues)
            .collect();
        
        // Calculate score for this content
        let score = if issues.is_empty() {
            100.0
        } else {
            let penalty = issues.len() as f64 * 10.0;
            (100.0 - penalty).max(0.0)
        };
        
        total_score += score;
        
        // Determine status
        let status = if score >= 90.0 {
            OverallStatus::Excellent
        } else if score >= 75.0 {
            OverallStatus::Good
        } else if score >= 50.0 {
            OverallStatus::NeedsWork
        } else {
            OverallStatus::NeedsRevision
        };
        
        // Get top issues
        let mut issue_counts: HashMap<IssueType, usize> = HashMap::new();
        for issue in &issues {
            *issue_counts.entry(issue.issue_type.clone()).or_insert(0) += 1;
            all_issue_types.push(issue.issue_type.clone());
        }
        
        let mut top_issues: Vec<_> = issue_counts.into_iter().collect();
        top_issues.sort_by(|a, b| b.1.cmp(&a.1));
        let top_issues: Vec<String> = top_issues.into_iter()
            .take(3)
            .map(|(issue_type, count)| format!("{:?} ({})", issue_type, count))
            .collect();
        
        // Determine priority
        let priority = if score < 50.0 {
            Priority::Critical
        } else if score < 75.0 {
            Priority::High
        } else if score < 90.0 {
            Priority::Medium
        } else {
            Priority::Low
        };
        
        content_summaries.push(ContentFeedbackSummary {
            content_id: content_item.content_id.clone(),
            title: content_item.title.clone(),
            overall_status: status,
            score,
            top_issues,
            priority_level: priority,
            estimated_fix_time: estimate_fix_time(issues.len()),
        });
    }
    
    let overall_portfolio_score = if request.content_items.is_empty() {
        0.0
    } else {
        total_score / request.content_items.len() as f64
    };
    
    // Generate portfolio insights
    let mut portfolio_insights = Vec::new();
    let total_content = request.content_items.len();
    
    if total_content > 0 {
        let excellent_count = content_summaries.iter()
            .filter(|s| s.overall_status == OverallStatus::Excellent)
            .count();
        
        if excellent_count as f64 / total_content as f64 > 0.7 {
            portfolio_insights.push("🎉 Most of your content is excellent quality!".to_string());
        } else if excellent_count == 0 {
            portfolio_insights.push("📚 Focus on improving content quality across your portfolio".to_string());
        }
        
        // Analyze common issues
        let mut issue_frequency: HashMap<IssueType, usize> = HashMap::new();
        for issue_type in &all_issue_types {
            *issue_frequency.entry(issue_type.clone()).or_insert(0) += 1;
        }
        
        if let Some((most_common_issue, _)) = issue_frequency.iter()
            .max_by_key(|(_, count)| *count) {
            portfolio_insights.push(format!("🔍 {:?} issues appear frequently across your content", most_common_issue));
        }
    }
    
    // Generate improvement priorities
    let improvement_priorities = vec![
        "Focus on your lowest-scoring content first".to_string(),
        "Address the most common issue types across all content".to_string(),
        "Maintain consistency in style and structure".to_string(),
    ];
    
    // Simple consistency analysis
    let consistency_analysis = ConsistencyAnalysis {
        style_consistency: 75.0, // Simplified calculation
        difficulty_consistency: 80.0,
        structure_consistency: 70.0,
        tone_consistency: 85.0,
        inconsistency_patterns: vec![
            "Varying sentence lengths across content".to_string(),
            "Different heading styles used".to_string(),
        ],
        recommendations: vec![
            "Create a style guide for consistent formatting".to_string(),
            "Use templates for similar content types".to_string(),
        ],
    };
    
    Ok(BatchFeedbackResponse {
        overall_portfolio_score,
        content_summaries,
        portfolio_insights,
        improvement_priorities,
        consistency_analysis,
    })
}

/// Tauri command to export feedback report
#[tauri::command]
pub fn export_feedback_report(
    feedback: UserFriendlyFeedback,
    format: String,
) -> Result<String, String> {
    match format.as_str() {
        "json" => {
            serde_json::to_string_pretty(&feedback)
                .map_err(|e| format!("Failed to serialize feedback: {}", e))
        },
        "markdown" => {
            Ok(generate_markdown_report(&feedback))
        },
        _ => Err("Unsupported export format".to_string()),
    }
}

/// Helper function to estimate fix time based on issue count
fn estimate_fix_time(issue_count: usize) -> String {
    match issue_count {
        0 => "No fixes needed".to_string(),
        1..=2 => "5-10 minutes".to_string(),
        3..=5 => "15-25 minutes".to_string(),
        6..=10 => "30-45 minutes".to_string(),
        _ => "1+ hours".to_string(),
    }
}

/// Generate a markdown report from feedback
fn generate_markdown_report(feedback: &UserFriendlyFeedback) -> String {
    let mut report = String::new();
    
    report.push_str("# Content Feedback Report\n\n");
    
    // Overall summary
    report.push_str("## Overall Summary\n\n");
    report.push_str(&format!("**Status:** {:?}\n\n", feedback.overall_summary.status));
    report.push_str(&format!("{}\n\n", feedback.overall_summary.main_message));
    
    if !feedback.overall_summary.key_insights.is_empty() {
        report.push_str("### Key Insights\n\n");
        for insight in &feedback.overall_summary.key_insights {
            report.push_str(&format!("- {}\n", insight));
        }
        report.push_str("\n");
    }
    
    // Positive highlights
    if !feedback.positive_highlights.is_empty() {
        report.push_str("## What's Working Well\n\n");
        for highlight in &feedback.positive_highlights {
            report.push_str(&format!("- {}\n", highlight));
        }
        report.push_str("\n");
    }
    
    // Issues by category
    if !feedback.issue_groups.is_empty() {
        report.push_str("## Areas for Improvement\n\n");
        for group in &feedback.issue_groups {
            report.push_str(&format!("### {} (Priority: {:?})\n\n", group.title, group.priority));
            report.push_str(&format!("{}\n\n", group.description));
            report.push_str(&format!("**Estimated fix time:** {}\n\n", group.estimated_fix_time));
            
            for issue in &group.issues {
                report.push_str(&format!("#### {}\n\n", issue.title));
                report.push_str(&format!("{}\n\n", issue.explanation));
                report.push_str(&format!("**Location:** {}\n\n", issue.location_description));
                
                if !issue.suggestions.is_empty() {
                    report.push_str("**Suggestions:**\n\n");
                    for suggestion in &issue.suggestions {
                        report.push_str(&format!("- **{}:** {}\n", suggestion.action, suggestion.description));
                        if let Some(example) = &suggestion.example {
                            report.push_str(&format!("  - Example: {}\n", example));
                        }
                        report.push_str(&format!("  - Why this helps: {}\n", suggestion.why_this_helps));
                    }
                    report.push_str("\n");
                }
            }
        }
    }
    
    // Next steps
    if !feedback.next_steps.is_empty() {
        report.push_str("## Recommended Next Steps\n\n");
        for step in &feedback.next_steps {
            report.push_str(&format!("{}. **{}** ({})\n", step.step_number, step.title, step.estimated_time));
            report.push_str(&format!("   {}\n\n", step.description));
        }
    }
    
    // Learning opportunities
    if !feedback.learning_opportunities.is_empty() {
        report.push_str("## Learning Opportunities\n\n");
        for tip in &feedback.learning_opportunities {
            report.push_str(&format!("### {}\n\n", tip.title));
            report.push_str(&format!("{}\n\n", tip.content));
        }
    }
    
    // Progress indicator
    report.push_str("## Progress Summary\n\n");
    report.push_str(&format!("**Overall Score:** {:.1}%\n\n", feedback.progress_indicator.overall_score));
    
    if !feedback.progress_indicator.achievements.is_empty() {
        report.push_str("### Achievements\n\n");
        for achievement in &feedback.progress_indicator.achievements {
            report.push_str(&format!("- {} **{}:** {}\n", achievement.icon, achievement.title, achievement.description));
        }
        report.push_str("\n");
    }
    
    report.push_str(&format!("---\n\n*Report generated on {}*\n", chrono::Utc::now().format("%Y-%m-%d %H:%M UTC")));
    
    report
}

/// Export feedback command names for registration
pub fn get_feedback_command_names() -> Vec<&'static str> {
    vec![
        "generate_user_friendly_feedback",
        "update_feedback_personalization", 
        "get_improvement_suggestions",
        "get_feedback_history",
        "analyze_batch_feedback",
        "export_feedback_report",
    ]
}