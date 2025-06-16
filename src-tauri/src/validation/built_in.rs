use super::validators::*;
use crate::content::{GeneratedContent, ContentType};
use anyhow::Result;
use chrono::Utc;
use std::collections::HashMap;
use regex::Regex;

/// Structure validator ensures content has proper organization and required sections
pub struct StructureValidator {
    required_sections: HashMap<ContentType, Vec<String>>,
}

impl StructureValidator {
    pub fn new() -> Self {
        let mut required_sections = HashMap::new();
        
        required_sections.insert(ContentType::Slides, vec![
            "title".to_string(),
            "learning_objectives".to_string(),
            "content".to_string(),
            "summary".to_string(),
        ]);
        
        required_sections.insert(ContentType::Quiz, vec![
            "instructions".to_string(),
            "questions".to_string(),
            "answers".to_string(),
        ]);
        
        required_sections.insert(ContentType::Worksheet, vec![
            "title".to_string(),
            "instructions".to_string(),
            "exercises".to_string(),
        ]);
        
        required_sections.insert(ContentType::InstructorNotes, vec![
            "overview".to_string(),
            "key_points".to_string(),
            "timing".to_string(),
        ]);
        
        required_sections.insert(ContentType::ActivityGuide, vec![
            "overview".to_string(),
            "materials".to_string(),
            "steps".to_string(),
            "assessment".to_string(),
        ]);

        Self { required_sections }
    }
}

#[async_trait::async_trait]
impl Validator for StructureValidator {
    fn name(&self) -> &str {
        "structure"
    }

    fn description(&self) -> &str {
        "Validates that content has proper structure and required sections"
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
                                section_name.replace('_', " ").to_title_case(), 
                                section_name.replace('_', " "))
                };
                
                return Ok(Some(format!("Add the following section to your content:\n\n{}", template)));
            }
        }
        
        Ok(None)
    }
}

impl StructureValidator {
    fn count_questions(&self, content: &str) -> Option<usize> {
        let question_pattern = Regex::new(r"\?").unwrap();
        let count = question_pattern.find_iter(content).count();
        if count > 0 { Some(count) } else { None }
    }
}

/// Readability validator checks content complexity and accessibility
pub struct ReadabilityValidator {
    max_sentence_length: usize,
    max_paragraph_length: usize,
}

impl ReadabilityValidator {
    pub fn new() -> Self {
        Self {
            max_sentence_length: 25, // words
            max_paragraph_length: 150, // words
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

        // Calculate Flesch reading ease score
        let flesch_score = self.calculate_flesch_score(&content.content);
        let reading_level = flesch_score;

        // Check against threshold
        if flesch_score < config.readability_threshold * 10.0 {
            issues.push(
                ValidationIssue::new(
                    IssueSeverity::Warning,
                    IssueType::Readability,
                    format!("Content may be too complex (Flesch score: {:.1})", flesch_score),
                    None,
                )
                .with_remediation_hint("Consider simplifying sentences and using more common words".to_string())
            );
            score *= 0.8;
        }

        // Check sentence length
        let sentences: Vec<&str> = content.content
            .split(&['.', '!', '?'][..])
            .filter(|s| !s.trim().is_empty())
            .collect();

        for (i, sentence) in sentences.iter().enumerate() {
            let word_count = sentence.split_whitespace().count();
            if word_count > self.max_sentence_length {
                issues.push(
                    ValidationIssue::new(
                        IssueSeverity::Info,
                        IssueType::Readability,
                        format!("Long sentence detected ({} words)", word_count),
                        Some(ContentLocation {
                            section: None,
                            line: Some(i + 1),
                            character_range: None,
                            slide_number: None,
                            question_number: None,
                        }),
                    )
                    .with_remediation_hint("Consider breaking this sentence into shorter ones".to_string())
                );
            }
        }

        // Check paragraph length
        let paragraphs: Vec<&str> = content.content
            .split("\n\n")
            .filter(|p| !p.trim().is_empty())
            .collect();

        for (i, paragraph) in paragraphs.iter().enumerate() {
            let word_count = paragraph.split_whitespace().count();
            if word_count > self.max_paragraph_length {
                issues.push(
                    ValidationIssue::new(
                        IssueSeverity::Info,
                        IssueType::Readability,
                        format!("Long paragraph detected ({} words)", word_count),
                        Some(ContentLocation {
                            section: Some(format!("Paragraph {}", i + 1)),
                            line: None,
                            character_range: None,
                            slide_number: None,
                            question_number: None,
                        }),
                    )
                    .with_remediation_hint("Consider breaking this paragraph into smaller chunks".to_string())
                );
            }
        }

        if !issues.is_empty() {
            score *= 0.9_f64.powi(issues.len() as i32);
        }

        let execution_time = start_time.elapsed();
        let metadata = ValidationMetadata {
            execution_time_ms: execution_time.as_millis() as u64,
            content_analyzed: ContentAnalysis {
                word_count: content.metadata.word_count,
                section_count: paragraphs.len(),
                slide_count: None,
                question_count: None,
                reading_level: Some(reading_level),
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

/// Helper trait for string manipulation
trait StringExt {
    fn to_title_case(&self) -> String;
}

impl StringExt for str {
    fn to_title_case(&self) -> String {
        self.split_whitespace()
            .map(|word| {
                let mut chars: Vec<char> = word.chars().collect();
                if let Some(first) = chars.get_mut(0) {
                    *first = first.to_uppercase().next().unwrap_or(*first);
                }
                chars.into_iter().collect::<String>()
            })
            .collect::<Vec<String>>()
            .join(" ")
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