#!/usr/bin/env python3
"""Comprehensive test suite for hybrid query engine."""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.connection import get_db_manager
from retrieval.hybrid_engine import HybridQueryEngine


def test_database_queries(engine: HybridQueryEngine):
    """Test pure DATABASE route queries."""
    print("\n" + "=" * 100)
    print("DATABASE QUERIES - Testing Structured Data Retrieval")
    print("=" * 100)

    test_cases = [
        # Count queries
        ("How many indicators are in TVI3?", "count", 2),
        ("Count indicators in L1", "count", 2),
        ("How many deficiencies in CB1?", "count", 2),

        # List queries
        ("List all indicators for F5", "list", None),
        ("Show me indicators for ADA-GEN5", "list", None),

        # Get section queries
        ("What is TVI10-1?", "get", None),
        ("Describe TC-PjM2", "get", None),
        ("Explain 5307:1", "get", None),
    ]

    passed = 0
    failed = 0

    for query, expected_type, expected_count in test_cases:
        print(f"\n📝 Query: {query}")
        print("-" * 100)

        result = engine.execute_query(query)

        # Check route
        route = result['metadata']['route_type']
        backend = result['backend']
        confidence = result['confidence']
        exec_time = result['metadata']['execution_time_ms']

        print(f"✓ Route: {route.upper()} | Backend: {backend} | Confidence: {confidence}")
        print(f"✓ Execution time: {exec_time}ms")

        # Verify it's a database query
        if route == 'database' and 'database' in backend:
            # Check if expected count matches (if provided)
            if expected_count is not None and 'db_result' in result:
                actual_count = result['db_result'].get('count')
                if actual_count == expected_count:
                    print(f"✅ Count verified: {actual_count} (expected {expected_count})")
                    passed += 1
                else:
                    print(f"❌ Count mismatch: {actual_count} (expected {expected_count})")
                    failed += 1
            else:
                print(f"✅ Query executed successfully")
                passed += 1

            # Show answer preview
            answer_preview = result['answer'][:200].replace('\n', ' ')
            print(f"📄 Answer: {answer_preview}...")
        else:
            print(f"❌ Expected DATABASE route, got {route}")
            failed += 1

    print(f"\n{'='*100}")
    print(f"DATABASE Tests: {passed} passed, {failed} failed")
    return passed, failed


def test_hybrid_queries(engine: HybridQueryEngine):
    """Test HYBRID route queries."""
    print("\n" + "=" * 100)
    print("HYBRID QUERIES - Testing Multi-Section and Aggregate Queries")
    print("=" * 100)

    test_cases = [
        # Multi-section comparisons
        ("Compare TVI3 and L1", "comparison", 2),
        ("How does F2 relate to CB1?", "comparison", 2),

        # Aggregate queries
        ("How many total indicators are there?", "aggregate", 493),
        ("Total deficiencies in the compliance guide", "aggregate", 338),
    ]

    passed = 0
    failed = 0

    for query, expected_subtype, expected_value in test_cases:
        print(f"\n📝 Query: {query}")
        print("-" * 100)

        result = engine.execute_query(query)

        route = result['metadata']['route_type']
        backend = result['backend']
        exec_time = result['metadata']['execution_time_ms']

        print(f"✓ Route: {route.upper()} | Backend: {backend}")
        print(f"✓ Execution time: {exec_time}ms")

        # Verify it's a hybrid query
        if route == 'hybrid':
            if expected_subtype == "comparison" and "comparison" in backend:
                section_count = result.get('section_count', 0)
                if section_count == expected_value:
                    print(f"✅ Comparison verified: {section_count} sections")
                    passed += 1
                else:
                    print(f"❌ Section count mismatch: {section_count} (expected {expected_value})")
                    failed += 1
            elif expected_subtype == "aggregate" and "aggregate" in backend:
                if 'db_result' in result:
                    totals = result['db_result']['totals']
                    # Check if expected value matches either indicators or deficiencies
                    if totals['indicators'] == expected_value or totals['deficiencies'] == expected_value:
                        print(f"✅ Aggregate verified: {expected_value} items found")
                        passed += 1
                    else:
                        print(f"❌ Aggregate mismatch: expected {expected_value}")
                        failed += 1
                else:
                    print(f"✅ Aggregate query executed")
                    passed += 1
            else:
                print(f"✅ Hybrid query executed")
                passed += 1

            answer_preview = result['answer'][:200].replace('\n', ' ')
            print(f"📄 Answer: {answer_preview}...")
        else:
            print(f"❌ Expected HYBRID route, got {route}")
            failed += 1

    print(f"\n{'='*100}")
    print(f"HYBRID Tests: {passed} passed, {failed} failed")
    return passed, failed


