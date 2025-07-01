use serde::{Deserialize, Serialize};
use std::time::Duration;
use std::sync::Arc;
use tokio::sync::Mutex;
use anyhow::Result;
use crate::content::workflow::{
    WorkflowStep, StepExecutionResult, StepMetadata, StepCategory, StepStatus, WorkflowContext
};
use crate::content::{ContentType, GeneratedContent, ContentGenerator};
use crate::content::generator::ContentMetadata;

/// Step that collects and validates user input for content generation
#[derive(Debug)]
pub struct InputValidationStep;

impl WorkflowStep for InputValidationStep {
    async fn execute(
        &self,
        context: &mut WorkflowContext,
        _input_data: &serde_json::Value,
    ) -> Result<StepExecutionResult> {
        // Validate the content request
        let request = &context.content_request;
        
        if request.topic.trim().is_empty() {
            return Ok(StepExecutionResult {
                status: StepStatus::Failed,
                output_data: None,
                error_message: Some("Topic cannot be empty".to_string()),
                progress_percent: Some(0.0),
                status_message: Some("Validation failed".to_string()),
            });
        }

        if request.learning_objectives.is_empty() {
            return Ok(StepExecutionResult {
                status: StepStatus::Failed,
                output_data: None,
                error_message: Some("At least one learning objective is required".to_string()),
                progress_percent: Some(0.0),
                status_message: Some("Validation failed".to_string()),
            });
        }

        if request.content_types.is_empty() {
            return Ok(StepExecutionResult {
                status: StepStatus::Failed,
                output_data: None,
                error_message: Some("At least one content type must be selected".to_string()),
                progress_percent: Some(0.0),
                status_message: Some("Validation failed".to_string()),
            });
        }

        // Store validation results in context
        context.variables.insert("input_validated".to_string(), serde_json::Value::Bool(true));
        context.variables.insert("validation_timestamp".to_string(), 
            serde_json::Value::String(chrono::Utc::now().to_rfc3339()));

        Ok(StepExecutionResult {
            status: StepStatus::Completed,
            output_data: Some(serde_json::json!({
                "validated": true,
                "topic": request.topic,
                "objective_count": request.learning_objectives.len(),
                "content_type_count": request.content_types.len()
            })),
            error_message: None,
            progress_percent: Some(100.0),
            status_message: Some("Input validation completed".to_string()),
        })
    }

    fn get_metadata(&self) -> StepMetadata {
        StepMetadata {
            step_type: "input_validation".to_string(),
            name: "Input Validation".to_string(),
            description: "Validates user input for content generation".to_string(),
            required_inputs: vec!["content_request".to_string()],
            optional_inputs: vec![],
            outputs: vec!["validation_result".to_string()],
            category: StepCategory::Input,
        }
    }

    fn validate_input(&self, _input_data: &serde_json::Value) -> Result<()> {
        // Input validation step doesn't require specific input data
        Ok(())
    }

    fn estimated_duration(&self, _input_data: &serde_json::Value) -> Option<Duration> {
        Some(Duration::from_secs(1)) // Very fast validation
    }
}

/// Step that generates learning objectives if not provided by user
#[derive(Debug)]
pub struct LearningObjectiveGenerationStep;

impl WorkflowStep for LearningObjectiveGenerationStep {
    async fn execute(
        &self,
        context: &mut WorkflowContext,
        _input_data: &serde_json::Value,
    ) -> Result<StepExecutionResult> {
        let topic = &context.content_request.topic;
        let existing_objectives = &context.content_request.learning_objectives;

        // If we already have objectives, skip this step
        if !existing_objectives.is_empty() {
            return Ok(StepExecutionResult {
                status: StepStatus::Skipped,
                output_data: Some(serde_json::json!({
                    "reason": "Learning objectives already provided",
                    "objective_count": existing_objectives.len()
                })),
                error_message: None,
                progress_percent: Some(100.0),
                status_message: Some("Using existing learning objectives".to_string()),
            });
        }

        // Generate learning objectives based on topic
        // In a real implementation, this would use LLM
        let generated_objectives = vec![
            format!("Students will understand the key concepts of {}", topic),
            format!("Students will be able to apply {} principles in practical scenarios", topic),
            format!("Students will analyze and evaluate {} methodologies", topic),
        ];

        // Update context with generated objectives
        context.content_request.learning_objectives = generated_objectives.clone();
        context.variables.insert("objectives_generated".to_string(), serde_json::Value::Bool(true));

        Ok(StepExecutionResult {
            status: StepStatus::Completed,
            output_data: Some(serde_json::json!({
                "generated_objectives": generated_objectives,
                "count": generated_objectives.len()
            })),
            error_message: None,
            progress_percent: Some(100.0),
            status_message: Some("Learning objectives generated".to_string()),
        })
    }

