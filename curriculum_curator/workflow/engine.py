import asyncio
import uuid
from datetime import datetime
from pathlib import Path
import structlog

logger = structlog.get_logger()


class WorkflowError(Exception):
    """Exception raised for errors in workflow execution."""
    pass


class WorkflowStep:
    """Base class for workflow steps."""
    
    def __init__(self, name, config):
        """Initialize a workflow step.
        
        Args:
            name (str): Name of the step
            config (dict): Step configuration
        """
        self.name = name
        self.config = config
    
    async def execute(self, context, prompt_registry, llm_manager, content_transformer, validation_manager):
        """Execute this workflow step.
        
        Args:
            context (dict): Workflow context
            prompt_registry: PromptRegistry instance
            llm_manager: LLMManager instance
            content_transformer: ContentTransformer instance
            validation_manager: ValidationManager instance
            
        Returns:
            Any: Result of the step execution
        """
        raise NotImplementedError("Subclasses must implement execute()")


class PromptStep(WorkflowStep):
    """A workflow step that uses an LLM to generate content from a prompt."""
    
    async def execute(self, context, prompt_registry, llm_manager, content_transformer, validation_manager):
        """Execute a prompt-based step.
        
        Args:
            context (dict): Workflow context
            prompt_registry: PromptRegistry instance
            llm_manager: LLMManager instance
            content_transformer: ContentTransformer instance
            validation_manager: ValidationManager instance
            
        Returns:
            str: The transformed content
        """
        # Get prompt
        prompt_path = self.config.get("prompt")
        if not prompt_path:
            raise WorkflowError(f"Missing prompt path for step {self.name}")
        
        try:
            prompt_data = prompt_registry.get_prompt(prompt_path)
        except FileNotFoundError as e:
            raise WorkflowError(f"Failed to load prompt: {e}")
        
        # Check required variables
        required_vars = prompt_data["metadata"].get("requires", [])
        missing_vars = [var for var in required_vars if var not in context]
        if missing_vars:
            raise WorkflowError(
                f"Missing required variables for prompt {prompt_path}: {', '.join(missing_vars)}"
            )
        
        # Fill in prompt template
        try:
            prompt_content = prompt_data["content"]
            filled_prompt = prompt_content.format(**context)
        except KeyError as e:
            raise WorkflowError(f"Error formatting prompt: {e}")
        
        # Get LLM response
        model_alias = self.config.get("llm_model_alias")
        try:
            response = await llm_manager.generate(filled_prompt, model_alias)
        except Exception as e:
            raise WorkflowError(f"LLM generation failed: {e}")
        
        # Transform content if requested
        output_format = self.config.get("output_format", "raw")
        transformation_rules = self.config.get("transformation_rules", {})
        
        try:
            transformed_content = content_transformer.transform(
                response, output_format, transformation_rules
            )
        except Exception as e:
            raise WorkflowError(f"Content transformation failed: {e}")
        
        # Store in context under output_variable
        output_variable = self.config.get("output_variable")
        if output_variable:
            context[output_variable] = transformed_content
        
        # Store usage information in context
        usage_stats = llm_manager.generate_usage_report(
            workflow_id=context.get("workflow_id"),
            step_name=self.name
        )
        
        context.setdefault("usage_stats", {})
        context["usage_stats"][self.name] = usage_stats
        
        return transformed_content


class ValidationStep(WorkflowStep):
    """A workflow step that validates content."""
    
    async def execute(self, context, prompt_registry, llm_manager, content_transformer, validation_manager):
        """Execute a validation step.
        
        Args:
            context (dict): Workflow context
            prompt_registry: PromptRegistry instance
            llm_manager: LLMManager instance
            content_transformer: ContentTransformer instance
            validation_manager: ValidationManager instance
            
        Returns:
            list: Validation issues
        """
        # This is a placeholder implementation
        logger.info("validation_step_placeholder")
        return []


class OutputStep(WorkflowStep):
    """A workflow step that generates output files."""
    
    async def execute(self, context, prompt_registry, llm_manager, content_transformer, validation_manager):
        """Execute an output generation step.
        
        Args:
            context (dict): Workflow context
            prompt_registry: PromptRegistry instance
            llm_manager: LLMManager instance
            content_transformer: ContentTransformer instance
            validation_manager: ValidationManager instance
            
        Returns:
            dict: Output file paths
        """
        # This is a placeholder implementation
        logger.info("output_step_placeholder")
        return {}


