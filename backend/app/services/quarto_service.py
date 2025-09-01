"""
Quarto document processing service

Handles rendering of Quarto markdown to various output formats
and manages user presets for front matter configurations.
"""

import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from app.models.quarto_preset import QuartoPreset


class QuartoService:
    """Service for processing Quarto documents and managing presets"""

    def __init__(self):
        self.quarto_path = os.getenv("QUARTO_PATH", "quarto")
        self.output_dir = Path("/tmp/quarto_output")
        self.output_dir.mkdir(exist_ok=True)

    def generate_yaml_from_simple(self, settings: dict[str, Any]) -> str:
        """Generate YAML front matter from simple UI settings"""
        yaml_dict = {}

        # Add title and author if provided
        if settings.get("title"):
            yaml_dict["title"] = settings["title"]
        if settings.get("subtitle"):
            yaml_dict["subtitle"] = settings["subtitle"]
        if settings.get("author"):
            yaml_dict["author"] = settings["author"]

        # Configure output formats
        formats = settings.get("formats", ["html"])
        if len(formats) == 1:
            # Single format
            format_name = formats[0]
            format_config = {}

            if settings.get("theme") and format_name in ["html", "revealjs"]:
                format_config["theme"] = settings["theme"]
            if settings.get("toc") and format_name in ["html", "pdf"]:
                format_config["toc"] = True

            yaml_dict["format"] = (
                {format_name: format_config} if format_config else format_name
            )
        else:
            # Multiple formats
            yaml_dict["format"] = {}
            for format_name in formats:
                format_config = {}

                if format_name == "html" and settings.get("theme"):
                    format_config["theme"] = settings["theme"]
                if format_name in ["html", "pdf"] and settings.get("toc"):
                    format_config["toc"] = True
                if format_name == "revealjs" and settings.get("theme"):
                    format_config["theme"] = settings.get("revealjs_theme", "default")

                yaml_dict["format"][format_name] = (
                    format_config if format_config else {}
                )

        return yaml.dump(yaml_dict, default_flow_style=False)

    async def render_content(
        self,
        content: str,
        mode: str = "simple",
        settings: dict[str, Any] | None = None,
        content_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Render Quarto content to specified formats

        Args:
            content: The markdown/quarto content
            mode: 'simple' or 'advanced' mode
            settings: Settings based on mode
            content_id: Optional content ID for naming

        Returns:
            Dictionary with output file paths and metadata
        """
        # Generate unique ID for this render
        render_id = content_id or str(uuid.uuid4())

        # Create temporary directory for this render
        temp_dir = Path(tempfile.mkdtemp(prefix=f"quarto_{render_id}_"))

        try:
            # Generate YAML front matter based on mode
            if mode == "simple":
                yaml_content = self.generate_yaml_from_simple(settings or {})
            else:
                # Advanced mode - use provided YAML
                yaml_content = settings.get("yaml", "")

            # Create the .qmd file with front matter and content
            qmd_file = temp_dir / f"{render_id}.qmd"
            with qmd_file.open("w", encoding="utf-8") as f:
                if yaml_content:
                    f.write("---\n")
                    f.write(yaml_content)
                    f.write("---\n\n")
                f.write(content)

            # Run quarto render
            result = subprocess.run(
                [self.quarto_path, "render", str(qmd_file)],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            if result.returncode != 0:
                msg = f"Quarto render failed: {result.stderr}"
                raise RuntimeError(msg)

            # Collect output files
            outputs = []
            for file_path in temp_dir.glob(f"{render_id}.*"):
                if file_path.suffix not in [".qmd", ".md"]:
                    # Move to output directory
                    output_path = self.output_dir / file_path.name
                    file_path.rename(output_path)

                    outputs.append(
                        {
                            "format": file_path.suffix[1:],  # Remove the dot
                            "path": str(output_path),
                            "filename": file_path.name,
                            "size": output_path.stat().st_size,
                        }
                    )

            return {
                "success": True,
                "render_id": render_id,
                "outputs": outputs,
                "yaml_used": yaml_content,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "render_id": render_id,
            }
        finally:
            # Clean up temp directory
            if temp_dir.exists():
                for file in temp_dir.glob("*"):
                    file.unlink()
                temp_dir.rmdir()

    async def preview_content(
        self, content: str, settings: dict[str, Any] | None = None
    ) -> str:
        """
        Generate HTML preview of Quarto content

        Args:
            content: The markdown/quarto content
            settings: Optional settings for preview

        Returns:
            HTML string of rendered content
        """
        # Force HTML output for preview
        preview_settings = settings.copy() if settings else {}
        preview_settings["formats"] = ["html"]

        result = await self.render_content(
            content=content,
            mode="simple",
            settings=preview_settings,
        )

        if result["success"] and result["outputs"]:
            html_output = next(
                (o for o in result["outputs"] if o["format"] == "html"), None
            )
            if html_output:
                with Path(html_output["path"]).open(encoding="utf-8") as f:
                    return f.read()

        return "<p>Preview generation failed</p>"

    async def get_user_presets(
        self, db: Session, user_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        """
        Get user's saved Quarto presets

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of preset dictionaries
        """

        presets = (
            db.query(QuartoPreset)
            .filter(QuartoPreset.user_id == user_id)
            .order_by(QuartoPreset.name)
            .all()
        )

        return [
            {
                "id": str(preset.id),
                "name": preset.name,
                "yaml_content": preset.yaml_content,
                "is_default": preset.is_default,
                "created_at": preset.created_at.isoformat(),
            }
            for preset in presets
        ]

    async def save_preset(
        self,
        db: Session,
        user_id: uuid.UUID,
        name: str,
        yaml_content: str,
        is_default: bool = False,
    ) -> dict[str, Any]:
        """
        Save a new Quarto preset for user

        Args:
            db: Database session
            user_id: User ID
            name: Preset name
            yaml_content: YAML front matter content
            is_default: Whether this is the default preset

        Returns:
            Created preset dictionary
        """

        # If setting as default, unset other defaults
        if is_default:
            db.query(QuartoPreset).filter(
                QuartoPreset.user_id == user_id, QuartoPreset.is_default
            ).update({"is_default": False})

        preset = QuartoPreset(
            user_id=user_id,
            name=name,
            yaml_content=yaml_content,
            is_default=is_default,
        )

        db.add(preset)
        db.commit()
        db.refresh(preset)

        return {
            "id": str(preset.id),
            "name": preset.name,
            "yaml_content": preset.yaml_content,
            "is_default": preset.is_default,
            "created_at": preset.created_at.isoformat(),
        }

    async def delete_preset(
        self, db: Session, user_id: uuid.UUID, preset_id: str
    ) -> bool:
        """
        Delete a user's preset

        Args:
            db: Database session
            user_id: User ID
            preset_id: Preset ID to delete

        Returns:
            True if deleted, False if not found
        """

        preset = (
            db.query(QuartoPreset)
            .filter(QuartoPreset.id == preset_id, QuartoPreset.user_id == user_id)
            .first()
        )

        if preset:
            db.delete(preset)
            db.commit()
            return True

        return False

    async def get_available_themes(self) -> dict[str, list[str]]:
        """Get available themes for different output formats"""
        return {
            "html": [
                "default",
                "cosmo",
                "flatly",
                "journal",
                "litera",
                "lumen",
                "lux",
                "materia",
                "minty",
                "morph",
                "pulse",
                "quartz",
                "sandstone",
                "simplex",
                "sketchy",
                "slate",
                "solar",
                "spacelab",
                "superhero",
                "united",
                "vapor",
                "yeti",
                "zephyr",
            ],
            "revealjs": [
                "default",
                "beige",
                "blood",
                "dark",
                "league",
                "moon",
                "night",
                "serif",
                "simple",
                "sky",
                "solarized",
                "white",
            ],
        }

    def cleanup_old_outputs(self, max_age_hours: int = 24):
        """Clean up old output files"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        for file_path in self.output_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()


# Singleton instance
quarto_service = QuartoService()
