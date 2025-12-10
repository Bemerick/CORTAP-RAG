#!/usr/bin/env python3
"""Re-ingest the full FTA guide by intelligently chunking all 23 sections."""
import os
from pathlib import Path
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ingestion import EmbeddingManager
from config import settings

# Load environment variables
load_dotenv()


def extract_full_pdf_text(pdf_path: Path) -> str:
    """Extract all text from the main PDF."""
    print(f"Reading PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    text_parts = []

    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text:
            # Add page markers to help with tracking
            text_parts.append(f"[PAGE {i}]\n{text}")

    full_text = "\n\n".join(text_parts)
    print(f"Extracted {len(reader.pages)} pages, {len(full_text)} characters")
    return full_text


def intelligent_chunk_by_sections(text: str, chunk_size: int = 2000, chunk_overlap: int = 200):
    """
    Chunk text intelligently using RecursiveCharacterTextSplitter.

    This will:
    - Preserve section boundaries when possible
    - Handle large sections by splitting at paragraph/sentence boundaries
    - Maintain context overlap between chunks
    """
    print(f"\nChunking with size={chunk_size}, overlap={chunk_overlap}")

    # Define section headers to help identify boundaries
    # These are common FTA compliance section patterns
    separators = [
        "\n\n## ",  # Level 2 headers
        "\n\n### ", # Level 3 headers
        "\n\nREVIEW AREA",  # Common FTA pattern
        "\n\nPURPOSE OF THIS REVIEW AREA",
        "\n\nINDICATORS OF COMPLIANCE",
        "\n\n",  # Double newline (paragraphs)
        "\n",    # Single newline
        ". ",    # Sentences
        " ",     # Words
    ]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len,
    )

    chunks = text_splitter.split_text(text)
    print(f"Created {len(chunks)} chunks")

    return chunks


def detect_section_category(chunk_text: str, chunk_index: int) -> str:
    """
    Detect the FTA compliance category from chunk content.

    Returns category name based on keywords found in the text.
    """
    text_lower = chunk_text.lower()

    # Define category keywords (in priority order)
    categories = {
        "ADA_Complementary_Paratransit": ["complementary paratransit", "ada paratransit", "paratransit eligibility"],
        "ADA_General": ["americans with disabilities act", "ada general", "accessible", "disability"],
        "Charter_Service": ["charter service", "charter bus", "charter operation"],
        "School_Bus": ["school bus", "school transportation", "tripper service"],
        "Disadvantaged_Business_Enterprise": ["disadvantaged business enterprise", "dbe", "small business"],
        "Drug_and_Alcohol_Testing": ["drug and alcohol", "drug testing", "alcohol testing", "fta drug"],
        "Financial_Management_and_Capacity": ["financial management", "financial capacity", "budget", "accounting"],
        "Procurement": ["procurement", "acquisition", "competitive bidding", "third party contract"],
        "Public_Transportation_Agency_Safety_Plan": ["safety plan", "public transportation agency safety", "ptasp"],
        "Satisfactory_Continuing_Control": ["satisfactory continuing control", "equipment disposition", "property management"],
        "Technical_Capacity_Award_Management": ["award management", "technical capacity", "grant management"],
        "Technical_Capacity_Program_Management": ["program management", "project management"],
        "Title_VI": ["title vi", "civil rights", "nondiscrimination", "equal access"],
    }

    # Check for exact matches first
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category

    # Fallback: use chunk index to roughly map to sections
    # This is a backup if keyword detection fails
    sections_per_chunk = 23 / 100  # Rough estimate
    estimated_section = int(chunk_index * sections_per_chunk) % 13

    fallback_categories = [
        "ADA_General", "ADA_Complementary_Paratransit", "Charter_Service",
        "Disadvantaged_Business_Enterprise", "Drug_and_Alcohol_Testing",
        "Financial_Management_and_Capacity", "Procurement", "Title_VI",
        "Public_Transportation_Agency_Safety_Plan", "Satisfactory_Continuing_Control",
        "Technical_Capacity_Award_Management", "Technical_Capacity_Program_Management",
        "School_Bus"
    ]

    return fallback_categories[estimated_section]


