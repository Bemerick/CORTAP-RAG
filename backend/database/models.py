"""SQLAlchemy ORM models for FTA compliance data."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, Index
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
