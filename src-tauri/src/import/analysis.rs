use super::*;
use anyhow::Result;
use regex::Regex;
use std::collections::HashMap;
use chrono::Utc;

/// Content analysis engine for imported documents
pub struct ContentAnalyzer;

/// Results of content analysis
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct AnalysisResult {
    pub detected_pedagogy: PedagogicalApproach,
    pub learning_objectives: Vec<LearningObjective>,
    pub content_structure: ContentStructureAnalysis,
    pub quality_metrics: QualityMetrics,
    pub improvement_areas: Vec<ImprovementArea>,
    pub content_gaps: Vec<ContentGap>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq, Eq, Hash)]
pub enum PedagogicalApproach {
    Bloom,
    Gagne,
    Constructivist,
    ProblemBased,
    Traditional,
    Mixed,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct LearningObjective {
    pub text: String,
    pub bloom_level: BloomLevel,
    pub action_verb: String,
    pub content_area: String,
    pub measurable: bool,
    pub confidence: f32,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub enum BloomLevel {
    Remember,
    Understand,
    Apply,
    Analyze,
    Evaluate,
    Create,
    Unknown,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ContentStructureAnalysis {
    pub has_clear_introduction: bool,
    pub has_learning_objectives: bool,
    pub has_assessments: bool,
    pub has_activities: bool,
    pub has_summary: bool,
    pub logical_flow_score: f32,
    pub sections: Vec<SectionAnalysis>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct SectionAnalysis {
    pub title: String,
    pub content_type: String,
    pub word_count: u32,
    pub reading_level: f32,
    pub key_concepts: Vec<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct QualityMetrics {
    pub readability_score: f32,
    pub structure_score: f32,
    pub engagement_score: f32,
    pub accessibility_score: f32,
    pub completeness_score: f32,
    pub overall_quality: f32,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ImprovementArea {
    pub category: ImprovementCategory,
    pub description: String,
    pub priority: Priority,
    pub suggested_action: String,
    pub estimated_impact: f32,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub enum ImprovementCategory {
    LearningObjectives,
    ContentStructure,
    Engagement,
    Assessment,
    Accessibility,
    Clarity,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub enum Priority {
    High,
    Medium,
    Low,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ContentGap {
    pub gap_type: GapType,
    pub description: String,
    pub suggested_content: String,
    pub importance: f32,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub enum GapType {
    MissingPrerequisites,
    IncompleteExplanation,
    LackOfExamples,
    NoAssessment,
    MissingVisuals,
    InsufficientPractice,
}

impl ContentAnalyzer {
    /// Analyze imported content and provide insights
    pub fn analyze(imported_content: &[ImportedContent]) -> Result<AnalysisResult> {
        let full_text = Self::combine_content(imported_content);
        
        Ok(AnalysisResult {
            detected_pedagogy: Self::detect_pedagogical_approach(&full_text),
            learning_objectives: Self::extract_learning_objectives(imported_content),
            content_structure: Self::analyze_structure(imported_content),
            quality_metrics: Self::assess_quality(&full_text, imported_content),
            improvement_areas: Self::identify_improvements(imported_content),
            content_gaps: Self::find_content_gaps(imported_content),
        })
    }
    
    fn combine_content(content: &[ImportedContent]) -> String {
        content.iter()
            .map(|c| format!("{}\n{}", c.title, c.content))
            .collect::<Vec<_>>()
            .join("\n\n")
    }
    
    fn detect_pedagogical_approach(text: &str) -> PedagogicalApproach {
        let text_lower = text.to_lowercase();
        let mut scores = HashMap::new();
        
        // Bloom's taxonomy indicators
        let bloom_keywords = ["remember", "understand", "apply", "analyze", "evaluate", "create", 
                              "knowledge", "comprehension", "application", "synthesis"];
        scores.insert(PedagogicalApproach::Bloom, 
            bloom_keywords.iter().filter(|k| text_lower.contains(*k)).count());
        
        // Gagne's events indicators
        let gagne_keywords = ["attention", "objective", "recall", "stimulus", "guidance", 
                              "elicit", "feedback", "assess", "retention"];
        scores.insert(PedagogicalApproach::Gagne,
            gagne_keywords.iter().filter(|k| text_lower.contains(*k)).count());
        
        // Constructivist indicators
        let constructivist_keywords = ["construct", "explore", "discover", "collaborate", 
                                       "reflect", "experience", "build"];
        scores.insert(PedagogicalApproach::Constructivist,
            constructivist_keywords.iter().filter(|k| text_lower.contains(*k)).count());
        
        // Problem-based learning indicators
        let pbl_keywords = ["problem", "solve", "investigate", "research", "case study", 
                            "real-world", "scenario"];
        scores.insert(PedagogicalApproach::ProblemBased,
            pbl_keywords.iter().filter(|k| text_lower.contains(*k)).count());
        
        scores.into_iter()
            .max_by_key(|(_, score)| *score)
            .map(|(approach, _)| approach)
            .unwrap_or(PedagogicalApproach::Traditional)
    }
    
    fn extract_learning_objectives(content: &[ImportedContent]) -> Vec<LearningObjective> {
        let mut objectives = Vec::new();
        
        // Patterns for detecting learning objectives
        let patterns = vec![
            Regex::new(r"(?i)(?:students?\s+will\s+be\s+able\s+to|SWBAT)\s+(.+?)(?:\.|$)").unwrap(),
            Regex::new(r"(?i)(?:learners?\s+will|participants?\s+will)\s+(.+?)(?:\.|$)").unwrap(),
            Regex::new(r"(?i)(?:by\s+the\s+end.*?will)\s+(.+?)(?:\.|$)").unwrap(),
            Regex::new(r"(?i)(?:objective|goal|aim)s?:\s*(.+?)(?:\n|$)").unwrap(),
        ];
        
        for item in content {
            let text = format!("{} {}", item.title, item.content);
            
            for pattern in &patterns {
                for cap in pattern.captures_iter(&text) {
                    if let Some(objective_text) = cap.get(1) {
                        let obj_str = objective_text.as_str().trim();
                        if let Some(objective) = Self::parse_learning_objective(obj_str) {
                            objectives.push(objective);
                        }
                    }
                }
            }
        }
        
        objectives
    }
    
    fn parse_learning_objective(text: &str) -> Option<LearningObjective> {
        let action_verbs = Self::extract_action_verb(text)?;
        let bloom_level = Self::classify_bloom_level(&action_verbs.0);
        
        Some(LearningObjective {
            text: text.to_string(),
            bloom_level: bloom_level.clone(),
            action_verb: action_verbs.0,
            content_area: action_verbs.1,
            measurable: Self::is_measurable(text),
            confidence: Self::calculate_objective_confidence(text, &bloom_level),
        })
    }
    
    fn extract_action_verb(text: &str) -> Option<(String, String)> {
        // Simple verb extraction - could be enhanced with NLP
        let words: Vec<&str> = text.split_whitespace().collect();
        if words.len() < 2 {
            return None;
        }
        
        // Look for common action verbs
        let action_verbs = ["identify", "describe", "explain", "analyze", "evaluate", 
                            "create", "design", "implement", "demonstrate", "apply",
                            "compare", "contrast", "define", "summarize", "classify"];
        
        for (i, word) in words.iter().enumerate() {
            let word_lower = word.to_lowercase();
            if action_verbs.contains(&word_lower.as_str()) {
                let content_area = words[i+1..].join(" ");
                return Some((word_lower, content_area));
            }
        }
        
        // Fallback: first verb-like word
        Some((words[0].to_lowercase(), words[1..].join(" ")))
    }
    
    fn classify_bloom_level(verb: &str) -> BloomLevel {
        let verb_lower = verb.to_lowercase();
        
        match verb_lower.as_str() {
            "list" | "name" | "identify" | "define" | "describe" | "recall" => BloomLevel::Remember,
            "explain" | "summarize" | "interpret" | "classify" | "compare" => BloomLevel::Understand,
            "apply" | "demonstrate" | "use" | "implement" | "solve" => BloomLevel::Apply,
            "analyze" | "differentiate" | "organize" | "examine" | "contrast" => BloomLevel::Analyze,
            "evaluate" | "critique" | "judge" | "defend" | "assess" => BloomLevel::Evaluate,
            "create" | "design" | "construct" | "develop" | "formulate" => BloomLevel::Create,
            _ => BloomLevel::Unknown,
        }
    }
    
    fn is_measurable(text: &str) -> bool {
        // Check if the objective has measurable criteria
        let measurable_indicators = ["will be able to", "demonstrate", "complete", 
                                     "achieve", "perform", "produce"];
        let text_lower = text.to_lowercase();
        measurable_indicators.iter().any(|ind| text_lower.contains(ind))
    }
    
    fn calculate_objective_confidence(text: &str, bloom_level: &BloomLevel) -> f32 {
        let mut confidence: f32 = 0.5;
        
        // Increase confidence for clear action verbs
        if !matches!(bloom_level, BloomLevel::Unknown) {
            confidence += 0.2;
        }
        
        // Increase for specific, measurable language
        if Self::is_measurable(text) {
            confidence += 0.2;
        }
        
        // Decrease for vague language
        let vague_terms = ["understand", "know", "learn about", "appreciate"];
        if vague_terms.iter().any(|term| text.to_lowercase().contains(term)) {
            confidence -= 0.1;
        }
        
        confidence.clamp(0.0, 1.0)
    }
    
    fn analyze_structure(content: &[ImportedContent]) -> ContentStructureAnalysis {
        let has_objectives = content.iter()
            .any(|c| c.content_type.contains("Objective") || 
                     c.title.to_lowercase().contains("objective"));
        
        let has_assessments = content.iter()
            .any(|c| c.content_type.contains("Assessment") || 
                     c.content_type.contains("Quiz") ||
                     c.title.to_lowercase().contains("quiz") ||
                     c.title.to_lowercase().contains("test"));
        
        let has_activities = content.iter()
            .any(|c| c.content_type.contains("Activity") || 
                     c.title.to_lowercase().contains("activity") ||
                     c.title.to_lowercase().contains("exercise"));
        
        let sections = content.iter()
            .map(|c| Self::analyze_section(c))
            .collect();
        
        ContentStructureAnalysis {
            has_clear_introduction: content.first()
                .map(|c| c.title.to_lowercase().contains("introduction") || 
                         c.order == 1)
                .unwrap_or(false),
            has_learning_objectives: has_objectives,
            has_assessments,
            has_activities,
            has_summary: content.last()
                .map(|c| c.title.to_lowercase().contains("summary") || 
                         c.title.to_lowercase().contains("conclusion"))
                .unwrap_or(false),
            logical_flow_score: Self::calculate_flow_score(content),
            sections,
        }
    }
    
    fn analyze_section(content: &ImportedContent) -> SectionAnalysis {
        SectionAnalysis {
            title: content.title.clone(),
            content_type: content.content_type.clone(),
            word_count: content.word_count,
            reading_level: Self::calculate_reading_level(&content.content),
            key_concepts: Self::extract_key_concepts(&content.content),
        }
    }
    
    fn calculate_flow_score(content: &[ImportedContent]) -> f32 {
        // Simple flow score based on logical ordering
        let mut score: f32 = 0.7; // Base score
        
        // Check for logical progression
        let has_intro = content.first()
            .map(|c| c.title.to_lowercase().contains("introduction"))
            .unwrap_or(false);
        if has_intro {
            score += 0.1;
        }
        
        // Check for consistent ordering
        let is_ordered = content.windows(2)
            .all(|pair| pair[0].order < pair[1].order);
        if is_ordered {
            score += 0.1;
        }
        
        // Check for conclusion
        let has_conclusion = content.last()
            .map(|c| c.title.to_lowercase().contains("conclusion") || 
                     c.title.to_lowercase().contains("summary"))
            .unwrap_or(false);
        if has_conclusion {
            score += 0.1;
        }
        
        score.clamp(0.0, 1.0)
    }
    
    fn calculate_reading_level(text: &str) -> f32 {
        // Simplified Flesch-Kincaid Grade Level
        let sentences = text.split('.').filter(|s| !s.trim().is_empty()).count() as f32;
        let words = text.split_whitespace().count() as f32;
        let syllables = text.split_whitespace()
            .map(|word| Self::count_syllables(word))
            .sum::<usize>() as f32;
        
        if sentences == 0.0 || words == 0.0 {
            return 0.0;
        }
        
        0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
    }
    
    fn count_syllables(word: &str) -> usize {
        // Simple syllable counting heuristic
        let vowels = ['a', 'e', 'i', 'o', 'u', 'y'];
        let word_lower = word.to_lowercase();
        let mut count = 0;
        let mut prev_was_vowel = false;
        
        for ch in word_lower.chars() {
            let is_vowel = vowels.contains(&ch);
            if is_vowel && !prev_was_vowel {
                count += 1;
            }
            prev_was_vowel = is_vowel;
        }
        
        // Adjust for silent 'e'
        if word_lower.ends_with('e') && count > 1 {
            count -= 1;
        }
        
        count.max(1)
    }
    
    fn extract_key_concepts(text: &str) -> Vec<String> {
        // Simple keyword extraction - could be enhanced with TF-IDF
        let stop_words = ["the", "a", "an", "and", "or", "but", "in", "on", "at", 
                          "to", "for", "of", "with", "by", "from", "as", "is", 
                          "was", "are", "were", "been", "be", "have", "has", "had",
                          "will", "would", "could", "should", "may", "might"];
        
        let words: Vec<String> = text.split_whitespace()
            .map(|w| w.to_lowercase().trim_matches(|c: char| !c.is_alphanumeric()).to_string())
            .filter(|w| w.len() > 3 && !stop_words.contains(&w.as_str()))
            .collect();
        
        // Count frequency
        let mut word_freq = HashMap::new();
        for word in words {
            *word_freq.entry(word).or_insert(0) += 1;
        }
        
        // Return top 5 most frequent
        let mut concepts: Vec<_> = word_freq.into_iter().collect();
        concepts.sort_by(|a, b| b.1.cmp(&a.1));
        concepts.into_iter()
            .take(5)
            .map(|(word, _)| word)
            .collect()
    }
    
    fn assess_quality(text: &str, content: &[ImportedContent]) -> QualityMetrics {
        let readability = Self::calculate_reading_level(text);
        let structure = Self::calculate_structure_score(content);
        let engagement = Self::calculate_engagement_score(text);
        let accessibility = Self::calculate_accessibility_score(text, content);
        let completeness = Self::calculate_completeness_score(content);
        
        let overall = (readability + structure + engagement + accessibility + completeness) / 5.0;
        
        QualityMetrics {
            readability_score: Self::normalize_score(readability, 8.0, 16.0),
            structure_score: structure,
            engagement_score: engagement,
            accessibility_score: accessibility,
            completeness_score: completeness,
            overall_quality: overall,
        }
    }
    
    fn normalize_score(value: f32, min: f32, max: f32) -> f32 {
        // Normalize to 0-1 range where middle is best
        if value < min {
            value / min
        } else if value > max {
            2.0 - (value / max)
        } else {
            1.0
        }.clamp(0.0, 1.0)
    }
    
    fn calculate_structure_score(content: &[ImportedContent]) -> f32 {
        let mut score = 0.0;
        let checks = [
            content.iter().any(|c| c.content_type.contains("Introduction")),
            content.iter().any(|c| c.content_type.contains("Objective")),
            content.iter().any(|c| c.content_type.contains("Content")),
            content.iter().any(|c| c.content_type.contains("Activity")),
            content.iter().any(|c| c.content_type.contains("Assessment")),
            content.iter().any(|c| c.content_type.contains("Summary")),
        ];
        
        for check in checks {
            if check {
                score += 1.0 / checks.len() as f32;
            }
        }
        
        score
    }
    
    fn calculate_engagement_score(text: &str) -> f32 {
        let mut score: f32 = 0.5; // Base score
        let text_lower = text.to_lowercase();
        
        // Check for engagement indicators
        let engagement_terms = ["activity", "exercise", "practice", "example", 
                                "hands-on", "interactive", "collaborate", "discuss",
                                "explore", "create", "build", "design"];
        
        let count = engagement_terms.iter()
            .filter(|term| text_lower.contains(*term))
            .count();
        
        score += (count as f32 * 0.05).min(0.5);
        score.clamp(0.0, 1.0)
    }
    
    fn calculate_accessibility_score(text: &str, content: &[ImportedContent]) -> f32 {
        let mut score: f32 = 0.7; // Base score
        
        // Check for clear headings
        if content.iter().all(|c| !c.title.is_empty()) {
            score += 0.1;
        }
        
        // Check for reasonable reading level
        let reading_level = Self::calculate_reading_level(text);
        if reading_level >= 8.0 && reading_level <= 12.0 {
            score += 0.1;
        }
        
        // Check for varied content types
        let unique_types: std::collections::HashSet<_> = content.iter()
            .map(|c| &c.content_type)
            .collect();
        if unique_types.len() > 3 {
            score += 0.1;
        }
        
        score.clamp(0.0, 1.0)
    }
    
    fn calculate_completeness_score(content: &[ImportedContent]) -> f32 {
        let mut score = 0.0;
        let expected_components = [
            ("Introduction", content.iter().any(|c| c.content_type.contains("Introduction"))),
            ("Learning Objectives", content.iter().any(|c| c.content_type.contains("Objective"))),
            ("Main Content", content.iter().any(|c| c.content_type.contains("Content") || c.content_type == "Slide")),
            ("Examples", content.iter().any(|c| c.content.to_lowercase().contains("example"))),
            ("Activities", content.iter().any(|c| c.content_type.contains("Activity"))),
            ("Assessment", content.iter().any(|c| c.content_type.contains("Assessment") || c.content_type.contains("Quiz"))),
            ("Summary", content.iter().any(|c| c.content_type.contains("Summary") || c.title.to_lowercase().contains("conclusion"))),
        ];
        
        for (_, exists) in expected_components {
            if exists {
                score += 1.0 / expected_components.len() as f32;
            }
        }
        
        score
    }
    
    fn identify_improvements(content: &[ImportedContent]) -> Vec<ImprovementArea> {
        let mut improvements = Vec::new();
        
        // Check for learning objectives
        let has_objectives = content.iter()
            .any(|c| c.content_type.contains("Objective"));
        
        if !has_objectives {
            improvements.push(ImprovementArea {
                category: ImprovementCategory::LearningObjectives,
                description: "No clear learning objectives found".to_string(),
                priority: Priority::High,
                suggested_action: "Add specific, measurable learning objectives using action verbs".to_string(),
                estimated_impact: 0.8,
            });
        }
        
        // Check for assessments
        let has_assessment = content.iter()
            .any(|c| c.content_type.contains("Assessment") || c.content_type.contains("Quiz"));
        
        if !has_assessment {
            improvements.push(ImprovementArea {
                category: ImprovementCategory::Assessment,
                description: "No assessment or quiz found".to_string(),
                priority: Priority::Medium,
                suggested_action: "Add formative assessments to measure learning objective achievement".to_string(),
                estimated_impact: 0.7,
            });
        }
        
        // Check for engagement
        let total_text = content.iter()
            .map(|c| c.content.as_str())
            .collect::<Vec<_>>()
            .join(" ");
        
        let engagement_score = Self::calculate_engagement_score(&total_text);
        if engagement_score < 0.6 {
            improvements.push(ImprovementArea {
                category: ImprovementCategory::Engagement,
                description: "Limited interactive or engaging elements".to_string(),
                priority: Priority::Medium,
                suggested_action: "Add hands-on activities, examples, or collaborative exercises".to_string(),
                estimated_impact: 0.6,
            });
        }
        
        // Check reading level
        let avg_reading_level = content.iter()
            .map(|c| Self::calculate_reading_level(&c.content))
            .sum::<f32>() / content.len() as f32;
        
        if avg_reading_level > 14.0 {
            improvements.push(ImprovementArea {
                category: ImprovementCategory::Clarity,
                description: format!("Reading level too high ({:.1})", avg_reading_level),
                priority: Priority::Medium,
                suggested_action: "Simplify language and break down complex concepts".to_string(),
                estimated_impact: 0.5,
            });
        }
        
        improvements
    }
    
    fn find_content_gaps(content: &[ImportedContent]) -> Vec<ContentGap> {
        let mut gaps = Vec::new();
        
        // Check for missing examples
        let has_examples = content.iter()
            .any(|c| c.content.to_lowercase().contains("example") || 
                     c.content.to_lowercase().contains("for instance"));
        
        if !has_examples {
            gaps.push(ContentGap {
                gap_type: GapType::LackOfExamples,
                description: "No concrete examples found".to_string(),
                suggested_content: "Add 2-3 real-world examples for each main concept".to_string(),
                importance: 0.7,
            });
        }
        
        // Check for practice opportunities
        let has_practice = content.iter()
            .any(|c| c.content_type.contains("Activity") || 
                     c.content.to_lowercase().contains("practice") ||
                     c.content.to_lowercase().contains("exercise"));
        
        if !has_practice {
            gaps.push(ContentGap {
                gap_type: GapType::InsufficientPractice,
                description: "Limited practice opportunities".to_string(),
                suggested_content: "Add guided practice exercises with increasing difficulty".to_string(),
                importance: 0.8,
            });
        }
        
        // Check for visual content mentions
        let has_visuals = content.iter()
            .any(|c| c.metadata.has_images || 
                     c.content.to_lowercase().contains("diagram") ||
                     c.content.to_lowercase().contains("figure") ||
                     c.content.to_lowercase().contains("chart"));
        
        if !has_visuals {
            gaps.push(ContentGap {
                gap_type: GapType::MissingVisuals,
                description: "No visual learning aids detected".to_string(),
                suggested_content: "Add diagrams, charts, or infographics to illustrate key concepts".to_string(),
                importance: 0.6,
            });
        }
        
        gaps
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_bloom_classification() {
        assert!(matches!(
            ContentAnalyzer::classify_bloom_level("create"),
            BloomLevel::Create
        ));
        assert!(matches!(
            ContentAnalyzer::classify_bloom_level("analyze"),
            BloomLevel::Analyze
        ));
        assert!(matches!(
            ContentAnalyzer::classify_bloom_level("remember"),
            BloomLevel::Remember
        ));
    }
    
    #[test]
    fn test_syllable_counting() {
        assert_eq!(ContentAnalyzer::count_syllables("hello"), 2);
        assert_eq!(ContentAnalyzer::count_syllables("education"), 4);
        assert_eq!(ContentAnalyzer::count_syllables("a"), 1);
    }
}