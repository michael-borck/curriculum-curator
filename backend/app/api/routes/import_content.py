"""
API routes for importing and analyzing course content from PDFs
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models import (
    AssessmentPlan,
    Content,
    ContentCategory,
    ContentType,
    CourseOutline,
    Unit,
    UnitLearningOutcome,
    User,
    WeeklyTopic,
)
from app.services.document_analyzer_service import (
    document_analyzer_service,
)
from app.services.pdf_parser_service import ExtractionMethod, pdf_parser_service

router = APIRouter()


@router.post("/import/pdf/analyze")
async def analyze_pdf(
    file: UploadFile = File(...),
    extraction_method: ExtractionMethod = ExtractionMethod.AUTO,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Analyze a PDF document and extract course content structure

    This endpoint:
    1. Extracts text and structure from PDF
    2. Analyzes content for course elements
    3. Returns structured data without saving
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    # Check file size (max 50MB)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50MB limit",
        )

    try:
        # Extract content from PDF
        extracted_doc = await pdf_parser_service.extract_from_bytes(contents, extraction_method)

        # Analyze document structure
        analysis = await document_analyzer_service.analyze_document(extracted_doc)

        # Map to course structure
        course_mapping = await document_analyzer_service.map_to_course_structure(analysis)

        return {
            "status": "success",
            "filename": file.filename,
            "document_type": analysis.document_type,
            "metadata": {
                "title": analysis.title,
                "page_count": analysis.metadata["page_count"],
                "word_count": analysis.metadata["word_count"],
                "has_toc": analysis.metadata["has_toc"],
            },
            "extracted_content": {
                "sections_count": len(analysis.sections),
                "learning_outcomes_count": len(analysis.learning_outcomes),
                "assessments_count": len(analysis.assessments),
                "weekly_content_count": len(analysis.weekly_content),
                "key_concepts_count": len(analysis.key_concepts),
            },
            "course_structure": course_mapping,
            "sections": [
                {
                    "title": section.title,
                    "level": section.level,
                    "page_start": section.page_start,
                    "word_count": section.word_count,
                }
                for section in analysis.sections[:10]  # Limit to first 10
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF: {e!s}",
        )


@router.post("/import/pdf/extract-text")
async def extract_pdf_text(
    file: UploadFile = File(...),
    extraction_method: ExtractionMethod = ExtractionMethod.AUTO,
    output_format: str = "markdown",
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Extract text from PDF in various formats

    Supported output formats:
    - raw: Plain text as extracted
    - clean: Cleaned and normalized text
    - markdown: Converted to Markdown format
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    # Check file size (max 50MB)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50MB limit",
        )

    try:
        # Extract content from PDF
        extracted_doc = await pdf_parser_service.extract_from_bytes(contents, extraction_method)

        # Format output based on request
        if output_format == "markdown":
            text = await pdf_parser_service.convert_to_markdown(extracted_doc)
        elif output_format == "clean":
            text = pdf_parser_service.clean_extracted_text(extracted_doc.full_text)
        else:  # raw
            text = extracted_doc.full_text

        # Extract structure for additional info
        structure = await pdf_parser_service.extract_structure(extracted_doc)

        return {
            "status": "success",
            "filename": file.filename,
            "metadata": {
                "title": extracted_doc.metadata.title,
                "author": extracted_doc.metadata.author,
                "page_count": extracted_doc.metadata.page_count,
                "extraction_method": extracted_doc.extraction_method,
            },
            "text": text,
            "structure": structure,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting text from PDF: {e!s}",
        )


@router.post("/import/pdf/create-course-structure/{unit_id}")
async def create_course_structure_from_pdf(
    unit_id: str,
    file: UploadFile = File(...),
    auto_create: bool = True,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Import PDF and create course structure (outline, outcomes, topics, assessments)

    Parameters:
    - unit_id: Target unit for the course structure
    - file: PDF file to import
    - auto_create: Automatically create all extracted elements
    """
    # Verify unit exists and user has access
    unit = db.query(Unit).filter(Unit.id == unit_id, Unit.owner_id == current_user.id).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Check if unit already has a course outline
    existing_outline = db.query(CourseOutline).filter(CourseOutline.unit_id == unit_id).first()
    if existing_outline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit already has a course outline. Delete existing outline first.",
        )

    # Process PDF
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50MB limit",
        )

    try:
        # Extract and analyze PDF
        extracted_doc = await pdf_parser_service.extract_from_bytes(contents)
        analysis = await document_analyzer_service.analyze_document(extracted_doc)
        course_mapping = await document_analyzer_service.map_to_course_structure(analysis)

        created_items = {
            "course_outline": None,
            "learning_outcomes": [],
            "weekly_topics": [],
            "assessments": [],
        }

        if auto_create:
            # Create course outline
            outline_data = course_mapping["course_outline"]
            outline = CourseOutline(
                id=uuid.uuid4(),
                unit_id=unit_id,
                title=outline_data["title"] or f"Course Outline for {unit.name}",
                description=outline_data["description"],
                duration_weeks=outline_data["duration_weeks"],
                created_by_id=current_user.id,
            )
            db.add(outline)
            db.flush()  # Get ID without committing
            created_items["course_outline"] = outline.id

            # Create learning outcomes
            for lo_data in course_mapping["learning_outcomes"]:
                outcome = UnitLearningOutcome(
                    id=uuid.uuid4(),
                    unit_id=unit_id,
                    course_outline_id=outline.id,
                    outcome_type=lo_data["outcome_type"],
                    outcome_text=lo_data["outcome_text"],
                    bloom_level=lo_data["bloom_level"] or "understand",
                    created_by_id=current_user.id,
                )
                db.add(outcome)
                created_items["learning_outcomes"].append(
                    {"id": str(outcome.id), "text": outcome.outcome_text[:100]}
                )

            # Create weekly topics
            for topic_data in course_mapping["weekly_topics"]:
                topic = WeeklyTopic(
                    id=uuid.uuid4(),
                    course_outline_id=outline.id,
                    unit_id=unit_id,
                    week_number=topic_data["week_number"],
                    topic_title=topic_data["topic_title"],
                    pre_class_modules=topic_data.get("pre_class_modules"),
                    in_class_activities=topic_data.get("in_class_activities"),
                    post_class_tasks=topic_data.get("post_class_tasks"),
                    required_readings=topic_data.get("required_readings"),
                    created_by_id=current_user.id,
                )
                db.add(topic)
                created_items["weekly_topics"].append(
                    {"id": str(topic.id), "week": topic.week_number, "title": topic.topic_title}
                )

            # Create assessments
            for assess_data in course_mapping["assessments"]:
                assessment = AssessmentPlan(
                    id=uuid.uuid4(),
                    course_outline_id=outline.id,
                    unit_id=unit_id,
                    assessment_name=assess_data["assessment_name"],
                    assessment_type=assess_data["assessment_type"],
                    description=assess_data.get("description", ""),
                    weight_percentage=assess_data.get("weight_percentage", 0),
                    due_week=assess_data.get("due_week", 12),
                    created_by_id=current_user.id,
                )
                db.add(assessment)
                created_items["assessments"].append(
                    {
                        "id": str(assessment.id),
                        "name": assessment.assessment_name,
                        "type": assessment.assessment_type,
                    }
                )

            db.commit()

            return {
                "status": "success",
                "message": "Course structure created successfully",
                "created": created_items,
                "document_info": {
                    "filename": file.filename,
                    "document_type": analysis.document_type,
                    "title": analysis.title,
                },
            }

        # Return preview without creating
        return {
            "status": "preview",
            "message": "Course structure preview (not saved)",
            "course_structure": course_mapping,
            "document_info": {
                "filename": file.filename,
                "document_type": analysis.document_type,
                "title": analysis.title,
            },
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating course structure: {e!s}",
        )


