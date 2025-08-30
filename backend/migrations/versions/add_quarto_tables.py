"""Add Quarto settings and presets tables

Revision ID: add_quarto_tables
Revises: 340f082dc2fc
Create Date: 2024-12-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_quarto_tables'
down_revision = '340f082dc2fc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create quarto_presets table
    op.create_table(
        'quarto_presets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('yaml_content', sa.Text(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quarto_presets_id'), 'quarto_presets', ['id'], unique=False)
    op.create_index(op.f('ix_quarto_presets_user_id'), 'quarto_presets', ['user_id'], unique=False)

    # Create content_quarto_settings table
    op.create_table(
        'content_quarto_settings',
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('simple_settings', sa.JSON(), nullable=True),
        sa.Column('advanced_yaml', sa.Text(), nullable=True),
        sa.Column('active_mode', sa.String(length=20), nullable=True),
        sa.Column('active_preset', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ),
        sa.PrimaryKeyConstraint('content_id')
    )
    op.create_index(op.f('ix_content_quarto_settings_content_id'), 'content_quarto_settings', ['content_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_content_quarto_settings_content_id'), table_name='content_quarto_settings')
    op.drop_table('content_quarto_settings')
    op.drop_index(op.f('ix_quarto_presets_user_id'), table_name='quarto_presets')
    op.drop_index(op.f('ix_quarto_presets_id'), table_name='quarto_presets')
    op.drop_table('quarto_presets')