<<<<<<< HEAD
# 📚 RAG Chatbot with PDF Upload

A sophisticated Retrieval-Augmented Generation (RAG) chatbot that allows users to upload PDF documents and ask questions about their content. The system uses vector embeddings, semantic search, and AI generation to provide accurate answers based on uploaded documents.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │    │   FastAPI       │    │ Enhanced RAG    │
│                 │───▶│   Backend       │───▶│ Service         │
│   (Frontend)    │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Modern UI     │    │ Document        │    │   Qdrant DB     │
│   Components    │    │ Processing      │    │   (Vectors)     │
│                 │    │ Pipeline        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │                       │
                               ▼                       ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │  PDF Processor  │    │  Embedding      │
                    │  Text Extractor │    │  Generation     │
                    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+
- Node.js 16+
- Qdrant Cloud account (or local instance)
- Gemini API key from Google AI Studio

### Step 1: Backend Setup

```bash
# Navigate to project root
cd qdrant_chatbot

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file with your API keys
echo "QDRANT_URL=your_qdrant_cloud_url" > .env
echo "QDRANT_API_KEY=your_qdrant_api_key" >> .env
echo "COLLECTION_NAME=chatbot_docs" >> .env
echo "GEMINI_API_KEY=your_gemini_api_key" >> .env

# Start the backend server
python backend/main.py
```

Backend will run on: **http://localhost:8000**

### Step 2: Frontend Setup

Open a new terminal:

```bash
# Navigate to frontend directory
cd qdrant_chatbot/frontend

# Install dependencies
npm install

# Start the development server
npm start
```

Frontend will run on: **http://localhost:3000**

## 🎯 How the RAG Processing Works

### 1. Document Upload & Processing Flow

```
User uploads PDF → FastAPI receives files → Document Processing Pipeline
                                                        ↓
Enhanced RAG Service ← Vector Storage ← Embedding Generation ← Text Extraction
                                                        ↓
        Chat Interface ← Answer Generation ← Semantic Search ← Ready for Chat
```

### 2. Technical Implementation

1. **Document Upload**: Files are uploaded via FastAPI multipart form
2. **Text Extraction**: PyMuPDF extracts text while preserving formatting
3. **Chunking**: Intelligent text splitting with overlap for context
4. **Embedding Generation**: FastEmbed creates 384-dimensional vectors
5. **Vector Storage**: Qdrant stores embeddings with metadata
6. **Search & Retrieval**: Hybrid search (semantic + keyword) 
7. **Answer Generation**: Gemini AI generates contextual responses

### 3. Session Management

Each user session:
- Creates isolated RAG service instance
- Maintains conversation history
- Stores uploaded documents separately
- Preserves context across questions

## 📁 File Structure & Key Components

### Backend Architecture
```
backend/
├── main.py                    # FastAPI app with RAG integration
├── enhanced_rag_service.py    # Advanced RAG with conversation memory
├── ingestion_pipeline.py      # Document processing pipeline
├── rag_service.py            # Core RAG functionality
├── pdf_processor.py          # PDF text extraction
├── embedding_service.py      # Vector generation
├── qdrant_service.py         # Vector database operations
└── config.py                 # Configuration management
```

### Frontend Architecture
```
frontend/src/
├── App.tsx                   # Main application with workflow
├── components/
│   ├── chat/                # Chat interface components
│   └── documents/           # Document upload components
└── index.css               # Modern UI styling
```

## 🔧 API Endpoints

### Session Management
- `POST /api/chat/session` - Create new session
- `DELETE /api/chat/session/{id}` - Delete session

### Document Processing
- `POST /api/documents/upload` - Upload files
- `POST /api/documents/process` - Process uploaded files (creates embeddings)
- `GET /api/documents/status` - Check processing status

### Chat Interface
- `POST /api/chat/question` - Ask questions
- `POST /api/chat/ask` - Alternative chat endpoint

### Health & Status
- `GET /api/health` - Backend health check
- `GET /` - Root endpoint

## 🛠️ Troubleshooting

### Backend Connection Issues

**Problem**: "Failed to connect to the server"
**Solutions**:
1. **Check if backend is running**:
   ```bash
   curl http://localhost:8000/api/health
   # Should return: {"status": "ok", "rag_available": true}
   ```

2. **Start backend correctly**:
   ```bash
   cd qdrant_chatbot
   python backend/main.py
   ```

3. **Check for missing dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify RAG services are available**:
   - Check if all Python files are in the correct location
   - Ensure .env file has proper API keys
   - Test Qdrant connection

### Document Processing Issues

**Problem**: Documents upload but processing fails
**Solutions**:
1. **Check file format**: Only PDF, TXT, DOC, DOCX supported
2. **Verify Qdrant connection**: Check QDRANT_URL and API key
3. **Check Gemini API**: Ensure GEMINI_API_KEY is valid
4. **Review backend logs**: Look for specific error messages

### Chat Issues

