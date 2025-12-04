"""PDF processing and text extraction."""
import os
from pathlib import Path
from typing import List, Dict
from pypdf import PdfReader


class PDFProcessor:
    """Extract text and metadata from PDF chunks."""

    def __init__(self, chunks_directory: str):
        self.chunks_directory = Path(chunks_directory)

    def extract_metadata_from_filename(self, filename: str) -> Dict[str, any]:
        """Parse metadata from filename pattern: {Category}_chunk_{N}.pdf"""
        name_without_ext = filename.replace(".pdf", "")
        parts = name_without_ext.split("_chunk_")

        if len(parts) == 2:
            category = parts[0]
            chunk_number = int(parts[1])
        else:
            category = "Unknown"
            chunk_number = 0

        return {
            "chunk_id": name_without_ext,
            "category": category,
            "chunk_number": chunk_number,
            "file_path": str(self.chunks_directory / filename),
        }

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract all text from a PDF file."""
        try:
            reader = PdfReader(pdf_path)
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n".join(text_parts)
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
            return ""

    def process_all_chunks(self) -> List[Dict[str, any]]:
        """Process all PDF chunks and return list of documents with metadata."""
        documents = []

        if not self.chunks_directory.exists():
            raise FileNotFoundError(f"Chunks directory not found: {self.chunks_directory}")

        pdf_files = sorted(self.chunks_directory.glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files to process")

        for pdf_file in pdf_files:
            print(f"Processing {pdf_file.name}...")

            # Extract metadata
            metadata = self.extract_metadata_from_filename(pdf_file.name)

            # Extract text
            text = self.extract_text_from_pdf(pdf_file)

            if text.strip():
                documents.append({
                    "text": text,
                    "metadata": metadata,
                })
            else:
                print(f"Warning: No text extracted from {pdf_file.name}")

        print(f"Successfully processed {len(documents)} documents")
        return documents
