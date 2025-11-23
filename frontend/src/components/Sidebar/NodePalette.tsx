/**
 * Node palette component - displays available nodes organized by category
 */

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronRight, Search } from 'lucide-react';
import { listNodes } from '@/services/nodes';
import { NodeCard } from './NodeCard';
import { NodeCategory } from './NodeCategory';
import type { NodeMetadata } from '@/types/node';
import { Spinner } from '@/components/common/Spinner';

export function NodePalette() {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({
    input: true,
    processing: true,
    embedding: true,
    storage: true,
    retrieval: true,
    llm: true,
    tool: true,
    memory: true,
    agent: true,
  });

  // Fetch nodes from API
  const { data: nodes = [], isLoading, error } = useQuery({
    queryKey: ['nodes'],
    queryFn: listNodes,
    retry: 1,
  });

  // Group nodes by category
  const nodesByCategory = nodes?.reduce((acc, node) => {
    const category = node.category || 'other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(node);
    return acc;
  }, {} as Record<string, NodeMetadata[]>) || {};

  // Filter nodes based on search
  const filteredNodesByCategory = Object.entries(nodesByCategory).reduce(
    (acc, [category, categoryNodes]) => {
      const filtered = categoryNodes.filter(
        (node) =>
          node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          node.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
      if (filtered.length > 0) {
        acc[category] = filtered;
      }
      return acc;
    },
    {} as Record<string, NodeMetadata[]>
  );

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [category]: !prev[category],
    }));
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-red-600 mb-2">Failed to load nodes</p>
          <p className="text-sm text-gray-600">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col glass-strong border-r border-white/10">
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <h2 className="text-lg font-semibold text-white mb-3">Node Palette</h2>
        
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search nodes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          />
        </div>
      </div>

      {/* Node categories */}
      <div className="flex-1 overflow-y-auto p-2">
        {Object.entries(filteredNodesByCategory).map(([category, categoryNodes]) => (
          <NodeCategory
            key={category}
            category={category}
            nodes={categoryNodes}
            isExpanded={expandedCategories[category]}
            onToggle={() => toggleCategory(category)}
          />
        ))}
        
        {Object.keys(filteredNodesByCategory).length === 0 && (
          <div className="text-center py-8 text-slate-400">
            <p>No nodes found</p>
            {searchQuery && (
              <p className="text-sm mt-2">Try a different search term</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

