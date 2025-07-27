use serde::{Deserialize, Serialize};
use anyhow::Result;
use uuid::Uuid;
use crate::content::{ContentType, ContentRequest, GeneratedContent, PedagogicalApproach};

/// Module structure for organizing educational content
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentModule {
    pub id: Uuid,
    pub title: String,
    pub description: String,
    pub learning_objectives: Vec<String>,
    pub estimated_duration_minutes: u32,
    pub content_items: Vec<ContentItem>,
    pub module_structure: ModuleStructure,
    pub dependencies: Vec<Uuid>, // Other modules this depends on
    pub assessments: Vec<AssessmentItem>,
    pub metadata: ModuleMetadata,
}

/// Individual content item within a module
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentItem {
    pub id: Uuid,
    pub content_type: ContentType,
    pub title: String,
    pub order_index: u32,
    pub estimated_duration_minutes: u32,
    pub content: Option<GeneratedContent>, // Populated when generated
    pub is_required: bool,
    pub dependencies: Vec<Uuid>, // Other content items this depends on
}

/// Structure and organization of a module
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModuleStructure {
    pub organization_type: ModuleOrganizationType,
    pub sections: Vec<ModuleSection>,
    pub flow_control: FlowControl,
}

/// Types of module organization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ModuleOrganizationType {
    Linear,        // Sequential progression through content
    Hierarchical,  // Nested topics with increasing complexity
    Hub,           // Central topic with related subtopics
    Spiral,        // Recurring themes with deepening understanding
    Workshop,      // Hands-on practice-focused organization
    Seminar,       // Discussion and analysis focused
}

/// Individual section within a module
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModuleSection {
    pub id: Uuid,
    pub title: String,
    pub description: String,
    pub content_items: Vec<Uuid>, // References to ContentItem IDs
    pub section_type: SectionType,
    pub estimated_duration_minutes: u32,
}

/// Types of module sections
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SectionType {
    Introduction,    // Opening and context setting
    CoreContent,     // Main instructional content
    Practice,        // Hands-on activities and exercises
    Assessment,      // Evaluation and testing
    Synthesis,       // Integration and summary
    Extension,       // Additional exploration opportunities
}

/// Flow control for module progression
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FlowControl {
    pub allow_nonlinear_access: bool,
    pub prerequisite_enforcement: bool,
    pub adaptive_sequencing: bool,
    pub branching_points: Vec<BranchingPoint>,
}

/// Decision points for different learning paths
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BranchingPoint {
    pub id: Uuid,
    pub condition: BranchingCondition,
    pub paths: Vec<LearningPath>,
}

/// Conditions for branching decisions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BranchingCondition {
    AssessmentScore(f32),           // Based on assessment performance
    LearnerPreference(String),      // Based on stated preferences
    PriorKnowledge(Vec<String>),    // Based on prerequisite knowledge
    LearningStyle(LearningStyle),   // Based on learning style preference
    TimeConstraint(u32),            // Based on available time (minutes)
}

/// Learning style preferences
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LearningStyle {
    Visual,
    Auditory,
    Kinesthetic,
    ReadingWriting,
    Multimodal,
}

/// Alternative learning paths
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LearningPath {
    pub id: Uuid,
    pub name: String,
    pub description: String,
    pub content_sequence: Vec<Uuid>, // Ordered content item IDs
    pub estimated_duration_minutes: u32,
}

/// Assessment items within a module
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssessmentItem {
    pub id: Uuid,
    pub assessment_type: AssessmentType,
    pub title: String,
    pub instructions: String,
    pub points_possible: u32,
    pub estimated_duration_minutes: u32,
    pub rubric: Option<AssessmentRubric>,
}

/// Types of assessments
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AssessmentType {
    Quiz,
    Assignment,
    Project,
    Discussion,
    Presentation,
    PeerReview,
    SelfReflection,
    Practical,
}

/// Assessment rubric for grading
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssessmentRubric {
    pub criteria: Vec<RubricCriterion>,
    pub performance_levels: Vec<PerformanceLevel>,
}

