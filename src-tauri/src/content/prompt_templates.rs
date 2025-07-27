use serde::{Deserialize, Serialize};
use handlebars::{Handlebars, Context, RenderContext, Helper, Output, HelperResult, JsonRender};
use anyhow::Result;
use std::collections::HashMap;
use crate::content::{ContentType, ContentRequest};

/// Prompt template system for educational content generation
#[derive(Debug)]
pub struct PromptTemplateEngine {
    handlebars: Handlebars<'static>,
    templates: HashMap<String, PromptTemplate>,
}

/// Educational prompt template with metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptTemplate {
    pub id: String,
    pub name: String,
    pub description: String,
    pub content_type: ContentType,
    pub template_content: String,
    pub required_variables: Vec<String>,
    pub optional_variables: Vec<String>,
    pub pedagogical_approach: PedagogicalApproach,
    pub difficulty_level: DifficultyLevel,
    pub language: String,
    pub version: String,
}

/// Pedagogical approaches for content generation
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum PedagogicalApproach {
    GagnesNineEvents,      // Gagne's Nine Events of Instruction
    BloomsRevised,         // Revised Bloom's Taxonomy
    ConstructivistLearning, // Constructivist Learning Theory
    ScaffoldedLearning,    // Scaffolded Learning Approach
    InquiryBased,          // Inquiry-Based Learning
    ProblemBased,          // Problem-Based Learning
    CollaborativeLearning, // Collaborative Learning
    ExperientialLearning,  // Experiential Learning
    FlippedClassroom,      // Flipped Classroom Model
    MasteryLearning,       // Mastery Learning
}

/// Difficulty levels for educational content
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DifficultyLevel {
    Beginner,
    Intermediate,
    Advanced,
    Expert,
    Mixed, // Contains multiple difficulty levels
}

/// Template rendering context with educational metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemplateContext {
    pub content_request: ContentRequest,
    pub variables: HashMap<String, serde_json::Value>,
    pub pedagogical_metadata: PedagogicalMetadata,
    pub content_metadata: ContentGenerationMetadata,
}

/// Pedagogical metadata for template rendering
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PedagogicalMetadata {
    pub approach: PedagogicalApproach,
    pub difficulty_level: DifficultyLevel,
    pub prerequisite_knowledge: Vec<String>,
    pub learning_outcomes: Vec<String>,
    pub assessment_methods: Vec<String>,
    pub time_allocation: TimeAllocation,
}

/// Time allocation for different learning activities
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimeAllocation {
    pub total_duration_minutes: u32,
    pub introduction_percent: f32,
    pub content_delivery_percent: f32,
    pub practice_percent: f32,
    pub assessment_percent: f32,
    pub wrap_up_percent: f32,
}

/// Content generation metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentGenerationMetadata {
    pub target_word_count: Option<u32>,
    pub reading_level: ReadingLevel,
    pub include_examples: bool,
    pub include_activities: bool,
    pub include_assessments: bool,
    pub multimedia_suggestions: bool,
    pub accessibility_features: Vec<AccessibilityFeature>,
}

/// Reading level for educational content
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ReadingLevel {
    Elementary,
    MiddleSchool,
    HighSchool,
    College,
    Graduate,
    Professional,
}

/// Accessibility features for inclusive education
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AccessibilityFeature {
    AltTextForImages,
    HighContrastSupport,
    LargeTextOptions,
    ScreenReaderFriendly,
    SimplifiedLanguage,
    VisualAids,
    AudioTranscripts,
    ClosedCaptions,
}

/// Template validation result
#[derive(Debug, Clone)]
pub struct TemplateValidationResult {
    pub is_valid: bool,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
    pub missing_variables: Vec<String>,
    pub unused_variables: Vec<String>,
}

impl PromptTemplateEngine {
    /// Create a new prompt template engine
    pub fn new() -> Result<Self> {
        let mut handlebars = Handlebars::new();
        
        // Register custom helpers for educational content
        Self::register_helpers(&mut handlebars)?;
        
        let mut engine = Self {
            handlebars,
            templates: HashMap::new(),
        };
        
        // Load default educational templates
        engine.load_default_templates()?;
        
        Ok(engine)
    }

    /// Register custom Handlebars helpers for educational content
    fn register_helpers(handlebars: &mut Handlebars) -> Result<()> {
        // Helper for formatting learning objectives
        handlebars.register_helper("format_objectives", Box::new(format_objectives_helper));
        
        // Helper for generating assessment questions
        handlebars.register_helper("assessment_questions", Box::new(assessment_questions_helper));
        
        // Helper for time allocation formatting
        handlebars.register_helper("time_format", Box::new(time_format_helper));
        
        // Helper for difficulty-appropriate language
        handlebars.register_helper("difficulty_language", Box::new(difficulty_language_helper));
        
        // Helper for pedagogical structure
        handlebars.register_helper("pedagogical_structure", Box::new(pedagogical_structure_helper));
        
        // Helper for accessibility features
        handlebars.register_helper("accessibility", Box::new(accessibility_helper));
        
        // Helper for mathematical operations
        handlebars.register_helper("multiply", Box::new(multiply_helper));
        
        Ok(())
    }

