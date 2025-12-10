"""add_historical_audit_reviews

Revision ID: f83e4032d4e2
Revises: 989ceebf408f
Create Date: 2025-12-10 08:21:34.165017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f83e4032d4e2'
down_revision: Union[str, None] = '989ceebf408f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create recipients table
    op.create_table(
        'recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('acronym', sa.String(length=50), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=2), nullable=True),
        sa.Column('region_number', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('recipient_id')
    )
    op.create_index('ix_recipients_acronym', 'recipients', ['acronym'])
    op.create_index('ix_recipients_name', 'recipients', ['name'])
    op.create_index('ix_recipients_recipient_id', 'recipients', ['recipient_id'])
    op.create_index('ix_recipients_region_number', 'recipients', ['region_number'])
    op.create_index('ix_recipients_state', 'recipients', ['state'])

    # Create audit_reviews table
    op.create_table(
        'audit_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('fiscal_year', sa.String(length=10), nullable=False),
        sa.Column('review_type', sa.String(length=100), nullable=False),
        sa.Column('report_date', sa.Date(), nullable=True),
        sa.Column('site_visit_start_date', sa.Date(), nullable=True),
        sa.Column('site_visit_end_date', sa.Date(), nullable=True),
        sa.Column('exit_conference_date', sa.Date(), nullable=True),
        sa.Column('exit_conference_format', sa.String(length=50), nullable=True),
        sa.Column('lead_reviewer_name', sa.String(length=255), nullable=True),
        sa.Column('contractor_name', sa.String(length=255), nullable=True),
        sa.Column('lead_reviewer_phone', sa.String(length=50), nullable=True),
        sa.Column('lead_reviewer_email', sa.String(length=255), nullable=True),
        sa.Column('fta_pm_name', sa.String(length=255), nullable=True),
        sa.Column('fta_pm_title', sa.String(length=255), nullable=True),
        sa.Column('fta_pm_phone', sa.String(length=50), nullable=True),
        sa.Column('fta_pm_email', sa.String(length=255), nullable=True),
        sa.Column('total_deficiencies', sa.Integer(), nullable=True),
        sa.Column('total_areas_reviewed', sa.Integer(), nullable=True),
        sa.Column('review_status', sa.String(length=50), nullable=True),
        sa.Column('source_file', sa.String(length=500), nullable=True),
        sa.Column('extracted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recipient_id'], ['recipients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_recipient_fiscal_year', 'audit_reviews', ['recipient_id', 'fiscal_year'])
    op.create_index('idx_review_type_fiscal_year', 'audit_reviews', ['review_type', 'fiscal_year'])
    op.create_index('ix_audit_reviews_fiscal_year', 'audit_reviews', ['fiscal_year'])
    op.create_index('ix_audit_reviews_recipient_id', 'audit_reviews', ['recipient_id'])
    op.create_index('ix_audit_reviews_review_type', 'audit_reviews', ['review_type'])

    # Create historical_assessments table
    op.create_table(
        'historical_assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('audit_review_id', sa.Integer(), nullable=False),
        sa.Column('section_id', sa.Integer(), nullable=True),
        sa.Column('review_area', sa.String(length=255), nullable=False),
        sa.Column('finding', sa.String(length=10), nullable=False),
        sa.Column('deficiency_code', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('corrective_action', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('date_closed', sa.Date(), nullable=True),
        sa.Column('narrative_text', sa.Text(), nullable=True),
        sa.Column('reviewer_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['audit_review_id'], ['audit_reviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['compliance_sections.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_section', 'historical_assessments', ['audit_review_id', 'section_id'])
    op.create_index('idx_deficiency_code', 'historical_assessments', ['deficiency_code'])
    op.create_index('idx_finding_type', 'historical_assessments', ['finding'])
    op.create_index('ix_historical_assessments_audit_review_id', 'historical_assessments', ['audit_review_id'])
    op.create_index('ix_historical_assessments_finding', 'historical_assessments', ['finding'])
    op.create_index('ix_historical_assessments_review_area', 'historical_assessments', ['review_area'])
    op.create_index('ix_historical_assessments_section_id', 'historical_assessments', ['section_id'])

    # Create lessons_learned table
    op.create_table(
        'lessons_learned',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('audit_review_id', sa.Integer(), nullable=False),
        sa.Column('section_id', sa.Integer(), nullable=True),
        sa.Column('lesson_type', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('applicability', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['audit_review_id'], ['audit_reviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['compliance_sections.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_section_lesson', 'lessons_learned', ['audit_review_id', 'section_id'])
    op.create_index('idx_category', 'lessons_learned', ['category'])
    op.create_index('idx_lesson_type', 'lessons_learned', ['lesson_type'])
    op.create_index('ix_lessons_learned_audit_review_id', 'lessons_learned', ['audit_review_id'])
    op.create_index('ix_lessons_learned_category', 'lessons_learned', ['category'])
    op.create_index('ix_lessons_learned_lesson_type', 'lessons_learned', ['lesson_type'])
    op.create_index('ix_lessons_learned_section_id', 'lessons_learned', ['section_id'])


def downgrade() -> None:
    op.drop_table('lessons_learned')
    op.drop_table('historical_assessments')
    op.drop_table('audit_reviews')
    op.drop_table('recipients')
