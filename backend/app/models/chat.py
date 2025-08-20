from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class ChatRequest(BaseModel):
    """Request model for chat interactions"""
    question: str = Field(..., description="The user's question")
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Chat session identifier")
    conversation_context: bool = Field(default=True, description="Whether to use conversation context")

class Source(BaseModel):
    """Source information for an answer"""
    filename: Optional[str] = None
    page_number: Optional[int] = None
    text: Optional[str] = None
    relevance: Optional[float] = None
    search_method: Optional[str] = None

class ChatResponse(BaseModel):
    """Response model for chat interactions"""
    answer: str
    sources: List[Source] = []
    confidence: float = 0.0
    search_method: str = "unknown"
    session_id: str
    retrieved_docs_count: Optional[int] = 0
    context_chunks_used: Optional[int] = 0
    has_conversation_context: Optional[bool] = False
    timestamp: datetime = Field(default_factory=datetime.now)

class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    current_session: Optional[Any] = None
    memory_stats: Dict[str, Any] = {}
    cache_stats: Dict[str, Any] = {}
    sources: List[Source] = Field(default_factory=list, description="Source documents used")
    confidence: float = Field(..., description="Confidence score", ge=0.0, le=1.0)
    search_method: str = Field(..., description="Search method used")
    session_id: str = Field(..., description="Session ID")
    retrieved_docs_count: int = Field(default=0, description="Number of documents retrieved")
    context_chunks_used: int = Field(default=0, description="Number of context chunks used")
    has_conversation_context: bool = Field(default=False, description="Whether conversation context was used")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "answer": "Machine learning is a subset of artificial intelligence...",
                "sources": [
                    {
                        "filename": "ml_textbook.pdf",
                        "chunk_id": "chunk_003",
                        "score": 0.92,
                        "search_method": "semantic"
                    }
                ],
                "confidence": 0.89,
                "search_method": "hybrid",
                "session_id": "session_12345",
                "retrieved_docs_count": 15,
                "context_chunks_used": 5,
                "has_conversation_context": True,
                "timestamp": "2024-01-15T10:30:00"
            }
        }

class SessionInfo(BaseModel):
    """Model for session information"""
    session_id: str = Field(..., description="Session ID")
    current_session: Optional[str] = Field(None, description="Current active session")
    memory_stats: Dict[str, Any] = Field(default_factory=dict, description="Memory statistics")
    cache_stats: Dict[str, Any] = Field(default_factory=dict, description="Cache statistics")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session_12345",
                "current_session": "session_12345",
                "memory_stats": {
                    "total_sessions": 3,
                    "message_count": 10
                },
                "cache_stats": {
                    "total_entries": 25,
                    "total_size_mb": 15.2
                }
            }
        }

class StreamChunk(BaseModel):
    """Model for streaming response chunks"""
    type: str = Field(..., description="Type of chunk: 'text_chunk', 'metadata', 'error'")
    content: Optional[str] = Field(None, description="Text content (for text_chunk type)")
    sources: Optional[List[Source]] = Field(None, description="Sources (for metadata type)")
    confidence: Optional[float] = Field(None, description="Confidence (for metadata type)")
    search_method: Optional[str] = Field(None, description="Search method (for metadata type)")
    session_id: Optional[str] = Field(None, description="Session ID (for metadata type)")
    message: Optional[str] = Field(None, description="Error message (for error type)")
    is_final: bool = Field(default=False, description="Whether this is the final chunk")
