from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    """Response model for document operations"""
    document_id: str
    filename: str
    chunks_count: int
    upload_time: datetime = Field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None

class DocumentListResponse(BaseModel):
    """Response model for listing documents"""
    documents: List[DocumentResponse] = []
    total_count: int = 0
    total_chunks: int = 0

class CollectionInfo(BaseModel):
    """Collection information model"""
    vectors_count: int = 0
    points_count: int = 0
    status: str = "unknown"
    error: Optional[str] = None
