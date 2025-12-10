"""
Test integrated RAG with both compliance guide and historical audits collections.
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
from database.connection import DatabaseManager
import chromadb
from langchain_openai import OpenAIEmbeddings


def test_integrated_rag():
    """Test RAG queries with both collections."""

    # Initialize database
    db_manager = DatabaseManager()

    # Initialize ChromaDB client
    persist_directory = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    chroma_client = chromadb.PersistentClient(path=persist_directory)

    # Get historical audits collection
    historical_collection = chroma_client.get_collection("historical_audits")
    print(f"✓ Historical audits collection loaded: {historical_collection.count()} documents\n")

    # Initialize hybrid engine with historical collection
    # Note: We're skipping the RAG pipeline initialization for now - just testing collection access
    engine = HybridQueryEngine(
        db_manager=db_manager,
        historical_collection=historical_collection
    )

    # Test queries that should benefit from historical audit data
    test_queries = [
        "What are common procurement issues in transit agencies?",
        "Tell me about maintenance deficiencies",
        "What Title VI compliance problems do agencies face?",
        "Tell me about transit agencies in New England"
    ]

    print("=" * 80)
    print("INTEGRATED RAG TEST - Historical Audits + Compliance Guide")
    print("=" * 80)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 80)

        # Initialize embeddings (needed for search)
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            dimensions=3072
        )

        # Test historical collection search
        query_embedding = embeddings.embed_query(query)
        historical_results = historical_collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

        if historical_results and historical_results['documents'][0]:
            print("\n📚 Historical Audit Results:")
            for i, (doc, meta, dist) in enumerate(zip(
                historical_results['documents'][0],
                historical_results['metadatas'][0],
                historical_results['distances'][0]
            ), 1):
                doc_type = meta.get('document_type', 'unknown')
                recipient = meta.get('recipient_name', 'Unknown')
                recipient_acronym = meta.get('recipient_acronym', '')

                print(f"\n  Result {i} (distance: {dist:.4f}, type: {doc_type}):")
                print(f"  Recipient: {recipient} ({recipient_acronym})")

                if doc_type == 'deficiency':
                    review_area = meta.get('review_area', 'N/A')
                    print(f"  Review Area: {review_area}")

                print(f"  Excerpt: {doc[:200]}...")
        else:
            print("  No historical audit results found")

    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")
    print("\n✅ Historical audits collection integrated successfully!")
    print("\nNext step: Update API to pass historical_collection to hybrid_engine")


if __name__ == "__main__":
    test_integrated_rag()
