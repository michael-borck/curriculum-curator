"""Prompt editor for creating and editing prompts with front matter."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any

import structlog
import frontmatter
import yaml
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from curriculum_curator.prompt.registry import PromptRegistry

logger = structlog.get_logger()

# Default prompt templates by type
DEFAULT_TEMPLATES = {
    "course/overview": """---
title: Course Overview
tags: [course, overview]
description: Generate a course overview with objectives, topics, and prerequisites
variables:
  - course_title
  - target_audience
---
You are an expert curriculum designer. Your task is to create a comprehensive overview for a course titled "{{course_title}}".

The target audience for this course is {{target_audience}}.

Your overview should include:

1. A compelling introduction to the subject matter
2. 3-5 clear learning objectives
3. Key topics that will be covered
4. Prerequisites for taking the course
5. Expected outcomes upon completion

Format the overview in markdown, with appropriate headings, lists, and emphasis.
""",

    "module/outline": """---
title: Module Outline
tags: [module, outline]
description: Generate a module outline with topics and learning activities
variables:
  - module_title
  - module_number
  - course_context
---
You are an expert curriculum designer. Your task is to create a detailed outline for Module {{module_number}}: {{module_title}} within the context of {{course_context}}.

Your module outline should include:

1. Module introduction and goals
2. 3-5 specific learning objectives
3. Key topics to be covered, organized logically
4. Learning activities for each topic
5. Assessment opportunities

Format the outline in markdown, with appropriate headings, lists, and emphasis.
""",

    "lecture/content": """---
title: Lecture Content
tags: [lecture, content]
description: Generate detailed lecture content for a specific topic
variables:
  - lecture_title
  - module_context
  - duration
---
You are an expert educator. Your task is to create detailed lecture content for "{{lecture_title}}" within the context of {{module_context}}. The lecture should be designed to take approximately {{duration}} minutes.

Your lecture content should include:

1. An engaging introduction to the topic
2. Clear explanations of key concepts
3. Illustrative examples and applications
4. Discussion questions to promote engagement
5. A concise summary of main points

Format the content in markdown, with appropriate headings, lists, and emphasis. Include any diagrams or visual aid descriptions in markdown format.
""",

    "assessment/questions": """---
title: Assessment Questions
tags: [assessment, questions]
description: Generate assessment questions for a specific module or topic
variables:
  - topic
  - difficulty_level
  - question_types
---
You are an expert assessment designer. Your task is to create a set of assessment questions for "{{topic}}" at a {{difficulty_level}} difficulty level.

Include the following question types: {{question_types}}

For each question:
1. Provide clear instructions
2. Include the question text
3. For multiple choice questions, provide 4-5 options with one correct answer
4. Indicate the correct answer(s)
5. Provide a brief explanation of why the answer is correct

Format the questions in markdown, with appropriate numbering and organization.
""",

    "custom": """---
title: Custom Prompt
tags: [custom]
description: Custom prompt template
variables:
  - variable1
  - variable2
