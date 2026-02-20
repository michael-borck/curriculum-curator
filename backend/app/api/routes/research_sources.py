"""
Research Sources API routes - CRUD operations for academic source management.

Provides endpoints for:
- Managing research sources (save, update, delete, list)
- Citation formatting in various styles
- Adding citations to content
- Synthesizing content from multiple sources
"""

import json
import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.research_source import (
    CitationStyle,
    ContentCitation,
    ResearchSource,
    SourceType,
)
from app.repositories import content_repo, unit_repo
from app.schemas.research_source import (
    AuthorSchema,
    BulkCitationRequest,
    CitationRequest,
    CitationResponse,
    ContentCitationCreate,
    ContentCitationResponse,
    ReferenceListResponse,
    ResearchSourceCreate,
    ResearchSourceList,
    ResearchSourceResponse,
    ResearchSourceUpdate,
    SaveFromSearchRequest,
    SynthesisRequest,
    SynthesisResponse,
)
from app.schemas.user import UserResponse
from app.services.citation_service import citation_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


def source_to_response(source: ResearchSource) -> ResearchSourceResponse:
    """Convert SQLAlchemy model to Pydantic response."""
    # Convert author dicts to AuthorSchema instances
    authors = [
        AuthorSchema(
            first_name=author.get("first_name", ""),
            last_name=author.get("last_name", ""),
            suffix=author.get("suffix"),
        )
        for author in source.authors
    ]

    return ResearchSourceResponse(
        id=str(source.id),
        user_id=str(source.user_id),
        unit_id=str(source.unit_id) if source.unit_id else None,
        url=source.url,
        title=source.title,
        source_type=SourceType(source.source_type),
        authors=authors,
        publication_date=source.publication_date,
        publisher=source.publisher,
        journal_name=source.journal_name,
        volume=source.volume,
        issue=source.issue,
        pages=source.pages,
        doi=source.doi,
        isbn=source.isbn,
        summary=source.summary,
        key_points=source.key_points,
        academic_score=source.academic_score,
        usage_count=source.usage_count,
        last_used_at=source.last_used_at,
        tags=source.tags,
        notes=source.notes,
        is_favorite=source.is_favorite,
        access_date=source.access_date,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


# =============================================================================
# Research Source CRUD
# =============================================================================


@router.post(
    "", response_model=ResearchSourceResponse, status_code=status.HTTP_201_CREATED
)
async def create_research_source(
    data: ResearchSourceCreate,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Create a new research source.

    The source is associated with the current user and optionally with a unit.
    """
    # Convert authors to JSON
    authors_json = (
        json.dumps([a.model_dump() for a in data.authors]) if data.authors else None
    )
    key_points_json = json.dumps(data.key_points) if data.key_points else None
    tags_json = json.dumps(data.tags) if data.tags else None

    source = ResearchSource(
        user_id=current_user.id,
        unit_id=data.unit_id,
        url=data.url,
        title=data.title,
        source_type=data.source_type.value
        if isinstance(data.source_type, SourceType)
        else data.source_type,
        authors_json=authors_json,
        publication_date=data.publication_date,
        publisher=data.publisher,
        journal_name=data.journal_name,
        volume=data.volume,
        issue=data.issue,
        pages=data.pages,
        doi=data.doi,
        isbn=data.isbn,
        summary=data.summary,
        key_points_json=key_points_json,
        tags_json=tags_json,
        notes=data.notes,
        is_favorite=data.is_favorite,
        access_date=data.access_date or datetime.now().strftime("%Y-%m-%d"),
    )

    db.add(source)
    db.commit()
    db.refresh(source)

    logger.info(
        f"Created research source '{source.title}' for user {current_user.email}"
    )
    return source_to_response(source)


@router.post(
    "/from-search",
    response_model=ResearchSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_from_search(
    data: SaveFromSearchRequest,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Save a research source from search results.

    This is a convenience endpoint that pre-populates fields from search/summarization.
    """
    key_points_json = json.dumps(data.key_points) if data.key_points else None
    tags_json = json.dumps(data.tags) if data.tags else None

    source = ResearchSource(
        user_id=current_user.id,
        unit_id=data.unit_id,
        url=data.url,
        title=data.title,
        source_type=data.source_type.value
        if isinstance(data.source_type, SourceType)
        else data.source_type,
        summary=data.summary,
        key_points_json=key_points_json,
        academic_score=data.academic_score,
        tags_json=tags_json,
        access_date=datetime.now().strftime("%Y-%m-%d"),
    )

    db.add(source)
    db.commit()
    db.refresh(source)

    logger.info(
        f"Saved source from search: '{source.title}' for user {current_user.email}"
    )
    return source_to_response(source)


@router.get("", response_model=ResearchSourceList)
async def list_research_sources(
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
    unit_id: str | None = Query(None, description="Filter by unit ID"),
    favorites_only: bool = Query(False, description="Show only favorites"),
    tag: str | None = Query(None, description="Filter by tag"),
    search: str | None = Query(None, description="Search in title and summary"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List research sources for the current user.

    Supports filtering by unit, favorites, tags, and text search.
    """
    query = db.query(ResearchSource).filter(ResearchSource.user_id == current_user.id)

    if unit_id:
        query = query.filter(ResearchSource.unit_id == unit_id)

    if favorites_only:
        query = query.filter(ResearchSource.is_favorite.is_(True))

    if tag:
        # Search in JSON tags field
        query = query.filter(ResearchSource.tags_json.contains(f'"{tag}"'))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (ResearchSource.title.ilike(search_term))
            | (ResearchSource.summary.ilike(search_term))
        )

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    sources = (
        query.order_by(ResearchSource.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ResearchSourceList(
        sources=[source_to_response(s) for s in sources],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/{source_id}", response_model=ResearchSourceResponse)
async def get_research_source(
    source_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """Get a specific research source by ID."""
    source = (
        db.query(ResearchSource)
        .filter(
            ResearchSource.id == source_id,
            ResearchSource.user_id == current_user.id,
        )
        .first()
    )

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research source not found",
        )

    return source_to_response(source)


@router.patch("/{source_id}", response_model=ResearchSourceResponse)
async def update_research_source(
    source_id: str,
    data: ResearchSourceUpdate,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """Update a research source."""
    source = (
        db.query(ResearchSource)
        .filter(
            ResearchSource.id == source_id,
            ResearchSource.user_id == current_user.id,
        )
        .first()
    )

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research source not found",
        )

    # Update fields if provided
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "authors" and value is not None:
            source.authors_json = json.dumps(
                [a.model_dump() if hasattr(a, "model_dump") else a for a in value]
            )
        elif field == "key_points" and value is not None:
            source.key_points_json = json.dumps(value)
        elif field == "tags" and value is not None:
            source.tags_json = json.dumps(value)
        elif field == "source_type" and value is not None:
            source.source_type = value.value if isinstance(value, SourceType) else value
        elif hasattr(source, field):
            setattr(source, field, value)

    db.commit()
    db.refresh(source)

    logger.info(f"Updated research source '{source.title}'")
    return source_to_response(source)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research_source(
    source_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """Delete a research source."""
    source = (
        db.query(ResearchSource)
        .filter(
            ResearchSource.id == source_id,
            ResearchSource.user_id == current_user.id,
        )
        .first()
    )

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research source not found",
        )

    db.delete(source)
    db.commit()

    logger.info(f"Deleted research source '{source.title}'")


@router.post("/{source_id}/favorite", response_model=ResearchSourceResponse)
async def toggle_favorite(
    source_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """Toggle favorite status for a research source."""
    source = (
        db.query(ResearchSource)
        .filter(
            ResearchSource.id == source_id,
            ResearchSource.user_id == current_user.id,
        )
        .first()
    )

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research source not found",
        )

    source.is_favorite = not source.is_favorite
    db.commit()
    db.refresh(source)

    return source_to_response(source)


# =============================================================================
# Citation Formatting
# =============================================================================


@router.post("/citations/format", response_model=CitationResponse)
async def format_citation(
    data: CitationRequest,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """Format a citation for a research source."""
    source = (
        db.query(ResearchSource)
        .filter(
            ResearchSource.id == data.source_id,
            ResearchSource.user_id == current_user.id,
        )
        .first()
    )

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research source not found",
        )

    full_citation = citation_service.format_citation(source, data.style)
    in_text = citation_service.format_in_text_citation(source, data.style)

    return CitationResponse(
        source_id=str(source.id),
        style=data.style,
        full_citation=full_citation,
        in_text_citation=in_text,
    )


@router.post("/citations/format-bulk", response_model=ReferenceListResponse)
async def format_reference_list(
    data: BulkCitationRequest,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """Format a reference list from multiple sources."""
    sources = (
        db.query(ResearchSource)
        .filter(
            ResearchSource.id.in_(data.source_ids),
            ResearchSource.user_id == current_user.id,
        )
        .all()
    )

    if len(sources) != len(data.source_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more sources not found",
        )

    reference_list = citation_service.format_reference_list(sources, data.style)

    citations = [
        CitationResponse(
            source_id=str(source.id),
            style=data.style,
            full_citation=citation_service.format_citation(source, data.style),
            in_text_citation=citation_service.format_in_text_citation(
                source, data.style
            ),
        )
        for source in sources
    ]

    return ReferenceListResponse(
        style=data.style,
        reference_list=reference_list,
        citations=citations,
    )


# =============================================================================
# Content Citations
# =============================================================================


@router.post(
    "/content/{content_id}/citations",
    response_model=ContentCitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_citation_to_content(
    content_id: str,
    data: ContentCitationCreate,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """Add a citation from a research source to content."""
    # Verify content ownership
    content = content_repo.get_content_by_id(db, content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    unit = unit_repo.get_unit_by_id(db, content.unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found or access denied",
        )

    # Verify source ownership
    source = (
        db.query(ResearchSource)
        .filter(
            ResearchSource.id == data.source_id,
            ResearchSource.user_id == current_user.id,
        )
        .first()
    )

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research source not found",
        )

    # Format citation
    full_citation = citation_service.format_citation(source, data.citation_style)
    in_text = citation_service.format_in_text_citation(source, data.citation_style)

    # Create citation link
    citation = ContentCitation(
        content_id=content_id,
        source_id=data.source_id,
        citation_style=data.citation_style.value,
        citation_text=full_citation,
        in_text_citation=in_text,
        position_start=data.position_start,
        position_end=data.position_end,
    )

    db.add(citation)

    # Update source usage
    source.usage_count += 1
    source.last_used_at = datetime.now()

    db.commit()
    db.refresh(citation)

    return ContentCitationResponse(
        id=str(citation.id),
        content_id=content_id,
        source_id=data.source_id,
        citation_style=data.citation_style,
        citation_text=full_citation,
        in_text_citation=in_text,
        position_start=data.position_start,
        position_end=data.position_end,
        created_at=citation.created_at,
        source_title=source.title,
        source_url=source.url,
    )


@router.get(
    "/content/{content_id}/citations", response_model=list[ContentCitationResponse]
)
async def list_content_citations(
    content_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """List all citations for a piece of content."""
    # Verify content ownership
    content = content_repo.get_content_by_id(db, content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    unit = unit_repo.get_unit_by_id(db, content.unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found or access denied",
        )

    citations = (
        db.query(ContentCitation).filter(ContentCitation.content_id == content_id).all()
    )

    result = []
    for cit in citations:
        source = (
            db.query(ResearchSource).filter(ResearchSource.id == cit.source_id).first()
        )
        result.append(
            ContentCitationResponse(
                id=str(cit.id),
                content_id=content_id,
                source_id=str(cit.source_id),
                citation_style=CitationStyle(cit.citation_style),
                citation_text=cit.citation_text,
                in_text_citation=cit.in_text_citation,
                position_start=cit.position_start,
                position_end=cit.position_end,
                created_at=cit.created_at,
                source_title=source.title if source else None,
                source_url=source.url if source else None,
            )
        )

    return result


@router.delete(
    "/content/{content_id}/citations/{citation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_citation_from_content(
    content_id: str,
    citation_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """Remove a citation from content."""
    # Verify content ownership
    content = content_repo.get_content_by_id(db, content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    unit = unit_repo.get_unit_by_id(db, content.unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found or access denied",
        )

    citation = (
        db.query(ContentCitation)
        .filter(
            ContentCitation.id == citation_id,
            ContentCitation.content_id == content_id,
        )
        .first()
    )

    if not citation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citation not found",
        )

    db.delete(citation)
    db.commit()


# =============================================================================
# Synthesis (Multi-source content generation)
# =============================================================================


@router.post("/synthesize", response_model=SynthesisResponse)
async def synthesize_from_sources(
    data: SynthesisRequest,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Synthesize content from multiple research sources.

    Uses LLM to create cohesive content with proper citations.
    """
    # Get all sources
    sources = (
        db.query(ResearchSource)
        .filter(
            ResearchSource.id.in_(data.source_ids),
            ResearchSource.user_id == current_user.id,
        )
        .all()
    )

    if len(sources) != len(data.source_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more sources not found",
        )

    # Build source context for LLM
    source_context = []
    for i, source in enumerate(sources, 1):
        in_text = citation_service.format_in_text_citation(source, data.citation_style)
        context = f"""
Source {i}: {source.title}
Citation key: {in_text}
Summary: {source.summary or "No summary available"}
Key Points: {", ".join(source.key_points) if source.key_points else "None"}
"""
        source_context.append(context)

    prompt = f"""Synthesize the following sources into a cohesive piece of content for: {data.purpose}

Topic: {data.topic}
Target word count: {data.word_count} words

Sources:
{"".join(source_context)}

Instructions:
1. Create well-structured, educational content that synthesizes insights from all sources
2. {"Include in-text citations using the citation keys provided (e.g., (Smith, 2024))" if data.include_citations else "Do not include citations"}
3. Ensure the content flows naturally and serves the stated purpose
4. Use clear, professional academic language appropriate for university-level content
5. Do not simply summarize each source separately - integrate the information thematically

Write the synthesized content:"""

    try:
        result = await llm_service.generate_text(
            prompt=prompt,
            max_tokens=data.word_count * 2,  # Rough token estimate
            stream=False,  # Don't stream for synthesis
        )
        # Result should be a string when stream=False
        synthesized_content = str(result) if not isinstance(result, str) else result
    except Exception:
        logger.exception("LLM synthesis failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to synthesize content",
        )

    # Format reference list
    reference_list = citation_service.format_reference_list(
        sources, data.citation_style
    )

    # Update usage counts
    for source in sources:
        source.usage_count += 1
        source.last_used_at = datetime.now()
    db.commit()

    # Count words in synthesized content
    word_count = len(synthesized_content.split())

    return SynthesisResponse(
        content=synthesized_content,
        reference_list=reference_list,
        sources_used=[str(s.id) for s in sources],
        word_count=word_count,
    )
