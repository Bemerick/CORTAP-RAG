"""API route handlers."""
from fastapi import APIRouter, HTTPException, Depends
from models import QueryRequest, QueryResponse, CommonQuestion, HealthResponse
from typing import List
from config import settings

router = APIRouter(prefix="/api/v1")


def get_rag_service():
    """Dependency injection for RAG service."""
    from api.service import RAGService
    return RAGService()


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest,
    rag_service: "RAGService" = Depends(get_rag_service)
):
    """
    Main Q&A endpoint.

    Args:
        request: Query request with question and optional recipient_type

    Returns:
        Answer with confidence score and source citations
    """
    try:
        response = rag_service.process_query(
            question=request.question,
            recipient_type=request.recipient_type
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.get("/common-questions", response_model=List[CommonQuestion])
async def get_common_questions():
    """
    Get list of suggested common questions.

    Returns:
        List of common questions with categories
    """
    return [CommonQuestion(**q) for q in settings.common_questions]


@router.get("/health", response_model=HealthResponse)
async def health_check(rag_service: "RAGService" = Depends(get_rag_service)):
    """
    Health check endpoint.

    Returns:
        Service status and database readiness
    """
    try:
        db_ready = rag_service.check_database_ready()
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            database_ready=db_ready
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            database_ready=False
        )
