"""RAG pipeline for query processing and answer generation."""
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import json
from difflib import SequenceMatcher
from .query_classifier import classify_query, get_system_prompt_modifier
from .query_router import QueryRouter, QueryRoute


class RAGPipeline:
    """Orchestrate retrieval and generation for Q&A."""

    def __init__(
        self,
        openai_api_key: str,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.0
    ):
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=openai_api_key
        )
        self.router = QueryRouter()

    def route_query(self, question: str) -> QueryRoute:
        """
        Route a query to determine the best processing strategy.

        Args:
            question: User's question

        Returns:
            QueryRoute with classification and metadata
        """
        route = self.router.classify_query(question)
        print(f"[ROUTER] Query classified as: {route.route_type.upper()}")
        print(f"[ROUTER] Confidence: {route.confidence:.2f}")
        print(f"[ROUTER] Reasoning: {route.reasoning}")
        if route.section_names:
            print(f"[ROUTER] Sections: {', '.join(route.section_names)}")
        return route

    def deduplicate_chunks(self, chunks: List[Dict[str, any]], similarity_threshold: float = 0.85) -> List[Dict[str, any]]:
        """
        Remove duplicate chunks based on text similarity and diversify by sub-area.

        Args:
            chunks: List of retrieved chunks
            similarity_threshold: Similarity ratio (0-1) above which chunks are considered duplicates

        Returns:
            Deduplicated and diversified list of chunks
        """
        if not chunks:
            return chunks

        deduplicated = []
        seen_texts = []
        seen_sections = {}  # Track how many chunks per section (e.g., TVI3, TVI6)

        for chunk in chunks:
            chunk_text = chunk['text'].strip()
            is_duplicate = False

            # Extract section ID (e.g., TVI3, TVI6) from text
            section_id = None
            import re
            section_match = re.search(r'\b(TVI\d+(?:-\d+)?)\b', chunk_text)
            if section_match:
                section_id = section_match.group(1)

            # Check text similarity
            for seen_text in seen_texts:
                similarity = SequenceMatcher(None, chunk_text, seen_text).ratio()
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    print(f"[DEDUP] Skipping duplicate chunk (similarity: {similarity:.2f})")
                    break

            # Also limit chunks per section to avoid over-representation
            if not is_duplicate and section_id:
                section_count = seen_sections.get(section_id, 0)
                # Allow max 3 chunks per section to ensure diversity
                if section_count >= 3:
                    print(f"[DEDUP] Skipping chunk from {section_id} (already have {section_count} chunks from this section)")
                    is_duplicate = True
                else:
                    seen_sections[section_id] = section_count + 1

            if not is_duplicate:
                deduplicated.append(chunk)
                seen_texts.append(chunk_text)

        print(f"[DEDUP] Reduced {len(chunks)} chunks to {len(deduplicated)} unique chunks")
        print(f"[DEDUP] Sections represented: {list(seen_sections.keys())}")
        return deduplicated

    def build_context(self, retrieved_chunks: List[Dict[str, any]]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []

        for i, chunk in enumerate(retrieved_chunks, 1):
            category = chunk['metadata'].get('category', 'Unknown')
            chunk_id = chunk['chunk_id']
            text = chunk['text'][:5000]  # Increased from 3000 to capture more indicators

            context_parts.append(
                f"[Source {i}] Category: {category}, ID: {chunk_id}\n{text}\n"
            )

        return "\n---\n".join(context_parts)

    def generate_answer(
        self,
        question: str,
        retrieved_chunks: List[Dict[str, any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """
        Generate answer using GPT-4 with retrieved context.

        Args:
            question: User's question
            retrieved_chunks: List of retrieved document chunks
            conversation_history: Previous conversation messages (optional)

        Returns:
            Dict with answer, confidence, and formatted sources
        """
        # Classify query type
        query_type = classify_query(question)
        query_modifier = get_system_prompt_modifier(query_type)

        # Build context
        context = self.build_context(retrieved_chunks)

        # For count queries, modify the JSON format instruction
        if query_type == "count":
            json_format_instruction = """
Format your response as valid JSON with the answer field containing PLAIN TEXT ONLY (do NOT wrap in markdown code blocks):
{
  "answer": "There are [X] indicators of compliance:\\n\\n1. First indicator [Source N]\\n\\n2. Second indicator [Source N]\\n\\n3. Third indicator [Source N]",
  "confidence": "low|medium|high",
  "reasoning": "Brief explanation of confidence level"
}

CRITICAL: The "answer" field must be a plain text string with \\n for newlines, NOT a JSON object or array!"""
        else:
            json_format_instruction = """
Format your response as valid JSON (do NOT wrap in markdown code blocks):
{
  "answer": "Your detailed answer with [Source N] citations.",
  "confidence": "low|medium|high",
  "reasoning": "Brief explanation of confidence level"
}"""

        # Create prompt
        system_prompt = f"""You are an expert FTA (Federal Transit Administration) compliance assistant.

Your task is to answer questions based on the provided context from the FTA compliance guide.

Rules:
1. Answer the CURRENT question using ONLY the retrieved sources provided below
2. If previous conversation history is shown, use it ONLY to understand context - do NOT reference previous topics unless the current question explicitly asks about them
3. When the question topic changes (e.g., from ADA to Charter Bus), completely switch focus to the NEW topic based on the retrieved sources
4. Cite specific sources using [Source N] citations in your answer
5. If sources mention the topic but don't have complete details, provide what information IS available and note what's missing
6. Be helpful - extract and synthesize relevant information from the sources even if it's partial
7. Reference specific compliance requirements, regulations, or review areas mentioned in the sources
8. Rate your confidence: "high" if sources directly answer the question, "medium" if sources have relevant but incomplete info, "low" if sources barely mention the topic

IMPORTANT: Each question should be answered independently based on the retrieved sources. Do not carry over topics from previous questions unless explicitly asked.

{query_modifier}

{json_format_instruction}"""

        # Build conversation context if provided
        conversation_context = ""
        if conversation_history and len(conversation_history) > 0:
            # Include last 3 exchanges (6 messages max) for context
            recent_history = conversation_history[-6:]
            conversation_parts = []
            for msg in recent_history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                conversation_parts.append(f"{role.upper()}: {content}")
            conversation_context = f"""Previous conversation (for context only - answer the CURRENT question based on sources below):
{chr(10).join(conversation_parts)}

---

"""

        user_prompt = f"""{conversation_context}Retrieved Sources from FTA Compliance Guide (use THESE to answer the current question):

{context}

---

Question: {question}

Provide your answer as a valid JSON object (raw JSON, no markdown formatting)."""

        # Call LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)

        # Parse JSON response - handle various formats
        content = response.content.strip()

        # Remove markdown code blocks if present
        if content.startswith('```'):
            # Extract content between ```json and ``` or ``` and ```
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
            content = content.replace('```json', '').replace('```', '').strip()

        try:
            result = json.loads(content)
            # Ensure we have the required fields
            if 'answer' not in result:
                result = {
                    "answer": content,
                    "confidence": "low",
                    "reasoning": "Invalid response format"
                }
            # Ensure answer is a string (handle cases where LLM returns structured data)
            elif not isinstance(result['answer'], str):
                # Format structured count/list responses nicely
                answer_data = result['answer']
                if isinstance(answer_data, dict):
                    # Check if it's a count response
                    if 'total_indicators' in answer_data or 'total_indicators_of_compliance' in answer_data:
                        total = answer_data.get('total_indicators') or answer_data.get('total_indicators_of_compliance', 0)
                        details = answer_data.get('details', answer_data.get('indicators', []))

                        # Format as a readable string
                        formatted = f"**Total: {total} indicators found**\n\n"
                        for item in details:
                            source_num = item.get('source', '?')
                            indicator = item.get('indicator', item.get('description', ''))
                            formatted += f"[Source {source_num}] {indicator}\n\n"
                        result['answer'] = formatted.strip()
                    else:
                        # Generic dict formatting
                        result['answer'] = json.dumps(answer_data, indent=2)
                else:
                    # Fallback for other non-string types
                    result['answer'] = str(answer_data)
            # Check if answer string contains JSON-like structure that needs formatting
            elif isinstance(result['answer'], str):
                answer_stripped = result['answer'].strip()
                # Check if it starts with { or [ or contains JSON patterns (various spacing)
                has_json_pattern = (
                    answer_stripped.startswith('{') or
                    answer_stripped.startswith('[') or
                    '"1"' in answer_stripped or
                    '{ "1"' in answer_stripped or
                    answer_stripped.startswith('{"1"')
                )

                print(f"[DEBUG] Answer is string, checking for JSON pattern")
                print(f"[DEBUG] First 100 chars: {answer_stripped[:100]}")
                print(f"[DEBUG] Has JSON pattern: {has_json_pattern}")

                if has_json_pattern:
                    try:
                        # Try to parse the answer as JSON
                        answer_data = json.loads(answer_stripped)
                        print(f"[DEBUG] Successfully parsed JSON")
                        print(f"[DEBUG] Type: {type(answer_data)}")

                        # Handle dict with numbered keys (indicators)
                        if isinstance(answer_data, dict):
                            print(f"[DEBUG] Keys: {list(answer_data.keys())}")

                            # Check for various "Indicators of Compliance" key variations
                            indicators_key = None
                            for key in ["Indicators of Compliance", "indicators_of_compliance", "indicators"]:
                                if key in answer_data:
                                    indicators_key = key
                                    break

                            if indicators_key:
                                indicators = answer_data[indicators_key]
                                if isinstance(indicators, list):
                                    formatted = f"There are {len(indicators)} indicators of compliance:\n\n"
                                    for idx, item in enumerate(indicators, 1):
                                        # Handle dict items with "indicator" key
                                        if isinstance(item, dict) and "indicator" in item:
                                            indicator_text = item["indicator"]
                                        elif isinstance(item, str):
                                            indicator_text = item
                                        else:
                                            indicator_text = str(item)

                                        # Remove letter bullets (a., b., c., etc.) from the beginning
                                        cleaned_item = indicator_text.strip()
                                        if len(cleaned_item) > 2 and cleaned_item[0].isalpha() and cleaned_item[1] == '.':
                                            cleaned_item = cleaned_item[2:].strip()
                                        formatted += f"{idx}. {cleaned_item}\n\n"
                                    result['answer'] = formatted.strip()
                                    print(f"[DEBUG] Formatted {indicators_key} list with {len(indicators)} items")
                                else:
                                    result['answer'] = json.dumps(answer_data, indent=2)
                            else:
                                # Check for numbered indicators pattern
                                numeric_keys = [k for k in answer_data.keys() if k.isdigit()]
                                print(f"[DEBUG] Numeric keys found: {numeric_keys}")
                                if numeric_keys:
                                    # Format as numbered list with count
                                    total = len(numeric_keys)
                                    formatted = f"There are {total} indicators of compliance:\n\n"
                                    for key in sorted(numeric_keys, key=int):
                                        formatted += f"{key}. {answer_data[key]}\n\n"
                                    result['answer'] = formatted.strip()
                                    print(f"[DEBUG] Formatted answer created")
                                else:
                                    # Generic formatting for other dicts
                                    result['answer'] = json.dumps(answer_data, indent=2)

                        # Handle array/list format
                        elif isinstance(answer_data, list):
                            print(f"[DEBUG] Got list with {len(answer_data)} items")
                            # Format list items as numbered list
                            formatted = f"There are {len(answer_data)} indicators of compliance:\n\n"
                            for idx, item in enumerate(answer_data, 1):
                                if isinstance(item, str):
                                    formatted += f"{idx}. {item}\n\n"
                                else:
                                    formatted += f"{idx}. {json.dumps(item)}\n\n"
                            result['answer'] = formatted.strip()
                            print(f"[DEBUG] Formatted list answer created")
                    except (json.JSONDecodeError, ValueError) as e:
                        # Not valid JSON, leave as-is
                        print(f"[DEBUG] JSON parse error: {e}")
                        pass
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails - just use the content as answer
            result = {
                "answer": content,
                "confidence": "low",
                "reasoning": "Failed to parse structured response"
            }

        return result

    def format_sources(self, retrieved_chunks: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Format retrieved chunks as source citations."""
        sources = []

        for chunk in retrieved_chunks:
            metadata = chunk['metadata']
            sources.append({
                'chunk_id': chunk['chunk_id'],
                'category': metadata.get('category', 'Unknown'),
                'excerpt': chunk['text'][:300] + "...",  # First 300 chars
                'score': round(chunk['hybrid_score'], 3),
                'file_path': metadata.get('file_path', ''),
                'page_range': metadata.get('page_range', None),
            })

        return sources

    def process_query(
        self,
        question: str,
        retrieved_chunks: List[Dict[str, any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """
        Full RAG pipeline: generate answer and format response.

        Args:
            question: User's question
            retrieved_chunks: Retrieved document chunks with scores
            conversation_history: Previous conversation messages (optional)

        Returns:
            Formatted response with answer, confidence, and sources
        """
        # Deduplicate chunks for count queries to improve accuracy
        query_type = classify_query(question)
        if query_type == "count":
            print(f"[QUERY] Count query detected, deduplicating chunks...")
            deduplicated_chunks = self.deduplicate_chunks(retrieved_chunks, similarity_threshold=0.85)
        else:
            deduplicated_chunks = retrieved_chunks

        # Generate answer
        llm_result = self.generate_answer(question, deduplicated_chunks, conversation_history)

        # Post-process answer to remove duplicate sections for count queries
        if query_type == "count":
            llm_result['answer'] = self._remove_duplicate_sections(llm_result['answer'])

        # Format sources (use original chunks for source references)
        sources = self.format_sources(retrieved_chunks)

        return {
            'answer': llm_result['answer'],
            'confidence': llm_result['confidence'],
            'sources': sources[:3],  # Top 3 for main citations
            'ranked_chunks': sources,  # All results ranked
        }

    def _remove_duplicate_sections(self, answer: str) -> str:
        """
        Remove duplicate section headers from indicator count responses.

        Args:
            answer: The LLM-generated answer

        Returns:
            Answer with duplicate sections removed
        """
        import re

        lines = answer.split('\n')
        seen_headers = set()
        cleaned_lines = []
        skip_until_next_header = False

        for line in lines:
            # Check if line is a section header (e.g., **TVI6. Does the recipient...)
            header_match = re.match(r'\*\*(TVI\d+(?:-\d+)?)\.\s+(.+?)\*\*', line)

            if header_match:
                section_id = header_match.group(1)
                question_text = header_match.group(2)
                header_key = f"{section_id}:{question_text[:50]}"  # Use first 50 chars to identify

                if header_key in seen_headers:
                    print(f"[POSTPROC] Removing duplicate section: {section_id}")
                    skip_until_next_header = True
                    continue
                else:
                    seen_headers.add(header_key)
                    skip_until_next_header = False
                    cleaned_lines.append(line)
            elif skip_until_next_header:
                # Skip lines under duplicate header until we hit next header
                continue
            else:
                cleaned_lines.append(line)

        # Recalculate total count
        cleaned_answer = '\n'.join(cleaned_lines)

        # Count actual indicators (lines starting with a., b., c., etc.)
        indicator_count = len(re.findall(r'\n[a-z]\.\s+', cleaned_answer))

        # Update the total count in the first line
        cleaned_answer = re.sub(
            r'There are \d+ indicators',
            f'There are {indicator_count} indicators',
            cleaned_answer,
            count=1
        )

        print(f"[POSTPROC] Corrected count to {indicator_count} indicators")

        return cleaned_answer
