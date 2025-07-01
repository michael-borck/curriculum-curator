use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use anyhow::Result;
use uuid::Uuid;
use std::time::{SystemTime, Duration};
use crate::content::{ContentRequest, GeneratedContent};

/// Workflow execution engine for step-based content generation
#[derive(Debug)]
pub struct WorkflowEngine {
    workflows: HashMap<Uuid, WorkflowInstance>,
}

/// A workflow instance represents a single execution of a content generation workflow
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowInstance {
    pub id: Uuid,
    pub name: String,
    pub steps: Vec<WorkflowStepInstance>,
    pub current_step: usize,
    pub status: WorkflowStatus,
    pub context: WorkflowContext,
    pub created_at: SystemTime,
    pub updated_at: SystemTime,
    pub estimated_duration: Option<Duration>,
}

/// Individual step instance within a workflow
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowStepInstance {
    pub id: Uuid,
    pub step_type: String,
    pub name: String,
    pub description: String,
    pub status: StepStatus,
    pub input_data: serde_json::Value,
    pub output_data: Option<serde_json::Value>,
    pub error_message: Option<String>,
    pub started_at: Option<SystemTime>,
    pub completed_at: Option<SystemTime>,
    pub estimated_duration: Option<Duration>,
    pub dependencies: Vec<Uuid>, // Step IDs this step depends on
}

/// Workflow execution status
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum WorkflowStatus {
    Created,
    Running,
    Paused,
    Completed,
    Failed,
    Cancelled,
}

/// Individual step execution status
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum StepStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Skipped,
    WaitingForDependencies,
}

/// Workflow context contains shared data between steps
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowContext {
    pub content_request: ContentRequest,
    pub generated_content: Vec<GeneratedContent>,
    pub variables: HashMap<String, serde_json::Value>,
    pub user_inputs: HashMap<String, serde_json::Value>,
    pub metadata: HashMap<String, serde_json::Value>,
}

/// Progress information for the entire workflow
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowProgress {
    pub workflow_id: Uuid,
    pub current_step: usize,
    pub total_steps: usize,
    pub completed_steps: usize,
    pub failed_steps: usize,
    pub skipped_steps: usize,
    pub overall_progress_percent: f32,
    pub current_step_progress_percent: Option<f32>,
    pub estimated_time_remaining: Option<Duration>,
    pub status: WorkflowStatus,
    pub status_message: String,
}

/// Result of workflow step execution
#[derive(Debug, Clone)]
pub struct StepExecutionResult {
    pub status: StepStatus,
    pub output_data: Option<serde_json::Value>,
    pub error_message: Option<String>,
    pub progress_percent: Option<f32>,
    pub status_message: Option<String>,
}

/// Trait that all workflow steps must implement
pub trait WorkflowStep: Send + Sync + std::fmt::Debug {
    /// Execute the step with the given context
    async fn execute(
        &self,
        context: &mut WorkflowContext,
        input_data: &serde_json::Value,
    ) -> Result<StepExecutionResult>;

    /// Get step metadata
    fn get_metadata(&self) -> StepMetadata;

    /// Validate if the step can execute with the given input
    fn validate_input(&self, input_data: &serde_json::Value) -> Result<()>;

    /// Get estimated duration for this step
    fn estimated_duration(&self, input_data: &serde_json::Value) -> Option<Duration>;
}

/// Metadata about a workflow step type
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepMetadata {
    pub step_type: String,
    pub name: String,
    pub description: String,
    pub required_inputs: Vec<String>,
    pub optional_inputs: Vec<String>,
    pub outputs: Vec<String>,
    pub category: StepCategory,
}

/// Categories of workflow steps
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum StepCategory {
    Input,        // User input collection
    Processing,   // Data processing and generation
    Validation,   // Content validation
    Output,       // Result generation
    Integration,  // External system integration
}

impl WorkflowEngine {
    /// Create a new workflow engine
    pub fn new() -> Self {
        Self {
            workflows: HashMap::new(),
        }
    }

