"""
Ingest historical audit narratives into ChromaDB for semantic search.

This script:
1. Extracts deficiency descriptions and corrective actions from PostgreSQL
2. Creates rich document chunks with metadata (recipient, review area, etc.)
3. Embeds them using OpenAI embeddings
4. Stores in ChromaDB collection 'historical_audits'

Usage:
    python ingest_historical_narratives.py [--reset]
"""
import sys
import os
import argparse
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import DatabaseManager
from database.models import Recipient, AuditReview, HistoricalAssessment
from ingestion.embeddings import EmbeddingManager
import chromadb
from langchain_openai import OpenAIEmbeddings


class HistoricalNarrativeIngestor:
    """Ingest historical audit narratives into ChromaDB."""

    def __init__(self, reset: bool = False):
        """
        Initialize the ingestor.

        Args:
            reset: If True, delete and recreate the collection
        """
        self.db = DatabaseManager()
        self.collection_name = "historical_audits"
        self.reset = reset

        # Initialize ChromaDB client
        persist_directory = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)

        # Initialize OpenAI embeddings
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            dimensions=3072,
            api_key=openai_api_key
        )

        # Setup collection
        self._setup_collection()

    def _setup_collection(self):
        """Create or get the ChromaDB collection."""
        if self.reset:
            try:
                self.chroma_client.delete_collection(name=self.collection_name)
                print(f"✓ Deleted existing collection '{self.collection_name}'")
            except Exception as e:
                print(f"  (Collection didn't exist or couldn't be deleted: {e})")

        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Historical FTA audit review narratives for semantic search"}
        )
        print(f"✓ Collection '{self.collection_name}' ready")

    def extract_narratives(self) -> List[Dict[str, Any]]:
        """
        Extract deficiency narratives from database.

        Returns:
            List of narrative documents with metadata
        """
        narratives = []

        with self.db.get_session() as session:
            # Query all deficiencies with narrative text
            query = session.query(
                HistoricalAssessment,
                AuditReview,
                Recipient
            ).join(
                AuditReview, HistoricalAssessment.audit_review_id == AuditReview.id
            ).join(
                Recipient, AuditReview.recipient_id == Recipient.id
            ).filter(
                HistoricalAssessment.finding == 'D',
                HistoricalAssessment.description.isnot(None)
            )

            results = query.all()

            print(f"Found {len(results)} deficiencies with narrative text")

            for assessment, review, recipient in results:
                # Build rich narrative text
                narrative_parts = []

                # Title/Context
                narrative_parts.append(f"Review Area: {assessment.review_area}")
                narrative_parts.append(f"Recipient: {recipient.name} ({recipient.acronym})")
                narrative_parts.append(f"Location: {recipient.city}, {recipient.state}")
                narrative_parts.append(f"FTA Region: {recipient.region_number}")
                narrative_parts.append(f"Fiscal Year: {review.fiscal_year}")

                if assessment.deficiency_code:
                    narrative_parts.append(f"Deficiency Code: {assessment.deficiency_code}")

                # Main deficiency description
                narrative_parts.append(f"\nDeficiency Description:\n{assessment.description}")

                # Corrective action if available
                if assessment.corrective_action:
                    narrative_parts.append(f"\nCorrective Action Required:\n{assessment.corrective_action}")

                # Combine into single document
                document_text = "\n".join(narrative_parts)

                # Create metadata
                metadata = {
                    "assessment_id": assessment.id,
                    "recipient_name": recipient.name,
                    "recipient_acronym": recipient.acronym,
                    "recipient_city": recipient.city,
                    "recipient_state": recipient.state,
                    "region_number": recipient.region_number,
                    "fiscal_year": review.fiscal_year,
                    "review_type": review.review_type,
                    "review_area": assessment.review_area,
                    "deficiency_code": assessment.deficiency_code or "N/A",
                    "has_corrective_action": bool(assessment.corrective_action),
                    "document_type": "deficiency"
                }

                narratives.append({
                    "id": f"deficiency_{assessment.id}",
                    "text": document_text,
                    "metadata": metadata
                })

        return narratives

    def embed_and_store(self, narratives: List[Dict[str, Any]]):
        """
        Embed narratives and store in ChromaDB.

        Args:
            narratives: List of narrative documents
        """
        print(f"\nEmbedding {len(narratives)} narratives...")

        # Prepare data for ChromaDB
        ids = [n["id"] for n in narratives]
        documents = [n["text"] for n in narratives]
        metadatas = [n["metadata"] for n in narratives]

        # Generate embeddings using OpenAI
        print("  Generating embeddings with OpenAI (text-embedding-3-large)...")
        embeddings = self.embeddings.embed_documents(documents)
        print(f"  ✓ Generated {len(embeddings)} embeddings")

        # Add to ChromaDB in batches (ChromaDB has a batch limit)
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_end = min(i + batch_size, len(ids))

            self.collection.add(
                ids=ids[i:batch_end],
                embeddings=embeddings[i:batch_end],
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end]
            )

            print(f"  ✓ Added batch {i//batch_size + 1}: documents {i+1}-{batch_end}")

        print(f"\n✓ Successfully ingested {len(narratives)} narratives into ChromaDB")

    def get_statistics(self):
        """Print statistics about the collection."""
        count = self.collection.count()

        print(f"\n{'='*80}")
        print(f"HISTORICAL NARRATIVES COLLECTION STATISTICS")
        print(f"{'='*80}")
        print(f"Total Documents: {count}")

        # Sample a document to show structure
        if count > 0:
            result = self.collection.peek(limit=1)
            if result and result['documents']:
                print(f"\nSample Document Preview:")
                print(f"{'-'*80}")
                print(result['documents'][0][:500] + "..." if len(result['documents'][0]) > 500 else result['documents'][0])
                print(f"{'-'*80}")
                print(f"\nMetadata Keys: {list(result['metadatas'][0].keys())}")

        print(f"{'='*80}")

    def test_search(self, query: str, n_results: int = 3):
        """
        Test semantic search on the collection.

        Args:
            query: Search query
            n_results: Number of results to return
        """
        print(f"\n{'='*80}")
        print(f"TEST SEARCH: '{query}'")
        print(f"{'='*80}")

        query_embedding = self.embeddings.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        if results and results['documents']:
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ), 1):
                print(f"\n--- Result {i} (distance: {distance:.4f}) ---")
                print(f"Recipient: {metadata['recipient_name']} ({metadata['recipient_acronym']})")
                print(f"Review Area: {metadata['review_area']}")
                print(f"Code: {metadata['deficiency_code']}")
                print(f"\nExcerpt:\n{doc[:300]}...")
        else:
            print("No results found")

        print(f"{'='*80}")

    def run(self, test_queries: List[str] = None):
        """
        Run the full ingestion pipeline.

        Args:
            test_queries: Optional list of test queries to run after ingestion
        """
        print(f"\n{'='*80}")
        print(f"HISTORICAL NARRATIVES INGESTION")
        print(f"{'='*80}\n")

        # Step 1: Extract narratives
        print("Step 1: Extracting narratives from PostgreSQL...")
        narratives = self.extract_narratives()

        if not narratives:
            print("❌ No narratives found in database")
            return

        # Step 2: Embed and store
        print(f"\nStep 2: Embedding and storing in ChromaDB...")
        self.embed_and_store(narratives)

        # Step 3: Show statistics
        self.get_statistics()

        # Step 4: Test search (optional)
        if test_queries:
            print(f"\nStep 4: Testing semantic search...")
            for query in test_queries:
                self.test_search(query)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Ingest historical audit narratives into ChromaDB')
    parser.add_argument('--reset', action='store_true',
                        help='Delete and recreate the collection')
    parser.add_argument('--test', action='store_true',
                        help='Run test queries after ingestion')

    args = parser.parse_args()

    # Test queries for validation
    test_queries = [
        "What are common procurement issues?",
        "Maintenance deficiencies and best practices",
        "Title VI compliance problems"
    ] if args.test else None

    try:
        ingestor = HistoricalNarrativeIngestor(reset=args.reset)
        ingestor.run(test_queries=test_queries)

        print(f"\n✅ Ingestion complete!")
        print(f"\nCollection '{ingestor.collection_name}' is ready for semantic search.")

    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
