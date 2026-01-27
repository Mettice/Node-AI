/**
 * Node palette component - displays available nodes organized by category
 *
 * Integration nodes (Airtable, S3, Slack, etc.) are hidden from the palette
 * and accessed via MCP integrations instead.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Plug } from 'lucide-react';
import { listNodes } from '@/services/nodes';
import { NodeCategory } from './NodeCategory';
import type { NodeMetadata } from '@/types/node';
import { Spinner } from '@/components/common/Spinner';

/**
 * Node types that require external service authentication.
 * These are hidden from the palette and accessed via MCP integrations.
 */
const HIDDEN_NODE_TYPES = new Set([
  // Storage integrations (use MCP instead)
  'airtable',
  's3',
  'azure_blob',
  'google_sheets',
  'google_drive',
  'database',
  'knowledge_graph',

  // Communication integrations (use MCP instead)
  'slack',
  'email',
  'reddit',

  // External API integrations (use MCP instead)
  'stripe_analytics',
  'graph_tools',
  'ai_web_search',
  'rerank',  // Cohere API - can use MCP

  // Generic tool node (replaced by MCP tools)
  'tool',

  // Placeholder nodes
  'lead_enricher',
]);

/**
 * Preferred category display order for cleaner organization
 */
const CATEGORY_ORDER = [
  'agent',       // AI Agents first (main feature)
  'llm',         // LLM interaction
  'intelligence', // AI analysis
  'content',     // AI content generation
  'sales',       // Sales AI
  'business',    // Business AI
  'developer',   // Developer AI
  'retrieval',   // RAG retrieval
  'embedding',   // Embeddings
  'processing',  // Text/data processing
  'input',       // Input nodes
  'storage',     // Vector Store and other storage nodes
  'memory',      // Memory/state
  'training',    // Fine-tuning
];

export function NodePalette() {
  const [searchQuery, setSearchQuery] = useState('');
  // Agent category expanded by default (main feature)
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({
    agent: true,
    llm: false,
    intelligence: false,
    content: false,
    sales: false,
    business: false,
    developer: false,
    retrieval: false,
    embedding: false,
    processing: false,
    input: false,
    memory: false,
    training: false,
  });

  // Fetch nodes from API
  const { data: nodes = [], isLoading, error } = useQuery({
    queryKey: ['nodes'],
    queryFn: listNodes,
    retry: 1,
  });

  // Filter out hidden integration nodes and group by category
  const nodesByCategory = nodes?.reduce((acc, node) => {
    // Skip hidden integration nodes
    if (HIDDEN_NODE_TYPES.has(node.type)) {
      return acc;
    }

    const category = node.category || 'other';

    // Skip entire communication and integration categories (all moved to MCP)
    // Storage category is allowed (vector_store, etc.) but individual integration nodes are hidden via HIDDEN_NODE_TYPES
    if (category === 'communication' || category === 'integration') {
      return acc;
    }

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
            className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>
      </div>

      {/* Node categories - ordered by importance */}
      <div className="flex-1 overflow-y-auto p-2">
        {/* Render categories in preferred order */}
        {CATEGORY_ORDER
          .filter((category) => filteredNodesByCategory[category]?.length > 0)
          .map((category) => (
            <NodeCategory
              key={category}
              category={category}
              nodes={filteredNodesByCategory[category]}
              isExpanded={expandedCategories[category]}
              onToggle={() => toggleCategory(category)}
            />
          ))}

        {/* Render any remaining categories not in the order list */}
        {Object.entries(filteredNodesByCategory)
          .filter(([category]) => !CATEGORY_ORDER.includes(category))
          .map(([category, categoryNodes]) => (
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

        {/* MCP Integrations link */}
        <div className="mt-4 p-3 bg-gradient-to-r from-blue-500/10 to-amber-500/10 border border-white/10 rounded-lg">
          <div className="flex items-center gap-2 text-sm text-slate-300 mb-1">
            <Plug className="w-4 h-4 text-blue-400" />
            <span className="font-medium">Need MCP Integrations?</span>
          </div>
          <p className="text-xs text-slate-400">
            Connect Slack, Gmail, Airtable via MCP button in toolbar or Settings → MCP Tools
          </p>
        </div>
      </div>
    </div>
  );
}

