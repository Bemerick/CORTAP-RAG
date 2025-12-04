"""RAG pipeline for query processing and answer generation."""
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import json


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

    def build_context(self, retrieved_chunks: List[Dict[str, any]]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []

        for i, chunk in enumerate(retrieved_chunks, 1):
            category = chunk['metadata'].get('category', 'Unknown')
            chunk_id = chunk['chunk_id']
            text = chunk['text'][:3000]  # Limit chunk size for context

            context_parts.append(
                f"[Source {i}] Category: {category}, ID: {chunk_id}\n{text}\n"
            )

        return "\n---\n".join(context_parts)

    def generate_answer(
        self,
        question: str,
        retrieved_chunks: List[Dict[str, any]]
    ) -> Dict[str, any]:
        """
        Generate answer using GPT-4 with retrieved context.

        Args:
            question: User's question
            retrieved_chunks: List of retrieved document chunks

        Returns:
            Dict with answer, confidence, and formatted sources
        """
        # Build context
        context = self.build_context(retrieved_chunks)

        # Create prompt
        system_prompt = """You are an expert FTA (Federal Transit Administration) compliance assistant.

Your task is to answer questions based on the provided context from the FTA compliance guide.

Rules:
1. Use ONLY information from the provided sources
2. Cite specific sources using [Source N] notation in your answer
3. If sources mention the topic but don't have complete details, provide what information IS available and note what's missing
4. Be helpful - extract and synthesize relevant information from the sources even if it's partial
5. Reference specific compliance requirements, regulations, or review areas mentioned in the sources
6. Rate your confidence: "high" if sources directly answer the question, "medium" if sources have relevant but incomplete info, "low" if sources barely mention the topic

Format your response as valid JSON (do NOT wrap in markdown code blocks):
{
  "answer": "Your detailed answer with [Source N] citations. Include all relevant information found in the sources.",
  "confidence": "low|medium|high",
  "reasoning": "Brief explanation of confidence level"
}"""

        user_prompt = f"""Context from FTA Compliance Guide:

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
        retrieved_chunks: List[Dict[str, any]]
    ) -> Dict[str, any]:
        """
        Full RAG pipeline: generate answer and format response.

        Args:
            question: User's question
            retrieved_chunks: Retrieved document chunks with scores

        Returns:
            Formatted response with answer, confidence, and sources
        """
        # Generate answer
        llm_result = self.generate_answer(question, retrieved_chunks)

        # Format sources
        sources = self.format_sources(retrieved_chunks)

        return {
            'answer': llm_result['answer'],
            'confidence': llm_result['confidence'],
            'sources': sources[:3],  # Top 3 for main citations
            'ranked_chunks': sources,  # All results ranked
        }
