"""
Update Recipient Names in Database

Reads recipient_name_mappings.txt and updates the database with correct recipient information.

Usage:
    1. Review/edit recipient_name_mappings.txt with correct names
    2. Run: python update_recipient_names.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.models import Recipient, AuditReview
from database.connection import DatabaseManager


def parse_mappings_file(filepath: str):
    """Parse the recipient_name_mappings.txt file."""
    mappings = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse: source_file | recipient_name | acronym | city | state | region
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                mapping = {
                    'source_file': parts[0],
                    'recipient_name': parts[1],
                    'acronym': parts[2],
                    'city': parts[3],
                    'state': parts[4],
                    'region_number': int(parts[5]) if parts[5].isdigit() else None
                }
                mappings.append(mapping)

    return mappings


def update_recipients(mappings, dry_run=True):
    """Update recipient information in database."""
    db = DatabaseManager()
    updated = 0
    not_found = 0

    with db.get_session() as session:
        for mapping in mappings:
            source_file = mapping['source_file']

            # Find audit review by source file
            audit_review = session.query(AuditReview).filter_by(source_file=source_file).first()

            if not audit_review:
                print(f"⚠️  Not found in database: {source_file}")
                not_found += 1
                continue

            # Get the recipient
            recipient = session.query(Recipient).filter_by(id=audit_review.recipient_id).first()

            if not recipient:
                print(f"⚠️  No recipient found for: {source_file}")
                not_found += 1
                continue

            # Show what would be updated
            print(f"\n📝 Update for: {source_file}")
            print(f"   Current: {recipient.name} ({recipient.acronym})")
            print(f"   New:     {mapping['recipient_name']} ({mapping['acronym']})")
            print(f"   Location: {mapping['city']}, {mapping['state']}")
            print(f"   Region: {mapping['region_number']}")

            # Update recipient (both dry-run and real)
            if not dry_run:
                recipient.name = mapping['recipient_name']
                recipient.acronym = mapping['acronym']
                recipient.city = mapping['city']
                recipient.state = mapping['state']
                if mapping['region_number']:
                    recipient.region_number = mapping['region_number']

                # Update the temp recipient_id to use acronym
                if recipient.recipient_id.startswith('TEMP-'):
                    recipient.recipient_id = mapping['acronym']

            updated += 1  # Count even in dry-run

        if not dry_run:
            session.commit()
            print(f"\n✅ Committed changes to database")
        else:
            print(f"\n🔍 DRY RUN - No changes committed")

    print(f"\n{'=' * 80}")
    print(f"Summary:")
    print(f"  Total mappings: {len(mappings)}")
    print(f"  {'Would be updated' if dry_run else 'Updated'}: {updated}")
    print(f"  Not found: {not_found}")

    if dry_run:
        print(f"\nTo apply changes, run: python update_recipient_names.py --apply")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Update recipient names in database')
    parser.add_argument('--apply', action='store_true',
                        help='Apply changes (default is dry-run)')
    parser.add_argument('--mappings', default='./scripts/recipient_name_mappings.txt',
                        help='Path to mappings file')

    args = parser.parse_args()

    # Check if mappings file exists
    if not Path(args.mappings).exists():
        print(f"❌ Error: Mappings file not found: {args.mappings}")
        print(f"   Please create the file or specify correct path with --mappings")
        return 1

    print(f"Reading mappings from: {args.mappings}")
    mappings = parse_mappings_file(args.mappings)

    if not mappings:
        print(f"❌ Error: No valid mappings found in file")
        return 1

    print(f"Found {len(mappings)} mappings to process\n")

    # Update recipients
    update_recipients(mappings, dry_run=not args.apply)

    return 0


if __name__ == "__main__":
    sys.exit(main())
