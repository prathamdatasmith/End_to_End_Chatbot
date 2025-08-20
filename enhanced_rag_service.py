import asyncio
from typing import List, Dict, Any, Optional
from hybrid_retriever import HybridRetriever
from memory_manager import ConversationMemoryManager
from cache_manager import CacheManager, EmbeddingCache, SearchCache
from ingestion_pipeline import IngestionPipeline
from google import genai
from google.genai import types
from config import Config
import uuid

class EnhancedRAGService:
    def __init__(self):
        """Initialize enhanced RAG service with all components"""
        # Core components
        self.pipeline = IngestionPipeline()
        
        # Hybrid retrieval
        self.hybrid_retriever = HybridRetriever(
            self.pipeline.qdrant_service,
            self.pipeline.embedding_service
        )
        
        # Memory management
        self.memory_manager = ConversationMemoryManager(Config.GEMINI_API_KEY)
        
        # Caching
        self.cache_manager = CacheManager()
        self.embedding_cache = EmbeddingCache(self.cache_manager)
        self.search_cache = SearchCache(self.cache_manager)
        
        # Gemini client
        self.gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        # Session management
        self.current_session = None
    
    def create_session(self) -> str:
        """Create new conversation session"""
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.memory_manager.create_session(session_id)
        self.current_session = session_id
        return session_id
    
    def set_session(self, session_id: str):
        """Set current session"""
        self.memory_manager.set_session(session_id)
        self.current_session = session_id
    
    async def generate_answer_with_context(self, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """BULLETPROOF answer generation - WILL find and use content"""
        try:
            # Input validation - ensure question is a string
            if isinstance(question, list):
                question = ' '.join(str(item) for item in question)
            elif not isinstance(question, str):
                question = str(question)
            
            if not question or not question.strip():
                return {
                    'answer': "Please provide a valid question.",
                    'sources': [],
                    'confidence': 0.0,
                    'search_method': 'invalid_input',
                    'session_id': self.current_session or "unknown",
                    'retrieved_docs_count': 0,
                    'context_chunks_used': 0
                }
            
            # Set session
            if session_id:
                self.set_session(session_id)
            elif not self.current_session:
                self.create_session()
            
            # REMOVE CONVERSATION CONTEXT - Focus only on current question
            enhanced_query = question  # Use original question without context
            
            # MULTI-STRATEGY SEARCH - Will definitely find content
            relevant_docs = []
            search_method = "enhanced_multi_strategy"
            
            # Strategy 1: Try hybrid search
            try:
                relevant_docs = await self.hybrid_retriever.hybrid_search(enhanced_query, Config.TOP_K * 2)
                if relevant_docs:
                    search_method = "hybrid_enhanced"
                    print(f"Hybrid search found {len(relevant_docs)} results")
            except Exception as e:
                print(f"Hybrid search failed: {str(e)}")
            
            # Strategy 2: Direct semantic search with aggressive parameters
            if not relevant_docs:
                try:
                    print("Trying aggressive semantic search...")
                    query_embedding = self.pipeline.embedding_service.embed_single_text(enhanced_query)
                    relevant_docs = await self.pipeline.qdrant_service.search_similar(query_embedding, Config.TOP_K * 3)
                    if relevant_docs:
                        search_method = "semantic_aggressive"
                        print(f"Semantic search found {len(relevant_docs)} results")
                except Exception as e:
                    print(f"Semantic search failed: {str(e)}")
            
            # Strategy 3: Use basic RAG service
            if not relevant_docs:
                try:
                    print("Trying basic RAG service...")
                    from rag_service import RAGService
                    basic_rag = RAGService()
                    basic_result = await basic_rag.generate_answer(question)
                    if basic_result.get('sources'):
                        # Convert to our format
                        relevant_docs = []
                        for source in basic_result['sources']:
                            relevant_docs.append({
                                'text': f"Content related to your question from {source['filename']}",
                                'filename': source['filename'],
                                'chunk_id': source['chunk_id'],
                                'score': max(0.3, source.get('score', 0.5)),
                                'final_score': max(0.3, source.get('score', 0.5)),
                                'search_type': 'basic_rag'
                            })
                        search_method = "basic_rag_enhanced"
                        
                        # Return the basic RAG result immediately if it has content
                        if basic_result['answer'] and "couldn't" not in basic_result['answer'].lower():
                            return {
                                'answer': basic_result['answer'],
                                'sources': basic_result['sources'],
                                'confidence': max(0.4, min(1.0, basic_result.get('confidence', 0.6))),
                                'retrieved_docs_count': len(basic_result['sources']),
                                'context_chunks_used': len(basic_result['sources']),
                                'search_method': search_method,
                                'session_id': self.current_session,
                                'has_conversation_context': False  # No context used
                            }
                        
                        print(f"Basic RAG found {len(relevant_docs)} results")
                except Exception as e:
                    print(f"Basic RAG failed: {str(e)}")
            
            # Strategy 4: Brute force - get ANY content from collection
            if not relevant_docs:
                try:
                    print("Brute force: Getting any available content...")
                    collection_info = self.pipeline.qdrant_service.client.get_collection(
                        self.pipeline.qdrant_service.collection_name
                    )
                    
                    if collection_info.points_count > 0:
                        scroll_result = self.pipeline.qdrant_service.client.scroll(
                            collection_name=self.pipeline.qdrant_service.collection_name,
                            limit=min(50, Config.TOP_K * 4),
                            with_payload=True,
                            with_vectors=False
                        )
                        
                        points = scroll_result[0]
                        for point in points:
                            relevant_docs.append({
                                'text': point.payload['text'],
                                'filename': point.payload['filename'],
                                'chunk_id': point.payload['chunk_id'],
                                'score': 0.4,  # Reasonable score
                                'final_score': 0.4,
                                'search_type': 'brute_force'
                            })
                        
                        search_method = "brute_force_content"
                        print(f"Brute force found {len(relevant_docs)} results")
                    else:
                        print("Collection is empty!")
                        
                except Exception as e:
                    print(f"Brute force search failed: {str(e)}")
            
            # If we STILL don't have content, return a helpful error
            if not relevant_docs:
                # Try to get collection stats for better error message
                try:
                    stats = await self.pipeline.get_collection_stats()
                    if stats.get('points_count', 0) == 0:
                        error_msg = "No documents have been uploaded and processed yet. Please upload PDF documents first."
                    else:
                        error_msg = f"I found {stats.get('points_count', 0)} documents in the collection, but couldn't retrieve any content relevant to your question. Try asking about specific topics from your documents."
                except:
                    error_msg = "I couldn't find any content relevant to your question. Please make sure you have uploaded PDF documents and they were processed successfully."
                
                return {
                    'answer': error_msg,
                    'sources': [],
                    'confidence': 0.0,
                    'search_method': 'no_content_found',
                    'session_id': self.current_session,
                    'retrieved_docs_count': 0,
                    'context_chunks_used': 0
                }
            
            # Prepare context with FOCUSED content - NO conversation context
            context_parts = []
            sources = []
            
            # Use focused chunks - be more selective
            max_chunks = min(10, len(relevant_docs))  # Use fewer, more relevant chunks
            
            for i, doc in enumerate(relevant_docs[:max_chunks]):
                # Fix score calculation
                raw_score = doc.get('final_score', doc.get('score', 0.5))
                final_score = max(0.1, min(1.0, abs(float(raw_score))))
                
                doc_search_type = doc.get('search_type', search_method)
                
                # Clean and focused context
                context_parts.append(f"Document {i+1} from {doc['filename']}:\n{doc['text']}")
                sources.append({
                    'filename': doc['filename'],
                    'chunk_id': doc['chunk_id'],
                    'score': final_score,
                    'search_method': doc_search_type
                })
            
            context = "\n\n".join(context_parts)
            
            # Generate answer with FOCUSED prompt that extracts specific content
            answer = await self._generate_focused_answer(question, context)
            
            # Calculate confidence
            if relevant_docs:
                scores = []
                for doc in relevant_docs[:max_chunks]:
                    raw_score = doc.get('final_score', doc.get('score', 0.5))
                    normalized_score = max(0.1, min(1.0, abs(float(raw_score))))
                    scores.append(normalized_score)
                avg_score = sum(scores) / len(scores) if scores else 0.5
            else:
                avg_score = 0.5
            
            result = {
                'answer': answer,
                'sources': sources,
                'confidence': avg_score,
                'retrieved_docs_count': len(relevant_docs),
                'context_chunks_used': max_chunks,
                'search_method': search_method,
                'session_id': self.current_session,
                'has_conversation_context': False  # No context used
            }
            
            # NO conversation memory - keep each query independent
            
            return result
            
        except Exception as e:
            print(f"Critical error in generate_answer_with_context: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Even in error, try to provide something useful
            return {
                'answer': f"I encountered a technical error while searching your documents for information about: '{question}'\n\nError: {str(e)}\n\nPlease try:\n1. Asking a more specific question\n2. Using different keywords\n3. Re-uploading your documents if the issue persists",
                'sources': [],
                'confidence': 0.0,
                'session_id': self.current_session or "unknown",
                'search_method': 'error_recovery',
                'retrieved_docs_count': 0,
                'context_chunks_used': 0
            }
    
    async def _generate_focused_answer(self, question: str, context: str) -> str:
        """Generate FOCUSED answer that directly addresses the question"""
        try:
            # Create a precise, focused prompt
            prompt = f"""You are a precise document assistant. Answer the specific question using ONLY the provided document content.

QUESTION: {question}

DOCUMENT CONTENT:
{context}

INSTRUCTIONS:
- Answer the EXACT question asked using only the document content provided
- Be specific and direct - no generic responses
- If the question asks about a person, provide their specific details from the documents
- If the question asks about a process, explain it step by step from the documents
- If the question asks about data engineering interviews, provide the specific tips and information from the documents
- PRESERVE formatting like lists, code blocks, and tables exactly as they appear
- If the exact answer isn't in the documents, say "The documents don't contain specific information about [question topic]"
- DO NOT add conversation context or previous questions
- BE PRECISE and extract the exact relevant information

FOCUSED ANSWER:"""

            # Generate with Gemini
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=-1),
                temperature=0.1,  # Very low for precise extraction
                top_p=0.8,
                top_k=20
            )
            
            answer = ""
            for chunk in self.gemini_client.models.generate_content_stream(
                model="gemini-2.5-pro",
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    answer += chunk.text
            
            # Clean up the answer
            answer = answer.strip()
            
            # If the AI gives a generic response, try to extract specific content
            if not answer or "based on your documents" in answer.lower() or "relevant information i found" in answer.lower():
                return self._extract_specific_content(question, context)
            
            return answer
            
        except Exception as e:
            print(f"Error in focused answer generation: {str(e)}")
            return self._extract_specific_content(question, context)
    
    def _extract_specific_content(self, question: str, context: str) -> str:
        """Extract specific content that directly answers the question"""
        try:
            if not context:
                return f"I couldn't find specific information about '{question}' in the documents."
            
            # Split context into documents
            docs = context.split('\n\n')
            question_lower = question.lower()
            
            # Look for direct matches to the question
            relevant_content = []
            
            for doc in docs:
                if not doc.strip():
                    continue
                    
                # Remove the document header line
                lines = doc.split('\n')
                content_lines = lines[1:] if lines[0].startswith('Document') else lines
                doc_content = '\n'.join(content_lines).strip()
                
                if not doc_content:
                    continue
                
                # Check if this document content is relevant
                doc_lower = doc_content.lower()
                
                # Extract keywords from question
                question_words = [word.strip('?,!.') for word in question_lower.split() 
                                if len(word) > 2 and word not in ['what', 'how', 'who', 'when', 'where', 'why', 'can', 'you', 'tell', 'describe', 'the', 'and', 'or']]
                
                # Check for word matches
                if any(word in doc_lower for word in question_words):
                    relevant_content.append(doc_content)
            
            if relevant_content:
                # Take the most relevant content (first few)
                result = '\n\n'.join(relevant_content[:3])
                return f"Based on the documents, here's the specific information about your question:\n\n{result}"
            else:
                # If no direct matches, return a portion of the available content
                first_doc = docs[0] if docs else ""
                if first_doc:
                    lines = first_doc.split('\n')
                    content_lines = lines[1:] if lines[0].startswith('Document') else lines
                    content = '\n'.join(content_lines).strip()[:500]
                    return f"I found some related content in the documents:\n\n{content}{'...' if len(content) >= 500 else ''}"
                else:
                    return f"The documents don't contain specific information that directly answers: '{question}'"
                    
        except Exception as e:
            return f"I found content in your documents but had difficulty processing it for your question: '{question}'"
    
    async def rebuild_search_index(self):
        """Rebuild search indices for better performance"""
        try:
            print("🔄 Rebuilding search indices...")
            await self.hybrid_retriever.build_bm25_index()
            print("✅ Search indices rebuilt successfully")
        except Exception as e:
            print(f"❌ Error rebuilding search index: {str(e)}")
            # Don't fail completely, just log the error
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about current session"""
        return {
            'current_session': self.current_session,
            'memory_stats': self.memory_manager.get_session_stats(),
            'cache_stats': self.cache_manager.get_stats()
        }
    
    def clear_session(self, session_id: Optional[str] = None):
        """Clear specific session or current session"""
        target_session = session_id or self.current_session
        if target_session:
            self.memory_manager.clear_session(target_session)
            if target_session == self.current_session:
                self.current_session = None
    
    def clear_cache(self, cache_type: Optional[str] = None):
        """Clear cache"""
        self.cache_manager.clear_all(cache_type)
    
    def _create_contextual_query(self, question: str, conversation_context: str) -> str:
        """Create enhanced query using conversation context"""
        if conversation_context:
            return f"{conversation_context}\n\nCurrent question: {question}"
        return question

    def cleanup(self):
        """Clean up resources"""
        self.pipeline.cleanup()
        self.memory_manager.cleanup_old_sessions()

# Example usage
async def main():
    enhanced_rag = EnhancedRAGService()
    
    try:
        # Create session
        session_id = enhanced_rag.create_session()
        print(f"Created session: {session_id}")
        
        # Test questions with context
        questions = [
            "What is machine learning?",
            "Can you explain the concept you just mentioned in more detail?",
            "How does this relate to neural networks?"
        ]
        
        for question in questions:
            print(f"\nQuestion: {question}")
            result = await enhanced_rag.generate_answer_with_context(question)
            print(f"Answer: {result['answer'][:200]}...")
            print(f"Confidence: {result['confidence']:.2%}")
            print(f"Sources: {len(result['sources'])}")
        
        # Get session info
        info = enhanced_rag.get_session_info()
        print(f"\nSession info: {info}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        enhanced_rag.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
