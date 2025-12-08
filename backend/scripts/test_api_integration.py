#!/usr/bin/env python3
"""Test API integration with hybrid query engine."""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from api.service import RAGService


def test_service_initialization():
    """Test that RAGService initializes hybrid engine correctly."""
    print("\n" + "=" * 80)
    print("TEST 1: RAGService Initialization")
    print("=" * 80)

    service = RAGService()

    # Check if hybrid engine is initialized
    if service.hybrid_engine:
        print("✅ HybridQueryEngine initialized successfully")
        print(f"   - Database manager: {service.db_manager is not None}")
        print(f"   - RAG pipeline: {service.rag_pipeline is not None}")
        print(f"   - Hybrid retriever: {service.hybrid_retriever is not None}")
    else:
        print("⚠️  HybridQueryEngine not initialized (DATABASE_URL not set)")
        print("   - Service will fall back to pure RAG mode")

    return service


def test_database_query(service: RAGService):
    """Test a database query."""
    print("\n" + "=" * 80)
    print("TEST 2: Database Query")
    print("=" * 80)

    question = "How many indicators are in TVI3?"
    print(f"Query: {question}")
    print("-" * 80)

    response = service.process_query(question)

    print(f"\n✓ Backend: {response.get('backend', 'unknown')}")
    print(f"✓ Confidence: {response.get('confidence', 'unknown')}")

    if 'metadata' in response:
        metadata = response['metadata']
        print(f"✓ Route: {metadata.get('route_type', 'unknown')}")
        print(f"✓ Execution time: {metadata.get('execution_time_ms', 0):.2f}ms")

    answer_preview = response['answer'][:200].replace('\n', ' ')
    print(f"\n📄 Answer: {answer_preview}...")

    # Validation
    if response.get('backend', '').startswith('database'):
        print("\n✅ DATABASE query successful")
        return True
    else:
        print("\n⚠️  Expected database backend")
        return False


def test_hybrid_query(service: RAGService):
    """Test a hybrid query."""
    print("\n" + "=" * 80)
    print("TEST 3: Hybrid Query")
    print("=" * 80)

    question = "Compare TVI3 and L1"
    print(f"Query: {question}")
    print("-" * 80)

    response = service.process_query(question)

    print(f"\n✓ Backend: {response.get('backend', 'unknown')}")
    print(f"✓ Confidence: {response.get('confidence', 'unknown')}")

    if 'metadata' in response:
        metadata = response['metadata']
        print(f"✓ Route: {metadata.get('route_type', 'unknown')}")
        print(f"✓ Execution time: {metadata.get('execution_time_ms', 0):.2f}ms")

    answer_preview = response['answer'][:200].replace('\n', ' ')
    print(f"\n📄 Answer: {answer_preview}...")

    # Validation
    if response.get('backend', '') in ['hybrid', 'database_comparison']:
        print("\n✅ HYBRID query successful")
        return True
    else:
        print("\n⚠️  Expected hybrid or database_comparison backend")
        return False


def test_response_format(service: RAGService):
    """Test that response has required API fields."""
    print("\n" + "=" * 80)
    print("TEST 4: Response Format Validation")
    print("=" * 80)

    question = "List indicators for L1"
    response = service.process_query(question)

    required_fields = ['answer', 'confidence', 'sources', 'ranked_chunks', 'backend', 'metadata']
    missing_fields = []

    for field in required_fields:
        if field in response:
            print(f"✅ Field '{field}': present")
        else:
            print(f"❌ Field '{field}': MISSING")
            missing_fields.append(field)

    if not missing_fields:
        print("\n✅ All required fields present")
        return True
    else:
        print(f"\n❌ Missing fields: {missing_fields}")
        return False


def main():
    """Run all tests."""
    import os

    print("\n" + "=" * 80)
    print("HYBRID QUERY ENGINE - API INTEGRATION TEST")
    print("=" * 80)

    # Check environment
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        print(f"✓ DATABASE_URL configured")
    else:
        print(f"⚠️  DATABASE_URL not set - tests will run in RAG-only mode")

    # Initialize service
    service = test_service_initialization()

    # Run tests
    passed = 0
    failed = 0

    if service.hybrid_engine:
        # Run hybrid engine tests
        if test_database_query(service):
            passed += 1
        else:
            failed += 1

        if test_hybrid_query(service):
            passed += 1
        else:
            failed += 1

        if test_response_format(service):
            passed += 1
        else:
            failed += 1

    else:
        print("\n" + "=" * 80)
        print("SKIPPING HYBRID TESTS (DATABASE_URL not configured)")
        print("=" * 80)
        print("\nTo run full tests, set DATABASE_URL environment variable:")
        print("export DATABASE_URL='postgresql://postgres:Forest12345#@localhost:5432/cortap_compliance'")

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    if passed > 0 or failed > 0:
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print("=" * 80)

        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! 🎉\n")
            return 0
        else:
            print(f"\n⚠️  {failed} test(s) failed\n")
            return 1
    else:
        print("No tests run (DATABASE_URL not configured)")
        return 0


if __name__ == "__main__":
    exit(main())
