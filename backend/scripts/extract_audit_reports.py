"""
PDF Extraction Pipeline for FTA Audit Final Reports

Extracts structured data from audit final reports (both PDF portfolios and standard PDFs)
and prepares data for ingestion into PostgreSQL and ChromaDB.

Usage:
    python extract_audit_reports.py --input-dir "../docs/final reports" --output-dir "./extracted_data"
"""

import os
import re
import json
import PyPDF2
import pdfplumber
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AuditReportExtractor:
    """Extract structured data from FTA audit final reports."""

    # Review area mappings (23 standard areas)
    REVIEW_AREAS = [
        "Legal",
        "Financial Management and Capacity",
        "Technical Capacity - Award Management",
        "Technical Capacity - Program Management and Subrecipient Oversight",
        "Technical Capacity - Project Management",
        "Transit Asset Management",
        "Satisfactory Continuing Control",
        "Maintenance",
        "Procurement",
        "Disadvantaged Business Enterprise",
        "Title VI",
        "Americans with Disabilities Act (ADA) - General",
        "Americans with Disabilities Act (ADA) - Complementary Paratransit",
        "Equal Employment Opportunity",
        "School Bus",
        "Charter Bus",
        "Drug-Free Workplace Act",
        "Drug and Alcohol Program",
        "Section 5307 Program Requirements",
        "Section 5310 Program Requirements",
        "Section 5311 Program Requirements",
        "Public Transportation Agency Safety Plan (PTASP)",
        "Cybersecurity"
    ]

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.filename = os.path.basename(pdf_path)
        self.extracted_data = {
            "source_file": self.filename,
            "extracted_at": datetime.now().isoformat(),
            "recipient": {},
            "review_info": {},
            "reviewer_info": {},
            "fta_pm_info": {},
            "assessments": [],
            "narrative_sections": {}
        }

    def parse_filename(self) -> Dict[str, str]:
        """
        Extract metadata from filename pattern: 01_CT_1337_GNHTD_2023_TR_Final Report.pdf
        Pattern: {region}_{state}_{recipient_id}_{acronym}_{year}_{review_type}_Final Report.pdf
        """
        # Pattern: 01_CT_1337_GNHTD_2023_TR
        pattern = r'^(\d+)_([A-Z]{2})_(\d+)_([A-Z]+)_(\d{4})_([A-Z]+)'
        match = re.match(pattern, self.filename)

        if match:
            region, state, recipient_id, acronym, year, review_type = match.groups()
            return {
                "region_number": int(region),
                "state": state,
                "recipient_id": recipient_id,
                "acronym": acronym,
                "year": year,
                "fiscal_year": f"FY{year}",
                "review_type_code": review_type  # TR, SMR, etc.
            }
        else:
            logger.warning(f"Could not parse filename: {self.filename}")
            return {}

    def extract_text_from_pdf(self) -> str:
        """Extract all text from PDF (handles both portfolios and standard PDFs)."""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from {self.filename}: {e}")
            return ""

    def extract_recipient_info(self, text: str) -> Dict:
        """Extract recipient information from report text."""
        info = {}

        # Extract recipient name (usually appears early in document)
        name_pattern = r'(?:Recipient[:\s]+|Review of[:\s]+)([A-Z][A-Za-z\s&,]+?)(?:\n|(?:Location|City))'
        name_match = re.search(name_pattern, text)
        if name_match:
            info["name"] = name_match.group(1).strip()

        # Extract city/state
        location_pattern = r'(?:Location|City)[:\s]+([A-Za-z\s]+),\s*([A-Z]{2})'
        loc_match = re.search(location_pattern, text)
        if loc_match:
            info["city"] = loc_match.group(1).strip()
            info["state"] = loc_match.group(2).strip()

        return info

    def extract_review_dates(self, text: str) -> Dict:
        """Extract review dates from report text."""
        dates = {}

        # Site visit dates
        site_visit_pattern = r'(?:Site Visit|On-?site Review)[:\s]+([A-Za-z]+\s+\d{1,2}(?:-\d{1,2})?,?\s+\d{4})'
        sv_match = re.search(site_visit_pattern, text, re.IGNORECASE)
        if sv_match:
            dates["site_visit_dates"] = sv_match.group(1).strip()

        # Report date
        report_date_pattern = r'(?:Report Date|Date of Report)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})'
        rd_match = re.search(report_date_pattern, text, re.IGNORECASE)
        if rd_match:
            dates["report_date"] = rd_match.group(1).strip()

        return dates

    def extract_reviewer_info(self, text: str) -> Dict:
        """Extract lead reviewer and contractor information."""
        info = {}

        # Contractor name
        contractor_pattern = r'(?:Contractor|Reviewed by)[:\s]+([A-Za-z\s,&.]+(?:LLC|Inc|Group|Consulting))'
        contractor_match = re.search(contractor_pattern, text, re.IGNORECASE)
        if contractor_match:
            info["contractor_name"] = contractor_match.group(1).strip()

        # Lead reviewer
        reviewer_pattern = r'(?:Lead Reviewer|Review Team Leader)[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)'
        reviewer_match = re.search(reviewer_pattern, text, re.IGNORECASE)
        if reviewer_match:
            info["lead_reviewer_name"] = reviewer_match.group(1).strip()

        return info

    def extract_fta_pm_info(self, text: str) -> Dict:
        """Extract FTA Program Manager information."""
        info = {}

        # FTA PM name
        pm_pattern = r'(?:FTA Program Manager|Program Manager)[:\s]+([A-Z][a-z]+\s+[A-Z]\.?\s+[A-Z][a-z]+)'
        pm_match = re.search(pm_pattern, text, re.IGNORECASE)
        if pm_match:
            info["fta_pm_name"] = pm_match.group(1).strip()

        return info

    def extract_assessments_table(self, text: str) -> List[Dict]:
        """
        Extract assessment findings from the summary table.
        Looks for patterns like: "Legal    D" or "Title VI    ND"
        """
        assessments = []

        for review_area in self.REVIEW_AREAS:
            # Look for review area followed by finding (D, ND, NA)
            # Pattern: "Review Area Name" followed by whitespace and D/ND/NA
            pattern = rf'{re.escape(review_area)}\s+(D|ND|NA)'
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                finding = match.group(1).upper()
                assessments.append({
                    "review_area": review_area,
                    "finding": finding,
                    "deficiency_code": None,
                    "description": None,
                    "corrective_action": None
                })
            else:
                # If not found in table, default to NA (not reviewed)
                assessments.append({
                    "review_area": review_area,
                    "finding": "NA",
                    "deficiency_code": None,
                    "description": None,
                    "corrective_action": None
                })

        return assessments

    def extract_deficiency_details(self, pdf_path: str, assessments: List[Dict]) -> List[Dict]:
        """
        Extract detailed deficiency descriptions and corrective actions from PDF.

        Searches for:
        1. Deficiency summary table (page 5-8) with deficiency codes
        2. Detailed sections with "Deficiency Description #N: [Title] (Code)"
        3. Corrective Action sections
        """
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n\n"

        for assessment in assessments:
            if assessment["finding"] == "D":
                review_area = assessment["review_area"]

                # Extract deficiency code from summary table
                # Pattern: "Review Area Code Description..."
                code_pattern = rf'{re.escape(review_area)}\s+([A-Z0-9-]+):\s+'
                code_match = re.search(code_pattern, full_text, re.IGNORECASE)
                if code_match:
                    assessment["deficiency_code"] = code_match.group(1).strip()

                # Extract detailed deficiency description
                # Pattern: "Deficiency Description #N: [Title] (Code)" followed by text
                desc_pattern = rf'Deficiency Description[^\n]*?{re.escape(review_area)}[^\n]{{0,100}}?\n(.*?)(?=Corrective Action|Deficiency Description|$)'
                desc_match = re.search(desc_pattern, full_text, re.DOTALL | re.IGNORECASE)

                if not desc_match:
                    # Try alternate pattern: "Deficiency Description #N: [Title] (Code)"
                    if assessment["deficiency_code"]:
                        desc_pattern2 = rf'Deficiency Description[^\n]*?{re.escape(assessment["deficiency_code"])}[^\n]*?\n(.*?)(?=Corrective Action|Deficiency Description|$)'
                        desc_match = re.search(desc_pattern2, full_text, re.DOTALL | re.IGNORECASE)

                if desc_match:
                    desc_text = desc_match.group(1).strip()
                    # Clean up: take first 500 chars or until regulatory citation
                    lines = []
                    for line in desc_text.split('\n'):
                        # Stop at regulatory citations (49 U.S.C, 2 CFR, etc.)
                        if re.match(r'^\d+\s+(U\.S\.C|CFR)', line):
                            break
                        if line.strip():
                            lines.append(line.strip())
                        if len(' '.join(lines)) > 500:
                            break
                    assessment["description"] = ' '.join(lines)[:500]

                # Extract corrective action
                # Pattern: "Corrective Action(s) and Schedule: By [Date]:" followed by numbered list
                ca_pattern = rf'Corrective Action\(s\)[^\n]*?:\s*(?:By [^\n]+:)?\s*(.*?)(?=Deficiency Description|Review Area|Page \d+|$)'
                ca_match = re.search(ca_pattern, full_text, re.DOTALL | re.IGNORECASE)

                if ca_match:
                    ca_text = ca_match.group(1).strip()
                    # Clean up: take first 500 chars
                    lines = []
                    for line in ca_text.split('\n'):
                        if line.strip() and not re.match(r'^Page \d+', line):
                            lines.append(line.strip())
                        if len(' '.join(lines)) > 500:
                            break
                    assessment["corrective_action"] = ' '.join(lines)[:500]

        return assessments

    def extract_narrative_sections(self, text: str) -> Dict[str, str]:
        """
        Extract narrative text for each review area (for RAG vector database).
        This captures the detailed observations and context.
        """
        narratives = {}
        review_areas_joined = '|'.join([re.escape(a) for a in self.REVIEW_AREAS])

        for review_area in self.REVIEW_AREAS:
            # Look for section header and capture text until next review area
            area_pattern = rf'{re.escape(review_area)}\s*\n+(.*?)(?=(?:{review_areas_joined})|APPENDIX|$)'
            area_match = re.search(area_pattern, text, re.DOTALL | re.IGNORECASE)

            if area_match:
                narrative = area_match.group(1).strip()
                # Only store if there's meaningful content (more than 100 chars)
                if len(narrative) > 100:
                    narratives[review_area] = narrative[:5000]  # Limit to 5000 chars

        return narratives

    def extract_all(self) -> Dict:
        """Main extraction method - orchestrates all extraction steps."""
        logger.info(f"Extracting data from: {self.filename}")

        # Parse filename
        filename_data = self.parse_filename()

        # Extract full text
        full_text = self.extract_text_from_pdf()

        if not full_text:
            logger.error(f"No text extracted from {self.filename}")
            return None

        # Extract all components
        recipient_info = self.extract_recipient_info(full_text)
        review_dates = self.extract_review_dates(full_text)
        reviewer_info = self.extract_reviewer_info(full_text)
        fta_pm_info = self.extract_fta_pm_info(full_text)
        assessments = self.extract_assessments_table(full_text)
        assessments = self.extract_deficiency_details(self.pdf_path, assessments)
        narratives = self.extract_narrative_sections(full_text)

        # Merge filename data with extracted data
        self.extracted_data["recipient"] = {**filename_data, **recipient_info}
        self.extracted_data["review_info"] = {**filename_data, **review_dates}
        self.extracted_data["reviewer_info"] = reviewer_info
        self.extracted_data["fta_pm_info"] = fta_pm_info
        self.extracted_data["assessments"] = assessments
        self.extracted_data["narrative_sections"] = narratives

        # Calculate summary stats
        deficiency_count = sum(1 for a in assessments if a["finding"] == "D")
        self.extracted_data["summary"] = {
            "total_deficiencies": deficiency_count,
            "total_areas_reviewed": len([a for a in assessments if a["finding"] != "NA"]),
            "deficiency_areas": [a["review_area"] for a in assessments if a["finding"] == "D"]
        }

        logger.info(f"  Extracted: {deficiency_count} deficiencies, {len(narratives)} narrative sections")

        return self.extracted_data


def extract_all_reports(input_dir: str, output_dir: str):
    """Extract data from all PDF reports in input directory."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_path.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files to process")

    results = []
    successful = 0
    failed = 0

    for pdf_file in pdf_files:
        try:
            extractor = AuditReportExtractor(str(pdf_file))
            data = extractor.extract_all()

            if data:
                # Save individual JSON file
                output_file = output_path / f"{pdf_file.stem}.json"
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)

                results.append(data)
                successful += 1
            else:
                failed += 1

        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {e}")
            failed += 1

    # Save combined results
    combined_file = output_path / "all_reports_combined.json"
    with open(combined_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"\nExtraction complete:")
    logger.info(f"  Successful: {successful}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Output directory: {output_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description='Extract data from FTA audit final reports')
    parser.add_argument('--input-dir', default='../docs/final reports',
                        help='Directory containing PDF reports')
    parser.add_argument('--output-dir', default='./extracted_data',
                        help='Directory to save extracted JSON files')

    args = parser.parse_args()

    extract_all_reports(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
