"""
Enhanced database models for additional audit report data.

New tables to add:
1. Awards - FTA award/grant information
2. Projects - Completed, ongoing, and future projects
3. FindingsSummary - Summary table data from executive summary
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from database.models import Base


class Award(Base):
    """FTA awards and grants for each recipient."""
    __tablename__ = 'awards'

    id = Column(Integer, primary_key=True)
    audit_review_id = Column(Integer, ForeignKey('audit_reviews.id'), nullable=False, index=True)

    # Award identification
    award_number = Column(String(100), nullable=False, index=True)
    award_year = Column(String(10))

    # Award details
    description = Column(Text)
    amount = Column(Numeric(precision=12, scale=2))  # Dollar amount

    # Relationships
    audit_review = relationship("AuditReview", back_populates="awards")


class Project(Base):
    """Projects (completed, ongoing, future) mentioned in audit reviews."""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    audit_review_id = Column(Integer, ForeignKey('audit_reviews.id'), nullable=False, index=True)

    # Project details
    project_type = Column(String(20), nullable=False, index=True)  # 'completed', 'ongoing', 'future'
    description = Column(Text, nullable=False)

    # Optional fields
    completion_date = Column(String(50))  # Free text (e.g., "August 2021")
    funding_sources = Column(String(255))  # e.g., "FTA & PennDOT"

    # Relationships
    audit_review = relationship("AuditReview", back_populates="projects")


class FindingsSummaryItem(Base):
    """
    Individual findings from the Summary of Findings table in executive summary.

    This is the deficiency summary table that shows:
    - Review Area
    - Deficiency Code
    - Brief description/rationale
    - Corrective Action summary
    - Response Due Date
    """
    __tablename__ = 'findings_summary_items'

    id = Column(Integer, primary_key=True)
    audit_review_id = Column(Integer, ForeignKey('audit_reviews.id'), nullable=False, index=True)

    # Finding identification
    review_area = Column(String(255), nullable=False, index=True)
    deficiency_code = Column(String(50), index=True)

    # Summary information (from executive summary table)
    code_rationale = Column(Text)  # Brief description of what the code means
    corrective_action_summary = Column(Text)  # Summary of required actions
    response_due_date = Column(String(50))  # e.g., "11/7/2023"

    # Relationships
    audit_review = relationship("AuditReview", back_populates="findings_summary")


# Update AuditReview model to add relationships (add these to existing models.py)
# audit_review.awards = relationship("Award", back_populates="audit_review")
# audit_review.projects = relationship("Project", back_populates="audit_review")
# audit_review.findings_summary = relationship("FindingsSummaryItem", back_populates="audit_review")
