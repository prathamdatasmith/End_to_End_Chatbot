export interface Source {
  filename?: string;
  page_number?: number;
  text?: string;
  relevance?: number;
  score?: number;
}

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  sources?: Source[];
  confidence?: number;
  searchMethod?: string;
  isError?: boolean;
}

export interface ChatSession {
  id: string;
  name: string;
  created_at: Date;
  updated_at: Date;
}
