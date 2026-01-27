/**
 * FileList component - displays list of uploaded files
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { File, Trash2, Loader2 } from 'lucide-react';
import { listFiles, deleteFile, type FileInfo } from '@/services/files';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';

interface FileListProps {
  onSelectFile?: (fileId: string) => void;
  selectedFileId?: string;
}

export function FileList({ onSelectFile, selectedFileId }: FileListProps) {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['files'],
    queryFn: listFiles,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      toast.success('File deleted successfully');
    },
    onError: (error) => {
      toast.error(`Failed to delete file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
      </div>
    );
  }

  if (!data || data.files.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400">
        <File className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p className="text-sm">No files uploaded yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {data.files.map((file) => (
        <div
          key={file.file_id}
          className={cn(
            'flex items-center justify-between p-3 rounded-lg border transition-all cursor-pointer',
            selectedFileId === file.file_id
              ? 'bg-amber-500/20 border-amber-500/50'
              : 'bg-white/5 border-white/10 hover:bg-white/8 hover:border-white/20'
          )}
          onClick={() => onSelectFile?.(file.file_id)}
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="p-2 rounded bg-white/10 text-slate-400 flex-shrink-0">
              <File className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-slate-200 truncate">
                {file.filename}
              </div>
              <div className="text-xs text-slate-400">
                {formatFileSize(file.size)} • {file.file_type.toUpperCase()}
                {file.text_extracted && (
                  <span className="ml-2 text-green-400">✓ Extracted</span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (confirm(`Delete "${file.filename}"?`)) {
                deleteMutation.mutate(file.file_id);
              }
            }}
            className="p-1.5 rounded hover:bg-red-500/20 text-red-400 transition-colors flex-shrink-0"
            title="Delete file"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}

