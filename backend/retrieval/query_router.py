"""Query routing system for intelligent query classification and database section extraction."""
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass

# Add config to path for section mappings
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.section_mappings import find_matching_sections


QueryType = Literal["database", "rag", "hybrid"]


@dataclass
class QueryRoute:
    """Result of query classification."""
    route_type: QueryType
    confidence: float  # 0.0 to 1.0
    reasoning: str
    section_names: Optional[List[str]] = None  # For database queries
    keywords: Optional[List[str]] = None  # For RAG queries


class QueryRouter:
    """Classifies queries and routes them to the appropriate backend."""

    # Section patterns - match ALL question code formats from the database
    # Matches: TVI3, TVI10-1, L1, F9, CB1, ADA-GEN12, TC-PjM4, PTASP5, 5307:1, etc.
    SECTION_PATTERN = re.compile(
        r'\b('
        r'TVI\d+(?:-\d+)?|'          # Title VI: TVI3, TVI10-1
        r'ADA-(?:GEN|CPT)\d+|'       # ADA: ADA-GEN1, ADA-CPT8
        r'TC-(?:PjM|AM|PrgM)\d+|'    # Technical Capacity: TC-PjM1, TC-AM2, TC-PrgM3
        r'[A-Z]{1,6}\d+|'            # Generic: L1, F2, CB3, PTASP5, DBE12, etc.
        r'\d{4}:\d+'                 # Numeric: 5307:1, 5310:2, 5311:3
        r')\b',
        re.IGNORECASE
    )

    # Database-friendly patterns (exact lookups)
    # Note: These patterns will match any section code via SECTION_PATTERN
    DATABASE_PATTERNS = [
        # Count queries for specific sections
        # Matches: "How many indicators in TVI3?", "Count deficiencies in L1", "How many in CB2?"
        (r'how many (?:indicators|deficiencies|questions).+?(?:in|for|under|within)\s+', 'count_in_section'),
        (r'count.+?(?:indicators|deficiencies|questions)', 'count_in_section'),

        # List queries for specific sections
        # Matches: "List all indicators in F5", "Show deficiencies for ADA-GEN3"
        (r'list\s+all\s+(?:indicators|deficiencies|questions)', 'list_in_section'),
        (r'show\s+(?:me\s+)?(?:indicators|deficiencies|questions)', 'list_in_section'),
        (r'(?:all|get)\s+(?:indicators|deficiencies|questions)\s+(?:in|for|under)', 'list_in_section'),

        # Direct section queries (without "why" or "purpose")
        # Matches: "What is L1?", "Describe TC-PjM2", "Explain PTASP5"
        (r'what is \w+\??$', 'get_section'),
        (r'describe \w+', 'get_section'),
        (r'explain \w+\??$', 'get_section'),

        # Exact question code lookup
        # Matches: "TVI3 requirements", "CB1 compliance", "5307:2 question"
        (r'\w+\s+(?:question|requirements|compliance)', 'get_section'),
    ]

    # Hybrid patterns (database + RAG needed)
    HYBRID_PATTERNS = [
        # Compare across sections
        # Matches: "Compare TVI3 and L1", "Difference between CB1 and SB2"
        r'(?:compare|difference|similar|related)',
        r'how does \w+.+?(?:relate|differ|compare)',

        # Aggregate queries across sections (not scoped to single section)
        # Matches: "Total indicators", "All deficiencies overall"
        r'(?:all|total)\s+(?:indicators|deficiencies)(?!\s+(?:in|for)\s+\w+)',  # negative lookahead
        r'how many.+?(?:indicators|deficiencies)\s+(?:are there|total|overall)',

        # Section + conceptual query (purpose, rationale, etc.)
        # Matches: "What's the purpose of F5?", "Why is PTASP2 important?"
        r'\w+.+?(?:why|purpose|rationale|best practice)',
        r'(?:what|what\'s).+?(?:purpose|rationale)',
        r'\w+.+?(?:how does|relate)',
    ]

    # Pure RAG patterns (conceptual, no specific sections)
    RAG_PATTERNS = [
        # Conceptual questions
        r'what (?:is|are).+?(?:ada|charter|procurement|safety)',
        r'explain.+?(?:compliance|requirements|regulations)',
        r'how (?:do|does|should|can).+?(?:recipients|transit|agencies)',

        # General guidance
        r'best practices',
        r'what steps',
        r'how to',

        # Topic-based (no section IDs)
        r'tell me about',
        r'information (?:on|about)',
    ]

    def __init__(self):
        """Initialize the query router."""
        pass

    def extract_section_names(self, query: str) -> List[str]:
        """
        Extract section IDs from query using both code patterns and semantic names.

        Examples:
            "How many indicators in TVI3?" → ["TVI3"] (code pattern)
            "How many indicators in Title VI?" → ["TVI1", "TVI2", ...] (semantic name)
            "Legal section indicators" → ["L1", "L2", "L3"] (semantic name)

        Args:
            query: User query text

        Returns:
            List of section IDs found (uppercase, e.g., ['TVI3', 'TVI6'] or ['L1', 'L2', 'L3'])
        """
        sections = []

        # Method 1: Extract explicit section codes (TVI3, L1, CB1, etc.)
        code_matches = self.SECTION_PATTERN.findall(query)
        sections.extend([m.upper() for m in code_matches])

        # Method 2: Match semantic section names ("Legal", "Title VI", etc.)
        semantic_matches = find_matching_sections(query)
        sections.extend(semantic_matches)

        # Deduplicate and sort
        return sorted(list(set(sections)))

    def _check_database_patterns(self, query: str) -> Optional[tuple[str, float]]:
        """
        Check if query matches database patterns.

        Returns:
            Tuple of (pattern_type, confidence) or None
        """
        query_lower = query.lower()

        for pattern, pattern_type in self.DATABASE_PATTERNS:
            if re.search(pattern, query_lower):
                return (pattern_type, 0.9)

        return None

    def _check_hybrid_patterns(self, query: str) -> bool:
        """Check if query matches hybrid patterns."""
        query_lower = query.lower()

        for pattern in self.HYBRID_PATTERNS:
            if re.search(pattern, query_lower):
                return True

        return False

    def _check_rag_patterns(self, query: str) -> bool:
        """Check if query matches RAG patterns."""
        query_lower = query.lower()

        for pattern in self.RAG_PATTERNS:
            if re.search(pattern, query_lower):
                return True

        return False

    def classify_query(self, query: str) -> QueryRoute:
        """
        Classify a query and determine routing strategy.

        Classification logic:
        1. Database: Specific section + count/list/lookup queries
        2. Hybrid: Multiple sections OR section + conceptual OR aggregate queries
        3. RAG: Conceptual questions with no section IDs

        Args:
            query: User query text

        Returns:
            QueryRoute with classification and metadata
        """
        sections = self.extract_section_names(query)

        # Check patterns
        db_match = self._check_database_patterns(query)
        is_hybrid_pattern = self._check_hybrid_patterns(query)

        # Decision tree
        if len(sections) > 1:
            # Multiple sections = hybrid (need cross-section analysis)
            return QueryRoute(
                route_type="hybrid",
                confidence=0.8,
                reasoning=f"Multiple sections detected: {', '.join(sections)}. Requires both structured data and context.",
                section_names=sections
            )

        elif len(sections) == 1:
            # Single section - check if it's hybrid or database
            if is_hybrid_pattern:
                # Hybrid pattern detected (e.g., "purpose of TVI6", "why TVI3")
                return QueryRoute(
                    route_type="hybrid",
                    confidence=0.75,
                    reasoning=f"Section {sections[0]} with conceptual query. Requires both database and RAG.",
                    section_names=sections
                )
            elif db_match:
                # Specific database pattern (list, count, get)
                pattern_type, confidence = db_match
                return QueryRoute(
                    route_type="database",
                    confidence=confidence,
                    reasoning=f"Specific section query ({pattern_type}) with section IDs: {', '.join(sections)}",
                    section_names=sections
                )
            else:
                # Default: single section = database
                return QueryRoute(
                    route_type="database",
                    confidence=0.85,
                    reasoning=f"Single section query for {sections[0]}. Direct database lookup suitable.",
                    section_names=sections
                )

        else:
            # No sections = check if pure RAG or hybrid aggregate
            if is_hybrid_pattern or self._is_aggregate_query(query):
                return QueryRoute(
                    route_type="hybrid",
                    confidence=0.7,
                    reasoning="Aggregate query across all sections. Requires database + RAG.",
                    section_names=None
                )
            else:
                # Pure conceptual query
                return QueryRoute(
                    route_type="rag",
                    confidence=0.85,
                    reasoning="Conceptual question with no specific sections. Pure RAG retrieval.",
                    section_names=None,
                    keywords=self._extract_keywords(query)
                )

    def _is_aggregate_query(self, query: str) -> bool:
        """Check if query is asking for aggregate data across all sections."""
        query_lower = query.lower()
        aggregate_terms = [
            'total', 'all', 'overall', 'across', 'entire',
            'how many indicators', 'how many deficiencies',
            'count all', 'list all'
        ]
        return any(term in query_lower for term in aggregate_terms)

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract key terms from query for RAG retrieval.

        Args:
            query: User query text

        Returns:
            List of important keywords
        """
        # Remove common stopwords and extract meaningful terms
        stopwords = {'what', 'is', 'are', 'the', 'a', 'an', 'how', 'do', 'does', 'can',
                     'should', 'tell', 'me', 'about', 'for', 'to', 'in', 'on', 'with'}

        # Tokenize (simple split)
        words = re.findall(r'\b\w+\b', query.lower())

        # Filter stopwords and short words
        keywords = [w for w in words if w not in stopwords and len(w) > 3]

        return keywords[:5]  # Top 5 keywords


# Convenience function for backward compatibility
def route_query(query: str) -> QueryRoute:
    """
    Route a query to the appropriate backend.

    Args:
        query: User query text

    Returns:
        QueryRoute with classification and metadata
    """
    router = QueryRouter()
    return router.classify_query(query)


# Example usage
if __name__ == "__main__":
    router = QueryRouter()

    test_queries = [
        "How many indicators of compliance are in TVI3?",
        "What are the ADA compliance requirements?",
        "List all deficiencies in TVI6",
        "Compare TVI3 and TVI6 requirements",
        "How many total indicators are there?",
        "What is charter bus service?",
        "Explain TVI3",
        "What's the purpose of TVI6 and how does it relate to safety?",
    ]

    print("Query Router Test Results")
    print("=" * 80)

    for query in test_queries:
        route = router.classify_query(query)
        print(f"\nQuery: {query}")
        print(f"Route: {route.route_type.upper()}")
        print(f"Confidence: {route.confidence:.2f}")
        print(f"Reasoning: {route.reasoning}")
        if route.section_names:
            print(f"Sections: {', '.join(route.section_names)}")
        if route.keywords:
            print(f"Keywords: {', '.join(route.keywords)}")
        print("-" * 80)
