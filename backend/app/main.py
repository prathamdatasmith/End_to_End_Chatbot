from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import sys

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our API routes
from app.api import chat, documents, health
# from app.middleware.cors import setup_cors

# Create FastAPI application
app = FastAPI(
    title="RAG Chatbot API",
    description="A sophisticated RAG chatbot with PDF document processing",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed for your use case
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

# Serve static files (if needed)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "message": "RAG Chatbot API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/api/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
