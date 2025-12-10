"""SQLAlchemy ORM models for FTA compliance data."""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, Date, Index, Numeric
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ComplianceSection(Base):
    """Top-level compliance sections (Legal, Title VI, ADA, etc.)."""

    __tablename__ = 'compliance_sections'

    id = Column(Integer, primary_key=True)
    section_code = Column(String(50), unique=True, nullable=False, index=True)
    section_name = Column(String(255), nullable=False)
    page_range = Column(String(50))
    purpose = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    questions = relationship("ComplianceQuestion", back_populates="section", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ComplianceSection(code='{self.section_code}', name='{self.section_name}')>"


class ComplianceQuestion(Base):
    """Compliance questions (sub_areas in JSON)."""

    __tablename__ = 'compliance_questions'

    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey('compliance_sections.id', ondelete='CASCADE'), nullable=False)
    question_code = Column(String(50), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    basic_requirement = Column(Text)
    applicability = Column(Text, index=True)
    detailed_explanation = Column(Text)
    instructions_for_reviewer = Column(Text)
    question_order = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    section = relationship("ComplianceSection", back_populates="questions")
    indicators = relationship("ComplianceIndicator", back_populates="question", cascade="all, delete-orphan")
    deficiencies = relationship("ComplianceDeficiency", back_populates="question", cascade="all, delete-orphan")

    # Composite unique constraint
    __table_args__ = (
        Index('idx_section_questions', 'section_id'),
        Index('idx_question_order', 'section_id', 'question_order'),
        Index('uq_section_question_code', 'section_id', 'question_code', unique=True),
    )

    def __repr__(self):
        return f"<ComplianceQuestion(code='{self.question_code}', text='{self.question_text[:50]}...')>"


class ComplianceIndicator(Base):
    """Indicators of compliance (lettered items: a, b, c, etc.)."""

    __tablename__ = 'compliance_indicators'

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('compliance_questions.id', ondelete='CASCADE'), nullable=False)
    letter = Column(String(5), nullable=False)
    indicator_text = Column(Text, nullable=False)
    indicator_order = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    question = relationship("ComplianceQuestion", back_populates="indicators")

    # Indexes and constraints
    __table_args__ = (
        Index('idx_question_indicators', 'question_id'),
        Index('idx_indicator_order', 'question_id', 'indicator_order'),
        Index('uq_question_letter', 'question_id', 'letter', unique=True),
    )

    def __repr__(self):
        return f"<ComplianceIndicator(letter='{self.letter}', text='{self.indicator_text[:50]}...')>"


class ComplianceDeficiency(Base):
    """Potential deficiency determinations and corrective actions."""

    __tablename__ = 'compliance_deficiencies'

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('compliance_questions.id', ondelete='CASCADE'), nullable=False)
    deficiency_code = Column(String(50), nullable=False, index=True)
    deficiency_title = Column(Text, nullable=False)
    determination = Column(Text, nullable=False)
    corrective_action = Column(Text)
    deficiency_order = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    question = relationship("ComplianceQuestion", back_populates="deficiencies")

    # Indexes and constraints
    __table_args__ = (
        Index('idx_question_deficiencies', 'question_id'),
        Index('uq_question_deficiency_code', 'question_id', 'deficiency_code', unique=True),
    )

    def __repr__(self):
        return f"<ComplianceDeficiency(code='{self.deficiency_code}', title='{self.deficiency_title[:50]}...')>"


# ============================================================================
# Historical Audit Review Models
# ============================================================================

