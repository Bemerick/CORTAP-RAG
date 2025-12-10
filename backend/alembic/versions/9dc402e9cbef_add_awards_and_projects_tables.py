"""add_awards_and_projects_tables

Revision ID: 9dc402e9cbef
Revises: f83e4032d4e2
Create Date: 2025-12-10 10:44:47.741743

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9dc402e9cbef'
down_revision: Union[str, None] = 'f83e4032d4e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create awards table
    op.create_table(
        'awards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('audit_review_id', sa.Integer(), nullable=False),
        sa.Column('award_number', sa.String(length=100), nullable=False),
        sa.Column('award_year', sa.String(length=10), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['audit_review_id'], ['audit_reviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_awards_audit_review_id', 'awards', ['audit_review_id'])
    op.create_index('ix_awards_award_number', 'awards', ['award_number'])

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('audit_review_id', sa.Integer(), nullable=False),
        sa.Column('project_type', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('completion_date', sa.String(length=50), nullable=True),
        sa.Column('funding_sources', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['audit_review_id'], ['audit_reviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_type', 'projects', ['project_type'])
    op.create_index('ix_projects_audit_review_id', 'projects', ['audit_review_id'])


def downgrade() -> None:
    op.drop_table('projects')
    op.drop_table('awards')
