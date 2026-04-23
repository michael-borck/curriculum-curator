"""Pydantic schemas for CLO Sets."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import CamelModel


class CLOItemBase(CamelModel):
    code: str = Field(..., min_length=1, max_length=20, description="e.g. CLO1")
    description: str = Field(..., min_length=1)
    order_index: int = Field(default=0, ge=0)


class CLOItemCreate(CLOItemBase):
    pass


class CLOItemUpdate(CamelModel):
    code: str | None = Field(None, min_length=1, max_length=20)
    description: str | None = Field(None, min_length=1)
    order_index: int | None = Field(None, ge=0)


class CLOItemResponse(CLOItemBase):
    id: str
    clo_set_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CLOItemReorder(BaseModel):
    item_ids: list[str] = Field(..., min_length=1)


# ── CLO Set ──────────────────────────────────────────────────


class CLOSetBase(CamelModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    program_code: str | None = Field(None, max_length=20)


class CLOSetCreate(CLOSetBase):
    pass


class CLOSetUpdate(CamelModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    program_code: str | None = Field(None, max_length=20)


class CLOSetResponse(CLOSetBase):
    id: str
    user_id: str
    items: list[CLOItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CLOSetSummary(CamelModel):
    """Lightweight response — no items list."""

    id: str
    name: str
    program_code: str | None
    item_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Mappings ──────────────────────────────────────────────────


class ULOCLOMappingCreate(CamelModel):
    clo_item_id: str
    is_ai_suggested: bool = False
    notes: str | None = None


class ULOCLOMappingResponse(CamelModel):
    id: str
    ulo_id: str
    clo_item_id: str
    is_ai_suggested: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BulkULOCLOMappingCreate(CamelModel):
    clo_item_ids: list[str]
    is_ai_suggested: bool = False


class CLOSuggestionPair(CamelModel):
    ulo_id: str
    clo_item_id: str


class CLOSuggestionsResponse(CamelModel):
    suggestions: list[CLOSuggestionPair]
    message: str = ""
