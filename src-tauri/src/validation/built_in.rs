use super::validators::*;
use crate::content::{GeneratedContent, ContentType};
use anyhow::Result;
use chrono::Utc;
use std::collections::HashMap;

/// Helper trait for string formatting
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

/// Enhanced structure validator for educational content organization with pedagogical validation
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct StructureValidator {
    required_sections: HashMap<ContentType, Vec<String>>,
    pedagogical_patterns: HashMap<ContentType, Vec<PedagogicalPattern>>,
    config: StructureConfig,
}

/// Configuration for structure validation
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct StructureConfig {
    pub enforce_pedagogical_flow: bool,
    pub require_learning_objectives: bool,
    pub require_assessment_alignment: bool,
    pub min_sections: HashMap<ContentType, usize>,
    pub max_sections: HashMap<ContentType, usize>,
    pub required_flow_patterns: HashMap<ContentType, Vec<String>>,
    pub enable_auto_fix: bool,
}

/// Educational patterns that should appear in well-structured content
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct PedagogicalPattern {
    pub name: String,
    pub description: String,
    pub keywords: Vec<String>,
    pub section_order: Option<usize>,
    pub required: bool,
}

/// Detailed analysis of content structure
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct StructureAnalysis {
    pub detected_sections: Vec<DetectedSection>,
    pub missing_sections: Vec<String>,
    pub flow_score: f64,
    pub organization_score: f64,
    pub pedagogical_alignment: f64,
}

/// Information about a detected section
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct DetectedSection {
    pub name: String,
    pub line_number: usize,
    pub content_preview: String,
    pub pedagogical_purpose: Option<String>,
    pub quality_score: f64,
}

impl Default for StructureConfig {
    fn default() -> Self {
        let mut min_sections = HashMap::new();
        let mut max_sections = HashMap::new();
        let mut required_flow_patterns = HashMap::new();
        
        // Minimum sections for each content type
        min_sections.insert(ContentType::Slides, 3);
        min_sections.insert(ContentType::Quiz, 2);
        min_sections.insert(ContentType::Worksheet, 2);
        min_sections.insert(ContentType::InstructorNotes, 2);
        min_sections.insert(ContentType::ActivityGuide, 3);
        
        // Maximum sections for readability
        max_sections.insert(ContentType::Slides, 10);
        max_sections.insert(ContentType::Quiz, 6);
        max_sections.insert(ContentType::Worksheet, 8);
        max_sections.insert(ContentType::InstructorNotes, 6);
        max_sections.insert(ContentType::ActivityGuide, 12);
        
        // Educational flow patterns
        required_flow_patterns.insert(ContentType::Slides, vec![
            "introduction".to_string(),
            "objectives".to_string(),
            "content".to_string(),
            "conclusion".to_string(),
        ]);
        
        required_flow_patterns.insert(ContentType::Quiz, vec![
            "instructions".to_string(),
            "questions".to_string(),
        ]);
        
        Self {
            enforce_pedagogical_flow: true,
            require_learning_objectives: true,
            require_assessment_alignment: true,
            min_sections,
            max_sections,
            required_flow_patterns,
            enable_auto_fix: true,
        }
    }
}

impl StructureValidator {
    pub fn new() -> Self {
        Self::with_config(StructureConfig::default())
    }
    
    pub fn with_config(config: StructureConfig) -> Self {
        let mut required_sections = HashMap::new();
        let mut pedagogical_patterns = HashMap::new();
        
        // Enhanced required sections with pedagogical considerations
        required_sections.insert(ContentType::Slides, vec![
            "title".to_string(),
            "learning_objectives".to_string(),
            "introduction".to_string(),
            "main_content".to_string(),
            "practice".to_string(),
            "summary".to_string(),
            "next_steps".to_string(),
        ]);
        
        required_sections.insert(ContentType::Quiz, vec![
            "instructions".to_string(),
            "learning_objectives".to_string(),
            "questions".to_string(),
            "answer_key".to_string(),
            "grading_criteria".to_string(),
        ]);
        
        required_sections.insert(ContentType::Worksheet, vec![
            "title".to_string(),
            "learning_objectives".to_string(),
            "instructions".to_string(),
            "warm_up".to_string(),
            "main_exercises".to_string(),
            "reflection".to_string(),
        ]);
        
        required_sections.insert(ContentType::InstructorNotes, vec![
            "lesson_overview".to_string(),
            "learning_objectives".to_string(),
            "key_concepts".to_string(),
            "teaching_strategies".to_string(),
            "timing_guide".to_string(),
            "common_misconceptions".to_string(),
            "assessment_notes".to_string(),
        ]);
        
        required_sections.insert(ContentType::ActivityGuide, vec![
            "activity_overview".to_string(),
            "learning_objectives".to_string(),
            "materials_needed".to_string(),
            "preparation_steps".to_string(),
            "activity_steps".to_string(),
            "debrief_questions".to_string(),
            "assessment_criteria".to_string(),
        ]);
        
        // Define pedagogical patterns for each content type
        pedagogical_patterns.insert(ContentType::Slides, vec![
            PedagogicalPattern {
                name: "Hook/Attention Grabber".to_string(),
                description: "Engaging opening to capture attention".to_string(),
                keywords: vec!["hook".to_string(), "attention".to_string(), "opener".to_string(), "question".to_string()],
                section_order: Some(1),
                required: true,
            },
            PedagogicalPattern {
                name: "Learning Objectives".to_string(),
                description: "Clear statements of what students will learn".to_string(),
                keywords: vec!["objectives".to_string(), "goals".to_string(), "will be able to".to_string(), "by the end".to_string()],
                section_order: Some(2),
                required: true,
            },
            PedagogicalPattern {
                name: "Prior Knowledge Activation".to_string(),
                description: "Connection to existing knowledge".to_string(),
                keywords: vec!["recall".to_string(), "previous".to_string(), "remember".to_string(), "review".to_string()],
                section_order: Some(3),
                required: false,
            },
            PedagogicalPattern {
                name: "Content Delivery".to_string(),
                description: "Main instructional content".to_string(),
                keywords: vec!["content".to_string(), "explanation".to_string(), "information".to_string(), "concept".to_string()],
                section_order: Some(4),
                required: true,
            },
            PedagogicalPattern {
                name: "Guided Practice".to_string(),
                description: "Structured practice opportunities".to_string(),
                keywords: vec!["practice".to_string(), "try".to_string(), "exercise".to_string(), "example".to_string()],
                section_order: Some(5),
                required: true,
            },
            PedagogicalPattern {
                name: "Closure/Summary".to_string(),
                description: "Wrap-up and key point reinforcement".to_string(),
                keywords: vec!["summary".to_string(), "conclusion".to_string(), "key points".to_string(), "review".to_string()],
                section_order: Some(6),
                required: true,
            },
        ]);

        Self { 
            required_sections, 
            pedagogical_patterns,
            config,
        }
    }
    
    /// Analyze the overall structure of content
    fn analyze_structure(&self, content: &GeneratedContent) -> Result<StructureAnalysis> {
        let lines: Vec<&str> = content.content.lines().collect();
        let mut detected_sections = Vec::new();
        let mut current_section: Option<DetectedSection> = None;
        
        for (line_num, line) in lines.iter().enumerate() {
            if self.is_section_header(line) {
                // Save previous section if it exists
                if let Some(section) = current_section.take() {
                    detected_sections.push(section);
                }
                
                // Start new section
                let section_name = self.extract_section_name(line);
                current_section = Some(DetectedSection {
                    name: section_name.clone(),
                    line_number: line_num + 1,
                    content_preview: line.chars().take(100).collect(),
                    pedagogical_purpose: self.identify_pedagogical_purpose(&section_name, &content.content_type),
                    quality_score: self.assess_section_quality(&section_name, &content.content_type),
                });
            }
        }
        
        // Add the last section
        if let Some(section) = current_section {
            detected_sections.push(section);
        }
        
        // Identify missing sections
        let required_sections = self.required_sections.get(&content.content_type).cloned().unwrap_or_default();
        let detected_names: Vec<String> = detected_sections.iter().map(|s| s.name.to_lowercase()).collect();
        let missing_sections: Vec<String> = required_sections.into_iter()
            .filter(|req| !detected_names.iter().any(|det| det.contains(&req.to_lowercase())))
            .collect();
        
        // Calculate scores
        let flow_score = self.calculate_flow_score(&detected_sections, &content.content_type);
        let organization_score = self.calculate_organization_score(&detected_sections);
        let pedagogical_alignment = self.calculate_pedagogical_alignment(&detected_sections, &content.content_type);
        
        Ok(StructureAnalysis {
            detected_sections,
            missing_sections,
            flow_score,
            organization_score,
            pedagogical_alignment,
        })
    }
    
    /// Check if a line represents a section header
    fn is_section_header(&self, line: &str) -> bool {
        let trimmed = line.trim();
        
        // Markdown headers
        if trimmed.starts_with('#') {
            return true;
        }
        
        // ALL CAPS headers (but not too short to avoid false positives)
        if trimmed.len() > 3 && trimmed == trimmed.to_uppercase() && trimmed.chars().any(|c| c.is_alphabetic()) {
            return true;
        }
        
        // Common section patterns
        let section_patterns = [
            "objectives:", "objective:", "goals:", "introduction:", "overview:",
            "materials:", "steps:", "instructions:", "summary:", "conclusion:",
            "assessment:", "practice:", "exercises:", "activities:", "resources:"
        ];
        
        section_patterns.iter().any(|pattern| trimmed.to_lowercase().starts_with(pattern))
    }
    
    /// Extract section name from header line
    fn extract_section_name(&self, line: &str) -> String {
        let cleaned = line.trim()
            .trim_start_matches('#')
            .trim_end_matches(':')
            .trim()
            .to_string();
        
        if cleaned.is_empty() {
            "unnamed_section".to_string()
        } else {
            cleaned.to_lowercase().replace(' ', "_")
        }
    }
    
    /// Identify the pedagogical purpose of a section
    fn identify_pedagogical_purpose(&self, section_name: &str, content_type: &ContentType) -> Option<String> {
        if let Some(patterns) = self.pedagogical_patterns.get(content_type) {
            for pattern in patterns {
                if pattern.keywords.iter().any(|keyword| section_name.contains(keyword)) {
                    return Some(pattern.description.clone());
                }
            }
        }
        None
    }
    
    /// Assess the quality of a section based on its name and type
    fn assess_section_quality(&self, section_name: &str, content_type: &ContentType) -> f64 {
        let mut score: f64 = 0.5; // Base score
        
        // Check if it matches pedagogical patterns
        if let Some(patterns) = self.pedagogical_patterns.get(content_type) {
            for pattern in patterns {
                if pattern.keywords.iter().any(|keyword| section_name.contains(keyword)) {
                    score += 0.3;
                    if pattern.required {
                        score += 0.2;
                    }
                    break;
                }
            }
        }
        
        // Bonus for descriptive names
        if section_name.len() > 5 && section_name.contains('_') {
            score += 0.1;
        }
        
        score.min(1.0)
    }
    
