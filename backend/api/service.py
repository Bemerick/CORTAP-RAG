"""RAG service for handling query processing."""
from typing import Dict, Optional
import os
from ingestion import EmbeddingManager
from retrieval import HybridRetriever, RAGPipeline
from retrieval.query_classifier import classify_query, get_retrieval_params
from retrieval.hybrid_engine import HybridQueryEngine
from database.connection import get_db_manager
from config import settings


class RAGService:
    """Service layer for RAG operations."""

    _instance = None
    _initialized = False

    def __new__(cls):
        """Singleton pattern to reuse connections."""
        if cls._instance is None:
            cls._instance = super(RAGService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize RAG service components."""
        if not self._initialized:
            self._initialize_components()
            RAGService._initialized = True

    def _initialize_components(self):
        """Initialize embedding manager, retriever, and RAG pipeline."""
        # Initialize embedding manager (connects to ChromaDB)
        self.embedding_manager = EmbeddingManager(
            db_path=settings.chroma_db_path,
            openai_api_key=settings.openai_api_key,
            embedding_model=settings.embedding_model
        )

        # Initialize hybrid retriever
        self.hybrid_retriever = HybridRetriever(
            semantic_weight=settings.semantic_weight,
            keyword_weight=settings.keyword_weight
        )

        # Build BM25 index from all documents in ChromaDB
        self._build_bm25_index()

        # Initialize RAG pipeline
        self.rag_pipeline = RAGPipeline(
            openai_api_key=settings.openai_api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature
        )

        # Initialize database manager (for structured queries)
        db_url = settings.database_url
        if db_url:
            self.db_manager = get_db_manager(db_url)
            # Initialize hybrid query engine
            self.hybrid_engine = HybridQueryEngine(
                db_manager=self.db_manager,
                rag_pipeline=self.rag_pipeline,
                hybrid_retriever=self.hybrid_retriever,
                embedding_manager=self.embedding_manager
            )
            print("[RAG SERVICE] Hybrid query engine initialized with database support")
        else:
            self.db_manager = None
            self.hybrid_engine = None
            print("[RAG SERVICE] No DATABASE_URL found, running in RAG-only mode")

    def _build_bm25_index(self):
        """Build BM25 index from all documents in ChromaDB."""
        # Get all documents from collection
        all_docs = self.embedding_manager.collection.get()

        if all_docs and all_docs['ids']:
            documents = all_docs['documents']
            doc_ids = all_docs['ids']

            self.hybrid_retriever.build_bm25_index(documents, doc_ids)
            print(f"BM25 index built with {len(documents)} documents")
        else:
            print("Warning: No documents in ChromaDB. BM25 index not built.")

    def check_database_ready(self) -> bool:
        """Check if database is ready with documents."""
        count = self.embedding_manager.get_collection_count()
        return count > 0

    def process_query(
        self,
        question: str,
        recipient_type: Optional[str] = None,
        conversation_history: Optional[list] = None
    ) -> Dict[str, any]:
        """
        Process a user query through the hybrid query engine or RAG pipeline.

        Args:
            question: User's question
            recipient_type: Optional recipient type for filtering
            conversation_history: Previous conversation messages (optional)

        Returns:
            Query response with answer, confidence, sources, and backend type
        """
        # Use hybrid engine if available (database + RAG routing)
        if self.hybrid_engine:
            print("[RAG SERVICE] Using hybrid query engine")
            response = self.hybrid_engine.execute_query(
                question=question,
                conversation_history=conversation_history
            )
            return response

        # Fallback to pure RAG pipeline (no database)
        print("[RAG SERVICE] Using pure RAG pipeline (no database)")

        # Step 0: Classify query and get retrieval parameters
        query_type = classify_query(question)
        retrieval_params = get_retrieval_params(query_type)
        top_k = retrieval_params["top_k"]

        print(f"Query type: {query_type}, retrieving top {top_k} chunks")

        # Step 1: Semantic retrieval from ChromaDB
        filter_metadata = None
        if recipient_type:
            # Future: implement metadata filtering by recipient_type
            pass

        semantic_results = self.embedding_manager.query_collection(
            query_text=question,
            n_results=top_k,
            filter_metadata=filter_metadata
        )

        # Step 2: Hybrid search (merge semantic + BM25)
        retrieved_chunks = self.hybrid_retriever.merge_results(
            semantic_results=semantic_results,
            query=question,
            top_k=top_k
        )

        if not retrieved_chunks:
            return {
                'answer': "I couldn't find relevant information in the FTA compliance guide to answer your question.",
                'confidence': 'low',
                'sources': [],
                'ranked_chunks': [],
                'backend': 'rag',
                'metadata': {}
            }

        # Step 3: Generate answer with RAG pipeline
        response = self.rag_pipeline.process_query(
            question=question,
            retrieved_chunks=retrieved_chunks,
            conversation_history=conversation_history
        )

        # Add backend type for consistency
        response['backend'] = 'rag'
        response['metadata'] = response.get('metadata', {})

        return response
