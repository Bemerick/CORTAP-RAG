"""Hybrid search combining semantic and keyword-based retrieval."""
from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi


class HybridRetriever:
    """Combines semantic (vector) and keyword (BM25) search."""

    def __init__(self, semantic_weight: float = 0.7, keyword_weight: float = 0.3):
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.bm25_index = None
        self.documents = []
        self.document_ids = []

    def build_bm25_index(self, documents: List[str], document_ids: List[str]):
        """
        Build BM25 index for keyword search.

        Args:
            documents: List of document texts
            document_ids: Corresponding document IDs
        """
        self.documents = documents
        self.document_ids = document_ids

        # Tokenize documents (simple whitespace tokenization)
        tokenized_docs = [doc.lower().split() for doc in documents]
        self.bm25_index = BM25Okapi(tokenized_docs)

    def get_bm25_scores(self, query: str) -> Dict[str, float]:
        """
        Get BM25 scores for all documents.

        Args:
            query: Query string

        Returns:
            Dictionary mapping document_id to BM25 score
        """
        if not self.bm25_index:
            return {}

        tokenized_query = query.lower().split()
        scores = self.bm25_index.get_scores(tokenized_query)

        # Normalize scores to 0-1 range
        max_score = max(scores) if max(scores) > 0 else 1.0
        normalized_scores = [score / max_score for score in scores]

        return dict(zip(self.document_ids, normalized_scores))

    def merge_results(
        self,
        semantic_results: Dict[str, any],
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, any]]:
        """
        Merge semantic and BM25 results with hybrid scoring.

        Args:
            semantic_results: Results from ChromaDB query
            query: Original query string
            top_k: Number of top results to return

        Returns:
            List of documents with hybrid scores, sorted by relevance
        """
        # Get BM25 scores
        bm25_scores = self.get_bm25_scores(query)

        # Parse semantic results
        merged_results = []
        for i in range(len(semantic_results['ids'][0])):
            doc_id = semantic_results['ids'][0][i]
            semantic_score = 1 - semantic_results['distances'][0][i]  # Convert distance to similarity
            document_text = semantic_results['documents'][0][i]
            metadata = semantic_results['metadatas'][0][i]

            # Get BM25 score for this document
            bm25_score = bm25_scores.get(doc_id, 0.0)

            # Calculate hybrid score
            hybrid_score = (
                self.semantic_weight * semantic_score +
                self.keyword_weight * bm25_score
            )

            merged_results.append({
                'chunk_id': doc_id,
                'text': document_text,
                'metadata': metadata,
                'semantic_score': semantic_score,
                'bm25_score': bm25_score,
                'hybrid_score': hybrid_score,
            })

        # Sort by hybrid score
        merged_results.sort(key=lambda x: x['hybrid_score'], reverse=True)

        return merged_results[:top_k]