**Problem**: "No documents have been processed for this session"
**Solutions**:
1. Upload documents first
2. Wait for processing to complete
3. Check document status via API
4. Ensure session hasn't expired

### Frontend Issues

**Problem**: UI not loading properly
**Solutions**:
1. **Check Node.js version**: Use Node 16+
2. **Clear npm cache**: `npm cache clean --force`
3. **Reinstall dependencies**: 
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```
4. **Check backend URL**: Verify API_BASE_URL in .env

## 📈 Advanced Configuration

### Performance Tuning

For **large documents**:
```python
# In config.py
CHUNK_SIZE = 3000
CHUNK_OVERLAP = 600
MAX_CONTEXT_CHUNKS = 20
```

For **faster processing**:
```python
# In config.py
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_CONTEXT_CHUNKS = 8
```

### Custom Embedding Models

```python
# In config.py
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Faster
# or
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"  # More accurate
```

## 🔒 Production Deployment

### Security Considerations
- Restrict CORS origins to your domain
- Add authentication middleware
- Use environment variables for secrets
- Implement rate limiting

### Scaling Options
- Use Redis for session storage
- Implement connection pooling
- Add load balancing
- Use Docker containers

## 📚 Usage Examples

### 1. Upload and Process Documents
1. Start backend and frontend
2. Click "Upload Documents"
3. Select PDF files
4. Wait for automatic processing
5. Start chatting!

### 2. Ask Questions
```
User: "What are the key findings in the research paper?"
AI: Based on the uploaded document 'research-paper.pdf', the key findings include...

User: "Can you summarize the methodology section?"
AI: The methodology section describes a three-phase approach...
```

### 3. Session Management
- Create new sessions for different document sets
- Each session maintains separate conversation history
- Sessions automatically clean up resources

---

## 🤝 Contributing

We welcome contributions! Please read our contributing guidelines and submit pull requests for any improvements.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

**Happy chatting with your documents! 🚀📚**
```

**Multi-Strategy Approach Reasoning**:
- **Semantic Search**: Captures meaning and context
- **Keyword Search**: Handles specific terms and jargon
- **Reference Search**: Finds numbered sections and chapters
- **Emergency Search**: Ensures something is always found

2. **Context Preparation**:
```python
context_parts = []
for i, doc in enumerate(relevant_docs[:max_chunks]):
    context_parts.append(f"Source {i+1} (Score: {doc['score']:.3f}, File: {doc['filename']}): {doc['text']}")
context = "\n\n".join(context_parts)
```

**Context Engineering**:
- **Source Attribution**: Enables citation and verification
- **Score Inclusion**: Indicates relevance confidence
- **Structured Format**: Optimizes AI understanding

3. **AI Generation with Gemini**:
```python
async def _generate_with_gemini(self, question: str, context: str, docs: List[Dict]) -> str:
    prompt = f"""You are a helpful AI assistant that answers questions based on provided document context.

CONTEXT FROM DOCUMENTS:
{context}

INSTRUCTIONS:
- Answer using ONLY the provided context
- PRESERVE ALL ORIGINAL FORMATTING
- Use proper markdown for code blocks
- Maintain table structures
- Keep technical notation exact
"""
```

**Prompt Engineering Principles**:
- **Clear Instructions**: Explicit behavior guidelines
- **Context Emphasis**: Prevents hallucination
- **Formatting Preservation**: Maintains document integrity
- **Technical Accuracy**: Preserves code and formulas

**Why Gemini 2.5 Pro?**
- **Advanced Reasoning**: Superior context understanding
- **Formatting Awareness**: Preserves document structure
- **Large Context Window**: Handles extensive document content
- **Instruction Following**: Reliable adherence to prompts

---

### 🖥️ User Interface

#### `app.py` - Interactive Streamlit Application
**Purpose**: User-friendly web interface for document upload and questioning.

**UI Architecture**:

1. **Sidebar - Document Management**:
```python
uploaded_files = st.file_uploader(
    "Upload PDF documents",
    type=['pdf'],
    accept_multiple_files=True,
    key="pdf_uploader"
)
```

**Features**:
- **Multi-file Upload**: Batch document processing
- **Progress Tracking**: Real-time processing feedback
- **File Management**: View uploaded documents and statistics
- **Collection Control**: Clear database when needed

2. **Main Area - Chat Interface**:
```python
if prompt := st.chat_input("Ask a question about your documents..."):
    # Process user question
    response = asyncio.run(get_answer(prompt, rag_service))
    # Display answer with sources and confidence
```

**Chat Features**:
- **Message History**: Persistent conversation context
- **Source Attribution**: Transparent answer sourcing
- **Confidence Scoring**: Quality indicators
- **Error Handling**: Graceful failure management

**Async Integration**:
```python
result = asyncio.run(process_uploaded_file(uploaded_file, rag_service))
```

**Why Asyncio?**
- **Non-blocking Operations**: UI remains responsive
- **Concurrent Processing**: Efficient resource utilization
- **Database Compatibility**: Matches async database operations

