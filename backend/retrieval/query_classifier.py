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
        "total of"
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
            "top_k": 50,
            "description": "Retrieve all matching chunks for counting/enumeration"
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
IMPORTANT: This is a COUNTING/ENUMERATION query.
- Count all distinct occurrences across ALL provided sources
- List each distinct item you find
- Provide the total count
- Be thorough and check every source for matches
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
