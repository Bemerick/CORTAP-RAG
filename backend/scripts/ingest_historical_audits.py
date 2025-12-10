"""
Ingest Historical Audit Reports into PostgreSQL

Reads extracted JSON files from extract_audit_reports.py and loads data
into the historical audit review database tables.

Usage:
    python ingest_historical_audits.py --input-dir "./extracted_data"
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.models import (
    Base, Recipient, AuditReview, HistoricalAssessment,
    LessonLearned, ComplianceSection, Award, Project
)
from database.connection import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HistoricalAuditIngestor:
    """Ingest historical audit review data into PostgreSQL."""

    def __init__(self):
        self.db = DatabaseManager()
        self.section_map = {}  # Cache compliance_sections ID mapping

    def load_compliance_sections(self):
        """Load existing compliance sections for FK mapping."""
        with self.db.get_session() as session:
            sections = session.query(ComplianceSection).all()
            # Map section_name -> section_id
            for section in sections:
                self.section_map[section.section_name] = section.id
            logger.info(f"Loaded {len(self.section_map)} compliance sections")

    def parse_date(self, date_str: str):
        """Parse date string into datetime.date object."""
        if not date_str or date_str == "TBD":
            return None

        # Try multiple date formats
        formats = [
            "%B %d, %Y",      # August 18, 2023
            "%m/%d/%Y",       # 08/18/2023
            "%Y-%m-%d",       # 2023-08-18
            "%B %Y",          # August 2023
            "%Y",             # 2023
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # Handle date ranges like "June 7-9, 2023"
        if "-" in date_str and "," in date_str:
            # "June 7-9, 2023" -> take first date
            try:
                parts = date_str.split("-")[0]
                month_day = parts.strip()
                year = date_str.split(",")[-1].strip()
                return datetime.strptime(f"{month_day}, {year}", "%B %d, %Y").date()
            except Exception:
                pass

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def get_or_create_recipient(self, session, recipient_data: Dict, source_file: str) -> Recipient:
        """Get existing recipient or create new one."""
        recipient_id = recipient_data.get("recipient_id")
        acronym = recipient_data.get("acronym") or "N/A"  # Provide default if missing
        name = recipient_data.get("name", "Unknown Transit Agency")

        # Try to find by recipient_id first
        if recipient_id and recipient_id != "UNKNOWN":
            recipient = session.query(Recipient).filter_by(recipient_id=recipient_id).first()
            if recipient:
                logger.debug(f"Found existing recipient: {recipient.name}")
                return recipient

        # Try to find by name (case-insensitive)
        recipient = session.query(Recipient).filter(
            Recipient.name.ilike(f"%{name}%")
        ).first()
        if recipient:
            logger.debug(f"Found existing recipient by name: {recipient.name}")
            return recipient

        # Create new recipient with unique temp ID based on filename
        # Use first part of filename to ensure uniqueness
        temp_id = f"TEMP-{source_file[:20].replace(' ', '_')}"

        recipient = Recipient(
            recipient_id=recipient_id if recipient_id else temp_id,
            name=name,
            acronym=acronym,
            city=recipient_data.get("city"),
            state=recipient_data.get("state"),
            region_number=recipient_data.get("region_number")
        )
        session.add(recipient)
        session.flush()  # Get ID without committing
        logger.info(f"Created new recipient: {recipient.name} ({recipient.acronym}) [temp_id={recipient.recipient_id}]")
        return recipient

    def map_review_type(self, review_type_code: str) -> str:
        """Map review type code to full name."""
        mapping = {
            "TR": "Triennial Review",
            "SMR": "State Management Review",
            "TR_SMR": "Combined Triennial and State Management Review"
        }
        return mapping.get(review_type_code, review_type_code)

    def ingest_audit_review(self, session, data: Dict) -> AuditReview:
        """Ingest single audit review with all assessments."""
        # Get or create recipient
        recipient = self.get_or_create_recipient(session, data["recipient"], data.get("source_file", "unknown.pdf"))

        # Parse review info
        review_info = data.get("review_info", {})
        reviewer_info = data.get("reviewer_info", {})
        fta_pm_info = data.get("fta_pm_info", {})
        summary = data.get("summary", {})

        # Map review type
        review_type = self.map_review_type(review_info.get("review_type_code") or review_info.get("review_type", "TR"))

        # Helper to truncate string fields
        def truncate(value, max_len=255):
            if value and len(value) > max_len:
                return value[:max_len-3] + "..."
            return value

        # Calculate summary statistics from assessments
        assessments_data = data.get("assessments", [])
        total_deficiencies = sum(1 for a in assessments_data if a.get("finding") == "D")
        total_areas_reviewed = len(assessments_data)

        # Create audit review
        audit_review = AuditReview(
            recipient_id=recipient.id,
            fiscal_year=review_info.get("fiscal_year", "FY2023"),
            review_type=review_type,
            report_date=self.parse_date(review_info.get("report_date")),
            site_visit_start_date=self.parse_date(review_info.get("site_visit_start_date")),
            site_visit_end_date=self.parse_date(review_info.get("site_visit_end_date")),
            exit_conference_date=self.parse_date(review_info.get("exit_conference_date")),
            exit_conference_format=truncate(review_info.get("exit_conference_format"), 50),
            lead_reviewer_name=truncate(reviewer_info.get("lead_reviewer_name")),
            contractor_name=truncate(reviewer_info.get("contractor_name")),
            lead_reviewer_phone=truncate(reviewer_info.get("lead_reviewer_phone"), 50),
            lead_reviewer_email=truncate(reviewer_info.get("lead_reviewer_email")),
            fta_pm_name=truncate(fta_pm_info.get("fta_pm_name")),
            fta_pm_title=truncate(fta_pm_info.get("fta_pm_title")),
            fta_pm_phone=truncate(fta_pm_info.get("fta_pm_phone"), 50),
            fta_pm_email=truncate(fta_pm_info.get("fta_pm_email")),
            total_deficiencies=summary.get("total_deficiencies", total_deficiencies),
            total_areas_reviewed=summary.get("total_areas_reviewed", total_areas_reviewed),
            review_status="Completed",
            source_file=truncate(data.get("source_file", "unknown.pdf"), 500),
            extracted_at=datetime.fromisoformat(data["extracted_at"]) if "extracted_at" in data else datetime.utcnow()
        )
        session.add(audit_review)
        session.flush()

        logger.info(f"Created audit review: {recipient.acronym} {audit_review.fiscal_year} - {audit_review.total_deficiencies} deficiencies")

        # Ingest assessments
        assessments_count = 0
        for assessment_data in assessments_data:
            review_area = assessment_data.get("review_area")
            section_id = self.section_map.get(review_area)  # FK to compliance_sections

            # Get narrative text if available
            narrative_sections = data.get("narrative_sections", {})
            narrative_text = narrative_sections.get(review_area) if narrative_sections else None

            assessment = HistoricalAssessment(
                audit_review_id=audit_review.id,
                section_id=section_id,
                review_area=review_area,
                finding=assessment_data.get("finding", "ND"),
                deficiency_code=assessment_data.get("deficiency_code"),
                description=assessment_data.get("description"),
                corrective_action=assessment_data.get("corrective_action"),
                due_date=self.parse_date(assessment_data.get("response_due_date")) if assessment_data.get("response_due_date") else None,
                date_closed=self.parse_date(assessment_data.get("date_closed")) if assessment_data.get("date_closed") else None,
                narrative_text=narrative_text,
                reviewer_notes=None
            )
            session.add(assessment)
            assessments_count += 1

        logger.info(f"  Added {assessments_count} assessments")

        # Ingest awards if present
        awards_count = 0
        if "awards" in data:
            for award_data in data["awards"]:
                award = Award(
                    audit_review_id=audit_review.id,
                    award_number=award_data.get("award_number", ""),
                    award_year=award_data.get("award_year"),
                    description=award_data.get("description"),
                    amount=award_data.get("amount")
                )
                session.add(award)
                awards_count += 1
            logger.info(f"  Added {awards_count} awards")

        # Ingest projects if present
        projects_count = 0
        if "projects" in data:
            projects_data = data["projects"]

            # Handle list structure (Claude extraction format with project_type field)
            if isinstance(projects_data, list):
                for project_data in projects_data:
                    if isinstance(project_data, dict):
                        project = Project(
                            audit_review_id=audit_review.id,
                            project_type=project_data.get("project_type", "completed"),
                            description=project_data.get("description", ""),
                            completion_date=project_data.get("completion_date"),
                            funding_sources=project_data.get("funding_sources")
                        )
                        session.add(project)
                        projects_count += 1

            # Handle dict structure (completed/ongoing/future keys)
            elif isinstance(projects_data, dict):
                # Handle completed projects
                for project_data in projects_data.get("completed", []):
                    desc = project_data if isinstance(project_data, str) else project_data.get("description", "")
                    project = Project(
                        audit_review_id=audit_review.id,
                        project_type="completed",
                        description=desc,
                        completion_date=project_data.get("completion_date") if isinstance(project_data, dict) else None,
                        funding_sources=project_data.get("funding_sources") if isinstance(project_data, dict) else None
                    )
                    session.add(project)
                    projects_count += 1

                # Handle ongoing projects
                for project_data in projects_data.get("ongoing", []):
                    desc = project_data if isinstance(project_data, str) else project_data.get("description", "")
                    project = Project(
                        audit_review_id=audit_review.id,
                        project_type="ongoing",
                        description=desc,
                        completion_date=None,
                        funding_sources=project_data.get("funding_sources") if isinstance(project_data, dict) else None
                    )
                    session.add(project)
                    projects_count += 1

                # Handle future projects
                for project_data in projects_data.get("future", []):
                    desc = project_data if isinstance(project_data, str) else project_data.get("description", "")
                    project = Project(
                        audit_review_id=audit_review.id,
                        project_type="future",
                        description=desc,
                        completion_date=None,
                        funding_sources=project_data.get("funding_sources") if isinstance(project_data, dict) else None
                    )
                    session.add(project)
                    projects_count += 1

            if projects_count > 0:
                logger.info(f"  Added {projects_count} projects")

        return audit_review

    def ingest_all(self, input_dir: str):
        """Ingest all extracted JSON files."""
        input_path = Path(input_dir)

        # Skip the combined file
        json_files = [f for f in input_path.glob("*.json") if f.name != "all_reports_combined.json"]
        logger.info(f"Found {len(json_files)} JSON files to ingest")

        # Load compliance sections first
        self.load_compliance_sections()

        successful = 0
        failed = 0
        skipped = 0

        with self.db.get_session() as session:
            for json_file in json_files:
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)

                    # Skip only if both name and acronym are completely missing
                    if not data.get("recipient", {}).get("name") and not data.get("recipient", {}).get("acronym"):
                        logger.warning(f"Skipping {json_file.name} - missing recipient information")
                        skipped += 1
                        continue

                    # Check if already exists (based on source_file)
                    source_file = data.get("source_file", json_file.name)
                    existing = session.query(AuditReview).filter_by(source_file=source_file).first()
                    if existing:
                        logger.info(f"Skipping {json_file.name} - already in database")
                        skipped += 1
                        continue

                    self.ingest_audit_review(session, data)
                    successful += 1

                except Exception as e:
                    logger.error(f"Failed to ingest {json_file.name}: {e}")
                    failed += 1
                    session.rollback()
                    continue

            # Commit all at end
            session.commit()
            logger.info(f"\nIngestion complete:")
            logger.info(f"  Successful: {successful}")
            logger.info(f"  Skipped: {skipped}")
            logger.info(f"  Failed: {failed}")

    def get_statistics(self):
        """Print database statistics after ingestion."""
        with self.db.get_session() as session:
            recipients_count = session.query(Recipient).count()
            reviews_count = session.query(AuditReview).count()
            assessments_count = session.query(HistoricalAssessment).count()
            deficiencies_count = session.query(HistoricalAssessment).filter_by(finding='D').count()
            awards_count = session.query(Award).count()
            projects_count = session.query(Project).count()

            logger.info(f"\n=== Database Statistics ===")
            logger.info(f"Recipients: {recipients_count}")
            logger.info(f"Audit Reviews: {reviews_count}")
            logger.info(f"Assessments: {assessments_count}")
            logger.info(f"Deficiencies: {deficiencies_count}")
            logger.info(f"Awards: {awards_count}")
            logger.info(f"Projects: {projects_count}")

            # Top deficiency areas
            from sqlalchemy import func
            top_deficiency_areas = (
                session.query(
                    HistoricalAssessment.review_area,
                    func.count(HistoricalAssessment.id).label('count')
                )
                .filter_by(finding='D')
                .group_by(HistoricalAssessment.review_area)
                .order_by(func.count(HistoricalAssessment.id).desc())
                .limit(5)
                .all()
            )

            logger.info(f"\nTop 5 Deficiency Areas:")
            for area, count in top_deficiency_areas:
                logger.info(f"  {area}: {count}")


def main():
    parser = argparse.ArgumentParser(description='Ingest historical audit reports into PostgreSQL')
    parser.add_argument('--input-dir', default='./extracted_data',
                        help='Directory containing extracted JSON files')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print what would be done without committing')

    args = parser.parse_args()

    ingestor = HistoricalAuditIngestor()

    if args.dry_run:
        logger.info("DRY RUN MODE - no data will be committed")

    ingestor.ingest_all(args.input_dir)
    ingestor.get_statistics()


if __name__ == "__main__":
    main()
