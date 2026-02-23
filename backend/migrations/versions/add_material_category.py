"""add material category column

Revision ID: a1b2c3d4e5f6
Revises: add_sdg_mappings
Create Date: 2026-02-23
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "add_sdg_mappings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "weekly_materials",
        sa.Column("category", sa.String(20), server_default="general", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("weekly_materials", "category")