    /// Calculate flow score based on pedagogical patterns
    fn calculate_flow_score(&self, sections: &[DetectedSection], content_type: &ContentType) -> f64 {
        if let Some(patterns) = self.pedagogical_patterns.get(content_type) {
            let mut score = 0.0;
            let mut found_required = 0;
            let total_required = patterns.iter().filter(|p| p.required).count();
            
            for pattern in patterns {
                if sections.iter().any(|s| {
                    pattern.keywords.iter().any(|k| s.name.contains(k))
                }) {
                    score += 1.0;
                    if pattern.required {
                        found_required += 1;
                    }
                }
            }
            
            let pattern_score = score / patterns.len() as f64;
            let required_score = if total_required > 0 {
                found_required as f64 / total_required as f64
            } else {
                1.0
            };
            
            (pattern_score + required_score) / 2.0
        } else {
            0.5 // Default score if no patterns defined
        }
    }
    
    /// Calculate organization score
    fn calculate_organization_score(&self, sections: &[DetectedSection]) -> f64 {
        if sections.is_empty() {
            return 0.0;
        }
        
        let avg_quality: f64 = sections.iter().map(|s| s.quality_score).sum::<f64>() / sections.len() as f64;
        let length_bonus = if sections.len() >= 3 { 0.1 } else { 0.0 };
        
        (avg_quality + length_bonus).min(1.0)
    }
    
    /// Calculate pedagogical alignment score
    fn calculate_pedagogical_alignment(&self, sections: &[DetectedSection], content_type: &ContentType) -> f64 {
        let mut alignment_score: f64 = 0.0;
        
        // Check for presence of key educational elements
        let has_objectives = sections.iter().any(|s| s.name.contains("objective") || s.name.contains("goal"));
        let has_content = sections.iter().any(|s| s.name.contains("content") || s.name.contains("main"));
        let has_closure = sections.iter().any(|s| s.name.contains("summary") || s.name.contains("conclusion"));
        
        if has_objectives { alignment_score += 0.4; }
        if has_content { alignment_score += 0.4; }
        if has_closure { alignment_score += 0.2; }
        
        // Content-type specific bonuses
        match content_type {
            ContentType::Slides => {
                if sections.iter().any(|s| s.name.contains("practice") || s.name.contains("exercise")) {
                    alignment_score += 0.1;
                }
            },
            ContentType::Quiz => {
                if sections.iter().any(|s| s.name.contains("instruction")) {
                    alignment_score += 0.1;
                }
            },
            ContentType::ActivityGuide => {
                if sections.iter().any(|s| s.name.contains("material")) {
                    alignment_score += 0.1;
                }
            },
            _ => {}
        }
        
        alignment_score.min(1.0)
    }
    
    /// Validate required sections
    fn validate_required_sections(&self, content: &GeneratedContent, analysis: &StructureAnalysis) -> (f64, Vec<ValidationIssue>) {
        let mut issues = Vec::new();
        let mut score = 1.0;
        
        if !analysis.missing_sections.is_empty() {
            score = 1.0 - (analysis.missing_sections.len() as f64 * 0.15);
            
            for missing in &analysis.missing_sections {
                let severity = if self.is_critical_section(missing, &content.content_type) {
                    IssueSeverity::Error
                } else {
                    IssueSeverity::Warning
                };
                
                issues.push(
                    ValidationIssue::new(
                        severity,
                        IssueType::Structure,
                        format!("Missing required section: {}", missing),
                        Some(ContentLocation::section(missing.clone())),
                    )
                    .with_remediation_hint(format!(
                        "Add a '{}' section to improve content structure and pedagogical effectiveness", 
                        missing.replace('_', " ")
                    ))
                    .with_auto_fix()
                );
            }
        }
        
        (score.max(0.0), issues)
    }
    
    /// Check if a section is critical for the content type
    fn is_critical_section(&self, section_name: &str, content_type: &ContentType) -> bool {
        let critical_sections = match content_type {
            ContentType::Slides => vec!["title", "learning_objectives", "main_content"],
            ContentType::Quiz => vec!["instructions", "questions"],
            ContentType::Worksheet => vec!["title", "instructions"],
            ContentType::InstructorNotes => vec!["lesson_overview", "learning_objectives"],
            ContentType::ActivityGuide => vec!["activity_overview", "activity_steps"],
        };
        
        critical_sections.iter().any(|&critical| section_name.contains(critical))
    }
    
    /// Validate pedagogical flow patterns
    fn validate_pedagogical_flow(&self, content: &GeneratedContent, analysis: &StructureAnalysis) -> (f64, Vec<ValidationIssue>) {
        let mut issues = Vec::new();
        let score = analysis.flow_score;
        
        if score < 0.6 {
            issues.push(
                ValidationIssue::new(
                    IssueSeverity::Warning,
                    IssueType::PedagogicalAlignment,
                    "Content does not follow recommended pedagogical flow patterns".to_string(),
                    None,
                )
                .with_remediation_hint("Consider reorganizing content to follow: Introduction → Objectives → Content → Practice → Summary".to_string())
                .with_auto_fix()
            );
        }
        
        (score, issues)
    }
    
    /// Validate section count constraints
    fn validate_section_counts(&self, content: &GeneratedContent, analysis: &StructureAnalysis) -> (f64, Vec<ValidationIssue>) {
        let mut issues = Vec::new();
        let mut score = 1.0;
        let section_count = analysis.detected_sections.len();
        
        if let Some(&min_sections) = self.config.min_sections.get(&content.content_type) {
            if section_count < min_sections {
                score *= 0.8;
                issues.push(
                    ValidationIssue::new(
                        IssueSeverity::Warning,
                        IssueType::Structure,
                        format!("Content has {} sections but needs at least {}", section_count, min_sections),
                        None,
                    )
                    .with_remediation_hint("Add more sections to improve content organization".to_string())
                );
            }
        }
        
        if let Some(&max_sections) = self.config.max_sections.get(&content.content_type) {
            if section_count > max_sections {
                score *= 0.9;
                issues.push(
                    ValidationIssue::new(
                        IssueSeverity::Info,
                        IssueType::Structure,
                        format!("Content has {} sections, consider consolidating (recommended max: {})", section_count, max_sections),
                        None,
                    )
                    .with_remediation_hint("Consider combining related sections for better readability".to_string())
                );
            }
        }
        
        (score, issues)
    }
    
    /// Validate learning objectives presence and quality
    fn validate_learning_objectives(&self, content: &GeneratedContent) -> (f64, Vec<ValidationIssue>) {
        let mut issues = Vec::new();
        let mut score = 1.0;
        
        let content_lower = content.content.to_lowercase();
        let has_objectives = content_lower.contains("objective") || content_lower.contains("goal") || 
                           content_lower.contains("will be able to") || content_lower.contains("by the end");
        
        if !has_objectives {
            score = 0.7;
            issues.push(
                ValidationIssue::new(
                    IssueSeverity::Warning,
                    IssueType::LearningObjectives,
                    "Content lacks clear learning objectives".to_string(),
                    None,
                )
                .with_remediation_hint("Add a section with specific, measurable learning objectives".to_string())
                .with_auto_fix()
            );
        } else {
            // Check objective quality
            let objective_quality = self.assess_objective_quality(&content.content);
            if objective_quality < 0.6 {
                score *= 0.9;
                issues.push(
                    ValidationIssue::new(
                        IssueSeverity::Info,
                        IssueType::LearningObjectives,
                        "Learning objectives could be more specific or measurable".to_string(),
                        None,
                    )
                    .with_remediation_hint("Use action verbs and specific criteria in learning objectives".to_string())
                );
            }
        }
        
        (score, issues)
    }
    
    /// Assess the quality of learning objectives
    fn assess_objective_quality(&self, content: &str) -> f64 {
        let action_verbs = ["identify", "explain", "analyze", "evaluate", "create", "apply", 
                          "understand", "demonstrate", "compare", "synthesize"];
        let content_lower = content.to_lowercase();
        
        let verb_count = action_verbs.iter().filter(|&verb| content_lower.contains(verb)).count();
        let has_measurable = content_lower.contains("will be able to") || content_lower.contains("students will");
        
        let mut quality: f64 = 0.5;
        if verb_count > 0 {
            quality += 0.3;
        }
        if has_measurable {
            quality += 0.2;
        }
        
        quality.min(1.0)
    }
    
    /// Validate organizational quality
    fn validate_organization_quality(&self, content: &GeneratedContent, analysis: &StructureAnalysis) -> (f64, Vec<ValidationIssue>) {
        let mut issues = Vec::new();
        let score = analysis.organization_score;
        
        if score < 0.5 {
            issues.push(
                ValidationIssue::new(
                    IssueSeverity::Info,
                    IssueType::Structure,
                    "Content organization could be improved".to_string(),
                    None,
                )
                .with_remediation_hint("Use clear headings and logical section flow".to_string())
            );
        }
        
        // Check for very long sections without subsections
        let lines = content.content.lines().count();
        if lines > 50 && analysis.detected_sections.len() < 3 {
            issues.push(
                ValidationIssue::new(
                    IssueSeverity::Info,
                    IssueType::Structure,
                    "Long content would benefit from more sections".to_string(),
                    None,
                )
                .with_remediation_hint("Break long content into smaller, focused sections".to_string())
            );
        }
        
        (score, issues)
    }
    
    /// Validate assessment alignment
    fn validate_assessment_alignment(&self, content: &GeneratedContent) -> (f64, Vec<ValidationIssue>) {
        let mut issues = Vec::new();
        let mut score = 1.0;
        
        let content_lower = content.content.to_lowercase();
        let has_assessment = content_lower.contains("assessment") || content_lower.contains("quiz") ||
                           content_lower.contains("test") || content_lower.contains("exercise");
        
        match content.content_type {
            ContentType::Slides | ContentType::ActivityGuide => {
                if !has_assessment {
                    score = 0.8;
                    issues.push(
                        ValidationIssue::new(
                            IssueSeverity::Info,
                            IssueType::PedagogicalAlignment,
                            "Content lacks assessment or practice opportunities".to_string(),
                            None,
                        )
                        .with_remediation_hint("Add practice exercises or assessment activities".to_string())
                    );
                }
            },
            _ => {} // Other content types may not require assessment
        }
        
        (score, issues)
    }
    
