use tauri::command;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::sync::Arc;
use tokio::sync::Mutex;
use crate::content::{
    WorkflowEngine, WorkflowInstance, WorkflowStatus, WorkflowContext,
    WorkflowStepInstance, StepStatus, ContentRequest,
    InputValidationStep, LearningObjectiveGenerationStep, ContentGenerationStep,
    ContentValidationStep, OutputFinalizationStep, WorkflowStep,
};
use crate::llm::LLMManager;
use crate::state::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct WorkflowError {
    pub message: String,
    pub code: Option<String>,
}

impl From<anyhow::Error> for WorkflowError {
    fn from(error: anyhow::Error) -> Self {
        WorkflowError {
            message: error.to_string(),
            code: None,
        }
    }
}

// Workflow commands
#[command]
pub async fn create_workflow(
    name: String,
    content_request: ContentRequest,
) -> Result<String, WorkflowError> {
    // Create workflow instance
    let workflow_id = Uuid::new_v4();
    let context = WorkflowContext {
        content_request,
        generated_content: Vec::new(),
        variables: std::collections::HashMap::new(),
        user_inputs: std::collections::HashMap::new(),
        metadata: std::collections::HashMap::new(),
    };
    
    // Define workflow steps based on Expert Mode UI
    let steps = vec![
        WorkflowStepInstance {
            id: Uuid::new_v4(),
            step_type: "content_planning".to_string(),
            name: "Content Planning".to_string(),
            description: "Generate learning objectives and content outline".to_string(),
            status: StepStatus::Pending,
            input_data: serde_json::json!({}),
            output_data: None,
            error_message: None,
            started_at: None,
            completed_at: None,
            estimated_duration: Some(std::time::Duration::from_secs(30)),
            dependencies: vec![],
        },
        WorkflowStepInstance {
            id: Uuid::new_v4(),
            step_type: "material_generation".to_string(),
            name: "Material Generation".to_string(),
            description: "Create slides, worksheets, and instructor materials".to_string(),
            status: StepStatus::Pending,
            input_data: serde_json::json!({}),
            output_data: None,
            error_message: None,
            started_at: None,
            completed_at: None,
            estimated_duration: Some(std::time::Duration::from_secs(120)),
            dependencies: vec![],
        },
        WorkflowStepInstance {
            id: Uuid::new_v4(),
            step_type: "assessment_creation".to_string(),
            name: "Assessment Creation".to_string(),
            description: "Build quizzes, rubrics, and answer keys".to_string(),
            status: StepStatus::Pending,
            input_data: serde_json::json!({}),
            output_data: None,
            error_message: None,
            started_at: None,
            completed_at: None,
            estimated_duration: Some(std::time::Duration::from_secs(60)),
            dependencies: vec![],
        },
        WorkflowStepInstance {
            id: Uuid::new_v4(),
            step_type: "quality_review".to_string(),
            name: "Quality Review".to_string(),
            description: "Validate content alignment and quality standards".to_string(),
            status: StepStatus::Pending,
            input_data: serde_json::json!({}),
            output_data: None,
            error_message: None,
            started_at: None,
            completed_at: None,
            estimated_duration: Some(std::time::Duration::from_secs(30)),
            dependencies: vec![],
        },
    ];
    
    let workflow = WorkflowInstance {
        id: workflow_id,
        name,
        steps,
        current_step: 0,
        status: WorkflowStatus::Created,
        context,
        created_at: std::time::SystemTime::now(),
        updated_at: std::time::SystemTime::now(),
        estimated_duration: Some(std::time::Duration::from_secs(240)),
    };
    
    // Store workflow in state (would need to add workflow storage to AppState)
    // For now, just return the ID
    Ok(workflow_id.to_string())
}