/// Individual criterion in a rubric
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RubricCriterion {
    pub name: String,
    pub description: String,
    pub weight: f32, // Percentage of total score
}

/// Performance levels for rubric scoring
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceLevel {
    pub level: String,
    pub description: String,
    pub point_value: u32,
}

/// Metadata about the module
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModuleMetadata {
    pub target_audience: String,
    pub difficulty_level: DifficultyLevel,
    pub pedagogical_approach: PedagogicalApproach,
    pub subject_area: String,
    pub keywords: Vec<String>,
    pub language: String,
    pub accessibility_features: Vec<AccessibilityFeature>,
    pub creation_date: chrono::DateTime<chrono::Utc>,
    pub last_modified: chrono::DateTime<chrono::Utc>,
    pub version: String,
}

/// Difficulty levels for modules
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DifficultyLevel {
    Beginner,
    Intermediate,
    Advanced,
    Expert,
    Mixed,
}

/// Accessibility features for inclusive design
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AccessibilityFeature {
    AltText,              // Alternative text for images
    ClosedCaptions,       // Captions for audio/video
    AudioDescriptions,    // Audio descriptions for visual content
    HighContrast,         // High contrast color schemes
    LargeText,            // Large text options
    ScreenReaderSupport,  // Screen reader compatibility
    KeyboardNavigation,   // Keyboard-only navigation
    SimplifiedLanguage,   // Simplified language options
}

/// Content type selection configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentTypeSelection {
    pub selected_types: Vec<ContentTypeConfig>,
    pub generation_preferences: GenerationPreferences,
    pub module_options: ModuleOptions,
}

/// Configuration for each content type
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentTypeConfig {
    pub content_type: ContentType,
    pub is_required: bool,
    pub priority: ContentPriority,
    pub customization: ContentCustomization,
    pub dependencies: Vec<ContentType>, // Other content types this depends on
}

/// Priority levels for content generation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ContentPriority {
    High,    // Generate first
    Medium,  // Generate after high priority
    Low,     // Generate last
    Optional, // Generate only if requested
}

/// Customization options for content types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentCustomization {
    pub template_preference: Option<String>,
    pub style_guidelines: Vec<String>,
    pub length_preference: LengthPreference,
    pub complexity_adjustment: ComplexityAdjustment,
}

/// Length preferences for content
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LengthPreference {
    Brief,    // Concise content
    Standard, // Normal length
    Detailed, // Comprehensive content
    Custom(u32), // Specific word/slide count
}

/// Complexity adjustments for content
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ComplexityAdjustment {
    Simplified,  // Reduce complexity
    Standard,    // Maintain original complexity
    Enhanced,    // Increase complexity
    Adaptive,    // Adjust based on audience
}

/// Generation preferences for the overall process
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GenerationPreferences {
    pub batch_generation: bool,
    pub parallel_processing: bool,
    pub quality_checks: bool,
    pub user_review_points: Vec<ReviewPoint>,
    pub auto_save_interval: Option<u32>, // Minutes
}

/// Points where user review is required
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ReviewPoint {
    AfterOutline,       // Review content outline before generation
    AfterEachType,      // Review each content type after generation
    AfterCompletion,    // Review everything at the end
    OnErrors,           // Review when errors occur
    OnQualityFlags,     // Review when quality issues detected
}

/// Module generation options
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModuleOptions {
    pub create_modules: bool,
    pub module_size_preference: ModuleSizePreference,
    pub organization_preference: ModuleOrganizationType,
    pub include_assessments: bool,
    pub adaptive_paths: bool,
}

/// Preferences for module sizing
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ModuleSizePreference {
    Small,    // 15-30 minutes
    Medium,   // 30-60 minutes
    Large,    // 60-90 minutes
    Extended, // 90+ minutes
    Custom(u32), // Specific duration in minutes
}

/// Module generator for organizing content
pub struct ModuleGenerator {
    // Will be injected with content generator and other dependencies
}