---
Your prompt content here. You can use variables like {{variable1}} and {{variable2}}.
"""
}


class PromptEditor:
    """Interactive editor for creating and editing prompts."""
    
    def __init__(self, base_path: Path):
        """Initialize the prompt editor.
        
        Args:
            base_path: Base directory for prompts
        """
        self.console = Console()
        self.base_path = Path(base_path)
        self.registry = PromptRegistry(base_path)
    
    def run_interactive(self, prompt_path: Optional[str] = None):
        """Run the interactive prompt editor.
        
        Args:
            prompt_path: Optional path to a specific prompt to edit
        """
        if prompt_path:
            # Edit specific prompt
            full_path = self._resolve_prompt_path(prompt_path)
            self._edit_prompt(full_path)
        else:
            # Show menu of options
            self._show_main_menu()
    
    def _resolve_prompt_path(self, prompt_path: str) -> Path:
        """Resolve a prompt path to a full path.
        
        Args:
            prompt_path: Relative path to a prompt
            
        Returns:
            Full path to the prompt
        """
        # If path is absolute, use it directly
        if os.path.isabs(prompt_path):
            return Path(prompt_path)
            
        # Otherwise, resolve relative to base path
        return self.base_path / prompt_path
    
    def _show_main_menu(self):
        """Show the main menu for prompt editing."""
        self.console.print(Panel("[bold blue]Prompt Editor[/bold blue]", 
                                subtitle="Create and edit prompts"))
        
        # Create base directory if it doesn't exist
        if not self.base_path.exists():
            if Confirm.ask(f"Prompt directory {self.base_path} does not exist. Create it?", default=True):
                self.base_path.mkdir(parents=True, exist_ok=True)
                self.console.print(f"[green]Created directory {self.base_path}[/green]")
            else:
                self.console.print("[yellow]Cannot continue without a prompt directory.[/yellow]")
                return
        
        while True:
            self.console.print("\n[bold]Main Menu:[/bold]")
            self.console.print("1. List and edit existing prompts")
            self.console.print("2. Create a new prompt")
            self.console.print("3. Install default prompt templates")
            self.console.print("4. Exit")
            
            choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"])
            
            if choice == "1":
                self._list_and_edit_prompts()
            elif choice == "2":
                self._create_new_prompt()
            elif choice == "3":
                self._install_default_templates()
            elif choice == "4":
                break
    
    def _list_and_edit_prompts(self):
        """List existing prompts and allow user to select one to edit."""
        prompts = self.registry.list_prompts()
        
        if not prompts:
            self.console.print("[yellow]No prompts found.[/yellow]")
            return
        
        table = Table(title="Available Prompts")
        table.add_column("#", style="dim")
        table.add_column("Path", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Description")
        
        # Load metadata for each prompt
        prompt_metadata = []
        for i, prompt_path in enumerate(prompts, 1):
            try:
                metadata = self.registry.get_prompt_metadata(prompt_path)
                title = metadata.get("title", "Untitled")
                description = metadata.get("description", "")
                table.add_row(str(i), prompt_path, title, description)
                prompt_metadata.append((prompt_path, metadata))
            except Exception:
                table.add_row(str(i), prompt_path, "[red]Error loading metadata[/red]", "")
                prompt_metadata.append((prompt_path, {}))
        
        self.console.print(table)
        
        prompt_idx = Prompt.ask(
            "Enter prompt number to edit (or 'back' to return)",
            default="back"
        )
        
        if prompt_idx.lower() == "back":
            return
            
        if prompt_idx.isdigit() and 1 <= int(prompt_idx) <= len(prompts):
            idx = int(prompt_idx) - 1
            prompt_path = prompts[idx]
            full_path = self._resolve_prompt_path(prompt_path)
            self._edit_prompt(full_path)
        else:
            self.console.print("[red]Invalid choice.[/red]")
    
    def _create_new_prompt(self):
        """Create a new prompt from scratch or from a template."""
        # Choose template type
        self.console.print("\n[bold]Select Prompt Type:[/bold]")
        templates = list(DEFAULT_TEMPLATES.keys())
        for i, template_name in enumerate(templates, 1):
            self.console.print(f"{i}. {template_name}")
        
        template_idx = Prompt.ask(
            "Choose a template (or 'back' to return)",
            default="back"
        )
        
        if template_idx.lower() == "back":
            return
            
        if template_idx.isdigit() and 1 <= int(template_idx) <= len(templates):
            template_name = templates[int(template_idx) - 1]
            template_content = DEFAULT_TEMPLATES[template_name]
            
            # Get file path
            if "/" in template_name and template_name != "custom":
                default_path = template_name + ".txt"
            else:
                default_path = "custom.txt"
                
            prompt_path = Prompt.ask("Enter prompt file path (relative to prompt directory)", default=default_path)
            
            # Create directories if needed
            full_path = self._resolve_prompt_path(prompt_path)
            os.makedirs(full_path.parent, exist_ok=True)
            
            # Write template content to file
            with open(full_path, "w") as f:
                f.write(template_content)
                
            self.console.print(f"[green]Created prompt template at {full_path}[/green]")
            
            # Open for editing
            if Confirm.ask("Edit the new prompt now?", default=True):
                self._edit_prompt(full_path)
        else:
            self.console.print("[red]Invalid choice.[/red]")
    
    def _install_default_templates(self):
        """Install all default templates to the prompt directory."""
        if not Confirm.ask("This will install default templates in your prompt directory. Continue?", default=True):
            return
            
        for template_name, content in DEFAULT_TEMPLATES.items():
            if template_name == "custom":
                continue  # Skip the generic custom template
                
            prompt_path = template_name + ".txt"
            full_path = self._resolve_prompt_path(prompt_path)
            
            # Create directories if needed
            os.makedirs(full_path.parent, exist_ok=True)
            
            # Only write if file doesn't exist or user confirms overwrite
            if not full_path.exists() or Confirm.ask(f"{full_path} already exists. Overwrite?", default=False):
                with open(full_path, "w") as f:
                    f.write(content)
                self.console.print(f"[green]Installed template: {prompt_path}[/green]")
        
        self.console.print("[green]Default templates installed successfully![/green]")
    
    def _edit_prompt(self, file_path: Path):
        """Open a prompt file in the user's editor.
        
        Args:
            file_path: Path to the prompt file
        """
        if not file_path.exists():
            self.console.print(f"[yellow]File {file_path} does not exist.[/yellow]")
            if Confirm.ask("Create it?", default=True):
                # Create parent directories if needed
                os.makedirs(file_path.parent, exist_ok=True)
                with open(file_path, "w") as f:
                    # Insert basic front matter template
                    f.write("---\ntitle: Untitled\ntags: []\ndescription: \n---\n\n")
            else:
                return
        
        # Get the user's preferred editor from environment
        editor = os.environ.get("EDITOR", "nano")  # Default to nano if not set
        
        try:
            # Open the file in the editor
            subprocess.run([editor, str(file_path)], check=True)
            self.console.print(f"[green]File edited: {file_path}[/green]")
            
            # Validate front matter after editing
            self._validate_front_matter(file_path)
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]Error running editor: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]An error occurred: {e}[/red]")
    
    def _validate_front_matter(self, file_path: Path):
        """Validate the front matter in a prompt file.
        
        Args:
            file_path: Path to the prompt file
        """
        try:
            with open(file_path, "r") as f:
                content = f.read()
                
            # Parse front matter
            post = frontmatter.loads(content)
            metadata = post.metadata
            
            # Check for required fields
            required_fields = ["title", "description"]
            missing_fields = [field for field in required_fields if field not in metadata or not metadata[field]]
            
            if missing_fields:
                self.console.print(f"[yellow]Warning: Missing front matter fields: {', '.join(missing_fields)}[/yellow]")
            else:
                self.console.print("[green]Front matter validation successful![/green]")
                
            # Display front matter
            self.console.print("\n[bold]Front Matter:[/bold]")
            for key, value in metadata.items():
                self.console.print(f"  {key}: {value}")
        except Exception as e:
            self.console.print(f"[red]Error validating front matter: {e}[/red]")


def edit_prompt(base_path: Path, prompt_path: Optional[str] = None):
    """Edit a prompt using the interactive editor.
    
    Args:
        base_path: Base directory for prompts
        prompt_path: Optional specific prompt to edit
    """
    editor = PromptEditor(base_path)
    editor.run_interactive(prompt_path)