"""
Test script for quick fixes:
1. Source collection metadata display
2. Recipient name extraction (multi-word)
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from retrieval.hybrid_engine import HybridQueryEngine
from retrieval.rag_pipeline import RAGPipeline
from database.connection import DatabaseManager
import chromadb
from langchain_openai import OpenAIEmbeddings


class MockEmbeddingManager:
    """Mock embedding manager for testing."""
    def __init__(self, collection):
        self.collection = collection
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            dimensions=3072
        )


def test_source_collection_metadata():
    """Test that source_collection is present in response sources."""
    print("\n" + "=" * 80)
    print("TEST 1: Source Collection Metadata Display")
    print("=" * 80)

    # Initialize components
    db_manager = DatabaseManager()
    persist_directory = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    chroma_client = chromadb.PersistentClient(path=persist_directory)

    try:
        compliance_collection = chroma_client.get_collection("compliance_guide")
        historical_collection = chroma_client.get_collection("historical_audits")
    except Exception as e:
        print(f"❌ Failed to load collections: {e}")
        return

    embedding_manager = MockEmbeddingManager(compliance_collection)

    # Initialize RAG pipeline
    rag_pipeline = RAGPipeline(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4-turbo-preview",
        temperature=0.0
    )

    # Initialize hybrid engine
    engine = HybridQueryEngine(
        db_manager=db_manager,
        rag_pipeline=rag_pipeline,
        embedding_manager=embedding_manager,
        historical_collection=historical_collection
    )

    # Test query that should return RAG results from both collections
    query = "What are common procurement issues?"

    print(f"\nQuery: {query}")
    print("-" * 80)

    result = engine.execute_query(query)

    # Check if sources have source_collection field
    if 'sources' in result and result['sources']:
        print(f"\n✓ Found {len(result['sources'])} sources:")
        for i, source in enumerate(result['sources'], 1):
            collection = source.get('source_collection', '❌ MISSING')
            print(f"  Source {i}: {source.get('chunk_id', 'N/A')}")
            print(f"    Collection: {collection}")
            print(f"    File path: {source.get('file_path', 'N/A')}")

            if 'source_collection' not in source:
                print("    ⚠️  WARNING: source_collection field is missing!")

        # Verify we have sources from both collections (for a procurement query)
        collections = [s.get('source_collection') for s in result['sources']]
        if 'compliance_guide' in collections:
            print("\n✓ Found compliance_guide sources")
        if 'historical_audits' in collections:
            print("✓ Found historical_audits sources")
    else:
        print("❌ No sources returned")

    print(f"\nBackend: {result.get('backend')}")
    print(f"Confidence: {result.get('confidence')}")


def test_recipient_name_extraction():
    """Test that multi-word recipient names are extracted correctly."""
    print("\n" + "=" * 80)
    print("TEST 2: Multi-Word Recipient Name Extraction")
    print("=" * 80)

    # Initialize components
    db_manager = DatabaseManager()

    # Initialize hybrid engine (minimal setup for historical queries)
    engine = HybridQueryEngine(db_manager=db_manager)

    # Test queries with multi-word recipient names
    test_cases = [
        ("What deficiencies did Alameda CTC have?", "Alameda CTC"),
        ("Tell me about GNHTD audit results", "GNHTD"),
        ("Greater New Haven Transit deficiencies", "Greater New Haven Transit"),
        ("What deficiencies did COLTS have?", "COLTS"),
    ]

    for query, expected_name in test_cases:
        print(f"\nQuery: {query}")
        print(f"Expected recipient: {expected_name}")
        print("-" * 80)

        result = engine.execute_query(query)

        # Check if the query was routed to historical database
        if result.get('backend') == 'historical_audit':
            print(f"✓ Correctly routed to historical audit backend")

            # Check answer for recipient name
            answer = result.get('answer', '')
            if expected_name.lower() in answer.lower():
                print(f"✓ Found '{expected_name}' in response")
            else:
                print(f"⚠️  Expected '{expected_name}' not found in response")
                print(f"   Answer preview: {answer[:200]}...")
        else:
            print(f"⚠️  Routed to {result.get('backend')} instead of historical_audit")
            print(f"   Answer preview: {result.get('answer', '')[:200]}...")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("QUICK FIXES TEST SUITE")
    print("=" * 80)

    # Test 1: Source collection metadata
    test_source_collection_metadata()

    # Test 2: Recipient name extraction
    test_recipient_name_extraction()

    print("\n" + "=" * 80)
    print("TESTS COMPLETE")
    print("=" * 80)