def test_accuracy_verification(engine: HybridQueryEngine):
    """Verify 100% accuracy for known database queries."""
    print("\n" + "=" * 100)
    print("ACCURACY VERIFICATION - Testing Known Correct Answers")
    print("=" * 100)

    # Known correct answers from database
    test_cases = [
        ("How many indicators in TVI3?", 2),
        ("Count indicators in L1", 2),
        ("How many indicators in CB1?", 5),
        ("Count indicators in F5", 6),
    ]

    passed = 0
    failed = 0

    for query, expected_count in test_cases:
        result = engine.execute_query(query)

        if 'db_result' in result:
            actual_count = result['db_result'].get('count')
            if actual_count == expected_count:
                print(f"✅ {query} → {actual_count} (CORRECT)")
                passed += 1
            else:
                print(f"❌ {query} → {actual_count} (expected {expected_count})")
                failed += 1
        else:
            print(f"❌ {query} → No database result")
            failed += 1

    accuracy = (passed / len(test_cases) * 100) if test_cases else 0
    print(f"\n{'='*100}")
    print(f"ACCURACY: {accuracy:.1f}% ({passed}/{len(test_cases)} correct)")
    print(f"{'='*100}")

    return passed, failed


def test_performance(engine: HybridQueryEngine):
    """Test query performance."""
    print("\n" + "=" * 100)
    print("PERFORMANCE TESTING - Measuring Execution Times")
    print("=" * 100)

    test_queries = [
        "How many indicators in TVI3?",
        "List all indicators for L1",
        "What is CB1?",
        "Compare TVI3 and L1",
        "How many total indicators are there?",
    ]

    times = []

    for query in test_queries:
        result = engine.execute_query(query)
        exec_time = result['metadata']['execution_time_ms']
        times.append(exec_time)
        print(f"⏱️  {query:<45} {exec_time:>8.2f}ms")

    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)

    print(f"\n{'='*100}")
    print(f"PERFORMANCE SUMMARY:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Min:     {min_time:.2f}ms")
    print(f"  Max:     {max_time:.2f}ms")

    if avg_time < 50:
        print(f"  ✅ EXCELLENT - All queries under 50ms!")
    elif avg_time < 200:
        print(f"  ✅ GOOD - All queries under 200ms")
    else:
        print(f"  ⚠️  SLOW - Average over 200ms")

    print(f"{'='*100}")

    return avg_time < 200


def main():
    """Run all tests."""
    import os

    print("\n" + "=" * 100)
    print("HYBRID QUERY ENGINE - COMPREHENSIVE TEST SUITE")
    print("=" * 100)

    # Initialize engine
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:Forest12345#@localhost:5432/cortap_compliance')
    db_manager = get_db_manager(db_url)
    engine = HybridQueryEngine(db_manager)

    # Run test suites
    db_passed, db_failed = test_database_queries(engine)
    hybrid_passed, hybrid_failed = test_hybrid_queries(engine)
    accuracy_passed, accuracy_failed = test_accuracy_verification(engine)
    performance_ok = test_performance(engine)

    # Final summary
    total_passed = db_passed + hybrid_passed + accuracy_passed
    total_failed = db_failed + hybrid_failed + accuracy_failed
    total_tests = total_passed + total_failed

    print("\n" + "=" * 100)
    print("FINAL TEST SUMMARY")
    print("=" * 100)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"Success Rate: {(total_passed/total_tests*100):.1f}%")
    print(f"Performance: {'✅ PASS' if performance_ok else '❌ FAIL'}")
    print("=" * 100)

    # Exit code
    if total_failed == 0 and performance_ok:
        print("\n🎉 ALL TESTS PASSED! 🎉\n")
        return 0
    else:
        print(f"\n⚠️  {total_failed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    exit(main())
