"""
Extract organizational descriptions from Section III of FTA audit PDFs.

This script uses Claude AI to extract the "III. Recipient Description - 1. Organization"
section from audit reports and adds them to the historical_audits ChromaDB collection.

Usage:
    python extract_org_descriptions.py --pdf-dir "./docs/final reports/reports only"
"""
import sys
import os
import argparse
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
import anthropic
import pypdf

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import DatabaseManager
from database.models import Recipient
import chromadb
from langchain_openai import OpenAIEmbeddings


class OrganizationDescriptionExtractor:
    """Extract organization descriptions from PDFs using Claude AI."""

    def __init__(self, pdf_dir: str):
        """
        Initialize extractor.

        Args:
            pdf_dir: Directory containing PDF files
        """
        self.pdf_dir = Path(pdf_dir)
        self.db = DatabaseManager()

        # Initialize Anthropic Claude
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.claude = anthropic.Anthropic(api_key=anthropic_api_key)

        # Initialize ChromaDB
        persist_directory = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.chroma_client.get_or_create_collection(
            name="historical_audits"
        )

        # Initialize OpenAI embeddings
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            dimensions=3072,
            api_key=openai_api_key
        )

    def extract_text_from_pdf(self, pdf_path: Path, max_pages: int = 10) -> str:
        """
        Extract text from first N pages of PDF.

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to extract (Section III is usually in first 5-10 pages)

        Returns:
            Extracted text
        """
        text_chunks = []

        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            total_pages = min(len(pdf_reader.pages), max_pages)

            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text_chunks.append(page.extract_text())

        return "\n\n".join(text_chunks)

    def extract_organization_description(self, pdf_text: str, recipient_name: str) -> Dict:
        """
        Use Claude AI to extract organization description.

        Args:
            pdf_text: PDF text content
            recipient_name: Name of recipient for context

        Returns:
            Dictionary with organization description
        """
        prompt = f"""You are analyzing an FTA compliance audit report for {recipient_name}.

Extract ONLY the organization description from Section III "Recipient Description" - subsection "1. Organization".

This section typically includes:
- What type of transit agency/organization it is
- When it was established
- Geographic service area
- Population served
- Governance structure
- Key services provided
- Fleet information

Return ONLY the organization description text. If you cannot find Section III or the Organization subsection, return "NOT_FOUND".

PDF Content:
{pdf_text[:15000]}
"""

        try:
            message = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            description = message.content[0].text.strip()

            if "NOT_FOUND" in description:
                return {"found": False, "description": None}

            return {"found": True, "description": description}

        except Exception as e:
            print(f"  ❌ Claude API error: {e}")
            return {"found": False, "description": None, "error": str(e)}

    def get_recipient_from_filename(self, filename: str) -> Dict:
        """
        Extract recipient info from filename.

        Args:
            filename: PDF filename

        Returns:
            Dictionary with recipient info or None
        """
        # Extract acronym from filename patterns like:
        # "01_CT_1337_GNHTD_2023_TR_Final Report.pdf" -> GNHTD
        # "03_PA_COLTS_TR23_Final_Letter.pdf" -> COLTS
        # "GBT 2023 TR Final Report.pdf" -> GBT
        # "GNHTD_2023_TR_Final Report.pdf" -> GNHTD

        filename_clean = filename.replace(".pdf", "")

        # Try underscore-separated parts first
        parts = filename_clean.split("_")

        # Skip state codes and common words
        skip_words = {'CT', 'MA', 'ME', 'NH', 'PA', 'VA', 'DE', 'WV', 'TR', 'SMR', 'FY',
                      'Final', 'Report', 'Letter', 'TGC', 'Signature', 'TC', 'R3', 'Draft',
                      'CL', 'ERF', 'and', 'Cover'}

        # Find acronym in parts (usually 2-10 uppercase letters)
        for part in parts:
            part_clean = part.strip()
            if len(part_clean) >= 2 and len(part_clean) <= 10 and part_clean.isupper() and part_clean.isalpha():
                if part_clean not in skip_words:
                    return {"acronym": part_clean}

        # Try space-separated for files like "GBT 2023 TR Final Report.pdf"
        parts_space = filename_clean.split(" ")
        for part in parts_space:
            part_clean = part.strip()
            if len(part_clean) >= 2 and len(part_clean) <= 10 and part_clean.isupper() and part_clean.isalpha():
                if part_clean not in skip_words:
                    return {"acronym": part_clean}

        # Special cases - extract from longer names
        # "Bangor_2023_TR_Final Report.pdf" -> check database for "Bangor"
        # Return the first capitalized word that might be a city/agency name
        for part in parts + parts_space:
            part_clean = part.strip()
            if len(part_clean) >= 4 and part_clean[0].isupper() and not part_clean.isupper():
                # This might be a city name, try to match in database by name
                return {"name_hint": part_clean}

        return None

    def match_recipient_in_db(self, identifier: str, is_name_hint: bool = False):
        """
        Find recipient in database by acronym or name hint.

        Args:
            identifier: Recipient acronym or name hint
            is_name_hint: If True, search by name instead of acronym

        Returns:
            Recipient object or None
        """
        from sqlalchemy import func, or_

        with self.db.get_session() as session:
            if is_name_hint:
                # Search by name or city (case-insensitive partial match)
                recipient = session.query(Recipient).filter(
                    or_(
                        func.lower(Recipient.name).like(f"%{identifier.lower()}%"),
                        func.lower(Recipient.city).like(f"%{identifier.lower()}%")
                    )
                ).first()
            else:
                # Search by exact acronym
                recipient = session.query(Recipient).filter(
                    Recipient.acronym == identifier
                ).first()

            if recipient:
                return {
                    "id": recipient.id,
                    "name": recipient.name,
                    "acronym": recipient.acronym,
                    "city": recipient.city,
                    "state": recipient.state,
                    "region": recipient.region_number
                }

        return None

    def process_pdfs(self):
        """Process all PDFs and extract organization descriptions."""
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files\n")

        successful = 0
        not_found = 0
        errors = 0
        documents_to_add = []

        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")

            # Get recipient from filename
            recipient_info = self.get_recipient_from_filename(pdf_path.name)
            if not recipient_info:
                print(f"  ⚠️ Could not extract identifier from filename")
                errors += 1
                continue

            # Match with database
            if "acronym" in recipient_info:
                acronym = recipient_info["acronym"]
                recipient = self.match_recipient_in_db(acronym, is_name_hint=False)
                identifier = acronym
            elif "name_hint" in recipient_info:
                name_hint = recipient_info["name_hint"]
                recipient = self.match_recipient_in_db(name_hint, is_name_hint=True)
                identifier = name_hint
            else:
                print(f"  ⚠️ Invalid recipient info")
                errors += 1
                continue

            if not recipient:
                print(f"  ⚠️ Recipient '{identifier}' not found in database")
                errors += 1
                continue

            print(f"  ✓ Matched: {recipient['name']} ({recipient['acronym']})")

            # Extract PDF text
            try:
                pdf_text = self.extract_text_from_pdf(pdf_path, max_pages=10)
            except Exception as e:
                print(f"  ❌ PDF extraction error: {e}")
                errors += 1
                continue

            # Extract organization description with Claude
            result = self.extract_organization_description(pdf_text, recipient['name'])

            if not result["found"]:
                print(f"  ⚠️ Organization description not found in PDF")
                not_found += 1
                continue

            description = result["description"]
            print(f"  ✓ Extracted {len(description)} characters")

            # Prepare document for ChromaDB
            document_text = f"""Organization Description

Recipient: {recipient['name']} ({recipient['acronym']})
Location: {recipient['city']}, {recipient['state']}
FTA Region: {recipient['region']}

{description}
"""

            metadata = {
                "recipient_name": recipient['name'],
                "recipient_acronym": recipient['acronym'],
                "recipient_city": recipient['city'],
                "recipient_state": recipient['state'],
                "region_number": recipient['region'],
                "document_type": "organization_description"
            }

            documents_to_add.append({
                "id": f"org_desc_{recipient['id']}",
                "text": document_text,
                "metadata": metadata
            })

            successful += 1

        # Add all documents to ChromaDB
        if documents_to_add:
            print(f"\n{'='*80}")
            print(f"Adding {len(documents_to_add)} organization descriptions to ChromaDB...")

            ids = [d["id"] for d in documents_to_add]
            documents = [d["text"] for d in documents_to_add]
            metadatas = [d["metadata"] for d in documents_to_add]

            # Generate embeddings
            print("  Generating embeddings with OpenAI...")
            embeddings = self.embeddings.embed_documents(documents)
            print(f"  ✓ Generated {len(embeddings)} embeddings")

            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

            print(f"  ✓ Added to ChromaDB collection 'historical_audits'")

        # Summary
        print(f"\n{'='*80}")
        print(f"EXTRACTION SUMMARY")
        print(f"{'='*80}")
        print(f"Total PDFs: {len(pdf_files)}")
        print(f"Successful: {successful}")
        print(f"Not Found: {not_found}")
        print(f"Errors: {errors}")
        print(f"{'='*80}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Extract organization descriptions from audit PDFs')
    parser.add_argument('--pdf-dir', default='./docs/final reports/reports only',
                        help='Directory containing PDF files')

    args = parser.parse_args()

    try:
        extractor = OrganizationDescriptionExtractor(args.pdf_dir)
        extractor.process_pdfs()

        print(f"\n✅ Extraction complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
