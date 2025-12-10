"""Test script for historical audit query integration."""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from retrieval.hybrid_engine import HybridQueryEngine
from database.connection import DatabaseManager


def test_historical_queries():
    """Test various historical audit queries."""

    # Initialize engine
    db_manager = DatabaseManager()
    engine = HybridQueryEngine(db_manager)

    test_queries = [
        # Recipient-specific queries
        "What deficiencies did GNHTD have?",
        "Show me AMTRAN audit results",
        "What deficiencies did COLTS have?",

        # Regional queries
        "Region 1 deficiencies",
        "Show Region 3 procurement deficiencies",

        # Common deficiencies
        "Common procurement deficiencies",
        "What are the typical deficiencies?",

        # List queries
        "List all recipients",
        "List all agencies in Region 1",
    ]

    print("=" * 80)
    print("HISTORICAL AUDIT QUERY INTEGRATION TEST")
    print("=" * 80)

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")

        try:
            result = engine.execute_query(query)

            print(f"\nRoute: {result['metadata']['route_type'].upper()}")
            print(f"Backend: {result.get('backend')}")
            print(f"Confidence: {result.get('confidence')}")
            print(f"Execution Time: {result['metadata']['execution_time_ms']}ms")
            print(f"\nAnswer Preview (first 500 chars):")
            print("-" * 80)
            print(result['answer'][:500])
            if len(result['answer']) > 500:
                print("... (truncated)")
            print("-" * 80)

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    test_historical_queries()