    /// Load default educational templates
    fn load_default_templates(&mut self) -> Result<()> {
        // Load slide presentation template
        self.add_template(create_slides_template())?;
        
        // Load instructor notes template
        self.add_template(create_instructor_notes_template())?;
        
        // Load worksheet template
        self.add_template(create_worksheet_template())?;
        
        // Load quiz template
        self.add_template(create_quiz_template())?;
        
        // Load activity guide template
        self.add_template(create_activity_guide_template())?;
        
        Ok(())
    }

    /// Add a new template to the engine
    pub fn add_template(&mut self, template: PromptTemplate) -> Result<()> {
        // Validate template before adding
        let validation = self.validate_template(&template)?;
        if !validation.is_valid {
            return Err(anyhow::anyhow!("Template validation failed: {:?}", validation.errors));
        }
        
        // Register with Handlebars
        self.handlebars.register_template_string(&template.id, &template.template_content)?;
        
        // Store template metadata
        self.templates.insert(template.id.clone(), template);
        
        Ok(())
    }

    /// Render a template with the given context
    pub fn render_template(&self, template_id: &str, context: &TemplateContext) -> Result<String> {
        let _template = self.templates.get(template_id)
            .ok_or_else(|| anyhow::anyhow!("Template '{}' not found", template_id))?;
        
        // Create Handlebars context
        let handlebars_context = self.create_handlebars_context(context)?;
        
        // Render template
        let rendered = self.handlebars.render(template_id, &handlebars_context)?;
        
        Ok(rendered)
    }

    /// Create Handlebars context from template context
    fn create_handlebars_context(&self, context: &TemplateContext) -> Result<serde_json::Value> {
        let mut data = serde_json::Map::new();
        
        // Add content request data
        data.insert("topic".to_string(), serde_json::Value::String(context.content_request.topic.clone()));
        data.insert("learning_objectives".to_string(), serde_json::Value::Array(
            context.content_request.learning_objectives.iter()
                .map(|obj| serde_json::Value::String(obj.clone()))
                .collect()
        ));
        data.insert("duration".to_string(), serde_json::Value::String(context.content_request.duration.clone()));
        data.insert("audience".to_string(), serde_json::Value::String(context.content_request.audience.clone()));
        
        // Add custom variables
        for (key, value) in &context.variables {
            data.insert(key.clone(), value.clone());
        }
        
        // Add pedagogical metadata
        data.insert("pedagogical".to_string(), serde_json::to_value(&context.pedagogical_metadata)?);
        
        // Add content metadata
        data.insert("content_meta".to_string(), serde_json::to_value(&context.content_metadata)?);
        
        Ok(serde_json::Value::Object(data))
    }

    /// Validate a template
    pub fn validate_template(&self, template: &PromptTemplate) -> Result<TemplateValidationResult> {
        let mut result = TemplateValidationResult {
            is_valid: true,
            errors: Vec::new(),
            warnings: Vec::new(),
            missing_variables: Vec::new(),
            unused_variables: Vec::new(),
        };

        // Check if template content is not empty
        if template.template_content.trim().is_empty() {
            result.errors.push("Template content cannot be empty".to_string());
            result.is_valid = false;
        }

        // Try to compile the template with a temporary Handlebars instance
        let mut temp_handlebars = Handlebars::new();
        match temp_handlebars.register_template_string("validation_temp", &template.template_content) {
            Ok(_) => {
                // Template compiles successfully
            }
            Err(e) => {
                result.errors.push(format!("Template compilation error: {}", e));
                result.is_valid = false;
            }
        }

        // Check for required variables (basic check)
        for required_var in &template.required_variables {
            if !template.template_content.contains(&format!("{{{{{}}}}}", required_var)) {
                result.missing_variables.push(required_var.clone());
                result.warnings.push(format!("Required variable '{}' not found in template", required_var));
            }
        }

        Ok(result)
    }

    /// Get template by ID
    pub fn get_template(&self, template_id: &str) -> Option<&PromptTemplate> {
        self.templates.get(template_id)
    }

    /// List all available templates
    pub fn list_templates(&self) -> Vec<&PromptTemplate> {
        self.templates.values().collect()
    }

    /// List templates by content type
    pub fn list_templates_by_type(&self, content_type: &ContentType) -> Vec<&PromptTemplate> {
        self.templates.values()
            .filter(|t| &t.content_type == content_type)
            .collect()
    }

    /// Get template suggestions based on pedagogical approach
    pub fn suggest_templates(&self, approach: &PedagogicalApproach, content_type: &ContentType) -> Vec<&PromptTemplate> {
        self.templates.values()
            .filter(|t| &t.content_type == content_type && &t.pedagogical_approach == approach)
            .collect()
    }