@router.post("/import/pdf/create-content/{unit_id}")
async def create_content_from_pdf(
    unit_id: str,
    file: UploadFile = File(...),
    content_type: ContentType = ContentType.LECTURE,
    content_category: ContentCategory = ContentCategory.GENERAL,
    week_number: int | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Import PDF and create content item

    Parameters:
    - unit_id: Target unit for the content
    - file: PDF file to import
    - content_type: Type of content to create
    - content_category: Category (pre/in/post class)
    - week_number: Optional week number
    """
    # Verify unit exists and user has access
    unit = db.query(Unit).filter(Unit.id == unit_id, Unit.owner_id == current_user.id).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Process PDF
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50MB limit",
        )

    try:
        # Extract and convert to markdown
        extracted_doc = await pdf_parser_service.extract_from_bytes(contents)
        markdown_content = await pdf_parser_service.convert_to_markdown(extracted_doc)

        # Create content item
        content = Content(
            id=uuid.uuid4(),
            unit_id=unit_id,
            title=extracted_doc.metadata.title or file.filename.replace(".pdf", ""),
            type=content_type.value,
            content_markdown=markdown_content,
            week_number=week_number,
            content_category=content_category.value,
            estimated_duration_minutes=extracted_doc.metadata.page_count * 3,  # Rough estimate
            generation_metadata={
                "source": "pdf_import",
                "filename": file.filename,
                "extraction_method": extracted_doc.extraction_method,
                "page_count": extracted_doc.metadata.page_count,
            },
        )
        db.add(content)
        db.commit()
        db.refresh(content)

        return {
            "status": "success",
            "message": "Content created successfully",
            "content": {
                "id": str(content.id),
                "title": content.title,
                "type": content.type,
                "category": content.content_category,
                "week_number": content.week_number,
            },
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating content: {e!s}",
        )


@router.get("/import/suggestions/{unit_id}")
async def get_import_suggestions(
    unit_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get suggestions for what content to import/create for a unit

    Returns recommendations based on:
    - What content already exists
    - Typical course structure
    - Gaps in current content
    """
    # Verify unit exists and user has access
    unit = db.query(Unit).filter(Unit.id == unit_id, Unit.owner_id == current_user.id).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Check what already exists
    has_outline = (
        db.query(CourseOutline).filter(CourseOutline.unit_id == unit_id).first() is not None
    )

    outcomes_count = (
        db.query(UnitLearningOutcome).filter(UnitLearningOutcome.unit_id == unit_id).count()
    )

    weekly_topics_count = (
        db.query(WeeklyTopic).filter(WeeklyTopic.unit_id == unit_id).count()
    )

    assessments_count = (
        db.query(AssessmentPlan).filter(AssessmentPlan.unit_id == unit_id).count()
    )

    content_count = db.query(Content).filter(Content.unit_id == unit_id).count()

    # Generate suggestions
    suggestions = []

    if not has_outline:
        suggestions.append(
            {
                "priority": "high",
                "type": "course_outline",
                "title": "Import Unit Outline",
                "description": "Start by importing a unit outline PDF to establish course structure",
                "recommended_file_types": ["Unit outline", "Course syllabus", "Study guide"],
            }
        )

    if outcomes_count < 5:
        suggestions.append(
            {
                "priority": "high",
                "type": "learning_outcomes",
                "title": "Add Learning Outcomes",
                "description": f"Currently have {outcomes_count} outcomes. Aim for 5-10 unit learning outcomes.",
                "recommended_action": "Import from unit outline or create manually",
            }
        )

    if weekly_topics_count < 12:
        suggestions.append(
            {
                "priority": "medium",
                "type": "weekly_topics",
                "title": "Complete Weekly Schedule",
                "description": f"Currently have {weekly_topics_count} weeks planned. Most units have 12-13 weeks.",
                "recommended_action": "Import weekly schedule or create topics",
            }
        )

    if assessments_count < 3:
        suggestions.append(
            {
                "priority": "medium",
                "type": "assessments",
                "title": "Add Assessment Plans",
                "description": f"Currently have {assessments_count} assessments. Most units have 3-5 assessments.",
                "recommended_action": "Import assessment briefs or create assessment plans",
            }
        )

    if content_count < weekly_topics_count * 2:
        suggestions.append(
            {
                "priority": "low",
                "type": "content",
                "title": "Add Course Content",
                "description": f"Currently have {content_count} content items. Consider adding lecture notes, worksheets, and activities.",
                "recommended_file_types": ["Lecture slides", "Tutorial guides", "Workshop materials"],
            }
        )

    # Check for specific content gaps
    content_types = (
        db.query(Content.type).filter(Content.unit_id == unit_id).distinct().all()
    )
    existing_types = [ct[0] for ct in content_types]

    if ContentType.SYLLABUS.value not in existing_types:
        suggestions.append(
            {
                "priority": "high",
                "type": "content",
                "subtype": "syllabus",
                "title": "Create Syllabus",
                "description": "No syllabus found. This is essential for students.",
            }
        )

    if ContentType.SCHEDULE.value not in existing_types:
        suggestions.append(
            {
                "priority": "medium",
                "type": "content",
                "subtype": "schedule",
                "title": "Create Schedule",
                "description": "No schedule found. Students need to know weekly topics.",
            }
        )

    return {
        "unit": {"id": unit_id, "name": unit.name},
        "current_state": {
            "has_outline": has_outline,
            "outcomes_count": outcomes_count,
            "weekly_topics_count": weekly_topics_count,
            "assessments_count": assessments_count,
            "content_count": content_count,
            "content_types": existing_types,
        },
        "suggestions": suggestions,
        "next_steps": [
            "1. Import unit outline PDF to establish structure",
            "2. Review and refine extracted learning outcomes",
            "3. Import or create weekly content",
            "4. Add assessment briefs and rubrics",
            "5. Generate student-facing materials",
        ],
    }