    /// Generate section template for auto-fix
    fn generate_section_template(&self, section_name: &str, content_type: &ContentType) -> String {
        let temp_str = section_name.replace('_', " ");
        let formatted_name = StringFormatting::to_title_case(temp_str.as_str());
        
        match section_name {
            "learning_objectives" => format!(
                "## {}\n\nBy the end of this {}, students will be able to:\n- [Add specific, measurable objective]\n- [Add another objective]\n- [Add a third objective]\n\n",
                formatted_name,
                match content_type {
                    ContentType::Slides => "lesson",
                    ContentType::ActivityGuide => "activity",
                    ContentType::Worksheet => "worksheet",
                    _ => "content"
                }
            ),
            "introduction" => format!(
                "## {}\n\n[Engaging opening that captures attention and introduces the topic]\n\n**Hook:** [Question, scenario, or interesting fact]\n\n**Context:** [Why this topic matters]\n\n",
                formatted_name
            ),
            "summary" => format!(
                "## {}\n\n### Key Points Covered:\n- [Main concept 1]\n- [Main concept 2]\n- [Main concept 3]\n\n### Next Steps:\n[What students should do next or how this connects to future learning]\n\n",
                formatted_name
            ),
            "materials_needed" => format!(
                "## {}\n\n### Required Materials:\n- [Essential item 1]\n- [Essential item 2]\n\n### Optional Materials:\n- [Enhancement item 1]\n- [Enhancement item 2]\n\n",
                formatted_name
            ),
            "assessment_criteria" => format!(
                "## {}\n\n### Success Criteria:\n- [Criterion 1: What does success look like?]\n- [Criterion 2: How will progress be measured?]\n\n### Evaluation Methods:\n- [Method 1: e.g., observation, quiz, project]\n- [Method 2: e.g., peer review, self-assessment]\n\n",
                formatted_name
            ),
            _ => format!(
                "## {}\n\n[Add {} content here. Consider including:\n- Key information or instructions\n- Examples or explanations\n- Activities or exercises\n- Assessment or reflection questions]\n\n",
                formatted_name,
                section_name.replace('_', " ")
            )
        }
    }
    
    /// Add structure headings to content
    fn add_structure_headings(&self, content: &str) -> String {
        let lines: Vec<&str> = content.lines().collect();
        let mut result = String::new();
        let mut in_section = false;
        
        // Simple heuristic to add headings
        for (i, line) in lines.iter().enumerate() {
            if i == 0 && !line.starts_with('#') {
                result.push_str("# Main Content\n\n");
            }
            
            // Add section breaks for paragraphs
            if line.is_empty() && i > 0 && i < lines.len() - 1 {
                if !in_section && lines[i + 1].len() > 20 {
                    result.push_str(&format!("\n## Section {}\n\n", (i / 10) + 1));
                    in_section = true;
                }
            }
            
            result.push_str(line);
            result.push('\n');
        }
        
        result
    }
    
    /// Reorganize content flow according to pedagogical patterns
    fn reorganize_content_flow(&self, content: &str, content_type: &ContentType) -> String {
        // This is a simplified reorganization - in practice, this would be more sophisticated
        let sections = vec![
            "# Content Overview\n\n",
            "## Learning Objectives\n\n[Objectives to be added]\n\n",
            "## Introduction\n\n",
            content, // Original content goes in the main section
            "\n\n## Summary\n\n[Key points to be summarized]\n\n",
            "## Next Steps\n\n[Follow-up activities or connections]\n\n"
        ];
        
        sections.join("")
    }
    
    /// Count slides in content
    fn count_slides(&self, content: &str) -> Option<usize> {
        let slide_indicators = content.matches("---").count() + 
                             content.matches("# ").count() +
                             content.matches("## ").count();
        if slide_indicators > 0 {
            Some(slide_indicators)
        } else {
            None
        }
    }
    
    /// Count questions in content (existing method)
    fn count_questions(&self, content: &str) -> Option<usize> {
        let question_count = content.matches('?').count() +
                           content.matches("Question:").count() +
                           content.matches("Q:").count();
        if question_count > 0 {
            Some(question_count)
        } else {
            None
        }
    }
}

#[async_trait::async_trait]
impl Validator for StructureValidator {
    fn name(&self) -> &str {
        "structure"
    }

    fn description(&self) -> &str {
        "Validates educational content structure, organization, and pedagogical flow patterns"
    }

    fn version(&self) -> &str {
        "1.0.0"
    }

    fn categories(&self) -> Vec<IssueType> {
        vec![IssueType::Structure, IssueType::Completeness]
    }

    fn supported_content_types(&self) -> Vec<ContentType> {
        vec![
            ContentType::Slides,
            ContentType::Quiz,
            ContentType::Worksheet,
            ContentType::InstructorNotes,
            ContentType::ActivityGuide,
        ]
    }

    async fn validate(&self, content: &GeneratedContent, config: &ValidationConfig) -> Result<ValidationResult> {
        let start_time = std::time::Instant::now();
        let mut issues = Vec::new();
        let mut score = 1.0;

        // Get required sections for this content type
        if let Some(required) = self.required_sections.get(&content.content_type) {
            let content_lower = content.content.to_lowercase();
            let mut missing_sections = Vec::new();

            for section in required {
                // Simple check for section presence (could be made more sophisticated)
                if !content_lower.contains(&section.to_lowercase()) {
                    missing_sections.push(section.clone());
                }
            }

            // Calculate score based on missing sections
            if !missing_sections.is_empty() {
                score = (required.len() - missing_sections.len()) as f64 / required.len() as f64;
                
                for missing in missing_sections {
                    issues.push(
                        ValidationIssue::new(
                            IssueSeverity::Warning,
                            IssueType::Structure,
                            format!("Missing required section: {}", missing),
                            Some(ContentLocation::section(missing.clone())),
                        )
                        .with_remediation_hint(format!("Add a '{}' section to improve content structure", missing))
                        .with_auto_fix()
                    );
                }
            }
        }

        // Check for basic structure elements
        let lines: Vec<&str> = content.content.lines().collect();
        
        // Check for headings/structure
        let has_headings = lines.iter().any(|line| {
            line.starts_with('#') || line.starts_with("##") || 
            line.to_uppercase() == *line && line.len() > 3
        });

        if !has_headings && content.content.len() > 500 {
            issues.push(
                ValidationIssue::new(
                    IssueSeverity::Info,
                    IssueType::Structure,
                    "Content lacks clear section headings".to_string(),
                    None,
                )
                .with_remediation_hint("Add headings to organize content into clear sections".to_string())
            );
            score *= 0.9;
        }

        let execution_time = start_time.elapsed();
        let metadata = ValidationMetadata {
            execution_time_ms: execution_time.as_millis() as u64,
            content_analyzed: ContentAnalysis {
                word_count: content.metadata.word_count,
                section_count: lines.len(),
                slide_count: None,
                question_count: self.count_questions(&content.content),
                reading_level: None,
            },
            validator_version: self.version().to_string(),
            timestamp: Utc::now(),
        };

        let passed = issues.iter().all(|i| i.severity > IssueSeverity::Error);

        Ok(if passed {
            ValidationResult::success(self.name().to_string(), score, metadata)
        } else {
            ValidationResult::failure(self.name().to_string(), score, issues, metadata)
        })
    }

    async fn auto_fix(&self, content: &GeneratedContent, issue: &ValidationIssue) -> Result<Option<String>> {
        if issue.issue_type == IssueType::Structure && issue.message.contains("Missing required section") {
            if let Some(section_name) = issue.message.strip_prefix("Missing required section: ") {
                let template = match section_name {
                    "learning_objectives" => "## Learning Objectives\n\n- [Add specific learning objective here]\n- [Add another objective here]\n\n",
                    "summary" => "## Summary\n\n[Add a brief summary of the key points covered]\n\n",
                    "instructions" => "## Instructions\n\n[Provide clear instructions for completing this content]\n\n",
                    "materials" => "## Materials Needed\n\n- [List required materials]\n- [Add more items as needed]\n\n",
                    "assessment" => "## Assessment\n\n[Describe how learning will be assessed]\n\n",
                    _ => &format!("## {}\n\n[Add {} content here]\n\n", 
                                {
                                    let temp_str = section_name.replace('_', " ");
                                    StringFormatting::to_title_case(temp_str.as_str())
                                }, 
                                section_name.replace('_', " "))
                };
                
                return Ok(Some(format!("Add the following section to your content:\n\n{}", template)));
            }
        }
        
        Ok(None)
    }
}


/// Configuration for readability validation
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ReadabilityConfig {
    /// Minimum Flesch Reading Ease score (0-100, higher = easier)
    pub min_flesch_score: f64,
    /// Maximum sentence length in words
    pub max_sentence_length: usize,
    /// Maximum paragraph length in words
    pub max_paragraph_length: usize,
    /// Maximum syllables per word average
    pub max_syllables_per_word: f64,
    /// Target education level (grades 1-16+)
    pub target_grade_level: Option<f64>,
    /// Content complexity level
    pub complexity_level: ComplexityLevel,
    /// Age-specific thresholds
    pub age_specific_thresholds: AgeSpecificThresholds,
}

/// Complexity levels for different educational contexts
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub enum ComplexityLevel {
    Elementary,    // Grades K-5
    MiddleSchool,  // Grades 6-8
    HighSchool,    // Grades 9-12
    College,       // Undergraduate
    Graduate,      // Graduate level
    Professional,  // Professional/adult learning
}

/// Age-specific readability thresholds
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct AgeSpecificThresholds {
    pub elementary: ReadabilityThresholds,
    pub middle_school: ReadabilityThresholds,
    pub high_school: ReadabilityThresholds,
    pub college: ReadabilityThresholds,
    pub adult: ReadabilityThresholds,
}

/// Specific thresholds for readability metrics
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ReadabilityThresholds {
    pub min_flesch_score: f64,
    pub max_sentence_length: usize,
    pub max_paragraph_length: usize,
    pub max_syllables_per_word: f64,
    pub recommended_flesch_range: (f64, f64),
}

impl Default for ReadabilityConfig {
    fn default() -> Self {
        Self {
            min_flesch_score: 60.0, // Standard reading level
            max_sentence_length: 20,
            max_paragraph_length: 150,
            max_syllables_per_word: 1.6,
            target_grade_level: None,
            complexity_level: ComplexityLevel::HighSchool,
            age_specific_thresholds: AgeSpecificThresholds::default(),
        }
    }
}

/// Sentence analysis metrics
#[derive(Debug, Clone)]
pub struct SentenceAnalysis {
    pub total_sentences: usize,
    pub avg_length: f64,
    pub max_length: usize,
    pub min_length: usize,
    pub long_sentences: usize,
    pub very_long_sentences: usize,
    pub length_variance: f64,
}

impl Default for SentenceAnalysis {
    fn default() -> Self {
        Self {
            total_sentences: 0,
            avg_length: 0.0,
            max_length: 0,
            min_length: 0,
            long_sentences: 0,
            very_long_sentences: 0,
            length_variance: 0.0,
        }
    }
}

impl AgeSpecificThresholds {
    pub fn get_for_level(&self, level: &ComplexityLevel) -> &ReadabilityThresholds {
        match level {
            ComplexityLevel::Elementary => &self.elementary,
            ComplexityLevel::MiddleSchool => &self.middle_school,
            ComplexityLevel::HighSchool => &self.high_school,
            ComplexityLevel::College => &self.college,
            ComplexityLevel::Graduate => &self.adult,
            ComplexityLevel::Professional => &self.adult,
        }
    }
}

