"""
Association tables for many-to-many relationships between entities
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Table,
)

from app.core.database import Base
from app.models.user import GUID

# Material to Unit Learning Outcome mapping
material_ulo_mappings = Table(
    "material_ulo_mappings",
    Base.metadata,
    Column(
        "material_id",
        GUID(),
        ForeignKey("weekly_materials.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "ulo_id",
        GUID(),
        ForeignKey("unit_learning_outcomes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime, nullable=False, default=lambda: datetime.now(UTC)),
    extend_existing=True,
)

# Assessment to Unit Learning Outcome mapping
assessment_ulo_mappings = Table(
    "assessment_ulo_mappings",
    Base.metadata,
    Column(
        "assessment_id",
        GUID(),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "ulo_id",
        GUID(),
        ForeignKey("unit_learning_outcomes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime, nullable=False, default=lambda: datetime.now(UTC)),
    extend_existing=True,
)

# NOTE: wlo_ulo_mappings removed - referenced non-existent weekly_learning_outcomes table
# If weekly learning outcomes are needed in future, create the model first

# Assessment to Material links
assessment_material_links = Table(
    "assessment_material_links",
    Base.metadata,
    Column(
        "assessment_id",
        GUID(),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "material_id",
        GUID(),
        ForeignKey("weekly_materials.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime, nullable=False, default=lambda: datetime.now(UTC)),
    extend_existing=True,
)