impl ModuleGenerator {
    pub fn new() -> Self {
        Self {}
    }

    /// Generate a complete module with selected content types
    pub async fn generate_module(
        &self,
        request: &ContentRequest,
        selection: &ContentTypeSelection,
    ) -> Result<ContentModule> {
        let module_id = Uuid::new_v4();
        let now = chrono::Utc::now();

        // Create basic module structure
        let mut module = ContentModule {
            id: module_id,
            title: format!("Module: {}", request.topic),
            description: format!("Educational module covering {}", request.topic),
            learning_objectives: request.learning_objectives.clone(),
            estimated_duration_minutes: self.calculate_estimated_duration(selection),
            content_items: Vec::new(),
            module_structure: self.create_module_structure(selection)?,
            dependencies: Vec::new(),
            assessments: Vec::new(),
            metadata: ModuleMetadata {
                target_audience: request.audience.clone(),
                difficulty_level: DifficultyLevel::Intermediate, // Default, should be configurable
                pedagogical_approach: PedagogicalApproach::GagnesNineEvents, // Default
                subject_area: request.topic.clone(),
                keywords: vec![request.topic.clone()],
                language: "en".to_string(),
                accessibility_features: vec![
                    AccessibilityFeature::AltText,
                    AccessibilityFeature::ScreenReaderSupport,
                ],
                creation_date: now,
                last_modified: now,
                version: "1.0".to_string(),
            },
        };

        // Generate content items based on selection
        module.content_items = self.create_content_items(request, selection)?;

        // Generate assessments if requested
        if selection.module_options.include_assessments {
            module.assessments = self.create_assessments(request, selection)?;
        }

        Ok(module)
    }

    /// Create the module structure based on preferences
    fn create_module_structure(&self, selection: &ContentTypeSelection) -> Result<ModuleStructure> {
        let sections = self.create_module_sections(selection)?;

        Ok(ModuleStructure {
            organization_type: selection.module_options.organization_preference.clone(),
            sections,
            flow_control: FlowControl {
                allow_nonlinear_access: selection.module_options.adaptive_paths,
                prerequisite_enforcement: true,
                adaptive_sequencing: selection.module_options.adaptive_paths,
                branching_points: Vec::new(), // Will be populated based on content
            },
        })
    }

    /// Create module sections based on content types
    fn create_module_sections(&self, selection: &ContentTypeSelection) -> Result<Vec<ModuleSection>> {
        let mut sections = Vec::new();

        // Introduction section
        sections.push(ModuleSection {
            id: Uuid::new_v4(),
            title: "Introduction".to_string(),
            description: "Module introduction and objectives".to_string(),
            content_items: Vec::new(),
            section_type: SectionType::Introduction,
            estimated_duration_minutes: 5,
        });

        // Core content section(s)
        let core_content_types: Vec<_> = selection
            .selected_types
            .iter()
            .filter(|ct| matches!(ct.content_type, ContentType::Slides | ContentType::InstructorNotes))
            .collect();

        if !core_content_types.is_empty() {
            sections.push(ModuleSection {
                id: Uuid::new_v4(),
                title: "Core Content".to_string(),
                description: "Main instructional content".to_string(),
                content_items: Vec::new(),
                section_type: SectionType::CoreContent,
                estimated_duration_minutes: 30,
            });
        }

        // Practice section
        let practice_content_types: Vec<_> = selection
            .selected_types
            .iter()
            .filter(|ct| matches!(ct.content_type, ContentType::Worksheet | ContentType::ActivityGuide))
            .collect();

        if !practice_content_types.is_empty() {
            sections.push(ModuleSection {
                id: Uuid::new_v4(),
                title: "Practice Activities".to_string(),
                description: "Hands-on practice and exercises".to_string(),
                content_items: Vec::new(),
                section_type: SectionType::Practice,
                estimated_duration_minutes: 20,
            });
        }

        // Assessment section
        let assessment_content_types: Vec<_> = selection
            .selected_types
            .iter()
            .filter(|ct| matches!(ct.content_type, ContentType::Quiz))
            .collect();

        if !assessment_content_types.is_empty() {
            sections.push(ModuleSection {
                id: Uuid::new_v4(),
                title: "Assessment".to_string(),
                description: "Knowledge check and evaluation".to_string(),
                content_items: Vec::new(),
                section_type: SectionType::Assessment,
                estimated_duration_minutes: 15,
            });
        }

        Ok(sections)
    }