class Recipient(Base):
    """Transit agencies/recipients that undergo FTA compliance reviews."""

    __tablename__ = 'recipients'

    id = Column(Integer, primary_key=True)
    recipient_id = Column(String(50), unique=True, nullable=False, index=True)  # FTA ID (e.g., "1337")
    name = Column(String(255), nullable=False, index=True)
    acronym = Column(String(50), nullable=False, index=True)
    city = Column(String(100))
    state = Column(String(2), index=True)  # Two-letter state code
    region_number = Column(Integer, index=True)  # FTA Region 1-10
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    audit_reviews = relationship("AuditReview", back_populates="recipient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Recipient(id='{self.recipient_id}', name='{self.name}', acronym='{self.acronym}')>"


class AuditReview(Base):
    """Historical FTA compliance audit reviews."""

    __tablename__ = 'audit_reviews'

    id = Column(Integer, primary_key=True)
    recipient_id = Column(Integer, ForeignKey('recipients.id', ondelete='CASCADE'), nullable=False, index=True)

    # Review identification
    fiscal_year = Column(String(10), nullable=False, index=True)  # e.g., "FY2023"
    review_type = Column(String(100), nullable=False, index=True)  # TR, SMR, Combined
    report_date = Column(Date)
    site_visit_start_date = Column(Date)
    site_visit_end_date = Column(Date)
    exit_conference_date = Column(Date)
    exit_conference_format = Column(String(50))  # virtual, in-person

    # Reviewer information
    lead_reviewer_name = Column(String(255))
    contractor_name = Column(String(255))
    lead_reviewer_phone = Column(String(50))
    lead_reviewer_email = Column(String(255))

    # FTA Program Manager
    fta_pm_name = Column(String(255))
    fta_pm_title = Column(String(255))
    fta_pm_phone = Column(String(50))
    fta_pm_email = Column(String(255))

    # Summary statistics
    total_deficiencies = Column(Integer, default=0)
    total_areas_reviewed = Column(Integer, default=23)
    review_status = Column(String(50), default='Completed')  # In Progress, Completed, Draft

    # Source tracking
    source_file = Column(String(500))  # Original PDF filename
    extracted_at = Column(DateTime, default=datetime.utcnow)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recipient = relationship("Recipient", back_populates="audit_reviews")
    assessments = relationship("HistoricalAssessment", back_populates="audit_review", cascade="all, delete-orphan")
    lessons = relationship("LessonLearned", back_populates="audit_review", cascade="all, delete-orphan")
    awards = relationship("Award", back_populates="audit_review", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="audit_review", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_recipient_fiscal_year', 'recipient_id', 'fiscal_year'),
        Index('idx_review_type_fiscal_year', 'review_type', 'fiscal_year'),
    )

    def __repr__(self):
        return f"<AuditReview(recipient_id={self.recipient_id}, fiscal_year='{self.fiscal_year}', type='{self.review_type}')>"


class HistoricalAssessment(Base):
    """Assessment results for each of 23 review areas in historical audits."""

    __tablename__ = 'historical_assessments'

    id = Column(Integer, primary_key=True)
    audit_review_id = Column(Integer, ForeignKey('audit_reviews.id', ondelete='CASCADE'), nullable=False, index=True)
    section_id = Column(Integer, ForeignKey('compliance_sections.id', ondelete='SET NULL'), nullable=True, index=True)

    # Assessment data
    review_area = Column(String(255), nullable=False, index=True)  # Full name (e.g., "Title VI")
    finding = Column(String(10), nullable=False, index=True)  # D, ND, NA

    # Deficiency details (populated only if finding='D')
    deficiency_code = Column(String(50), index=True)
    description = Column(Text)
    corrective_action = Column(Text)
    due_date = Column(Date)
    date_closed = Column(Date)

    # Narrative context (for RAG)
    narrative_text = Column(Text)  # Detailed observations from final report
    reviewer_notes = Column(Text)  # Additional context

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    audit_review = relationship("AuditReview", back_populates="assessments")
    section = relationship("ComplianceSection")

    # Indexes
    __table_args__ = (
        Index('idx_audit_section', 'audit_review_id', 'section_id'),
        Index('idx_finding_type', 'finding'),
        Index('idx_deficiency_code', 'deficiency_code'),
    )

    def __repr__(self):
        return f"<HistoricalAssessment(review_area='{self.review_area}', finding='{self.finding}')>"


class LessonLearned(Base):
    """Best practices, common issues, and lessons learned from audits."""

    __tablename__ = 'lessons_learned'

    id = Column(Integer, primary_key=True)
    audit_review_id = Column(Integer, ForeignKey('audit_reviews.id', ondelete='CASCADE'), nullable=False, index=True)
    section_id = Column(Integer, ForeignKey('compliance_sections.id', ondelete='SET NULL'), nullable=True, index=True)

    # Categorization
    lesson_type = Column(String(50), nullable=False, index=True)  # deficiency, best_practice, observation, recommendation
    category = Column(String(255), index=True)  # procurement, financial, safety, etc.

    # Content
    title = Column(String(500))
    description = Column(Text, nullable=False)
    recommendation = Column(Text)

    # Context
    context = Column(Text)  # When/why this lesson applies
    applicability = Column(Text)  # Which types of agencies this applies to

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    audit_review = relationship("AuditReview", back_populates="lessons")
    section = relationship("ComplianceSection")

    # Indexes
    __table_args__ = (
        Index('idx_lesson_type', 'lesson_type'),
        Index('idx_category', 'category'),
        Index('idx_audit_section_lesson', 'audit_review_id', 'section_id'),
    )

    def __repr__(self):
        return f"<LessonLearned(type='{self.lesson_type}', category='{self.category}', title='{self.title[:50]}...')>"


class Award(Base):
    """FTA awards and grants for each recipient."""
    __tablename__ = 'awards'

    id = Column(Integer, primary_key=True)
    audit_review_id = Column(Integer, ForeignKey('audit_reviews.id', ondelete='CASCADE'), nullable=False, index=True)

    # Award identification
    award_number = Column(String(100), nullable=False, index=True)
    award_year = Column(String(10))

    # Award details
    description = Column(Text)
    amount = Column(Numeric(precision=12, scale=2))  # Dollar amount

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    audit_review = relationship("AuditReview", back_populates="awards")

    def __repr__(self):
        return f"<Award(number='{self.award_number}', year='{self.award_year}', amount=${self.amount})>"


class Project(Base):
    """Projects (completed, ongoing, future) mentioned in audit reviews."""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    audit_review_id = Column(Integer, ForeignKey('audit_reviews.id', ondelete='CASCADE'), nullable=False, index=True)

    # Project details
    project_type = Column(String(20), nullable=False, index=True)  # 'completed', 'ongoing', 'future'
    description = Column(Text, nullable=False)

    # Optional fields
    completion_date = Column(String(50))  # Free text (e.g., "August 2021")
    funding_sources = Column(String(255))  # e.g., "FTA & PennDOT"

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    audit_review = relationship("AuditReview", back_populates="projects")

    # Indexes
    __table_args__ = (
        Index('idx_project_type', 'project_type'),
    )

    def __repr__(self):
        return f"<Project(type='{self.project_type}', desc='{self.description[:50]}...')>"


