const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('📦 Starting frontend setup...');

// Ensure frontend directory exists
const frontendDir = path.join(__dirname, 'frontend');
if (!fs.existsSync(frontendDir)) {
  console.log('Creating frontend directory...');
  fs.mkdirSync(frontendDir, { recursive: true });
}

// Create necessary files and directories
try {
  console.log('Setting up frontend project structure...');
  
  // Create basic structure
  const directories = [
    path.join(frontendDir, 'src'),
    path.join(frontendDir, 'public'),
    path.join(frontendDir, 'src', 'components'),
    path.join(frontendDir, 'src', 'components', 'chat'),
    path.join(frontendDir, 'src', 'components', 'documents'),
    path.join(frontendDir, 'src', 'hooks'),
    path.join(frontendDir, 'src', 'types')
  ];
  
  directories.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
  
  // Now clear the node_modules completely to avoid any conflicts
  const nodeModulesPath = path.join(frontendDir, 'node_modules');
  if (fs.existsSync(nodeModulesPath)) {
    console.log('Removing existing node_modules to ensure clean install...');
    try {
      if (process.platform === 'win32') {
        // Windows needs special handling for deep directory structures
        execSync(`rmdir /s /q "${nodeModulesPath}"`, { stdio: 'inherit' });
      } else {
        execSync(`rm -rf "${nodeModulesPath}"`, { stdio: 'inherit' });
      }
    } catch (error) {
      console.warn('Warning: Could not completely remove node_modules. Continuing anyway...');
    }
  }
  
  // Change to the frontend directory
  process.chdir(frontendDir);
  
  // Update package.json with exact content
  console.log('Creating package.json with precise dependencies...');
  const packageJson = {
    "name": "qdrant-chatbot-frontend",
    "version": "1.0.0",
    "private": true,
    "dependencies": {
      "@heroicons/react": "^2.0.18",
      "axios": "^1.6.2",
      "framer-motion": "^10.16.5",
      "react": "^18.2.0",
      "react-dom": "^18.2.0",
      "react-hot-toast": "^2.4.1",
      "react-scripts": "5.0.1",
      "typescript": "^4.9.5",
      "uuid": "^9.0.1",
      "web-vitals": "^3.5.0"
    },
    "devDependencies": {
      "@types/node": "^20.10.0",
      "@types/react": "^18.2.38",
      "@types/react-dom": "^18.2.15",
      "@types/uuid": "^9.0.7",
      "autoprefixer": "^10.4.16",
      "postcss": "^8.4.31",
      "tailwindcss": "^3.3.5"
    },
    "scripts": {
      "start": "react-scripts start",
      "build": "react-scripts build",
      "test": "react-scripts test",
      "eject": "react-scripts eject"
    },
    "eslintConfig": {
      "extends": [
        "react-app",
        "react-app/jest"
      ]
    },
    "browserslist": {
      "production": [
        ">0.2%",
        "not dead",
        "not op_mini all"
      ],
      "development": [
        "last 1 chrome version",
        "last 1 firefox version",
        "last 1 safari version"
      ]
    }
  };
  
  fs.writeFileSync(
    path.join(frontendDir, 'package.json'),
    JSON.stringify(packageJson, null, 2)
  );
  
  // Install dependencies with npm or alternative approaches
  console.log('Installing dependencies...');
  console.log('This may take a few minutes, please be patient...');
  
  try {
    // First attempt: regular npm install
    execSync('npm install', { stdio: 'inherit' });
  } catch (error) {
    console.log('First installation attempt failed, trying alternative approach...');
    
    try {
      // Second attempt: Install react-scripts explicitly first
      execSync('npm install react-scripts --save', { stdio: 'inherit' });
      execSync('npm install', { stdio: 'inherit' });
    } catch (secondError) {
      console.log('Second installation attempt failed, trying with force flag...');
      
      // Third attempt: Use force flag
      try {
        execSync('npm install --force', { stdio: 'inherit' });
      } catch (thirdError) {
        console.error('All installation attempts failed. Please try manually:');
        console.error('cd frontend');
        console.error('npm install react-scripts --save');
        console.error('npm install --force');
        throw new Error('Failed to install dependencies');
      }
    }
  }
  
  console.log('Creating essential frontend files...');
  
  // Create index.html
  const indexHtml = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="RAG Chatbot with PDF processing" />
    <title>RAG Chatbot</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>`;
  
  fs.writeFileSync(path.join(frontendDir, 'public', 'index.html'), indexHtml);
  
  // Create basic App.tsx file
  const appTsx = `import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { v4 as uuidv4 } from 'uuid';
import { DocumentUploader } from './components/documents/DocumentUploader';
import { ChatInterface } from './components/chat/ChatInterface';
import axios from 'axios';
import toast from 'react-hot-toast';
import { 
  CheckCircleIcon, 
  CloudArrowUpIcon, 
  CogIcon, 
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import './App.css';

interface SessionResponse {
  session_id: string;
}

interface DocumentStatusResponse {
  processed: boolean;
}

const App: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>('');
  const [documentsProcessed, setDocumentsProcessed] = useState<boolean>(false);
  const [documentsUploaded, setDocumentsUploaded] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [currentStep, setCurrentStep] = useState<'upload' | 'process' | 'chat'>('upload');
  const [error, setError] = useState<string | null>(null);
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const existingSessionId = localStorage.getItem('chatSessionId');
    if (existingSessionId) {
      setSessionId(existingSessionId);
      checkDocumentsStatus(existingSessionId);
    } else {
      createNewSession();
    }
  }, []);

  const createNewSession = async () => {
    setIsLoading(true);
    setError(null);
    try {
      console.log('Creating new session...');
      const response = await axios.post<SessionResponse>(\`\${API_BASE_URL}/api/chat/session\`, {}, {
        headers: { 'Content-Type': 'application/json' },
        timeout: 10000
      });
      const newSessionId = response.data.session_id;
      localStorage.setItem('chatSessionId', newSessionId);
      setSessionId(newSessionId);
      setDocumentsProcessed(false);
      setDocumentsUploaded(false);
      setCurrentStep('upload');
      console.log('Session created successfully:', newSessionId);
    } catch (err: any) {
      console.error('Failed to create session:', err);
      let errorMsg = 'Failed to connect to the server';
      
      if (err.code === 'ECONNREFUSED' || err.message?.includes('ECONNREFUSED')) {
        errorMsg = 'Backend server is not running. Please start it with: python backend/main.py';
      } else if (err.response?.status === 500) {
        errorMsg = 'Server error. Check if RAG services are properly configured.';
      }
      
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const checkDocumentsStatus = async (sid: string) => {
    try {
      const response = await axios.get<DocumentStatusResponse>(\`\${API_BASE_URL}/api/documents/status?session_id=\${sid}\`);
      const processed = response.data.processed;
      setDocumentsProcessed(processed);
      if (processed) {
        setDocumentsUploaded(true);
        setCurrentStep('chat');
      }
    } catch (err) {
      console.log('No documents processed yet or session not found:', err);
      setDocumentsProcessed(false);
    }
  };

  const handleDocumentsUploaded = () => {
    setDocumentsUploaded(true);
    setDocumentsProcessed(true);
    setCurrentStep('chat');
    toast.success('Documents processed! You can now start chatting.');
  };

  const resetWorkflow = () => {
    setDocumentsUploaded(false);
    setDocumentsProcessed(false);
    setCurrentStep('upload');
    setError(null);
    createNewSession();
  };

  const handleServerError = (errorMessage: string) => {
    const safeErrorMessage = typeof errorMessage === 'string' 
      ? errorMessage 
      : 'Connection to server failed';
    setError(safeErrorMessage);
    toast.error(safeErrorMessage);
  };

  const handleSessionChange = (newSessionId: string) => {
    localStorage.setItem('chatSessionId', newSessionId);
    setSessionId(newSessionId);
    checkDocumentsStatus(newSessionId);
  };

  return (
    <>
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'white',
            color: '#1f2937',
            borderRadius: '0.75rem',
            border: '1px solid #e5e7eb',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          },
        }}
      />
      
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        fontFamily: 'Inter, sans-serif',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <header style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
          padding: '1rem 2rem',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            maxWidth: '1400px',
            margin: '0 auto'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <h1 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1f2937', margin: 0 }}>
                🤖 RAG Assistant
              </h1>
              <span style={{
                fontSize: '0.875rem',
                color: '#6b7280',
                background: '#f3f4f6',
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px'
              }}>
                Session: {sessionId ? sessionId.substring(0, 8) + '...' : 'Loading...'}
              </span>
            </div>
            
            <button 
              onClick={resetWorkflow}
              style={{
                background: '#4f46e5',
                color: 'white',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '0.5rem',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              title="Start New Session"
            >
              New Session
            </button>
          </div>
        </header>

        {/* Main Content */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {error && (
            <div style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#991b1b',
              padding: '1rem 2rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              fontWeight: '500'
            }}>
              <ExclamationTriangleIcon style={{ width: '1.25rem', height: '1.25rem' }} />
              <span>{error}</span>
              <button 
                onClick={createNewSession} 
                disabled={isLoading}
                style={{
                  background: '#dc2626',
                  color: 'white',
                  border: 'none',
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  fontWeight: '500',
                  cursor: 'pointer',
                  marginLeft: 'auto'
                }}
              >
                {isLoading ? 'Retrying...' : 'Retry'}
              </button>
            </div>
          )}

          {!sessionId || isLoading ? (
            <div style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              color: 'white',
              padding: '2rem'
            }}>
              <div style={{
                width: '4rem',
                height: '4rem',
                border: '4px solid rgba(255, 255, 255, 0.3)',
                borderLeft: '4px solid white',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                marginBottom: '2rem'
              }}></div>
              <h2 style={{ fontSize: '2rem', marginBottom: '0.5rem', fontWeight: '600' }}>
                Initializing RAG Assistant...
              </h2>
              <p style={{ fontSize: '1.125rem', opacity: 0.9, maxWidth: '400px' }}>
                Setting up your AI-powered document chat session
              </p>
            </div>
          ) : currentStep === 'upload' ? (
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '2rem'
            }}>
              <div style={{
                background: 'white',
                borderRadius: '1.5rem',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
                padding: '3rem',
                maxWidth: '600px',
                width: '100%',
                textAlign: 'center'
              }}>
                <CloudArrowUpIcon style={{
                  width: '4rem',
                  height: '4rem',
                  color: '#4f46e5',
                  margin: '0 auto 1rem'
                }} />
                <h2 style={{
                  fontSize: '1.75rem',
                  fontWeight: '600',
                  color: '#1f2937',
                  marginBottom: '0.5rem'
                }}>
                  Upload Your Documents
                </h2>
                <p style={{
                  color: '#6b7280',
                  fontSize: '1.125rem',
                  marginBottom: '2rem'
                }}>
                  Upload PDF, Word, or text documents to get started with AI-powered chat
                </p>
                
                <DocumentUploader 
                  sessionId={sessionId}
                  onUploadComplete={handleDocumentsUploaded}
                  onError={handleServerError}
                />
              </div>
            </div>
          ) : (
            <ChatInterface 
              sessionId={sessionId} 
              onSessionChange={handleSessionChange}
              onError={handleServerError} 
            />
          )}
        </main>
      </div>
    </>
  );
};

export default App;`;
  
  fs.writeFileSync(path.join(frontendDir, 'src', 'App.tsx'), appTsx);
  
  // Create index.tsx
  const indexTsx = `import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);`;
  
  fs.writeFileSync(path.join(frontendDir, 'src', 'index.tsx'), indexTsx);
  
  // Create index.css with Tailwind directives
  const indexCss = `@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}`;
  
  fs.writeFileSync(path.join(frontendDir, 'src', 'index.css'), indexCss);
  
  // Create App.css
  const appCss = `/* Add your custom styles here */`;
  fs.writeFileSync(path.join(frontendDir, 'src', 'App.css'), appCss);
  
  // Create tailwind.config.js
  const tailwindConfig = `module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}`;
  
  fs.writeFileSync(path.join(frontendDir, 'tailwind.config.js'), tailwindConfig);
  
  // Create postcss.config.js
  const postcssConfig = `module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  }
}`;
  
  fs.writeFileSync(path.join(frontendDir, 'postcss.config.js'), postcssConfig);
  
  // Create tsconfig.json
  const tsconfigJson = {
    "compilerOptions": {
      "target": "es5",
      "lib": [
        "dom",
        "dom.iterable",
        "esnext"
      ],
      "allowJs": true,
      "skipLibCheck": true,
      "esModuleInterop": true,
      "allowSyntheticDefaultImports": true,
      "strict": true,
      "forceConsistentCasingInFileNames": true,
      "noFallthroughCasesInSwitch": true,
      "module": "esnext",
      "moduleResolution": "node",
      "resolveJsonModule": true,
      "isolatedModules": true,
      "noEmit": true,
      "jsx": "react-jsx"
    },
    "include": [
      "src"
    ]
  };
  
  fs.writeFileSync(
    path.join(frontendDir, 'tsconfig.json'),
    JSON.stringify(tsconfigJson, null, 2)
  );
  
  // Create ChatInterface.tsx
  const chatInterfaceTsx = `import React, { useState, useRef, useEffect } from 'react';
import { useChatService } from '../../hooks/useChatService';
import toast from 'react-hot-toast';
import { PaperAirplaneIcon } from '@heroicons/react/24/outline';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    filename?: string;
    page_number?: number;
    text?: string;
    relevance?: number;
  }>;
  confidence?: number;
  search_method?: string;
}

interface ChatInterfaceProps {
  sessionId: string;
  onSessionChange: (sessionId: string) => void;
  onError: (message: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  onSessionChange,
  onError
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { askQuestion, isLoading, error } = useChatService();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading || !sessionId) {
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      console.log('Sending question:', {
        question: userMessage.content,
        session_id: sessionId
      });

      const response = await askQuestion({
        question: userMessage.content,
        session_id: sessionId
      });

      console.log('Received response:', response);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
        confidence: response.confidence,
        search_method: response.search_method
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      if (response.confidence > 0.7) {
        toast.success('High confidence answer generated!');
      } else if (response.confidence > 0.4) {
        toast('Answer generated with moderate confidence', { icon: '⚠️' });
      }

    } catch (err: any) {
      console.error('Error sending message:', err);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: \`I'm sorry, I encountered an error: \${err.message || 'Unknown error'}. Please try again or check if your documents were processed correctly.\`,
        timestamp: new Date(),
        confidence: 0,
        search_method: 'error'
      };

      setMessages(prev => [...prev, errorMessage]);
      onError(err.message || 'Failed to get response');
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      padding: '1rem 2rem 2rem'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '1.5rem',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Chat Header */}
        <div style={{
          background: 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)',
          color: 'white',
          padding: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: '3rem',
              height: '3rem',
              background: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.5rem',
              backdropFilter: 'blur(10px)'
            }}>
              🤖
            </div>
            <div>
              <div style={{
                fontSize: '1.25rem',
                fontWeight: '600',
                marginBottom: '0.25rem'
              }}>
                RAG Assistant
              </div>
              <div style={{
                fontSize: '0.875rem',
                opacity: 0.8
              }}>
                Ask questions about your documents
              </div>
            </div>
          </div>
          <div style={{
            fontSize: '0.875rem',
            opacity: 0.75
          }}>
            Session: {sessionId.substring(0, 8)}...
          </div>
        </div>

        {/* Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '2rem',
          background: '#f9fafb',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem'
        }}>
          {messages.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '3rem 1rem'
            }}>
              <div style={{
                fontSize: '4rem',
                marginBottom: '1.5rem',
                opacity: 0.8
              }}>
                💬
              </div>
              <h3 style={{
                fontSize: '1.5rem',
                fontWeight: '600',
                color: '#374151',
                marginBottom: '0.75rem'
              }}>
                Start a Conversation
              </h3>
              <p style={{
                color: '#6b7280',
                lineHeight: 1.6,
                maxWidth: '400px',
                margin: '0 auto'
              }}>
                Ask questions about your uploaded documents. I can help you find information, 
                summarize content, and answer specific questions based on your files.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} style={{
                display: 'flex',
                marginBottom: '1rem',
                justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start'
              }}>
                <div style={{
                  maxWidth: '75%',
                  padding: '1rem 1.5rem',
                  borderRadius: '0.75rem',
                  position: 'relative',
                  background: message.type === 'user' 
                    ? 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)'
                    : 'white',
                  color: message.type === 'user' ? 'white' : '#1f2937',
                  border: message.type === 'assistant' ? '1px solid #e5e7eb' : 'none',
                  boxShadow: message.type === 'assistant' ? '0 1px 2px 0 rgba(0, 0, 0, 0.05)' : 'none'
                }}>
                  <div style={{
                    fontSize: '0.95rem',
                    lineHeight: 1.6,
                    whiteSpace: 'pre-wrap'
                  }}>
                    {message.content}
                  </div>
                  
                  <div style={{
                    marginTop: '0.75rem',
                    fontSize: '0.75rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    color: message.type === 'user' ? 'rgba(255, 255, 255, 0.7)' : '#6b7280'
                  }}>
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                    {message.type === 'assistant' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {message.confidence && (
                          <span style={{
                            color: message.confidence > 0.7 ? '#059669' : 
                                  message.confidence > 0.4 ? '#ca8a04' : '#dc2626'
                          }}>
                            {Math.round(message.confidence * 100)}% confidence
                          </span>
                        )}
                        {message.search_method && (
                          <span style={{ opacity: 0.75 }}>
                            via {message.search_method}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div style={{
                      marginTop: '1rem',
                      paddingTop: '1rem',
                      borderTop: '1px solid #e5e7eb'
                    }}>
                      <div style={{
                        fontSize: '0.875rem',
                        fontWeight: '500',
                        color: '#4f46e5',
                        marginBottom: '0.75rem'
                      }}>
                        📚 Sources ({message.sources.length})
                      </div>
                      <div>
                        {message.sources.map((source, index) => (
                          <div key={index} style={{
                            marginTop: '0.75rem',
                            padding: '1rem',
                            background: '#f9fafb',
                            border: '1px solid #e5e7eb',
                            borderRadius: '0.5rem',
                            fontSize: '0.875rem'
                          }}>
                            <div style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'flex-start',
                              marginBottom: '0.5rem'
                            }}>
                              <div style={{
                                fontWeight: '600',
                                color: '#1f2937',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem'
                              }}>
                                📄 {source.filename || 'Unknown file'}
                                {source.page_number && (
                                  <span style={{
                                    color: '#6b7280',
                                    fontSize: '0.75rem'
                                  }}>
                                    Page {source.page_number}
                                  </span>
                                )}
                              </div>
                              {source.relevance && (
                                <span style={{
                                  padding: '0.25rem 0.75rem',
                                  borderRadius: '9999px',
                                  fontSize: '0.75rem',
                                  fontWeight: '600',
                                  background: source.relevance > 0.7 ? '#dcfce7' : 
                                           source.relevance > 0.4 ? '#fef9c3' : '#ffedd5',
                                  color: source.relevance > 0.7 ? '#166534' :
                                         source.relevance > 0.4 ? '#854d0e' : '#9a3412'
                                }}>
                                  {Math.round(source.relevance * 100)}%
                                </span>
                              )}
                            </div>
                            {source.text && (
                              <div style={{
                                color: '#4b5563',
                                lineHeight: 1.5
                              }}>
                                {source.text}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {/* Typing Indicator */}
          {isTyping && (
            <div style={{
              display: 'flex',
              marginBottom: '1rem',
              justifyContent: 'flex-start'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '1rem 1.5rem',
                background: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '0.75rem',
                maxWidth: '5rem',
                boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
              }}>
                <div style={{
                  width: '0.5rem',
                  height: '0.5rem',
                  background: '#9ca3af',
                  borderRadius: '50%',
                  animation: 'typingPulse 1.4s infinite ease-in-out'
                }}></div>
                <div style={{
                  width: '0.5rem',
                  height: '0.5rem',
                  background: '#9ca3af',
                  borderRadius: '50%',
                  animation: 'typingPulse 1.4s infinite ease-in-out 0.2s'
                }}></div>
                <div style={{
                  width: '0.5rem',
                  height: '0.5rem',
                  background: '#9ca3af',
                  borderRadius: '50%',
                  animation: 'typingPulse 1.4s infinite ease-in-out 0.4s'
                }}></div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <div style={{
          background: 'white',
          borderTop: '1px solid #e5e7eb',
          padding: '1.5rem'
        }}>
          <form onSubmit={handleSubmit} style={{
            display: 'flex',
            gap: '1rem',
            position: 'relative'
          }}>
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your documents..."
              style={{
                flex: 1,
                minHeight: '3.5rem',
                maxHeight: '8rem',
                padding: '1rem 3.5rem 1rem 1rem',
                border: '2px solid #e5e7eb',
                borderRadius: '0.75rem',
                fontSize: '0.95rem',
                lineHeight: 1.5,
                resize: 'none',
                transition: 'border-color 0.2s ease',
                fontFamily: 'inherit',
                outline: 'none'
              }}
              disabled={isLoading || !sessionId}
              rows={1}
            />
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim() || !sessionId}
              style={{
                position: 'absolute',
                right: '0.5rem',
                bottom: '0.5rem',
                width: '2.5rem',
                height: '2.5rem',
                background: '#4f46e5',
                border: 'none',
                borderRadius: '0.5rem',
                color: 'white',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease'
              }}
            >
              <PaperAirplaneIcon style={{ width: '1.25rem', height: '1.25rem' }} />
            </button>
          </form>
          
          <div style={{
            marginTop: '0.75rem',
            textAlign: 'center',
            fontSize: '0.75rem',
            color: '#6b7280'
          }}>
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;`;

  fs.writeFileSync(path.join(frontendDir, 'src', 'components', 'chat', 'ChatInterface.tsx'), chatInterfaceTsx);

  // Create DocumentUploader.tsx with proper error handling
  const documentUploaderTsx = `import React, { useState, useRef } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { CloudArrowUpIcon } from '@heroicons/react/24/outline';

interface ProgressEvent {
  loaded: number;
  total?: number;
}

interface UploadConfig {
  headers: {
    'Content-Type': string;
  };
  onUploadProgress?: (progressEvent: ProgressEvent) => void;
}

interface DocumentUploaderProps {
  sessionId: string;
  onUploadComplete: () => void;
  onError: (message: string) => void;
}

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({ 
  sessionId, 
  onUploadComplete,
  onError
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0 || !sessionId) {
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setProcessingStatus('Starting upload...');

    const formData = new FormData();
    formData.append('session_id', sessionId);
    
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      // Step 1: Upload files
      setProcessingStatus('📤 Uploading files to server...');
      const uploadResponse = await axios.post(\`\${API_BASE_URL}/api/documents/upload\`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent: any) => {
          const total = progressEvent.total || 100;
          const percentCompleted = Math.round(
            (progressEvent.loaded * 30) / total
          );
          setUploadProgress(percentCompleted);
        },
        timeout: 60000,
      });
      
      console.log('Upload response:', uploadResponse.data);
      setUploadProgress(35);
      setProcessingStatus('📄 Files uploaded! Starting processing...');
      
      // Step 2: Process documents
      setProcessingStatus('🧠 Step 1: Extracting text from documents...');
      
      const processData = { 
        session_id: sessionId
      };
      
      const processResponse = await axios.post(
        \`\${API_BASE_URL}/api/documents/process\`,
        processData,
        {
          headers: {
            'Content-Type': 'application/json',
          },
          timeout: 300000,
        }
      );
      
      console.log('Process response:', processResponse.data);
      setUploadProgress(100);
      setProcessingStatus('🎉 Processing complete! Ready for chat.');
      
      const responseData = processResponse.data;
      const chunks = responseData.total_chunks || 0;
      const processedFiles = responseData.processed_files || files.length;
      
      toast.success(\`✅ \${processedFiles} documents processed! \${chunks} text chunks created.\`);
      
      setTimeout(() => {
        onUploadComplete();
      }, 1000);
      
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
    } catch (error: any) {
      console.error('Error uploading/processing documents:', error);
      
      let errorMessage = 'Failed to upload or process documents';
      
      if (error.response?.status === 422) {
        errorMessage = 'Invalid request format. Please check your files and try again.';
        console.error('422 Error details:', error.response.data);
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error during processing. Check if backend services are running.';
      } else if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          errorMessage = detail.map((item: any) => {
            if (typeof item === 'string') return item;
            if (item.msg) return \`\${item.loc?.join('.')}: \${item.msg}\`;
            return 'Validation error';
          }).join(', ');
        }
      } else if (error.request) {
        errorMessage = 'No response from server. Check if backend is running on http://localhost:8000';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Request timeout. Large files may take longer to process.';
      }
      
      toast.error(errorMessage);
      onError(errorMessage);
    } finally {
      setIsUploading(false);
      setProcessingStatus(null);
    }
  };

  return (
    <div>
      {/* Upload Area */}
      <div style={{
        border: '2px dashed #d1d5db',
        borderRadius: '0.75rem',
        padding: '2rem',
        textAlign: 'center',
        transition: 'all 0.3s ease',
        background: '#f9fafb'
      }}>
        <input
          ref={fileInputRef}
          type="file"
          id="file-upload"
          multiple
          onChange={handleFileChange}
          accept=".pdf,.txt,.doc,.docx"
          style={{ display: 'none' }}
          disabled={isUploading || !sessionId}
        />
        <label
          htmlFor="file-upload"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '1rem',
            cursor: isUploading || !sessionId ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            opacity: isUploading || !sessionId ? 0.5 : 1
          }}
        >
          <CloudArrowUpIcon style={{
            width: '3rem',
            height: '3rem',
            color: '#4f46e5'
          }} />
          <span style={{
            fontSize: '1.125rem',
            fontWeight: '600',
            color: '#374151'
          }}>
            {isUploading ? 'Processing...' : 'Click to select files or drag and drop'}
          </span>
          <span style={{
            fontSize: '0.875rem',
            color: '#6b7280'
          }}>
            PDF, Word documents, and text files supported
          </span>
        </label>
      </div>

      {/* Progress */}
      {isUploading && (
        <div style={{ marginTop: '1.5rem' }}>
          <div style={{
            width: '100%',
            height: '0.5rem',
            background: '#e5e7eb',
            borderRadius: '9999px',
            overflow: 'hidden'
          }}>
            <div
              style={{
                height: '100%',
                background: 'linear-gradient(90deg, #4f46e5, #6366f1)',
                borderRadius: '9999px',
                transition: 'width 0.3s ease',
                width: \`\${uploadProgress}%\`
              }}
            />
          </div>
          <p style={{
            textAlign: 'center',
            fontSize: '0.875rem',
            color: '#4b5563',
            fontWeight: '500',
            marginTop: '0.75rem'
          }}>
            {processingStatus || \`Processing: \${uploadProgress}%\`}
          </p>
        </div>
      )}

      {/* Info */}
      <div style={{
        marginTop: '2rem',
        background: '#eff6ff',
        border: '1px solid #dbeafe',
        borderRadius: '0.5rem',
        padding: '1rem'
      }}>
        <h4 style={{
          fontSize: '0.875rem',
          fontWeight: '600',
          color: '#1e40af',
          marginBottom: '0.5rem'
        }}>
          📋 What happens when you upload:
        </h4>
        <ul style={{
          listStyle: 'none',
          padding: 0,
          margin: 0,
          display: 'flex',
          flexDirection: 'column',
          gap: '0.25rem'
        }}>
          <li style={{ fontSize: '0.875rem', color: '#1e40af' }}>
            📄 <strong>PDF documents</strong> - Text extracted and processed
          </li>
          <li style={{ fontSize: '0.875rem', color: '#1e40af' }}>
            📝 <strong>Text files (.txt)</strong> - Content directly processed
          </li>
          <li style={{ fontSize: '0.875rem', color: '#1e40af' }}>
            📃 <strong>Word documents (.doc, .docx)</strong> - Text extracted and processed
          </li>
          <li style={{ fontSize: '0.875rem', color: '#1e40af' }}>
            🧠 <strong>AI Processing</strong> - Creates embeddings for intelligent search
          </li>
        </ul>
      </div>
    </div>
  );
};

export default DocumentUploader;`;

  fs.writeFileSync(path.join(frontendDir, 'src', 'components', 'documents', 'DocumentUploader.tsx'), documentUploaderTsx);

  // Return to the original directory
  process.chdir(__dirname);
  
  console.log('✅ Frontend setup completed successfully!');
  console.log('');
  console.log('To start the frontend:');
  console.log('  cd frontend');
  console.log('  npm start');
  
} catch (error) {
  console.error('❌ Error during frontend setup:', error);
  console.error('');
  console.error('Manual fix instructions:');
  console.error('1. Navigate to the frontend directory: cd frontend');
  console.error('2. Delete node_modules folder if it exists');
  console.error('3. Install react-scripts explicitly: npm install react-scripts --save');
  console.error('4. Install all dependencies: npm install --force');
  process.exit(1);
}
