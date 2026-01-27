/**
 * KnowledgeBaseSelector component - select a knowledge base
 */

import { useQuery } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';
import { listKnowledgeBases } from '@/services/knowledgeBase';
import { Select } from '@/components/common/Select';

interface KnowledgeBaseSelectorProps {
  value: string;
  onChange: (kbId: string) => void;
  error?: string;
  showVersion?: boolean;
  versionValue?: number;
  onVersionChange?: (version: number) => void;
}

export function KnowledgeBaseSelector({
  value,
  onChange,
  error,
  showVersion = false,
  versionValue,
  onVersionChange,
}: KnowledgeBaseSelectorProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['knowledge-bases'],
    queryFn: listKnowledgeBases,
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-slate-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">Loading knowledge bases...</span>
      </div>
    );
  }

  if (!data || data.knowledge_bases.length === 0) {
    return (
      <div className="text-sm text-slate-400 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
        <p>No knowledge bases available. Create one from the Knowledge Base Manager.</p>
      </div>
    );
  }

  const options = data.knowledge_bases.map((kb) => ({
    value: kb.id,
    label: `${kb.name} (${kb.file_count} files, v${kb.current_version})`,
  }));

  // Get selected KB for version selector
  const selectedKB = data.knowledge_bases.find((kb) => kb.id === value);

  return (
    <div className="space-y-2">
      <Select
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          // Reset version when KB changes
          if (onVersionChange) {
            const newKB = data.knowledge_bases.find((kb) => kb.id === e.target.value);
            if (newKB) {
              onVersionChange(newKB.current_version);
            }
          }
        }}
        options={options}
        error={error}
      />
      
      {showVersion && selectedKB && onVersionChange && (
        <div className="space-y-1">
          <label className="block text-xs font-medium text-slate-400">
            Version (optional, defaults to current)
          </label>
          <input
            type="number"
            value={versionValue || selectedKB.current_version}
            onChange={(e) => {
              const version = parseInt(e.target.value, 10);
              if (!isNaN(version) && version > 0) {
                onVersionChange(version);
              }
            }}
            min={1}
            placeholder={`Current: v${selectedKB.current_version}`}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all text-sm"
          />
        </div>
      )}
    </div>
  );
}