impl Default for AgeSpecificThresholds {
    fn default() -> Self {
        Self {
            elementary: ReadabilityThresholds {
                min_flesch_score: 90.0,
                max_sentence_length: 10,
                max_paragraph_length: 50,
                max_syllables_per_word: 1.3,
                recommended_flesch_range: (90.0, 100.0),
            },
            middle_school: ReadabilityThresholds {
                min_flesch_score: 70.0,
                max_sentence_length: 15,
                max_paragraph_length: 100,
                max_syllables_per_word: 1.5,
                recommended_flesch_range: (70.0, 80.0),
            },
            high_school: ReadabilityThresholds {
                min_flesch_score: 60.0,
                max_sentence_length: 20,
                max_paragraph_length: 150,
                max_syllables_per_word: 1.6,
                recommended_flesch_range: (60.0, 70.0),
            },
            college: ReadabilityThresholds {
                min_flesch_score: 50.0,
                max_sentence_length: 25,
                max_paragraph_length: 200,
                max_syllables_per_word: 1.8,
                recommended_flesch_range: (50.0, 60.0),
            },
            adult: ReadabilityThresholds {
                min_flesch_score: 40.0,
                max_sentence_length: 30,
                max_paragraph_length: 250,
                max_syllables_per_word: 2.0,
                recommended_flesch_range: (40.0, 60.0),
            },
        }
    }
}

/// Enhanced readability validator with configurable thresholds
pub struct ReadabilityValidator {
    config: ReadabilityConfig,
}

impl ReadabilityValidator {
    pub fn new() -> Self {
        Self {
            config: ReadabilityConfig::default(),
        }
    }

    pub fn with_config(config: ReadabilityConfig) -> Self {
        Self { config }
    }

    pub fn with_complexity_level(mut self, level: ComplexityLevel) -> Self {
        self.config.complexity_level = level;
        self.apply_complexity_defaults();
        self
    }

    fn apply_complexity_defaults(&mut self) {
        let thresholds = match self.config.complexity_level {
            ComplexityLevel::Elementary => &self.config.age_specific_thresholds.elementary,
            ComplexityLevel::MiddleSchool => &self.config.age_specific_thresholds.middle_school,
            ComplexityLevel::HighSchool => &self.config.age_specific_thresholds.high_school,
            ComplexityLevel::College => &self.config.age_specific_thresholds.college,
            ComplexityLevel::Graduate => &self.config.age_specific_thresholds.college, // Use college thresholds for graduate
            ComplexityLevel::Professional => &self.config.age_specific_thresholds.adult,
        };

        self.config.min_flesch_score = thresholds.min_flesch_score;
        self.config.max_sentence_length = thresholds.max_sentence_length;
        self.config.max_paragraph_length = thresholds.max_paragraph_length;
        self.config.max_syllables_per_word = thresholds.max_syllables_per_word;
    }

    fn get_current_thresholds(&self) -> &ReadabilityThresholds {
        match self.config.complexity_level {
            ComplexityLevel::Elementary => &self.config.age_specific_thresholds.elementary,
            ComplexityLevel::MiddleSchool => &self.config.age_specific_thresholds.middle_school,
            ComplexityLevel::HighSchool => &self.config.age_specific_thresholds.high_school,
            ComplexityLevel::College => &self.config.age_specific_thresholds.college,
            ComplexityLevel::Graduate => &self.config.age_specific_thresholds.college, // Use college thresholds for graduate
            ComplexityLevel::Professional => &self.config.age_specific_thresholds.adult,
        }
    }

    fn calculate_flesch_score(&self, content: &str) -> f64 {
        let sentences = self.count_sentences(content);
        let words = content.split_whitespace().count();
        let syllables = self.count_syllables(content);

        if sentences == 0 || words == 0 {
            return 0.0;
        }

        let avg_sentence_length = words as f64 / sentences as f64;
        let avg_syllables_per_word = syllables as f64 / words as f64;

        206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    }

    fn count_sentences(&self, content: &str) -> usize {
        content.matches(&['.', '!', '?'][..]).count().max(1)
    }

    fn count_syllables(&self, content: &str) -> usize {
        content
            .split_whitespace()
            .map(|word| self.count_word_syllables(word))
            .sum()
    }

    fn count_word_syllables(&self, word: &str) -> usize {
        let vowels = "aeiouAEIOU";
        let word = word.to_lowercase();
        let mut count = 0;
        let mut prev_was_vowel = false;

        for char in word.chars() {
            let is_vowel = vowels.contains(char);
            if is_vowel && !prev_was_vowel {
                count += 1;
            }
            prev_was_vowel = is_vowel;
        }

        // Adjust for silent 'e'
        if word.ends_with('e') && count > 1 {
            count -= 1;
        }

        count.max(1)
    }

    fn calculate_flesch_kincaid_grade(&self, content: &str) -> f64 {
        let sentences = self.count_sentences(content);
        let words = content.split_whitespace().count();
        let syllables = self.count_syllables(content);

        if sentences == 0 || words == 0 {
            return 0.0;
        }

        let avg_sentence_length = words as f64 / sentences as f64;
        let avg_syllables_per_word = syllables as f64 / words as f64;

        0.39 * avg_sentence_length + 11.8 * avg_syllables_per_word - 15.59
    }

    fn calculate_avg_syllables_per_word(&self, content: &str) -> f64 {
        let words = content.split_whitespace().count();
        if words == 0 {
            return 0.0;
        }
        
        let syllables = self.count_syllables(content);
        syllables as f64 / words as f64
    }

    fn calculate_complexity_score(&self, content: &str) -> f64 {
        let words = content.split_whitespace().count();
        if words == 0 {
            return 0.0;
        }

        let complex_words = content
            .split_whitespace()
            .filter(|word| self.count_word_syllables(word) >= 3)
            .count();

        complex_words as f64 / words as f64 * 100.0
    }

    fn get_readability_improvement_hint(&self, flesch_score: f64, config: &ReadabilityConfig) -> String {
        let gap = config.min_flesch_score - flesch_score;
        
        match gap {
            gap if gap > 30.0 => "Content is significantly too complex. Consider breaking long sentences into shorter ones, using simpler vocabulary, and reducing technical jargon.".to_string(),
            gap if gap > 15.0 => "Content complexity is moderately high. Try shortening sentences and replacing complex words with simpler alternatives.".to_string(),
            gap if gap > 5.0 => "Content is slightly complex. Consider simplifying a few sentences and replacing some difficult words.".to_string(),
            _ => "Content is close to target readability. Minor adjustments to sentence length or vocabulary may help.".to_string(),
        }
    }

    fn analyze_sentence_patterns(&self, content: &str) -> SentenceAnalysis {
        let sentences: Vec<&str> = content
            .split(&['.', '!', '?'][..])
            .filter(|s| !s.trim().is_empty())
            .collect();

        let total_sentences = sentences.len();
        if total_sentences == 0 {
            return SentenceAnalysis::default();
        }

        let sentence_lengths: Vec<usize> = sentences
            .iter()
            .map(|s| s.split_whitespace().count())
            .collect();

        let avg_length = sentence_lengths.iter().sum::<usize>() as f64 / total_sentences as f64;
        let max_length = *sentence_lengths.iter().max().unwrap_or(&0);
        let min_length = *sentence_lengths.iter().min().unwrap_or(&0);

        let long_sentences = sentence_lengths.iter().filter(|&&len| len > 20).count();
        let very_long_sentences = sentence_lengths.iter().filter(|&&len| len > 30).count();

        SentenceAnalysis {
            total_sentences,
            avg_length,
            max_length,
            min_length,
            long_sentences,
            very_long_sentences,
            length_variance: self.calculate_variance(&sentence_lengths),
        }
    }

    fn calculate_variance(&self, lengths: &[usize]) -> f64 {
        if lengths.is_empty() {
            return 0.0;
        }

        let mean = lengths.iter().sum::<usize>() as f64 / lengths.len() as f64;
        let variance = lengths
            .iter()
            .map(|&len| {
                let diff = len as f64 - mean;
                diff * diff
            })
            .sum::<f64>() / lengths.len() as f64;

        variance.sqrt()
    }
}

#[async_trait::async_trait]
impl Validator for ReadabilityValidator {
    fn name(&self) -> &str {
        "readability"
    }

    fn description(&self) -> &str {
        "Validates content readability and complexity for target audience"
    }

    fn version(&self) -> &str {
        "1.0.0"
    }

    fn categories(&self) -> Vec<IssueType> {
        vec![IssueType::Readability, IssueType::AgeAppropriateness]
    }

    fn supported_content_types(&self) -> Vec<ContentType> {
        vec![
            ContentType::Slides,
            ContentType::Quiz,
            ContentType::Worksheet,
            ContentType::InstructorNotes,
            ContentType::ActivityGuide,
        ]
    }

