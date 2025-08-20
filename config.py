import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "chatbot_docs")
    
    # FastEmbed settings
    EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
    VECTOR_SIZE = 384  # This model produces 384-dimensional vectors
    
    # Chunking settings for formatted content
    CHUNK_SIZE = 2000  # Smaller chunks to preserve formatting
    CHUNK_OVERLAP = 400  # Overlap for context
    
    # Retrieval settings - ENHANCED for large documents
    TOP_K = 20               # Reduce to get more focused results
    SCORE_THRESHOLD = 0.3    # Add threshold to filter poor matches
    MAX_CONTEXT_CHUNKS = 10  # Reduce context to avoid noise
    
    # Gemini API settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Enhanced settings for large documents
    # Hybrid Retrieval Settings
    BM25_TOP_K = 15              # Reduce for more focused results
    SEMANTIC_TOP_K = 15          # Reduce for more focused results
    RERANK_TOP_K = 10            # Reduce for better precision

    # Score fusion weights
    SEMANTIC_WEIGHT = 0.7         # Weight for semantic search scores
    KEYWORD_WEIGHT = 0.3          # Weight for keyword search scores
    RERANK_WEIGHT = 0.6           # Weight for reranking scores

    # Memory settings
    MAX_CONVERSATION_MEMORY = 2000  # Max tokens in conversation memory
    CONVERSATION_SUMMARY_THRESHOLD = 1500  # When to start summarizing

    # Cache settings
    CACHE_EXPIRE_HOURS = 24       # Default cache expiration
    EMBEDDING_CACHE_HOURS = 168   # Embedding cache expiration (1 week)
    SEARCH_CACHE_HOURS = 6        # Search results cache expiration
    MAX_CACHE_SIZE_MB = 500       # Maximum cache size in MB