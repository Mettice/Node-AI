/**
 * ToolSelector - Select MCP tools and internal AI tools for agents
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Wrench,
  Sparkles,
  Plug,
  Search,
  Check,
  ChevronDown,
  ChevronRight,
  Loader2,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import type { MCPTool } from '@/services/mcp';
import { getMCPTools, getCategoryIcon } from '@/services/mcp';

type ToolMode = 'none' | 'all' | 'internal' | 'mcp' | 'custom';

interface ToolSelectorProps {
  value: string[];
  onChange: (tools: string[]) => void;
  label?: string;
  description?: string;
  compact?: boolean;
}

export function ToolSelector({
  value = [],
  onChange,
  label = 'Agent Tools',
  description,
  compact = false,
}: ToolSelectorProps) {
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  // Determine current mode from value
  const getMode = (): ToolMode => {
    if (!value || value.length === 0) return 'none';
    if (value.includes('all')) return 'all';
    if (value.includes('internal')) return 'internal';
    if (value.includes('mcp')) return 'mcp';
    return 'custom';
  };

  const mode = getMode();

  // Fetch tools from API
  const fetchTools = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getMCPTools();
      setTools(response.tools || []);
      setCategories(response.categories || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load tools');
      // Use empty arrays as fallback
      setTools([]);
      setCategories([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load tools when expanded
  useEffect(() => {
    if (expanded && tools.length === 0 && !loading) {
      fetchTools();
    }
  }, [expanded, tools.length, loading, fetchTools]);

  // Handle mode change
  const handleModeChange = (newMode: ToolMode) => {
    switch (newMode) {
      case 'none':
        onChange([]);
        break;
      case 'all':
        onChange(['all']);
        break;
      case 'internal':
        onChange(['internal']);
        break;
      case 'mcp':
        onChange(['mcp']);
        break;
      case 'custom':
        // Keep existing custom selections or start empty
        if (mode !== 'custom') {
          onChange([]);
        }
        break;
    }
  };

  // Handle individual tool toggle
  const toggleTool = (toolName: string) => {
    const currentTools = mode === 'custom' ? value : [];
    if (currentTools.includes(toolName)) {
      onChange(currentTools.filter((t) => t !== toolName));
    } else {
      onChange([...currentTools, toolName]);
    }
  };

  // Check if a tool is selected
  const isToolSelected = (toolName: string): boolean => {
    if (mode === 'all') return true;
    if (mode === 'internal') return tools.find((t) => t.name === toolName)?.source === 'internal';
    if (mode === 'mcp') return tools.find((t) => t.name === toolName)?.source === 'mcp';
    return value.includes(toolName);
  };

  // Filter tools by search
  const filteredTools = tools.filter(
    (tool) =>
      tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Group tools by category
  const toolsByCategory = filteredTools.reduce((acc, tool) => {
    const cat = tool.category || 'general';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(tool);
    return acc;
  }, {} as Record<string, MCPTool[]>);

  // Toggle category expansion
  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  // Get summary text
  const getSummaryText = (): string => {
    switch (mode) {
      case 'none':
        return 'No tools selected';
      case 'all':
        return `All tools (${tools.length} available)`;
      case 'internal':
        return `Internal AI tools (${tools.filter((t) => t.source === 'internal').length})`;
      case 'mcp':
        return `MCP integrations (${tools.filter((t) => t.source === 'mcp').length})`;
      case 'custom':
        return `${value.length} tool${value.length !== 1 ? 's' : ''} selected`;
      default:
        return 'No tools selected';
    }
  };

  // Mode options
  const modeOptions: { value: ToolMode; label: string; icon: typeof Wrench; description: string }[] = [
    {
      value: 'none',
      label: 'No Tools',
      icon: AlertCircle,
      description: 'Agent works without external tools',
    },
    {
      value: 'all',
      label: 'All Tools',
      icon: Sparkles,
      description: 'Access to all available tools',
    },
    {
      value: 'internal',
      label: 'Internal AI',
      icon: Wrench,
      description: 'NodeAI AI tools (content, analysis)',
    },
    {
      value: 'mcp',
      label: 'Integrations',
      icon: Plug,
      description: 'MCP servers (Slack, Gmail, etc.)',
    },
    {
      value: 'custom',
      label: 'Custom',
      icon: Check,
      description: 'Select specific tools',
    },
  ];

  if (compact) {
    return (
      <div className="space-y-2">
        <label className="block text-xs text-slate-300 mb-1">{label}</label>
        <div className="flex flex-wrap gap-2">
          {modeOptions.map((opt) => {
            const Icon = opt.icon;
            const isActive = mode === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => handleModeChange(opt.value)}
                className={cn(
                  'flex items-center gap-1.5 px-2 py-1 text-xs rounded-md transition-all',
                  isActive
                    ? 'bg-amber-600 text-white'
                    : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white'
                )}
                title={opt.description}
              >
                <Icon className="w-3 h-3" />
                {opt.label}
              </button>
            );
          })}
        </div>
        {mode === 'custom' && (
          <p className="text-xs text-slate-500">
            Click the expand button below to select specific tools.
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <label className="block text-xs text-slate-300">{label}</label>
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-amber-400 hover:text-amber-300 transition-colors"
        >
          {expanded ? (
            <>
              <ChevronDown className="w-3 h-3" />
              Collapse
            </>
          ) : (
            <>
              <ChevronRight className="w-3 h-3" />
              Configure
            </>
          )}
        </button>
      </div>

      {description && <p className="text-xs text-slate-500 -mt-1">{description}</p>}

      {/* Mode Selector */}
      <div className="grid grid-cols-5 gap-1">
        {modeOptions.map((opt) => {
          const Icon = opt.icon;
          const isActive = mode === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleModeChange(opt.value)}
              className={cn(
                'flex flex-col items-center gap-1 p-2 rounded-md transition-all text-center',
                isActive
                  ? 'bg-amber-600/20 border border-amber-500/50 text-amber-300'
                  : 'bg-white/5 border border-transparent text-slate-400 hover:bg-white/10 hover:text-white'
              )}
              title={opt.description}
            >
              <Icon className="w-4 h-4" />
              <span className="text-[10px] leading-tight">{opt.label}</span>
            </button>
          );
        })}
      </div>

      {/* Summary */}
      <div className="flex items-center justify-between p-2 bg-white/5 rounded-md">
        <span className="text-xs text-slate-300">{getSummaryText()}</span>
        {loading && <Loader2 className="w-3 h-3 animate-spin text-slate-400" />}
      </div>

      {/* Expanded Tool Selection */}
      {expanded && (
        <div className="border border-white/10 rounded-lg overflow-hidden">
          {/* Search and Refresh */}
          <div className="flex items-center gap-2 p-2 bg-white/5 border-b border-white/10">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search tools..."
                className="w-full pl-7 pr-2 py-1 text-xs bg-white/5 border border-white/10 rounded text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
              />
            </div>
            <button
              type="button"
              onClick={fetchTools}
              disabled={loading}
              className="p-1 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
              title="Refresh tools"
            >
              <RefreshCw className={cn('w-3 h-3', loading && 'animate-spin')} />
            </button>
          </div>

          {/* Error State */}
          {error && (
            <div className="p-3 bg-red-500/10 border-b border-red-500/20">
              <p className="text-xs text-red-400">{error}</p>
            </div>
          )}

          {/* Loading State */}
          {loading && tools.length === 0 && (
            <div className="p-6 text-center">
              <Loader2 className="w-6 h-6 animate-spin text-amber-500 mx-auto mb-2" />
              <p className="text-xs text-slate-400">Loading tools...</p>
            </div>
          )}

          {/* Tools List by Category */}
          {!loading && tools.length > 0 && (
            <div className="max-h-64 overflow-y-auto">
              {Object.entries(toolsByCategory).map(([category, categoryTools]) => (
                <div key={category} className="border-b border-white/5 last:border-0">
                  {/* Category Header */}
                  <button
                    type="button"
                    onClick={() => toggleCategory(category)}
                    className="w-full flex items-center gap-2 p-2 hover:bg-white/5 transition-colors"
                  >
                    {expandedCategories.has(category) ? (
                      <ChevronDown className="w-3 h-3 text-slate-500" />
                    ) : (
                      <ChevronRight className="w-3 h-3 text-slate-500" />
                    )}
                    <span className="text-sm">{getCategoryIcon(category)}</span>
                    <span className="text-xs font-medium text-slate-300 capitalize">{category}</span>
                    <span className="text-[10px] text-slate-500">({categoryTools.length})</span>
                  </button>

                  {/* Category Tools */}
                  {expandedCategories.has(category) && (
                    <div className="pb-2">
                      {categoryTools.map((tool) => {
                        const selected = isToolSelected(tool.name);
                        const disabled = mode !== 'custom' && mode !== 'none';
                        return (
                          <button
                            key={tool.name}
                            type="button"
                            onClick={() => !disabled && toggleTool(tool.name)}
                            disabled={disabled}
                            className={cn(
                              'w-full flex items-start gap-2 px-4 py-2 text-left transition-colors',
                              selected
                                ? 'bg-amber-500/10'
                                : 'hover:bg-white/5',
                              disabled && 'opacity-50 cursor-not-allowed'
                            )}
                          >
                            <div
                              className={cn(
                                'mt-0.5 w-4 h-4 rounded border flex items-center justify-center flex-shrink-0',
                                selected
                                  ? 'bg-amber-600 border-amber-600'
                                  : 'border-white/20'
                              )}
                            >
                              {selected && <Check className="w-3 h-3 text-white" />}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-medium text-white truncate">
                                  {tool.name}
                                </span>
                                <span
                                  className={cn(
                                    'text-[9px] px-1 py-0.5 rounded',
                                    tool.source === 'mcp'
                                      ? 'bg-blue-500/20 text-blue-400'
                                      : 'bg-green-500/20 text-green-400'
                                  )}
                                >
                                  {tool.source === 'mcp' ? 'MCP' : 'AI'}
                                </span>
                              </div>
                              <p className="text-[10px] text-slate-500 line-clamp-1">
                                {tool.description}
                              </p>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}

              {/* Empty State */}
              {filteredTools.length === 0 && (
                <div className="p-6 text-center">
                  <p className="text-xs text-slate-400">
                    {searchQuery ? 'No tools match your search' : 'No tools available'}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* No Tools Available */}
          {!loading && tools.length === 0 && !error && (
            <div className="p-6 text-center">
              <Wrench className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-xs text-slate-400 mb-2">No tools configured</p>
              <p className="text-[10px] text-slate-500">
                Add MCP servers in Settings to enable external tools
              </p>
            </div>
          )}
        </div>
      )}

      {/* Help Text */}
      {!expanded && mode === 'custom' && value.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {value.slice(0, 3).map((toolName) => (
            <span
              key={toolName}
              className="text-[10px] px-1.5 py-0.5 bg-amber-500/20 text-amber-300 rounded"
            >
              {toolName}
            </span>
          ))}
          {value.length > 3 && (
            <span className="text-[10px] px-1.5 py-0.5 bg-white/10 text-slate-400 rounded">
              +{value.length - 3} more
            </span>
          )}
        </div>
      )}
    </div>
  );
}