    async fn validate(&self, content: &GeneratedContent, config: &ValidationConfig) -> Result<ValidationResult> {
        let start_time = std::time::Instant::now();
        let mut issues = Vec::new();
        let mut score = 1.0;

        // Load validator-specific configuration if available
        let readability_config = if let Some(plugin_config) = self.get_plugin_config_raw(config) {
            match serde_json::from_value::<ReadabilityConfig>(plugin_config.clone()) {
                Ok(custom_config) => custom_config,
                Err(_) => self.config.clone(),
            }
        } else {
            self.config.clone()
        };

        // Calculate comprehensive readability metrics
        let flesch_score = self.calculate_flesch_score(&content.content);
        let flesch_kincaid_grade = self.calculate_flesch_kincaid_grade(&content.content);
        let avg_syllables_per_word = self.calculate_avg_syllables_per_word(&content.content);
        let complexity_score = self.calculate_complexity_score(&content.content);
        
        let thresholds = readability_config.age_specific_thresholds.get_for_level(&readability_config.complexity_level);

        // Check Flesch Reading Ease Score
        if flesch_score < readability_config.min_flesch_score {
            let severity = if flesch_score < readability_config.min_flesch_score - 20.0 {
                IssueSeverity::Warning
            } else {
                IssueSeverity::Info
            };

            issues.push(
                ValidationIssue::new(
                    severity,
                    IssueType::Readability,
                    format!("Content complexity too high (Flesch score: {:.1}, target: ≥{:.1})", 
                           flesch_score, readability_config.min_flesch_score),
                    None,
                )
                .with_remediation_hint(self.get_readability_improvement_hint(flesch_score, &readability_config))
            );
            score *= (flesch_score / readability_config.min_flesch_score).max(0.3);
        }

        // Check if content is in optimal range
        let optimal_range = thresholds.recommended_flesch_range;
        if flesch_score > optimal_range.1 {
            issues.push(
                ValidationIssue::new(
                    IssueSeverity::Info,
                    IssueType::Readability,
                    format!("Content may be too simple (Flesch score: {:.1}, optimal range: {:.1}-{:.1})", 
                           flesch_score, optimal_range.0, optimal_range.1),
                    None,
                )
                .with_remediation_hint("Consider adding more sophisticated vocabulary and sentence structures".to_string())
            );
        }

        // Check syllables per word
        if avg_syllables_per_word > readability_config.max_syllables_per_word {
            issues.push(
                ValidationIssue::new(
                    IssueSeverity::Info,
                    IssueType::Readability,
                    format!("High syllable complexity (avg: {:.2} syllables/word, target: ≤{:.2})", 
                           avg_syllables_per_word, readability_config.max_syllables_per_word),
                    None,
                )
                .with_remediation_hint("Use simpler words with fewer syllables where possible".to_string())
            );
            score *= 0.9;
        }

        // Check grade level if specified
        if let Some(target_grade) = readability_config.target_grade_level {
            if flesch_kincaid_grade > target_grade + 2.0 {
                issues.push(
                    ValidationIssue::new(
                        IssueSeverity::Warning,
                        IssueType::AgeAppropriateness,
                        format!("Content grade level too high ({:.1}, target: ≤{:.1})", 
                               flesch_kincaid_grade, target_grade),
                        None,
                    )
                    .with_remediation_hint("Simplify sentence structure and vocabulary for target age group".to_string())
                );
                score *= 0.8;
            }
        }

        // Perform detailed sentence analysis
        let sentence_analysis = self.analyze_sentence_patterns(&content.content);
        
        // Check sentence length using configurable thresholds
        for (i, sentence) in content.content
            .split(&['.', '!', '?'][..])
            .filter(|s| !s.trim().is_empty())
            .enumerate() {
            
            let word_count = sentence.split_whitespace().count();
            if word_count > readability_config.max_sentence_length {
                let severity = if word_count > readability_config.max_sentence_length + 10 {
                    IssueSeverity::Warning
                } else {
                    IssueSeverity::Info
                };

                issues.push(
                    ValidationIssue::new(
                        severity,
                        IssueType::Readability,
                        format!("Long sentence detected ({} words, target: ≤{})", word_count, readability_config.max_sentence_length),
                        Some(ContentLocation {
                            section: None,
                            line: Some(i + 1),
                            character_range: None,
                            slide_number: None,
                            question_number: None,
                        }),
                    )
                    .with_remediation_hint("Consider breaking this sentence into shorter ones for better readability".to_string())
                );
            }
        }

        // Check paragraph length using configurable thresholds
        for (i, paragraph) in content.content
            .split("\n\n")
            .filter(|p| !p.trim().is_empty())
            .enumerate() {
            
            let word_count = paragraph.split_whitespace().count();
            if word_count > readability_config.max_paragraph_length {
                issues.push(
                    ValidationIssue::new(
                        IssueSeverity::Info,
                        IssueType::Readability,
                        format!("Long paragraph detected ({} words, target: ≤{})", word_count, readability_config.max_paragraph_length),
                        Some(ContentLocation {
                            section: Some(format!("Paragraph {}", i + 1)),
                            line: None,
                            character_range: None,
                            slide_number: None,
                            question_number: None,
                        }),
                    )
                    .with_remediation_hint("Consider breaking this paragraph into smaller chunks for better readability".to_string())
                );
            }
        }

        // Add complexity analysis feedback
        if complexity_score > 30.0 {
            issues.push(
                ValidationIssue::new(
                    IssueSeverity::Info,
                    IssueType::Readability,
                    format!("High proportion of complex words ({:.1}%)", complexity_score),
                    None,
                )
                .with_remediation_hint("Consider replacing some complex words with simpler alternatives".to_string())
            );
            score *= 0.95;
        }

        // Calculate overall score adjustments
        if !issues.is_empty() {
            score *= 0.9_f64.powi(issues.iter().filter(|i| i.severity <= IssueSeverity::Warning).count() as i32);
        }

        let execution_time = start_time.elapsed();
        let metadata = ValidationMetadata {
            execution_time_ms: execution_time.as_millis() as u64,
            content_analyzed: ContentAnalysis {
                word_count: content.metadata.word_count,
                section_count: sentence_analysis.total_sentences,
                slide_count: None,
                question_count: None,
                reading_level: Some(flesch_score),
            },
            validator_version: self.version().to_string(),
            timestamp: Utc::now(),
        };

        let passed = issues.iter().all(|i| i.severity > IssueSeverity::Error);

        Ok(if passed {
            ValidationResult::success(self.name().to_string(), score, metadata)
        } else {
            ValidationResult::failure(self.name().to_string(), score, issues, metadata)
        })
    }
}

/// Completeness validator ensures all required content elements are present
pub struct CompletenessValidator {
    min_word_counts: HashMap<ContentType, usize>,
}

impl CompletenessValidator {
    pub fn new() -> Self {
        let mut min_word_counts = HashMap::new();
        min_word_counts.insert(ContentType::Slides, 200);
        min_word_counts.insert(ContentType::Quiz, 100);
        min_word_counts.insert(ContentType::Worksheet, 300);
        min_word_counts.insert(ContentType::InstructorNotes, 150);
        min_word_counts.insert(ContentType::ActivityGuide, 250);

        Self { min_word_counts }
    }
}

#[async_trait::async_trait]
impl Validator for CompletenessValidator {
    fn name(&self) -> &str {
        "completeness"
    }

    fn description(&self) -> &str {
        "Validates that content meets minimum requirements and includes necessary elements"
    }

    fn version(&self) -> &str {
        "1.0.0"
    }

    fn categories(&self) -> Vec<IssueType> {
        vec![IssueType::Completeness, IssueType::LearningObjectives]
    }

    fn supported_content_types(&self) -> Vec<ContentType> {
        vec![
            ContentType::Slides,
            ContentType::Quiz,
            ContentType::Worksheet,
            ContentType::InstructorNotes,
            ContentType::ActivityGuide,
        ]
    }

    async fn validate(&self, content: &GeneratedContent, _config: &ValidationConfig) -> Result<ValidationResult> {
        let start_time = std::time::Instant::now();
        let mut issues = Vec::new();
        let mut score = 1.0;

        // Check minimum word count
        if let Some(&min_words) = self.min_word_counts.get(&content.content_type) {
            if content.metadata.word_count < min_words {
                issues.push(
                    ValidationIssue::new(
                        IssueSeverity::Warning,
                        IssueType::Completeness,
                        format!(
                            "Content is below minimum word count ({} < {})",
                            content.metadata.word_count, min_words
                        ),
                        None,
                    )
                    .with_remediation_hint(format!(
                        "Add approximately {} more words to reach minimum length",
                        min_words - content.metadata.word_count
                    ))
                );
                score *= content.metadata.word_count as f64 / min_words as f64;
            }
        }

        // Check for learning objectives (if applicable)
        let content_lower = content.content.to_lowercase();
        if matches!(content.content_type, ContentType::Slides | ContentType::ActivityGuide | ContentType::Worksheet) {
            if !content_lower.contains("objective") && !content_lower.contains("goal") {
                issues.push(
                    ValidationIssue::new(
                        IssueSeverity::Info,
                        IssueType::LearningObjectives,
                        "No clear learning objectives found".to_string(),
                        None,
                    )
                    .with_remediation_hint("Add explicit learning objectives to help students understand expected outcomes".to_string())
                );
                score *= 0.9;
            }
        }

        // Check for examples (if applicable)
        if matches!(content.content_type, ContentType::Slides | ContentType::Worksheet) {
            if !content_lower.contains("example") && !content_lower.contains("for instance") {
                issues.push(
                    ValidationIssue::new(
                        IssueSeverity::Info,
                        IssueType::Completeness,
                        "Content could benefit from examples".to_string(),
                        None,
                    )
                    .with_remediation_hint("Add concrete examples to illustrate concepts".to_string())
                );
                score *= 0.95;
            }
        }

        let execution_time = start_time.elapsed();
        let metadata = ValidationMetadata {
            execution_time_ms: execution_time.as_millis() as u64,
            content_analyzed: ContentAnalysis {
                word_count: content.metadata.word_count,
                section_count: content.content.lines().count(),
                slide_count: None,
                question_count: None,
                reading_level: None,
            },
            validator_version: self.version().to_string(),
            timestamp: Utc::now(),
        };

        let passed = issues.iter().all(|i| i.severity > IssueSeverity::Error);

        Ok(if passed {
            ValidationResult::success(self.name().to_string(), score, metadata)
        } else {
            ValidationResult::failure(self.name().to_string(), score, issues, metadata)
        })
    }
}

/// Grammar validator checks for basic grammar and spelling issues
pub struct GrammarValidator {
    common_errors: HashMap<String, String>,
}

impl GrammarValidator {
    pub fn new() -> Self {
        let mut common_errors = HashMap::new();
        
        // Common grammatical errors and corrections
        common_errors.insert("it's".to_string(), "its".to_string());
        common_errors.insert("there".to_string(), "their/they're".to_string());
        common_errors.insert("your".to_string(), "you're".to_string());
        common_errors.insert("loose".to_string(), "lose".to_string());
        common_errors.insert("affect".to_string(), "effect".to_string());

        Self { common_errors }
    }
}

#[async_trait::async_trait]
impl Validator for GrammarValidator {
    fn name(&self) -> &str {
        "grammar"
    }

    fn description(&self) -> &str {
        "Validates content for basic grammar and spelling issues"
    }

    fn version(&self) -> &str {
        "1.0.0"
    }

    fn categories(&self) -> Vec<IssueType> {
        vec![IssueType::Grammar, IssueType::Spelling]
    }

    fn supported_content_types(&self) -> Vec<ContentType> {
        vec![
            ContentType::Slides,
            ContentType::Quiz,
            ContentType::Worksheet,
            ContentType::InstructorNotes,
            ContentType::ActivityGuide,
        ]
    }

    async fn validate(&self, content: &GeneratedContent, _config: &ValidationConfig) -> Result<ValidationResult> {
        let start_time = std::time::Instant::now();
        let mut issues = Vec::new();
        let mut score = 1.0;

        // Check for common grammatical errors
        let content_lower = content.content.to_lowercase();
        for (error, _correction) in &self.common_errors {
            if content_lower.contains(error) {
                issues.push(
                    ValidationIssue::new(
                        IssueSeverity::Info,
                        IssueType::Grammar,
                        format!("Potential grammar issue: '{}'", error),
                        None,
                    )
                    .with_remediation_hint(format!("Check usage of '{}' - consider context", error))
                );
            }
        }

        // Check for repeated words
        let words: Vec<&str> = content.content.split_whitespace().collect();
        for window in words.windows(2) {
            if window[0].to_lowercase() == window[1].to_lowercase() && window[0].len() > 3 {
                issues.push(
                    ValidationIssue::new(
                        IssueSeverity::Info,
                        IssueType::Grammar,
                        format!("Repeated word detected: '{}'", window[0]),
                        None,
                    )
                    .with_remediation_hint("Remove duplicate word".to_string())
                    .with_auto_fix()
                );
            }
        }

        // Check for proper capitalization
        let sentences: Vec<&str> = content.content
            .split(&['.', '!', '?'][..])
            .filter(|s| !s.trim().is_empty())
            .collect();

        for sentence in sentences {
            let trimmed = sentence.trim();
            if !trimmed.is_empty() {
                let first_char = trimmed.chars().next().unwrap();
                if first_char.is_lowercase() {
                    issues.push(
                        ValidationIssue::new(
                            IssueSeverity::Info,
                            IssueType::Grammar,
                            "Sentence should start with capital letter".to_string(),
                            None,
                        )
                        .with_remediation_hint("Capitalize the first letter of the sentence".to_string())
                        .with_auto_fix()
                    );
                }
            }
        }

        if !issues.is_empty() {
            score *= 0.95_f64.powi(issues.len() as i32);
        }

        let execution_time = start_time.elapsed();
        let metadata = ValidationMetadata {
            execution_time_ms: execution_time.as_millis() as u64,
            content_analyzed: ContentAnalysis {
                word_count: content.metadata.word_count,
                section_count: content.content.lines().count(),
                slide_count: None,
                question_count: None,
                reading_level: None,
            },
            validator_version: self.version().to_string(),
            timestamp: Utc::now(),
        };

        let passed = issues.iter().all(|i| i.severity > IssueSeverity::Error);

        Ok(if passed {
            ValidationResult::success(self.name().to_string(), score, metadata)
        } else {
            ValidationResult::failure(self.name().to_string(), score, issues, metadata)
        })
    }

