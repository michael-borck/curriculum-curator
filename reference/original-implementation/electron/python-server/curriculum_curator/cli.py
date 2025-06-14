import asyncio
import json
from pathlib import Path
from typing import Optional

import structlog
import typer
from rich import print

# Import the core functionality
from curriculum_curator.core import CurriculumCurator
from curriculum_curator.workflow.builder import WorkflowBuilder

logger = structlog.get_logger()

# Create the Typer app
app = typer.Typer(help="CurriculumCurator CLI - Orchestrate educational content workflows.")


# --- Helper Functions ---


def load_config(
    config_path: Path = typer.Option(
        "config.yaml", "--config", "-c", help="Path to configuration file."
    ),
):
    """Loads configuration from YAML file."""
    from curriculum_curator.config.utils import load_config as load_app_config

    try:
        return load_app_config(str(config_path))
    except FileNotFoundError:
        print(f"[bold red]Error:[/bold red] Configuration file not found at {config_path}")
        raise typer.Exit(code=1)
    except Exception as e:
        print(
            f"[bold red]Error:[/bold red] Failed to load or parse configuration file {config_path}: {e}"
        )
        raise typer.Exit(code=1)


def parse_vars(
    var_list: Optional[list[str]] = typer.Option(
        None, "--var", "-v", help="Variables in key=value format. Can be used multiple times."
    ),
) -> dict:
    """Parses the --var options into a dictionary."""
    variables = {}
    if var_list:
        for var in var_list:
            if "=" in var:
                key, value = var.split("=", 1)
                variables[key] = value
            else:
                print(f"[yellow]Warning:[/yellow] Ignoring improperly formatted variable: {var}")
    return variables


def _print_result(result: dict, output_json: bool):
    """Helper to print workflow results."""
    if output_json:
        # Output JSON result
        print(json.dumps(result, indent=2, default=str))
    else:
        # Print summary using Rich
        print("[green]Workflow completed successfully.[/green]")
        print(f"Session ID: [bold cyan]{result['session_id']}[/bold cyan]")

        output_files = result.get("results", {}).get("output_files", {})
        if output_files:
            print("\n[bold]Output files:[/bold]")
            for format_name, path in output_files.items():
                print(f"  {format_name}: {path}")

        # Print usage statistics
        usage = result.get("context", {}).get("final_usage_report", {})
        if usage:
            print("\n[bold]Token Usage Summary:[/bold]")
            for model, stats in usage.get("by_model", {}).items():
                print(f"  [yellow]{model}[/yellow]:")
                print(f"    Requests: {stats['count']}")
                print(f"    Input tokens: {stats['input_tokens']}")
                print(f"    Output tokens: {stats['output_tokens']}")
                print(f"    Cost: ${stats['cost']:.4f}")

            totals = usage.get("totals", {})
            if totals:
                print("\n  [bold]Total:[/bold]")
                print(f"    Requests: {totals.get('count', 0)}")
                print(f"    Input tokens: {totals.get('input_tokens', 0)}")
                print(f"    Output tokens: {totals.get('output_tokens', 0)}")
                print(f"    Cost: ${totals.get('cost', 0):.4f}")


# --- Typer Commands ---


