import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Message } from '../../types/chat';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [showSources, setShowSources] = useState(false);
  
  const isUser = message.role === 'user';
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-3xl rounded-lg p-4 ${
          isUser 
            ? 'bg-blue-600 text-white rounded-br-none' 
            : 'bg-gray-100 text-gray-800 rounded-bl-none'
        } ${message.isError ? 'bg-red-100 border border-red-300' : ''}`}
      >
        {/* Message content with markdown formatting */}
        <div className="prose prose-sm">
          {message.content}
        </div>
        
        {/* Sources section */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3">
            <button
              onClick={() => setShowSources(!showSources)}
              className="text-xs flex items-center font-medium text-blue-700 hover:underline"
            >
              {showSources ? 'Hide sources' : 'Show sources'} ({message.sources.length})
            </button>
            
            {showSources && (
              <div className="mt-2 text-xs border-t border-gray-200 pt-2">
                <p className="font-medium mb-1">Sources:</p>
                <ul className="space-y-1">
                  {message.sources.map((source, idx) => (
                    <li key={idx} className="bg-white p-2 rounded border border-gray-200">
                      {source.filename && (
                        <p className="font-medium">{source.filename} {source.page_number ? `(Page ${source.page_number})` : ''}</p>
                      )}
                      {source.text && (
                        <p className="mt-1 text-gray-600 line-clamp-2">{source.text}</p>
                      )}
                      {source.relevance !== undefined && (
                        <p className="text-gray-400 mt-1">Relevance: {(source.relevance * 100).toFixed(0)}%</p>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        
        {/* Metadata section */}
        {!isUser && (
          <div className="mt-2 text-xs text-gray-500 flex items-center">
            <span>
              {message.confidence !== undefined && 
                `Confidence: ${(message.confidence * 100).toFixed(0)}% · `}
              {message.searchMethod && `Method: ${message.searchMethod}`}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
};

// Add this at the end to make it a module
export {};