#!/usr/bin/env python3
"""
Initialize database - create tables only (no data).

Usage:
    python scripts/init_db.py
    python scripts/init_db.py --database-url postgresql://user:pass@host/db
    python scripts/init_db.py --drop  # Drop tables first
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_db_manager


def main():
    parser = argparse.ArgumentParser(description='Initialize database tables')
    parser.add_argument(
        '--database-url',
        type=str,
        help='PostgreSQL connection string'
    )
    parser.add_argument(
        '--drop',
        action='store_true',
        help='Drop existing tables first'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Database Initialization")
    print("=" * 60)

    db_manager = get_db_manager(args.database_url)

    # Test connection
    if not db_manager.test_connection():
        print(f"\n❌ Cannot connect to database: {db_manager.database_url}")
        sys.exit(1)

    # Drop tables if requested
    if args.drop:
        print("\n⚠️  Dropping existing tables...")
        db_manager.drop_tables()

    # Create tables
    print("\n🔨 Creating database tables...")
    db_manager.create_tables()

    print("\n✅ Database initialized successfully!")
    print(f"   URL: {db_manager.database_url}")
    print("\nNext steps:")
    print("  1. Ingest data: python scripts/ingest_structured_data.py")


if __name__ == '__main__':
    main()