    /// Create a new workflow instance
    pub fn create_workflow(
        &mut self,
        name: String,
        content_request: ContentRequest,
        steps: Vec<WorkflowStepDefinition>,
    ) -> Result<Uuid> {
        let workflow_id = Uuid::new_v4();
        let now = SystemTime::now();

        // Convert step definitions to step instances
        let step_instances: Vec<WorkflowStepInstance> = steps
            .into_iter()
            .map(|def| WorkflowStepInstance {
                id: Uuid::new_v4(),
                step_type: def.step_type,
                name: def.name,
                description: def.description,
                status: StepStatus::Pending,
                input_data: def.input_data,
                output_data: None,
                error_message: None,
                started_at: None,
                completed_at: None,
                estimated_duration: def.estimated_duration,
                dependencies: def.dependencies,
            })
            .collect();

        let workflow = WorkflowInstance {
            id: workflow_id,
            name,
            steps: step_instances,
            current_step: 0,
            status: WorkflowStatus::Created,
            context: WorkflowContext {
                content_request,
                generated_content: Vec::new(),
                variables: HashMap::new(),
                user_inputs: HashMap::new(),
                metadata: HashMap::new(),
            },
            created_at: now,
            updated_at: now,
            estimated_duration: None,
        };

        self.workflows.insert(workflow_id, workflow);
        Ok(workflow_id)
    }

    /// Execute a workflow step by step
    pub async fn execute_workflow(&mut self, workflow_id: Uuid) -> Result<WorkflowStatus> {
        // Set initial status
        {
            let workflow = self.workflows.get_mut(&workflow_id)
                .ok_or_else(|| anyhow::anyhow!("Workflow {} not found", workflow_id))?;
            workflow.status = WorkflowStatus::Running;
            workflow.updated_at = SystemTime::now();
        }

        loop {
            // Get current step info
            let (current_step, _total_steps, dependencies_satisfied) = {
                let workflow = self.workflows.get(&workflow_id).unwrap();
                let step_index = workflow.current_step;
                
                if step_index >= workflow.steps.len() {
                    break;
                }
                
                let dependencies_satisfied = self.are_dependencies_satisfied(workflow, step_index)?;
                (step_index, workflow.steps.len(), dependencies_satisfied)
            };

            // Check if all dependencies are satisfied
            if !dependencies_satisfied {
                let workflow = self.workflows.get_mut(&workflow_id).unwrap();
                workflow.steps[current_step].status = StepStatus::WaitingForDependencies;
                break;
            }

            // Execute the current step
            let step_result = self.execute_step(workflow_id, current_step).await?;
            
            // Update workflow based on step result
            let should_continue = {
                let workflow = self.workflows.get_mut(&workflow_id).unwrap();
                match step_result.status {
                    StepStatus::Completed => {
                        workflow.current_step += 1;
                        true
                    }
                    StepStatus::Failed => {
                        workflow.status = WorkflowStatus::Failed;
                        false
                    }
                    _ => false, // Paused or waiting
                }
            };

            if !should_continue {
                break;
            }
        }

        // Update final status
        let final_status = {
            let workflow = self.workflows.get_mut(&workflow_id).unwrap();
            if workflow.current_step >= workflow.steps.len() && workflow.status == WorkflowStatus::Running {
                workflow.status = WorkflowStatus::Completed;
            }
            workflow.updated_at = SystemTime::now();
            workflow.status.clone()
        };

        Ok(final_status)
    }