    async fn auto_fix(&self, _content: &GeneratedContent, issue: &ValidationIssue) -> Result<Option<String>> {
        if issue.message.contains("Repeated word detected") {
            return Ok(Some("Remove the duplicate word".to_string()));
        }
        
        if issue.message.contains("should start with capital letter") {
            return Ok(Some("Capitalize the first letter of the sentence".to_string()));
        }
        
        Ok(None)
    }
}

/// Content alignment validator ensures consistency between related educational materials
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ContentAlignmentValidator {
    config: AlignmentConfig,
    content_repository: std::collections::HashMap<String, Vec<GeneratedContent>>,
}

/// Configuration for content alignment validation
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct AlignmentConfig {
    pub check_learning_objectives: bool,
    pub check_topic_coverage: bool,
    pub check_difficulty_progression: bool,
    pub check_terminology_consistency: bool,
    pub check_assessment_alignment: bool,
    pub similarity_threshold: f64,
    pub alignment_requirements: std::collections::HashMap<ContentType, Vec<ContentType>>,
    pub topic_extraction_enabled: bool,
}

/// Alignment analysis results
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct AlignmentAnalysis {
    pub objective_alignment_score: f64,
    pub topic_coverage_score: f64,
    pub terminology_consistency_score: f64,
    pub difficulty_alignment_score: f64,
    pub assessment_alignment_score: f64,
    pub missing_topics: Vec<String>,
    pub inconsistent_terms: Vec<TermInconsistency>,
    pub misaligned_objectives: Vec<ObjectiveAlignment>,
    pub overall_alignment_score: f64,
}

/// Terminology inconsistency detection
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct TermInconsistency {
    pub term_variants: Vec<String>,
    pub recommended_term: String,
    pub context_examples: Vec<String>,
    pub impact_severity: IssueSeverity,
}

/// Learning objective alignment analysis
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ObjectiveAlignment {
    pub source_objective: String,
    pub target_coverage: f64,
    pub missing_elements: Vec<String>,
    pub alignment_quality: f64,
}

/// Topic extraction and analysis
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct TopicAnalysis {
    pub extracted_topics: Vec<String>,
    pub key_concepts: Vec<String>,
    pub learning_outcomes: Vec<String>,
    pub coverage_depth: std::collections::HashMap<String, f64>,
}

impl Default for AlignmentConfig {
    fn default() -> Self {
        let mut alignment_requirements = std::collections::HashMap::new();
        
        // Define which content types should align with which others
        alignment_requirements.insert(ContentType::Slides, vec![
            ContentType::Worksheet, 
            ContentType::Quiz, 
            ContentType::InstructorNotes,
            ContentType::ActivityGuide
        ]);
        
        alignment_requirements.insert(ContentType::Worksheet, vec![
            ContentType::Slides,
            ContentType::Quiz,
            ContentType::InstructorNotes
        ]);
        
        alignment_requirements.insert(ContentType::Quiz, vec![
            ContentType::Slides,
            ContentType::Worksheet,
            ContentType::InstructorNotes
        ]);
        
        alignment_requirements.insert(ContentType::InstructorNotes, vec![
            ContentType::Slides,
            ContentType::Worksheet,
            ContentType::Quiz,
            ContentType::ActivityGuide
        ]);
        
        alignment_requirements.insert(ContentType::ActivityGuide, vec![
            ContentType::Slides,
            ContentType::InstructorNotes
        ]);
        
        Self {
            check_learning_objectives: true,
            check_topic_coverage: true,
            check_difficulty_progression: true,
            check_terminology_consistency: true,
            check_assessment_alignment: true,
            similarity_threshold: 0.7,
            alignment_requirements,
            topic_extraction_enabled: true,
        }
    }
}

impl ContentAlignmentValidator {
    pub fn new() -> Self {
        Self::with_config(AlignmentConfig::default())
    }
    
    pub fn with_config(config: AlignmentConfig) -> Self {
        Self {
            config,
            content_repository: std::collections::HashMap::new(),
        }
    }
    
    /// Add content to the repository for alignment checking
    pub fn add_content(&mut self, session_id: String, content: GeneratedContent) {
        self.content_repository.entry(session_id).or_insert_with(Vec::new).push(content);
    }
    
    /// Set content repository for a session
    pub fn set_content_repository(&mut self, session_id: String, contents: Vec<GeneratedContent>) {
        self.content_repository.insert(session_id, contents);
    }
    
    /// Analyze alignment between content and related materials
    fn analyze_content_alignment(&self, content: &GeneratedContent, related_content: &[GeneratedContent]) -> Result<AlignmentAnalysis> {
        let mut analysis = AlignmentAnalysis {
            objective_alignment_score: 1.0,
            topic_coverage_score: 1.0,
            terminology_consistency_score: 1.0,
            difficulty_alignment_score: 1.0,
            assessment_alignment_score: 1.0,
            missing_topics: Vec::new(),
            inconsistent_terms: Vec::new(),
            misaligned_objectives: Vec::new(),
            overall_alignment_score: 1.0,
        };
        
        if related_content.is_empty() {
            return Ok(analysis);
        }
        
        // Extract topics from current content
        let current_topics = self.extract_topics(content)?;
        
        // Analyze each type of alignment
        if self.config.check_learning_objectives {
            analysis.objective_alignment_score = self.analyze_objective_alignment(content, related_content, &mut analysis.misaligned_objectives)?;
        }
        
        if self.config.check_topic_coverage {
            analysis.topic_coverage_score = self.analyze_topic_coverage(content, related_content, &current_topics, &mut analysis.missing_topics)?;
        }
        
        if self.config.check_terminology_consistency {
            analysis.terminology_consistency_score = self.analyze_terminology_consistency(content, related_content, &mut analysis.inconsistent_terms)?;
        }
        
        if self.config.check_difficulty_progression {
            analysis.difficulty_alignment_score = self.analyze_difficulty_alignment(content, related_content)?;
        }
        
        if self.config.check_assessment_alignment {
            analysis.assessment_alignment_score = self.analyze_assessment_alignment(content, related_content)?;
        }
        
        // Calculate overall alignment score
        analysis.overall_alignment_score = (
            analysis.objective_alignment_score +
            analysis.topic_coverage_score +
            analysis.terminology_consistency_score +
            analysis.difficulty_alignment_score +
            analysis.assessment_alignment_score
        ) / 5.0;
        
        Ok(analysis)
    }
    
    /// Extract topics and key concepts from content
    fn extract_topics(&self, content: &GeneratedContent) -> Result<TopicAnalysis> {
        let text = &content.content;
        let lines: Vec<&str> = text.lines().collect();
        
        let mut extracted_topics = Vec::new();
        let mut key_concepts = Vec::new();
        let mut learning_outcomes = Vec::new();
        let mut coverage_depth = std::collections::HashMap::new();
        
        // Simple topic extraction based on headers and emphasized text
        for line in &lines {
            let trimmed = line.trim();
            
            // Extract from headers
            if trimmed.starts_with('#') {
                let topic = trimmed.trim_start_matches('#').trim().to_string();
                if !topic.is_empty() && topic.len() > 3 {
                    extracted_topics.push(topic.clone());
                    coverage_depth.insert(topic, 1.0);
                }
            }
            
            // Extract from bold/emphasized text
            if trimmed.contains("**") || trimmed.contains("__") {
                let emphasized = self.extract_emphasized_text(trimmed);
                key_concepts.extend(emphasized);
            }
            
            // Extract learning outcomes/objectives
            if trimmed.to_lowercase().contains("objective") || 
               trimmed.to_lowercase().contains("will be able to") ||
               trimmed.to_lowercase().contains("students will") {
                learning_outcomes.push(trimmed.to_string());
            }
        }
        
        // Extract topics from content body using simple keyword analysis
        let content_words: Vec<&str> = text.split_whitespace().collect();
        let important_keywords = self.identify_important_keywords(&content_words);
        extracted_topics.extend(important_keywords);
        
        Ok(TopicAnalysis {
            extracted_topics,
            key_concepts,
            learning_outcomes,
            coverage_depth,
        })
    }
    
    /// Extract emphasized text from a line
    fn extract_emphasized_text(&self, line: &str) -> Vec<String> {
        let mut emphasized = Vec::new();
        
        // Extract text between ** markers
        let chars: Vec<char> = line.chars().collect();
        let mut i = 0;
        while i < chars.len() - 1 {
            if chars[i] == '*' && chars[i + 1] == '*' {
                let start = i + 2;
                let mut end = start;
                while end < chars.len() - 1 {
                    if chars[end] == '*' && chars[end + 1] == '*' {
                        let text: String = chars[start..end].iter().collect();
                        if !text.trim().is_empty() && text.len() > 2 {
                            emphasized.push(text.trim().to_string());
                        }
                        i = end + 2;
                        break;
                    }
                    end += 1;
                }
                if end >= chars.len() - 1 {
                    break;
                }
            } else {
                i += 1;
            }
        }
        
        emphasized
    }
    
    /// Identify important keywords using simple frequency and length analysis
    fn identify_important_keywords(&self, words: &[&str]) -> Vec<String> {
        let mut word_freq = std::collections::HashMap::new();
        let stop_words = vec!["the", "is", "at", "which", "on", "and", "a", "to", "as", "are", "was", "will", "be", "have", "has", "had", "do", "does", "did", "can", "could", "should", "would", "may", "might", "must", "shall", "will", "in", "of", "for", "with", "by"];
        
        for &word in words {
            let clean_word = word.to_lowercase().trim_matches(|c: char| !c.is_alphabetic()).to_string();
            if clean_word.len() >= 4 && !stop_words.contains(&clean_word.as_str()) {
                *word_freq.entry(clean_word).or_insert(0) += 1;
            }
        }
        
        // Return words that appear multiple times or are longer than 6 characters
        word_freq.into_iter()
            .filter(|(word, freq)| *freq > 1 || word.len() > 6)
            .map(|(word, _)| word)
            .collect()
    }
    
