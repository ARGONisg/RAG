import { UploadCloud, FileType } from "lucide-react";
import { useState, useRef } from "react";

interface FileUploadProps {
  onUploadSuccess: (filename: string, chunksIndexed: number) => void;
  onCancel?: () => void;
}

export function FileUpload({ onUploadSuccess, onCancel }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const processFile = async (file: File) => {
    const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt', '.md', '.csv'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
      setError("Please upload a supported document.");
      return;
    }

    setError(null);
    setIsUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/api/v1/documents/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();
      if (data.status === "success") {
        onUploadSuccess(data.filename, data.chunks_indexed);
      } else {
        throw new Error("Upload returned unexpected status");
      }
    } catch (err) {
      setError("Couldn't upload the document. Please check the file and try again.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-surface-02 border-2 border-dashed border-border-subtle rounded-xl max-w-md w-full mx-auto">
      {isUploading ? (
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <h3 className="text-lg font-medium text-text-primary">Uploading...</h3>
          <p className="text-sm text-text-secondary mt-2">Please wait while your document is being processed.</p>
        </div>
      ) : (
        <div 
          className="relative text-center w-full h-full flex flex-col items-center justify-center"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {isDragging && (
            <div className="absolute inset-[-2rem] z-10 flex flex-col items-center justify-center bg-surface-02/95 backdrop-blur-md rounded-xl border-2 border-primary border-dashed transition-all duration-200">
              <UploadCloud className="text-primary mb-4 animate-bounce" size={48} />
              <p className="text-primary font-semibold text-xl">Drop document here</p>
            </div>
          )}
          <UploadCloud className="mx-auto text-primary mb-4" size={48} />
          <h3 className="text-xl font-medium text-text-primary mb-2">Upload a Document</h3>
          <p className="text-sm text-text-secondary mb-6">Drag and drop your document here or click below to browse.</p>
          
          <input 
            type="file" 
            accept=".pdf,.doc,.docx,.txt,.md,.csv" 
            className="hidden" 
            ref={fileInputRef} 
            onChange={handleFileChange}
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="bg-surface-03 hover:bg-border-subtle text-text-primary border border-border-subtle px-6 py-2 rounded-lg font-medium transition-colors mb-2 w-full"
          >
            Choose File
          </button>
          {onCancel && (
            <button onClick={onCancel} className="text-sm text-text-muted hover:text-text-primary mt-4">
              Cancel
            </button>
          )}
          {error && (
            <div className="mt-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg relative z-20">
              <p className="text-sm font-semibold text-red-400 mb-1">Unsupported file type</p>
              <p className="text-xs text-red-300">{error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