    /// Execute a single step
    async fn execute_step(&mut self, workflow_id: Uuid, step_index: usize) -> Result<StepExecutionResult> {
        // Get workflow reference first to avoid borrowing issues
        let (step_type, input_data) = {
            let workflow = self.workflows.get(&workflow_id)
                .ok_or_else(|| anyhow::anyhow!("Workflow {} not found", workflow_id))?;

            if step_index >= workflow.steps.len() {
                return Err(anyhow::anyhow!("Step index {} out of bounds", step_index));
            }

            let step_instance = &workflow.steps[step_index];
            (step_instance.step_type.clone(), step_instance.input_data.clone())
        };

        // Update step status
        {
            let workflow = self.workflows.get_mut(&workflow_id).unwrap();
            let step_instance = &mut workflow.steps[step_index];
            step_instance.status = StepStatus::Running;
            step_instance.started_at = Some(SystemTime::now());
        }

        // Execute the step using the concrete executor
        let result = {
            let workflow = self.workflows.get_mut(&workflow_id).unwrap();
            StepExecutor::execute_step(&step_type, &mut workflow.context, &input_data).await
        };

        // Update step based on result
        let workflow = self.workflows.get_mut(&workflow_id).unwrap();
        let step_instance = &mut workflow.steps[step_index];
        
        match result {
            Ok(execution_result) => {
                step_instance.status = execution_result.status.clone();
                step_instance.output_data = execution_result.output_data.clone();
                step_instance.error_message = execution_result.error_message.clone();
                
                if execution_result.status == StepStatus::Completed {
                    step_instance.completed_at = Some(SystemTime::now());
                }

                Ok(execution_result)
            }
            Err(error) => {
                step_instance.status = StepStatus::Failed;
                step_instance.error_message = Some(error.to_string());
                step_instance.completed_at = Some(SystemTime::now());

                Ok(StepExecutionResult {
                    status: StepStatus::Failed,
                    output_data: None,
                    error_message: Some(error.to_string()),
                    progress_percent: None,
                    status_message: None,
                })
            }
        }
    }

    /// Check if all dependencies for a step are satisfied
    fn are_dependencies_satisfied(&self, workflow: &WorkflowInstance, step_index: usize) -> Result<bool> {
        let step = &workflow.steps[step_index];
        
        for dep_id in &step.dependencies {
            let dep_step = workflow.steps.iter()
                .find(|s| s.id == *dep_id)
                .ok_or_else(|| anyhow::anyhow!("Dependency step {} not found", dep_id))?;
            
            if dep_step.status != StepStatus::Completed {
                return Ok(false);
            }
        }
        
        Ok(true)
    }

    /// Get workflow progress information
    pub fn get_progress(&self, workflow_id: Uuid) -> Result<WorkflowProgress> {
        let workflow = self.workflows.get(&workflow_id)
            .ok_or_else(|| anyhow::anyhow!("Workflow {} not found", workflow_id))?;

        let total_steps = workflow.steps.len();
        let completed_steps = workflow.steps.iter()
            .filter(|s| s.status == StepStatus::Completed)
            .count();
        let failed_steps = workflow.steps.iter()
            .filter(|s| s.status == StepStatus::Failed)
            .count();
        let skipped_steps = workflow.steps.iter()
            .filter(|s| s.status == StepStatus::Skipped)
            .count();

        let overall_progress_percent = if total_steps > 0 {
            (completed_steps as f32 / total_steps as f32) * 100.0
        } else {
            0.0
        };

        let status_message = match workflow.status {
            WorkflowStatus::Created => "Workflow created, ready to start".to_string(),
            WorkflowStatus::Running => {
                if workflow.current_step < workflow.steps.len() {
                    format!("Executing step: {}", workflow.steps[workflow.current_step].name)
                } else {
                    "Finalizing workflow".to_string()
                }
            }
            WorkflowStatus::Paused => "Workflow paused".to_string(),
            WorkflowStatus::Completed => "Workflow completed successfully".to_string(),
            WorkflowStatus::Failed => "Workflow failed".to_string(),
            WorkflowStatus::Cancelled => "Workflow cancelled".to_string(),
        };

        Ok(WorkflowProgress {
            workflow_id,
            current_step: workflow.current_step,
            total_steps,
            completed_steps,
            failed_steps,
            skipped_steps,
            overall_progress_percent,
            current_step_progress_percent: None, // Could be updated by individual steps
            estimated_time_remaining: None, // Could be calculated based on step durations
            status: workflow.status.clone(),
            status_message,
        })
    }

    /// Get workflow instance
    pub fn get_workflow(&self, workflow_id: Uuid) -> Option<&WorkflowInstance> {
        self.workflows.get(&workflow_id)
    }