    /// Analyze learning objective alignment between content types
    fn analyze_objective_alignment(&self, content: &GeneratedContent, related_content: &[GeneratedContent], misaligned: &mut Vec<ObjectiveAlignment>) -> Result<f64> {
        let current_objectives = self.extract_learning_objectives(content);
        if current_objectives.is_empty() {
            return Ok(0.5); // Neutral score if no objectives found
        }
        
        let mut total_alignment = 0.0;
        let mut objective_count = 0;
        
        for objective in &current_objectives {
            let mut best_coverage = 0.0;
            let mut missing_elements = Vec::new();
            
            // Check coverage in related content
            for related in related_content {
                let coverage = self.calculate_objective_coverage(objective, related);
                if coverage > best_coverage {
                    best_coverage = coverage;
                }
            }
            
            if best_coverage < self.config.similarity_threshold {
                missing_elements.push(format!("Objective '{}' not adequately covered in related materials", objective));
                
                misaligned.push(ObjectiveAlignment {
                    source_objective: objective.clone(),
                    target_coverage: best_coverage,
                    missing_elements: missing_elements.clone(),
                    alignment_quality: best_coverage,
                });
            }
            
            total_alignment += best_coverage;
            objective_count += 1;
        }
        
        Ok(if objective_count > 0 { total_alignment / objective_count as f64 } else { 1.0 })
    }
    
    /// Extract learning objectives from content
    fn extract_learning_objectives(&self, content: &GeneratedContent) -> Vec<String> {
        let lines: Vec<&str> = content.content.lines().collect();
        let mut objectives = Vec::new();
        let mut in_objectives_section = false;
        
        for line in lines {
            let trimmed = line.trim().to_lowercase();
            
            // Check if we're entering an objectives section
            if trimmed.contains("objective") || trimmed.contains("goals") || trimmed.contains("will be able to") {
                in_objectives_section = true;
                
                // If the line itself contains an objective, extract it
                if trimmed.contains("will be able to") || trimmed.contains("students will") {
                    objectives.push(line.trim().to_string());
                }
                continue;
            }
            
            // If we're in objectives section, extract bullet points or numbered items
            if in_objectives_section {
                if trimmed.starts_with('-') || trimmed.starts_with('*') || 
                   trimmed.chars().next().map_or(false, |c| c.is_ascii_digit()) {
                    let objective = line.trim().trim_start_matches(|c: char| c == '-' || c == '*' || c.is_ascii_digit() || c == '.' || c == ')').trim();
                    if !objective.is_empty() && objective.len() > 10 {
                        objectives.push(objective.to_string());
                    }
                } else if trimmed.is_empty() || trimmed.starts_with('#') {
                    in_objectives_section = false;
                }
            }
        }
        
        objectives
    }
    
    /// Calculate how well an objective is covered in related content
    fn calculate_objective_coverage(&self, objective: &str, content: &GeneratedContent) -> f64 {
        let objective_words: Vec<&str> = objective.split_whitespace().collect();
        let content_lower = content.content.to_lowercase();
        
        let mut coverage_score = 0.0;
        let mut important_word_count = 0;
        
        for word in objective_words {
            let lowercase_word = word.to_lowercase();
            let clean_word = lowercase_word.trim_matches(|c: char| !c.is_alphabetic());
            if clean_word.len() >= 4 {
                important_word_count += 1;
                if content_lower.contains(&clean_word) {
                    coverage_score += 1.0;
                }
            }
        }
        
        if important_word_count > 0 {
            coverage_score / important_word_count as f64
        } else {
            0.0
        }
    }
    
    /// Analyze topic coverage alignment
    fn analyze_topic_coverage(&self, content: &GeneratedContent, related_content: &[GeneratedContent], current_topics: &TopicAnalysis, missing_topics: &mut Vec<String>) -> Result<f64> {
        if current_topics.extracted_topics.is_empty() {
            return Ok(1.0); // No topics to check
        }
        
        let mut covered_topics = 0;
        let total_topics = current_topics.extracted_topics.len();
        
        for topic in &current_topics.extracted_topics {
            let mut found_in_related = false;
            
            for related in related_content {
                if self.topic_exists_in_content(topic, related) {
                    found_in_related = true;
                    break;
                }
            }
            
            if found_in_related {
                covered_topics += 1;
            } else {
                missing_topics.push(topic.clone());
            }
        }
        
        Ok(covered_topics as f64 / total_topics as f64)
    }
    
    /// Check if a topic exists in content
    fn topic_exists_in_content(&self, topic: &str, content: &GeneratedContent) -> bool {
        let content_lower = content.content.to_lowercase();
        let topic_lower = topic.to_lowercase();
        
        // Direct match
        if content_lower.contains(&topic_lower) {
            return true;
        }
        
        // Word-based similarity check
        let topic_words: Vec<&str> = topic_lower.split_whitespace().collect();
        if topic_words.len() > 1 {
            let mut word_matches = 0;
            for word in &topic_words {
                if word.len() >= 4 && content_lower.contains(word) {
                    word_matches += 1;
                }
            }
            return word_matches >= (topic_words.len() + 1) / 2; // At least half the words match
        }
        
        false
    }
    
    /// Analyze terminology consistency
    fn analyze_terminology_consistency(&self, content: &GeneratedContent, related_content: &[GeneratedContent], inconsistent_terms: &mut Vec<TermInconsistency>) -> Result<f64> {
        let current_terms = self.extract_key_terms(content);
        let mut consistency_score: f64 = 1.0;
        let mut inconsistency_count = 0;
        
        for term in current_terms {
            let variants = self.find_term_variants(&term, related_content);
            if variants.len() > 1 {
                inconsistency_count += 1;
                consistency_score -= 0.1; // Reduce score for each inconsistency
                
                inconsistent_terms.push(TermInconsistency {
                    term_variants: variants.clone(),
                    recommended_term: self.select_preferred_term(&variants),
                    context_examples: self.extract_term_contexts(&term, content, related_content),
                    impact_severity: if variants.len() > 3 { IssueSeverity::Warning } else { IssueSeverity::Info },
                });
            }
        }
        
        Ok(consistency_score.max(0.0))
    }
    
    /// Extract key terms from content
    fn extract_key_terms(&self, content: &GeneratedContent) -> Vec<String> {
        let emphasized_terms = self.extract_emphasized_text(&content.content);
        let topic_analysis = self.extract_topics(content).unwrap_or_else(|_| TopicAnalysis {
            extracted_topics: Vec::new(),
            key_concepts: Vec::new(),
            learning_outcomes: Vec::new(),
            coverage_depth: std::collections::HashMap::new(),
        });
        
        let mut terms = emphasized_terms;
        terms.extend(topic_analysis.key_concepts);
        terms.extend(topic_analysis.extracted_topics);
        
        // Deduplicate and filter
        terms.sort();
        terms.dedup();
        terms.into_iter().filter(|t| t.len() >= 3 && t.len() <= 50).collect()
    }
    
    /// Find variants of a term in related content
    fn find_term_variants(&self, term: &str, related_content: &[GeneratedContent]) -> Vec<String> {
        let mut variants = vec![term.to_string()];
        let term_lower = term.to_lowercase();
        
        for content in related_content {
            let words: Vec<&str> = content.content.split_whitespace().collect();
            for word in words {
                let clean_word = word.trim_matches(|c: char| !c.is_alphabetic()).to_lowercase();
                if self.are_similar_terms(&term_lower, &clean_word) && !variants.contains(&clean_word) {
                    variants.push(clean_word);
                }
            }
        }
        
        variants
    }
    
    /// Check if two terms are similar (handle plurals, verb forms, etc.)
    fn are_similar_terms(&self, term1: &str, term2: &str) -> bool {
        if term1 == term2 {
            return true;
        }
        
        // Handle plurals
        if term1.len() > 3 && term2.len() > 3 {
            let stem1 = if term1.ends_with('s') { &term1[..term1.len()-1] } else { term1 };
            let stem2 = if term2.ends_with('s') { &term2[..term2.len()-1] } else { term2 };
            if stem1 == stem2 {
                return true;
            }
        }
        
        // Handle common verb forms (-ing, -ed)
        if term1.len() > 4 && term2.len() > 4 {
            let root1 = if term1.ends_with("ing") { &term1[..term1.len()-3] } 
                       else if term1.ends_with("ed") { &term1[..term1.len()-2] } 
                       else { term1 };
            let root2 = if term2.ends_with("ing") { &term2[..term2.len()-3] } 
                       else if term2.ends_with("ed") { &term2[..term2.len()-2] } 
                       else { term2 };
            if root1 == root2 {
                return true;
            }
        }
        
        false
    }
    
    /// Select the preferred term from variants
    fn select_preferred_term(&self, variants: &[String]) -> String {
        // Prefer the shortest non-plural form, or most common form
        variants.iter()
            .min_by(|a, b| {
                let a_score = if a.ends_with('s') { a.len() + 1 } else { a.len() };
                let b_score = if b.ends_with('s') { b.len() + 1 } else { b.len() };
                a_score.cmp(&b_score)
            })
            .cloned()
            .unwrap_or_else(|| variants[0].clone())
    }
    
    /// Extract contexts where terms appear
    fn extract_term_contexts(&self, term: &str, content: &GeneratedContent, related_content: &[GeneratedContent]) -> Vec<String> {
        let mut contexts = Vec::new();
        let all_content = std::iter::once(content).chain(related_content.iter());
        
        for content_item in all_content {
            let lines: Vec<&str> = content_item.content.lines().collect();
            for line in lines {
                if line.to_lowercase().contains(&term.to_lowercase()) {
                    contexts.push(line.trim().to_string());
                    if contexts.len() >= 3 {
                        break;
                    }
                }
            }
        }
        
        contexts
    }
    
    /// Analyze difficulty alignment between content types
    fn analyze_difficulty_alignment(&self, content: &GeneratedContent, related_content: &[GeneratedContent]) -> Result<f64> {
        let current_difficulty = self.estimate_content_difficulty(content);
        
        if related_content.is_empty() {
            return Ok(1.0);
        }
        
        let mut alignment_scores = Vec::new();
        
        for related in related_content {
            let related_difficulty = self.estimate_content_difficulty(related);
            let difficulty_difference = (current_difficulty - related_difficulty).abs();
            
            // Score based on how close the difficulties are
            let alignment = (1.0 - (difficulty_difference / 10.0)).max(0.0);
            alignment_scores.push(alignment);
        }
        
        Ok(alignment_scores.iter().sum::<f64>() / alignment_scores.len() as f64)
    }
    
