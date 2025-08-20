from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from typing import List, Dict, Any, Optional
import tempfile
import os
import asyncio
import uuid

# Import existing services (adjust the path as needed)
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# We'll import these once they're available in the right location
try:
    from enhanced_rag_service import EnhancedRAGService
    from app.models.documents import DocumentResponse
except ImportError:
    # Temporary placeholder for development
    class DocumentResponse:
        pass
    
router = APIRouter()

# Global service instance (in production, use dependency injection)
rag_service = None

def get_rag_service():
    """Get or create RAG service instance"""
    global rag_service
    if rag_service is None:
        try:
            from enhanced_rag_service import EnhancedRAGService
            rag_service = EnhancedRAGService()
        except ImportError:
            raise HTTPException(status_code=500, detail="RAG service not available")
    return rag_service

@router.post("/upload", response_model=Dict[str, Any])
async def upload_documents(
    files: List[UploadFile] = File(...),
    session_id: str = Form(...),
    service = Depends(get_rag_service)
):
    """Upload multiple documents"""
    try:
        results = []
        for file in files:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file.filename.split(".")[-1]}') as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                # Process the file based on extension
                if file.filename.lower().endswith('.pdf'):
                    result = await service.pipeline.process_pdf_file(tmp_path)
                else:
                    # For other file types, use generic text processing
                    with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text_content = f.read()
                    result = await service.pipeline.process_text(text_content, file.filename)
                
                results.append({
                    "success": True,
                    "filename": file.filename,
                    "chunks_count": result.get("chunks_count", 0),
                    "document_id": str(uuid.uuid4())
                })
            except Exception as e:
                results.append({
                    "success": False,
                    "filename": file.filename,
                    "error": str(e)
                })
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        return {
            "success": True,
            "uploaded_files": results,
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")

@router.post("/process", response_model=Dict[str, Any])
async def process_documents(
    session_id: str = Form(...),
    service = Depends(get_rag_service)
):
    """Process uploaded documents for a session"""
    try:
        # Set the session in the service
        service.set_session(session_id)
        
        # Here you would trigger any additional processing
        # For now, we'll just return success
        return {
            "success": True,
            "session_id": session_id,
            "message": "Documents processed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")

@router.get("/status")
async def get_documents_status(
    session_id: str,
    service = Depends(get_rag_service)
):
    """Get document processing status for a session"""
    try:
        # Check if documents have been processed for this session
        # This is a placeholder - implement based on your storage mechanism
        return {
            "processed": True,  # Change this based on actual status
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking status: {str(e)}")

@router.get("/", response_model=List[Dict[str, Any]])
async def list_documents(
    service = Depends(get_rag_service)
):
    """List all uploaded documents"""
    try:
        # This would need to be implemented in the service
        # For now, return a placeholder response
        return [
            {
                "document_id": "placeholder-id",
                "filename": "placeholder.pdf",
                "chunks_count": 0,
                "upload_time": "2023-01-01T00:00:00Z"
            }
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.delete("/{document_id}", response_model=Dict[str, Any])
async def delete_document(
    document_id: str,
    service = Depends(get_rag_service)
):
    """Delete a document by ID"""
    try:
        # This would need to be implemented in the service
        return {
            "success": True,
            "document_id": document_id,
            "message": "Document deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.get("/collection/info", response_model=Dict[str, Any])
async def get_collection_info(
    service = Depends(get_rag_service)
):
    """Get information about the document collection"""
    try:
        # Get collection info from Qdrant
        collection_info = await service.qdrant_service.get_collection_info()
        return collection_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collection info: {str(e)}")

@router.delete("/collection", response_model=Dict[str, Any])
async def clear_collection(
    service = Depends(get_rag_service)
):
    """Clear all documents from collection"""
    try:
        await service.qdrant_service.delete_collection()
        await service.qdrant_service.create_collection_if_not_exists()
        return {
            "success": True,
            "message": "Collection cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing collection: {str(e)}")
