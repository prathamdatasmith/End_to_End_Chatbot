import { useState, useCallback } from 'react';
import axios from 'axios';

const API_BASE_URL = window.env?.REACT_APP_API_URL || 'http://localhost:8000';

interface UploadResponse {
  success: boolean;
  message: string;
  files: string[];
  session_id: string;
  upload_complete: boolean;
  processed: boolean;
  processed_files: number;
  total_chunks: number;
  errors?: string[];
}

export const useDocumentService = () => {
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);

  const uploadDocument = useCallback(
    async (file: File, sessionId: string): Promise<UploadResponse> => {
      try {
        setError(null);
        setIsUploading(true);

        // Create FormData exactly as backend expects
        const formData = new FormData();
        formData.append('files', file); // Backend expects 'files' (not 'file')
        formData.append('session_id', sessionId); // Required session_id

        console.log('Uploading file:', file.name, 'for session:', sessionId);

        const response = await axios.post(
          `${API_BASE_URL}/api/documents/upload`,
          formData,
          {
            headers: {
              // Don't set Content-Type manually - let browser set it with boundary
            },
            timeout: 300000, // 5 minutes for large files
          }
        );

        return response.data as UploadResponse;
      } catch (err: any) {
        let errorMessage = 'Upload failed';

        if (err.response?.status === 422) {
          const details = err.response.data?.detail;
          if (Array.isArray(details)) {
            errorMessage = `Validation error: ${details.map((d: any) => d.msg).join(', ')}`;
          } else {
            errorMessage = `Validation error: ${details || 'Invalid request format'}`;
          }
        } else if (err.response?.data?.detail) {
          errorMessage = err.response.data.detail;
        } else if (err.message) {
          errorMessage = err.message;
        }

        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setIsUploading(false);
      }
    },
    []
  );

  const getCollectionInfo = useCallback(
    async (): Promise<any> => {
      try {
        setError(null);
        const response = await axios.get(`${API_BASE_URL}/api/documents/collection/info`);
        return response.data;
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
    uploadDocument,
    getCollectionInfo,
    isUploading,
    error,
  };
};