#[command]
pub async fn execute_workflow_step(
    workflow_id: String,
    step_index: usize,
    state: tauri::State<'_, AppState>,
) -> Result<serde_json::Value, WorkflowError> {
    let workflow_uuid = Uuid::parse_str(&workflow_id)
        .map_err(|e| WorkflowError {
            message: format!("Invalid workflow ID: {}", e),
            code: Some("INVALID_WORKFLOW_ID".to_string()),
        })?;
    
    // For this example, we'll create a temporary workflow context
    // In a real implementation, this would be retrieved from storage
    let mut context = WorkflowContext {
        content_request: ContentRequest {
            topic: "Sample Topic".to_string(),
            learning_objectives: vec!["Objective 1".to_string()],
            duration: "45 minutes".to_string(),
            audience: "Students".to_string(),
            content_types: vec![crate::content::ContentType::Slides],
        },
        generated_content: Vec::new(),
        variables: std::collections::HashMap::new(),
        user_inputs: std::collections::HashMap::new(),
        metadata: std::collections::HashMap::new(),
    };
    
    let llm_manager = state.llm_manager.clone();
    
    // Execute the appropriate step based on index
    let result = match step_index {
        0 => {
            // Content Planning
            let step = LearningObjectiveGenerationStep;
            step.execute(&mut context, &serde_json::json!({})).await?
        }
        1 => {
            // Material Generation
            let step = ContentGenerationStep::new(llm_manager);
            step.execute(&mut context, &serde_json::json!({})).await?
        }
        2 => {
            // Assessment Creation (use content generation for quizzes)
            context.content_request.content_types = vec![crate::content::ContentType::Quiz];
            let step = ContentGenerationStep::new(llm_manager);
            step.execute(&mut context, &serde_json::json!({})).await?
        }
        3 => {
            // Quality Review
            let step = ContentValidationStep;
            step.execute(&mut context, &serde_json::json!({})).await?
        }
        _ => {
            return Err(WorkflowError {
                message: "Invalid step index".to_string(),
                code: Some("INVALID_STEP_INDEX".to_string()),
            });
        }
    };
    
    Ok(serde_json::json!({
        "workflow_id": workflow_id,
        "step_index": step_index,
        "status": format!("{:?}", result.status),
        "output": result.output_data,
        "error": result.error_message,
        "progress": result.progress_percent,
        "message": result.status_message,
    }))
}

#[command]
pub async fn get_workflow_status(
    workflow_id: String,
) -> Result<serde_json::Value, WorkflowError> {
    let workflow_uuid = Uuid::parse_str(&workflow_id)
        .map_err(|e| WorkflowError {
            message: format!("Invalid workflow ID: {}", e),
            code: Some("INVALID_WORKFLOW_ID".to_string()),
        })?;
    
    // In a real implementation, this would retrieve the workflow from storage
    Ok(serde_json::json!({
        "workflow_id": workflow_id,
        "status": "created",
        "current_step": 0,
        "total_steps": 4,
        "steps": [
            {
                "name": "Content Planning",
                "status": "pending",
                "progress": 0
            },
            {
                "name": "Material Generation",
                "status": "pending",
                "progress": 0
            },
            {
                "name": "Assessment Creation",
                "status": "pending",
                "progress": 0
            },
            {
                "name": "Quality Review",
                "status": "pending",
                "progress": 0
            }
        ]
    }))
}

#[command]
pub async fn execute_quick_action(
    action: String,
    content_request: ContentRequest,
    state: tauri::State<'_, AppState>,
) -> Result<serde_json::Value, WorkflowError> {
    let llm_manager = state.llm_manager.clone();
    let mut context = WorkflowContext {
        content_request: content_request.clone(),
        generated_content: Vec::new(),
        variables: std::collections::HashMap::new(),
        user_inputs: std::collections::HashMap::new(),
        metadata: std::collections::HashMap::new(),
    };
    
    match action.as_str() {
        "slides_only" => {
            // Generate only slides
            context.content_request.content_types = vec![crate::content::ContentType::Slides];
            let step = ContentGenerationStep::new(llm_manager);
            let result = step.execute(&mut context, &serde_json::json!({})).await?;
            
            Ok(serde_json::json!({
                "action": action,
                "status": format!("{:?}", result.status),
                "content": context.generated_content,
                "message": result.status_message,
            }))
        }
        "assessment_suite" => {
            // Generate quiz and rubrics
            context.content_request.content_types = vec![
                crate::content::ContentType::Quiz,
                crate::content::ContentType::ActivityGuide,
            ];
            let step = ContentGenerationStep::new(llm_manager);
            let result = step.execute(&mut context, &serde_json::json!({})).await?;
            
            Ok(serde_json::json!({
                "action": action,
                "status": format!("{:?}", result.status),
                "content": context.generated_content,
                "message": result.status_message,
            }))
        }
        "learning_objectives" => {
            // Generate learning objectives only
            let step = LearningObjectiveGenerationStep;
            let result = step.execute(&mut context, &serde_json::json!({})).await?;
            
            Ok(serde_json::json!({
                "action": action,
                "status": format!("{:?}", result.status),
                "output": result.output_data,
                "message": result.status_message,
            }))
        }
        "complete_package" => {
            // Generate all content types
            let step = ContentGenerationStep::new(llm_manager);
            let result = step.execute(&mut context, &serde_json::json!({})).await?;
            
            Ok(serde_json::json!({
                "action": action,
                "status": format!("{:?}", result.status),
                "content": context.generated_content,
                "message": result.status_message,
            }))
        }
        _ => {
            Err(WorkflowError {
                message: format!("Unknown action: {}", action),
                code: Some("UNKNOWN_ACTION".to_string()),
            })
        }
    }
}