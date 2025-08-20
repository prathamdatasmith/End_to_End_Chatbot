# 🚀 How to Run the RAG Chatbot (React + FastAPI)

## Prerequisites

Before you start, make sure you have:
- Python 3.8+ installed
- Node.js 16+ and npm installed
- Your existing `.env` file with API keys

## 📥 Installation Steps

### Step 1: Install Node.js (if not installed)

1. Go to [nodejs.org](https://nodejs.org/)
2. Download the LTS version
3. Install it (this also installs npm)
4. Verify installation:
   ```bash
   node --version
   npm --version
   ```

### Step 2: Set Up Backend (FastAPI)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on: http://localhost:8000

### Step 3: Set Up Frontend (React)

Open a new terminal window:

```bash
# Navigate to project root directory
cd qdrant_chatbot

# Run the frontend setup script
npm run setup-frontend

# Navigate to frontend directory
cd frontend

# Start the development server
npm start
```

If you encounter any issues with the setup, try our automatic fix:

```bash
# Run the fix script from the project root
npm run fix-frontend

# Then start the server again
cd frontend
npm start
```

Or manually fix it:

```bash
# Navigate to frontend directory
cd frontend

# Remove node_modules directory
rm -rf node_modules  # On Linux/Mac
rmdir /s /q node_modules  # On Windows

# Clear npm cache
npm cache clean --force

# Install React Scripts specifically
npm install react-scripts@5.0.1 --save

# Install all dependencies with force flag
npm install --force
```

Frontend will run on: http://localhost:3000

### Step 4: Access the Application

1. Open your web browser
2. Go to: http://localhost:3000
3. You should see the modern chatbot interface!

## 🔧 Development Commands

### Backend Commands
```bash
# Start backend in development mode
uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black app/
```

### Frontend Commands
```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Format code
npm run format
```

## 🚨 Troubleshooting

### Common Issues:

1. **Port already in use**
   - Backend: Change port with `--port 8001`
   - Frontend: It will automatically suggest a different port

2. **Module not found errors**
   - Backend: Make sure virtual environment is activated
   - Frontend: Run `npm install` again

3. **CORS errors**
   - Make sure backend is running on port 8000
   - Check that frontend is making requests to the correct URL

4. **API key errors**
   - Make sure your `.env` file is in the backend directory
   - Check that all required environment variables are set

5. **React Scripts not found**
   - Run our fix script: `npm run fix-frontend`
   - Or manually reinstall with: `npm install react-scripts@5.0.1 --save`
   - Make sure your package.json has the correct scripts section
   - Try deleting node_modules folder and running `npm install --force`
   - Ensure you're using a compatible Node.js version (16+ recommended)

6. **npm ERR! Refusing to delete**
   - If you see this error when installing dependencies, use the `--force` flag:
   - `npm install --force react-scripts`

7. **Module not found: Can't resolve 'react'**
   - This typically happens when dependencies are not properly installed
   - Run: `npm install --legacy-peer-deps`

8. **"Cannot find module" errors**
   - Make sure to run the setup from the project root: `npm run setup-frontend`
   - Check that all dependencies in package.json are properly installed

9. **Chat Interface Not Showing**
   - Make sure `ChatInterface` component is imported in `App.tsx`
   - Check if all required components are created:
     - `ChatInterface.tsx`
     - `ChatMessage.tsx`
     - `TypingIndicator.tsx`
   - Verify that the `sessionId` is being passed correctly
   - Make sure all component imports and exports match
   - If using VS Code, try using the "Reload Window" command to refresh TypeScript type checking

10. **API Connection Issues**
    - Ensure the backend is running on the expected port (default: 8000)
    - Check CORS settings in the backend
    - Look for error messages in the browser console
    - Try setting `REACT_APP_API_URL` in a `.env` file if your API is on a different URL

11. **Chatbot Responses Look Garbled (Markdown Not Rendered)**
    - **Problem**: Chatbot answers with tables, code, or formatting look messy or "garbled" in the React UI.
    - **Solution**: The frontend must render chatbot responses as Markdown, not plain text.
    - **How to Fix**:
      1. Install a markdown renderer in your frontend:
         ```bash
         cd frontend
         npm install react-markdown
         ```
      2. In your chat message component (e.g., `ChatMessage.tsx`), use `react-markdown` to render the chatbot's answer:
         ```tsx
         // ...existing imports...
         import ReactMarkdown from 'react-markdown';

         // ...inside your component...
         <ReactMarkdown>{message.content}</ReactMarkdown>
         ```
      3. (Optional) Add plugins for tables, code highlighting, and sanitization for security.
      4. Now, tables, code blocks, and formatting from the backend will display correctly, just like in Streamlit.

## 🔄 Quick Restart

If something goes wrong, here's how to restart everything:

1. Stop both servers (Ctrl+C in both terminals)
2. Run the fix-frontend script: `npm run fix-frontend` 
3. Restart backend: `uvicorn app.main:app --reload`
4. Restart frontend: `npm start`

## 📱 Using the Application

1. **Upload Documents**: Click the upload button to add PDF files
2. **Ask Questions**: Type your questions in the chat interface
3. **View Sources**: Click on source references to see where answers came from
4. **Session Management**: Create new sessions or clear chat history

## 🐳 Docker Setup (Optional)

If you prefer using Docker:

```bash
# Build and run everything with Docker Compose
docker-compose up --build

# Access the application at http://localhost:3000
```

## 🆘 Getting Help

If you run into issues:
1. Check the console/terminal for error messages
2. Make sure all prerequisites are installed
3. Verify your `.env` file contains all required keys
4. Try our fix script: `npm run fix-frontend`
5. Try running with legacy peer deps: `npm start --legacy-peer-deps`

Happy chatting! 🤖✨
