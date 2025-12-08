"""Query classification to determine retrieval strategy."""
from typing import Literal, Dict

QueryType = Literal["specific", "aggregate", "count"]


def classify_query(question: str) -> QueryType:
    """
    Classify user query to determine appropriate retrieval strategy.

    - specific: Find specific information (default)
    - aggregate: Summarize across multiple sections
    - count: Count occurrences of something

    Args:
        question: User's natural language question

    Returns:
        Query type classification
    """
    question_lower = question.lower()

    # Count queries
    count_keywords = [
        "how many",
        "count of",
        "number of",
        "total number",
        "how much",
        "total of",
        "what are the indicators",
        "indicators of compliance"
    ]
    if any(keyword in question_lower for keyword in count_keywords):
        return "count"

    # Aggregate queries
    aggregate_keywords = [
        "list all",
        "summarize all",
        "across all",
        "in the entire",
        "throughout the guide",
        "all sections",
        "every section",
        "across the guide",
        "in all"
    ]
    if any(keyword in question_lower for keyword in aggregate_keywords):
        return "aggregate"

    # Default: specific query
    return "specific"


def get_retrieval_params(query_type: QueryType) -> Dict[str, any]:
    """
    Get retrieval parameters based on query type.

    Args:
        query_type: Classification of query

    Returns:
        Dictionary with top_k and strategy description
    """
    if query_type == "specific":
        return {
            "top_k": 5,
            "description": "Retrieve most relevant chunks for specific question"
        }
    elif query_type == "aggregate":
        return {
            "top_k": 30,
            "description": "Retrieve many chunks for summarization across sections"
        }
    elif query_type == "count":
        return {
            "top_k": 80,
            "description": "Retrieve matching chunks for counting/enumeration"
        }
    else:
        return {
            "top_k": 5,
            "description": "Default retrieval"
        }


def get_system_prompt_modifier(query_type: QueryType) -> str:
    """
    Get additional instructions for the LLM based on query type.

    Args:
        query_type: Classification of query

    Returns:
        Additional system prompt instructions
    """
    if query_type == "count":
        return """
CRITICAL FORMATTING INSTRUCTIONS FOR COUNTING QUERIES:

This is a COUNTING/ENUMERATION query about indicators of compliance. These indicators are organized by review questions in the guide.

DOCUMENT STRUCTURE - HOW TO FIND INDICATORS:
The guide uses a consistent structure for each review area:
1. Question header (e.g., "TVI6. Does the recipient monitor...")
2. Basic Requirement section
3. Applicability section
4. Detailed Explanation for Reviewer section
5. **"INDICATORS OF COMPLIANCE"** section header (all caps, bold)
6. Lettered list items (a., b., c., etc.) immediately following the header

CRITICAL EXTRACTION RULES:
- ONLY extract items from sections with the "INDICATORS OF COMPLIANCE" header
- ONLY count lettered items (a., b., c., etc.) that appear directly under this header
- IGNORE numbered lists, bullet points, or lettered items in other sections
- Each question/review area may have its own "INDICATORS OF COMPLIANCE" section
- Look for the section header pattern: "INDICATORS OF COMPLIANCE" followed by lettered items

REQUIRED OUTPUT FORMAT:
1. Count the TOTAL number of lettered sub-indicators (all the a., b., c., etc. items found under "INDICATORS OF COMPLIANCE" headers)
2. Start with: "There are [X] indicators of compliance organized by review area:" where X is the total count
3. Group indicators by their parent review question/area (e.g., TVI6, TVI7, etc.)
4. For each group, show the question/area as a header, then list all sub-indicators with their letter prefixes EXACTLY as they appear
5. Preserve the letter prefixes (a., b., c., etc.) from the original text
6. Include source citations like [Source N]

CORRECT EXAMPLE:
There are 7 indicators of compliance organized by review area:

**TVI6. Does the recipient have financial management policies?** [Source 1]
a. Recipient has written financial management policies and procedures
b. Policies include the two elements required by 2 CFR part 200
c. Policies address internal control practices

**TVI7. Are reports submitted on time?** [Source 2]
a. Milestone Progress Reports (MPRs) are submitted to FTA on time
b. Federal Financial Reports (FFRs) are complete and accurate

**TVI8. Does the recipient track funds?** [Source 3]
a. Correct drawdown of Federal funds
b. Tracking the use of Federal funds for eligible expenses

IMPORTANT:
- Count ALL the lettered sub-indicators found under "INDICATORS OF COMPLIANCE" headers - in example above, that's 3+2+2=7 total
- Keep indicators grouped under their parent question (preserve TVI6, TVI7, etc. numbering)
- Preserve letter prefixes (a., b., c.) exactly as shown in sources
- Don't renumber - keep the original structure
- CRITICAL: Remove duplicate indicators - if you see the same indicator text across multiple sources, only include it ONCE
- CRITICAL: Only include items that appear under "INDICATORS OF COMPLIANCE" section headers
- If you find lettered items in other sections (like "Detailed Explanation"), do NOT count them as indicators
- CRITICAL: Include EVERY unique TVI section found in the sources - do not skip sections
- CRITICAL: If you see TVI1, TVI2, TVI3, TVI4, TVI5, TVI6, TVI7, TVI8, TVI9, and TVI10 in the sources, you MUST include ALL of them in your response
"""
    elif query_type == "aggregate":
        return """
IMPORTANT: This is a SUMMARY/AGGREGATION query.
- Synthesize information from ALL provided sources
- Look for patterns and commonalities
- Provide a comprehensive overview
- Group similar items together
"""
    else:
        return ""