    /// Create a context from a content request with defaults
    pub fn create_context_from_request(&self, request: &ContentRequest) -> TemplateContext {
        TemplateContext {
            content_request: request.clone(),
            variables: HashMap::new(),
            pedagogical_metadata: PedagogicalMetadata {
                approach: PedagogicalApproach::BloomsRevised,
                difficulty_level: DifficultyLevel::Intermediate,
                prerequisite_knowledge: Vec::new(),
                learning_outcomes: request.learning_objectives.clone(),
                assessment_methods: vec!["Formative Assessment".to_string(), "Summative Assessment".to_string()],
                time_allocation: TimeAllocation {
                    total_duration_minutes: Self::parse_duration(&request.duration),
                    introduction_percent: 10.0,
                    content_delivery_percent: 50.0,
                    practice_percent: 25.0,
                    assessment_percent: 10.0,
                    wrap_up_percent: 5.0,
                },
            },
            content_metadata: ContentGenerationMetadata {
                target_word_count: None,
                reading_level: ReadingLevel::College,
                include_examples: true,
                include_activities: true,
                include_assessments: true,
                multimedia_suggestions: true,
                accessibility_features: vec![
                    AccessibilityFeature::ScreenReaderFriendly,
                    AccessibilityFeature::HighContrastSupport,
                ],
            },
        }
    }

    /// Parse duration string to minutes
    fn parse_duration(duration: &str) -> u32 {
        // Simple parser for duration strings like "60 minutes", "1 hour", etc.
        let duration_lower = duration.to_lowercase();
        if duration_lower.contains("hour") {
            if let Some(hours) = duration_lower.split_whitespace().next().and_then(|s| s.parse::<u32>().ok()) {
                return hours * 60;
            }
        } else if duration_lower.contains("minute") {
            if let Some(minutes) = duration_lower.split_whitespace().next().and_then(|s| s.parse::<u32>().ok()) {
                return minutes;
            }
        }
        60 // Default to 60 minutes
    }
}

impl Default for PromptTemplateEngine {
    fn default() -> Self {
        Self::new().unwrap_or_else(|_| Self {
            handlebars: Handlebars::new(),
            templates: HashMap::new(),
        })
    }
}

// Custom Handlebars helpers for educational content

fn format_objectives_helper(
    h: &Helper,
    _: &Handlebars,
    _: &Context,
    _: &mut RenderContext,
    out: &mut dyn Output,
) -> HelperResult {
    if let Some(objectives) = h.param(0) {
        if let Some(array) = objectives.value().as_array() {
            let formatted: Vec<String> = array.iter()
                .enumerate()
                .map(|(i, obj)| format!("{}. {}", i + 1, obj.render()))
                .collect();
            out.write(&formatted.join("\n"))?;
        }
    }
    Ok(())
}

fn assessment_questions_helper(
    h: &Helper,
    _: &Handlebars,
    _: &Context,
    _: &mut RenderContext,
    out: &mut dyn Output,
) -> HelperResult {
    let topic = h.param(0).map(|v| v.render()).unwrap_or("the topic".to_string());
    let count = h.param(1)
        .and_then(|v| v.value().as_u64())
        .unwrap_or(3) as usize;
    
    let question_starters = [
        "What are the key concepts of",
        "How does",
        "Why is",
        "Compare and contrast",
        "Analyze the relationship between",
        "Evaluate the effectiveness of",
        "Apply the principles of",
    ];
    
    let questions: Vec<String> = question_starters.iter()
        .take(count)
        .enumerate()
        .map(|(i, starter)| format!("{}. {} {}?", i + 1, starter, topic))
        .collect();
    
    out.write(&questions.join("\n"))?;
    Ok(())
}

fn time_format_helper(
    h: &Helper,
    _: &Handlebars,
    _: &Context,
    _: &mut RenderContext,
    out: &mut dyn Output,
) -> HelperResult {
    if let Some(minutes) = h.param(0).and_then(|v| v.value().as_u64()) {
        if minutes >= 60 {
            let hours = minutes / 60;
            let remaining_minutes = minutes % 60;
            if remaining_minutes > 0 {
                out.write(&format!("{} hour(s) and {} minute(s)", hours, remaining_minutes))?;
            } else {
                out.write(&format!("{} hour(s)", hours))?;
            }
        } else {
            out.write(&format!("{} minute(s)", minutes))?;
        }
    }
    Ok(())
}

fn difficulty_language_helper(
    h: &Helper,
    _: &Handlebars,
    _: &Context,
    _: &mut RenderContext,
    out: &mut dyn Output,
) -> HelperResult {
    let text = h.param(0).map(|v| v.render()).unwrap_or_default();
    let level = h.param(1).map(|v| v.render()).unwrap_or("Intermediate".to_string());
    
    // Adjust language complexity based on difficulty level
    let adjusted_text = match level.as_str() {
        "Beginner" => text.replace("utilize", "use")
            .replace("demonstrate", "show")
            .replace("comprehend", "understand"),
        "Advanced" | "Expert" => text.replace("use", "utilize")
            .replace("show", "demonstrate")
            .replace("understand", "comprehend"),
        _ => text, // Intermediate - no changes
    };
    
    out.write(&adjusted_text)?;
    Ok(())
}

