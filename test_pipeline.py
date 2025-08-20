import asyncio
import os
from ingestion_pipeline import IngestionPipeline
from rag_service import RAGService
from enhanced_rag_service import EnhancedRAGService

async def test_pipeline():
    """Test the complete enhanced pipeline"""
    print("🧪 Testing Enhanced RAG Pipeline...")
    
    # Initialize enhanced service
    enhanced_rag = EnhancedRAGService()
    
    try:
        # Test 1: Check Qdrant connection
        print("\n1. Testing Qdrant connection...")
        stats = await enhanced_rag.pipeline.get_collection_stats()
        print(f"✅ Connection successful: {stats}")
        
        # Test 2: Test basic embedding service
        print("\n2. Testing embedding service...")
        test_text = "This is a test sentence for embedding."
        embedding = enhanced_rag.pipeline.embedding_service.embed_single_text(test_text)
        print(f"✅ Embedding generated: dimension {len(embedding)}")
        
        # Test 3: Test search functionality
        print("\n3. Testing search functionality...")
        try:
            query_embedding = enhanced_rag.pipeline.embedding_service.embed_single_text("test query")
            search_results = await enhanced_rag.pipeline.qdrant_service.search_similar(query_embedding, 5)
            print(f"✅ Search test: found {len(search_results)} results")
        except Exception as e:
            print(f"⚠️ Search test failed: {str(e)}")
        
        # Test 4: Test hybrid search index building
        print("\n4. Testing hybrid search setup...")
        try:
            await enhanced_rag.rebuild_search_index()
            print("✅ Hybrid search index built")
        except Exception as e:
            print(f"⚠️ Hybrid search setup failed: {str(e)}")
        
        # Test 5: Test conversation with enhanced context
        print("\n5. Testing enhanced conversation with BULLETPROOF search...")
        session_id = enhanced_rag.create_session()
        
        test_questions = [
            "What is this document about?",
            "Example 7-1",  # Your specific example
            "Vertical partitioning",  # Part of your example
            "Apache Spark",  # Another part
            "foreachBatch",  # Method mentioned
            "Can you provide more details?",
            "What are the main topics covered?",
            "Tell me anything you can find",  # Very broad question
            "Show me some content",  # Another broad question
        ]
        
        for question in test_questions:
            print(f"\n   Question: {question}")
            response = await enhanced_rag.generate_answer_with_context(question, session_id)
            print(f"   Answer preview: {response['answer'][:200]}...")
            print(f"   Confidence: {response['confidence']:.2%}")
            print(f"   Sources: {len(response['sources'])}")
            print(f"   Search method: {response.get('search_method', 'unknown')}")
            
            # Check if we're getting the dreaded "couldn't generate" message
            if "couldn't generate" in response['answer'].lower():
                print(f"   ⚠️ WARNING: Still getting 'couldn't generate' for: {question}")
            else:
                print(f"   ✅ SUCCESS: Got substantive answer for: {question}")
        
        # Test 6: System diagnostics
        print("\n6. System diagnostics...")
        session_info = enhanced_rag.get_session_info()
        print(f"✅ Session info: {session_info['current_session'][:8] if session_info['current_session'] else 'None'}...")
        
        cache_stats = enhanced_rag.cache_manager.get_stats()
        print(f"✅ Cache stats: {cache_stats.get('total_entries', 0)} entries")
        
        print("\n🎉 Enhanced pipeline test completed!")
        
    except Exception as e:
        print(f"❌ Critical test failure: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        enhanced_rag.cleanup()

if __name__ == "__main__":
    asyncio.run(test_pipeline())