    /// Create content items based on selected types
    fn create_content_items(
        &self,
        request: &ContentRequest,
        selection: &ContentTypeSelection,
    ) -> Result<Vec<ContentItem>> {
        let mut content_items = Vec::new();
        let mut order_index = 0;

        // Sort content types by priority
        let mut sorted_types = selection.selected_types.clone();
        sorted_types.sort_by(|a, b| {
            use ContentPriority::*;
            let a_priority = match &a.priority {
                High => 0,
                Medium => 1,
                Low => 2,
                Optional => 3,
            };
            let b_priority = match &b.priority {
                High => 0,
                Medium => 1,
                Low => 2,
                Optional => 3,
            };
            a_priority.cmp(&b_priority)
        });

        for content_config in sorted_types {
            let content_item = ContentItem {
                id: Uuid::new_v4(),
                content_type: content_config.content_type.clone(),
                title: format!("{} for {}", content_config.content_type, request.topic),
                order_index,
                estimated_duration_minutes: self.estimate_content_duration(&content_config),
                content: None, // Will be populated during generation
                is_required: content_config.is_required,
                dependencies: self.resolve_content_dependencies(&content_config, &content_items),
            };

            content_items.push(content_item);
            order_index += 1;
        }

        Ok(content_items)
    }

    /// Create assessment items for the module
    fn create_assessments(
        &self,
        _request: &ContentRequest,
        _selection: &ContentTypeSelection,
    ) -> Result<Vec<AssessmentItem>> {
        let mut assessments = Vec::new();

        // Knowledge check quiz
        assessments.push(AssessmentItem {
            id: Uuid::new_v4(),
            assessment_type: AssessmentType::Quiz,
            title: "Knowledge Check".to_string(),
            instructions: "Complete this quiz to check your understanding of the module content.".to_string(),
            points_possible: 100,
            estimated_duration_minutes: 10,
            rubric: None,
        });

        Ok(assessments)
    }

    /// Calculate estimated duration for the entire module
    fn calculate_estimated_duration(&self, selection: &ContentTypeSelection) -> u32 {
        let content_duration: u32 = selection
            .selected_types
            .iter()
            .map(|ct| self.estimate_content_duration(ct))
            .sum();

        // Add overhead for transitions, introductions, etc.
        let overhead = (content_duration as f32 * 0.2) as u32;
        content_duration + overhead
    }

    /// Estimate duration for a specific content type
    fn estimate_content_duration(&self, content_config: &ContentTypeConfig) -> u32 {
        // Base estimates for different content types
        let base_duration = match content_config.content_type {
            ContentType::Slides => 20,
            ContentType::InstructorNotes => 5,
            ContentType::Worksheet => 15,
            ContentType::Quiz => 10,
            ContentType::ActivityGuide => 25,
        };

        // Adjust based on complexity and length preferences
        let complexity_multiplier = match content_config.customization.complexity_adjustment {
            ComplexityAdjustment::Simplified => 0.8,
            ComplexityAdjustment::Standard => 1.0,
            ComplexityAdjustment::Enhanced => 1.3,
            ComplexityAdjustment::Adaptive => 1.1,
        };

        let length_multiplier = match content_config.customization.length_preference {
            LengthPreference::Brief => 0.7,
            LengthPreference::Standard => 1.0,
            LengthPreference::Detailed => 1.5,
            LengthPreference::Custom(_) => 1.0, // Would need specific calculation
        };

        ((base_duration as f32) * complexity_multiplier * length_multiplier) as u32
    }

