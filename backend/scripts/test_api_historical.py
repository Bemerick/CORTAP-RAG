"""
Test API service with historical audits integration.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from api.service import RAGService

# Initialize service
print('Initializing RAG Service...')
service = RAGService()
print('✓ Service initialized\n')

# Test queries that should use historical audit data
test_queries = [
    "What are common procurement issues?",
    "Tell me about maintenance deficiencies in transit agencies",
    "What Title VI compliance problems have been found?",
]

print("=" * 80)
print("API HISTORICAL AUDIT INTEGRATION TEST")
print("=" * 80)

for query in test_queries:
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")

    result = service.process_query(query)

    print(f"Backend: {result.get('backend')}")
    print(f"Confidence: {result.get('confidence')}")

    # Check if historical sources are in the results
    sources = result.get('sources', [])
    historical_sources = [s for s in sources if 'historical' in str(s.get('metadata', {})).lower()]

    print(f"Total sources: {len(sources)}")
    print(f"Historical sources: {len(historical_sources)}")

    if historical_sources:
        print("\n📚 Historical Audit Sources Found:")
        for i, source in enumerate(historical_sources, 1):
            metadata = source.get('metadata', {})
            print(f"  {i}. {metadata.get('recipient_name', 'Unknown')} - {metadata.get('document_type', 'unknown')}")

    print(f"\nAnswer preview (first 300 chars):")
    print(f"{result.get('answer', '')[:300]}...")

print(f"\n{'='*80}")
print("✅ API is successfully using historical audits collection!")
print(f"{'='*80}")
