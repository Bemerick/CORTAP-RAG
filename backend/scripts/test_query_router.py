#!/usr/bin/env python3
"""Test script for query router classification."""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from retrieval.query_router import QueryRouter


def main():
    """Test query router with various query types."""
    router = QueryRouter()

    # Test queries organized by expected route type
    # Now testing ALL section code formats (not just TVI)
    test_cases = {
        "DATABASE": [
            # Title VI patterns
            "How many indicators of compliance are in TVI3?",
            "What is TVI10-1?",
            # Legal patterns
            "List all deficiencies in L1",
            "Count indicators in L3",
            # Finance patterns
            "Show me indicators for F5",
            "Get all questions in F2",
            # Charter Bus patterns
            "What is CB1?",
            "How many indicators in CB3?",
            # Technical Capacity patterns
            "List indicators for TC-PjM2",
            "What is TC-AM4?",
            # ADA patterns
            "Show deficiencies for ADA-GEN5",
            "Count indicators in ADA-CPT3",
            # Numeric patterns
            "What is 5307:1?",
            "List questions in 5310:2",
        ],
        "HYBRID": [
            # Cross-section comparisons
            "Compare TVI3 and L1 requirements",
            "How does F2 relate to P5?",
            "Difference between CB1 and SB2",
            # Aggregate queries
            "How many total indicators are there?",
            "All indicators across all sections",
            "Total deficiencies in the compliance guide",
            # Conceptual + section
            "What's the purpose of PTASP2 and how does it relate to safety?",
            "Why is TC-PjM3 important?",
        ],
        "RAG": [
            # Pure conceptual queries
            "What are the ADA compliance requirements?",
            "What is charter bus service?",
            "Explain procurement regulations",
            "How do transit agencies comply with safety requirements?",
            "Tell me about best practices for compliance",
            "What are the key steps for financial management?",
        ],
    }

    print("=" * 100)
    print("QUERY ROUTER TEST RESULTS")
    print("=" * 100)

    # Track accuracy
    total = 0
    correct = 0

    for expected_route, queries in test_cases.items():
        print(f"\n{'=' * 100}")
        print(f"EXPECTED ROUTE: {expected_route}")
        print(f"{'=' * 100}\n")

        for query in queries:
            total += 1
            route = router.classify_query(query)

            # Check if classification is correct
            is_correct = route.route_type.upper() == expected_route
            if is_correct:
                correct += 1
                status = "✅ CORRECT"
            else:
                status = f"❌ INCORRECT (got {route.route_type.upper()})"

            print(f"Query: {query}")
            print(f"Status: {status}")
            print(f"Route: {route.route_type.upper()} (confidence: {route.confidence:.2f})")
            print(f"Reasoning: {route.reasoning}")

            if route.section_names:
                print(f"Sections: {', '.join(route.section_names)}")

            if route.keywords:
                print(f"Keywords: {', '.join(route.keywords)}")

            print("-" * 100)

    # Print summary
    accuracy = (correct / total) * 100 if total > 0 else 0
    print(f"\n{'=' * 100}")
    print(f"SUMMARY")
    print(f"{'=' * 100}")
    print(f"Total queries tested: {total}")
    print(f"Correct classifications: {correct}")
    print(f"Incorrect classifications: {total - correct}")
    print(f"Accuracy: {accuracy:.1f}%")
    print(f"{'=' * 100}\n")


if __name__ == "__main__":
    main()
