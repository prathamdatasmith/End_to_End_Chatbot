import { useState } from 'react';
import axios from 'axios';

interface UploadResponse {
  success: boolean;
  message: string;
  total_chunks?: number;
  processed_files?: number;
  chunks_count?: number;
  files?: string[];
  upload_complete?: boolean;
  processed?: boolean;
}

export const useDocumentService = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const uploadDocument = async (file: File, sessionId?: string): Promise<UploadResponse> => {
    setIsUploading(true);
    setError(null);

    try {
      console.log('🚀 Starting document upload:', file.name, 'Session:', sessionId);
      
      if (!sessionId) {
        throw new Error('Session ID is required for document upload');
      }
      
      // Create FormData with exact backend format
      const formData = new FormData();
      
      // IMPORTANT: Backend expects 'files' as array, so append each file individually
      formData.append('files', file, file.name);
      formData.append('session_id', sessionId);

      console.log('📤 Uploading to:', `${API_BASE_URL}/api/documents/upload`);
      console.log('📤 FormData contents:');
      console.log('  - files:', file.name, file.type, file.size);
      console.log('  - session_id:', sessionId);
      
      // The backend now handles both upload AND processing in one step
      const response = await axios.post(
        `${API_BASE_URL}/api/documents/upload`,
        formData,
        {
          headers: {
            // Don't set Content-Type manually - let browser set it with boundary
            'Accept': 'application/json',
          },
          timeout: 300000, // 5 minutes for processing
          // Add upload progress tracking
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              console.log(`Upload progress: ${percentCompleted}%`);
            }
          }
        }
      );

      console.log('✅ Upload and processing successful:', response.data);

      // Handle different response formats from backend
      const responseData = response.data;
      
      return {
        success: responseData.success !== false, // Default to true if not explicitly false
        message: responseData.message || 'Document uploaded and processed successfully',
        total_chunks: responseData.total_chunks || responseData.chunks_count || 0,
        processed_files: responseData.processed_files || 1,
        chunks_count: responseData.total_chunks || responseData.chunks_count || 0,
        files: responseData.files || [file.name],
        upload_complete: responseData.upload_complete !== false,
        processed: responseData.processed !== false
      };

    } catch (err: any) {
      console.error('💥 Document service error:', err);
      console.error('💥 Error details:', {
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        headers: err.response?.headers
      });
      
      let errorMessage = 'Failed to upload document';
      
      if (err.response?.status === 422) {
        const details = err.response.data?.detail;
        console.error('422 Validation Error Details:', details);
        
        if (Array.isArray(details)) {
          // Handle FastAPI validation errors
          const fieldErrors = details.map(d => {
            const field = Array.isArray(d.loc) ? d.loc.join('.') : 'unknown';
            return `${field}: ${d.msg || d.type || 'validation error'}`;
          });
          errorMessage = `Validation error: ${fieldErrors.join(', ')}`;
        } else if (typeof details === 'string') {
          errorMessage = `Validation error: ${details}`;
        } else {
          errorMessage = 'Invalid file format or request structure. Please check file type and size.';
        }
      } else if (err.response?.status === 413) {
        errorMessage = 'File too large. Please try a smaller file.';
      } else if (err.response?.status === 415) {
        errorMessage = 'Unsupported file type. Please use PDF, TXT, DOC, or DOCX files.';
      } else if (err.response?.status === 500) {
        const serverError = err.response.data?.detail || 'Server error during processing';
        errorMessage = `Server error: ${serverError}`;
      } else if (err.response?.status === 404) {
        errorMessage = 'Session not found. Please refresh the page and try again.';
      } else if (err.response?.status === 400) {
        const badRequestError = err.response.data?.detail || 'Bad request';
        errorMessage = `Request error: ${badRequestError}`;
      } else if (err.code === 'ECONNABORTED') {
        errorMessage = 'Upload timeout - file may be too large or server is overloaded';
      } else if (err.code === 'ECONNREFUSED') {
        errorMessage = 'Cannot connect to backend server. Please check if it\'s running on http://localhost:8000';
      } else if (err.code === 'NETWORK_ERROR' || !err.response) {
        errorMessage = 'Network error - cannot connect to server';
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  return {
    uploadDocument,
    isUploading,
    error,
  };
};
