"""Workflow builder for creating and editing workflow configurations."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import structlog
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from curriculum_curator.config.models import AppConfig
from curriculum_curator.workflow.models import WorkflowConfig
from curriculum_curator.prompt.registry import PromptRegistry
from curriculum_curator.validation.validators import VALIDATOR_REGISTRY
from curriculum_curator.remediation.remediators import REMEDIATOR_REGISTRY

logger = structlog.get_logger()


class WorkflowBuilder:
    """Interactive builder for creating and editing workflow configurations."""
    
    def __init__(self, config: Optional[Union[dict, AppConfig]] = None):
        """Initialize the workflow builder.
        
        Args:
            config: Optional configuration (either dict or AppConfig)
        """
        self.console = Console()
        
        # Initialize config
        if config:
            if not isinstance(config, AppConfig):
                self.config = AppConfig.model_validate(config)
            else:
                self.config = config
        else:
            self.config = None
            
        # Initialize workflow template
        self.workflow = {
            "name": "",
            "description": "",
            "defaults": {},
            "steps": []
        }
        
        # Get available components
        self.available_prompts = []
        self.available_validators = list(name for name, cls in VALIDATOR_REGISTRY.items() if cls is not None)
        self.available_remediators = list(name for name, cls in REMEDIATOR_REGISTRY.items() if cls is not None)
        
        # Setup prompt registry if config provided
        if self.config and hasattr(self.config, 'prompt_path'):
            prompt_path = self.config.prompt_path
            if prompt_path:
                self.prompt_registry = PromptRegistry(prompt_path)
                self.available_prompts = self.prompt_registry.list_prompts()
        
    def load_base(self, file_path: Union[str, Path]) -> None:
        """Load an existing workflow as a base.
        
        Args:
            file_path: Path to the workflow configuration file
        """
        path = Path(file_path)
        if not path.exists():
            self.console.print(f"[red]Error: File {path} not found.[/red]")
            return
            
        try:
            with open(path, 'r') as f:
                self.workflow = yaml.safe_load(f)
                
            # Validate the loaded workflow
            WorkflowConfig.model_validate(self.workflow)
            
            self.console.print(f"[green]Loaded workflow '{self.workflow['name']}' as base.[/green]")
        except Exception as e:
            self.console.print(f"[red]Error loading workflow: {str(e)}[/red]")
            # Initialize empty workflow
            self.workflow = {
                "name": "",
                "description": "",
                "defaults": {},
                "steps": []
            }
    
    def run_interactive(self) -> None:
        """Run the interactive workflow builder."""
        self.console.print(Panel("[bold blue]Curriculum Curator - Workflow Builder[/bold blue]", 
                                 subtitle="Interactive workflow configuration"))
        
        # Main menu loop
        while True:
            self._display_current_workflow()
            
            self.console.print("\n[bold]Main Menu:[/bold]")
            self.console.print("1. Set workflow name and description")
            self.console.print("2. Configure default settings")
            self.console.print("3. Add workflow step")
            self.console.print("4. Edit workflow step")
            self.console.print("5. Remove workflow step")
            self.console.print("6. Reorder workflow steps")
            self.console.print("7. Validate workflow")
            self.console.print("8. Save workflow")
            self.console.print("9. Exit")
            
            choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"])
            
            if choice == "1":
                self._set_workflow_metadata()
            elif choice == "2":
                self._configure_defaults()
            elif choice == "3":
                self._add_step()
            elif choice == "4":
                self._edit_step()
            elif choice == "5":
                self._remove_step()
            elif choice == "6":
                self._reorder_steps()
            elif choice == "7":
                self._validate_workflow()
            elif choice == "8":
                if self._validate_workflow():
                    output_path = Prompt.ask("Enter path to save workflow")
                    self.save(Path(output_path))
            elif choice == "9":
                if Confirm.ask("Are you sure you want to exit?"):
                    break
    
    def _display_current_workflow(self) -> None:
        """Display the current workflow configuration."""
        self.console.print("\n[bold]Current Workflow Configuration:[/bold]")
        
        if not self.workflow["name"]:
            self.console.print("[yellow]Workflow name not set[/yellow]")
        else:
            self.console.print(f"Name: [cyan]{self.workflow['name']}[/cyan]")
            
        if not self.workflow["description"]:
            self.console.print("[yellow]Workflow description not set[/yellow]")
        else:
            self.console.print(f"Description: {self.workflow['description']}")
            
        if self.workflow["defaults"]:
            self.console.print("\nDefaults:")
            for key, value in self.workflow["defaults"].items():
                self.console.print(f"  {key}: {value}")
        
        if not self.workflow["steps"]:
            self.console.print("\n[yellow]No steps defined[/yellow]")
        else:
            table = Table(title="Workflow Steps")
            table.add_column("#", style="dim")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Details")
            
            for i, step in enumerate(self.workflow["steps"], 1):
                details = ""
                if step["type"] == "prompt":
                    details = f"Prompt: {step.get('prompt')}, Output: {step.get('output_variable')}"
                elif step["type"] == "validation":
                    details = f"Content: {step.get('content_variable')}, Validators: {', '.join(step.get('validators', []))}"
                elif step["type"] == "remediation":
                    details = f"Content: {step.get('content_variable')}, Issues: {step.get('issues_variable')}"
                elif step["type"] == "output":
                    details = f"Output dir: {step.get('output_dir')}"
                
                table.add_row(str(i), step["name"], step["type"], details)
            
            self.console.print(table)
    
    def _set_workflow_metadata(self) -> None:
        """Set workflow name and description."""
        current_name = self.workflow.get("name", "")
        current_desc = self.workflow.get("description", "")
        
        self.console.print(f"\nCurrent name: [cyan]{current_name or 'Not set'}[/cyan]")
        name = Prompt.ask("Enter workflow name", default=current_name if current_name else None)
        self.workflow["name"] = name
        
        self.console.print(f"\nCurrent description: [cyan]{current_desc or 'Not set'}[/cyan]")
        desc = Prompt.ask("Enter workflow description", default=current_desc if current_desc else None)
        self.workflow["description"] = desc
    
    def _configure_defaults(self) -> None:
        """Configure default settings for workflow steps."""
        self.console.print("\n[bold]Configure Default Settings:[/bold]")
        self.console.print("Current defaults:")
        
        if not self.workflow.get("defaults"):
            self.workflow["defaults"] = {}
            self.console.print("[yellow]No defaults set[/yellow]")
        else:
            for key, value in self.workflow["defaults"].items():
                self.console.print(f"  {key}: {value}")
        
        self.console.print("\n[bold]Available Default Settings:[/bold]")
        self.console.print("1. Set default LLM model alias")
        self.console.print("2. Set default output format")
        self.console.print("3. Remove a default setting")
        self.console.print("4. Return to main menu")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"])
        
        if choice == "1":
            model_alias = Prompt.ask("Enter default LLM model alias")
            self.workflow["defaults"]["llm_model_alias"] = model_alias
        elif choice == "2":
            format_choices = ["raw", "json", "list", "html"]
            for i, fmt in enumerate(format_choices, 1):
                self.console.print(f"{i}. {fmt}")
            fmt_choice = Prompt.ask("Choose output format", choices=["1", "2", "3", "4"])
            self.workflow["defaults"]["output_format"] = format_choices[int(fmt_choice) - 1]
        elif choice == "3":
            if not self.workflow["defaults"]:
                self.console.print("[yellow]No defaults to remove[/yellow]")
                return
                
            options = list(self.workflow["defaults"].keys())
            for i, key in enumerate(options, 1):
                self.console.print(f"{i}. {key}: {self.workflow['defaults'][key]}")
                
            if options:
                remove_choice = Prompt.ask("Choose setting to remove", 
                                          choices=[str(i) for i in range(1, len(options) + 1)])
                key_to_remove = options[int(remove_choice) - 1]
                del self.workflow["defaults"][key_to_remove]
                self.console.print(f"[green]Removed default: {key_to_remove}[/green]")
    
    def _add_step(self) -> None:
        """Add a new step to the workflow."""
        self.console.print("\n[bold]Select Step Type to Add:[/bold]")
        self.console.print("1. Prompt (Generate Content)")
        self.console.print("2. Validation")
        self.console.print("3. Remediation")
        self.console.print("4. Output")
        self.console.print("5. Cancel")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            self._add_prompt_step()
        elif choice == "2":
            self._add_validation_step()
        elif choice == "3":
            self._add_remediation_step()
        elif choice == "4":
            self._add_output_step()
    
    def _add_prompt_step(self) -> None:
        """Add a prompt step to the workflow."""
        step = {"type": "prompt"}
        
        step["name"] = Prompt.ask("Enter step name")
        
        # Show available prompts
        if self.available_prompts:
            self.console.print("\nAvailable prompt templates:")
            for i, prompt in enumerate(self.available_prompts, 1):
                self.console.print(f"{i}. {prompt}")
            
            prompt_choice = Prompt.ask("Choose a prompt (number) or enter custom path")
            if prompt_choice.isdigit() and 1 <= int(prompt_choice) <= len(self.available_prompts):
                step["prompt"] = self.available_prompts[int(prompt_choice) - 1]
            else:
                step["prompt"] = prompt_choice
        else:
            step["prompt"] = Prompt.ask("Enter prompt template path")
        
        step["output_variable"] = Prompt.ask("Enter output variable name")
        
        format_choices = ["raw", "json", "list", "html"]
        self.console.print("\nOutput formats:")
        for i, fmt in enumerate(format_choices, 1):
            self.console.print(f"{i}. {fmt}")
        format_idx = Prompt.ask(
            "Choose output format",
            choices=["1", "2", "3", "4"],
            default="1"
        )
        step["output_format"] = format_choices[int(format_idx) - 1]
        
        # Optional: LLM model alias
        use_model = Confirm.ask("Specify LLM model alias?", default=False)
        if use_model:
            step["llm_model_alias"] = Prompt.ask("Enter LLM model alias")
        
        self.workflow["steps"].append(step)
        self.console.print("[green]Prompt step added successfully![/green]")
    
    def _add_validation_step(self) -> None:
        """Add a validation step to the workflow."""
        step = {"type": "validation"}
        
        step["name"] = Prompt.ask("Enter step name")
        step["content_variable"] = Prompt.ask("Enter content variable to validate")
        step["output_variable"] = Prompt.ask("Enter variable to store validation issues")
        
        # Show available validators
        validators = []
        if self.available_validators:
            while True:
                self.console.print("\nAvailable validators:")
                for i, validator in enumerate(self.available_validators, 1):
                    self.console.print(f"{i}. {validator}")
                
                validator_choice = Prompt.ask(
                    "Choose a validator to add (number) or 'done' to finish",
                    default="done"
                )
                
                if validator_choice.lower() == "done":
                    if not validators:
                        self.console.print("[yellow]Warning: No validators selected. At least one validator is required.[/yellow]")
                        continue
                    break
                    
                if validator_choice.isdigit() and 1 <= int(validator_choice) <= len(self.available_validators):
                    validator = self.available_validators[int(validator_choice) - 1]
                    if validator not in validators:
                        validators.append(validator)
                        self.console.print(f"[green]Added validator: {validator}[/green]")
                    else:
                        self.console.print(f"[yellow]Validator {validator} already added[/yellow]")
                else:
                    self.console.print("[red]Invalid choice. Please enter a number or 'done'.[/red]")
        
        step["validators"] = validators
        
        self.workflow["steps"].append(step)
        self.console.print("[green]Validation step added successfully![/green]")
    
    def _add_remediation_step(self) -> None:
        """Add a remediation step to the workflow."""
        step = {"type": "remediation"}
        
        step["name"] = Prompt.ask("Enter step name")
        step["content_variable"] = Prompt.ask("Enter content variable to remediate")
        step["issues_variable"] = Prompt.ask("Enter variable containing validation issues")
        step["output_variable"] = Prompt.ask("Enter variable to store remediated content")
        
        # Optional: actions variable
        use_actions = Confirm.ask("Store remediation actions in a variable?", default=False)
        if use_actions:
            step["actions_variable"] = Prompt.ask("Enter variable to store remediation actions")
        
        self.workflow["steps"].append(step)
        self.console.print("[green]Remediation step added successfully![/green]")
    
    def _add_output_step(self) -> None:
        """Add an output step to the workflow."""
        step = {"type": "output"}
        
        step["name"] = Prompt.ask("Enter step name")
        step["output_dir"] = Prompt.ask("Enter output directory path")
        
        # Get output mapping
        step["output_mapping"] = {}
        self.console.print("\nDefine output mapping (variable to filename):")
        while True:
            variable = Prompt.ask("Enter variable name (or 'done')")
            if variable.lower() == "done":
                if not step["output_mapping"]:
                    self.console.print("[yellow]Warning: No output mappings defined. At least one is required.[/yellow]")
                    continue
                break
                
            filename = Prompt.ask(f"Enter output filename for '{variable}'")
            step["output_mapping"][variable] = filename
            
        # Optional: formats and format options
        use_formats = Confirm.ask("Specify output formats?", default=False)
        if use_formats:
            step["formats"] = []
            while True:
                format_name = Prompt.ask("Enter format name (or 'done')")
                if format_name.lower() == "done":
                    break
                step["formats"].append(format_name)
        
        self.workflow["steps"].append(step)
        self.console.print("[green]Output step added successfully![/green]")
    
    def _edit_step(self) -> None:
        """Edit an existing workflow step."""
        if not self.workflow["steps"]:
            self.console.print("[yellow]No steps to edit[/yellow]")
            return
            
        self._display_current_workflow()
        
        step_idx = Prompt.ask(
            "Enter step number to edit",
            choices=[str(i) for i in range(1, len(self.workflow["steps"]) + 1)]
        )
        
        idx = int(step_idx) - 1
        step = self.workflow["steps"][idx]
        step_type = step["type"]
        
        # Remove the step and add a new one of the same type
        self.workflow["steps"].pop(idx)
        
        self.console.print(f"\n[bold]Editing step {step_idx}: {step['name']} ({step_type})[/bold]")
        
        if step_type == "prompt":
            self._add_prompt_step()
        elif step_type == "validation":
            self._add_validation_step()
        elif step_type == "remediation":
            self._add_remediation_step()
        elif step_type == "output":
            self._add_output_step()
        
        # Move the edited step back to its original position
        if idx < len(self.workflow["steps"]):
            step = self.workflow["steps"].pop()
            self.workflow["steps"].insert(idx, step)
    
    def _remove_step(self) -> None:
        """Remove a workflow step."""
        if not self.workflow["steps"]:
            self.console.print("[yellow]No steps to remove[/yellow]")
            return
            
        self._display_current_workflow()
        
        step_idx = Prompt.ask(
            "Enter step number to remove",
            choices=[str(i) for i in range(1, len(self.workflow["steps"]) + 1)]
        )
        
        idx = int(step_idx) - 1
        step = self.workflow["steps"][idx]
        
        if Confirm.ask(f"Are you sure you want to remove step {step_idx}: {step['name']}?"):
            self.workflow["steps"].pop(idx)
            self.console.print(f"[green]Removed step {step_idx}: {step['name']}[/green]")
    
    def _reorder_steps(self) -> None:
        """Reorder workflow steps."""
        if not self.workflow["steps"] or len(self.workflow["steps"]) < 2:
            self.console.print("[yellow]Not enough steps to reorder[/yellow]")
            return
            
        self._display_current_workflow()
        
        step_idx = Prompt.ask(
            "Enter step number to move",
            choices=[str(i) for i in range(1, len(self.workflow["steps"]) + 1)]
        )
        
        new_idx = Prompt.ask(
            "Enter new position",
            choices=[str(i) for i in range(1, len(self.workflow["steps"]) + 1)]
        )
        
        idx = int(step_idx) - 1
        new_pos = int(new_idx) - 1
        
        if idx == new_pos:
            return
            
        step = self.workflow["steps"].pop(idx)
        self.workflow["steps"].insert(new_pos, step)
        
        self.console.print(f"[green]Moved step '{step['name']}' to position {new_idx}[/green]")
    
    def _validate_workflow(self) -> bool:
        """Validate the workflow configuration."""
        try:
            # Validate with Pydantic model
            WorkflowConfig.model_validate(self.workflow)
            self.console.print("[green]Workflow validation successful![/green]")
            return True
        except Exception as e:
            self.console.print("[red]Workflow validation failed:[/red]")
            self.console.print(f"[red]{str(e)}[/red]")
            return False
    
    def save(self, file_path: Path) -> None:
        """Save the workflow configuration to a file."""
        if not self._validate_workflow():
            if not Confirm.ask("Workflow validation failed. Save anyway?", default=False):
                return
        
        # Create directory if it doesn't exist
        os.makedirs(file_path.parent, exist_ok=True)
        
        try:
            with open(file_path, 'w') as f:
                yaml.dump(self.workflow, f, default_flow_style=False, sort_keys=False)
            self.console.print(f"[green]Workflow saved to {file_path}[/green]")
        except Exception as e:
            self.console.print(f"[red]Error saving workflow: {str(e)}[/red]")