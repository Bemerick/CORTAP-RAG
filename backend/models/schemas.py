"""Pydantic models for request/response validation."""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """Single message in conversation history."""
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")


class QueryRequest(BaseModel):
    """Request model for Q&A queries."""
    question: str = Field(..., min_length=1, description="Natural language question")
    recipient_type: Optional[str] = Field(None, description="Optional recipient type filter")
    conversation_history: List[ConversationMessage] = Field(default=[], description="Previous conversation messages")


class SourceCitation(BaseModel):
    """Source citation with metadata."""
    chunk_id: str
    category: str
    excerpt: str
    score: float
    file_path: str
    page_range: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for Q&A queries."""
    answer: str
    confidence: str = Field(..., description="low, medium, or high")
    sources: List[SourceCitation]
    ranked_chunks: List[SourceCitation]


class CommonQuestion(BaseModel):
    """Common question suggestion."""
    question: str
    category: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database_ready: bool
