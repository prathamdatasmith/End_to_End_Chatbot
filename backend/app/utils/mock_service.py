import uuid
from datetime import datetime
from typing import Dict, List, Any

class MockRAGService:
    def __init__(self):
        self.sessions = {}
    
    async def generate_answer_with_context(self, question: str, session_id: str) -> Dict[str, Any]:
        """Generate a mock answer for testing purposes"""
        if not session_id or session_id not in self.sessions:
            session_id = self.create_session()
        
        return {
            "answer": f"This is a mock answer to: {question}. The actual enhanced_rag_service module may not be available.",
            "sources": [
                {
                    "filename": "example.pdf", 
                    "page_number": 1, 
                    "text": "This is mock text content from a document.", 
                    "relevance": 0.85
                }
            ],
            "confidence": 0.75,
            "search_method": "mock_semantic",
            "session_id": session_id,
            "retrieved_docs_count": 1,
            "context_chunks_used": 1,
            "has_conversation_context": False
        }
    
    def create_session(self) -> str:
        """Create a new mock session"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
        return session_id
    
    def set_session(self, session_id: str) -> bool:
        """Set the current session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.now().isoformat(),
                "messages": []
            }
        return True
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get mock session info"""
        return {
            "current_session": "mock-session",
            "memory_stats": {"used": "10 MB", "total": "100 MB"},
            "cache_stats": {"hits": 5, "misses": 2}
        }
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a mock session"""
        if session_id in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.now().isoformat(),
                "messages": []
            }
        return True
    
    async def rebuild_search_index(self) -> bool:
        """Mock rebuilding the search index"""
        return True
    
    async def pipeline(self):
        """Mock pipeline for document processing"""
        class MockPipeline:
            async def process_pdf_file(self, file_path: str) -> Dict[str, Any]:
                return {
                    "success": True,
                    "chunks_count": 10,
                    "filename": file_path.split("/")[-1]
                }
        
        return MockPipeline()