class Workflow:
    """Orchestrates the execution of a sequence of workflow steps."""
    
    def __init__(self, config, prompt_registry, llm_manager, content_transformer, validation_manager, persistence_manager):
        """Initialize a workflow.
        
        Args:
            config (dict): Workflow configuration
            prompt_registry: PromptRegistry instance
            llm_manager: LLMManager instance
            content_transformer: ContentTransformer instance
            validation_manager: ValidationManager instance
            persistence_manager: PersistenceManager instance
        """
        self.config = config
        self.prompt_registry = prompt_registry
        self.llm_manager = llm_manager
        self.content_transformer = content_transformer
        self.validation_manager = validation_manager
        self.persistence_manager = persistence_manager
        self.session_dir = None
    
    def _create_step(self, step_config):
        """Create a workflow step from configuration.
        
        Args:
            step_config (dict): Step configuration
            
        Returns:
            WorkflowStep: The created step
        """
        step_type = step_config.get("type", "prompt")
        step_name = step_config.get("name")
        
        if step_type == "prompt":
            return PromptStep(step_name, step_config)
        elif step_type == "validation":
            return ValidationStep(step_name, step_config)
        elif step_type == "output":
            return OutputStep(step_name, step_config)
        else:
            raise WorkflowError(f"Unknown step type: {step_type}")
    
    def _initialize_session(self, session_id=None):
        """Initialize a new session or load an existing one.
        
        Args:
            session_id (str, optional): Session ID to use
            
        Returns:
            str: Session ID
        """
        # Create session directory
        session_id, session_dir = self.persistence_manager.create_session(session_id)
        self.session_dir = session_dir
        return session_id
    
    def _save_session_state(self, context):
        """Save the current session state to disk.
        
        Args:
            context (dict): Workflow context
        """
        if not self.session_dir:
            return
            
        # Save config used
        self.persistence_manager.save_config(context["session_id"], self.config)
            
        # Save session state
        self.persistence_manager.save_session_state(context["session_id"], context)
    
    async def execute(self, workflow_name, initial_context=None, session_id=None):
        """Execute the specified workflow.
        
        Args:
            workflow_name (str): Name of the workflow to execute
            initial_context (dict, optional): Initial context variables
            session_id (str, optional): Session ID to use
            
        Returns:
            dict: Execution results
        """
        # Initialize context
        context = initial_context or {}
        context["workflow_name"] = workflow_name
        context["workflow_id"] = session_id or str(uuid.uuid4())
        context["start_time"] = datetime.now()
        
        # Initialize session
        session_id = self._initialize_session(session_id)
        context["session_id"] = session_id
        
        # Configure LLM manager with workflow context
        self.llm_manager.current_workflow_id = context["workflow_id"]
        
        # Get workflow steps
        step_configs = self.config.get("steps", [])
        if not step_configs:
            raise WorkflowError(f"No steps defined for workflow")
        
        # Execute steps
        results = {}
        try:
            for i, step_config in enumerate(step_configs):
                step = self._create_step(step_config)
                context["current_step"] = step.name
                context["current_step_index"] = i
                
                logger.info(
                    "workflow_step_started",
                    workflow_name=workflow_name,
                    workflow_id=context["workflow_id"],
                    step_name=step.name,
                    step_index=i
                )
                
                self.llm_manager.current_step_name = step.name
                
                try:
                    result = await step.execute(
                        context, 
                        self.prompt_registry,
                        self.llm_manager,
                        self.content_transformer,
                        self.validation_manager
                    )
                    results[step.name] = result
                    
                    logger.info(
                        "workflow_step_completed",
                        workflow_name=workflow_name,
                        workflow_id=context["workflow_id"],
                        step_name=step.name,
                        step_index=i
                    )
                except Exception as e:
                    logger.exception(
                        "workflow_step_failed",
                        workflow_name=workflow_name,
                        workflow_id=context["workflow_id"],
                        step_name=step.name,
                        step_index=i,
                        error=str(e)
                    )
                    context["error"] = str(e)
                    context["failed_step"] = step.name
                    self._save_session_state(context)
                    raise WorkflowError(f"Step {step.name} failed: {e}")
                
                # Save session state after each step
                self._save_session_state(context)
                
        finally:
            context["end_time"] = datetime.now()
            context["duration"] = (context["end_time"] - context["start_time"]).total_seconds()
            
            # Generate final usage report
            context["final_usage_report"] = self.llm_manager.generate_usage_report(
                workflow_id=context["workflow_id"]
            )
            
            # Save final session state
            self._save_session_state(context)
                
        return {
            "results": results,
            "context": context,
            "session_id": session_id
        }
        
    async def resume(self, session_id, from_step=None):
        """Resume a previously interrupted workflow.
        
        Args:
            session_id (str): Session ID of the workflow to resume
            from_step (str, optional): Name of the step to resume from
            
        Returns:
            dict: Execution results
        """
        # Placeholder implementation
        logger.info("resume_workflow_placeholder", 
                   session_id=session_id, 
                   from_step=from_step)
        
        # In a real implementation, we would:
        # 1. Load the session state
        # 2. Determine where to resume from
        # 3. Execute remaining steps
        
        return {
            "results": {},
            "context": {"workflow_id": session_id},
            "session_id": session_id
        }