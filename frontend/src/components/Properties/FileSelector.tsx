/**
 * FileSelector component - select an uploaded file
 */

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2, Upload } from 'lucide-react';
import { listFiles } from '@/services/files';
import { Select } from '@/components/common/Select';
import { FileUploadModal } from '@/components/Files/FileUploadModal';

interface FileSelectorProps {
  value: string;
  onChange: (fileId: string) => void;
  error?: string;
}

export function FileSelector({ value, onChange, error }: FileSelectorProps) {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const queryClient = useQueryClient();
  
  const { data, isLoading } = useQuery({
    queryKey: ['files'],
    queryFn: listFiles,
  });

  const handleFileSelected = (fileId: string) => {
    onChange(fileId);
    setShowUploadModal(false);
    queryClient.invalidateQueries({ queryKey: ['files'] });
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-slate-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">Loading files...</span>
      </div>
    );
  }

  if (!data || data.files.length === 0) {
    return (
      <div className="space-y-2">
        <div className="text-sm text-slate-400 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
          <p className="mb-2">No files uploaded yet.</p>
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded text-sm font-medium transition-colors"
          >
            <Upload className="w-4 h-4" />
            Upload File
          </button>
        </div>
        <FileUploadModal
          isOpen={showUploadModal}
          onClose={() => setShowUploadModal(false)}
          onFileSelected={handleFileSelected}
        />
      </div>
    );
  }

  const options = data.files.map((file) => ({
    value: file.file_id,
    label: `${file.filename} (${file.file_type.toUpperCase()})`,
  }));

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <div className="flex-1">
          <Select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            options={options}
            error={error}
          />
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="px-3 py-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 rounded-lg border border-amber-500/30 transition-colors flex items-center gap-1.5 text-sm flex-shrink-0"
          title="Upload new file"
        >
          <Upload className="w-4 h-4" />
          <span>Upload</span>
        </button>
      </div>
      <FileUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onFileSelected={handleFileSelected}
      />
    </div>
  );
}