    fn get_metadata(&self) -> StepMetadata {
        StepMetadata {
            step_type: "learning_objective_generation".to_string(),
            name: "Learning Objective Generation".to_string(),
            description: "Generates learning objectives if not provided by user".to_string(),
            required_inputs: vec!["topic".to_string()],
            optional_inputs: vec!["existing_objectives".to_string()],
            outputs: vec!["generated_objectives".to_string()],
            category: StepCategory::Processing,
        }
    }

    fn validate_input(&self, input_data: &serde_json::Value) -> Result<()> {
        if !input_data.get("topic").and_then(|v| v.as_str()).map_or(false, |s| !s.is_empty()) {
            return Err(anyhow::anyhow!("Topic is required for learning objective generation"));
        }
        Ok(())
    }

    fn estimated_duration(&self, _input_data: &serde_json::Value) -> Option<Duration> {
        Some(Duration::from_secs(10)) // LLM generation time
    }
}

/// Step that generates content for each requested content type
#[derive(Debug)]
pub struct ContentGenerationStep {
    llm_manager: Arc<Mutex<crate::llm::LLMManager>>,
}

impl ContentGenerationStep {
    pub fn new(llm_manager: Arc<Mutex<crate::llm::LLMManager>>) -> Self {
        Self { llm_manager }
    }
    
    pub fn default_metadata() -> StepMetadata {
        StepMetadata {
            step_type: "ContentGeneration".to_string(),
            name: "Content Generation".to_string(),
            description: "Generate slides, worksheets, and other educational materials".to_string(),
            category: StepCategory::Processing,
            required_inputs: vec![
                "learning_objectives".to_string(),
                "topic".to_string(),
                "audience".to_string(),
            ],
            optional_inputs: vec![
                "content_types".to_string(),
                "duration".to_string(),
            ],
            outputs: vec![
                "slides".to_string(),
                "worksheet".to_string(),
                "instructor_notes".to_string(),
            ],
        }
    }
}

impl WorkflowStep for ContentGenerationStep {
    async fn execute(
        &self,
        context: &mut WorkflowContext,
        _input_data: &serde_json::Value,
    ) -> Result<StepExecutionResult> {
        let request = &context.content_request;
        let mut generated_content = Vec::new();

        // Generate content for each requested type
        for content_type in &request.content_types {
            let content = self.generate_content_for_type(request, content_type).await?;
            generated_content.push(content);
        }

        // Store generated content in context
        context.generated_content = generated_content.clone();
        context.variables.insert("content_generated".to_string(), serde_json::Value::Bool(true));
        context.variables.insert("generation_timestamp".to_string(), 
            serde_json::Value::String(chrono::Utc::now().to_rfc3339()));

        Ok(StepExecutionResult {
            status: StepStatus::Completed,
            output_data: Some(serde_json::json!({
                "generated_content_count": generated_content.len(),
                "content_types": request.content_types
            })),
            error_message: None,
            progress_percent: Some(100.0),
            status_message: Some("Content generation completed".to_string()),
        })
    }

    fn get_metadata(&self) -> StepMetadata {
        StepMetadata {
            step_type: "content_generation".to_string(),
            name: "Content Generation".to_string(),
            description: "Generates educational content for requested types".to_string(),
            required_inputs: vec!["content_request".to_string()],
            optional_inputs: vec!["template_preferences".to_string()],
            outputs: vec!["generated_content".to_string()],
            category: StepCategory::Processing,
        }
    }

    fn validate_input(&self, input_data: &serde_json::Value) -> Result<()> {
        // Validate that we have content types to generate
        if !input_data.get("content_types").and_then(|v| v.as_array()).map_or(false, |arr| !arr.is_empty()) {
            return Err(anyhow::anyhow!("At least one content type is required"));
        }
        Ok(())
    }

    fn estimated_duration(&self, input_data: &serde_json::Value) -> Option<Duration> {
        let content_type_count = input_data.get("content_types")
            .and_then(|v| v.as_array())
            .map(|arr| arr.len())
            .unwrap_or(1);
        
        // Estimate 30 seconds per content type
        Some(Duration::from_secs(30 * content_type_count as u64))
    }
}

