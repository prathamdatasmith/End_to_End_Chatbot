import React, { useState } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Message } from '../../types/chat';

interface ChatMessageProps {
  message: Message;
}

const CopyButton: React.FC<{ code: string }> = ({ code }) => {
  const [copied, setCopied] = useState(false);
  return (
    <button
      className="absolute top-2 right-2 px-2 py-1 text-xs bg-gray-700 text-white rounded hover:bg-gray-900 transition"
      onClick={() => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 1200);
      }}
      title="Copy code"
      type="button"
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
};

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
        className={`max-w-3xl rounded-lg p-4 relative ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-gray-100 text-gray-800 rounded-bl-none'
        } ${message.isError ? 'bg-red-100 border border-red-300' : ''}`}
      >
        {/* Markdown content */}
        <div className="prose prose-sm max-w-none break-words">
          {isUser ? (
            message.content
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const codeString = String(children).replace(/\n$/, '');
                  const match = /language-(\w+)/.exec(className || '');
                  if (!inline && match) {
                    return (
                      <div className="relative group">
                        <SyntaxHighlighter
                          style={vscDarkPlus}
                          language={match[1]}
                          PreTag="div"
                          customStyle={{ borderRadius: '0.5rem', fontSize: '0.95em', margin: 0 }}
                          {...props}
                        >
                          {codeString}
                        </SyntaxHighlighter>
                        <CopyButton code={codeString} />
                      </div>
                    );
                  }
                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
                table({ children }) {
                  return (
                    <div className="overflow-x-auto">
                      <table className="table-auto border">{children}</table>
                    </div>
                  );
                },
                th({ children }) {
                  return <th className="border px-2 py-1 bg-gray-100">{children}</th>;
                },
                td({ children }) {
                  return <td className="border px-2 py-1">{children}</td>;
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
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
