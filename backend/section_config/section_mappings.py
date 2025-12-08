"""Section name to question code mappings for natural language queries."""

# Section name variations mapped to their question code prefixes
SECTION_NAME_MAPPINGS = {
    # Legal (L1-L3)
    "legal": ["L1", "L2", "L3"],
    "law": ["L1", "L2", "L3"],
    "legal matters": ["L1", "L2", "L3"],
    "legal requirements": ["L1", "L2", "L3"],

    # Financial Management (F1-F9)
    "financial": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],
    "finance": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],
    "financial management": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],
    "financial capacity": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],
    "budget": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],

    # Technical Capacity - Award Management (TC-AM1-5)
    "technical capacity award": ["TC-AM1", "TC-AM2", "TC-AM3", "TC-AM4", "TC-AM5"],
    "award management": ["TC-AM1", "TC-AM2", "TC-AM3", "TC-AM4", "TC-AM5"],
    "tc award": ["TC-AM1", "TC-AM2", "TC-AM3", "TC-AM4", "TC-AM5"],

    # Technical Capacity - Program Management (TC-PrgM1-7)
    "technical capacity program": ["TC-PrgM1", "TC-PrgM2", "TC-PrgM3", "TC-PrgM4", "TC-PrgM5", "TC-PrgM6", "TC-PrgM7"],
    "program management": ["TC-PrgM1", "TC-PrgM2", "TC-PrgM3", "TC-PrgM4", "TC-PrgM5", "TC-PrgM6", "TC-PrgM7"],
    "subrecipient oversight": ["TC-PrgM1", "TC-PrgM2", "TC-PrgM3", "TC-PrgM4", "TC-PrgM5", "TC-PrgM6", "TC-PrgM7"],

    # Technical Capacity - Project Management (TC-PjM1-4)
    "technical capacity project": ["TC-PjM1", "TC-PjM2", "TC-PjM3", "TC-PjM4"],
    "project management": ["TC-PjM1", "TC-PjM2", "TC-PjM3", "TC-PjM4"],
    "tc project": ["TC-PjM1", "TC-PjM2", "TC-PjM3", "TC-PjM4"],

    # Transit Asset Management (TAM1-8)
    "transit asset": ["TAM1", "TAM2", "TAM3", "TAM4", "TAM5", "TAM6", "TAM7", "TAM8"],
    "asset management": ["TAM1", "TAM2", "TAM3", "TAM4", "TAM5", "TAM6", "TAM7", "TAM8"],
    "tam": ["TAM1", "TAM2", "TAM3", "TAM4", "TAM5", "TAM6", "TAM7", "TAM8"],

    # Satisfactory Continuing Control (SCC1-13)
    "continuing control": ["SCC1", "SCC2", "SCC3", "SCC4", "SCC5", "SCC6", "SCC7", "SCC8", "SCC9", "SCC10", "SCC11", "SCC12", "SCC13"],
    "scc": ["SCC1", "SCC2", "SCC3", "SCC4", "SCC5", "SCC6", "SCC7", "SCC8", "SCC9", "SCC10", "SCC11", "SCC12", "SCC13"],
    "satisfactory control": ["SCC1", "SCC2", "SCC3", "SCC4", "SCC5", "SCC6", "SCC7", "SCC8", "SCC9", "SCC10", "SCC11", "SCC12", "SCC13"],

    # Maintenance (M1-5)
    "maintenance": ["M1", "M2", "M3", "M4", "M5"],
    "vehicle maintenance": ["M1", "M2", "M3", "M4", "M5"],

    # Procurement (P1-20)
    "procurement": ["P1", "P2", "P4", "P5", "P6", "P7", "P8", "P9", "P10", "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18", "P19", "P20", "P21"],
    "purchasing": ["P1", "P2", "P4", "P5", "P6", "P7", "P8", "P9", "P10", "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18", "P19", "P20", "P21"],
    "contracting": ["P1", "P2", "P4", "P5", "P6", "P7", "P8", "P9", "P10", "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18", "P19", "P20", "P21"],

    # DBE (DBE1-13)
    "dbe": ["DBE1", "DBE2", "DBE3", "DBE4", "DBE5", "DBE6", "DBE7", "DBE8", "DBE9", "DBE10", "DBE11", "DBE12", "DBE13"],
    "disadvantaged business": ["DBE1", "DBE2", "DBE3", "DBE4", "DBE5", "DBE6", "DBE7", "DBE8", "DBE9", "DBE10", "DBE11", "DBE12", "DBE13"],
    "dbe program": ["DBE1", "DBE2", "DBE3", "DBE4", "DBE5", "DBE6", "DBE7", "DBE8", "DBE9", "DBE10", "DBE11", "DBE12", "DBE13"],

    # Title VI (TVI1-10)
    "title vi": ["TVI1", "TVI2", "TVI3", "TVI4", "TVI5", "TVI6", "TVI7", "TVI8", "TVI9", "TVI10"],
    "title 6": ["TVI1", "TVI2", "TVI3", "TVI4", "TVI5", "TVI6", "TVI7", "TVI8", "TVI9", "TVI10"],
    "civil rights": ["TVI1", "TVI2", "TVI3", "TVI4", "TVI5", "TVI6", "TVI7", "TVI8", "TVI9", "TVI10"],
    "nondiscrimination": ["TVI1", "TVI2", "TVI3", "TVI4", "TVI5", "TVI6", "TVI7", "TVI8", "TVI9", "TVI10"],

    # ADA General (ADA-GEN1-14)
    "ada": ["ADA-GEN1", "ADA-GEN2", "ADA-GEN3", "ADA-GEN4", "ADA-GEN5", "ADA-GEN6", "ADA-GEN7", "ADA-GEN8", "ADA-GEN9", "ADA-GEN10", "ADA-GEN11", "ADA-GEN12", "ADA-GEN13", "ADA-GEN14"],
    "ada general": ["ADA-GEN1", "ADA-GEN2", "ADA-GEN3", "ADA-GEN4", "ADA-GEN5", "ADA-GEN6", "ADA-GEN7", "ADA-GEN8", "ADA-GEN9", "ADA-GEN10", "ADA-GEN11", "ADA-GEN12", "ADA-GEN13", "ADA-GEN14"],
    "americans with disabilities": ["ADA-GEN1", "ADA-GEN2", "ADA-GEN3", "ADA-GEN4", "ADA-GEN5", "ADA-GEN6", "ADA-GEN7", "ADA-GEN8", "ADA-GEN9", "ADA-GEN10", "ADA-GEN11", "ADA-GEN12", "ADA-GEN13", "ADA-GEN14"],
    "accessibility": ["ADA-GEN1", "ADA-GEN2", "ADA-GEN3", "ADA-GEN4", "ADA-GEN5", "ADA-GEN6", "ADA-GEN7", "ADA-GEN8", "ADA-GEN9", "ADA-GEN10", "ADA-GEN11", "ADA-GEN12", "ADA-GEN13", "ADA-GEN14"],
    "disabilities": ["ADA-GEN1", "ADA-GEN2", "ADA-GEN3", "ADA-GEN4", "ADA-GEN5", "ADA-GEN6", "ADA-GEN7", "ADA-GEN8", "ADA-GEN9", "ADA-GEN10", "ADA-GEN11", "ADA-GEN12", "ADA-GEN13", "ADA-GEN14"],

    # ADA Paratransit (ADA-CPT1-8)
    "paratransit": ["ADA-CPT1", "ADA-CPT2", "ADA-CPT3", "ADA-CPT4", "ADA-CPT5", "ADA-CPT6", "ADA-CPT7", "ADA-CPT8"],
    "ada paratransit": ["ADA-CPT1", "ADA-CPT2", "ADA-CPT3", "ADA-CPT4", "ADA-CPT5", "ADA-CPT6", "ADA-CPT7", "ADA-CPT8"],
    "complementary paratransit": ["ADA-CPT1", "ADA-CPT2", "ADA-CPT3", "ADA-CPT4", "ADA-CPT5", "ADA-CPT6", "ADA-CPT7", "ADA-CPT8"],

    # EEO (EEO1-5)
    "eeo": ["EEO1", "EEO2", "EEO3", "EEO4", "EEO5"],
    "equal employment": ["EEO1", "EEO2", "EEO3", "EEO4", "EEO5"],
    "employment opportunity": ["EEO1", "EEO2", "EEO3", "EEO4", "EEO5"],

    # School Bus (SB1-4)
    "school bus": ["SB1", "SB2", "SB3", "SB4"],
    "school transportation": ["SB1", "SB2", "SB3", "SB4"],

    # Charter Bus (CB1-3)
    "charter bus": ["CB1", "CB2", "CB3"],
    "charter service": ["CB1", "CB2", "CB3"],
    "charter operations": ["CB1", "CB2", "CB3"],

    # Drug-Free Workplace (DFWA1-3)
    "drug free": ["DFWA1", "DFWA2", "DFWA3"],
    "drug-free workplace": ["DFWA1", "DFWA2", "DFWA3"],
    "dfwa": ["DFWA1", "DFWA2", "DFWA3"],

    # Drug and Alcohol (DA1-5)
    "drug and alcohol": ["DA1", "DA2", "DA3", "DA4", "DA5"],
    "drug alcohol program": ["DA1", "DA2", "DA3", "DA4", "DA5"],
    "substance abuse": ["DA1", "DA2", "DA3", "DA4", "DA5"],

    # Section 5307 (5307:1-5)
    "5307": ["5307:1", "5307:2", "5307:3", "5307:4", "5307:5"],
    "section 5307": ["5307:1", "5307:2", "5307:3", "5307:4", "5307:5"],
    "urbanized area": ["5307:1", "5307:2", "5307:3", "5307:4", "5307:5"],

    # Section 5310 (5310:1-5)
    "5310": ["5310:1", "5310:2", "5310:3", "5310:4", "5310:5"],
    "section 5310": ["5310:1", "5310:2", "5310:3", "5310:4", "5310:5"],
    "elderly and disabled": ["5310:1", "5310:2", "5310:3", "5310:4", "5310:5"],

    # Section 5311 (5311:1-4)
    "5311": ["5311:1", "5311:2", "5311:3", "5311:4"],
    "section 5311": ["5311:1", "5311:2", "5311:3", "5311:4"],
    "rural area": ["5311:1", "5311:2", "5311:3", "5311:4"],
    "rural transit": ["5311:1", "5311:2", "5311:3", "5311:4"],

    # PTASP (PTASP1-6)
    "ptasp": ["PTASP1", "PTASP2", "PTASP3", "PTASP4", "PTASP5", "PTASP6"],
    "safety plan": ["PTASP1", "PTASP2", "PTASP3", "PTASP4", "PTASP5", "PTASP6"],
    "agency safety plan": ["PTASP1", "PTASP2", "PTASP3", "PTASP4", "PTASP5", "PTASP6"],

    # Cybersecurity (C1)
    "cybersecurity": ["C1"],
    "cyber security": ["C1"],
    "information security": ["C1"],
}


def get_question_codes_for_section(section_name: str) -> list[str]:
    """
    Get question codes for a section name.

    Args:
        section_name: Natural language section name (e.g., "Legal", "Title VI")

    Returns:
        List of question codes (e.g., ["L1", "L2", "L3"])
    """
    section_lower = section_name.lower().strip()
    return SECTION_NAME_MAPPINGS.get(section_lower, [])


def find_matching_sections(query: str) -> list[str]:
    """
    Find all section question codes mentioned in a query.

    Args:
        query: User query text

    Returns:
        List of question codes found via section name matching
    """
    query_lower = query.lower()
    matched_codes = []

    # Check each section name variant
    for section_name, codes in SECTION_NAME_MAPPINGS.items():
        if section_name in query_lower:
            matched_codes.extend(codes)

    # Deduplicate and return
    return list(set(matched_codes))
