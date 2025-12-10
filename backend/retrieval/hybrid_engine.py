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
from database.audit_queries import AuditQueryHelper


class HybridQueryEngine:
    """Orchestrate query routing and execution across database and RAG."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        rag_pipeline=None,  # RAGPipeline instance (optional for now)
        hybrid_retriever=None,  # HybridRetriever instance (optional)
        embedding_manager=None,  # EmbeddingManager for ChromaDB access (optional)
        historical_collection=None  # ChromaDB collection for historical audits (optional)
    ):
        """
        Initialize hybrid query engine.

        Args:
            db_manager: DatabaseManager for database queries
            rag_pipeline: RAGPipeline for answer generation (optional)
            hybrid_retriever: HybridRetriever for vector search (optional)
            embedding_manager: EmbeddingManager for ChromaDB access (optional)
            historical_collection: ChromaDB collection for historical audits (optional)
        """
        self.router = QueryRouter()
        self.query_builder = QueryBuilder(db_manager)
        self.audit_helper = AuditQueryHelper(db_manager)
        self.rag_pipeline = rag_pipeline
        self.hybrid_retriever = hybrid_retriever
        self.embedding_manager = embedding_manager
        self.historical_collection = historical_collection

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

        # Check if this is a historical audit query (section_names will be None for these)
        if route.section_names is None and 'Historical audit query' in route.reasoning:
            return self._execute_historical_query(question, route)

        if not route.section_names or len(route.section_names) == 0:
            return {
                'answer': "I couldn't identify which section you're asking about. Please specify a section code (e.g., TVI3, L1, CB2).",
                'confidence': 'low',
                'sources': [],
                'backend': 'database_error'
            }

        # Determine query type from question
        question_lower = question.lower()

        # For list/count queries with multiple sections, aggregate across all
        if len(route.section_names) > 1 and ('list' in question_lower or 'show' in question_lower or 'what are' in question_lower or 'how many' in question_lower or 'question' in question_lower):
            # Multi-section list/count query - aggregate results with hierarchical structure
            is_deficiency = 'deficienc' in question_lower
            is_indicator = 'indicator' in question_lower
            is_count = 'how many' in question_lower or 'count' in question_lower
            is_questions = 'question' in question_lower

            if is_count:
                # Count aggregation
                total_count = 0
                for section_code in route.section_names:
                    if is_deficiency:
                        result = self.query_builder.count_deficiencies(section_code)
                    else:
                        result = self.query_builder.count_indicators(section_code)
                    total_count += result.get('count', 0)

                return self._format_count_result({'count': total_count, 'sections': route.section_names}, question)
            else:
                # List aggregation - use hierarchical structure
                sections_data = []
                total_items = 0

                for section_code in route.section_names:
                    if is_deficiency:
                        db_result = self.query_builder.list_deficiencies(section_code)
                        if db_result.get('found'):
                            items = db_result.get('deficiencies', [])
                            sections_data.append({
                                'question_code': section_code,
                                'question_text': db_result.get('question', {}).get('text', ''),
                                'items': items,
                                'item_type': 'deficiencies'
                            })
                            total_items += len(items)
                    elif is_indicator:
                        db_result = self.query_builder.list_indicators(section_code)
                        if db_result.get('found'):
                            items = db_result.get('indicators', [])
                            sections_data.append({
                                'question_code': section_code,
                                'question_text': db_result.get('question', {}).get('text', ''),
                                'items': items,
                                'item_type': 'indicators'
                            })
                            total_items += len(items)
                    else:
                        # Show questions with both indicators and deficiencies
                        db_result = self.query_builder.get_section(section_code)
                        if db_result.get('found'):
                            indicators = db_result.get('indicators', [])
                            deficiencies = db_result.get('deficiencies', [])
                            sections_data.append({
                                'question_code': section_code,
                                'question_text': db_result.get('question', {}).get('text', ''),
                                'items': {'indicators': indicators, 'deficiencies': deficiencies},
                                'item_type': 'both'
                            })
                            total_items += len(indicators) + len(deficiencies)

                return self._format_hierarchical_list(sections_data, total_items, question)

        # Use first section for single-section queries
        section_code = route.section_names[0]

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

        if not self.rag_pipeline or not self.embedding_manager:
            return {
                'answer': "RAG pipeline not initialized. Please use database queries for now.",
                'confidence': 'low',
                'sources': [],
                'ranked_chunks': [],
                'backend': 'rag_unavailable'
            }

        # Retrieve documents from ChromaDB collections
        # Need to embed the query using OpenAI embeddings (same as collections)
        query_embedding = self.embedding_manager.embeddings.embed_query(question)

        # Query compliance guide collection (primary)
        compliance_results = self.embedding_manager.collection.query(
            query_embeddings=[query_embedding],
            n_results=3  # Reduced to make room for historical audits
        )

        # Query historical audits collection if available
        historical_results = None
        if self.historical_collection:
            print(f"[RAG] Querying historical audits collection...")
            historical_results = self.historical_collection.query(
                query_embeddings=[query_embedding],
                n_results=3  # Get 3 historical examples
            )

        # Merge results from both collections
        all_results = {
            'ids': [[]],
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }

        # Add compliance guide results
        if compliance_results and compliance_results['ids'][0]:
            all_results['ids'][0].extend(compliance_results['ids'][0])
            all_results['documents'][0].extend(compliance_results['documents'][0])
            # Add source indicator to metadata
            for meta in compliance_results['metadatas'][0]:
                meta['source_collection'] = 'compliance_guide'
            all_results['metadatas'][0].extend(compliance_results['metadatas'][0])
            all_results['distances'][0].extend(compliance_results['distances'][0])

        # Add historical audit results
        if historical_results and historical_results['ids'][0]:
            all_results['ids'][0].extend(historical_results['ids'][0])
            all_results['documents'][0].extend(historical_results['documents'][0])
            # Add source indicator to metadata
            for meta in historical_results['metadatas'][0]:
                meta['source_collection'] = 'historical_audits'
            all_results['metadatas'][0].extend(historical_results['metadatas'][0])
            all_results['distances'][0].extend(historical_results['distances'][0])

        # Sort by distance (lower is better) and take top 5
        if all_results['ids'][0]:
            combined = list(zip(
                all_results['ids'][0],
                all_results['documents'][0],
                all_results['metadatas'][0],
                all_results['distances'][0]
            ))
            combined.sort(key=lambda x: x[3])  # Sort by distance
            combined = combined[:5]  # Take top 5

            all_results = {
                'ids': [[x[0] for x in combined]],
                'documents': [[x[1] for x in combined]],
                'metadatas': [[x[2] for x in combined]],
                'distances': [[x[3] for x in combined]]
            }

        # Merge with BM25 if hybrid retriever available
        if self.hybrid_retriever:
            retrieved_chunks = self.hybrid_retriever.merge_results(
                all_results,
                question,
                top_k=5
            )
        else:
            # Fallback to semantic only
            retrieved_chunks = []
            for i in range(len(all_results['ids'][0])):
                retrieved_chunks.append({
                    'chunk_id': all_results['ids'][0][i],
                    'text': all_results['documents'][0][i],
                    'metadata': all_results['metadatas'][0][i],
                    'semantic_score': 1 - all_results['distances'][0][i],
                    'bm25_score': 0.0,
                    'hybrid_score': 1 - all_results['distances'][0][i]
                })

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

        # Check if asking for list vs count vs applicability
        is_list_query = any(word in question_lower for word in ['list', 'show', 'what are', 'give me', 'display'])
        is_count_query = any(word in question_lower for word in ['how many', 'count', 'number of'])
        is_applicability_query = 'applicability' in question_lower

        # If asking for APPLICABILITY across multiple sections
        if is_applicability_query and len(route.section_names) > 1:
            print(f"[HYBRID] Applicability query for {len(route.section_names)} sections")

            applicability_info = []
            for section_code in route.section_names:
                db_result = self.query_builder.get_section(section_code)
                if db_result.get('found'):
                    applicability_info.append({
                        'question_code': section_code,
                        'question_text': db_result['question']['text'],
                        'applicability': db_result['question'].get('applicability', 'Not specified')
                    })

            # Format the applicability response
            answer = f"**Applicability Requirements for Charter Bus**\n\n"
            answer += f"The Charter Bus requirements have the following applicability:\n\n"

            # Get unique applicability statements
            unique_applicability = set()
            for info in applicability_info:
                if info['applicability'] and info['applicability'] != 'Not specified':
                    unique_applicability.add(info['applicability'])

            if unique_applicability:
                for appl in unique_applicability:
                    answer += f"- {appl}\n"
            else:
                answer += "No specific applicability information found.\n"

            answer += f"\n**Related Questions:**\n"
            for info in applicability_info:
                answer += f"- **{info['question_code']}**: {info['question_text']}\n"

            answer += f"\n*Source: Structured database (100% accurate)*"

            return {
                'answer': answer,
                'confidence': 'high',
                'sources': [{
                    'chunk_id': '_'.join(route.section_names),
                    'category': 'database_applicability',
                    'excerpt': f"Applicability for {len(route.section_names)} Charter Bus questions",
                    'score': 1.0,
                    'file_path': 'database://compliance_guide/charter_bus_applicability'
                }],
                'ranked_chunks': [],
                'backend': 'database_applicability',
                'metadata': {
                    'section_count': len(route.section_names)
                }
            }

        # If asking for LIST of indicators/deficiencies/questions across multiple sections
        if is_list_query and len(route.section_names) > 1:
            print(f"[HYBRID] List query for {len(route.section_names)} sections")

            # Determine what they're asking for
            is_deficiencies = 'deficienc' in question_lower
            is_indicators = 'indicator' in question_lower
            is_questions = 'question' in question_lower

            # Collect all sections with their items grouped by question
            sections_data = []
            total_items = 0

            for section_code in route.section_names:
                if is_deficiencies:
                    db_result = self.query_builder.list_deficiencies(section_code)
                elif is_indicators:
                    db_result = self.query_builder.list_indicators(section_code)
                else:
                    # Default to getting full section (both indicators and deficiencies)
                    db_result = self.query_builder.get_section(section_code)

                if db_result.get('found'):
                    items = []
                    if is_deficiencies:
                        items = db_result.get('deficiencies', [])
                    elif is_indicators:
                        items = db_result.get('indicators', [])
                    else:
                        # For questions, show both indicators and deficiencies
                        items = {
                            'indicators': db_result.get('indicators', []),
                            'deficiencies': db_result.get('deficiencies', [])
                        }

                    sections_data.append({
                        'question_code': section_code,
                        'question_text': db_result.get('question', {}).get('text', ''),
                        'items': items,
                        'stats': db_result.get('stats', {})
                    })

                    if isinstance(items, dict):
                        total_items += len(items.get('indicators', [])) + len(items.get('deficiencies', []))
                    else:
                        total_items += len(items)

            # Format the hierarchical list
            if is_deficiencies:
                item_type = 'Deficiencies'
                answer = f"**Possible Deficiencies Grouped by Question**\n\n"
            elif is_indicators:
                item_type = 'Indicators of Compliance'
                answer = f"**Indicators of Compliance Grouped by Question**\n\n"
            else:
                item_type = 'Questions'
                answer = f"**Questions with Indicators and Deficiencies**\n\n"

            answer += f"Found **{len(sections_data)} questions** with **{total_items} total items**:\n\n"

            # Group items under questions
            for section in sections_data:
                answer += f"### {section['question_code']}\n"
                answer += f"**Question:** {section['question_text']}\n\n"

                if isinstance(section['items'], dict):
                    # Show both indicators and deficiencies
                    indicators = section['items'].get('indicators', [])
                    deficiencies = section['items'].get('deficiencies', [])

                    if indicators:
                        answer += f"**Indicators of Compliance ({len(indicators)}):**\n"
                        for ind in indicators:
                            answer += f"  {ind.get('letter', '')}. {ind.get('text', '')}\n"
                        answer += "\n"

                    if deficiencies:
                        answer += f"**Possible Deficiencies ({len(deficiencies)}):**\n"
                        for def_ in deficiencies:
                            answer += f"  • **{def_.get('code', 'N/A')}**: {def_.get('title', '')}\n"
                        answer += "\n"
                else:
                    # Show only indicators or only deficiencies
                    if is_deficiencies:
                        answer += f"**Possible Deficiencies ({len(section['items'])}):**\n"
                        for def_ in section['items']:
                            answer += f"  • **{def_.get('code', 'N/A')}**: {def_.get('title', '')}\n"
                    else:
                        answer += f"**Indicators of Compliance ({len(section['items'])}):**\n"
                        for ind in section['items']:
                            answer += f"  {ind.get('letter', '')}. {ind.get('text', '')}\n"
                    answer += "\n"

            answer += f"*Source: Structured database (100% accurate)*"

            return {
                'answer': answer,
                'confidence': 'high',
                'sources': [{
                    'chunk_id': f"list_{'_'.join(route.section_names[:3])}",
                    'category': 'database_list',
                    'excerpt': f"{total_items} items from {len(sections_data)} questions",
                    'score': 1.0,
                    'file_path': 'database://compliance_guide/multi_section_list'
                }],
                'ranked_chunks': [],
                'backend': 'database_list',
                'metadata': {
                    'section_count': len(route.section_names),
                    'item_count': total_items
                }
            }

        # If asking for count across multiple sections, aggregate
        if is_count_query and len(route.section_names) > 1:
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
                    'chunk_id': f"multi_section_{'_'.join(route.section_names[:3])}",
                    'category': 'database_aggregate',
                    'excerpt': f"{count_value} {count_type} across {len(route.section_names)} questions",
                    'score': 1.0,
                    'file_path': f"database://compliance_guide/{section_name.lower().replace(' ', '_')}"
                }],
                'ranked_chunks': [],
                'backend': 'database_aggregate',
                'metadata': {
                    'section_count': len(route.section_names),
                    'total_indicators': total_indicators,
                    'total_deficiencies': total_deficiencies
                }
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
        # Check if multi-section aggregation
        is_multi_section = 'sections' in db_result and not db_result.get('question_info')

        if is_multi_section:
            # Multi-section count
            count = db_result['count']
            sections = db_result['sections']
            count_type = 'deficiencies' if 'deficienc' in question.lower() else 'indicators of compliance'

            answer = f"There are **{count} total {count_type}** across {len(sections)} questions ({', '.join(sections)}).\n\n"
            answer += f"*Source: Structured database (100% accurate)*"

            chunk_id = ', '.join(sections)
            file_path = f"database://compliance_guide/{'-'.join(sections)}"
            excerpt = f"Total count from {len(sections)} questions: {count} {count_type}"
        else:
            # Single-section count
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

            chunk_id = question_code
            file_path = f"database://compliance_guide/{question_code}"
            excerpt = f"{question_text[:100]}..."

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'chunk_id': chunk_id,
                'category': 'database_count',
                'excerpt': excerpt,
                'score': 1.0,
                'file_path': file_path
            }],
            'ranked_chunks': [],
            'backend': 'database',
            'metadata': {'db_result': db_result}
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

        # Check if multi-section aggregation
        is_multi_section = db_result.get('multi_section', False)

        if is_multi_section:
            # Multi-section list result
            sections = db_result.get('sections', [])

            if 'indicators' in db_result:
                items = db_result['indicators']
                item_type = 'indicators of compliance'
                answer = f"**{len(items)} total indicators of compliance** across {len(sections)} questions ({', '.join(sections)}):\n\n"

                for i, item in enumerate(items, 1):
                    answer += f"{i}. {item['text']}\n\n"
            else:
                items = db_result['deficiencies']
                item_type = 'potential deficiencies'
                answer = f"**{len(items)} total potential deficiencies** across {len(sections)} questions ({', '.join(sections)}):\n\n"

                for i, item in enumerate(items, 1):
                    answer += f"{i}. **{item.get('code', 'N/A')}**: {item.get('title', item.get('text', ''))}\n\n"
        else:
            # Single-section result
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

        # Build source citation
        if is_multi_section:
            chunk_id = ', '.join(sections)
            file_path = f"database://compliance_guide/{'-'.join(sections)}"
            excerpt = f"Aggregated data from {len(sections)} questions ({len(items)} items)"
        else:
            chunk_id = question_code
            file_path = f"database://compliance_guide/{question_code}"
            excerpt = f"{question_text[:100]}... ({len(items)} items)"

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'chunk_id': chunk_id,
                'category': 'database_list',
                'excerpt': excerpt,
                'score': 1.0,
                'file_path': file_path
            }],
            'ranked_chunks': [],
            'backend': 'database',
            'metadata': {'db_result': db_result}
        }

    def _format_hierarchical_list(self, sections_data: List[Dict[str, Any]], total_items: int, question: str) -> Dict[str, Any]:
        """
        Format a hierarchical list showing items grouped under questions.

        Args:
            sections_data: List of dicts with question_code, question_text, items, item_type
            total_items: Total count of all items
            question: Original question text

        Returns:
            Formatted response dict
        """
        if not sections_data:
            return {
                'answer': "No data found for the requested sections.",
                'confidence': 'low',
                'sources': [],
                'ranked_chunks': [],
                'backend': 'database'
            }

        # Determine title based on query
        question_lower = question.lower()
        if 'deficienc' in question_lower:
            title = "**Possible Deficiencies Grouped by Question**"
        elif 'indicator' in question_lower:
            title = "**Indicators of Compliance Grouped by Question**"
        else:
            title = "**Questions with Indicators and Deficiencies**"

        answer = f"{title}\n\n"
        answer += f"Found **{len(sections_data)} questions** with **{total_items} total items**:\n\n"

        # Format each section hierarchically
        for section in sections_data:
            answer += f"### {section['question_code']}\n"
            answer += f"**Question:** {section['question_text']}\n\n"

            if section['item_type'] == 'both':
                # Show both indicators and deficiencies
                indicators = section['items'].get('indicators', [])
                deficiencies = section['items'].get('deficiencies', [])

                if indicators:
                    answer += f"**Indicators of Compliance ({len(indicators)}):**\n"
                    for ind in indicators:
                        answer += f"  {ind.get('letter', '')}. {ind.get('text', '')}\n"
                    answer += "\n"

                if deficiencies:
                    answer += f"**Possible Deficiencies ({len(deficiencies)}):**\n"
                    for def_ in deficiencies:
                        answer += f"  • **{def_.get('code', 'N/A')}**: {def_.get('title', '')}\n"
                    answer += "\n"

            elif section['item_type'] == 'deficiencies':
                # Show only deficiencies
                items = section['items']
                if items:
                    answer += f"**Possible Deficiencies ({len(items)}):**\n"
                    for def_ in items:
                        answer += f"  • **{def_.get('code', 'N/A')}**: {def_.get('title', '')}\n"
                    answer += "\n"

            elif section['item_type'] == 'indicators':
                # Show only indicators
                items = section['items']
                if items:
                    answer += f"**Indicators of Compliance ({len(items)}):**\n"
                    for ind in items:
                        answer += f"  {ind.get('letter', '')}. {ind.get('text', '')}\n"
                    answer += "\n"

        answer += f"*Source: Structured database (100% accurate)*"

        # Build section codes list for metadata
        section_codes = [s['question_code'] for s in sections_data]

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'chunk_id': '_'.join(section_codes[:3]) + ('...' if len(section_codes) > 3 else ''),
                'category': 'database_hierarchical_list',
                'excerpt': f"{total_items} items from {len(sections_data)} questions",
                'score': 1.0,
                'file_path': f"database://compliance_guide/{'-'.join(section_codes[:3])}"
            }],
            'ranked_chunks': [],
            'backend': 'database_hierarchical',
            'metadata': {
                'section_count': len(sections_data),
                'item_count': total_items
            }
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
                'chunk_id': question_code,
                'category': 'database_section',
                'excerpt': f"{question['text'][:100]}...",
                'score': 1.0,
                'file_path': f"database://compliance_guide/{section.get('code')}/{question_code}"
            }],
            'ranked_chunks': [],
            'backend': 'database',
            'metadata': {'db_result': db_result}
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
                'chunk_id': 'aggregate_stats',
                'category': 'database_aggregate',
                'excerpt': f"Total stats: {totals['sections']} sections, {totals['questions']} questions, {totals['indicators']} indicators",
                'score': 1.0,
                'file_path': 'database://compliance_guide/aggregate'
            }],
            'ranked_chunks': [],
            'backend': 'database_aggregate',
            'metadata': {'db_result': db_result}
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
                'chunk_id': '_'.join([d['question_code'] for d in section_data[:3]]),
                'category': 'database_comparison',
                'excerpt': f"Comparison of {len(section_data)} sections",
                'score': 1.0,
                'file_path': 'database://compliance_guide/comparison'
            }],
            'ranked_chunks': [],
            'backend': 'database_comparison',
            'metadata': {'section_count': len(section_data)}
        }

    def _execute_historical_query(self, question: str, route: QueryRoute) -> Dict[str, Any]:
        """
        Execute a historical audit query.

        Args:
            question: User's question
            route: QueryRoute with pattern_type in keywords

        Returns:
            Formatted historical audit result
        """
        import re

        question_lower = question.lower()
        print(f"[HISTORICAL] Executing historical audit query: {route.reasoning}")

        # Extract recipient identifier from question
        # Strategy: Try multiple patterns to capture both acronyms and multi-word names

        # Pattern 1: Uppercase acronyms (e.g., "GNHTD", "AMTRAN")
        acronym_pattern = r'\b([A-Z]{2,10})\b'
        acronym_matches = re.findall(acronym_pattern, question)

        # Filter out common words
        common_words = {'FTA', 'FY', 'TR', 'SMR', 'ADA', 'DBE', 'REGION', 'THE', 'AND', 'FOR', 'WITH'}
        recipient_candidates = [m for m in acronym_matches if m not in common_words]

        # Pattern 2: Multi-word capitalized names (e.g., "Alameda CTC", "Greater New Haven Transit", "City of Bangor")
        # This pattern matches:
        # - Capitalized word + acronym (e.g., "Alameda CTC")
        # - Multiple capitalized words (e.g., "Greater New Haven Transit")
        # - City/County/Borough + of + Name (e.g., "City of Bangor", "County of Lackawanna")
        multiword_patterns = [
            r'\b((?:City|County|Borough|Town)\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # City of X
            r'\b([A-Z][a-z]+\s+[A-Z]{2,10})\b',  # Word + Acronym (e.g., "Alameda CTC")
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'  # Multiple words (e.g., "Greater New Haven")
        ]
        multiword_matches = []
        for pattern in multiword_patterns:
            multiword_matches.extend(re.findall(pattern, question))

        # Combine both patterns (prefer multiword matches as they're more specific)
        recipient_candidates = multiword_matches + recipient_candidates

        print(f"[HISTORICAL] Extracted recipient candidates: {recipient_candidates}")

        # Handle recipient-specific queries
        if 'deficienc' in question_lower and recipient_candidates:
            recipient = recipient_candidates[0]
            fiscal_year = None

            # Extract fiscal year if mentioned
            fy_pattern = r'(FY\s*\d{4}|\d{4})'
            fy_match = re.search(fy_pattern, question, re.IGNORECASE)
            if fy_match:
                fiscal_year = fy_match.group(1)

            result = self.audit_helper.get_recipient_deficiencies(recipient, fiscal_year)
            return self._format_recipient_deficiencies(result, recipient)

        # Handle regional queries
        if 'region' in question_lower:
            region_match = re.search(r'region\s+(\d+)', question_lower)
            if region_match:
                region_num = int(region_match.group(1))

                # Check if filtering by review area
                review_area = None
                if 'procurement' in question_lower:
                    review_area = 'Procurement'
                elif 'legal' in question_lower:
                    review_area = 'Legal'
                elif 'maintenance' in question_lower:
                    review_area = 'Maintenance'
                elif 'title vi' in question_lower or 'title 6' in question_lower:
                    review_area = 'Title VI'

                result = self.audit_helper.get_regional_deficiencies(region_num, review_area)
                return self._format_regional_deficiencies(result)

        # Handle common deficiencies queries
        if 'common' in question_lower or 'typical' in question_lower or 'frequent' in question_lower:
            review_area = None
            if 'procurement' in question_lower:
                review_area = 'Procurement'
            elif 'legal' in question_lower:
                review_area = 'Legal'
            elif 'maintenance' in question_lower:
                review_area = 'Maintenance'

            result = self.audit_helper.get_common_deficiencies(review_area, min_occurrences=2)
            return self._format_common_deficiencies(result)

        # Handle ranking queries
        if 'ranking_query' in route.reasoning or any(term in question_lower for term in ['most', 'worst', 'best', 'least', 'highest', 'lowest', 'top', 'bottom']):
            # Determine order (most/worst/highest = desc, least/best/lowest = asc)
            order = 'desc'
            if any(term in question_lower for term in ['least', 'best', 'lowest', 'fewest']):
                order = 'asc'

            result = self.audit_helper.get_recipients_by_deficiency_count(limit=10, order=order)
            return self._format_ranking_result(result, question)

        # Handle list all recipients query
        if 'list' in question_lower and ('recipient' in question_lower or 'agenc' in question_lower):
            region_num = None
            region_match = re.search(r'region\s+(\d+)', question_lower)
            if region_match:
                region_num = int(region_match.group(1))

            result = self.audit_helper.list_all_recipients(region_number=region_num)
            return self._format_recipients_list(result)

        # Default: couldn't parse historical query
        return {
            'answer': "I understand you're asking about historical audit data, but I couldn't parse your specific question. Try asking:\n\n- 'What deficiencies did [ACRONYM] have?' (e.g., GNHTD, AMTRAN)\n- 'Region 1 deficiencies'\n- 'Common procurement deficiencies'\n- 'List all recipients'",
            'confidence': 'low',
            'sources': [],
            'ranked_chunks': [],
            'backend': 'historical_query_error'
        }

    def _format_recipient_deficiencies(self, result: Dict[str, Any], recipient_id: str) -> Dict[str, Any]:
        """Format recipient deficiency query results."""
        if 'error' in result:
            return {
                'answer': result['error'],
                'confidence': 'low',
                'sources': [],
                'ranked_chunks': [],
                'backend': 'historical_not_found'
            }

        recipient = result['recipient']
        deficiencies = result['deficiencies']

        answer = f"## {recipient['name']} ({recipient['acronym']})\n\n"
        answer += f"**Location**: {recipient['city']}, {recipient['state']}\n"
        answer += f"**FTA Region**: {recipient['region']}\n\n"
        answer += f"**Total Deficiencies**: {result['total_deficiencies']}\n\n"

        if deficiencies:
            answer += "### Deficiencies by Review Area\n\n"

            # Group by review area
            by_area = {}
            for d in deficiencies:
                area = d['review_area']
                if area not in by_area:
                    by_area[area] = []
                by_area[area].append(d)

            for area, items in sorted(by_area.items()):
                answer += f"**{area}** ({len(items)} deficienc{'y' if len(items) == 1 else 'ies'}):\n\n"
                for d in items:
                    if d['deficiency_code']:
                        answer += f"- **{d['deficiency_code']}**: {d['description'][:200] if d['description'] else 'No description'}\n"
                    else:
                        answer += f"- {d['description'][:200] if d['description'] else 'No description'}\n"
                answer += "\n"
        else:
            answer += "*No deficiencies found for this recipient.*\n"

        answer += "\n*Source: Historical FTA Audit Reviews Database*"

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'chunk_id': f"audit_{recipient['acronym']}",
                'category': 'historical_audit',
                'excerpt': f"{recipient['name']} audit deficiencies",
                'score': 1.0,
                'file_path': 'database://historical_audits/recipient_deficiencies',
                'source_collection': 'historical_audits'
            }],
            'ranked_chunks': [],
            'backend': 'historical_audit'
        }

    def _format_regional_deficiencies(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format regional deficiency query results."""
        region = result['region']
        recipients = result['recipients']

        answer = f"## Region {region} Deficiencies\n\n"
        answer += f"**Total Recipients with Deficiencies**: {result['total_recipients']}\n\n"

        if recipients:
            for r in recipients:
                answer += f"### {r['name']} ({r['acronym']}) - {r['state']}\n\n"
                for d in r['deficiencies']:
                    answer += f"- **{d['review_area']}**: {d['count']} deficienc{'y' if d['count'] == 1 else 'ies'}\n"
                answer += "\n"
        else:
            answer += "*No deficiencies found for this region.*\n"

        answer += "\n*Source: Historical FTA Audit Reviews Database*"

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'chunk_id': f"region_{region}",
                'category': 'historical_audit',
                'excerpt': f"Region {region} audit deficiencies",
                'score': 1.0,
                'file_path': 'database://historical_audits/regional_deficiencies',
                'source_collection': 'historical_audits'
            }],
            'ranked_chunks': [],
            'backend': 'historical_audit'
        }

    def _format_common_deficiencies(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format common deficiency query results."""
        deficiencies = result['common_deficiencies']

        answer = "## Common Deficiencies Across All Recipients\n\n"

        if deficiencies:
            answer += "| Review Area | Recipients Affected | Total Occurrences |\n"
            answer += "|------------|---------------------|-------------------|\n"

            for d in deficiencies:
                answer += f"| {d['review_area']} | {d['recipient_count']} | {d['total_deficiencies']} |\n"

            answer += f"\n**Total Areas with Common Deficiencies**: {len(deficiencies)}\n"
        else:
            answer += "*No common deficiencies found.*\n"

        answer += "\n*Source: Historical FTA Audit Reviews Database (minimum 2 recipients)*"

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'chunk_id': 'common_deficiencies',
                'category': 'historical_audit',
                'excerpt': 'Common deficiencies across recipients',
                'score': 1.0,
                'file_path': 'database://historical_audits/common_deficiencies',
                'source_collection': 'historical_audits'
            }],
            'ranked_chunks': [],
            'backend': 'historical_audit'
        }

    def _format_ranking_result(self, result: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Format ranking query results."""
        recipients = result['recipients']
        order = result['order']

        # Determine title based on order
        if order == 'desc':
            title = "## Recipients with Most Deficiencies\n\n"
        else:
            title = "## Recipients with Fewest Deficiencies\n\n"

        answer = title

        if recipients:
            answer += f"Showing top {len(recipients)} recipients:\n\n"
            answer += "| Rank | Recipient | Location | Region | Deficiencies |\n"
            answer += "|------|-----------|----------|--------|-------------|\n"

            for i, r in enumerate(recipients, 1):
                city_str = f"{r['city']}, " if r['city'] else ""
                location = f"{city_str}{r['state']}"
                answer += f"| {i} | **{r['name']}** ({r['acronym']}) | {location} | {r['region']} | {r['deficiency_count']} |\n"

            # Add summary
            if order == 'desc':
                answer += f"\n**Most deficiencies**: {recipients[0]['name']} with {recipients[0]['deficiency_count']} deficiencies\n"
            else:
                answer += f"\n**Fewest deficiencies**: {recipients[0]['name']} with {recipients[0]['deficiency_count']} deficiencies\n"
        else:
            answer += "*No recipients found.*\n"

        answer += "\n*Source: Historical FTA Audit Reviews Database*"

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'chunk_id': 'ranking_deficiencies',
                'category': 'historical_audit',
                'excerpt': f'Top {len(recipients)} recipients by deficiency count',
                'score': 1.0,
                'file_path': 'database://historical_audits/ranking',
                'source_collection': 'historical_audits'
            }],
            'ranked_chunks': [],
            'backend': 'historical_audit'
        }

    def _format_recipients_list(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format recipients list query results."""
        recipients = result['recipients']

        answer = f"## All Recipients ({result['total_recipients']} total)\n\n"

        if recipients:
            # Group by state
            by_state = {}
            for r in recipients:
                state = r['state'] or 'Unknown'
                if state not in by_state:
                    by_state[state] = []
                by_state[state].append(r)

            for state, items in sorted(by_state.items()):
                answer += f"### {state}\n\n"
                for r in items:
                    city_str = f", {r['city']}" if r['city'] else ""
                    reviews = f"{r['review_count']} review{'s' if r['review_count'] != 1 else ''}"
                    answer += f"- **{r['name']}** ({r['acronym']}) - Region {r['region']}{city_str} - *{reviews}*\n"
                answer += "\n"
        else:
            answer += "*No recipients found.*\n"

        answer += "\n*Source: Historical FTA Audit Reviews Database*"

        return {
            'answer': answer,
            'confidence': 'high',
            'sources': [{
                'chunk_id': 'all_recipients',
                'category': 'historical_audit',
                'excerpt': f'{result["total_recipients"]} recipients',
                'score': 1.0,
                'file_path': 'database://historical_audits/recipients',
                'source_collection': 'historical_audits'
            }],
            'ranked_chunks': [],
            'backend': 'historical_audit'
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
