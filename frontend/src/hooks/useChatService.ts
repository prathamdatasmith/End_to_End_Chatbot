import { useState, useCallback } from 'react';
import axios from 'axios';

// API base URL - adjust as needed for your environment
const API_BASE_URL = window.env?.REACT_APP_API_URL || 'http://localhost:8000';

interface AskQuestionParams {
  question: string;
  session_id: string;
}

interface AskQuestionResponse {
  answer: string;
  sources: Array<{
    filename?: string;
    page_number?: number;
    text?: string;
    relevance?: number;
  }>;
  confidence: number;
  search_method: string;
}

interface CreateSessionResponse {
  session_id: string;
  status: string;
}

export const useChatService = () => {
  const [error, setError] = useState<string | null>(null);

  const askQuestion = useCallback(
    async (params: AskQuestionParams): Promise<AskQuestionResponse> => {
      try {
        setError(null);
        // Updated endpoint to match backend route
        const response = await axios.post(
          `${API_BASE_URL}/api/chat/ask`,
          params
        );
        return response.data as AskQuestionResponse;
      } catch (err) {
        const errorMessage = err instanceof Error 
          ? err.message 
          : 'An unknown error occurred';
        setError(errorMessage);
        throw err;
      }
    },
    []
  );

  const createSession = useCallback(
    async (): Promise<CreateSessionResponse> => {
      try {
        setError(null);
        // Updated endpoint to match backend route
        const response = await axios.post(`${API_BASE_URL}/api/chat/sessions`);
        return response.data as CreateSessionResponse;
      } catch (err) {
        const errorMessage = err instanceof Error 
          ? err.message 
          : 'An unknown error occurred';
        setError(errorMessage);
        throw err;
      }
    },
    []
  );

  return {
    askQuestion,
    createSession,
    error,
  };
};
