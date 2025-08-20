from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
from typing import Dict, Optional, List
import logging
import tempfile
import asyncio
import time

# Import your existing RAG services
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from enhanced_rag_service import EnhancedRAGService
    from ingestion_pipeline import IngestionPipeline
    from rag_service import RAGService
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"Warning: RAG services not available: {e}")
    RAG_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global services
sessions: Dict[str, dict] = {}
rag_services: Dict[str, EnhancedRAGService] = {}  # One per session
upload_dir = "uploads"
os.makedirs(upload_dir, exist_ok=True)

# Models
class ChatRequest(BaseModel):
    question: str
    session_id: str
    conversation_context: Optional[bool] = True  # ADD: Make this field optional with default

class Source(BaseModel):
    filename: Optional[str] = None
    page_number: Optional[int] = None
    text: Optional[str] = None
    relevance: Optional[float] = None
    score: Optional[float] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []
    confidence: float
    search_method: str

class SessionResponse(BaseModel):
    session_id: str

class DocumentProcessRequest(BaseModel):
    session_id: str

class DocumentStatusResponse(BaseModel):
    processed: bool

def get_or_create_rag_service(session_id: str) -> EnhancedRAGService:
    """Get or create RAG service for session"""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=500, detail="RAG services not available")
    
    if session_id not in rag_services:
        logger.info(f"Creating new RAG service for session {session_id}")
        rag_services[session_id] = EnhancedRAGService()
        # Set the session in the service
        rag_services[session_id].set_session(session_id)
    
    return rag_services[session_id]

@app.get("/")
async def root():
    return {"message": "RAG Chatbot Backend is running", "status": "ok"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "rag_available": RAG_AVAILABLE}

@app.post("/api/chat/session", response_model=SessionResponse)
async def create_session():
    try:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "history": [],
            "files": [],
            "processed": False,
            "upload_complete": False,
            "processing_status": "not_started",
            "created_at": str(uuid.uuid1().time)
        }
        logger.info(f"✅ Created new session: {session_id}")
        return SessionResponse(session_id=session_id)
    except Exception as e:
        logger.error(f"❌ Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.post("/api/documents/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    session_id: str = Form(...)
):
    try:
        logger.info(f"📤 Upload AND process request for session {session_id} with {len(files)} files")
        
        # Validate session
        if session_id not in sessions:
            logger.error(f"Session {session_id} not found")
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Create session folder
        session_folder = os.path.join(upload_dir, session_id)
        os.makedirs(session_folder, exist_ok=True)
        
        # Save and process files in one step
        saved_files = []
        processed_count = 0
        total_chunks = 0
        processing_errors = []
        
        # Verify RAG services
        if not RAG_AVAILABLE:
            logger.error("RAG services not available")
            raise HTTPException(status_code=500, detail="RAG services are not available")
        
        # Get RAG service
        rag_service = get_or_create_rag_service(session_id)
        logger.info(f"🔧 RAG service initialized for session {session_id}")
        
        for i, file in enumerate(files, 1):
            if not file.filename:
                continue
                
            file_path = os.path.join(session_folder, file.filename)
            content = await file.read()
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(content)
            
            saved_files.append({
                "filename": file.filename,
                "path": file_path,
                "size": len(content)
            })
            logger.info(f"💾 Saved file {file.filename} ({len(content)} bytes)")
            
            # Process file immediately
            try:
                logger.info(f"📋 Processing file {i}/{len(files)}: {file.filename}")
                
                if file.filename.lower().endswith('.pdf'):
                    logger.info(f"📄 Step 1: Extracting text from PDF: {file.filename}")
                    result = await rag_service.pipeline.process_pdf_file(file_path)
                elif file.filename.lower().endswith(('.txt', '.doc', '.docx')):
                    logger.info(f"📝 Step 1: Processing text file: {file.filename}")
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text_content = f.read()
                    result = await rag_service.pipeline.process_text(text_content, file.filename)
                else:
                    error_msg = f"Unsupported file type: {file.filename}"
                    logger.warning(f"⚠️ {error_msg}")
                    processing_errors.append(error_msg)
                    continue
                
                if result.get('success', False):
                    processed_count += 1
                    chunks_count = result.get('chunks_count', 0)
                    total_chunks += chunks_count
                    logger.info(f"✅ Step 4: Successfully processed {file.filename}: {chunks_count} chunks created")
                else:
                    error_msg = result.get('error', 'Unknown processing error')
                    logger.error(f"❌ Failed to process {file.filename}: {error_msg}")
                    processing_errors.append(f"{file.filename}: {error_msg}")
                    
            except Exception as e:
                error_msg = f"Exception processing {file.filename}: {str(e)}"
                logger.error(f"💥 {error_msg}")
                processing_errors.append(error_msg)
                continue
        
        # Update session with results
        sessions[session_id]["files"] = saved_files
        sessions[session_id]["upload_complete"] = True
        
        # Check if any files were processed successfully
        if processed_count > 0:
            sessions[session_id]["processed"] = True
            sessions[session_id]["processing_status"] = "completed"
            sessions[session_id]["total_chunks"] = total_chunks
            sessions[session_id]["processed_files"] = processed_count
            
            logger.info(f"🎉 UPLOAD & PROCESSING COMPLETE for session {session_id}:")
            logger.info(f"   📊 Files processed: {processed_count}/{len(files)}")
            logger.info(f"   📚 Total chunks created: {total_chunks}")
            logger.info(f"   ✅ Status: READY FOR CHAT")
            
            return {
                "message": f"Successfully uploaded and processed {processed_count} documents with {total_chunks} chunks",
                "files": [f["filename"] for f in saved_files],
                "session_id": session_id,
                "upload_complete": True,
                "processed": True,
                "success": True,
                "processed_files": processed_count,
                "total_chunks": total_chunks,
                "errors": processing_errors if processing_errors else []
            }
        else:
            sessions[session_id]["processed"] = False
            sessions[session_id]["processing_status"] = "failed"
            
            error_details = "; ".join(processing_errors[:3])
            logger.error(f"❌ No files processed successfully. Errors: {error_details}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to process any documents. Errors: {error_details}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading/processing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload and process documents: {str(e)}")