def create_documents_from_chunks(chunks: list) -> list:
    """Convert text chunks into document format with metadata."""
    documents = []

    print("\nCreating documents with metadata...")
    for i, chunk_text in enumerate(chunks, 1):
        # Detect category from content
        category = detect_section_category(chunk_text, i)

        # Create document
        doc = {
            "text": chunk_text,
            "metadata": {
                "chunk_id": f"{category}_chunk_{i}",
                "category": category,
                "chunk_number": i,
                "source": "Fiscal-Year-2025-Contractor-Manual",
                "file_path": "docs/guide/Fiscal-Year-2025-Contractor-Manual_0.pdf",
            }
        }
        documents.append(doc)

        # Print progress every 10 chunks
        if i % 10 == 0:
            print(f"  Processed {i}/{len(chunks)} chunks...")

    print(f"Created {len(documents)} documents")

    # Print category distribution
    print("\nCategory distribution:")
    from collections import Counter
    categories = [doc["metadata"]["category"] for doc in documents]
    category_counts = Counter(categories)
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count} chunks")

    return documents


def main():
    """Main ingestion pipeline - skips if data already exists."""
    print("=" * 70)
    print("CORTAP-RAG Full Guide Ingestion")
    print("=" * 70)

    # Initialize embedding manager first to check if data exists
    embedding_manager = EmbeddingManager(
        db_path=settings.chroma_db_path,
        openai_api_key=settings.openai_api_key,
        embedding_model=settings.embedding_model
    )

    # Check if data already exists
    current_count = embedding_manager.get_collection_count()
    if current_count > 1000:  # Expected ~1442 chunks
        print(f"\n✓ Compliance guide already ingested ({current_count} documents)")
        print("  Skipping re-ingestion to save time and API costs.")
        print("  To force re-ingestion, delete the ChromaDB collection first.")
        return

    print(f"\nCurrent collection has {current_count} documents - proceeding with ingestion...")

    # Paths
    project_root = Path(__file__).parent.parent
    main_pdf = project_root / "docs" / "guide" / "Fiscal-Year-2025-Contractor-Manual_0.pdf"

    if not main_pdf.exists():
        print(f"ERROR: Main PDF not found at {main_pdf}")
        return

    print(f"\nMain PDF: {main_pdf}")
    print(f"ChromaDB path: {settings.chroma_db_path}")
    print(f"Embedding model: {settings.embedding_model}\n")

    # Step 1: Extract full text
    print("\n[1/4] Extracting text from main PDF...")
    full_text = extract_full_pdf_text(main_pdf)

    # Step 2: Intelligent chunking
    print("\n[2/4] Chunking by sections...")
    chunks = intelligent_chunk_by_sections(
        full_text,
        chunk_size=2000,  # ~500 words, good for semantic search
        chunk_overlap=200  # 10% overlap to preserve context
    )

    # Step 3: Create documents with metadata
    print("\n[3/4] Creating documents with metadata...")
    documents = create_documents_from_chunks(chunks)

    # Step 4: Ingest into ChromaDB
    print("\n[4/4] Ingesting into ChromaDB...")

    # Clear existing collection if it has some data but not complete
    if current_count > 0:
        print(f"\nClearing incomplete collection ({current_count} documents)...")
        embedding_manager.clear_collection()

    # Ingest new documents
    print("\nGenerating embeddings and storing...")
    embedding_manager.ingest_documents(documents, batch_size=10)

    # Summary
    print("\n" + "=" * 70)
    print("Ingestion Complete!")
    print("=" * 70)
    print(f"Total documents indexed: {embedding_manager.get_collection_count()}")
    print(f"Database location: {settings.chroma_db_path}")
    print("\nAll 23 sections should now be represented in the database.")


if __name__ == "__main__":
    main()
