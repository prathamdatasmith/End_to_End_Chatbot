import asyncio
from typing import List, Dict, Any, Optional
import numpy as np
from embedding_service import EmbeddingService
from qdrant_service import QdrantService
from config import Config
import re

class HybridRetriever:
    def __init__(self, qdrant_service: QdrantService, embedding_service: EmbeddingService):
        """Initialize hybrid retriever with semantic and keyword search"""
        self.qdrant_service = qdrant_service
        self.embedding_service = embedding_service
        
        # Initialize reranker model with better error handling
        self.reranker = None
        try:
            from sentence_transformers import CrossEncoder
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            print("✅ Reranker model loaded successfully")
        except ImportError:
            print("⚠️  Warning: sentence-transformers not installed, skipping reranker")
        except Exception as e:
            print(f"⚠️  Warning: Could not load reranker model: {str(e)}")
        
        # BM25 initialization with better error handling
        self.bm25 = None
        self.bm25_available = False
        try:
            from rank_bm25 import BM25Okapi
            self.bm25_available = True
            print("✅ BM25 library available")
        except ImportError:
            print("⚠️  Warning: rank-bm25 not installed, using semantic search only")
        
        self.documents_corpus = []
        self.documents_metadata = []
        
    async def build_bm25_index(self):
        """Build BM25 index from all documents in collection"""
        try:
            print("Building BM25 index...")
            # Import BM25Okapi here to ensure it's defined
            from rank_bm25 import BM25Okapi
            # Get all documents from Qdrant - FIXED: removed await from non-async method
            all_docs = self._get_all_documents_sync()
            
            if not all_docs:
                print("No documents found for BM25 indexing")
                return
            
            # Prepare corpus for BM25
            self.documents_corpus = []
            self.documents_metadata = []
            
            for doc in all_docs:
                # Tokenize text for BM25
                tokenized_text = self._tokenize_text(doc['text'])
                self.documents_corpus.append(tokenized_text)
                self.documents_metadata.append({
                    'text': doc['text'],
                    'filename': doc['filename'],
                    'chunk_id': doc['chunk_id'],
                    'doc_id': doc.get('doc_id', '')
                })
            
            # Build BM25 index
            self.bm25 = BM25Okapi(self.documents_corpus)
            print(f"✅ Built BM25 index with {len(self.documents_corpus)} documents")
            
        except Exception as e:
            print(f"❌ Error building BM25 index: {str(e)}")
    
    def _get_all_documents_sync(self) -> List[Dict[str, Any]]:
        """Get all documents from Qdrant collection - SYNCHRONOUS"""
        try:
            # Use scroll method to get all documents
            documents = []
            
            # Get collection info first
            collection_info = self.qdrant_service.client.get_collection(
                self.qdrant_service.collection_name
            )
            
            if collection_info.points_count == 0:
                return []
            
            # Scroll through all points
            scroll_result = self.qdrant_service.client.scroll(
                collection_name=self.qdrant_service.collection_name,
                limit=10000,  # Get many documents at once
                with_payload=True,
                with_vectors=False  # We don't need vectors for BM25
            )
            
            points = scroll_result[0]  # Get the points from the tuple
            
            for point in points:
                documents.append({
                    'text': point.payload['text'],
                    'filename': point.payload['filename'],
                    'chunk_id': point.payload['chunk_id'],
                    'doc_id': str(point.id)
                })
            
            print(f"Retrieved {len(documents)} documents from Qdrant")
            return documents
            
        except Exception as e:
            print(f"Error getting all documents: {str(e)}")
            return []
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text for BM25"""
        # Input validation
        if isinstance(text, list):
            text = ' '.join(str(item) for item in text)
        elif not isinstance(text, str):
            text = str(text)
            
        # Simple tokenization - can be enhanced
        text = text.lower()
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\-\.]', ' ', text)
        tokens = text.split()
        # Filter out very short tokens
        tokens = [token for token in tokens if len(token) > 2]
        return tokens
    
    async def hybrid_search(self, query: str, top_k: int = Config.TOP_K) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword search"""
        try:
            # Always try semantic search first as it's most reliable
            semantic_results = await self._semantic_search(query, top_k * 2)
            
            # Ensure semantic results have valid scores
            for result in semantic_results:
                score = result.get('score', 0)
                result['score'] = max(0.0, min(1.0, abs(float(score))))
                result['search_type'] = 'semantic'
            
            # Try BM25 only if available and we have built index
            keyword_results = []
            if self.bm25_available and self.bm25 is not None:
                try:
                    keyword_results = self._keyword_search_sync(query, top_k)
                    # Normalize BM25 scores
                    for result in keyword_results:
                        raw_score = result.get('score', 0)
                        # BM25 scores can be large, normalize them
                        normalized_score = min(1.0, max(0.0, float(raw_score) / 10.0))
                        result['score'] = normalized_score
                        result['search_type'] = 'keyword'
                except Exception as e:
                    print(f"BM25 search failed: {str(e)}")
                    keyword_results = []
            
            # Combine results if we have both
            if keyword_results and semantic_results:
                combined_results = self._combine_results(semantic_results, keyword_results)
                search_type = 'hybrid'
            else:
                # Use semantic only
                combined_results = semantic_results
                search_type = 'semantic_only'
            
            # Update search type for all results
            for result in combined_results:
                if 'search_type' not in result:
                    result['search_type'] = search_type
            
            # Rerank if reranker is available
            if self.reranker is not None and combined_results:
                try:
                    final_results = self._rerank_results(query, combined_results, top_k)
                except Exception as e:
                    print(f"Reranking failed: {str(e)}")
                    # Fallback to simple sorting
                    combined_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                    final_results = combined_results[:top_k]
                    for result in final_results:
                        result['final_score'] = result.get('score', 0)
            else:
                # Simple sorting by score
                combined_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                final_results = combined_results[:top_k]
                for result in final_results:
                    result['final_score'] = result.get('score', 0)
            
            # Final score validation
            for result in final_results:
                final_score = result.get('final_score', result.get('score', 0))
                result['final_score'] = max(0.0, min(1.0, abs(float(final_score))))
            
            return final_results
            
        except Exception as e:
            print(f"Error in hybrid search: {str(e)}")
            # Fallback to basic semantic search
            try:
                semantic_results = await self._semantic_search(query, top_k)
                for result in semantic_results:
                    score = result.get('score', 0)
                    result['score'] = max(0.0, min(1.0, abs(float(score))))
                    result['search_type'] = 'semantic_fallback'
                    result['final_score'] = result['score']
                return semantic_results
            except Exception as e2:
                print(f"Even semantic fallback failed: {str(e2)}")
                return []

    async def _semantic_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        query_embedding = self.embedding_service.embed_single_text(query)
        return await self.qdrant_service.search_similar(query_embedding, limit)
    
    def _keyword_search_sync(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform keyword search using BM25 - SYNCHRONOUS"""
        if self.bm25 is None:
            return []
        
        try:
            # Tokenize query
            query_tokens = self._tokenize_text(query)
            
            if not query_tokens:
                return []
            
            # Get BM25 scores
            bm25_scores = self.bm25.get_scores(query_tokens)
            
            # Get top documents with scores
            doc_scores = [(i, score) for i, score in enumerate(bm25_scores)]
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for i, (doc_idx, score) in enumerate(doc_scores[:limit]):
                if doc_idx < len(self.documents_metadata) and score > 0:
                    doc_meta = self.documents_metadata[doc_idx]
                    results.append({
                        'text': doc_meta['text'],
                        'filename': doc_meta['filename'],
                        'chunk_id': doc_meta['chunk_id'],
                        'score': float(score),
                        'search_type': 'keyword'
                    })
            
            return results
            
        except Exception as e:
            print(f"Error in keyword search: {str(e)}")
            return []
    
    def _combine_results(self, semantic_results: List[Dict], keyword_results: List[Dict]) -> List[Dict[str, Any]]:
        """Combine and deduplicate results from different search methods"""
        combined = {}
        
        # Add semantic results
        for result in semantic_results:
            key = f"{result['filename']}_{result['chunk_id']}"
            if key not in combined:
                result['search_type'] = 'semantic'
                # Ensure valid score
                result['score'] = max(0.0, min(1.0, abs(float(result.get('score', 0)))))
                combined[key] = result
            else:
                # If already exists, combine scores
                existing_score = combined[key].get('score', 0)
                new_score = result.get('score', 0)
                combined[key]['score'] = max(existing_score, new_score)
                combined[key]['search_type'] = 'hybrid'
        
        # Add keyword results
        for result in keyword_results:
            key = f"{result['filename']}_{result['chunk_id']}"
            if key not in combined:
                # Ensure valid score for keyword results
                result['score'] = max(0.0, min(1.0, abs(float(result.get('score', 0)))))
                combined[key] = result
            else:
                # Normalize and combine BM25 and semantic scores
                semantic_score = combined[key].get('score', 0)
                keyword_score = result.get('score', 0)
                
                # Ensure both scores are valid
                semantic_score = max(0.0, min(1.0, abs(float(semantic_score))))
                keyword_score = max(0.0, min(1.0, abs(float(keyword_score))))
                
                # Simple score fusion
                combined_score = 0.7 * semantic_score + 0.3 * keyword_score
                combined[key]['score'] = combined_score
                combined[key]['search_type'] = 'hybrid'
        
        return list(combined.values())
    
    def _rerank_results(self, query: str, results: List[Dict], top_k: int) -> List[Dict[str, Any]]:
        """Rerank results using cross-encoder model"""
        if not results or self.reranker is None:
            # Simple sorting by score
            results.sort(key=lambda x: x['score'], reverse=True)
            for result in results:
                result['final_score'] = result['score']
            return results[:top_k]
        
        try:
            # Prepare query-document pairs for reranking
            query_doc_pairs = []
            for result in results:
                # Limit text length for reranker
                text_snippet = result['text'][:512]
                query_doc_pairs.append([query, text_snippet])
            
            # Get reranking scores
            rerank_scores = self.reranker.predict(query_doc_pairs)
            
            # Update results with rerank scores
            for i, result in enumerate(results):
                result['rerank_score'] = float(rerank_scores[i])
                # Combine original score with rerank score
                result['final_score'] = 0.4 * result['score'] + 0.6 * result['rerank_score']
            
            # Sort by final score and return top_k
            results.sort(key=lambda x: x['final_score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"Error in reranking: {str(e)}")
            # Fallback to original ranking
            results.sort(key=lambda x: x['score'], reverse=True)
            for result in results:
                result['final_score'] = result['score']
            return results[:top_k]
