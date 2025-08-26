"""add_missing_unit_structure_tables

Revision ID: 916afda7d070
Revises: 340f082dc2fc
Create Date: 2025-08-24 15:01:40.019299

"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime
from app.models.user import GUID

# revision identifiers, used by Alembic.
revision = "916afda7d070"
down_revision = "340f082dc2fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create weekly_materials table (doesn't exist yet)
    op.create_table(
        "weekly_materials",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("unit_id", GUID(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_weekly_materials_unit_id"),
        "weekly_materials",
        ["unit_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_weekly_materials_week_number"),
        "weekly_materials",
        ["week_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_weekly_materials_type"), "weekly_materials", ["type"], unique=False
    )

    # Create assessments table (doesn't exist yet)
    op.create_table(
        "assessments",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("unit_id", GUID(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specification", sa.Text(), nullable=True),
        sa.Column("release_week", sa.Integer(), nullable=True),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("due_week", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("duration", sa.String(100), nullable=True),
        sa.Column("rubric", sa.JSON(), nullable=True),
        sa.Column("questions", sa.Integer(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("group_work", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("submission_type", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assessments_unit_id"), "assessments", ["unit_id"], unique=False
    )
    op.create_index(op.f("ix_assessments_type"), "assessments", ["type"], unique=False)
    op.create_index(
        op.f("ix_assessments_category"), "assessments", ["category"], unique=False
    )

    # Create local_learning_outcomes table
    op.create_table(
        "local_learning_outcomes",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("material_id", GUID(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["material_id"], ["weekly_materials.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_local_learning_outcomes_material_id"),
        "local_learning_outcomes",
        ["material_id"],
        unique=False,
    )

    # Create weekly_learning_outcomes table
    op.create_table(
        "weekly_learning_outcomes",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("unit_id", GUID(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_weekly_learning_outcomes_unit_id"),
        "weekly_learning_outcomes",
        ["unit_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_weekly_learning_outcomes_week_number"),
        "weekly_learning_outcomes",
        ["week_number"],
        unique=False,
    )

    # Create assessment_learning_outcomes table
    op.create_table(
        "assessment_learning_outcomes",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("assessment_id", GUID(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"], ["assessments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assessment_learning_outcomes_assessment_id"),
        "assessment_learning_outcomes",
        ["assessment_id"],
        unique=False,
    )

    # Create mapping tables

    # Material to ULO mappings
    op.create_table(
        "material_ulo_mappings",
        sa.Column("material_id", GUID(), nullable=False),
        sa.Column("ulo_id", GUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["material_id"], ["weekly_materials.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["ulo_id"], ["unit_learning_outcomes.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("material_id", "ulo_id"),
    )

    # Assessment to ULO mappings
    op.create_table(
        "assessment_ulo_mappings",
        sa.Column("assessment_id", GUID(), nullable=False),
        sa.Column("ulo_id", GUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"], ["assessments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["ulo_id"], ["unit_learning_outcomes.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("assessment_id", "ulo_id"),
    )

    # Weekly Learning Outcome to ULO mappings
    op.create_table(
        "wlo_ulo_mappings",
        sa.Column("wlo_id", GUID(), nullable=False),
        sa.Column("ulo_id", GUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["wlo_id"], ["weekly_learning_outcomes.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["ulo_id"], ["unit_learning_outcomes.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("wlo_id", "ulo_id"),
    )

    # Assessment to Material links
    op.create_table(
        "assessment_material_links",
        sa.Column("assessment_id", GUID(), nullable=False),
        sa.Column("material_id", GUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"], ["assessments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["material_id"], ["weekly_materials.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("assessment_id", "material_id"),
    )


def downgrade() -> None:
    # Drop mapping tables first
    op.drop_table("assessment_material_links")
    op.drop_table("wlo_ulo_mappings")
    op.drop_table("assessment_ulo_mappings")
    op.drop_table("material_ulo_mappings")

    # Drop learning outcome tables
    op.drop_table("assessment_learning_outcomes")
    op.drop_table("weekly_learning_outcomes")
    op.drop_table("local_learning_outcomes")

    # Drop main tables
    op.drop_table("assessments")
    op.drop_table("weekly_materials")
