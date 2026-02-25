"""
CRUD routes for prompt templates.

Supports system, custom (user-owned), and public templates with
per-user visibility toggles stored in teaching_preferences.
"""

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.prompt_template import PromptTemplate
from app.models.user import User as UserModel
from app.schemas.prompt_template import (
    PromptTemplateCreate,
    PromptTemplateListItem,
    PromptTemplateResponse,
    PromptTemplateUpdate,
    TemplateVariable,
)
from app.schemas.user import UserResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hidden_ids(user: UserResponse) -> set[str]:
    """Return set of prompt-template IDs the user has hidden."""
    prefs = user.teaching_preferences or {}
    return set(prefs.get("hidden_prompt_template_ids", []))


def _parse_variables(raw: str | None) -> list[TemplateVariable] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return [TemplateVariable(**v) for v in data]
    except (json.JSONDecodeError, TypeError):
        return None


def _parse_tags(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _to_response(t: PromptTemplate) -> PromptTemplateResponse:
    return PromptTemplateResponse(
        id=str(t.id),
        name=t.name,
        description=t.description,
        type=t.type,
        template_content=t.template_content,
        variables=_parse_variables(t.variables),
        status=t.status,
        owner_id=t.owner_id,
        is_system=t.is_system,
        is_public=t.is_public,
        version=t.version,
        usage_count=t.usage_count,
        last_used=t.last_used,
        tags=_parse_tags(t.tags),
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _to_list_item(t: PromptTemplate) -> PromptTemplateListItem:
    return PromptTemplateListItem(
        id=str(t.id),
        name=t.name,
        description=t.description,
        type=t.type,
        is_system=t.is_system,
        is_public=t.is_public,
        usage_count=t.usage_count,
        variables=_parse_variables(t.variables),
        tags=_parse_tags(t.tags),
    )


# ---------------------------------------------------------------------------
# List & Get
# ---------------------------------------------------------------------------


@router.get("", response_model=list[PromptTemplateListItem])
async def list_prompt_templates(
    include_hidden: bool = Query(False),
    template_type: str | None = Query(None, alias="type"),
    current_user: UserResponse = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> list[PromptTemplateListItem]:
    """List visible prompt templates (system + own + public, minus hidden)."""
    from sqlalchemy import or_  # noqa: PLC0415

    query = db.query(PromptTemplate).filter(PromptTemplate.status == "active")

    # Visibility: system OR owned by user OR public
    query = query.filter(
        or_(
            PromptTemplate.is_system.is_(True),
            PromptTemplate.owner_id == current_user.id,
            PromptTemplate.is_public.is_(True),
        )
    )

    if template_type:
        query = query.filter(PromptTemplate.type == template_type)

    templates = query.order_by(PromptTemplate.name).all()

    # Filter out hidden
    if not include_hidden:
        hidden = _hidden_ids(current_user)
        templates = [t for t in templates if str(t.id) not in hidden]

    return [_to_list_item(t) for t in templates]


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: str,
    current_user: UserResponse = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> PromptTemplateResponse:
    """Get a single prompt template."""
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Access check: system, public, or owned
    if not (
        template.is_system or template.is_public or template.owner_id == current_user.id
    ):
        raise HTTPException(status_code=404, detail="Template not found")

    return _to_response(template)


# ---------------------------------------------------------------------------
# Create & Copy
# ---------------------------------------------------------------------------


@router.post("", response_model=PromptTemplateResponse, status_code=201)
async def create_prompt_template(
    data: PromptTemplateCreate,
    current_user: UserResponse = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> PromptTemplateResponse:
    """Create a custom prompt template."""
    template = PromptTemplate(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        type=data.type,
        template_content=data.template_content,
        variables=json.dumps([v.model_dump() for v in data.variables])
        if data.variables
        else None,
        tags=json.dumps(data.tags) if data.tags else None,
        owner_id=current_user.id,
        is_system=False,
        is_public=False,
        status="active",
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _to_response(template)


@router.post(
    "/{template_id}/copy", response_model=PromptTemplateResponse, status_code=201
)
async def copy_prompt_template(
    template_id: str,
    current_user: UserResponse = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> PromptTemplateResponse:
    """Copy a system or public template into the user's own custom list."""
    original = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Template not found")

    if not (
        original.is_system or original.is_public or original.owner_id == current_user.id
    ):
        raise HTTPException(status_code=404, detail="Template not found")

    copy = PromptTemplate(
        id=str(uuid.uuid4()),
        name=f"{original.name} (Copy)",
        description=original.description,
        type=original.type,
        template_content=original.template_content,
        variables=original.variables,
        tags=original.tags,
        owner_id=current_user.id,
        is_system=False,
        is_public=False,
        parent_id=str(original.id),
        status="active",
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return _to_response(copy)


# ---------------------------------------------------------------------------
# Update & Delete
# ---------------------------------------------------------------------------


@router.put("/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: str,
    data: PromptTemplateUpdate,
    current_user: UserResponse = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> PromptTemplateResponse:
    """Update a custom template (owner only)."""
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.is_system or template.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot edit system or other users' templates",
        )

    if data.name is not None:
        template.name = data.name
    if data.description is not None:
        template.description = data.description
    if data.type is not None:
        template.type = data.type
    if data.template_content is not None:
        template.template_content = data.template_content
    if data.variables is not None:
        template.variables = json.dumps([v.model_dump() for v in data.variables])
    if data.tags is not None:
        template.tags = json.dumps(data.tags)
    if data.status is not None:
        template.status = data.status
    if data.is_public is not None:
        template.is_public = data.is_public

    db.commit()
    db.refresh(template)
    return _to_response(template)


@router.delete("/{template_id}", status_code=204)
async def delete_prompt_template(
    template_id: str,
    current_user: UserResponse = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> None:
    """Delete a custom template (owner only)."""
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system templates",
        )
    if template.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete other users' templates",
        )

    db.delete(template)
    db.commit()


# ---------------------------------------------------------------------------
# Visibility & Usage
# ---------------------------------------------------------------------------


@router.post("/{template_id}/toggle-visibility")
async def toggle_visibility(
    template_id: str,
    current_user: UserResponse = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> dict[str, bool]:
    """Hide or unhide a prompt template for this user."""
    # Verify template exists
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Update user's hidden list
    user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prefs: dict = user.teaching_preferences or {}  # pyright: ignore[reportExplicitAny]
    hidden: list[str] = prefs.get("hidden_prompt_template_ids", [])

    is_hidden: bool
    if template_id in hidden:
        hidden.remove(template_id)
        is_hidden = False
    else:
        hidden.append(template_id)
        is_hidden = True

    prefs["hidden_prompt_template_ids"] = hidden
    user.teaching_preferences = prefs
    db.commit()

    return {"hidden": is_hidden}


@router.post("/{template_id}/increment-usage")
async def increment_usage(
    template_id: str,
    current_user: UserResponse = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> dict[str, int]:
    """Bump usage counter for a template."""
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template.usage_count = int(template.usage_count) + 1
    template.last_used = datetime.utcnow()
    db.commit()

    return {"usage_count": template.usage_count}


# ---------------------------------------------------------------------------
# Admin: create system template
# ---------------------------------------------------------------------------


@router.post("/admin/system", response_model=PromptTemplateResponse, status_code=201)
async def create_system_template(
    data: PromptTemplateCreate,
    current_user: UserResponse = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
) -> PromptTemplateResponse:
    """Create a system template (admin only)."""
    template = PromptTemplate(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        type=data.type,
        template_content=data.template_content,
        variables=json.dumps([v.model_dump() for v in data.variables])
        if data.variables
        else None,
        tags=json.dumps(data.tags) if data.tags else None,
        owner_id=None,
        is_system=True,
        is_public=True,
        status="active",
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _to_response(template)