fn pedagogical_structure_helper(
    h: &Helper,
    _: &Handlebars,
    _: &Context,
    _: &mut RenderContext,
    out: &mut dyn Output,
) -> HelperResult {
    let approach = h.param(0).map(|v| v.render()).unwrap_or("BloomsRevised".to_string());
    
    let structure = match approach.as_str() {
        "GagnesNineEvents" => "1. Gain Attention\n2. Inform Learners of Objectives\n3. Stimulate Recall\n4. Present Content\n5. Provide Learning Guidance\n6. Elicit Performance\n7. Provide Feedback\n8. Assess Performance\n9. Enhance Retention",
        "BloomsRevised" => "1. Remember (Recall facts)\n2. Understand (Explain concepts)\n3. Apply (Use knowledge)\n4. Analyze (Break down)\n5. Evaluate (Make judgments)\n6. Create (Produce new work)",
        "ProblemBased" => "1. Problem Presentation\n2. Problem Analysis\n3. Hypothesis Generation\n4. Learning Issues Identification\n5. Self-Directed Learning\n6. Solution Development\n7. Solution Evaluation",
        _ => "1. Introduction\n2. Content Delivery\n3. Practice\n4. Assessment\n5. Conclusion",
    };
    
    out.write(structure)?;
    Ok(())
}

fn accessibility_helper(
    h: &Helper,
    _: &Handlebars,
    _: &Context,
    _: &mut RenderContext,
    out: &mut dyn Output,
) -> HelperResult {
    let feature = h.param(0).map(|v| v.render()).unwrap_or_default();
    
    let guidance = match feature.as_str() {
        "ScreenReaderFriendly" => "Include descriptive headings and clear structure for screen readers.",
        "HighContrastSupport" => "Ensure high contrast between text and background colors.",
        "SimplifiedLanguage" => "Use clear, simple language and avoid unnecessary jargon.",
        "VisualAids" => "Include diagrams, charts, and visual representations to support learning.",
        _ => "Consider accessibility needs in content design.",
    };
    
    out.write(guidance)?;
    Ok(())
}

fn multiply_helper(
    h: &Helper,
    _: &Handlebars,
    _: &Context,
    _: &mut RenderContext,
    out: &mut dyn Output,
) -> HelperResult {
    let num1 = h.param(0).and_then(|v| v.value().as_f64()).unwrap_or(0.0);
    let num2 = h.param(1).and_then(|v| v.value().as_f64()).unwrap_or(0.0);
    let num3 = h.param(2).and_then(|v| v.value().as_f64()).unwrap_or(1.0);
    
    let result = num1 * num2 * num3;
    out.write(&format!("{:.0}", result))?;
    Ok(())
}

// Template factory functions

