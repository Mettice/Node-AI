/**
 * FileUpload component - drag & drop file upload with progress
 */

import { useState, useCallback } from 'react';
import { Upload, File, X, Loader2, CheckCircle2 } from 'lucide-react';
import { uploadFile, deleteFile, type FileInfo } from '@/services/files';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';

interface FileUploadProps {
  onFileUploaded: (fileId: string) => void;
  acceptedTypes?: string[];
  maxSize?: number; // in bytes
}

export function FileUpload({ 
  onFileUploaded, 
  acceptedTypes = [
    // Documents
    '.pdf', '.docx', '.txt', '.md', '.doc',
    // Images
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',
    // Audio
    '.mp3', '.wav', '.m4a', '.ogg', '.flac',
    // Video
    '.mp4', '.avi', '.mov', '.mkv', '.webm',
    // Data
    '.csv', '.xlsx', '.json', '.jsonl', '.parquet'
  ],
  maxSize = 50 * 1024 * 1024, // 50MB default
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFile = useCallback(async (file: File) => {
    // Validate file type
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!acceptedTypes.includes(fileExt)) {
      toast.error(`File type ${fileExt} not supported. Allowed: ${acceptedTypes.join(', ')}`);
      return;
    }

    // Validate file size
    if (file.size > maxSize) {
      toast.error(`File too large. Maximum size: ${(maxSize / 1024 / 1024).toFixed(0)}MB`);
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress (since we can't track actual upload progress easily)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 100);

      const result = await uploadFile(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      toast.success(`File "${file.name}" uploaded successfully!`);
      onFileUploaded(result.file_id);
      
      // Reset after a moment
      setTimeout(() => {
        setUploading(false);
        setUploadProgress(0);
      }, 1000);
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(`Failed to upload file: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setUploading(false);
      setUploadProgress(0);
    }
  }, [acceptedTypes, maxSize, onFileUploaded]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFile(files[0]); // Handle first file only
    }
  }, [handleFile]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  }, [handleFile]);

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        'relative border-2 border-dashed rounded-lg p-8 transition-all duration-200',
        isDragging
          ? 'border-amber-500 bg-amber-500/10'
          : 'border-white/20 bg-white/5 hover:border-white/30 hover:bg-white/8',
        uploading && 'pointer-events-none opacity-75'
      )}
    >
      <input
        type="file"
        id="file-upload"
        className="hidden"
        accept={acceptedTypes.join(',')}
        onChange={handleFileInput}
        disabled={uploading}
      />
      
      {uploading ? (
        <div className="flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 text-amber-400 animate-spin" />
          <div className="text-sm text-slate-300">Uploading...</div>
          <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
            <div
              className="bg-amber-500 h-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <div className="text-xs text-slate-400">{uploadProgress}%</div>
        </div>
      ) : (
        <label
          htmlFor="file-upload"
          className="flex flex-col items-center justify-center gap-3 cursor-pointer"
        >
          <div className={cn(
            'p-4 rounded-full transition-all duration-200',
            isDragging
              ? 'bg-amber-500/20 text-amber-400'
              : 'bg-white/10 text-slate-400 hover:bg-white/15 hover:text-amber-400'
          )}>
            <Upload className="w-8 h-8" />
          </div>
          <div className="text-center">
            <div className="text-sm font-semibold text-slate-200 mb-1">
              {isDragging ? 'Drop file here' : 'Click to upload or drag and drop'}
            </div>
            <div className="text-xs text-slate-400">
              {acceptedTypes.join(', ').toUpperCase()} (max {(maxSize / 1024 / 1024).toFixed(0)}MB)
            </div>
          </div>
        </label>
      )}
    </div>
  );
}

