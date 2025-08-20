import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { v4 as uuidv4 } from 'uuid';
import { ChatInterface } from './components/chat/ChatInterface';
import './App.css';

const App: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>('');

  useEffect(() => {
    // Create or retrieve a session ID when the app first loads
    const existingSessionId = localStorage.getItem('chatSessionId');
    if (existingSessionId) {
      setSessionId(existingSessionId);
    } else {
      const newSessionId = uuidv4();
      localStorage.setItem('chatSessionId', newSessionId);
      setSessionId(newSessionId);
    }
  }, []);

  const handleSessionChange = (newSessionId: string) => {
    localStorage.setItem('chatSessionId', newSessionId);
    setSessionId(newSessionId);
  };

  return (
    <div
      className="h-screen w-screen flex flex-col"
      style={{ minHeight: '100vh', minWidth: '100vw', margin: 0, padding: 0, boxSizing: 'border-box' }}
    >
      <Toaster position="top-right" />
      {/* Remove the outer header, only render ChatInterface */}
      <main className="flex-1 flex flex-col overflow-hidden" style={{ flex: '1 1 0%', minHeight: 0 }}>
        {sessionId ? (
          <ChatInterface
            sessionId={sessionId}
            onSessionChange={handleSessionChange}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center text-lg text-gray-500">
            Loading session...
          </div>
        )}
      </main>
    </div>
  );
};

export default App;