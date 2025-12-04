#!/usr/bin/env python3
"""Ingestion CLI script to process PDFs and populate ChromaDB."""
import os
from pathlib import Path
from dotenv import load_dotenv
from ingestion import PDFProcessor, EmbeddingManager
from config import settings

# Load environment variables
load_dotenv()


def main():
    """Main ingestion pipeline."""
    print("=" * 60)
    print("CORTAP-RAG Ingestion Pipeline")
    print("=" * 60)

    # Determine chunks directory (relative to project root)
    project_root = Path(__file__).parent.parent
    chunks_dir = project_root / "docs" / "guide" / "chunks"

    print(f"\nChunks directory: {chunks_dir}")
    print(f"ChromaDB path: {settings.chroma_db_path}")
    print(f"Embedding model: {settings.embedding_model}\n")

    # Step 1: Process PDFs
    print("\n[1/3] Processing PDF files...")
    processor = PDFProcessor(str(chunks_dir))
    documents = processor.process_all_chunks()

    if not documents:
        print("Error: No documents were processed. Exiting.")
        return

    # Step 2: Initialize embedding manager
    print("\n[2/3] Initializing ChromaDB and embeddings...")
    embedding_manager = EmbeddingManager(
        db_path=settings.chroma_db_path,
        openai_api_key=settings.openai_api_key,
        embedding_model=settings.embedding_model
    )

    # Clear existing data (optional - comment out to append)
    current_count = embedding_manager.get_collection_count()
    if current_count > 0:
        response = input(f"\nCollection has {current_count} documents. Clear it? (y/n): ")
        if response.lower() == 'y':
            embedding_manager.clear_collection()
            print("Collection cleared.")

    # Step 3: Ingest documents
    print("\n[3/3] Generating embeddings and storing in ChromaDB...")
    embedding_manager.ingest_documents(documents, batch_size=5)

    print("\n" + "=" * 60)
    print("Ingestion Complete!")
    print("=" * 60)
    print(f"Total documents indexed: {embedding_manager.get_collection_count()}")
    print(f"Database location: {settings.chroma_db_path}")


if __name__ == "__main__":
    main()
