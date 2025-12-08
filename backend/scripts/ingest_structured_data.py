#!/usr/bin/env python3
"""
Ingest FTA compliance guide JSON into PostgreSQL database.

Usage:
    python scripts/ingest_structured_data.py
    python scripts/ingest_structured_data.py --json-path /path/to/guide.json
    python scripts/ingest_structured_data.py --database-url postgresql://user:pass@host/db
    python scripts/ingest_structured_data.py --drop-existing  # CAREFUL: Drops all tables first
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import (
    ComplianceSection,
    ComplianceQuestion,
    ComplianceIndicator,
    ComplianceDeficiency
)
from database.connection import get_db_manager


def load_json_file(json_path: Path) -> Dict:
    """Load and parse JSON file."""
    print(f"\n📖 Reading JSON file: {json_path}")

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"✅ Loaded {len(data.get('sections', []))} sections")
    return data


def validate_json_structure(data: Dict) -> None:
    """Validate JSON has expected structure."""
    print("\n🔍 Validating JSON structure...")

    if 'sections' not in data:
        raise ValueError("JSON must have 'sections' key")

    sections = data['sections']
    if not sections:
        raise ValueError("No sections found in JSON")

    # Check first section has expected structure
    first_section = sections[0]
    if 'section' not in first_section:
        raise ValueError("Section missing 'section' key")

    if 'sub_areas' not in first_section:
        raise ValueError("Section missing 'sub_areas' key")

    print(f"✅ JSON structure valid ({len(sections)} sections)")


def ingest_section(session, section_data: Dict, section_order: int) -> ComplianceSection:
    """
    Ingest a single compliance section with all sub-areas.

    Args:
        session: Database session
        section_data: Section data from JSON
        section_order: Order/index of section

    Returns:
        ComplianceSection ORM object
    """
    section_info = section_data['section']

    # Create section
    section = ComplianceSection(
        section_code=section_info['id'],
        section_name=section_info['title'],
        page_range=section_info.get('page_range'),
        purpose=section_info.get('purpose')
    )

    session.add(section)
    session.flush()  # Get section.id for foreign keys

    # Track counts
    questions_count = 0
    indicators_count = 0
    deficiencies_count = 0
    seen_question_codes = set()  # Track to avoid duplicates

    # Process sub_areas (questions)
    for q_idx, sub_area in enumerate(section_data.get('sub_areas', []), 1):
        question_code = sub_area['id']

        # Skip duplicate question codes (data quality issue in JSON)
        if question_code in seen_question_codes:
            print(f"      ⚠️  Skipping duplicate question code: {question_code}")
            continue
        seen_question_codes.add(question_code)
        question = ComplianceQuestion(
            section_id=section.id,
            question_code=sub_area['id'],
            question_text=sub_area['question'],
            basic_requirement=sub_area.get('basic_requirement'),
            applicability=sub_area.get('applicability'),
            detailed_explanation=sub_area.get('detailed_explanation'),
            instructions_for_reviewer=sub_area.get('instructions_for_reviewer'),
            question_order=q_idx
        )

        session.add(question)
        session.flush()  # Get question.id for foreign keys
        questions_count += 1

        # Process indicators
        for i_idx, indicator_data in enumerate(sub_area.get('indicators_of_compliance', []), 1):
            indicator = ComplianceIndicator(
                question_id=question.id,
                letter=indicator_data['indicator_id'],
                indicator_text=indicator_data['text'],
                indicator_order=i_idx
            )
            session.add(indicator)
            indicators_count += 1

        # Process deficiencies
        for d_idx, deficiency_data in enumerate(sub_area.get('deficiencies', []), 1):
            deficiency = ComplianceDeficiency(
                question_id=question.id,
                deficiency_code=deficiency_data['code'],
                deficiency_title=deficiency_data['title'],
                determination=deficiency_data['determination'],
                corrective_action=deficiency_data.get('suggested_corrective_action'),
                deficiency_order=d_idx
            )
            session.add(deficiency)
            deficiencies_count += 1

    print(f"  ✓ {section.section_code:10} | "
          f"Q:{questions_count:3} | "
          f"I:{indicators_count:3} | "
          f"D:{deficiencies_count:3} | "
          f"{section.section_name}")

    return section


def ingest_all_sections(db_manager, json_data: Dict) -> None:
    """Ingest all sections from JSON into database."""
    print("\n📥 Ingesting data into PostgreSQL...\n")
    print(f"{'Section':<12} | {'Questions':^9} | {'Indicators':^10} | {'Deficiencies':^12} | Name")
    print("-" * 80)

    sections = json_data['sections']
    total_sections = 0
    total_questions = 0
    total_indicators = 0
    total_deficiencies = 0

    with db_manager.session_scope() as session:
        for idx, section_data in enumerate(sections, 1):
            try:
                section = ingest_section(session, section_data, idx)
                total_sections += 1
                total_questions += len(section.questions)
                total_indicators += sum(len(q.indicators) for q in section.questions)
                total_deficiencies += sum(len(q.deficiencies) for q in section.questions)

            except Exception as e:
                print(f"\n❌ Error ingesting section {section_data.get('section', {}).get('id', 'unknown')}: {e}")
                raise

    print("-" * 80)
    print(f"{'TOTAL':<12} | {total_questions:^9} | {total_indicators:^10} | {total_deficiencies:^12} | {total_sections} sections")
    print(f"\n✅ Successfully ingested all data!")


def verify_ingestion(db_manager) -> None:
    """Verify data was ingested correctly."""
    print("\n🔍 Verifying ingestion...\n")

    with db_manager.session_scope() as session:
        # Count totals
        sections_count = session.query(ComplianceSection).count()
        questions_count = session.query(ComplianceQuestion).count()
        indicators_count = session.query(ComplianceIndicator).count()
        deficiencies_count = session.query(ComplianceDeficiency).count()

        print(f"  Sections:     {sections_count:4}")
        print(f"  Questions:    {questions_count:4}")
        print(f"  Indicators:   {indicators_count:4}")
        print(f"  Deficiencies: {deficiencies_count:4}")

        # Verify Title VI specifically
        title_vi = session.query(ComplianceSection).filter_by(section_code='TVI').first()
        if title_vi:
            tvi_questions = len(title_vi.questions)
            tvi_indicators = sum(len(q.indicators) for q in title_vi.questions)
            tvi_deficiencies = sum(len(q.deficiencies) for q in title_vi.questions)

            print(f"\n  Title VI Validation:")
            print(f"    Questions:    {tvi_questions:3} (expected: 11)")
            print(f"    Indicators:   {tvi_indicators:3} (expected: 25)")
            print(f"    Deficiencies: {tvi_deficiencies:3}")

            if tvi_questions == 11 and tvi_indicators == 25:
                print("    ✅ Title VI data matches expected counts!")
            else:
                print("    ⚠️  Title VI counts don't match expected values")

        # Check for orphaned records
        orphaned_questions = session.query(ComplianceQuestion).filter(
            ~ComplianceQuestion.section_id.in_(
                session.query(ComplianceSection.id)
            )
        ).count()

        orphaned_indicators = session.query(ComplianceIndicator).filter(
            ~ComplianceIndicator.question_id.in_(
                session.query(ComplianceQuestion.id)
            )
        ).count()

        orphaned_deficiencies = session.query(ComplianceDeficiency).filter(
            ~ComplianceDeficiency.question_id.in_(
                session.query(ComplianceQuestion.id)
            )
        ).count()

        if orphaned_questions == 0 and orphaned_indicators == 0 and orphaned_deficiencies == 0:
            print(f"\n  ✅ No orphaned records found")
        else:
            print(f"\n  ⚠️  Found orphaned records:")
            print(f"    Questions: {orphaned_questions}")
            print(f"    Indicators: {orphaned_indicators}")
            print(f"    Deficiencies: {orphaned_deficiencies}")


def main():
    """Main ingestion pipeline."""
    parser = argparse.ArgumentParser(
        description='Ingest FTA compliance guide JSON into PostgreSQL'
    )
    parser.add_argument(
        '--json-path',
        type=Path,
        default=Path(__file__).parent.parent.parent / 'docs' / 'guide' / 'FTA_Complete_Extraction.json',
        help='Path to JSON file (default: docs/guide/FTA_Complete_Extraction.json)'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        help='PostgreSQL connection string (default: from DATABASE_URL env var)'
    )
    parser.add_argument(
        '--drop-existing',
        action='store_true',
        help='Drop existing tables before ingestion (CAREFUL!)'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("FTA Compliance Guide - Structured Data Ingestion")
    print("=" * 80)

    # Load JSON
    json_data = load_json_file(args.json_path)
    validate_json_structure(json_data)

    # Setup database
    db_manager = get_db_manager(args.database_url)

    # Test connection
    if not db_manager.test_connection():
        print("\n❌ Cannot connect to database. Check your DATABASE_URL.")
        print(f"   Current URL: {db_manager.database_url}")
        sys.exit(1)

    # Drop existing tables if requested
    if args.drop_existing:
        print("\n⚠️  Dropping existing tables...")
        response = input("Are you sure? This will delete all data! (yes/no): ")
        if response.lower() == 'yes':
            db_manager.drop_tables()
        else:
            print("Aborted.")
            sys.exit(0)

    # Create tables
    print("\n🔨 Creating database tables...")
    db_manager.create_tables()

    # Ingest data
    try:
        ingest_all_sections(db_manager, json_data)
        verify_ingestion(db_manager)

        print("\n" + "=" * 80)
        print("✅ INGESTION COMPLETE!")
        print("=" * 80)
        print(f"\nDatabase ready at: {db_manager.database_url}")
        print("\nNext steps:")
        print("  1. Test queries: python scripts/test_db_queries.py")
        print("  2. Build query router: backend/retrieval/query_router.py")
        print("  3. Integrate with API: backend/api/routes.py")

    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
