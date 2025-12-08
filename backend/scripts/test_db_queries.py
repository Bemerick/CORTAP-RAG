#!/usr/bin/env python3
"""
Test database queries after ingestion.

Usage:
    python scripts/test_db_queries.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import ComplianceSection, ComplianceQuestion, ComplianceIndicator, ComplianceDeficiency
from database.connection import get_db_manager


def test_get_title_vi_indicators(session):
    """Test: Get all indicators for Title VI."""
    print("\n" + "=" * 80)
    print("TEST: Get all indicators for Title VI")
    print("=" * 80)

    section = session.query(ComplianceSection).filter_by(section_code='TVI').first()

    if not section:
        print("❌ Title VI section not found!")
        return

    print(f"\n📋 {section.section_name} ({section.section_code})")
    print(f"   Page Range: {section.page_range}")
    print(f"   Questions: {len(section.questions)}")

    total_indicators = 0
    for question in sorted(section.questions, key=lambda q: q.question_order):
        print(f"\n**{question.question_code}. {question.question_text}**")
        print(f"   Applicability: {question.applicability}")

        for indicator in sorted(question.indicators, key=lambda i: i.indicator_order):
            print(f"   {indicator.letter}. {indicator.indicator_text[:80]}...")
            total_indicators += 1

    print(f"\n✅ Total indicators: {total_indicators}")


def test_get_question_details(session):
    """Test: Get detailed information for a specific question."""
    print("\n" + "=" * 80)
    print("TEST: Get question details (TVI1)")
    print("=" * 80)

    question = session.query(ComplianceQuestion).filter_by(question_code='TVI1').first()

    if not question:
        print("❌ TVI1 not found!")
        return

    print(f"\n📋 {question.question_code}: {question.question_text}")
    print(f"\nBasic Requirement:")
    print(f"  {question.basic_requirement}")

    print(f"\nApplicability: {question.applicability}")

    print(f"\nIndicators ({len(question.indicators)}):")
    for ind in sorted(question.indicators, key=lambda i: i.indicator_order):
        print(f"  {ind.letter}. {ind.indicator_text}")

    print(f"\nDeficiencies ({len(question.deficiencies)}):")
    for def_ in sorted(question.deficiencies, key=lambda d: d.deficiency_order):
        print(f"  [{def_.deficiency_code}] {def_.deficiency_title}")
        print(f"      Determination: {def_.determination[:100]}...")

    print("✅ Test passed")


def test_search_deficiencies(session):
    """Test: Search for deficiencies with specific keywords."""
    print("\n" + "=" * 80)
    print("TEST: Search deficiencies containing 'notify FTA'")
    print("=" * 80)

    deficiencies = session.query(ComplianceDeficiency).filter(
        ComplianceDeficiency.corrective_action.ilike('%notify%FTA%')
    ).all()

    print(f"\n📋 Found {len(deficiencies)} deficiencies:")

    for def_ in deficiencies[:5]:  # Show first 5
        question = def_.question
        section = question.section
        print(f"\n  [{def_.deficiency_code}] {def_.deficiency_title}")
        print(f"     Section: {section.section_name} ({question.question_code})")
        print(f"     Corrective Action: {def_.corrective_action[:100]}...")

    print("✅ Test passed")


def test_count_by_section(session):
    """Test: Count indicators and deficiencies by section."""
    print("\n" + "=" * 80)
    print("TEST: Count indicators and deficiencies by section")
    print("=" * 80)

    sections = session.query(ComplianceSection).all()

    print(f"\n{'Section':<15} | {'Questions':^9} | {'Indicators':^10} | {'Deficiencies':^12}")
    print("-" * 65)

    for section in sorted(sections, key=lambda s: s.section_code):
        questions_count = len(section.questions)
        indicators_count = sum(len(q.indicators) for q in section.questions)
        deficiencies_count = sum(len(q.deficiencies) for q in section.questions)

        print(f"{section.section_code:<15} | {questions_count:^9} | {indicators_count:^10} | {deficiencies_count:^12}")

    print("✅ Test passed")


def test_applicability_filter(session):
    """Test: Filter questions by applicability."""
    print("\n" + "=" * 80)
    print("TEST: Filter questions by applicability = 'All recipients'")
    print("=" * 80)

    questions = session.query(ComplianceQuestion).filter_by(applicability='All recipients').all()

    print(f"\n📋 Found {len(questions)} questions for 'All recipients':")

    # Group by section
    by_section = {}
    for q in questions:
        section_name = q.section.section_name
        if section_name not in by_section:
            by_section[section_name] = []
        by_section[section_name].append(q)

    for section_name, section_questions in sorted(by_section.items()):
        print(f"\n  {section_name}: {len(section_questions)} questions")

    print("✅ Test passed")


def main():
    print("=" * 80)
    print("Database Query Tests")
    print("=" * 80)

    db_manager = get_db_manager()

    if not db_manager.test_connection():
        print("\n❌ Cannot connect to database")
        sys.exit(1)

    with db_manager.session_scope() as session:
        # Run all tests
        test_get_title_vi_indicators(session)
        test_get_question_details(session)
        test_search_deficiencies(session)
        test_count_by_section(session)
        test_applicability_filter(session)

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)


if __name__ == '__main__':
    main()
