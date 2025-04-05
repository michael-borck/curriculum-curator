"""Interactive mode for Curriculum Curator."""

import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any

import structlog
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from curriculum_curator.core import CurriculumCurator
from curriculum_curator.workflow.builder import WorkflowBuilder
from curriculum_curator.prompt.editor import edit_prompt
from curriculum_curator.config.utils import load_config

logger = structlog.get_logger()


class InteractiveMode:
    """Interactive mode for Curriculum Curator with a menu-driven interface."""
    
    def __init__(self, config_path: Path = Path("config.yaml")):
        """Initialize the interactive mode.
        
        Args:
            config_path: Path to the configuration file
        """
        self.console = Console()
        self.config_path = config_path
        
        try:
            self.config = load_config(str(config_path))
            self.curator = CurriculumCurator(self.config)
        except FileNotFoundError:
            self.console.print(f"[yellow]Warning: Configuration file not found at {config_path}[/yellow]")
            self.console.print("[yellow]Some features may be limited. You can initialize a project with 'curator init'.[/yellow]")
            self.config = None
            self.curator = None
    
    def run(self):
        """Run the interactive mode with a menu of common operations."""
        self.console.print(Panel("[bold blue]Curriculum Curator Interactive Mode[/bold blue]",
                                subtitle="Menu-driven interface for common operations"))
        
        while True:
            self.console.print("\n[bold]Main Menu:[/bold]")
            self.console.print("1. Run a Workflow")
            self.console.print("2. Build/Edit Workflow")
            self.console.print("3. Edit Prompts")
            self.console.print("4. Initialize Project")
            self.console.print("5. Exit")
            
            choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                self._run_workflow()
            elif choice == "2":
                self._build_workflow()
            elif choice == "3":
                self._edit_prompts()
            elif choice == "4":
                self._initialize_project()
            elif choice == "5":
                break
    
    def _run_workflow(self):
        """Run a workflow interactively."""
        if not self.curator:
            self._load_config_first()
            return
            
        try:
            # Get available workflows
            workflows = []
            
            # Get predefined workflows
            from curriculum_curator.workflow import workflows as workflows_module
            import inspect
            
            for name, value in inspect.getmembers(workflows_module):
                if isinstance(value, dict) and "name" in value and "description" in value:
                    workflows.append((value["name"], value.get("description", "")))
            
            # Get workflows from config
            config_workflows = {}
            if hasattr(self.config, 'workflows'):
                config_workflows = self.config.workflows
            elif isinstance(self.config, dict) and 'workflows' in self.config:
                config_workflows = self.config['workflows']
                
            for name, workflow_config in config_workflows.items():
                description = workflow_config.get("description", "")
                workflows.append((name, description))
            
            if not workflows:
                self.console.print("[yellow]No workflows found.[/yellow]")
                return
            
            # Display available workflows
            self.console.print("\n[bold]Available Workflows:[/bold]")
            for i, (name, description) in enumerate(workflows, 1):
                self.console.print(f"{i}. [cyan]{name}[/cyan]: {description}")
            
            # Select a workflow
            workflow_idx = Prompt.ask(
                "Choose a workflow to run (or 'back' to return)",
                default="back"
            )
            
            if workflow_idx.lower() == "back":
                return
                
            if workflow_idx.isdigit() and 1 <= int(workflow_idx) <= len(workflows):
                workflow_name = workflows[int(workflow_idx) - 1][0]
                
                # Collect variables
                variables = {}
                self.console.print("\n[bold]Enter workflow variables (optional):[/bold]")
                self.console.print("Leave empty to finish entering variables.")
                
                while True:
                    var_name = Prompt.ask("Variable name", default="")
                    if not var_name:
                        break
                        
                    var_value = Prompt.ask(f"Value for {var_name}")
                    variables[var_name] = var_value
                
                # Run the workflow
                self.console.print(f"\n[bold]Running workflow '{workflow_name}'...[/bold]")
                
                # Use session ID?
                use_session = Confirm.ask("Specify a session ID?", default=False)
                session_id = None
                if use_session:
                    session_id = Prompt.ask("Enter session ID")
                
                # Run the workflow
                result = asyncio.run(self.curator.run_workflow(workflow_name, variables, session_id))
                
                # Print results
                self.console.print(f"[green]Workflow completed successfully.[/green]")
                self.console.print(f"Session ID: [bold cyan]{result['session_id']}[/bold cyan]")
                
                output_files = result.get("results", {}).get("output_files", {})
                if output_files:
                    self.console.print("\n[bold]Output files:[/bold]")
                    for format_name, path in output_files.items():
                        self.console.print(f"  {format_name}: {path}")
                
                # Print usage statistics
                usage = result.get("context", {}).get("final_usage_report", {})
                if usage:
                    self.console.print("\n[bold]Token Usage Summary:[/bold]")
                    for model, stats in usage.get("by_model", {}).items():
                        self.console.print(f"  [yellow]{model}[/yellow]:")
                        self.console.print(f"    Requests: {stats['count']}")
                        self.console.print(f"    Input tokens: {stats['input_tokens']}")
                        self.console.print(f"    Output tokens: {stats['output_tokens']}")
                        self.console.print(f"    Cost: ${stats['cost']:.4f}")
                
                    totals = usage.get("totals", {})
                    if totals:
                        self.console.print("\n  [bold]Total:[/bold]")
                        self.console.print(f"    Requests: {totals.get('count', 0)}")
                        self.console.print(f"    Input tokens: {totals.get('input_tokens', 0)}")
                        self.console.print(f"    Output tokens: {totals.get('output_tokens', 0)}")
                        self.console.print(f"    Cost: ${totals.get('cost', 0):.4f}")
            else:
                self.console.print("[red]Invalid choice.[/red]")
        except Exception as e:
            self.console.print(f"[bold red]Error running workflow:[/bold red] {e}")
            logger.exception("interactive_run_workflow_failed", error=str(e))
    
    def _build_workflow(self):
        """Build or edit a workflow interactively."""
        if not self.config:
            self._load_config_first()
            return
            
        try:
            # Get output file
            output_file = Prompt.ask("Enter path to save workflow", default="workflow.yaml")
            
            # Ask about base file
            use_base = Confirm.ask("Start from an existing workflow?", default=False)
            base_file = None
            if use_base:
                base_file = Prompt.ask("Enter path to base workflow")
            
            # Create builder
            builder = WorkflowBuilder(self.config)
            
            if base_file:
                builder.load_base(base_file)
            
            # Run the builder
            builder.run_interactive()
            
        except Exception as e:
            self.console.print(f"[bold red]Error building workflow:[/bold red] {e}")
            logger.exception("interactive_build_workflow_failed", error=str(e))
    
    def _edit_prompts(self):
        """Edit prompts interactively."""
        try:
            # Get prompt path from config
            if self.config and hasattr(self.config, 'prompt_path') and self.config.prompt_path:
                prompt_base_path = Path(self.config.prompt_path)
            else:
                # Default to 'prompts' directory if not specified in config
                prompt_base_path = Path("prompts")
            
            # Ask if user wants to edit a specific prompt
            edit_specific = Confirm.ask("Edit a specific prompt file?", default=False)
            
            prompt_path = None
            if edit_specific:
                prompt_path = Prompt.ask("Enter prompt path (relative to prompt directory)")
            
            # Launch the prompt editor
            edit_prompt(prompt_base_path, prompt_path)
            
        except Exception as e:
            self.console.print(f"[bold red]Error editing prompts:[/bold red] {e}")
            logger.exception("interactive_edit_prompts_failed", error=str(e))
    
    def _initialize_project(self):
        """Initialize a project with example prompts and configuration."""
        try:
            output_dir = Prompt.ask("Enter directory to initialize", default=".")
            
            # Create output directory if it doesn't exist
            if not os.path.exists(output_dir):
                if Confirm.ask(f"Directory {output_dir} does not exist. Create it?", default=True):
                    os.makedirs(output_dir, exist_ok=True)
                else:
                    return
            
            self.console.print(f"[bold]Initializing Curriculum Curator project in {output_dir}...[/bold]")
            
            # TODO: Copy example prompts and configuration
            
            # For now, we'll just create the directory structure and a minimal config
            os.makedirs(os.path.join(output_dir, "prompts"), exist_ok=True)
            os.makedirs(os.path.join(output_dir, "prompts", "course"), exist_ok=True)
            os.makedirs(os.path.join(output_dir, "prompts", "module"), exist_ok=True)
            os.makedirs(os.path.join(output_dir, "prompts", "lecture"), exist_ok=True)
            os.makedirs(os.path.join(output_dir, "prompts", "assessment"), exist_ok=True)
            os.makedirs(os.path.join(output_dir, "output"), exist_ok=True)
            
            # Create a minimal config file
            config_content = """# Curriculum Curator Configuration

# Base paths
prompt_path: prompts/
output_path: output/

# LLM Configuration
llm:
  default:
    type: openai
    model: gpt-4-turbo
    # Uncomment and add your API key if not set in environment
    # api_key: your-api-key-here
    
  default_smart:
    type: anthropic
    model: claude-3-opus-20240229
    # Uncomment and add your API key if not set in environment
    # api_key: your-api-key-here

# Workflow definitions can be added here
workflows:
  # Example:
  # minimal_example:
  #   name: minimal_example
  #   description: Minimal example workflow
  #   steps:
  #     - name: generate_content
  #       type: prompt
  #       prompt: course/overview.txt
  #       output_variable: course_overview
"""
            with open(os.path.join(output_dir, "config.yaml"), "w") as f:
                f.write(config_content)
            
            # Ask if user wants to install default prompt templates
            if Confirm.ask("Install default prompt templates?", default=True):
                prompt_base_path = Path(os.path.join(output_dir, "prompts"))
                edit_prompt(prompt_base_path)
                
                # Select option 3 from the prompt editor menu to install defaults
                self.console.print("\n[bold]Please select option 3 to install default templates.[/bold]")
            
            self.console.print("[green]Project initialized successfully.[/green]")
            self.console.print("\nNext steps:")
            self.console.print("1. Edit config.yaml to configure your LLM providers")
            self.console.print("2. Use 'curator edit-prompt' to create or modify prompts")
            self.console.print("3. Use 'curator build-workflow' to create workflows")
            self.console.print("4. Use 'curator run <workflow>' to run workflows")
            
            # Reload config if we initialized in the current directory
            if output_dir == "." and self.config_path.exists():
                self.config = load_config(str(self.config_path))
                self.curator = CurriculumCurator(self.config)
                
        except Exception as e:
            self.console.print(f"[bold red]Error initializing project:[/bold red] {e}")
            logger.exception("interactive_init_failed", error=str(e))
    
    def _load_config_first(self):
        """Show a message about loading config first."""
        self.console.print("[yellow]Please initialize the project or provide a configuration file first.[/yellow]")
        if Confirm.ask("Initialize the project now?", default=True):
            self._initialize_project()


def run_interactive(config_path: Path = Path("config.yaml")):
    """Run the interactive mode.
    
    Args:
        config_path: Path to the configuration file
    """
    interactive = InteractiveMode(config_path)
    interactive.run()