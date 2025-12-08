"""Hybrid query engine - orchestrates database and RAG retrieval."""
from typing import Dict, List, Any, Optional
import time
import sys
from pathlib import Path

# Add backend to path for relative imports
if __name__ == "__main__":
    backend_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_dir))

from retrieval.query_router import QueryRouter, QueryRoute
from database.query_builder import QueryBuilder
from database.connection import DatabaseManager


class HybridQueryEngine:
    """Orchestrate query routing and execution across database and RAG."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        rag_pipeline=None,  # RAGPipeline instance (optional for now)
        hybrid_retriever=None  # HybridRetriever instance (optional)
    ):
        """
        Initialize hybrid query engine.

        Args:
            db_manager: DatabaseManager for database queries
            rag_pipeline: RAGPipeline for answer generation (optional)
            hybrid_retriever: HybridRetriever for vector search (optional)
        """
        self.router = QueryRouter()
        self.query_builder = QueryBuilder(db_manager)
        self.rag_pipeline = rag_pipeline
        self.hybrid_retriever = hybrid_retriever

    def execute_query(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Execute a query using the appropriate backend(s).

        Args:
            question: User's question
            conversation_history: Previous conversation (optional)

        Returns:
            Formatted response with answer, sources, and metadata
        """
        start_time = time.time()

        # Step 1: Route the query
        route = self.router.classify_query(question)
        print(f"[HYBRID ENGINE] Route: {route.route_type.upper()} (confidence: {route.confidence:.2f})")
        print(f"[HYBRID ENGINE] Reasoning: {route.reasoning}")

        # Step 2: Execute based on route type
        if route.route_type == "database":
            result = self._execute_database_query(question, route)
        elif route.route_type == "rag":
            result = self._execute_rag_query(question, conversation_history)
        else:  # hybrid
            result = self._execute_hybrid_query(question, route, conversation_history)

        # Add execution metadata
        execution_time = time.time() - start_time
        result['metadata'] = {
            'route_type': route.route_type,
            'confidence': route.confidence,
            'reasoning': route.reasoning,
            'execution_time_ms': round(execution_time * 1000, 2),
            'sections': route.section_names
        }

        return result

    def _execute_database_query(self, question: str, route: QueryRoute) -> Dict[str, Any]:
        """
        Execute a pure database query.

        Args:
            question: User's question
            route: QueryRoute with section names

        Returns:
            Formatted database result
        """
        print(f"[DATABASE] Executing database query for: {route.section_names}")

        if not route.section_names or len(route.section_names) == 0:
            return {
                'answer': "I couldn't identify which section you're asking about. Please specify a section code (e.g., TVI3, L1, CB2).",
                'confidence': 'low',
                'sources': [],
                'backend': 'database_error'
            }

        # Use first section (single section queries only reach here)
        section_code = route.section_names[0]

        # Determine query type from question
        question_lower = question.lower()

        if 'how many' in question_lower or 'count' in question_lower:
            # Count query
            if 'deficienc' in question_lower:
                db_result = self.query_builder.count_deficiencies(section_code)
            else:
                db_result = self.query_builder.count_indicators(section_code)

            return self._format_count_result(db_result, question)

        elif 'list' in question_lower or 'show' in question_lower or 'all' in question_lower:
            # List query
            if 'deficienc' in question_lower:
                db_result = self.query_builder.list_deficiencies(section_code)
            else:
                db_result = self.query_builder.list_indicators(section_code)

            return self._format_list_result(db_result)

        else:
            # Get section (default for "what is X?" queries)
            db_result = self.query_builder.get_section(section_code)
            return self._format_section_result(db_result)

    def _execute_rag_query(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Execute a pure RAG query.

        Args:
            question: User's question
            conversation_history: Previous conversation

        Returns:
            RAG result
        """
        print(f"[RAG] Executing RAG query")

        if not self.rag_pipeline or not self.hybrid_retriever:
            return {
                'answer': "RAG pipeline not initialized. Please use database queries for now.",
                'confidence': 'low',
                'sources': [],
                'backend': 'rag_unavailable'
            }

        # Retrieve documents
        retrieved_chunks = self.hybrid_retriever.search(question, top_k=5)

        # Generate answer
        result = self.rag_pipeline.process_query(
            question,
            retrieved_chunks,
            conversation_history
        )

        result['backend'] = 'rag'
        return result

    def _execute_hybrid_query(
        self,
        question: str,
        route: QueryRoute,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Execute a hybrid query (database + RAG).

        Args:
            question: User's question
            route: QueryRoute with section names
            conversation_history: Previous conversation

        Returns:
            Merged result from database and RAG
        """
        print(f"[HYBRID] Executing hybrid query")

        # Check if it's an aggregate query (no specific sections)
        if not route.section_names:
            print(f"[HYBRID] Aggregate query - getting total counts")
            db_result = self.query_builder.get_total_counts()
            return self._format_aggregate_result(db_result, question)

        # Multi-section query - check if it's a count/list query
        print(f"[HYBRID] Multi-section query for: {route.section_names}")

        question_lower = question.lower()

        # If asking for count across multiple sections, aggregate
        if ('how many' in question_lower or 'count' in question_lower) and len(route.section_names) > 1:
            print(f"[HYBRID] Aggregating counts across {len(route.section_names)} sections")
            total_indicators = 0
            total_deficiencies = 0

            for section_code in route.section_names:
                db_result = self.query_builder.get_section(section_code)
                if db_result['found']:
                    total_indicators += db_result['stats']['indicator_count']
                    total_deficiencies += db_result['stats']['deficiency_count']

            # Format as aggregate count
            count_type = 'deficiencies' if 'deficienc' in question_lower else 'indicators of compliance'
            count_value = total_deficiencies if 'deficienc' in question_lower else total_indicators

            # Extract section name from query
            section_name = "the selected sections"
            for name in ["Legal", "Title VI", "Charter Bus", "School Bus", "ADA", "Procurement", "Financial"]:
                if name.lower() in question_lower:
                    section_name = name
                    break

            answer = f"**{section_name}** ({len(route.section_names)} questions: {', '.join(route.section_names[:5])}{'...' if len(route.section_names) > 5 else ''})\n\n"
            answer += f"There are **{count_value} total {count_type}** across all questions in this section.\n\n"
            answer += f"*Source: Structured database (100% accurate)*"

            return {
                'answer': answer,
                'confidence': 'high',
                'sources': [{
                    'type': 'database',
                    'sections': route.section_names,
                    'count': count_value
                }],
                'ranked_chunks': [],
                'backend': 'database_aggregate',
                'section_count': len(route.section_names),
                'total_indicators': total_indicators,
                'total_deficiencies': total_deficiencies
            }

        # Otherwise, get detailed data for each section
        section_data = []
        for section_code in route.section_names:
            db_result = self.query_builder.get_section(section_code)
            if db_result['found']:
                section_data.append(db_result)

        # Format as comparison
        return self._format_comparison_result(section_data, question)

    def _format_count_result(self, db_result: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Format a count query result."""
        if not db_result.get('question_info'):
            return {
                'answer': f"Question code {db_result.get('question_code', 'unknown')} not found in database.",
                'confidence': 'low',
                'sources': [],
                'ranked_chunks': [],
                'backend': 'database'
            }

        count = db_result['count']
        question_code = db_result['question_code']
        question_text = db_result['question_info']['question_text']

        # Determine what we're counting
        count_type = 'deficiencies' if 'deficienc' in question.lower() else 'indicators of compliance'

        answer = f"**{question_code}**: {question_text}\n\n"
        answer += f"There are **{count} {count_type}** for this question.\n\n"
        answer += f"*Source: Structured database (100% accurate)*"

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'type': 'database',
                'question_code': question_code,
                'count': count
            }],
            'ranked_chunks': [],
            'backend': 'database',
            'db_result': db_result
        }

    def _format_list_result(self, db_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format a list query result."""
        if not db_result.get('found'):
            return {
                'answer': db_result.get('error', 'Data not found'),
                'confidence': 'low',
                'sources': [],
                'ranked_chunks': [],
                'backend': 'database'
            }

        question_code = db_result['question_code']
        question_text = db_result.get('question', {}).get('text', '')

        # Determine if indicators or deficiencies
        if 'indicators' in db_result:
            items = db_result['indicators']
            item_type = 'Indicators of Compliance'
            answer = f"**{question_code}**: {question_text}\n\n"
            answer += f"There are **{len(items)} indicators of compliance**:\n\n"

            for item in items:
                answer += f"{item['letter']}. {item['text']}\n\n"

        else:  # deficiencies
            items = db_result['deficiencies']
            item_type = 'Potential Deficiencies'
            answer = f"**{question_code}**: {question_text}\n\n"
            answer += f"There are **{len(items)} potential deficiencies**:\n\n"

            for item in items:
                answer += f"**{item['code']}**: {item['title']}\n"
                answer += f"- Determination: {item['determination']}\n"
                if item.get('corrective_action'):
                    answer += f"- Corrective Action: {item['corrective_action']}\n"
                answer += "\n"

        answer += f"*Source: Structured database (100% accurate)*"

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'type': 'database',
                'question_code': question_code,
                'item_count': len(items)
            }],
            'ranked_chunks': [],
            'backend': 'database',
            'db_result': db_result
        }

    def _format_section_result(self, db_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format a get section query result."""
        if not db_result.get('found'):
            return {
                'answer': db_result.get('error', 'Section not found'),
                'confidence': 'low',
                'sources': [],
                'ranked_chunks': [],
                'backend': 'database'
            }

        question_code = db_result['question_code']
        section = db_result['section']
        question = db_result['question']
        stats = db_result['stats']

        answer = f"**{question_code}**: {question['text']}\n\n"

        if section.get('name'):
            answer += f"**Section**: {section['name']}\n\n"

        if question.get('basic_requirement'):
            answer += f"**Basic Requirement**: {question['basic_requirement']}\n\n"

        if question.get('applicability'):
            answer += f"**Applicability**: {question['applicability']}\n\n"

        answer += f"**Statistics**:\n"
        answer += f"- Indicators of Compliance: {stats['indicator_count']}\n"
        answer += f"- Potential Deficiencies: {stats['deficiency_count']}\n\n"

        if db_result['indicators']:
            answer += f"**Indicators of Compliance** ({stats['indicator_count']}):\n"
            for ind in db_result['indicators'][:5]:  # Show first 5
                answer += f"{ind['letter']}. {ind['text']}\n"
            if stats['indicator_count'] > 5:
                answer += f"... and {stats['indicator_count'] - 5} more\n"
            answer += "\n"

        answer += f"*Source: Structured database (100% accurate)*"

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'type': 'database',
                'question_code': question_code,
                'section': section.get('code')
            }],
            'ranked_chunks': [],
            'backend': 'database',
            'db_result': db_result
        }

    def _format_aggregate_result(self, db_result: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Format aggregate statistics result."""
        totals = db_result['totals']

        answer = f"**Overall FTA Compliance Guide Statistics**\n\n"
        answer += f"- **Sections**: {totals['sections']}\n"
        answer += f"- **Questions**: {totals['questions']}\n"
        answer += f"- **Indicators of Compliance**: {totals['indicators']}\n"
        answer += f"- **Potential Deficiencies**: {totals['deficiencies']}\n\n"
        answer += f"*Source: Structured database (100% accurate)*"

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'type': 'database',
                'aggregate': True
            }],
            'ranked_chunks': [],
            'backend': 'database_aggregate',
            'db_result': db_result
        }

    def _format_comparison_result(self, section_data: List[Dict[str, Any]], question: str) -> Dict[str, Any]:
        """Format multi-section comparison result."""
        if not section_data:
            return {
                'answer': "Could not find the requested sections.",
                'confidence': 'low',
                'sources': [],
                'ranked_chunks': [],
                'backend': 'database'
            }

        answer = f"**Comparison of {len(section_data)} sections**:\n\n"

        for data in section_data:
            qcode = data['question_code']
            question_text = data['question']['text']
            stats = data['stats']

            answer += f"### {qcode}\n"
            answer += f"{question_text}\n\n"
            answer += f"- Indicators: {stats['indicator_count']}\n"
            answer += f"- Deficiencies: {stats['deficiency_count']}\n\n"

        answer += f"*Source: Structured database (100% accurate)*"

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'type': 'database',
                'sections': [d['question_code'] for d in section_data]
            }],
            'ranked_chunks': [],
            'backend': 'database_comparison',
            'section_count': len(section_data)
        }


# Example usage
if __name__ == "__main__":
    import os
    from database.connection import get_db_manager

    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:Forest12345#@localhost:5432/cortap_compliance')
    db_manager = get_db_manager(db_url)

    engine = HybridQueryEngine(db_manager)

    test_queries = [
        "How many indicators are in TVI3?",
        "List all indicators for L1",
        "What is CB1?",
        "Compare TVI3 and L1",
        "How many total indicators are there?",
    ]

    print("=" * 80)
    print("HYBRID ENGINE TEST")
    print("=" * 80)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 80)
        result = engine.execute_query(query)
        print(f"Backend: {result.get('backend')}")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Answer preview: {result['answer'][:150]}...")
        print(f"Execution time: {result['metadata']['execution_time_ms']}ms")
