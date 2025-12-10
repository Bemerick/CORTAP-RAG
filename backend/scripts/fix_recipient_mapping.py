"""
Fix Recipient Mapping - Create Separate Recipients for Each Report

The original ingestion grouped multiple reports under the same "Description" recipient.
This script creates separate recipient records for each audit review.

Usage:
    python fix_recipient_mapping.py --apply
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.models import Recipient, AuditReview
from database.connection import DatabaseManager


def parse_mappings_file(filepath: str):
    """Parse the recipient_name_mappings.txt file."""
    mappings = {}  # source_file -> mapping dict

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                source_file = parts[0]
                mappings[source_file] = {
                    'recipient_name': parts[1],
                    'acronym': parts[2],
                    'city': parts[3],
                    'state': parts[4],
                    'region_number': int(parts[5]) if parts[5].isdigit() else None
                }

    return mappings


def fix_recipients(mappings, dry_run=True):
    """Create separate recipient records for each audit review."""
    db = DatabaseManager()
    created = 0
    updated = 0
    skipped = 0

    with db.get_session() as session:
        for source_file, mapping in mappings.items():
            # Find audit review
            audit_review = session.query(AuditReview).filter_by(source_file=source_file).first()

            if not audit_review:
                print(f"⚠️  Not found: {source_file}")
                skipped += 1
                continue

            # Check if recipient already has correct name
            current_recipient = session.query(Recipient).filter_by(id=audit_review.recipient_id).first()

            if current_recipient and current_recipient.name == mapping['recipient_name']:
                print(f"✓  Already correct: {source_file} -> {mapping['recipient_name']}")
                skipped += 1
                continue

            print(f"\n📝 {source_file}")
            print(f"   Current: {current_recipient.name if current_recipient else 'None'}")
            print(f"   New:     {mapping['recipient_name']} ({mapping['acronym']})")

            if not dry_run:
                # Check if recipient with this exact name already exists
                existing = session.query(Recipient).filter_by(
                    name=mapping['recipient_name']
                ).first()

                if existing:
                    # Use existing recipient
                    audit_review.recipient_id = existing.id
                    print(f"   → Using existing recipient (ID: {existing.id})")
                    updated += 1
                else:
                    # Create new recipient
                    new_recipient = Recipient(
                        recipient_id=mapping['acronym'],
                        name=mapping['recipient_name'],
                        acronym=mapping['acronym'],
                        city=mapping['city'],
                        state=mapping['state'],
                        region_number=mapping['region_number']
                    )
                    session.add(new_recipient)
                    session.flush()

                    audit_review.recipient_id = new_recipient.id
                    print(f"   → Created new recipient (ID: {new_recipient.id})")
                    created += 1

        if not dry_run:
            session.commit()
            print(f"\n✅ Committed changes")
        else:
            print(f"\n🔍 DRY RUN - No changes committed")

        # Clean up orphaned recipients with no reviews
        if not dry_run:
            orphaned = session.query(Recipient).filter(
                ~Recipient.audit_reviews.any()
            ).all()

            if orphaned:
                print(f"\n🗑️  Cleaning up {len(orphaned)} orphaned recipients...")
                for recipient in orphaned:
                    print(f"   Deleting: {recipient.name}")
                    session.delete(recipient)
                session.commit()

    print(f"\n{'=' * 80}")
    print(f"Summary:")
    print(f"  Total mappings: {len(mappings)}")
    print(f"  {'Would be created' if dry_run else 'Created'}: {created}")
    print(f"  {'Would be updated' if dry_run else 'Updated'}: {updated}")
    print(f"  Skipped (already correct): {skipped}")

    if dry_run:
        print(f"\nTo apply changes, run: python fix_recipient_mapping.py --apply")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Fix recipient mapping - create separate recipients')
    parser.add_argument('--apply', action='store_true', help='Apply changes')
    parser.add_argument('--mappings', default='./scripts/recipient_name_mappings.txt')

    args = parser.parse_args()

    print(f"Reading mappings from: {args.mappings}")
    mappings = parse_mappings_file(args.mappings)

    if not mappings:
        print(f"❌ Error: No valid mappings found")
        return 1

    print(f"Found {len(mappings)} mappings\n")
    fix_recipients(mappings, dry_run=not args.apply)

    return 0


if __name__ == "__main__":
    sys.exit(main())