@app.get("/api/documents/status", response_model=DocumentStatusResponse)
async def get_document_status(session_id: str):
    try:
        logger.info(f"📊 Checking status for session {session_id}")
        
        if session_id not in sessions:
            logger.warning(f"Session {session_id} not found")
            return DocumentStatusResponse(processed=False)
        
        session = sessions[session_id]
        processed = session.get("processed", False)
        processing_status = session.get("processing_status", "not_started")
        
        logger.info(f"📈 Session {session_id} status: processed={processed}, status={processing_status}")
        
        return DocumentStatusResponse(processed=processed)
        
    except Exception as e:
        logger.error(f"❌ Error checking document status: {str(e)}")
        return DocumentStatusResponse(processed=False)

@app.post("/api/chat/question", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id
        question = request.question
        
        logger.info(f"Chat request for session {session_id}: {question[:100]}...")
        
        # Check if session exists
        if session_id not in sessions:
            logger.error(f"Session {session_id} not found")
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        # Check if documents have been processed
        if not session.get("processed", False):
            logger.warning(f"No documents processed for session {session_id}")
            raise HTTPException(
                status_code=400, 
                detail="No documents have been processed for this session. Please upload and process documents first."
            )
        
        # Check if RAG service exists for this session
        if session_id not in rag_services:
            logger.error(f"RAG service not found for session {session_id}")
            raise HTTPException(status_code=500, detail="RAG service not initialized for this session")
        
        rag_service = rag_services[session_id]
        
        # Add user message to history
        session["history"].append({"role": "user", "content": question})
        
        # Generate response using RAG
        try:
            logger.info(f"Generating answer using RAG service for session {session_id}")
            
            # Use the enhanced RAG service method
            response = await rag_service.generate_answer_with_context(question, session_id)
            
            logger.info(f"Generated response with {len(response.get('sources', []))} sources")
            
            # Add assistant response to history
            session["history"].append({"role": "assistant", "content": response['answer']})
            
            # Convert sources to the expected format
            formatted_sources = []
            for source in response.get('sources', []):
                formatted_sources.append(Source(
                    filename=source.get('filename', 'Unknown'),
                    page_number=source.get('page_number'),
                    text=source.get('text', '')[:200] + '...' if source.get('text') else None,
                    relevance=source.get('relevance', source.get('score', 0.0)),
                    score=source.get('score', source.get('relevance', 0.0))
                ))
            
            return ChatResponse(
                answer=response['answer'],
                sources=formatted_sources,
                confidence=response.get('confidence', 0.0),
                search_method=response.get('search_method', 'enhanced_rag')
            )
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            
            # Enhanced fallback response with troubleshooting info
            session_info = f"Session has {session.get('total_chunks', 0)} chunks from {session.get('processed_files', 0)} files"
            fallback_answer = f"""I apologize, but I encountered an error while processing your question. 

**Error Details:** {str(e)}
**Session Info:** {session_info}

**Troubleshooting Steps:**
1. Try rephrasing your question
2. Check if documents were properly processed
3. Try uploading documents again if the issue persists

Please try asking your question again or contact support if the problem continues."""
            
            session["history"].append({"role": "assistant", "content": fallback_answer})
            
            return ChatResponse(
                answer=fallback_answer,
                sources=[],
                confidence=0.0,
                search_method="error_fallback"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Critical error processing chat question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing your question: {str(e)}")

# Alternative endpoint for compatibility - UPDATE: Use same endpoint as frontend expects
@app.post("/api/chat/ask", response_model=ChatResponse)
async def chat_ask(request: ChatRequest):
    return await chat_question_handler(request)

# ADD: Create a unified handler
async def chat_question_handler(request: ChatRequest):
    start_time = time.time()
    try:
        session_id = request.session_id
        question = request.question
        conversation_context = getattr(request, 'conversation_context', True)  # Handle optional field
        
        logger.info(f"🚀 Chat request for session {session_id}: {question[:100]}... (context: {conversation_context})")
        
        # Validate request
        if not question or not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        if len(question.strip()) > 4000:
            raise HTTPException(status_code=400, detail="Question too long. Please keep it under 4000 characters.")
        
        # Check if session exists
        if session_id not in sessions:
            logger.error(f"❌ Session {session_id} not found")
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        # Check if documents have been processed
        if not session.get("processed", False):
            logger.warning(f"⚠️ No documents processed for session {session_id}")
            raise HTTPException(
                status_code=400, 
                detail="No documents have been processed for this session. Please upload and process documents first."
            )
        
        # Get or create RAG service
        if session_id not in rag_services:
            logger.error(f"❌ RAG service not found for session {session_id}")
            try:
                rag_service = get_or_create_rag_service(session_id)
                logger.info(f"🔧 Recreated RAG service for session {session_id}")
            except Exception as e:
                logger.error(f"💥 Failed to recreate RAG service: {str(e)}")
                raise HTTPException(status_code=500, detail="RAG service not available. Please restart the session.")
        else:
            rag_service = rag_services[session_id]
        
        # Add user message to history if conversation context is enabled
        # DISABLE conversation context by default
        conversation_context = False  # Force disable conversation context
        
        if conversation_context:
            session["history"].append({"role": "user", "content": question})
        
        # Generate response with timeout protection
        try:
            logger.info(f"🧠 Generating answer using RAG service for session {session_id}")
            
            # Add timeout wrapper for the RAG generation
            async def generate_with_timeout():
                return await rag_service.generate_answer_with_context(question, session_id)
            
            # Set reasonable timeout for RAG processing
            response = await asyncio.wait_for(generate_with_timeout(), timeout=45.0)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Generated response in {processing_time:.2f}s with confidence {response.get('confidence', 0)}")
            
            # Validate response structure
            if not response or 'answer' not in response:
                logger.error(f"❌ Invalid response structure from RAG service")
                raise Exception("Invalid response from RAG service")
            
            # Add assistant response to history if conversation context is enabled
            if conversation_context:
                session["history"].append({"role": "assistant", "content": response['answer']})
            
            # Convert sources to expected format
            formatted_sources = []
            for source in response.get('sources', []):
                formatted_sources.append(Source(
                    filename=source.get('filename', 'Unknown'),
                    page_number=source.get('page_number'),
                    text=source.get('text', '')[:200] + '...' if source.get('text') else None,
                    relevance=source.get('relevance', source.get('score', 0.0)),
                    score=source.get('score', source.get('relevance', 0.0))
                ))
            
            return ChatResponse(
                answer=response['answer'],
                sources=formatted_sources,
                confidence=response.get('confidence', 0.8),
                search_method=response.get('search_method', 'enhanced_rag')
            )
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ RAG generation timeout after 45 seconds for session {session_id}")
            
            timeout_answer = f"""⏰ **Request Timeout**

Your question took too long to process (over 45 seconds). This can happen with:
- Very complex questions
- System overload
- Large document collections

**Your question:** "{question[:100]}{'...' if len(question) > 100 else ''}"

**Try:**
1. Ask a simpler, more specific question
2. Wait a moment and try again
3. Break complex questions into parts

I'm ready to help with your next question!"""
            
            if conversation_context:
                session["history"].append({"role": "assistant", "content": timeout_answer})
            
            return ChatResponse(
                answer=timeout_answer,
                sources=[],
                confidence=0.0,
                search_method="timeout"
            )
            
        except Exception as e:
            logger.error(f"💥 Error generating RAG response: {str(e)}")
            
            # Enhanced error response
            session_info = f"Session has {session.get('total_chunks', 0)} chunks from {session.get('processed_files', 0)} files"
            processing_time = time.time() - start_time
            
            error_answer = f"""🚨 **Processing Error**

I encountered an error while processing your question after {processing_time:.1f} seconds.

**Error:** {str(e)[:150]}{'...' if len(str(e)) > 150 else ''}
**Session:** {session_info}

**Quick fixes:**
1. Try rephrasing your question
2. Wait 10 seconds and try again
3. Check if your question is too complex

**If this persists:**
- Check backend logs for Gemini API errors
- Verify Qdrant connection
- Restart the session if needed

Please try a different question!"""
            
            if conversation_context:
                session["history"].append({"role": "assistant", "content": error_answer})
            
            return ChatResponse(
                answer=error_answer,
                sources=[],
                confidence=0.0,
                search_method="error"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"💥 Critical error after {processing_time:.1f}s: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Critical system error: {str(e)}")

@app.delete("/api/chat/session/{session_id}")
async def delete_session(session_id: str):
    try:
        # Clean up session data
        if session_id in sessions:
            del sessions[session_id]
        
        # Clean up RAG service
        if session_id in rag_services:
            # Clean up the RAG service resources
            try:
                rag_services[session_id].clear_session(session_id)
            except:
                pass
            del rag_services[session_id]
        
        # Clean up files
        session_folder = os.path.join(upload_dir, session_id)
        if os.path.exists(session_folder):
            import shutil
            shutil.rmtree(session_folder)
        
        return {"message": "Session deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete session")

if __name__ == "__main__":
    import uvicorn
    print("Starting RAG Chatbot Backend...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