---

### 🧪 Testing and Setup

#### `test_pipeline.py` - System Validation
**Purpose**: Comprehensive testing of all system components.

**Test Coverage**:
1. **Database Connectivity**: Verify Qdrant connection
2. **Embedding Generation**: Test vector creation
3. **Search Functionality**: Validate retrieval accuracy
4. **Error Handling**: Ensure graceful failure management

#### `setup.py` - Automated System Setup
**Purpose**: Streamlined environment configuration and dependency management.

**Setup Process**:
1. **Environment Validation**: Check .env file completeness
2. **Dependency Installation**: Install required packages
3. **Directory Creation**: Set up necessary folders
4. **Guidance Provision**: Clear next steps for users

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PDF documents to process
- Qdrant Cloud account (or local Qdrant instance)
- Gemini API key from Google AI Studio

### Installation

1. **Clone and Navigate**:
```bash
git clone <repository>
cd qdrant_chatbot
```

2. **Environment Setup**:
Create `.env` file:
```env
QDRANT_URL="your_qdrant_cloud_url"
QDRANT_API_KEY="your_qdrant_api_key"
COLLECTION_NAME="chatbot_docs"
GEMINI_API_KEY="your_gemini_api_key"
```

3. **Automated Setup**:
```bash
python setup.py
```

4. **Testing**:
```bash
python test_pipeline.py
```

5. **Launch Application**:
```bash
streamlit run app.py
```

## 🔧 Advanced Configuration

### Performance Tuning

**For Large Documents**:
- Increase `CHUNK_SIZE` to 3000+
- Adjust `MAX_CONTEXT_CHUNKS` to 15+
- Consider using `TOP_K` of 30+

**For Fast Processing**:
- Reduce `CHUNK_SIZE` to 1000
- Lower `MAX_CONTEXT_CHUNKS` to 8
- Use smaller embedding models

**For High Accuracy**:
- Increase `CHUNK_OVERLAP` to 500+
- Use `SCORE_THRESHOLD` of 0.1+
- Implement re-ranking algorithms

### Customization Options

**Different Embedding Models**:
```python
# In config.py
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Faster
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"                 # More accurate
```

**Database Alternatives**:
- Local Qdrant instance for privacy
- Pinecone for managed service
- Weaviate for GraphQL queries

**AI Model Options**:
- GPT-4 for enhanced reasoning
- Claude for better document understanding
- Local LLMs for complete privacy

## 🛠️ Troubleshooting

### Common Issues

**Negative Confidence Scores or "No Context" Errors**:
- **Cause**: Invalid score calculations or missing search dependencies
- **Solution**: 
  - Rebuild search index using the "🔄 Rebuild Search Index" button
  - Install missing dependencies: `pip install rank-bm25 sentence-transformers`
  - Clear cache and restart the application
  - Re-upload documents if the collection is empty

**"I couldn't generate an answer" Messages**:
- **Cause**: Search failures or empty document collection
- **Solution**:
  - Verify documents are uploaded and processed
  - Check collection stats in the sidebar
  - Try asking simpler, more direct questions
  - Use the emergency broad search fallback

**Hybrid Search Failures**:
- **Cause**: Missing BM25 or CrossEncoder dependencies
- **Solution**: The system automatically falls back to semantic search
- **Optional**: Install full dependencies for enhanced search capabilities

**Search Method Shows "failed" or "error"**:
- **Cause**: No documents in collection or search index corruption
- **Solution**:
  - Upload PDF documents first
  - Rebuild search index
  - Check Qdrant connection and API key
  - Verify documents were processed successfully

### Performance Optimization

**Memory Management**:
- Process documents in smaller batches
- Clear unused embeddings from memory
- Monitor system resource usage

**Speed Improvements**:
- Use GPU acceleration for embeddings
- Implement caching for repeated queries
- Optimize chunk sizes for your use case

## 📈 Monitoring and Analytics

### Usage Metrics
- Track query response times
- Monitor embedding generation speed
- Measure retrieval accuracy

### Quality Assurance
- Implement answer relevance scoring
- Track user satisfaction ratings
- Monitor source attribution accuracy

## 🔮 Future Enhancements

### Planned Features
- Multi-modal support (images, tables)
- Advanced query understanding
- Collaborative document management
- Real-time document updates

### Architecture Improvements
- Microservices decomposition
- Horizontal scaling capabilities
- Advanced caching strategies
- Enhanced security measures

---

## 🤝 Contributing

We welcome contributions! Please read our contributing guidelines and submit pull requests for any improvements.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Qdrant Team**: Excellent vector database
- **Google AI**: Powerful Gemini models
- **FastEmbed Contributors**: Efficient embedding library
- **Streamlit Team**: Amazing web app framework

---

**Happy chatting with your documents! 🚀📚**
=======
# End_to_End_Chatbot
>>>>>>> b35c0ef3e9be24eb834829d24d591863c151e2df
