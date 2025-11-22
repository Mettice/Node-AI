/**
 * Node category component - displays a collapsible category section
 */

import { ChevronDown, ChevronRight } from 'lucide-react';
import { NodeCard } from './NodeCard';
import { NODE_CATEGORY_COLORS } from '@/constants';
import type { NodeMetadata } from '@/types/node';
import { cn } from '@/utils/cn';

interface NodeCategoryProps {
  category: string;
  nodes: NodeMetadata[];
  isExpanded: boolean;
  onToggle: () => void;
}

const categoryLabels: Record<string, string> = {
  input: 'Input',
  processing: 'Processing',
  embedding: 'Embedding',
  storage: 'Storage',
  retrieval: 'Retrieval',
  llm: 'LLM',
  tool: 'Tool',
  memory: 'Memory',
  agent: 'Agent',
};

export function NodeCategory({ category, nodes, isExpanded, onToggle }: NodeCategoryProps) {
  const categoryColor = NODE_CATEGORY_COLORS[category as keyof typeof NODE_CATEGORY_COLORS] || '#9ca3af';
  const categoryLabel = categoryLabels[category] || category;

  return (
    <div className="mb-2">
      {/* Category header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-3 py-2 rounded-md hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          )}
          <span
            className="text-sm font-semibold"
            style={{ color: categoryColor }}
          >
            {categoryLabel}
          </span>
          <span className="text-xs text-slate-500">({nodes.length})</span>
        </div>
      </button>

      {/* Category nodes */}
      {isExpanded && (
        <div className="ml-4 mt-1 space-y-1">
          {nodes.map((node, index) => (
            <NodeCard key={`${node.type}-${index}`} node={node} />
          ))}
        </div>
      )}
    </div>
  );
}