    /// Resolve dependencies between content items
    fn resolve_content_dependencies(
        &self,
        content_config: &ContentTypeConfig,
        existing_items: &[ContentItem],
    ) -> Vec<Uuid> {
        let mut dependencies = Vec::new();

        for dep_type in &content_config.dependencies {
            if let Some(existing_item) = existing_items
                .iter()
                .find(|item| item.content_type == *dep_type)
            {
                dependencies.push(existing_item.id);
            }
        }

        dependencies
    }

    /// Get content type selection recommendations based on request
    pub fn recommend_content_types(&self, request: &ContentRequest) -> ContentTypeSelection {
        let mut selected_types = Vec::new();

        // Always recommend slides as core content
        selected_types.push(ContentTypeConfig {
            content_type: ContentType::Slides,
            is_required: true,
            priority: ContentPriority::High,
            customization: ContentCustomization {
                template_preference: None,
                style_guidelines: Vec::new(),
                length_preference: LengthPreference::Standard,
                complexity_adjustment: ComplexityAdjustment::Standard,
            },
            dependencies: Vec::new(),
        });

        // Recommend instructor notes for presenter support
        selected_types.push(ContentTypeConfig {
            content_type: ContentType::InstructorNotes,
            is_required: false,
            priority: ContentPriority::Medium,
            customization: ContentCustomization {
                template_preference: None,
                style_guidelines: Vec::new(),
                length_preference: LengthPreference::Standard,
                complexity_adjustment: ComplexityAdjustment::Standard,
            },
            dependencies: vec![ContentType::Slides],
        });

        // Recommend practice materials based on duration
        if self.parse_duration(&request.duration) >= 30 {
            selected_types.push(ContentTypeConfig {
                content_type: ContentType::Worksheet,
                is_required: false,
                priority: ContentPriority::Medium,
                customization: ContentCustomization {
                    template_preference: None,
                    style_guidelines: Vec::new(),
                    length_preference: LengthPreference::Standard,
                    complexity_adjustment: ComplexityAdjustment::Standard,
                },
                dependencies: vec![ContentType::Slides],
            });
        }

        // Recommend assessment for longer sessions
        if self.parse_duration(&request.duration) >= 45 {
            selected_types.push(ContentTypeConfig {
                content_type: ContentType::Quiz,
                is_required: false,
                priority: ContentPriority::Low,
                customization: ContentCustomization {
                    template_preference: None,
                    style_guidelines: Vec::new(),
                    length_preference: LengthPreference::Brief,
                    complexity_adjustment: ComplexityAdjustment::Standard,
                },
                dependencies: vec![ContentType::Slides],
            });
        }

        ContentTypeSelection {
            selected_types,
            generation_preferences: GenerationPreferences {
                batch_generation: true,
                parallel_processing: true,
                quality_checks: true,
                user_review_points: vec![ReviewPoint::AfterOutline],
                auto_save_interval: Some(5),
            },
            module_options: ModuleOptions {
                create_modules: true,
                module_size_preference: ModuleSizePreference::Medium,
                organization_preference: ModuleOrganizationType::Linear,
                include_assessments: self.parse_duration(&request.duration) >= 45,
                adaptive_paths: false,
            },
        }
    }

    /// Parse duration string to minutes
    fn parse_duration(&self, duration: &str) -> u32 {
        // Simple parser for common duration formats
        let duration_lower = duration.to_lowercase();
        
        if duration_lower.contains("hour") {
            if duration_lower.contains("1") || duration_lower.contains("one") {
                60
            } else if duration_lower.contains("2") || duration_lower.contains("two") {
                120
            } else {
                90 // Default to 1.5 hours
            }
        } else if duration_lower.contains("minute") {
            duration_lower
                .chars()
                .filter(|c| c.is_ascii_digit())
                .collect::<String>()
                .parse()
                .unwrap_or(45)
        } else {
            45 // Default duration
        }
    }
}

