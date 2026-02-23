"""add import provenance column

Revision ID: add_import_provenance
Revises: a1b2c3d4e5f6
Create Date: 2026-02-24
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_import_provenance"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "units",
        sa.Column("import_provenance", sa.JSON, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("units", "import_provenance")