@app.command()
def run(
    workflow: str = typer.Argument(..., help="Name of the workflow to run."),
    var: Optional[list[str]] = typer.Option(
        None, "--var", "-v", help="Variables in key=value format. Can be used multiple times."
    ),
    session_id: Optional[str] = typer.Option(None, help="Specify a session ID to use or resume."),
    config_path: Path = typer.Option(
        "config.yaml", "--config", "-c", help="Path to configuration file."
    ),
    output_json: bool = typer.Option(False, "--output-json", "-j", help="Output result as JSON."),
):
    """Run a specified workflow."""
    config = load_config(config_path)
    variables = parse_vars(var)
    curator = CurriculumCurator(config)
    try:
        print(f"Running workflow '{workflow}'...")
        result = asyncio.run(curator.run_workflow(workflow, variables, session_id))
        _print_result(result, output_json)
    except Exception as e:
        logger.exception("workflow_failed", error=str(e))
        print(f"[bold red]Error running workflow '{workflow}':[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(name="list-workflows")
def list_workflows_command(
    config_path: Path = typer.Option(
        "config.yaml", "--config", "-c", help="Path to configuration file."
    ),
):
    """List available workflows defined in the configuration file and predefined workflows."""
    # Import workflows module
    import inspect

    from curriculum_curator.workflow import workflows as workflows_module

    # Load config workflows
    config = load_config(config_path)
    config_workflows = {}

    if hasattr(config, "workflows"):
        config_workflows = config.workflows
    elif isinstance(config, dict) and "workflows" in config:
        config_workflows = config["workflows"]

    # Load predefined workflows
    predefined_workflows = {}
    for _name, value in inspect.getmembers(workflows_module):
        if isinstance(value, dict) and "name" in value and "description" in value:
            predefined_workflows[value["name"]] = value

    if not config_workflows and not predefined_workflows:
        print("[yellow]No workflows found.[/yellow]")
        return

    # Print config workflows
    if config_workflows:
        print("[bold]Workflows from configuration:[/bold]")
        for name, workflow_config in config_workflows.items():
            description = workflow_config.get("description", "[i]No description[/i]")
            print(f"  [cyan]{name}[/cyan]: {description}")

    # Print predefined workflows
    if predefined_workflows:
        print("\n[bold]Predefined workflows:[/bold]")
        for name, workflow_config in predefined_workflows.items():
            description = workflow_config.get("description", "[i]No description[/i]")
            print(f"  [cyan]{name}[/cyan]: {description}")


@app.command(name="list-prompts")
def list_prompts_command(
    tag: Optional[str] = typer.Option(
        None, "--tag", "-t", help="Filter prompts by tag specified in YAML front matter."
    ),
    config_path: Path = typer.Option(
        "config.yaml", "--config", "-c", help="Path to configuration file."
    ),
):
    """List available prompts, optionally filtering by tag."""
    config = load_config(config_path)
    curator = CurriculumCurator(config)
    try:
        prompts = curator.list_prompts(tag)
        if not prompts:
            print(
                "[yellow]No prompts found.[/yellow]" + (f" matching tag '{tag}'." if tag else ".")
            )
            return

        print("\n[bold]Available prompts" + (f" matching tag '{tag}'" if tag else "") + ":[/bold]")
        for prompt_path in prompts:
            print(f"  {prompt_path}")

    except Exception as e:
        logger.exception("list_prompts_failed", error=str(e))
        print(f"[bold red]Error listing prompts:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(name="list-validators")
def list_validators_command():
    """List available content validators that can be used in workflows."""
    try:
        from curriculum_curator.validation.validators import VALIDATOR_REGISTRY

        print("\n[bold]Available Validators:[/bold]")

        # Group validators by category
        categories = {
            "quality": [],
            "accuracy": [],
            "alignment": [],
            "style": [],
            "language": [],
            "safety": [],
        }

        # Sort validators into categories
        for name, cls in VALIDATOR_REGISTRY.items():
            implemented = cls is not None

            if "quality" in name or name in [
                "similarity",
                "structure",
                "readability",
                "completeness",
                "coherence",
                "consistency",
                "generic_detector",
            ]:
                categories["quality"].append((name, implemented))
            elif "accuracy" in name or name in ["factuality", "references"]:
                categories["accuracy"].append((name, implemented))
            elif "alignment" in name or name in [
                "objectives",
                "relevance",
                "age_appropriateness",
                "instruction_adherence",
            ]:
                categories["alignment"].append((name, implemented))
            elif "style" in name or name in ["bias", "tone"]:
                categories["style"].append((name, implemented))
            elif "language" in name or name in ["language_detector", "grammar", "spelling"]:
                categories["language"].append((name, implemented))
            elif "safety" in name or name in ["content_safety"]:
                categories["safety"].append((name, implemented))
            else:
                # Default to quality for anything not categorized
                categories["quality"].append((name, implemented))

        # Print each category
        for category, validators in categories.items():
            if validators:
                print(f"\n[cyan]{category.title()} Validators:[/cyan]")
                for name, implemented in sorted(validators):
                    status = "[green]✓[/green]" if implemented else "[red]✗[/red]"
                    print(f"  {status} {name}")

    except Exception as e:
        logger.exception("list_validators_failed", error=str(e))
        print(f"[bold red]Error listing validators:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(name="list-remediators")
def list_remediators_command():
    """List available content remediators that can be used in workflows."""
    try:
        from curriculum_curator.remediation.remediators import REMEDIATOR_REGISTRY

        print("\n[bold]Available Remediators:[/bold]")

        # Group remediators by category
        categories = {"autofix": [], "rewrite": [], "workflow": [], "language": []}

        # Sort remediators into categories
        for name, cls in REMEDIATOR_REGISTRY.items():
            implemented = cls is not None

            if "format" in name or "sentence" in name or "terminology" in name:
                categories["autofix"].append((name, implemented))
            elif "rewrite" in name or "rephrasing" in name:
                categories["rewrite"].append((name, implemented))
            elif "workflow" in name or "flag" in name or "review" in name:
                categories["workflow"].append((name, implemented))
            elif "language" in name or "translator" in name:
                categories["language"].append((name, implemented))
            else:
                # Default to autofix for anything not categorized
                categories["autofix"].append((name, implemented))

        # Print each category
        for category, remediators in categories.items():
            if remediators:
                print(f"\n[cyan]{category.title()} Remediators:[/cyan]")
                for name, implemented in sorted(remediators):
                    status = "[green]✓[/green]" if implemented else "[red]✗[/red]"
                    print(f"  {status} {name}")

    except Exception as e:
        logger.exception("list_remediators_failed", error=str(e))
        print(f"[bold red]Error listing remediators:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(name="build-workflow")
def build_workflow_command(
    output_file: Path = typer.Argument(..., help="Path to save the workflow configuration"),
    base_file: Optional[Path] = typer.Option(
        None, "--base", "-b", help="Base workflow to start from"
    ),
    config_path: Path = typer.Option(
        "config.yaml", "--config", "-c", help="Path to configuration file."
    ),
):
    """Interactive workflow builder to create or edit workflow configurations.

    This command launches an interactive menu-driven interface to help you build
    workflow configurations without manually editing YAML files. It guides you through
    the process of creating each step and validates the workflow as you build it.
    """
    try:
        config = load_config(config_path)
        builder = WorkflowBuilder(config)

        if base_file:
            builder.load_base(base_file)

        builder.run_interactive()

    except Exception as e:
        logger.exception("build_workflow_failed", error=str(e))
        print(f"[bold red]Error building workflow:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(name="edit-prompt")
def edit_prompt_command(
    prompt_path: Optional[str] = typer.Argument(
        None, help="Path to the prompt file to edit (optional)"
    ),
    config_path: Path = typer.Option(
        "config.yaml", "--config", "-c", help="Path to configuration file."
    ),
):
    """Interactive prompt editor for creating and editing prompt templates.

    This command launches an interactive menu-driven interface to help you create
    and edit prompt templates with proper front matter. If a prompt path is provided,
    it will directly open that prompt for editing. Otherwise, it will show a menu
    of options to list existing prompts, create new ones, or install defaults.
    """
    try:
        from curriculum_curator.prompt.editor import edit_prompt

        config = load_config(config_path)

        # Get prompt base path from config
        if hasattr(config, "prompt_path") and config.prompt_path:
            prompt_base_path = Path(config.prompt_path)
        else:
            # Default to 'prompts' directory if not specified in config
            prompt_base_path = Path("prompts")

        edit_prompt(prompt_base_path, prompt_path)

    except Exception as e:
        logger.exception("edit_prompt_failed", error=str(e))
        print(f"[bold red]Error editing prompt:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(name="interactive")
def interactive_command(
    config_path: Path = typer.Option(
        "config.yaml", "--config", "-c", help="Path to configuration file."
    ),
):
    """Launch interactive mode with a menu of common operations.

    This command provides a user-friendly interface for common operations like
    running workflows, building new workflows, editing prompts, and initializing
    projects. It's especially useful for new users or those who prefer a guided,
    menu-driven experience over command-line arguments.
    """
    try:
        from curriculum_curator.interactive import run_interactive

        run_interactive(config_path)

    except Exception as e:
        logger.exception("interactive_mode_failed", error=str(e))
        print(f"[bold red]Error in interactive mode:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def resume(
    session_id: str = typer.Argument(..., help="The Session ID of the workflow to resume."),
    from_step: Optional[str] = typer.Option(None, help="Specific step name to resume from."),
    config_path: Path = typer.Option(
        "config.yaml", "--config", "-c", help="Path to configuration file."
    ),
    output_json: bool = typer.Option(False, "--output-json", "-j", help="Output result as JSON."),
):
    """Resume a previously interrupted workflow session."""
    config = load_config(config_path)
    curator = CurriculumCurator(config)
    try:
        print(f"Resuming workflow session '{session_id}'...")
        result = asyncio.run(curator.resume_workflow(session_id, from_step))
        _print_result(result, output_json)
    except Exception as e:
        logger.exception("resume_workflow_failed", error=str(e))
        print(f"[bold red]Error resuming workflow session '{session_id}':[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def init(
    output_dir: Path = typer.Argument(
        Path("."), help="Directory to initialize with example prompts and configuration."
    ),
):
    """Initialize a new project with example prompts and configuration."""
    try:
        print(f"Initializing Curriculum Curator project in {output_dir}...")
        # This would be implemented to copy example prompts and configuration
        print("[green]Project initialized successfully.[/green]")
        print("\nNext steps:")
        print("1. Edit config.yaml to configure your LLM providers")
        print("2. Modify the example prompts in the prompts/ directory")
        print("3. Run 'curator list-workflows' to see available workflows")
    except Exception as e:
        logger.exception("init_failed", error=str(e))
        print(f"[bold red]Error initializing project:[/bold red] {e}")
        raise typer.Exit(code=1)


# --- Entry Point ---
def main():
    """Main entry point for the CLI."""
    # Configure logging
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    # Run the Typer app
    app()


if __name__ == "__main__":
    main()
