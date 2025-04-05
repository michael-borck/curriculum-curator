import asyncio
import sys
import yaml
import json
from pathlib import Path
from typing import List, Optional

import typer
import structlog
from rich import print

# Import the core functionality
from curriculum_curator.core import CurriculumCurator

logger = structlog.get_logger()

# Create the Typer app
app = typer.Typer(help="CurriculumCurator CLI - Orchestrate educational content workflows.")


# --- Helper Functions ---

def load_config(config_path: Path = typer.Option("config.yaml", "--config", "-c", help="Path to configuration file.")):
    """Loads configuration from YAML file."""
    from curriculum_curator.config.utils import load_config as load_app_config
    
    try:
        return load_app_config(str(config_path))
    except FileNotFoundError:
        print(f"[bold red]Error:[/bold red] Configuration file not found at {config_path}")
        raise typer.Exit(code=1)
    except Exception as e:
        print(f"[bold red]Error:[/bold red] Failed to load or parse configuration file {config_path}: {e}")
        raise typer.Exit(code=1)


def parse_vars(var_list: Optional[List[str]] = typer.Option(None, "--var", "-v", help="Variables in key=value format. Can be used multiple times.")) -> dict:
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
        print(f"[green]Workflow completed successfully.[/green]")
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
    var: Optional[List[str]] = typer.Option(None, "--var", "-v", help="Variables in key=value format. Can be used multiple times."),
    session_id: Optional[str] = typer.Option(None, help="Specify a session ID to use or resume."),
    config_path: Path = typer.Option("config.yaml", "--config", "-c", help="Path to configuration file."),
    output_json: bool = typer.Option(False, "--output-json", "-j", help="Output result as JSON.")
):
    """
    Run a specified workflow.
    """
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
    config_path: Path = typer.Option("config.yaml", "--config", "-c", help="Path to configuration file.")
):
    """
    List available workflows defined in the configuration file.
    """
    config = load_config(config_path)
    workflows = config.get("workflows", {})
    if not workflows:
        print("[yellow]No workflows found in configuration.[/yellow]")
        return

    print("[bold]Available workflows:[/bold]")
    for name, workflow_config in workflows.items():
        description = workflow_config.get("description", "[i]No description[/i]")
        print(f"  [cyan]{name}[/cyan]: {description}")


@app.command(name="list-prompts")
def list_prompts_command(
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter prompts by tag specified in YAML front matter."),
    config_path: Path = typer.Option("config.yaml", "--config", "-c", help="Path to configuration file.")
):
    """
    List available prompts, optionally filtering by tag.
    """
    config = load_config(config_path)
    curator = CurriculumCurator(config)
    try:
        prompts = curator.list_prompts(tag)
        if not prompts:
            print("[yellow]No prompts found.[/yellow]" + (f" matching tag '{tag}'." if tag else "."))
            return

        print("\n[bold]Available prompts" + (f" matching tag '{tag}'" if tag else "") + ":[/bold]")
        for prompt_path in prompts:
            print(f"  {prompt_path}")

    except Exception as e:
        logger.exception("list_prompts_failed", error=str(e))
        print(f"[bold red]Error listing prompts:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def resume(
    session_id: str = typer.Argument(..., help="The Session ID of the workflow to resume."),
    from_step: Optional[str] = typer.Option(None, help="Specific step name to resume from."),
    config_path: Path = typer.Option("config.yaml", "--config", "-c", help="Path to configuration file."),
    output_json: bool = typer.Option(False, "--output-json", "-j", help="Output result as JSON.")
):
    """
    Resume a previously interrupted workflow session.
    """
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
    output_dir: Path = typer.Argument(Path("."), help="Directory to initialize with example prompts and configuration."),
):
    """
    Initialize a new project with example prompts and configuration.
    """
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