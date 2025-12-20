/**
 * Node category component - displays a collapsible category section
 */

import { ChevronRight } from 'lucide-react';
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
    <div className="mb-1">
      {/* Category header with colored left border */}
      <button
        onClick={onToggle}
        className={cn(
          "w-full flex items-center justify-between px-3 py-2.5 rounded-lg",
          "hover:bg-white/5 transition-all duration-200",
          "border-l-4",
          isExpanded && "bg-white/[0.03]"
        )}
        style={{ 
          borderLeftColor: categoryColor,
        }}
      >
        <div className="flex items-center gap-2.5">
          {/* Colored icon indicator */}
          <div 
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: categoryColor }}
          />
          <span
            className="text-sm font-semibold tracking-wide"
            style={{ color: categoryColor }}
          >
            {categoryLabel}
          </span>
          <span className="text-xs text-slate-500 bg-white/5 px-1.5 py-0.5 rounded">
            {nodes.length}
          </span>
        </div>
        <div 
          className="transition-transform duration-200"
          style={{ transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}
        >
          <ChevronRight className="w-4 h-4 text-slate-400" />
        </div>
      </button>

      {/* Category nodes with animation */}
      <div 
        className={cn(
          "overflow-hidden transition-all duration-200 ease-out",
          isExpanded ? "max-h-[1000px] opacity-100" : "max-h-0 opacity-0"
        )}
      >
        <div className="ml-4 mt-1 space-y-1 pb-1">
          {nodes.map((node, index) => (
            <NodeCard key={`${node.type}-${index}`} node={node} />
          ))}
        </div>
      </div>
    </div>
  );
}

