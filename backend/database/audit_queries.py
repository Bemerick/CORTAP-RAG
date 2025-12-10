"""Database query helpers for historical audit data."""
from typing import Dict, List, Optional, Any
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from database.models import Recipient, AuditReview, HistoricalAssessment
from database.connection import DatabaseManager


class AuditQueryHelper:
    """Helper class for querying historical audit data."""

    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize query helper.

        Args:
            db_manager: DatabaseManager instance (optional, will create new one if not provided)
        """
        self.db = db_manager if db_manager else DatabaseManager()

    def get_recipient_by_name_or_acronym(
        self,
        session: Session,
        identifier: str
    ) -> Optional[Recipient]:
        """
        Find recipient by name or acronym (case-insensitive).

        Args:
            session: Database session
            identifier: Recipient name or acronym

        Returns:
            Recipient object or None
        """
        identifier_upper = identifier.upper()

        return session.query(Recipient).filter(
            or_(
                func.upper(Recipient.name).like(f"%{identifier_upper}%"),
                func.upper(Recipient.acronym) == identifier_upper
            )
        ).first()

    def get_recipient_deficiencies(
        self,
        recipient_identifier: str,
        fiscal_year: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all deficiencies for a specific recipient.

        Args:
            recipient_identifier: Recipient name or acronym
            fiscal_year: Optional fiscal year filter (e.g., "2023")

        Returns:
            Dictionary with recipient info and deficiencies
        """
        with self.db.get_session() as session:
            recipient = self.get_recipient_by_name_or_acronym(session, recipient_identifier)

            if not recipient:
                return {
                    "error": f"Recipient '{recipient_identifier}' not found",
                    "recipient": None,
                    "deficiencies": []
                }

            # Build query
            query = session.query(HistoricalAssessment).join(
                AuditReview
            ).filter(
                AuditReview.recipient_id == recipient.id,
                HistoricalAssessment.finding == 'D'
            )

            if fiscal_year:
                query = query.filter(AuditReview.fiscal_year == fiscal_year)

            deficiencies = query.all()

            return {
                "recipient": {
                    "name": recipient.name,
                    "acronym": recipient.acronym,
                    "city": recipient.city,
                    "state": recipient.state,
                    "region": recipient.region_number
                },
                "total_deficiencies": len(deficiencies),
                "deficiencies": [
                    {
                        "review_area": d.review_area,
                        "deficiency_code": d.deficiency_code,
                        "description": d.description,
                        "corrective_action": d.corrective_action
                    }
                    for d in deficiencies
                ]
            }

    def get_regional_deficiencies(
        self,
        region_number: int,
        review_area: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get deficiencies for a specific region.

        Args:
            region_number: FTA region number (1-10)
            review_area: Optional review area filter

        Returns:
            Dictionary with regional deficiency data
        """
        with self.db.get_session() as session:
            # Build query
            query = session.query(
                Recipient.name,
                Recipient.acronym,
                Recipient.state,
                HistoricalAssessment.review_area,
                func.count(HistoricalAssessment.id).label('deficiency_count')
            ).join(
                AuditReview, Recipient.id == AuditReview.recipient_id
            ).join(
                HistoricalAssessment, AuditReview.id == HistoricalAssessment.audit_review_id
            ).filter(
                Recipient.region_number == region_number,
                HistoricalAssessment.finding == 'D'
            )

            if review_area:
                query = query.filter(
                    func.lower(HistoricalAssessment.review_area).like(f"%{review_area.lower()}%")
                )

            query = query.group_by(
                Recipient.name,
                Recipient.acronym,
                Recipient.state,
                HistoricalAssessment.review_area
            )

            results = query.all()

            # Aggregate by recipient
            recipients_data = {}
            for row in results:
                recipient_key = row.acronym or row.name
                if recipient_key not in recipients_data:
                    recipients_data[recipient_key] = {
                        "name": row.name,
                        "acronym": row.acronym,
                        "state": row.state,
                        "deficiencies": []
                    }
                recipients_data[recipient_key]["deficiencies"].append({
                    "review_area": row.review_area,
                    "count": row.deficiency_count
                })

            return {
                "region": region_number,
                "total_recipients": len(recipients_data),
                "recipients": list(recipients_data.values())
            }

    def get_common_deficiencies(
        self,
        review_area: Optional[str] = None,
        min_occurrences: int = 2
    ) -> Dict[str, Any]:
        """
        Get common deficiencies across all recipients.

        Args:
            review_area: Optional review area filter
            min_occurrences: Minimum number of recipients with this deficiency

        Returns:
            Dictionary with common deficiency patterns
        """
        with self.db.get_session() as session:
            query = session.query(
                HistoricalAssessment.review_area,
                func.count(func.distinct(AuditReview.recipient_id)).label('recipient_count'),
                func.count(HistoricalAssessment.id).label('total_deficiencies')
            ).join(
                AuditReview
            ).filter(
                HistoricalAssessment.finding == 'D'
            )

            if review_area:
                query = query.filter(
                    func.lower(HistoricalAssessment.review_area).like(f"%{review_area.lower()}%")
                )

            query = query.group_by(
                HistoricalAssessment.review_area
            ).having(
                func.count(func.distinct(AuditReview.recipient_id)) >= min_occurrences
            ).order_by(
                func.count(func.distinct(AuditReview.recipient_id)).desc()
            )

            results = query.all()

            return {
                "common_deficiencies": [
                    {
                        "review_area": row.review_area,
                        "recipient_count": row.recipient_count,
                        "total_deficiencies": row.total_deficiencies
                    }
                    for row in results
                ]
            }

    def get_recipients_by_deficiency_count(
        self,
        limit: int = 10,
        order: str = 'desc'
    ) -> Dict[str, Any]:
        """
        Get recipients ranked by deficiency count.

        Args:
            limit: Number of recipients to return
            order: 'desc' for most deficiencies, 'asc' for least

        Returns:
            Dictionary with ranked recipients
        """
        with self.db.get_session() as session:
            query = session.query(
                Recipient.name,
                Recipient.acronym,
                Recipient.city,
                Recipient.state,
                Recipient.region_number,
                func.count(HistoricalAssessment.id).label('deficiency_count')
            ).join(
                AuditReview, Recipient.id == AuditReview.recipient_id
            ).join(
                HistoricalAssessment, AuditReview.id == HistoricalAssessment.audit_review_id
            ).filter(
                HistoricalAssessment.finding == 'D'
            ).group_by(
                Recipient.id,
                Recipient.name,
                Recipient.acronym,
                Recipient.city,
                Recipient.state,
                Recipient.region_number
            )

            # Order by deficiency count
            if order == 'desc':
                query = query.order_by(func.count(HistoricalAssessment.id).desc())
            else:
                query = query.order_by(func.count(HistoricalAssessment.id).asc())

            query = query.limit(limit)
            results = query.all()

            return {
                "total_recipients": len(results),
                "order": order,
                "recipients": [
                    {
                        "name": r.name,
                        "acronym": r.acronym,
                        "city": r.city,
                        "state": r.state,
                        "region": r.region_number,
                        "deficiency_count": r.deficiency_count
                    }
                    for r in results
                ]
            }

    def list_all_recipients(
        self,
        region_number: Optional[int] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all recipients with audit review counts.

        Args:
            region_number: Optional region filter
            state: Optional state filter

        Returns:
            Dictionary with recipient list
        """
        with self.db.get_session() as session:
            query = session.query(
                Recipient,
                func.count(AuditReview.id).label('review_count')
            ).outerjoin(
                AuditReview
            )

            if region_number:
                query = query.filter(Recipient.region_number == region_number)

            if state:
                query = query.filter(func.upper(Recipient.state) == state.upper())

            query = query.group_by(Recipient.id).order_by(Recipient.name)

            results = query.all()

            return {
                "total_recipients": len(results),
                "recipients": [
                    {
                        "name": r.Recipient.name,
                        "acronym": r.Recipient.acronym,
                        "city": r.Recipient.city,
                        "state": r.Recipient.state,
                        "region": r.Recipient.region_number,
                        "review_count": r.review_count
                    }
                    for r in results
                ]
            }

    def get_review_summary(
        self,
        recipient_identifier: str,
        fiscal_year: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get complete review summary for a recipient.

        Args:
            recipient_identifier: Recipient name or acronym
            fiscal_year: Optional fiscal year filter

        Returns:
            Dictionary with complete review data
        """
        with self.db.get_session() as session:
            recipient = self.get_recipient_by_name_or_acronym(session, recipient_identifier)

            if not recipient:
                return {
                    "error": f"Recipient '{recipient_identifier}' not found",
                    "reviews": []
                }

            query = session.query(AuditReview).filter(
                AuditReview.recipient_id == recipient.id
            )

            if fiscal_year:
                query = query.filter(AuditReview.fiscal_year == fiscal_year)

            reviews = query.all()

            review_data = []
            for review in reviews:
                # Get all assessments
                assessments = session.query(HistoricalAssessment).filter(
                    HistoricalAssessment.audit_review_id == review.id
                ).all()

                review_data.append({
                    "fiscal_year": review.fiscal_year,
                    "review_type": review.review_type,
                    "total_deficiencies": review.total_deficiencies,
                    "source_file": review.source_file,
                    "assessments": [
                        {
                            "review_area": a.review_area,
                            "finding": a.finding,
                            "deficiency_code": a.deficiency_code,
                            "description": a.description
                        }
                        for a in assessments
                    ]
                })

            return {
                "recipient": {
                    "name": recipient.name,
                    "acronym": recipient.acronym,
                    "city": recipient.city,
                    "state": recipient.state,
                    "region": recipient.region_number
                },
                "total_reviews": len(reviews),
                "reviews": review_data
            }

    def get_aggregate_stats(self) -> Dict[str, Any]:
        """
        Get aggregate statistics across all historical audits.

        Returns:
            Dictionary with aggregate statistics
        """
        with self.db.get_session() as session:
            total_recipients = session.query(func.count(Recipient.id)).scalar()
            total_reviews = session.query(func.count(AuditReview.id)).scalar()
            total_deficiencies = session.query(func.count(HistoricalAssessment.id)).filter(
                HistoricalAssessment.finding == 'D'
            ).scalar()

            # Deficiencies by region
            region_stats = session.query(
                Recipient.region_number,
                func.count(func.distinct(Recipient.id)).label('recipient_count'),
                func.count(HistoricalAssessment.id).label('deficiency_count')
            ).select_from(
                Recipient
            ).join(
                AuditReview, Recipient.id == AuditReview.recipient_id
            ).join(
                HistoricalAssessment, AuditReview.id == HistoricalAssessment.audit_review_id
            ).filter(
                HistoricalAssessment.finding == 'D',
                Recipient.region_number.isnot(None)
            ).group_by(
                Recipient.region_number
            ).order_by(
                Recipient.region_number
            ).all()

            # Top deficiency areas
            top_areas = session.query(
                HistoricalAssessment.review_area,
                func.count(HistoricalAssessment.id).label('count')
            ).filter(
                HistoricalAssessment.finding == 'D'
            ).group_by(
                HistoricalAssessment.review_area
            ).order_by(
                func.count(HistoricalAssessment.id).desc()
            ).limit(5).all()

            return {
                "total_recipients": total_recipients,
                "total_reviews": total_reviews,
                "total_deficiencies": total_deficiencies,
                "by_region": [
                    {
                        "region": r.region_number,
                        "recipients": r.recipient_count,
                        "deficiencies": r.deficiency_count
                    }
                    for r in region_stats
                ],
                "top_deficiency_areas": [
                    {
                        "review_area": a.review_area,
                        "count": a.count
                    }
                    for a in top_areas
                ]
            }


# Convenience functions
def query_recipient_deficiencies(recipient: str, fiscal_year: Optional[str] = None) -> Dict[str, Any]:
    """Get deficiencies for a specific recipient."""
    helper = AuditQueryHelper()
    return helper.get_recipient_deficiencies(recipient, fiscal_year)


def query_regional_data(region: int, review_area: Optional[str] = None) -> Dict[str, Any]:
    """Get regional deficiency data."""
    helper = AuditQueryHelper()
    return helper.get_regional_deficiencies(region, review_area)


def query_common_deficiencies(review_area: Optional[str] = None) -> Dict[str, Any]:
    """Get common deficiencies across all recipients."""
    helper = AuditQueryHelper()
    return helper.get_common_deficiencies(review_area)


def query_all_recipients(region: Optional[int] = None, state: Optional[str] = None) -> Dict[str, Any]:
    """List all recipients with review counts."""
    helper = AuditQueryHelper()
    return helper.list_all_recipients(region_number=region, state=state)


def query_aggregate_stats() -> Dict[str, Any]:
    """Get aggregate statistics."""
    helper = AuditQueryHelper()
    return helper.get_aggregate_stats()
