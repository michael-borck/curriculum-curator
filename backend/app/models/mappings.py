"""
Association tables for many-to-many relationships between entities
"""

from datetime import datetime

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
    Column("material_id", GUID(), ForeignKey("weekly_materials.id", ondelete="CASCADE"), primary_key=True),
    Column("ulo_id", GUID(), ForeignKey("unit_learning_outcomes.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

# Assessment to Unit Learning Outcome mapping
assessment_ulo_mappings = Table(
    "assessment_ulo_mappings",
    Base.metadata,
    Column("assessment_id", GUID(), ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True),
    Column("ulo_id", GUID(), ForeignKey("unit_learning_outcomes.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

# Weekly Learning Outcome to Unit Learning Outcome mapping
wlo_ulo_mappings = Table(
    "wlo_ulo_mappings",
    Base.metadata,
    Column("wlo_id", GUID(), ForeignKey("weekly_learning_outcomes.id", ondelete="CASCADE"), primary_key=True),
    Column("ulo_id", GUID(), ForeignKey("unit_learning_outcomes.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

# Assessment to Material links
assessment_material_links = Table(
    "assessment_material_links",
    Base.metadata,
    Column("assessment_id", GUID(), ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True),
    Column("material_id", GUID(), ForeignKey("weekly_materials.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)
