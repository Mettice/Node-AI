/**
 * FileUploadModal - modal for uploading and managing files
 */

import { useState } from 'react';
import { createPortal } from 'react-dom';
import { X, Upload } from 'lucide-react';
import { FileUpload } from './FileUpload';
import { FileList } from './FileList';
import { useQueryClient } from '@tanstack/react-query';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onFileSelected?: (fileId: string) => void;
}

export function FileUploadModal({ isOpen, onClose, onFileSelected }: FileUploadModalProps) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'upload' | 'list'>('upload');

  const handleFileUploaded = (fileId: string) => {
    // Refresh file list
    queryClient.invalidateQueries({ queryKey: ['files'] });
    // Switch to list tab
    setActiveTab('list');
    // Notify parent if callback provided
    onFileSelected?.(fileId);
  };

  if (!isOpen) return null;

  const modalContent = (
    <div 
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div 
        className="glass-strong rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col border border-white/20"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Upload className="w-5 h-5 text-purple-400" />
            <h2 className="text-lg font-semibold text-white">File Manager</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="px-4 pt-3 border-b border-white/10 flex gap-2">
          <button
            onClick={() => setActiveTab('upload')}
            className={activeTab === 'upload' 
              ? 'px-4 py-2 text-sm font-medium text-purple-400 border-b-2 border-purple-400'
              : 'px-4 py-2 text-sm font-medium text-slate-400 hover:text-slate-200'
            }
          >
            Upload
          </button>
          <button
            onClick={() => setActiveTab('list')}
            className={activeTab === 'list'
              ? 'px-4 py-2 text-sm font-medium text-purple-400 border-b-2 border-purple-400'
              : 'px-4 py-2 text-sm font-medium text-slate-400 hover:text-slate-200'
            }
          >
            Files ({queryClient.getQueryData<{ total: number }>(['files'])?.total || 0})
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'upload' ? (
            <FileUpload onFileUploaded={handleFileUploaded} />
          ) : (
            <FileList onSelectFile={onFileSelected} />
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}