    /// Estimate content difficulty based on various factors
    fn estimate_content_difficulty(&self, content: &GeneratedContent) -> f64 {
        let text = &content.content;
        let word_count = text.split_whitespace().count();
        let sentence_count = text.matches('.').count() + text.matches('!').count() + text.matches('?').count();
        
        let avg_sentence_length = if sentence_count > 0 {
            word_count as f64 / sentence_count as f64
        } else {
            10.0
        };
        
        // Simple difficulty estimation (scale 1-10)
        let mut difficulty: f64 = 5.0; // Base difficulty
        
        // Adjust based on sentence length
        if avg_sentence_length > 20.0 {
            difficulty += 1.5;
        } else if avg_sentence_length < 10.0 {
            difficulty -= 1.0;
        }
        
        // Adjust based on content type
        match content.content_type {
            ContentType::Quiz => difficulty += 1.0,
            ContentType::Worksheet => difficulty += 0.5,
            ContentType::InstructorNotes => difficulty += 2.0,
            ContentType::ActivityGuide => difficulty -= 0.5,
            ContentType::Slides => {}, // Neutral
        }
        
        // Look for complexity indicators
        let complexity_keywords = ["analyze", "synthesize", "evaluate", "compare", "contrast", "critically", "complex", "advanced"];
        for keyword in complexity_keywords {
            if text.to_lowercase().contains(keyword) {
                difficulty += 0.5;
            }
        }
        
        difficulty.clamp(1.0, 10.0)
    }
    
    /// Analyze assessment alignment
    fn analyze_assessment_alignment(&self, content: &GeneratedContent, related_content: &[GeneratedContent]) -> Result<f64> {
        let current_assessments = self.extract_assessment_elements(content);
        
        if current_assessments.is_empty() {
            return Ok(1.0); // No assessments to align
        }
        
        let mut alignment_score = 0.0;
        let mut assessment_count = 0;
        
        for assessment in current_assessments {
            let mut best_match = 0.0;
            
            for related in related_content {
                let related_assessments = self.extract_assessment_elements(related);
                for related_assessment in related_assessments {
                    let similarity = self.calculate_assessment_similarity(&assessment, &related_assessment);
                    if similarity > best_match {
                        best_match = similarity;
                    }
                }
            }
            
            alignment_score += best_match;
            assessment_count += 1;
        }
        
        Ok(if assessment_count > 0 { alignment_score / assessment_count as f64 } else { 1.0 })
    }
    
    /// Extract assessment elements from content
    fn extract_assessment_elements(&self, content: &GeneratedContent) -> Vec<String> {
        let mut assessments = Vec::new();
        let lines: Vec<&str> = content.content.lines().collect();
        
        for line in lines {
            let trimmed = line.trim().to_lowercase();
            
            // Look for questions
            if trimmed.contains('?') || trimmed.starts_with("question") {
                assessments.push(line.trim().to_string());
            }
            
            // Look for assessment keywords
            if trimmed.contains("exercise") || trimmed.contains("practice") || 
               trimmed.contains("activity") || trimmed.contains("assessment") ||
               trimmed.contains("quiz") || trimmed.contains("test") {
                assessments.push(line.trim().to_string());
            }
        }
        
        assessments
    }
    
    /// Calculate similarity between assessment elements
    fn calculate_assessment_similarity(&self, assessment1: &str, assessment2: &str) -> f64 {
        let words1: std::collections::HashSet<&str> = assessment1.split_whitespace().collect();
        let words2: std::collections::HashSet<&str> = assessment2.split_whitespace().collect();
        
        let intersection = words1.intersection(&words2).count();
        let union = words1.union(&words2).count();
        
        if union > 0 {
            intersection as f64 / union as f64
        } else {
            0.0
        }
    }
}

#[async_trait::async_trait]
impl Validator for ContentAlignmentValidator {
    fn name(&self) -> &str {
        "content_alignment"
    }

    fn description(&self) -> &str {
        "Validates alignment and consistency between related educational content"
    }

    fn version(&self) -> &str {
        "1.0.0"
    }

    fn categories(&self) -> Vec<IssueType> {
        vec![
            IssueType::Consistency, 
            IssueType::LearningObjectives, 
            IssueType::PedagogicalAlignment,
            IssueType::Completeness
        ]
    }

    fn supported_content_types(&self) -> Vec<ContentType> {
        vec![
            ContentType::Slides,
            ContentType::Quiz,
            ContentType::Worksheet,
            ContentType::InstructorNotes,
            ContentType::ActivityGuide,
        ]
    }

    async fn validate(&self, content: &GeneratedContent, _config: &ValidationConfig) -> Result<ValidationResult> {
        let start_time = std::time::Instant::now();
        let mut issues = Vec::new();
        let mut score = 1.0;

        // Get related content types that should be aligned
        let required_alignments = self.config.alignment_requirements.get(&content.content_type);
        
        if let Some(required_types) = required_alignments {
            // For this implementation, we'll simulate having related content
            // In a real implementation, this would fetch from the content repository
            let related_content = self.get_related_content_for_session("current_session", required_types);
            
            if !related_content.is_empty() {
                let alignment_analysis = self.analyze_content_alignment(content, &related_content)?;
                
                // Generate issues based on alignment analysis
                if alignment_analysis.overall_alignment_score < self.config.similarity_threshold {
                    score = alignment_analysis.overall_alignment_score;
                    
                    issues.push(
                        ValidationIssue::new(
                            IssueSeverity::Warning,
                            IssueType::Consistency,
                            format!("Content alignment score ({:.2}) below threshold ({:.2})", 
                                   alignment_analysis.overall_alignment_score, 
                                   self.config.similarity_threshold),
                            None,
                        )
                        .with_remediation_hint("Review and align content with related materials".to_string())
                    );
                }
                
                // Check specific alignment issues
                for missing_topic in alignment_analysis.missing_topics {
                    issues.push(
                        ValidationIssue::new(
                            IssueSeverity::Info,
                            IssueType::Completeness,
                            format!("Topic '{}' not covered in related materials", missing_topic),
                            None,
                        )
                        .with_remediation_hint("Consider adding this topic to related content or referencing it".to_string())
                    );
                }
                
                for inconsistency in alignment_analysis.inconsistent_terms {
                    issues.push(
                        ValidationIssue::new(
                            inconsistency.impact_severity,
                            IssueType::Consistency,
                            format!("Inconsistent terminology: {:?}", inconsistency.term_variants),
                            None,
                        )
                        .with_remediation_hint(format!("Use consistent term: '{}'", inconsistency.recommended_term))
                    );
                }
                
                for misaligned in alignment_analysis.misaligned_objectives {
                    issues.push(
                        ValidationIssue::new(
                            IssueSeverity::Warning,
                            IssueType::LearningObjectives,
                            format!("Learning objective not well-aligned: {}", misaligned.source_objective),
                            None,
                        )
                        .with_remediation_hint("Ensure this objective is addressed in related materials".to_string())
                    );
                }
            }
        } else {
            // Add info about standalone content
            issues.push(
                ValidationIssue::new(
                    IssueSeverity::Info,
                    IssueType::Consistency,
                    "Content is standalone - no alignment requirements defined".to_string(),
                    None,
                )
                .with_remediation_hint("Consider creating complementary materials".to_string())
            );
        }

        let execution_time = start_time.elapsed();
        let metadata = ValidationMetadata {
            execution_time_ms: execution_time.as_millis() as u64,
            content_analyzed: ContentAnalysis {
                word_count: content.metadata.word_count,
                section_count: content.content.lines().count(),
                slide_count: None,
                question_count: Some(content.content.matches('?').count()),
                reading_level: None,
            },
            validator_version: self.version().to_string(),
            timestamp: Utc::now(),
        };

        let passed = issues.iter().all(|i| i.severity <= IssueSeverity::Warning);

        Ok(if passed {
            ValidationResult::success(self.name().to_string(), score, metadata)
        } else {
            ValidationResult::failure(self.name().to_string(), score, issues, metadata)
        })
    }

    async fn auto_fix(&self, _content: &GeneratedContent, issue: &ValidationIssue) -> Result<Option<String>> {
        if issue.issue_type == IssueType::Consistency && issue.message.contains("Inconsistent terminology") {
            return Ok(Some("Consider standardizing terminology across all related materials".to_string()));
        }
        
        if issue.issue_type == IssueType::LearningObjectives && issue.message.contains("not well-aligned") {
            return Ok(Some("Add activities or content that address this learning objective".to_string()));
        }
        
        if issue.issue_type == IssueType::Completeness && issue.message.contains("not covered") {
            return Ok(Some("Add a section covering this topic or reference where it's covered".to_string()));
        }
        
        Ok(None)
    }
}

impl ContentAlignmentValidator {
    /// Get related content for a session (placeholder implementation)
    fn get_related_content_for_session(&self, session_id: &str, _required_types: &[ContentType]) -> Vec<GeneratedContent> {
        // In a real implementation, this would fetch from the content repository
        // For now, return empty to avoid requiring a full session management system
        self.content_repository.get(session_id).cloned().unwrap_or_default()
    }
}


#[cfg(test)]
mod tests {
    use super::*;
    use crate::content::generator::ContentMetadata;

    fn create_test_content(content_type: ContentType, content: &str) -> GeneratedContent {
        GeneratedContent {
            content_type,
            title: "Test Content".to_string(),
            content: content.to_string(),
            metadata: ContentMetadata {
                word_count: content.split_whitespace().count(),
                estimated_duration: "10 minutes".to_string(),
                difficulty_level: "Beginner".to_string(),
            },
        }
    }

    #[tokio::test]
    async fn test_structure_validator() {
        let validator = StructureValidator::new();
        let content = create_test_content(
            ContentType::Slides,
            "# Title\n## Learning Objectives\n- Objective 1\n## Content\nSome content\n## Summary\nSummary text"
        );
        let config = ValidationConfig::default();
        
        let result = validator.validate(&content, &config).await.unwrap();
        assert!(result.passed);
        assert!(result.score > 0.8);
    }

    #[tokio::test]
    async fn test_readability_validator() {
        let validator = ReadabilityValidator::new();
        let content = create_test_content(
            ContentType::Slides,
            "This is a simple sentence. Here is another one. These sentences are easy to read."
        );
        let config = ValidationConfig::default();
        
        let result = validator.validate(&content, &config).await.unwrap();
        assert!(result.passed);
    }

    #[tokio::test]
    async fn test_completeness_validator() {
        let validator = CompletenessValidator::new();
        let short_content = create_test_content(
            ContentType::Slides,
            "Too short"
        );
        let config = ValidationConfig::default();
        
        let result = validator.validate(&short_content, &config).await.unwrap();
        assert!(!result.issues.is_empty());
    }

    #[tokio::test]
    async fn test_grammar_validator() {
        let validator = GrammarValidator::new();
        let content = create_test_content(
            ContentType::Slides,
            "This is is a test with repeated repeated words."
        );
        let config = ValidationConfig::default();
        
        let result = validator.validate(&content, &config).await.unwrap();
        assert!(!result.issues.is_empty());
        assert!(result.issues.iter().any(|i| i.message.contains("Repeated word")));
    }
}