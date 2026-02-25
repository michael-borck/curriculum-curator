"""
Pydantic schemas for prompt template CRUD operations
"""

from datetime import datetime

from pydantic import Field

from app.schemas.base import CamelModel


class TemplateVariable(CamelModel):
    """Schema for a template variable definition"""

    name: str
    label: str
    default: str | None = None


class PromptTemplateCreate(CamelModel):
    """Schema for creating a custom prompt template"""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    type: str = "custom"
    template_content: str = Field(..., min_length=1)
    variables: list[TemplateVariable] | None = None
    tags: list[str] | None = None


class PromptTemplateUpdate(CamelModel):
    """Schema for updating a prompt template"""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    type: str | None = None
    template_content: str | None = None
    variables: list[TemplateVariable] | None = None
    tags: list[str] | None = None
    status: str | None = None
    is_public: bool | None = None


class PromptTemplateResponse(CamelModel):
    """Full prompt template response"""

    id: str
    name: str
    description: str | None = None
    type: str
    template_content: str
    variables: list[TemplateVariable] | None = None
    status: str
    owner_id: str | None = None
    is_system: bool
    is_public: bool
    version: int
    usage_count: int
    last_used: datetime | None = None
    tags: list[str] | None = None
    created_at: datetime | str
    updated_at: datetime | str | None = None


class PromptTemplateListItem(CamelModel):
    """Compact prompt template for list views"""

    id: str
    name: str
    description: str | None = None
    type: str
    is_system: bool
    is_public: bool
    usage_count: int
    variables: list[TemplateVariable] | None = None
    tags: list[str] | None = None
