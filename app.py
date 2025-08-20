import streamlit as st
import asyncio
import tempfile
import os
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime

# Import our services
from ingestion_pipeline import IngestionPipeline
from rag_service import RAGService

# Import enhanced service
from enhanced_rag_service import EnhancedRAGService

# Page configuration
st.set_page_config(
    page_title="RAG Chatbot with PDF Upload",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'enhanced_rag_service' not in st.session_state:
    st.session_state.enhanced_rag_service = None
if 'uploaded_files_info' not in st.session_state:
    st.session_state.uploaded_files_info = []
if 'conversation_session' not in st.session_state:
    st.session_state.conversation_session = None

def initialize_enhanced_rag_service():
    """Initialize enhanced RAG service if not already done"""
    if st.session_state.enhanced_rag_service is None:
        st.session_state.enhanced_rag_service = EnhancedRAGService()
        # Create conversation session
        session_id = st.session_state.enhanced_rag_service.create_session()
        st.session_state.conversation_session = session_id
    return st.session_state.enhanced_rag_service

async def process_uploaded_file(uploaded_file, rag_service):
    """Process uploaded PDF file"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Process the PDF
        result = await rag_service.pipeline.process_pdf_file(tmp_path)
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        return result
    except Exception as e:
        return {
            'success': False,
            'filename': uploaded_file.name,
            'error': str(e)
        }

async def get_answer(question: str, rag_service):
    """Get answer from RAG service"""
    return await rag_service.generate_answer(question)

async def get_enhanced_answer(question: str, enhanced_rag_service):
    """Get answer from enhanced RAG service"""
    # Input validation
    if isinstance(question, list):
        question = ' '.join(str(item) for item in question)
    elif not isinstance(question, str):
        question = str(question)
    
    return await enhanced_rag_service.generate_answer_with_context(
        question, st.session_state.conversation_session
    )

def main():
    st.title("📚 Enhanced RAG Chatbot with PDF Upload")
    st.markdown("Upload PDF documents and ask questions with conversation memory and hybrid search!")
    
    # Sidebar for document upload and management
    with st.sidebar:
        st.header("📁 Document Management")
        
        # Initialize enhanced RAG service
        enhanced_rag_service = initialize_enhanced_rag_service()
        
        # File upload
        uploaded_files = st.file_uploader(
            "Upload PDF documents",
            type=['pdf'],
            accept_multiple_files=True,
            key="pdf_uploader"
        )
        
        if uploaded_files:
            if st.button("🔄 Process Documents", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing {uploaded_file.name}...")
                    
                    # Run async function
                    result = asyncio.run(process_uploaded_file(uploaded_file, enhanced_rag_service))
                    
                    if result['success']:
                        st.success(f"✅ {result['filename']}: {result['chunks_count']} chunks")
                        
                        # Add to uploaded files info
                        file_info = {
                            'filename': result['filename'],
                            'chunks_count': result['chunks_count'],
                            'upload_time': datetime.now().strftime("%H:%M:%S"),
                            'status': 'Success'
                        }
                        
                        # Check if file already exists in session state
                        existing_files = [f['filename'] for f in st.session_state.uploaded_files_info]
                        if result['filename'] not in existing_files:
                            st.session_state.uploaded_files_info.append(file_info)
                        
                    else:
                        st.error(f"❌ {result['filename']}: {result['error']}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text("Processing complete!")
                st.rerun()
        
        # Display uploaded files information
        if st.session_state.uploaded_files_info:
            st.header("📋 Uploaded Documents")
            
            for file_info in st.session_state.uploaded_files_info:
                with st.expander(f"📄 {file_info['filename']}"):
                    st.write(f"**Chunks:** {file_info['chunks_count']}")
                    st.write(f"**Upload Time:** {file_info['upload_time']}")
                    st.write(f"**Status:** {file_info['status']}")
        
        # Enhanced features section
        st.header("🚀 Enhanced Features")
        
        # Session info
        if st.button("📊 Session Info"):
            try:
                session_info = enhanced_rag_service.get_session_info()
                st.json(session_info)
            except Exception as e:
                st.error(f"Error getting session info: {str(e)}")
        
        # Rebuild search index
        if st.button("🔄 Rebuild Search Index"):
            try:
                with st.spinner("Rebuilding search index..."):
                    asyncio.run(enhanced_rag_service.rebuild_search_index())
                st.success("Search index rebuilt!")
            except Exception as e:
                st.error(f"Error rebuilding index: {str(e)}")
        
        # Cache management
        st.subheader("💾 Cache Management")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📈 Cache Stats"):
                try:
                    cache_stats = enhanced_rag_service.cache_manager.get_stats()
                    st.json(cache_stats)
                except Exception as e:
                    st.error(f"Error getting cache stats: {str(e)}")
        
        with col2:
            if st.button("🗑️ Clear Cache"):
                try:
                    enhanced_rag_service.clear_cache()
                    st.success("Cache cleared!")
                except Exception as e:
                    st.error(f"Error clearing cache: {str(e)}")
        
        # Session management
        st.subheader("💬 Session Management")
        
        if st.button("🆕 New Session"):
            try:
                session_id = enhanced_rag_service.create_session()
                st.session_state.conversation_session = session_id
                st.session_state.messages = []
                st.success(f"New session created: {session_id[:8]}...")
                st.rerun()
            except Exception as e:
                st.error(f"Error creating session: {str(e)}")
        
        if st.button("🗑️ Clear Session"):
            try:
                enhanced_rag_service.clear_session(st.session_state.conversation_session)
                st.session_state.messages = []
                st.success("Session cleared!")
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing session: {str(e)}")
    
    # Main chat interface
    st.header("💬 Chat with your documents")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show sources if available
            if message["role"] == "assistant" and "sources" in message:
                if message["sources"]:
                    with st.expander("📚 Sources"):
                        for i, source in enumerate(message["sources"], 1):
                            st.write(f"**Source {i}:** {source['filename']} (Score: {source['score']:.3f})")
    
    # Chat input with enhanced processing
    if prompt := st.chat_input("Ask a question about your documents..."):
        if not st.session_state.uploaded_files_info:
            st.warning("Please upload and process some PDF documents first!")
            return
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate enhanced assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking with enhanced context..."):
                try:
                    response = asyncio.run(get_enhanced_answer(prompt, enhanced_rag_service))
                    
                    st.markdown(response['answer'])
                    
                    # Enhanced information display
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        confidence = response['confidence']
                        if confidence > 0.8:
                            st.success(f"Confidence: {confidence:.2%}")
                        elif confidence > 0.6:
                            st.warning(f"Confidence: {confidence:.2%}")
                        else:
                            st.error(f"Confidence: {confidence:.2%}")
                    
                    with col2:
                        search_method = response.get('search_method', 'unknown')
                        if search_method == 'hybrid':
                            st.success(f"🔍 {search_method}")
                        elif search_method in ['semantic_fallback', 'basic_rag_fallback']:
                            st.warning(f"🔍 {search_method}")
                        elif search_method in ['emergency_broad', 'failed', 'error']:
                            st.error(f"🔍 {search_method}")
                        else:
                            st.info(f"🔍 {search_method}")
                    
                    with col3:
                        # Remove conversation context display since we're not using it
                        st.info("🎯 Focused search")
                    
                    # Show additional debug info if search method indicates issues
                    if response.get('search_method') in ['failed', 'error', 'emergency_broad']:
                        st.warning("ℹ️ **Suggestion**: Try asking more specific questions or rebuilding the search index.")
                    
                    # Show enhanced sources
                    if response['sources']:
                        with st.expander("📚 Sources (Enhanced)"):
                            for i, source in enumerate(response['sources'], 1):
                                method = source.get('search_method', 'unknown')
                                confidence_color = "🟢" if source['score'] > 0.7 else "🟡" if source['score'] > 0.4 else "🔴"
                                st.write(f"{confidence_color} **Source {i}:** {source['filename']} "
                                       f"(Score: {source['score']:.3f}, Method: {method})")
                    else:
                        st.info("No sources found - this might indicate no documents were uploaded or processed.")
                    
                    # Add assistant message to chat history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response['answer'],
                        "sources": response['sources'],
                        "confidence": confidence,
                        "search_method": search_method
                    })
                    
                except Exception as e:
                    error_msg = f"Error generating enhanced response: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg
                    })

if __name__ == "__main__":
    main()