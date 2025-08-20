import React from 'react';

interface Source {
  filename?: string;
  page_number?: number;
  text?: string;
  relevance?: number;
}

interface SourceDisplayProps {
  sources: Source[];
}

export const SourceDisplay: React.FC<SourceDisplayProps> = ({ sources }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-2 text-xs border-t border-gray-200 pt-2">
      <p className="font-medium mb-1">Sources:</p>
      <ul className="space-y-1">
        {sources.map((source, idx) => (
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
  );
};

// Add this at the end to make it a module
export {};