"""
User data export functionality
"""

import json
from datetime import datetime
from io import BytesIO
from zipfile import ZipFile

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models import Content, Unit, User

router = APIRouter()


@router.get("/export/data")
async def export_user_data(
    export_format: str = "json",  # json or zip
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Export all user data.
    Returns user's courses and content in JSON or ZIP format.
    """
    # Get all user's units/courses
    units = db.query(Unit).filter(Unit.owner_id == current_user.id).all()

    # Build export data
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
        },
        "courses": [],
    }

    for unit in units:
        # Get all content for this unit
        contents = db.query(Content).filter(Content.unit_id == unit.id).all()

        unit_data = {
            "id": str(unit.id),
            "title": unit.title,
            "code": unit.code,
            "description": unit.description,
            "year": unit.year,
            "semester": unit.semester,
            "status": unit.status,
            "pedagogy_type": unit.pedagogy_type,
            "difficulty_level": unit.difficulty_level,
            "duration_weeks": unit.duration_weeks,
            "credit_points": unit.credit_points,
            "created_at": unit.created_at.isoformat(),
            "updated_at": unit.updated_at.isoformat(),
            "contents": [],
        }

        for content in contents:
            content_data = {
                "id": str(content.id),
                "title": content.title,
                "type": content.type,
                "status": content.status,
                "order_index": content.order_index,
                "content_markdown": content.content_markdown,
                "summary": content.summary,
                "estimated_duration_minutes": content.estimated_duration_minutes,
                "difficulty_level": content.difficulty_level,
                "learning_objectives": content.learning_objectives,
                "created_at": content.created_at.isoformat(),
                "updated_at": content.updated_at.isoformat(),
            }
            unit_data["contents"].append(content_data)

        export_data["courses"].append(unit_data)

    if export_format == "zip":
        # Create ZIP file with JSON and markdown files
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zip_file:
            # Add main JSON file
            zip_file.writestr(
                "export_data.json",
                json.dumps(export_data, indent=2),
            )

            # Add markdown files for each course
            for course in export_data["courses"]:
                course_dir = f"courses/{course['code']}_{course['title'][:30]}"

                # Course README
                course_readme = f"""# {course["title"]}

**Code:** {course["code"]}
**Year:** {course["year"]}
**Semester:** {course["semester"]}
**Status:** {course["status"]}

## Description
{course["description"] or "No description provided."}

## Contents
"""
                for content in course["contents"]:
                    course_readme += f"- {content['title']} ({content['type']})\n"

                zip_file.writestr(f"{course_dir}/README.md", course_readme)

                # Individual content files
                for content in course["contents"]:
                    if content["content_markdown"]:
                        filename = f"{course_dir}/{content['order_index']:02d}_{content['title'][:50]}.md"
                        zip_file.writestr(filename, content["content_markdown"])

        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=curriculum_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            },
        )

    # JSON format
    return StreamingResponse(
        BytesIO(json.dumps(export_data, indent=2).encode()),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=curriculum_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        },
    )
