import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PaperAirplaneIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { ChatMessage } from './ChatMessage';
import { TypingIndicator } from './TypingIndicator';
import { DocumentUploader } from '../documents/DocumentUploader';
import { useChatService } from '../../hooks/useChatService';
import { Message } from '../../types/chat';
import toast from 'react-hot-toast';

interface ChatInterfaceProps {
  sessionId: string;
  onSessionChange: (sessionId: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  onSessionChange
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showUploader, setShowUploader] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  const { askQuestion, createSession } = useChatService();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await askQuestion({
        question: inputValue,
        session_id: sessionId
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.answer,
        role: 'assistant',
        timestamp: new Date(),
        sources: response.sources,
        confidence: response.confidence,
        searchMethod: response.search_method
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Show confidence feedback
      if (response.confidence > 0.8) {
        toast.success(`High confidence answer (${(response.confidence * 100).toFixed(0)}%)`);
      } else if (response.confidence < 0.4) {
        toast.error(`Low confidence answer (${(response.confidence * 100).toFixed(0)}%)`);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message. Please try again.');
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        role: 'assistant',
        timestamp: new Date(),
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewSession = async () => {
    try {
      const response = await createSession();
      onSessionChange(response.session_id);
      setMessages([]);
      toast.success('New session created');
    } catch (error) {
      toast.error('Failed to create new session');
    }
  };

  const clearChat = () => {
    setMessages([]);
    toast.success('Chat cleared');
  };
  
  const toggleUploader = () => {
    setShowUploader(!showUploader);
  };

  const handleUploadComplete = () => {
    toast.success('All documents processed successfully');
    setShowUploader(false);
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
            <span className="text-sm font-bold">🤖</span>
          </div>
          <div>
            <h2 className="text-lg font-semibold">RAG Chatbot</h2>
            <p className="text-xs opacity-80">Session: {sessionId.slice(0, 8)}...</p>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={toggleUploader}
            className="p-2 bg-white bg-opacity-20 rounded-lg hover:bg-opacity-30 transition-colors"
            title="Upload Documents"
          >
            📄
          </button>
          <button
            onClick={handleNewSession}
            className="p-2 bg-white bg-opacity-20 rounded-lg hover:bg-opacity-30 transition-colors"
            title="New Session"
          >
            <ArrowPathIcon className="w-5 h-5" />
          </button>
          <button
            onClick={clearChat}
            className="p-2 bg-white bg-opacity-20 rounded-lg hover:bg-opacity-30 transition-colors"
            title="Clear Chat"
          >
            🗑️
          </button>
        </div>
      </div>

      {/* Document Uploader */}
      {showUploader && (
        <div className="p-4 border-b">
          <DocumentUploader 
            sessionId={sessionId}
            onUploadComplete={handleUploadComplete} 
            onError={(error) => toast.error(`Upload failed: ${error}`)}
          />
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center py-12"
            >
              <div className="text-6xl mb-4">💬</div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                Welcome to RAG Chatbot
              </h3>
              <p className="text-gray-500 max-w-md mx-auto">
                Upload your PDF documents and start asking questions. I'll help you find
                relevant information using advanced AI and semantic search.
              </p>
              <button
                onClick={toggleUploader}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Upload Documents
              </button>
            </motion.div>
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}
        </AnimatePresence>

        {isLoading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-gray-50 border-t">
        <div className="flex space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your documents..."
              className="w-full p-3 pr-12 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={1}
              style={{ minHeight: '50px', maxHeight: '120px' }}
              disabled={isLoading}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="absolute right-2 bottom-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              <PaperAirplaneIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
        
        <div className="mt-2 text-xs text-gray-500 text-center">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
};
