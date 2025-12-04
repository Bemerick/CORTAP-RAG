"""Embedding generation and vector database management."""
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_openai import OpenAIEmbeddings
from typing import List, Dict
from pathlib import Path


class EmbeddingManager:
    """Manage embeddings and ChromaDB operations."""

    def __init__(self, db_path: str, openai_api_key: str, embedding_model: str = "text-embedding-3-large"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=openai_api_key
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="fta_compliance_guide",
            metadata={"description": "FTA Compliance Guide RAG Collection"}
        )

    def get_collection_count(self) -> int:
        """Get count of documents in collection."""
        return self.collection.count()

    def clear_collection(self):
        """Clear all documents from collection."""
        self.client.delete_collection("fta_compliance_guide")
        self.collection = self.client.get_or_create_collection(
            name="fta_compliance_guide",
            metadata={"description": "FTA Compliance Guide RAG Collection"}
        )

    def ingest_documents(self, documents: List[Dict[str, any]], batch_size: int = 10):
        """
        Ingest documents into ChromaDB with embeddings.

        Args:
            documents: List of dicts with 'text' and 'metadata' keys
            batch_size: Number of documents to process at once
        """
        print(f"Ingesting {len(documents)} documents into ChromaDB...")

        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            texts = [doc["text"] for doc in batch]
            metadatas = [doc["metadata"] for doc in batch]
            ids = [doc["metadata"]["chunk_id"] for doc in batch]

            print(f"Processing batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}...")

            # Generate embeddings
            embedding_vectors = self.embeddings.embed_documents(texts)

            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embedding_vectors,
                documents=texts,
                metadatas=metadatas
            )

        print(f"Ingestion complete! Total documents in collection: {self.get_collection_count()}")

    def query_collection(self, query_text: str, n_results: int = 5, filter_metadata: Dict = None):
        """
        Query the collection with a text query.

        Args:
            query_text: The query string
            n_results: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            Query results from ChromaDB
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query_text)

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )

        return results
