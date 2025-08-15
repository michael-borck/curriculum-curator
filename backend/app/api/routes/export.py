"""
Export endpoints for converting materials to various formats using Quarto/Pandoc
"""

import io
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models import Course, Material, User
from app.services.git_content_service import get_git_service

router = APIRouter()

ExportFormat = Literal["pdf", "docx", "pptx", "html", "md", "tex"]


class QuartoExportService:
    """Service for exporting content using Quarto/Pandoc"""

    @staticmethod
    def create_quarto_project(content: str, title: str, author: str | None = None) -> Path:
        """Create a temporary Quarto project for export"""
        temp_dir = Path(tempfile.mkdtemp(prefix="quarto_export_"))

        # Create Quarto project structure
        qmd_file = temp_dir / "document.qmd"

        # Build Quarto front matter
        front_matter = {
            "title": title,
            "format": {
                "html": {"toc": True, "theme": "cosmo"},
                "pdf": {"toc": True, "documentclass": "article"},
                "docx": {"toc": True},
                "pptx": {"incremental": True}
            }
        }

        if author:
            front_matter["author"] = author

        # Write .qmd file
        qmd_content = f"""---
{json.dumps(front_matter, indent=2)[1:-1]}
---

{content}
"""
        qmd_file.write_text(qmd_content)

        return temp_dir

    @staticmethod
    def export_to_format(content: str, title: str, format: ExportFormat, author: str | None = None) -> bytes:  # noqa: A002
        """Export content to specified format using Quarto"""

        # Create temporary Quarto project
        project_dir = QuartoExportService.create_quarto_project(content, title, author)

        try:
            # Map format to Quarto output
            quarto_format_map = {
                "pdf": "pdf",
                "docx": "docx",
                "pptx": "pptx",
                "html": "html",
                "md": "gfm",  # GitHub Flavored Markdown
                "tex": "latex"
            }

            quarto_format = quarto_format_map.get(format, "html")

            # Run Quarto render
            cmd = [
                "quarto", "render",
                str(project_dir / "document.qmd"),
                "--to", quarto_format,
                "--quiet"
            ]

            subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Find output file
            output_extensions = {
                "pdf": ".pdf",
                "docx": ".docx",
                "pptx": ".pptx",
                "html": ".html",
                "md": ".md",
                "tex": ".tex"
            }

            output_file = project_dir / f"document{output_extensions[format]}"

            if not output_file.exists():
                raise FileNotFoundError("Export failed: output file not found")

            # Read and return file content
            return output_file.read_bytes()

        except subprocess.CalledProcessError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Export failed: {e.stderr}"
            )
        finally:
            # Cleanup temporary directory
            import shutil  # noqa: PLC0415
            shutil.rmtree(project_dir, ignore_errors=True)


@router.post("/{material_id}/export/{format}")
async def export_material(
    material_id: str,
    format: ExportFormat,  # noqa: A002
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Export a material to specified format (pdf, docx, pptx, html, md, tex).
    """
    # Get material and verify access
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    # Verify user has access to the course
    course = db.query(Course).filter(
        Course.id == material.course_id,
        Course.user_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get content from Git
    git_service = get_git_service()
    try:
        content = git_service.get_content(material.git_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material content not found in repository"
        )

    # Export using Quarto
    export_service = QuartoExportService()

    try:
        exported_content = export_service.export_to_format(
            content=content,
            title=material.title,
            format=format,
            author=current_user.name or current_user.email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {e!s}"
        )

    # Determine MIME type
    mime_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "html": "text/html",
        "md": "text/markdown",
        "tex": "text/x-tex"
    }

    mime_type = mime_types.get(format, "application/octet-stream")

    # Generate filename
    filename = f"{material.title.replace(' ', '_')}.{format}"

    # Return file response
    return StreamingResponse(
        io.BytesIO(exported_content),
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.post("/course/{course_id}/export")
async def export_course(
    course_id: str,
    format: ExportFormat,  # noqa: A002
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Export entire course materials to specified format.
    Combines all materials into a single document.
    """
    # Verify user owns the course
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or access denied"
        )

    # Get all materials for the course
    materials = db.query(Material).filter(
        Material.course_id == course_id
    ).order_by(Material.created_at).all()

    if not materials:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No materials found in course"
        )

    # Get Git service
    git_service = get_git_service()

    # Combine all materials
    combined_content = f"# {course.title}\n\n"
    if course.description:
        combined_content += f"{course.description}\n\n"

    for material in materials:
        try:
            content = git_service.get_content(material.git_path)
            combined_content += f"\n\n## {material.title}\n\n"
            if material.description:
                combined_content += f"*{material.description}*\n\n"
            combined_content += content
        except FileNotFoundError:
            combined_content += f"\n\n## {material.title}\n\n*Content not available*\n\n"

    # Export using Quarto
    export_service = QuartoExportService()

    try:
        exported_content = export_service.export_to_format(
            content=combined_content,
            title=course.title,
            format=format,
            author=current_user.name or current_user.email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {e!s}"
        )

    # Determine MIME type
    mime_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "html": "text/html",
        "md": "text/markdown",
        "tex": "text/x-tex"
    }

    mime_type = mime_types.get(format, "application/octet-stream")

    # Generate filename
    filename = f"{course.title.replace(' ', '_')}_complete.{format}"

    # Return file response
    return StreamingResponse(
        io.BytesIO(exported_content),
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/formats")
async def get_export_formats(
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get list of available export formats.
    """
    return {
        "formats": [
            {"id": "pdf", "name": "PDF", "description": "Portable Document Format"},
            {"id": "docx", "name": "Word", "description": "Microsoft Word Document"},
            {"id": "pptx", "name": "PowerPoint", "description": "Microsoft PowerPoint Presentation"},
            {"id": "html", "name": "HTML", "description": "Web Page"},
            {"id": "md", "name": "Markdown", "description": "Markdown Document"},
            {"id": "tex", "name": "LaTeX", "description": "LaTeX Document"}
        ]
    }