impl ContentGenerationStep {
    async fn generate_content_for_type(
        &self,
        request: &crate::content::ContentRequest,
        content_type: &ContentType,
    ) -> Result<GeneratedContent> {
        // Use the real content generator with LLM
        let generator = ContentGenerator::new(self.llm_manager.clone());
        let temp_request = crate::content::ContentRequest {
            topic: request.topic.clone(),
            learning_objectives: request.learning_objectives.clone(),
            duration: request.duration.clone(),
            audience: request.audience.clone(),
            content_types: vec![content_type.clone()],
        };
        
        let mut results = generator.generate(&temp_request).await?;
        results.pop().ok_or_else(|| anyhow::anyhow!("Failed to generate content"))
    }
    
    async fn generate_mock_content(
        &self,
        request: &crate::content::ContentRequest,
        content_type: &ContentType,
    ) -> Result<GeneratedContent> {
        // Fallback mock implementation
        let content = match content_type {
            ContentType::Slides => {
                format!("# {}\n\n## Learning Objectives\n{}\n\n## Content Slides\n- Slide 1: Introduction\n- Slide 2: Main Concepts\n- Slide 3: Examples\n- Slide 4: Summary", 
                    request.topic, 
                    request.learning_objectives.join("\n- "))
            },
            ContentType::InstructorNotes => {
                format!("# Instructor Notes for {}\n\n## Preparation\n- Review learning objectives\n- Prepare examples\n\n## Teaching Tips\n- Start with overview\n- Use interactive examples\n- Check understanding frequently\n\n## Learning Objectives\n{}", 
                    request.topic, 
                    request.learning_objectives.join("\n- "))
            },
            ContentType::Worksheet => {
                format!("# {} Worksheet\n\n## Instructions\nComplete the following exercises to reinforce your understanding of {}.\n\n## Exercises\n1. Define key terms\n2. Apply concepts to scenarios\n3. Analyze case studies\n\n## Learning Objectives\n{}", 
                    request.topic, 
                    request.topic,
                    request.learning_objectives.join("\n- "))
            },
            ContentType::Quiz => {
                format!("# {} Quiz\n\n## Multiple Choice Questions\n1. Which of the following best describes {}?\na) Option A\nb) Option B\nc) Option C\nd) Option D\n\n2. What is the main purpose of {}?\na) Option A\nb) Option B\nc) Option C\nd) Option D", 
                    request.topic, 
                    request.topic,
                    request.topic)
            },
            ContentType::ActivityGuide => {
                format!("# {} Activity Guide\n\n## Activity Overview\nThis activity helps students practice {} concepts through hands-on exercises.\n\n## Materials Needed\n- Worksheets\n- Examples\n- Timer\n\n## Instructions\n1. Divide into groups\n2. Assign roles\n3. Complete activities\n4. Discuss results\n\n## Learning Objectives\n{}", 
                    request.topic, 
                    request.topic,
                    request.learning_objectives.join("\n- "))
            },
        };

        let word_count = content.split_whitespace().count();
        
        Ok(GeneratedContent {
            content_type: content_type.clone(),
            title: format!("{} - {}", request.topic, content_type),
            content,
            metadata: ContentMetadata {
                word_count,
                estimated_duration: request.duration.clone(),
                difficulty_level: "Intermediate".to_string(),
            },
        })
    }
}

/// Step that validates generated content quality
#[derive(Debug)]
pub struct ContentValidationStep;

impl WorkflowStep for ContentValidationStep {
    async fn execute(
        &self,
        context: &mut WorkflowContext,
        _input_data: &serde_json::Value,
    ) -> Result<StepExecutionResult> {
        let mut validation_results = Vec::new();
        let mut all_valid = true;

        // Validate each piece of generated content
        for content in &context.generated_content {
            let validation = self.validate_content(content);
            if !validation.is_valid {
                all_valid = false;
            }
            validation_results.push(validation);
        }

        context.variables.insert("content_validated".to_string(), serde_json::Value::Bool(all_valid));
        context.variables.insert("validation_results".to_string(), 
            serde_json::to_value(&validation_results)?);

        let status = if all_valid { StepStatus::Completed } else { StepStatus::Failed };
        let status_message = if all_valid {
            "All content passed validation".to_string()
        } else {
            "Some content failed validation".to_string()
        };

        Ok(StepExecutionResult {
            status,
            output_data: Some(serde_json::json!({
                "validation_results": validation_results,
                "all_valid": all_valid,
                "content_count": context.generated_content.len()
            })),
            error_message: None,
            progress_percent: Some(100.0),
            status_message: Some(status_message),
        })
    }