    /// Pause a running workflow
    pub fn pause_workflow(&mut self, workflow_id: Uuid) -> Result<()> {
        let workflow = self.workflows.get_mut(&workflow_id)
            .ok_or_else(|| anyhow::anyhow!("Workflow {} not found", workflow_id))?;

        if workflow.status == WorkflowStatus::Running {
            workflow.status = WorkflowStatus::Paused;
            workflow.updated_at = SystemTime::now();
        }

        Ok(())
    }

    /// Resume a paused workflow
    pub async fn resume_workflow(&mut self, workflow_id: Uuid) -> Result<WorkflowStatus> {
        let workflow = self.workflows.get_mut(&workflow_id)
            .ok_or_else(|| anyhow::anyhow!("Workflow {} not found", workflow_id))?;

        if workflow.status == WorkflowStatus::Paused {
            self.execute_workflow(workflow_id).await
        } else {
            Ok(workflow.status.clone())
        }
    }

    /// Cancel a workflow
    pub fn cancel_workflow(&mut self, workflow_id: Uuid) -> Result<()> {
        let workflow = self.workflows.get_mut(&workflow_id)
            .ok_or_else(|| anyhow::anyhow!("Workflow {} not found", workflow_id))?;

        workflow.status = WorkflowStatus::Cancelled;
        workflow.updated_at = SystemTime::now();

        Ok(())
    }

    /// List all workflows
    pub fn list_workflows(&self) -> Vec<&WorkflowInstance> {
        self.workflows.values().collect()
    }

    /// Get available step types
    pub fn get_step_types(&self) -> Vec<StepMetadata> {
        StepExecutor::get_available_step_types()
    }
}

/// Concrete step executor that handles all step types
pub struct StepExecutor;

impl StepExecutor {
    /// Execute a step based on its type
    pub async fn execute_step(
        step_type: &str,
        context: &mut WorkflowContext,
        input_data: &serde_json::Value,
    ) -> Result<StepExecutionResult> {
        use crate::content::workflow_steps::*;
        
        match step_type {
            "input_validation" => {
                let step = InputValidationStep;
                step.execute(context, input_data).await
            }
            "learning_objective_generation" => {
                let step = LearningObjectiveGenerationStep;
                step.execute(context, input_data).await
            }
            "content_generation" => {
                // For now, we'll return an error since we need LLM manager access
                // This should be properly implemented with dependency injection
                Err(anyhow::anyhow!("Content generation step requires LLM manager configuration"))
            }
            "content_validation" => {
                let step = ContentValidationStep;
                step.execute(context, input_data).await
            }
            "output_finalization" => {
                let step = OutputFinalizationStep;
                step.execute(context, input_data).await
            }
            _ => Err(anyhow::anyhow!("Unknown step type: {}", step_type))
        }
    }

    /// Get metadata for all available step types
    pub fn get_available_step_types() -> Vec<StepMetadata> {
        use crate::content::workflow_steps::*;
        
        vec![
            InputValidationStep.get_metadata(),
            LearningObjectiveGenerationStep.get_metadata(),
            ContentGenerationStep::default_metadata(),
            ContentValidationStep.get_metadata(),
            OutputFinalizationStep.get_metadata(),
        ]
    }
}

/// Definition for creating a workflow step
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowStepDefinition {
    pub step_type: String,
    pub name: String,
    pub description: String,
    pub input_data: serde_json::Value,
    pub estimated_duration: Option<Duration>,
    pub dependencies: Vec<Uuid>,
}

impl Default for WorkflowEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl Default for WorkflowContext {
    fn default() -> Self {
        Self {
            content_request: ContentRequest {
                topic: String::new(),
                learning_objectives: Vec::new(),
                duration: String::new(),
                audience: String::new(),
                content_types: Vec::new(),
            },
            generated_content: Vec::new(),
            variables: HashMap::new(),
            user_inputs: HashMap::new(),
            metadata: HashMap::new(),
        }
    }
}