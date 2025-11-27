/**
 * Process Knowledge Base Modal
 * 
 * Allows selecting files and configuring processing options
 */

import { useState, useEffect, useRef } from 'react';
import { X, Upload, FileText, Loader2, Plus } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { listFiles, uploadFile } from '@/services/files';
import {
  processKnowledgeBase,
  getKnowledgeBase,
  type ProcessKnowledgeBaseRequest,
} from '@/services/knowledgeBase';
import toast from 'react-hot-toast';

interface ProcessKnowledgeBaseModalProps {
  kbId: string;
  isOpen: boolean;
  onClose: () => void;
  onProcessed: () => void;
}

export function ProcessKnowledgeBaseModal({
  kbId,
  isOpen,
  onClose,
  onProcessed,
}: ProcessKnowledgeBaseModalProps) {
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);
  const [createNewVersion, setCreateNewVersion] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [useCustomConfig, setUseCustomConfig] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { data: files } = useQuery({
    queryKey: ['files'],
    queryFn: listFiles,
  });


  const { data: kb } = useQuery({
    queryKey: ['knowledge-base', kbId],
    queryFn: () => getKnowledgeBase(kbId),
    enabled: isOpen && !!kbId,
  });

  useEffect(() => {
    if (!isOpen) {
      setSelectedFileIds([]);
      setCreateNewVersion(true);
      setUseCustomConfig(false);
      setProcessing(false);
      setUploading(false);
    }
  }, [isOpen]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await uploadFile(file);
      toast.success(`File "${file.name}" uploaded successfully!`);
      // Refresh file list
      queryClient.invalidateQueries({ queryKey: ['files'] });
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error: any) {
      console.error('Error uploading file:', error);
      toast.error(error.response?.data?.detail || error.message || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleProcess = async () => {
    if (selectedFileIds.length === 0) {
      toast.error('Please select at least one file to process');
      return;
    }

    setProcessing(true);
    try {
      const request: ProcessKnowledgeBaseRequest = {
        file_ids: selectedFileIds,
        create_new_version: createNewVersion,
        // Use custom configs if enabled, otherwise use KB defaults
        chunk_config: useCustomConfig ? {
          strategy: 'recursive',
          chunk_size: 512,
          chunk_overlap: 50,
          separators: [],
          min_chunk_size: 100,
          max_chunk_size: 1000,
          overlap_sentences: 1,
        } : undefined,
        embed_config: useCustomConfig ? {
          provider: 'openai',
          model: 'text-embedding-3-small',
          batch_size: 100,
          use_finetuned_model: false,
        } : undefined,
        vector_store_config: useCustomConfig ? {
          provider: 'faiss',
          index_type: 'flat',
          persist: true,
        } : undefined,
      };

      await processKnowledgeBase(kbId, request);
      toast.success('Processing started! Check the status in the detail view.');
      onProcessed();
      onClose();
    } catch (error: any) {
      console.error('Error processing knowledge base:', error);
      toast.error(error.response?.data?.detail?.message || error.message || 'Failed to start processing');
    } finally {
      setProcessing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
        onClick={onClose}
      />
      <div className="fixed inset-0 z-[101] flex items-center justify-center p-4">
        <div
          className="bg-slate-800 border border-white/10 rounded-lg shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between flex-shrink-0">
            <div>
              <h3 className="text-lg font-semibold text-white">Process Knowledge Base</h3>
              {kb && <p className="text-sm text-slate-400 mt-1">{kb.name}</p>}
            </div>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* File Selection */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium text-slate-300">
                  Select Files to Process
                </label>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="flex items-center gap-2 px-3 py-1.5 text-xs bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Plus className="w-3.5 h-3.5" />
                      Upload File
                    </>
                  )}
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileUpload}
                  className="hidden"
                  accept=".pdf,.docx,.txt,.md,.doc,.jpg,.jpeg,.png,.gif,.webp,.bmp,.mp3,.wav,.m4a,.ogg,.flac,.mp4,.avi,.mov,.mkv,.webm,.csv,.xlsx,.json,.parquet"
                />
              </div>
              {!files || (files.files?.length || 0) === 0 ? (
                <div className="text-sm text-slate-400 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                  <p className="mb-2">No files available. Click "Upload File" above to add documents.</p>
                  <p className="text-xs">Supported formats: PDF, DOCX, TXT, MD, images, audio, video, and data files.</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {(files.files || []).map((file) => (
                    <label
                      key={file.file_id}
                      className="flex items-center gap-3 p-3 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selectedFileIds.includes(file.file_id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedFileIds([...selectedFileIds, file.file_id]);
                          } else {
                            setSelectedFileIds(selectedFileIds.filter((id) => id !== file.file_id));
                          }
                        }}
                        className="w-4 h-4 text-purple-600 bg-white/5 border-white/20 rounded focus:ring-purple-500"
                      />
                      <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white truncate">{file.filename}</p>
                        <p className="text-xs text-slate-400">
                          {(file.size / 1024).toFixed(1)} KB • {file.file_type.toUpperCase()}
                        </p>
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Version Options */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-3">
                Version Options
              </label>
              <div className="space-y-2">
                <label className="flex items-center gap-3 p-3 bg-white/5 border border-white/10 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                  <input
                    type="radio"
                    checked={createNewVersion}
                    onChange={() => setCreateNewVersion(true)}
                    className="w-4 h-4 text-purple-600 bg-white/5 border-white/20 focus:ring-purple-500"
                  />
                  <div>
                    <p className="text-sm text-white">Create New Version</p>
                    <p className="text-xs text-slate-400">Keep existing version and create a new one</p>
                  </div>
                </label>
                <label className="flex items-center gap-3 p-3 bg-white/5 border border-white/10 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                  <input
                    type="radio"
                    checked={!createNewVersion}
                    onChange={() => setCreateNewVersion(false)}
                    className="w-4 h-4 text-purple-600 bg-white/5 border-white/20 focus:ring-purple-500"
                  />
                  <div>
                    <p className="text-sm text-white">Replace Current Version</p>
                    <p className="text-xs text-slate-400">Replace the current version (old version will be deprecated)</p>
                  </div>
                </label>
              </div>
            </div>

            {/* Custom Config Toggle */}
            <div>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useCustomConfig}
                  onChange={(e) => setUseCustomConfig(e.target.checked)}
                  className="w-4 h-4 text-purple-600 bg-white/5 border-white/20 rounded focus:ring-purple-500"
                />
                <span className="text-sm text-slate-300">Use custom processing configuration</span>
              </label>
              <p className="text-xs text-slate-400 mt-1 ml-7">
                {useCustomConfig
                  ? 'You can customize chunk size, embedding model, etc.'
                  : 'Uses knowledge base default configurations'}
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-white/10 flex items-center justify-end gap-3 flex-shrink-0">
            <button
              onClick={onClose}
              disabled={processing}
              className="px-4 py-2 text-sm text-slate-300 hover:text-white transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleProcess}
              disabled={processing || selectedFileIds.length === 0}
              className="px-4 py-2 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {processing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Start Processing</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

