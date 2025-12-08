"""SQL query builder for structured compliance data retrieval."""
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from .models import ComplianceSection, ComplianceQuestion, ComplianceIndicator, ComplianceDeficiency
from .connection import DatabaseManager


class QueryBuilder:
    """Build and execute SQL queries for compliance data."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize query builder.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager

    def count_indicators(
        self,
        question_code: Optional[str] = None,
        section_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Count indicators of compliance.

        Args:
            question_code: Specific question code (e.g., "TVI3", "L1", "CB2")
            section_code: Section code if different from question_code

        Returns:
            Dict with count and metadata
        """
        with self.db_manager.session_scope() as session:
            # Base query
            query = session.query(
                ComplianceIndicator.id
            ).join(
                ComplianceQuestion,
                ComplianceIndicator.question_id == ComplianceQuestion.id
            )

            # Filter by question code
            if question_code:
                query = query.filter(ComplianceQuestion.question_code == question_code.upper())

            # Execute count
            count = query.count()

            # Get question details if code provided
            question_info = None
            if question_code:
                question = session.query(ComplianceQuestion).filter(
                    ComplianceQuestion.question_code == question_code.upper()
                ).first()

                if question:
                    question_info = {
                        'question_code': question.question_code,
                        'question_text': question.question_text,
                        'applicability': question.applicability
                    }

            return {
                'count': count,
                'question_code': question_code.upper() if question_code else None,
                'question_info': question_info,
                'query_type': 'count_indicators'
            }

    def count_deficiencies(
        self,
        question_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Count potential deficiencies.

        Args:
            question_code: Specific question code

        Returns:
            Dict with count and metadata
        """
        with self.db_manager.session_scope() as session:
            query = session.query(
                ComplianceDeficiency.id
            ).join(
                ComplianceQuestion,
                ComplianceDeficiency.question_id == ComplianceQuestion.id
            )

            if question_code:
                query = query.filter(ComplianceQuestion.question_code == question_code.upper())

            count = query.count()

            return {
                'count': count,
                'question_code': question_code.upper() if question_code else None,
                'query_type': 'count_deficiencies'
            }

    def list_indicators(
        self,
        question_code: str,
        include_question_text: bool = True
    ) -> Dict[str, Any]:
        """
        List all indicators for a specific question.

        Args:
            question_code: Question code (e.g., "TVI3", "L1")
            include_question_text: Include full question details

        Returns:
            Dict with indicators list and metadata
        """
        with self.db_manager.session_scope() as session:
            # Get question
            question = session.query(ComplianceQuestion).filter(
                ComplianceQuestion.question_code == question_code.upper()
            ).first()

            if not question:
                return {
                    'found': False,
                    'question_code': question_code.upper(),
                    'error': f'Question code {question_code.upper()} not found',
                    'query_type': 'list_indicators'
                }

            # Get indicators
            indicators = session.query(ComplianceIndicator).filter(
                ComplianceIndicator.question_id == question.id
            ).order_by(ComplianceIndicator.indicator_order).all()

            # Format indicators
            indicator_list = [
                {
                    'letter': ind.letter,
                    'text': ind.indicator_text,
                    'order': ind.indicator_order
                }
                for ind in indicators
            ]

            result = {
                'found': True,
                'question_code': question.question_code,
                'count': len(indicator_list),
                'indicators': indicator_list,
                'query_type': 'list_indicators'
            }

            # Add question details if requested
            if include_question_text:
                result['question'] = {
                    'text': question.question_text,
                    'applicability': question.applicability,
                    'basic_requirement': question.basic_requirement
                }

            return result

    def list_deficiencies(
        self,
        question_code: str,
        include_question_text: bool = True
    ) -> Dict[str, Any]:
        """
        List all deficiencies for a specific question.

        Args:
            question_code: Question code
            include_question_text: Include full question details

        Returns:
            Dict with deficiencies list and metadata
        """
        with self.db_manager.session_scope() as session:
            # Get question
            question = session.query(ComplianceQuestion).filter(
                ComplianceQuestion.question_code == question_code.upper()
            ).first()

            if not question:
                return {
                    'found': False,
                    'question_code': question_code.upper(),
                    'error': f'Question code {question_code.upper()} not found',
                    'query_type': 'list_deficiencies'
                }

            # Get deficiencies
            deficiencies = session.query(ComplianceDeficiency).filter(
                ComplianceDeficiency.question_id == question.id
            ).order_by(ComplianceDeficiency.deficiency_order).all()

            # Format deficiencies
            deficiency_list = [
                {
                    'code': def_.deficiency_code,
                    'title': def_.deficiency_title,
                    'determination': def_.determination,
                    'corrective_action': def_.corrective_action
                }
                for def_ in deficiencies
            ]

            result = {
                'found': True,
                'question_code': question.question_code,
                'count': len(deficiency_list),
                'deficiencies': deficiency_list,
                'query_type': 'list_deficiencies'
            }

            if include_question_text:
                result['question'] = {
                    'text': question.question_text,
                    'applicability': question.applicability
                }

            return result

    def get_section(self, question_code: str) -> Dict[str, Any]:
        """
        Get complete section information including question, indicators, and deficiencies.

        Args:
            question_code: Question code (e.g., "TVI3", "L1")

        Returns:
            Dict with complete section data
        """
        with self.db_manager.session_scope() as session:
            # Get question with all relationships
            question = session.query(ComplianceQuestion).filter(
                ComplianceQuestion.question_code == question_code.upper()
            ).first()

            if not question:
                return {
                    'found': False,
                    'question_code': question_code.upper(),
                    'error': f'Question code {question_code.upper()} not found',
                    'query_type': 'get_section'
                }

            # Get section info
            section = session.query(ComplianceSection).filter(
                ComplianceSection.id == question.section_id
            ).first()

            # Get indicators
            indicators = session.query(ComplianceIndicator).filter(
                ComplianceIndicator.question_id == question.id
            ).order_by(ComplianceIndicator.indicator_order).all()

            # Get deficiencies
            deficiencies = session.query(ComplianceDeficiency).filter(
                ComplianceDeficiency.question_id == question.id
            ).order_by(ComplianceDeficiency.deficiency_order).all()

            return {
                'found': True,
                'question_code': question.question_code,
                'section': {
                    'code': section.section_code if section else None,
                    'name': section.section_name if section else None,
                    'purpose': section.purpose if section else None
                },
                'question': {
                    'text': question.question_text,
                    'basic_requirement': question.basic_requirement,
                    'applicability': question.applicability,
                    'detailed_explanation': question.detailed_explanation,
                    'instructions_for_reviewer': question.instructions_for_reviewer
                },
                'indicators': [
                    {
                        'letter': ind.letter,
                        'text': ind.indicator_text
                    }
                    for ind in indicators
                ],
                'deficiencies': [
                    {
                        'code': def_.deficiency_code,
                        'title': def_.deficiency_title,
                        'determination': def_.determination,
                        'corrective_action': def_.corrective_action
                    }
                    for def_ in deficiencies
                ],
                'stats': {
                    'indicator_count': len(indicators),
                    'deficiency_count': len(deficiencies)
                },
                'query_type': 'get_section'
            }

    def get_all_sections(self) -> Dict[str, Any]:
        """
        Get summary of all compliance sections.

        Returns:
            Dict with all sections and counts
        """
        with self.db_manager.session_scope() as session:
            sections = session.query(ComplianceSection).all()

            section_list = []
            for section in sections:
                # Count questions
                question_count = session.query(ComplianceQuestion).filter(
                    ComplianceQuestion.section_id == section.id
                ).count()

                # Count indicators
                indicator_count = session.query(ComplianceIndicator).join(
                    ComplianceQuestion
                ).filter(
                    ComplianceQuestion.section_id == section.id
                ).count()

                section_list.append({
                    'code': section.section_code,
                    'name': section.section_name,
                    'question_count': question_count,
                    'indicator_count': indicator_count
                })

            return {
                'found': True,
                'section_count': len(section_list),
                'sections': section_list,
                'query_type': 'get_all_sections'
            }

    def get_total_counts(self) -> Dict[str, Any]:
        """
        Get total counts across entire database.

        Returns:
            Dict with aggregate statistics
        """
        with self.db_manager.session_scope() as session:
            total_sections = session.query(ComplianceSection).count()
            total_questions = session.query(ComplianceQuestion).count()
            total_indicators = session.query(ComplianceIndicator).count()
            total_deficiencies = session.query(ComplianceDeficiency).count()

            return {
                'found': True,
                'totals': {
                    'sections': total_sections,
                    'questions': total_questions,
                    'indicators': total_indicators,
                    'deficiencies': total_deficiencies
                },
                'query_type': 'get_total_counts'
            }


# Convenience function for quick queries
def quick_query(query_type: str, question_code: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick query interface.

    Args:
        query_type: Type of query ('count_indicators', 'list_indicators', 'get_section', etc.)
        question_code: Question code if applicable

    Returns:
        Query results
    """
    from .connection import get_db_manager

    db_manager = get_db_manager()
    builder = QueryBuilder(db_manager)

    if query_type == 'count_indicators':
        return builder.count_indicators(question_code)
    elif query_type == 'list_indicators':
        return builder.list_indicators(question_code)
    elif query_type == 'get_section':
        return builder.get_section(question_code)
    elif query_type == 'get_all_sections':
        return builder.get_all_sections()
    elif query_type == 'get_total_counts':
        return builder.get_total_counts()
    else:
        return {'error': f'Unknown query type: {query_type}'}


# Example usage
if __name__ == "__main__":
    import os
    from .connection import get_db_manager

    # Set database URL
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:Forest12345#@localhost:5432/cortap_compliance')
    db_manager = get_db_manager(db_url)

    builder = QueryBuilder(db_manager)

    # Test queries
    print("=" * 80)
    print("QUERY BUILDER TEST")
    print("=" * 80)

    # Count indicators
    print("\n1. Count indicators in TVI3:")
    result = builder.count_indicators('TVI3')
    print(f"   Count: {result['count']}")

    # List indicators
    print("\n2. List all indicators for L1:")
    result = builder.list_indicators('L1')
    if result['found']:
        print(f"   Found {result['count']} indicators:")
        for ind in result['indicators'][:3]:
            print(f"   {ind['letter']}. {ind['text'][:60]}...")

    # Get section
    print("\n3. Get complete section for CB1:")
    result = builder.get_section('CB1')
    if result['found']:
        print(f"   Question: {result['question']['text'][:60]}...")
        print(f"   Indicators: {result['stats']['indicator_count']}")
        print(f"   Deficiencies: {result['stats']['deficiency_count']}")

    # Get total counts
    print("\n4. Get total counts:")
    result = builder.get_total_counts()
    print(f"   Sections: {result['totals']['sections']}")
    print(f"   Questions: {result['totals']['questions']}")
    print(f"   Indicators: {result['totals']['indicators']}")
    print(f"   Deficiencies: {result['totals']['deficiencies']}")

    print("\n" + "=" * 80)
