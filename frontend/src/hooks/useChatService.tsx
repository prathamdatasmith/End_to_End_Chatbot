import { useState, useCallback } from 'react';
import axios from 'axios';

interface ChatRequest {
  question: string;
  session_id: string;
  conversation_context?: boolean;
}

interface Source {
  filename?: string;
  page_number?: number;
  text?: string;
  relevance?: number;
  score?: number;
}

interface ChatResponse {
  answer: string;
  sources: Source[];
  confidence: number;
  search_method: string;
}

export const useChatService = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const askQuestion = async (request: ChatRequest): Promise<ChatResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      console.log('🤔 Asking question:', request.question.substring(0, 100));
      console.log('📍 Session ID:', request.session_id);

      const response = await axios.post(
        `${API_BASE_URL}/api/chat/question`,
        {
          question: request.question,
          session_id: request.session_id,
          conversation_context: false  // Always disable conversation context
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
          timeout: 60000, // 1 minute timeout
        }
      );

      console.log('✅ Received response:', {
        answerLength: response.data.answer?.length,
        sourcesCount: response.data.sources?.length,
        confidence: response.data.confidence,
        searchMethod: response.data.search_method
      });

      return response.data;

    } catch (err: any) {
      console.error('❌ Chat service error:', err);
      
      let errorMessage = 'Failed to get response';
      
      // More specific error handling
      if (err.code === 'ECONNABORTED') {
        errorMessage = 'Request timeout - AI processing took too long. Try a simpler question.';
      } else if (err.code === 'ECONNREFUSED') {
        errorMessage = 'Cannot connect to backend - check if server is running on http://localhost:8000';
      } else if (err.response?.status === 400) {
        errorMessage = err.response.data?.detail || 'Bad request - check request format';
      } else if (err.response?.status === 404) {
        errorMessage = 'Session not found - please create a new session';
      } else if (err.response?.status === 422) {
        // Validation error - likely API format mismatch
        const details = err.response.data?.detail;
        if (Array.isArray(details)) {
          errorMessage = `API validation error: ${details.map(d => d.msg).join(', ')}`;
        } else {
          errorMessage = 'API validation error - request format mismatch';
        }
      } else if (err.response?.status === 500) {
        errorMessage = 'Server error - check backend logs for Gemini API or Qdrant issues';
      } else if (!err.response && err.request) {
        errorMessage = 'No response from server - backend may be crashed or overloaded';
      }

      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const createSession = useCallback(
    async (): Promise<{ session_id: string }> => {
      try {
        setError(null);
        const response = await axios.post(`${API_BASE_URL}/api/chat/session`);
        return response.data;
      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || err.message || 'Failed to create session';
        setError(errorMessage);
        throw new Error(errorMessage);
      }
    },
    []
  );

  return {
    askQuestion,
    createSession,
    isLoading,
    error,
  };
};
