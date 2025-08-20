import React, { useState, useRef } from 'react';
import { useDocumentService } from '../../hooks/useDocumentService';
import toast from 'react-hot-toast';

interface DocumentUploaderProps {
  sessionId: string;
  onUploadComplete: () => void;
  onError: (message: string) => void;
}

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  sessionId,
  onUploadComplete,
  onError
}) => {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [open, setOpen] = useState(false); // Accordion state
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { uploadDocument } = useDocumentService();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const fileArray = Array.from(e.target.files);
      // Support multiple file types as backend supports
      const supportedFiles = fileArray.filter(file => 
        file.type === 'application/pdf' || 
        file.name.toLowerCase().endsWith('.pdf') ||
        file.name.toLowerCase().endsWith('.txt') ||
        file.name.toLowerCase().endsWith('.doc') ||
        file.name.toLowerCase().endsWith('.docx')
      );
      
      if (supportedFiles.length !== fileArray.length) {
        toast.error('Only PDF, TXT, DOC, and DOCX files are supported');
      }
      
      setFiles(supportedFiles);
    }
  };

  const handleUpload = async () => {
    if (files.length === 0 || !sessionId) {
      toast.error('Please select files and ensure session is active');
      return;
    }
    
    setUploading(true);
    setProgress(0);
    
    try {
      let totalProcessed = 0;
      let totalChunks = 0;
      
      // Upload files one by one
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const uploadId = `upload-${i}`;
        
        toast.loading(`Processing ${file.name}...`, { id: uploadId });
        
        try {
          const result = await uploadDocument(file, sessionId);
          
          if (result.success) {
            totalProcessed += result.processed_files || 1;
            totalChunks += result.total_chunks || 0;
            
            toast.success(
              `✅ ${file.name}: ${result.total_chunks} chunks created`, 
              { id: uploadId, duration: 3000 }
            );
          } else {
            toast.error(`❌ Failed to process ${file.name}`, { id: uploadId });
          }
        } catch (err: any) {
          console.error(`Error uploading ${file.name}:`, err);
          toast.error(`❌ Error: ${err.message}`, { id: uploadId });
          onError(err.message);
        }
        
        // Update progress
        setProgress(((i + 1) / files.length) * 100);
      }
      
      // Final success message
      if (totalProcessed > 0) {
        toast.success(
          `🎉 Processed ${totalProcessed} documents with ${totalChunks} total chunks!`,
          { duration: 5000 }
        );
        
        // Reset and callback
        setFiles([]);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        
        onUploadComplete();
      } else {
        toast.error('No documents were successfully processed');
      }
      
    } catch (error: any) {
      console.error('Upload error:', error);
      toast.error('An error occurred during upload');
      onError(error.message || 'Upload failed');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Accordion Header */}
      <button
        type="button"
        className="w-full flex items-center justify-between px-4 py-3 text-lg font-medium text-gray-800 bg-gray-100 rounded-t-lg focus:outline-none hover:bg-gray-200 transition-colors"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls="upload-accordion-content"
      >
        <span>Upload Documents</span>
        <svg
          className={`w-5 h-5 ml-2 transform transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Accordion Content */}
      <div
        id="upload-accordion-content"
        className={`overflow-hidden transition-all duration-300 ${open ? 'max-h-[1000px] py-4 px-4' : 'max-h-0 p-0'}`}
        style={{ background: open ? '#fff' : undefined }}
      >
        {open && (
          <>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center mb-3 hover:bg-gray-50 transition-colors">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                multiple
                accept=".pdf,.txt,.doc,.docx"
                className="hidden"
                id="file-upload"
                disabled={uploading || !sessionId}
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer flex flex-col items-center justify-center py-3"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-gray-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span className="text-gray-500 font-medium">
                  {uploading ? 'Processing...' : 'Click to select documents'}
                </span>
                <span className="text-sm text-gray-400 mt-1">
                  PDF, TXT, DOC, DOCX files supported
                </span>
              </label>
            </div>
            
            {!sessionId && (
              <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-3">
                <p className="text-yellow-800 text-sm">⚠️ Waiting for session to be created...</p>
              </div>
            )}
            
            {files.length > 0 && (
              <>
                <div className="mb-3">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Selected Files ({files.length})</h4>
                  <ul className="max-h-32 overflow-y-auto text-sm space-y-1">
                    {files.map((file, index) => (
                      <li key={index} className="py-1 px-2 bg-gray-50 rounded flex justify-between items-center">
                        <span className="truncate flex-1">{file.name}</span>
                        <span className="text-gray-400 text-xs ml-2">
                          {(file.size / (1024 * 1024)).toFixed(1)} MB
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
                
                {uploading && (
                  <div className="w-full bg-gray-200 rounded-full h-2.5 mb-3">
                    <div 
                      className="bg-blue-600 h-2.5 rounded-full transition-all duration-300" 
                      style={{ width: `${progress}%` }}
                    ></div>
                  </div>
                )}
                
                <button
                  onClick={handleUpload}
                  disabled={uploading || !sessionId}
                  className="w-full bg-blue-600 text-white rounded-lg px-4 py-2 font-medium hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                >
                  {uploading ? `Processing... (${Math.round(progress)}%)` : 'Upload & Process Documents'}
                </button>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};