    fn get_metadata(&self) -> StepMetadata {
        StepMetadata {
            step_type: "content_validation".to_string(),
            name: "Content Validation".to_string(),
            description: "Validates quality and completeness of generated content".to_string(),
            required_inputs: vec!["generated_content".to_string()],
            optional_inputs: vec!["validation_criteria".to_string()],
            outputs: vec!["validation_results".to_string()],
            category: StepCategory::Validation,
        }
    }

    fn validate_input(&self, input_data: &serde_json::Value) -> Result<()> {
        if !input_data.get("generated_content").and_then(|v| v.as_array()).map_or(false, |arr| !arr.is_empty()) {
            return Err(anyhow::anyhow!("Generated content is required for validation"));
        }
        Ok(())
    }

    fn estimated_duration(&self, input_data: &serde_json::Value) -> Option<Duration> {
        let content_count = input_data.get("generated_content")
            .and_then(|v| v.as_array())
            .map(|arr| arr.len())
            .unwrap_or(1);
        
        // Estimate 5 seconds per content piece
        Some(Duration::from_secs(5 * content_count as u64))
    }
}

impl ContentValidationStep {
    fn validate_content(&self, content: &GeneratedContent) -> ContentValidationResult {
        let mut issues = Vec::new();
        let mut is_valid = true;

        // Check minimum content length
        if content.content.len() < 100 {
            issues.push("Content is too short".to_string());
            is_valid = false;
        }

        // Check if content contains the title topic
        if !content.content.to_lowercase().contains(&content.title.to_lowercase()) {
            issues.push("Content should reference the topic".to_string());
            is_valid = false;
        }

        // Check word count accuracy
        let actual_word_count = content.content.split_whitespace().count();
        if (actual_word_count as i32 - content.metadata.word_count as i32).abs() > 10 {
            issues.push("Word count metadata is inaccurate".to_string());
            // This is not a blocking issue
        }

        ContentValidationResult {
            content_type: content.content_type.clone(),
            is_valid,
            issues,
            word_count: actual_word_count,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentValidationResult {
    pub content_type: ContentType,
    pub is_valid: bool,
    pub issues: Vec<String>,
    pub word_count: usize,
}

/// Step that finalizes the workflow and prepares output
#[derive(Debug)]
pub struct OutputFinalizationStep;

impl WorkflowStep for OutputFinalizationStep {
    async fn execute(
        &self,
        context: &mut WorkflowContext,
        _input_data: &serde_json::Value,
    ) -> Result<StepExecutionResult> {
        // Prepare final output summary
        let summary = WorkflowSummary {
            topic: context.content_request.topic.clone(),
            content_count: context.generated_content.len(),
            content_types: context.content_request.content_types.clone(),
            total_word_count: context.generated_content.iter()
                .map(|c| c.metadata.word_count)
                .sum(),
            completion_timestamp: chrono::Utc::now().to_rfc3339(),
        };

        context.variables.insert("workflow_summary".to_string(), 
            serde_json::to_value(&summary)?);

        Ok(StepExecutionResult {
            status: StepStatus::Completed,
            output_data: Some(serde_json::json!(summary)),
            error_message: None,
            progress_percent: Some(100.0),
            status_message: Some("Workflow completed successfully".to_string()),
        })
    }

    fn get_metadata(&self) -> StepMetadata {
        StepMetadata {
            step_type: "output_finalization".to_string(),
            name: "Output Finalization".to_string(),
            description: "Finalizes workflow output and creates summary".to_string(),
            required_inputs: vec!["generated_content".to_string()],
            optional_inputs: vec![],
            outputs: vec!["workflow_summary".to_string()],
            category: StepCategory::Output,
        }
    }

    fn validate_input(&self, _input_data: &serde_json::Value) -> Result<()> {
        Ok(())
    }

    fn estimated_duration(&self, _input_data: &serde_json::Value) -> Option<Duration> {
        Some(Duration::from_secs(2)) // Quick finalization
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowSummary {
    pub topic: String,
    pub content_count: usize,
    pub content_types: Vec<ContentType>,
    pub total_word_count: usize,
    pub completion_timestamp: String,
}