fn create_slides_template() -> PromptTemplate {
    PromptTemplate {
        id: "educational_slides".to_string(),
        name: "Educational Slide Presentation".to_string(),
        description: "Template for creating educational slide presentations".to_string(),
        content_type: ContentType::Slides,
        template_content: r#"# {{topic}}

## Slide 1: Title Slide
**{{topic}}**
*Duration: {{time_format pedagogical.time_allocation.total_duration_minutes}}*

{{#each learning_objectives}}
{{format_objectives this}}
{{/each}}

## Slide 2: Learning Objectives
{{pedagogical_structure pedagogical.approach}}

## Slide 3: Introduction
{{difficulty_language "This presentation will cover the fundamental concepts of {{topic}}" pedagogical.difficulty_level}}

{{#if content_meta.include_examples}}
## Slide 4: Key Examples
- Example 1: [Provide relevant example]
- Example 2: [Provide relevant example]
- Example 3: [Provide relevant example]
{{/if}}

## Slide 5: Main Content
[Detailed content about {{topic}} goes here]

{{#if content_meta.include_activities}}
## Slide 6: Interactive Activity
**Activity**: [Design an interactive element related to {{topic}}]
*Time: {{time_format (multiply pedagogical.time_allocation.total_duration_minutes pedagogical.time_allocation.practice_percent 0.01)}} minutes*
{{/if}}

{{#if content_meta.include_assessments}}
## Slide 7: Assessment Questions
{{assessment_questions topic 3}}
{{/if}}

## Slide 8: Summary
Key takeaways from today's lesson on {{topic}}:
{{#each learning_objectives}}
- {{this}}
{{/each}}

## Slide 9: Next Steps
[Outline follow-up activities or next lesson topics]

{{#each content_meta.accessibility_features}}
---
**Accessibility Note**: {{accessibility this}}
{{/each}}"#.to_string(),
        required_variables: vec!["topic".to_string(), "learning_objectives".to_string()],
        optional_variables: vec!["duration".to_string(), "audience".to_string()],
        pedagogical_approach: PedagogicalApproach::BloomsRevised,
        difficulty_level: DifficultyLevel::Mixed,
        language: "en".to_string(),
        version: "1.0.0".to_string(),
    }
}

fn create_instructor_notes_template() -> PromptTemplate {
    PromptTemplate {
        id: "instructor_notes".to_string(),
        name: "Instructor Teaching Notes".to_string(),
        description: "Comprehensive instructor notes for lesson delivery".to_string(),
        content_type: ContentType::InstructorNotes,
        template_content: r#"# Instructor Notes: {{topic}}

## Lesson Overview
**Topic**: {{topic}}
**Duration**: {{time_format pedagogical.time_allocation.total_duration_minutes}}
**Audience**: {{audience}}

## Learning Objectives
{{#each learning_objectives}}
{{format_objectives this}}
{{/each}}

## Pedagogical Approach
{{pedagogical_structure pedagogical.approach}}

## Pre-Class Preparation
### Materials Needed
- [List required materials]
- [Technology requirements]
- [Handouts or worksheets]

### Prerequisite Knowledge
{{#each pedagogical.prerequisite_knowledge}}
- {{this}}
{{/each}}

## Lesson Structure

### Introduction ({{multiply pedagogical.time_allocation.introduction_percent 0.01 pedagogical.time_allocation.total_duration_minutes}} minutes)
**Opening Hook**: [Attention-grabbing opening related to {{topic}}]

**Objectives Review**: 
{{difficulty_language "Today we will explore {{topic}} and by the end of this lesson, you will be able to..." pedagogical.difficulty_level}}

### Main Content Delivery ({{multiply pedagogical.time_allocation.content_delivery_percent 0.01 pedagogical.time_allocation.total_duration_minutes}} minutes)

#### Key Concepts to Cover:
1. [Primary concept of {{topic}}]
2. [Secondary concepts]
3. [Advanced applications]

#### Teaching Strategies:
- {{difficulty_language "Use clear explanations and build from basic to complex concepts" pedagogical.difficulty_level}}
- Incorporate real-world examples
- Check for understanding regularly

{{#if content_meta.include_examples}}
#### Examples to Use:
- Example 1: [Detailed example with explanation]
- Example 2: [Alternative approach example]
- Example 3: [Complex application example]
{{/if}}

### Practice Activities ({{multiply pedagogical.time_allocation.practice_percent 0.01 pedagogical.time_allocation.total_duration_minutes}} minutes)

{{#if content_meta.include_activities}}
**Main Activity**: 
[Detailed activity instructions for {{topic}}]

**Facilitation Notes**:
- Monitor student progress
- Provide individual support as needed
- Encourage collaboration
{{/if}}

### Assessment ({{multiply pedagogical.time_allocation.assessment_percent 0.01 pedagogical.time_allocation.total_duration_minutes}} minutes)

{{#if content_meta.include_assessments}}
**Formative Assessment Questions**:
{{assessment_questions topic 5}}

**Assessment Methods**:
{{#each pedagogical.assessment_methods}}
- {{this}}
{{/each}}
{{/if}}

### Wrap-up ({{multiply pedagogical.time_allocation.wrap_up_percent 0.01 pedagogical.time_allocation.total_duration_minutes}} minutes)
- Summarize key points
- Connect to learning objectives
- Preview next lesson

## Differentiation Strategies
### For Advanced Learners:
- [Additional challenges]
- [Extension activities]

### For Struggling Learners:
- [Additional support strategies]
- [Simplified explanations]

### For English Language Learners:
- [Language support strategies]
- [Visual aids and gestures]

## Technology Integration
{{#if content_meta.multimedia_suggestions}}
- Interactive presentations
- Online simulations
- Video demonstrations
- Digital assessment tools
{{/if}}

## Accessibility Considerations
{{#each content_meta.accessibility_features}}
- {{accessibility this}}
{{/each}}

## Extension Activities
- [Follow-up assignments]
- [Real-world applications]
- [Research projects]

## Resources and References
- [Textbook chapters]
- [Online resources]
- [Additional reading materials]

## Reflection Questions
1. What aspects of {{topic}} did students find most challenging?
2. Which teaching strategies were most effective?
3. How can this lesson be improved for next time?
4. Did all students achieve the learning objectives?"#.to_string(),
        required_variables: vec!["topic".to_string(), "learning_objectives".to_string()],
        optional_variables: vec!["duration".to_string(), "audience".to_string()],
        pedagogical_approach: PedagogicalApproach::GagnesNineEvents,
        difficulty_level: DifficultyLevel::Mixed,
        language: "en".to_string(),
        version: "1.0.0".to_string(),
    }
}

fn create_worksheet_template() -> PromptTemplate {
    PromptTemplate {
        id: "student_worksheet".to_string(),
        name: "Student Practice Worksheet".to_string(),
        description: "Interactive worksheet for student practice and reinforcement".to_string(),
        content_type: ContentType::Worksheet,
        template_content: r#"# {{topic}} - Practice Worksheet

**Name**: _________________________ **Date**: _____________

## Instructions
{{difficulty_language "Complete the following exercises to practice your understanding of {{topic}}. Show your work and explain your reasoning where indicated." pedagogical.difficulty_level}}

## Learning Objectives Review
By completing this worksheet, you will demonstrate your ability to:
{{#each learning_objectives}}
{{format_objectives this}}
{{/each}}

## Part 1: Vocabulary and Concepts (20 points)

### A. Key Terms
Define the following terms related to {{topic}}:

1. [Key term 1]: ________________________________
   ________________________________________________

2. [Key term 2]: ________________________________
   ________________________________________________

3. [Key term 3]: ________________________________
   ________________________________________________

### B. Concept Mapping
Create a concept map showing the relationships between the main ideas in {{topic}}.

[Space for concept map]

## Part 2: Application Exercises (30 points)

{{#if content_meta.include_examples}}
### Exercise 1: Guided Practice
Following the example demonstrated in class, solve the following problem:

**Problem**: [Problem statement related to {{topic}}]

**Solution**:
Step 1: ________________________________________
Step 2: ________________________________________
Step 3: ________________________________________
Answer: _______________________________________

### Exercise 2: Independent Practice
Now try this problem on your own:

**Problem**: [Independent problem]

**Your Solution**:
[Space for student work]
{{/if}}

## Part 3: Critical Thinking (25 points)

### Scenario Analysis
Read the following scenario and answer the questions:

**Scenario**: [Real-world scenario involving {{topic}}]

**Questions**:
1. {{difficulty_language "How does {{topic}} apply to this situation?" pedagogical.difficulty_level}}
   ________________________________________________
   ________________________________________________

2. What would happen if [variable] was changed?
   ________________________________________________
   ________________________________________________

3. {{difficulty_language "Propose an alternative solution using the principles of {{topic}}." pedagogical.difficulty_level}}
   ________________________________________________
   ________________________________________________

## Part 4: Reflection and Assessment (25 points)

### Self-Assessment
Rate your understanding of today's concepts (1 = need help, 5 = confident):

{{#each learning_objectives}}
- {{this}}: 1  2  3  4  5
{{/each}}

### Reflection Questions
1. What was the most important thing you learned about {{topic}} today?
   ________________________________________________
   ________________________________________________

2. What questions do you still have about {{topic}}?
   ________________________________________________
   ________________________________________________

3. How can you apply what you learned about {{topic}} outside of class?
   ________________________________________________
   ________________________________________________

## Bonus Challenge (5 extra points)
{{difficulty_language "Design your own problem related to {{topic}} and solve it." pedagogical.difficulty_level}}

**Your Problem**: ________________________________
________________________________________________

**Your Solution**: _______________________________
________________________________________________

---

## Answer Key (For Instructor Use)
[Include detailed answer key with explanations]

## Accessibility Notes
{{#each content_meta.accessibility_features}}
- {{accessibility this}}
{{/each}}

**Total Points**: _____ / 100

**Teacher Comments**:
________________________________________________
________________________________________________"#.to_string(),
        required_variables: vec!["topic".to_string(), "learning_objectives".to_string()],
        optional_variables: vec!["audience".to_string()],
        pedagogical_approach: PedagogicalApproach::ScaffoldedLearning,
        difficulty_level: DifficultyLevel::Mixed,
        language: "en".to_string(),
        version: "1.0.0".to_string(),
    }
}

fn create_quiz_template() -> PromptTemplate {
    PromptTemplate {
        id: "assessment_quiz".to_string(),
        name: "Assessment Quiz".to_string(),
        description: "Comprehensive quiz for evaluating student understanding".to_string(),
        content_type: ContentType::Quiz,
        template_content: r#"# {{topic}} - Assessment Quiz

**Name**: _________________________ **Date**: _____________
**Time Limit**: {{time_format pedagogical.time_allocation.assessment_percent 0.01 pedagogical.time_allocation.total_duration_minutes}} minutes

## Instructions
{{difficulty_language "Read each question carefully and choose the best answer or provide the requested information. Show your work for calculation problems." pedagogical.difficulty_level}}

## Part 1: Multiple Choice (40 points)
*Choose the best answer for each question. Mark your answer clearly.*

{{assessment_questions topic 8}}

1. Which of the following best describes {{topic}}?
   a) [Option A]
   b) [Option B]
   c) [Option C]
   d) [Option D]

2. The primary purpose of {{topic}} is to:
   a) [Option A]
   b) [Option B]
   c) [Option C]
   d) [Option D]

3. {{difficulty_language "When applying {{topic}} principles, which factor is most important?" pedagogical.difficulty_level}}
   a) [Option A]
   b) [Option B]
   c) [Option C]
   d) [Option D]

4. [Additional multiple choice question]
   a) [Option A]
   b) [Option B]
   c) [Option C]
   d) [Option D]

## Part 2: Short Answer (30 points)
*Provide brief but complete answers to the following questions.*

5. {{difficulty_language "Explain the key components of {{topic}} in your own words." pedagogical.difficulty_level}} (10 points)
   ________________________________________________
   ________________________________________________
   ________________________________________________

6. Give two examples of how {{topic}} is used in real-world situations. (10 points)
   
   Example 1: ___________________________________
   ____________________________________________
   
   Example 2: ___________________________________
   ____________________________________________

7. {{difficulty_language "What are the advantages and disadvantages of {{topic}}?" pedagogical.difficulty_level}} (10 points)
   
   Advantages: __________________________________
   ____________________________________________
   
   Disadvantages: _______________________________
   ____________________________________________

## Part 3: Problem Solving (20 points)
*Show all your work for full credit.*

8. [Problem-solving question related to {{topic}}] (20 points)
   
   **Given**: [Problem parameters]
   
   **Find**: [What students need to solve]
   
   **Solution**:
   Step 1: ____________________________________
   
   Step 2: ____________________________________
   
   Step 3: ____________________________________
   
   **Answer**: ________________________________

## Part 4: Critical Thinking (10 points)
*Demonstrate your understanding through analysis and evaluation.*

9. {{difficulty_language "Analyze the following scenario and explain how {{topic}} principles apply:" pedagogical.difficulty_level}} (10 points)
   
   **Scenario**: [Complex scenario requiring analysis]
   
   **Your Analysis**:
   ________________________________________________
   ________________________________________________
   ________________________________________________
   ________________________________________________

## Bonus Question (5 extra points)
{{difficulty_language "Create your own example of {{topic}} and explain why it demonstrates the key concepts we've studied." pedagogical.difficulty_level}}

**Your Example**: _______________________________
________________________________________________

**Explanation**: _______________________________
________________________________________________

---

## Answer Key (For Instructor Use)

### Part 1: Multiple Choice
1. [Correct answer with explanation]
2. [Correct answer with explanation]
3. [Correct answer with explanation]
4. [Correct answer with explanation]

### Part 2: Short Answer
5. [Sample answer with key points]
6. [Sample examples]
7. [Key advantages and disadvantages]

### Part 3: Problem Solving
8. [Step-by-step solution with explanations]

### Part 4: Critical Thinking
9. [Analysis framework and key points to look for]

### Bonus Question
[Sample response and grading criteria]

## Grading Rubric
- **90-100%**: Excellent understanding, clear explanations, minimal errors
- **80-89%**: Good understanding, mostly clear explanations, few errors
- **70-79%**: Satisfactory understanding, adequate explanations, some errors
- **60-69%**: Basic understanding, unclear explanations, several errors
- **Below 60%**: Insufficient understanding, needs review

## Accessibility Accommodations
{{#each content_meta.accessibility_features}}
- {{accessibility this}}
{{/each}}

**Total Points**: _____ / 100 (+ _____ bonus)

**Grade**: _______ **Comments**: ___________________
________________________________________________"#.to_string(),
        required_variables: vec!["topic".to_string()],
        optional_variables: vec!["learning_objectives".to_string()],
        pedagogical_approach: PedagogicalApproach::BloomsRevised,
        difficulty_level: DifficultyLevel::Mixed,
        language: "en".to_string(),
        version: "1.0.0".to_string(),
    }
}

fn create_activity_guide_template() -> PromptTemplate {
    PromptTemplate {
        id: "interactive_activity".to_string(),
        name: "Interactive Learning Activity".to_string(),
        description: "Hands-on activity guide for active learning".to_string(),
        content_type: ContentType::ActivityGuide,
        template_content: r#"# {{topic}} - Interactive Learning Activity

## Activity Overview
**Title**: [Creative activity name related to {{topic}}]
**Duration**: {{time_format pedagogical.time_allocation.practice_percent 0.01 pedagogical.time_allocation.total_duration_minutes}} minutes
**Group Size**: [Recommended group size]
**Difficulty Level**: {{pedagogical.difficulty_level}}

## Learning Objectives
By completing this activity, students will be able to:
{{#each learning_objectives}}
{{format_objectives this}}
{{/each}}

## Materials Needed
### Per Group:
- [List materials needed]
- [Technology requirements]
- [Handouts or worksheets]

### For Instructor:
- Timer
- [Additional instructor materials]

## Activity Instructions

### Setup (5 minutes)
1. {{difficulty_language "Divide students into groups of [number]" pedagogical.difficulty_level}}
2. Distribute materials to each group
3. Review safety guidelines (if applicable)
4. Explain the connection to {{topic}}

### Phase 1: Exploration ({{multiply pedagogical.time_allocation.practice_percent 0.3 0.01 pedagogical.time_allocation.total_duration_minutes}} minutes)
**Objective**: {{difficulty_language "Students explore the basic concepts of {{topic}} through hands-on investigation" pedagogical.difficulty_level}}

**Instructions for Students**:
1. [Step-by-step exploration instructions]
2. [Observation prompts]
3. [Initial questions to consider]

**Instructor Role**:
- Circulate among groups
- Ask guiding questions
- Provide hints if groups are stuck

### Phase 2: Investigation ({{multiply pedagogical.time_allocation.practice_percent 0.4 0.01 pedagogical.time_allocation.total_duration_minutes}} minutes)
**Objective**: Deepen understanding through systematic investigation

**Task**: [Specific investigation task related to {{topic}}]

**Student Instructions**:
1. [Detailed investigation steps]
2. [Data collection requirements]
3. [Analysis questions]

**Guiding Questions**:
{{assessment_questions topic 4}}

### Phase 3: Application ({{multiply pedagogical.time_allocation.practice_percent 0.3 0.01 pedagogical.time_allocation.total_duration_minutes}} minutes)
**Objective**: Apply {{topic}} principles to solve a real-world problem

**Challenge**: [Real-world challenge that requires {{topic}} knowledge]

**Requirements**:
- [Specific deliverables]
- [Success criteria]
- [Time constraints]

## Assessment and Reflection

### Formative Assessment
**Observation Checklist** (for instructor use):
- [ ] Students demonstrate understanding of key {{topic}} concepts
- [ ] Groups collaborate effectively
- [ ] Students apply {{topic}} principles correctly
- [ ] Students ask thoughtful questions
- [ ] Students make connections to prior learning

### Student Reflection Questions
1. {{difficulty_language "What did you discover about {{topic}} during this activity?" pedagogical.difficulty_level}}
2. How does this activity connect to what we learned in class?
3. What was the most challenging part of the activity?
4. How could you apply {{topic}} concepts outside of school?
5. What questions do you still have about {{topic}}?

### Group Sharing (Final 10 minutes)
**Gallery Walk**: 
- Groups post their findings
- Students rotate to view other groups' work
- Instructor facilitates whole-class discussion

**Discussion Questions**:
- What similarities did you notice across groups?
- What different approaches did groups take?
- How do the results connect to our {{topic}} learning objectives?

## Differentiation Strategies

### For Advanced Learners:
- [Extension challenges]
- [Additional complexity]
- [Leadership opportunities]

### For Struggling Learners:
- [Additional scaffolding]
- [Simplified tasks]
- [Peer support strategies]

### For English Language Learners:
- [Visual supports]
- [Vocabulary supports]
- [Collaborative structures]

## Technology Integration
{{#if content_meta.multimedia_suggestions}}
### Digital Tools:
- [Relevant apps or software]
- [Online simulations]
- [Data collection tools]
- [Presentation platforms]

### Digital Citizenship:
- [Appropriate use guidelines]
- [Data privacy considerations]
{{/if}}

## Safety Considerations
- [Safety guidelines if applicable]
- [Emergency procedures]
- [Material handling instructions]

## Accessibility Modifications
{{#each content_meta.accessibility_features}}
- {{accessibility this}}
{{/each}}

## Extensions and Follow-up

### Homework Connections:
- [Related homework assignments]
- [Research opportunities]
- [Real-world observations]

### Cross-Curricular Connections:
- [Math connections]
- [Science connections]
- [Social studies connections]
- [Language arts connections]

### Community Connections:
- [Local expert speakers]
- [Field trip opportunities]
- [Service learning projects]

## Assessment Rubric

### Collaboration (25%)
- **Excellent (4)**: Consistently contributes, listens actively, supports others
- **Proficient (3)**: Usually contributes, generally listens, mostly supportive
- **Developing (2)**: Sometimes contributes, occasionally listens, limited support
- **Beginning (1)**: Rarely contributes, seldom listens, little support

### Understanding of {{topic}} (50%)
- **Excellent (4)**: Demonstrates deep understanding, makes connections, applies concepts
- **Proficient (3)**: Shows good understanding, makes some connections, applies most concepts
- **Developing (2)**: Basic understanding, few connections, applies some concepts
- **Beginning (1)**: Limited understanding, no connections, difficulty applying concepts

### Communication (25%)
- **Excellent (4)**: Clear explanations, uses {{topic}} vocabulary correctly, asks thoughtful questions
- **Proficient (3)**: Generally clear, uses most vocabulary correctly, asks relevant questions
- **Developing (2)**: Sometimes clear, uses some vocabulary correctly, asks basic questions
- **Beginning (1)**: Unclear explanations, limited vocabulary use, few questions

## Instructor Notes
- [Preparation tips]
- [Common misconceptions to address]
- [Timing adjustments]
- [Material substitutions]

**Estimated Prep Time**: [Time needed for setup]
**Clean-up Time**: [Time needed for clean-up]

## Resources and References
- [Related textbook sections]
- [Online resources]
- [Additional materials]"#.to_string(),
        required_variables: vec!["topic".to_string(), "learning_objectives".to_string()],
        optional_variables: vec!["duration".to_string(), "audience".to_string()],
        pedagogical_approach: PedagogicalApproach::ExperientialLearning,
        difficulty_level: DifficultyLevel::Mixed,
        language: "en".to_string(),
        version: "1.0.0".to_string(),
    }
}