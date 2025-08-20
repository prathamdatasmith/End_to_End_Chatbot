from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import asyncio
import json
import uuid
from datetime import datetime

# Import existing services
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

try:
    from enhanced_rag_service import EnhancedRAGService
    from app.models.chat import ChatRequest, ChatResponse, SessionInfo
except ImportError:
    # Temporary placeholder classes for development
    class ChatRequest:
        question: str
        session_id: str
    
    class ChatResponse:
        answer: str
        sources: List[Dict[str, Any]]
        confidence: float
        search_method: str
        session_id: str
        timestamp: datetime
    
    class SessionInfo:
        session_id: str
        current_session: Dict[str, Any]
        memory_stats: Dict[str, Any]
        cache_stats: Dict[str, Any]

router = APIRouter()

# Global instances (in production, use dependency injection)
rag_service = None

def get_rag_service():
    """Get or create RAG service instance"""
    global rag_service
    if rag_service is None:
        try:
            from enhanced_rag_service import EnhancedRAGService
            rag_service = EnhancedRAGService()
        except ImportError:
            # Fallback to a mock service for development
            class MockRAGService:
                def __init__(self):
                    self.sessions = {}
                
                async def generate_answer_with_context(self, question, session_id):
                    return {
                        "answer": f"This is a mock answer to: {question}",
                        "sources": [{"filename": "mock.pdf", "page_number": 1, "text": "Mock text", "relevance": 0.8}],
                        "confidence": 0.7,
                        "search_method": "mock",
                        "session_id": session_id,
                    }
                
                def create_session(self):
                    session_id = str(uuid.uuid4())
                    self.sessions[session_id] = {"created_at": datetime.now().isoformat()}
                    return session_id
                
                def set_session(self, session_id):
                    if session_id not in self.sessions:
                        self.sessions[session_id] = {"created_at": datetime.now().isoformat()}
                    return session_id
                
                def get_session_info(self):
                    return {"current_session": "mock-session", "memory_stats": {}, "cache_stats": {}}
                
                def clear_session(self, session_id):
                    if session_id in self.sessions:
                        self.sessions[session_id] = {"created_at": datetime.now().isoformat()}
                    return True
                
                async def rebuild_search_index(self):
                    return True
            
            rag_service = MockRAGService()
            
    return rag_service

@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    service = Depends(get_rag_service)
) -> ChatResponse:
    """
    Ask a question and get an enhanced response
    """
    try:
        # Generate answer using enhanced RAG service
        result = await service.generate_answer_with_context(
            question=request.question,
            session_id=request.session_id
        )
        
        return ChatResponse(
            answer=result['answer'],
            sources=result['sources'],
            confidence=result.get('confidence', 0.0),
            search_method=result.get('search_method', 'unknown'),
            session_id=result['session_id'],
            retrieved_docs_count=result.get('retrieved_docs_count', 0),
            context_chunks_used=result.get('context_chunks_used', 0),
            has_conversation_context=result.get('has_conversation_context', False),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@router.post("/sessions", response_model=Dict[str, str])
async def create_session(
    service = Depends(get_rag_service)
) -> Dict[str, str]:
    """Create a new chat session"""
    try:
        session_id = service.create_session()
        return {"session_id": session_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session_info(
    session_id: str,
    service = Depends(get_rag_service)
) -> SessionInfo:
    """Get information about a specific session"""
    try:
        service.set_session(session_id)
        info = service.get_session_info()
        
        return SessionInfo(
            session_id=session_id,
            current_session=info.get('current_session'),
            memory_stats=info.get('memory_stats', {}),
            cache_stats=info.get('cache_stats', {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session info: {str(e)}")

@router.delete("/sessions/{session_id}")
async def clear_session(
    session_id: str,
    service = Depends(get_rag_service)
) -> Dict[str, str]:
    """Clear a specific session"""
    try:
        service.clear_session(session_id)
        return {"status": "cleared", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

@router.post("/rebuild-index")
async def rebuild_search_index(
    service = Depends(get_rag_service)
) -> Dict[str, str]:
    """Rebuild the search index for better performance"""
    try:
        await service.rebuild_search_index()
        return {"status": "rebuilt", "message": "Search index rebuilt successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebuilding index: {str(e)}")

# WebSocket endpoint for real-time chat
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.sessions: Dict[str, str] = {}  # websocket_id -> session_id

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

manager = ConnectionManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    service: EnhancedRAGService = Depends(get_rag_service)
):
    await manager.connect(websocket)
    
    try:
        # Set the session
        service.set_session(session_id)
        
        # Send welcome message
        welcome_msg = {
            "type": "connection",
            "message": "Connected to chat session",
            "session_id": session_id
        }
        await manager.send_personal_message(welcome_msg, websocket)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "question":
                question = message_data["content"]
                
                # Send thinking status
                thinking_msg = {
                    "type": "thinking",
                    "message": "Processing your question..."
                }
                await manager.send_personal_message(thinking_msg, websocket)
                
                # Get answer
                result = await service.generate_answer_with_context(question, session_id)
                
                # Send response
                response_msg = {
                    "type": "answer",
                    "content": result['answer'],
                    "sources": result['sources'],
                    "confidence": result['confidence'],
                    "search_method": result.get('search_method', 'unknown'),
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(response_msg, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        error_msg = {
            "type": "error",
            "message": f"Error: {str(e)}"
        }
        await manager.send_personal_message(error_msg, websocket)
        manager.disconnect(websocket)
        await manager.send_personal_message(error_msg, websocket)
        manager.disconnect(websocket)
