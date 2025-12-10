"""
Claude-based PDF extraction for FTA Audit Reports.

Uses Anthropic Claude API to extract structured data from audit reports
with better accuracy than regex-based extraction.

Usage:
    python extract_audit_reports_claude.py --input-dir "../docs/final reports/reports only" --output-dir "./extracted_data"
"""

import os
import json
import pdfplumber
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse
import logging
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ClaudeAuditExtractor:
    """Extract audit data using Claude AI."""

    def __init__(self, pdf_path: str, api_key: Optional[str] = None):
        """Initialize extractor with PDF path and API key."""
        self.pdf_path = pdf_path
        self.filename = os.path.basename(pdf_path)
        self.client = Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))

    def extract_pdf_text(self) -> str:
        """Extract full text from PDF."""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                text_parts = []
                for i, page in enumerate(pdf.pages):
                    text_parts.append(f"--- Page {i+1} ---\n{page.extract_text()}")
                return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from {self.filename}: {e}")
            return ""

    def extract_with_claude(self, pdf_text: str) -> Dict:
        """
        Use Claude to extract structured data from PDF text.

        Returns JSON with:
        - recipient info
        - review dates
        - assessments (23 review areas with findings)
        - deficiency details (only for areas with D finding)
        - awards
        - projects
        - findings_summary
        """

        extraction_prompt = f"""You are extracting data from an FTA (Federal Transit Administration) audit report.

IMPORTANT INSTRUCTIONS:
1. PRIMARY SOURCE: Use the "Summary of Findings" table (usually near the end of the report, Section V or VI) as the authoritative source for all 23 review areas and their findings
2. The Summary of Findings table has columns: Review Area | Finding | Code | Description | Corrective Action(s) | Response Due Date | Date Closed
3. Extract ALL 23 review areas from this table with their finding codes (D, ND, or NA)
4. For areas with "D" (Deficiency) findings: Also extract the DETAILED description and corrective actions from the "Results of the Review" section (Section IV)
5. For "ND" and "NA" findings: Only record the review area, finding code, and any brief info from the Summary table
6. Extract awards from the "Award and Project Activity" section (Section 2)
7. Extract projects (completed, ongoing, future) from the same section
8. DO NOT extract the executive summary deficiency table - we only need the Summary of Findings table

Extract the following information in valid JSON format:

{{
  "recipient": {{
    "name": "Full agency name",
    "acronym": "Agency acronym",
    "city": "City name or null",
    "state": "Two-letter state code or null",
    "region_number": FTA region number (1-10) or null
  }},
  "review_info": {{
    "fiscal_year": "FY2023",
    "review_type": "TR, SMR, or Combined",
    "report_date": "Month Day, Year or null"
  }},
  "assessments": [
    {{
      "review_area": "Legal",
      "finding": "D, ND, or NA",
      "deficiency_code": "Code from Summary of Findings table (e.g., L1, P4-1, TC-PjM3-1, SCC8-4, M5-1) or null",
      "description": "DETAILED description from Results of Review section (ONLY if finding is D, otherwise null)",
      "corrective_action": "DETAILED corrective actions from Results of Review section (ONLY if finding is D, otherwise null)",
      "response_due_date": "Date from Summary of Findings table or null",
      "date_closed": "Date closed from Summary of Findings table or null"
    }}
    // ... repeat for ALL 23 review areas from Summary of Findings table
  ],
  "awards": [
    {{
      "award_number": "PA-2020-046",
      "award_year": "2020",
      "description": "Award description",
      "amount": 1286868.00
    }}
  ],
  "projects": [
    {{
      "project_type": "completed",  // or "ongoing" or "future"
      "description": "Project description",
      "completion_date": "August 2021 or null",
      "funding_sources": "FTA & PennDOT or null"
    }}
  ]
}}

The 23 standard review areas are:
1. Legal
2. Financial Management and Capacity
3. Technical Capacity - Award Management
4. Technical Capacity - Program Management and Subrecipient Oversight
5. Technical Capacity - Project Management
6. Transit Asset Management
7. Satisfactory Continuing Control
8. Maintenance
9. Procurement
10. Disadvantaged Business Enterprise
11. Title VI
12. Americans with Disabilities Act (ADA) - General
13. Americans with Disabilities Act (ADA) - Complementary Paratransit
14. Equal Employment Opportunity
15. School Bus
16. Charter Bus
17. Drug-Free Workplace Act
18. Drug and Alcohol Program
19. Section 5307 Program Requirements
20. Section 5310 Program Requirements
21. Section 5311 Program Requirements
22. Public Transportation Agency Safety Plan (PTASP)
23. Cybersecurity

HERE IS THE PDF TEXT:

{pdf_text[:150000]}
"""

        try:
            logger.info(f"Sending {self.filename} to Claude for extraction...")

            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16000,
                messages=[{
                    "role": "user",
                    "content": extraction_prompt
                }]
            )

            response_text = message.content[0].text

            # Extract JSON from response (Claude might wrap it in markdown)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            extracted_data = json.loads(response_text)

            # Add metadata
            extracted_data["source_file"] = self.filename
            extracted_data["extracted_at"] = datetime.now().isoformat()
            extracted_data["extraction_method"] = "claude-api"

            return extracted_data

        except Exception as e:
            logger.error(f"Error in Claude extraction for {self.filename}: {e}")
            return None

    def extract_all(self) -> Dict:
        """Main extraction method."""
        logger.info(f"Extracting data from: {self.filename}")

        # Extract PDF text
        pdf_text = self.extract_pdf_text()
        if not pdf_text:
            logger.error(f"No text extracted from {self.filename}")
            return None

        # Use Claude to extract structured data
        extracted_data = self.extract_with_claude(pdf_text)

        if extracted_data:
            # Calculate summary stats
            assessments = extracted_data.get("assessments", [])
            deficiency_count = sum(1 for a in assessments if a.get("finding") == "D")
            extracted_data["summary"] = {
                "total_deficiencies": deficiency_count,
                "total_areas_reviewed": len(assessments)
            }
            logger.info(f"  ✓ Extracted: {deficiency_count} deficiencies, {len(extracted_data.get('awards', []))} awards, {len(extracted_data.get('projects', []))} projects")

        return extracted_data

    def save_json(self, data: Dict, output_dir: str):
        """Save extracted data to JSON file."""
        output_path = Path(output_dir) / f"{Path(self.filename).stem}.json"
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"  Saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Extract FTA audit data using Claude AI')
    parser.add_argument('--input-dir', default='../docs/final reports/reports only',
                        help='Directory containing PDF files')
    parser.add_argument('--output-dir', default='./extracted_data_claude',
                        help='Directory to save extracted JSON files')
    parser.add_argument('--api-key', help='Anthropic API key (or use ANTHROPIC_API_KEY env var)')
    parser.add_argument('--single-file', help='Process only this specific PDF file')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get list of PDFs
    input_dir = Path(args.input_dir)
    if args.single_file:
        pdf_files = [Path(args.single_file)]
    else:
        pdf_files = list(input_dir.glob('*.pdf'))

    logger.info(f"Found {len(pdf_files)} PDF files to process")

    # Process each PDF
    success_count = 0
    fail_count = 0
    skipped_count = 0

    for pdf_file in pdf_files:
        try:
            # Check if already extracted
            output_path = output_dir / f"{pdf_file.stem}.json"
            if output_path.exists():
                logger.info(f"Skipping (already extracted): {pdf_file.name}")
                skipped_count += 1
                continue

            extractor = ClaudeAuditExtractor(str(pdf_file), api_key=args.api_key)
            data = extractor.extract_all()

            if data:
                extractor.save_json(data, args.output_dir)
                success_count += 1
            else:
                fail_count += 1

        except Exception as e:
            logger.error(f"Failed to process {pdf_file}: {e}")
            fail_count += 1

    logger.info(f"\n{'='*80}")
    logger.info(f"Extraction complete: {success_count} successful, {fail_count} failed, {skipped_count} skipped")
    logger.info(f"Output directory: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
