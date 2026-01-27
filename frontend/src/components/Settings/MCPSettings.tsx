/**
 * MCP Settings - Manage MCP servers and tools for AI agents
 */

import { useState, useEffect } from 'react';
import {
  Plug,
  Plus,
  Trash2,
  Power,
  PowerOff,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Search,
  ExternalLink,
  Check,
  X,
  Loader2,
  Wrench,
  Sparkles,
  Server,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';
import type {
  MCPPreset,
  MCPServer,
  MCPTool,
  MCPStatus,
} from '@/services/mcp';
import {
  getMCPPresets,
  getMCPServers,
  getMCPTools,
  getMCPStatus,
  addServerFromPreset,
  connectServer,
  disconnectServer,
  removeServer,
  connectAllServers,
  getCategoryIcon,
} from '@/services/mcp';
import { ProviderIcon } from '@/components/common/ProviderIcon';

type TabType = 'servers' | 'tools';

export function MCPSettings() {
  const [activeTab, setActiveTab] = useState<TabType>('servers');
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<MCPStatus | null>(null);

  // Servers state
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [presets, setPresets] = useState<MCPPreset[]>([]);
  const [showAddServer, setShowAddServer] = useState(false);

  // Tools state
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [toolCategories, setToolCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [toolSearch, setToolSearch] = useState('');

  // Load data
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statusRes, serversRes, presetsRes, toolsRes] = await Promise.all([
        getMCPStatus(),
        getMCPServers(),
        getMCPPresets(),
        getMCPTools(),
      ]);

      setStatus(statusRes);
      setServers(serversRes.servers);
      setPresets(presetsRes.presets);
      setTools(toolsRes.tools);
      setToolCategories(toolsRes.categories);
    } catch (error: any) {
      console.error('Failed to load MCP data:', error);
      toast.error('Failed to load MCP settings');
    } finally {
      setLoading(false);
    }
  };

  // Filter tools
  const filteredTools = tools.filter((tool) => {
    const matchesCategory = selectedCategory === 'all' || tool.category === selectedCategory;
    const matchesSource = selectedSource === 'all' || tool.source === selectedSource;
    const matchesSearch =
      !toolSearch ||
      tool.name.toLowerCase().includes(toolSearch.toLowerCase()) ||
      tool.description.toLowerCase().includes(toolSearch.toLowerCase());
    return matchesCategory && matchesSource && matchesSearch;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Status */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1">MCP Integration</h3>
          <p className="text-sm text-slate-400">
            Connect external tools and services for your AI agents via Model Context Protocol
          </p>
        </div>
        <button
          onClick={loadData}
          className="p-2 hover:bg-white/5 rounded-lg text-slate-400 hover:text-white transition-colors"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Status Cards */}
      {status && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 mb-1">
              <Server className="w-4 h-4" />
              <span className="text-xs">Servers</span>
            </div>
            <div className="text-2xl font-bold text-white">
              {status.servers.connected}
              <span className="text-sm font-normal text-slate-400">/{status.servers.total}</span>
            </div>
            <div className="text-xs text-slate-500">connected</div>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 mb-1">
              <Wrench className="w-4 h-4" />
              <span className="text-xs">MCP Tools</span>
            </div>
            <div className="text-2xl font-bold text-white">{status.tools.mcp}</div>
            <div className="text-xs text-slate-500">from servers</div>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 mb-1">
              <Sparkles className="w-4 h-4" />
              <span className="text-xs">AI Tools</span>
            </div>
            <div className="text-2xl font-bold text-white">{status.tools.internal}</div>
            <div className="text-xs text-slate-500">built-in</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/10">
        <button
          onClick={() => setActiveTab('servers')}
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'servers'
              ? 'text-amber-400 border-amber-500'
              : 'text-slate-400 border-transparent hover:text-slate-300'
          )}
        >
          <Plug className="w-4 h-4" />
          Servers
        </button>
        <button
          onClick={() => setActiveTab('tools')}
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'tools'
              ? 'text-amber-400 border-amber-500'
              : 'text-slate-400 border-transparent hover:text-slate-300'
          )}
        >
          <Wrench className="w-4 h-4" />
          Tools
          <span className="ml-1 px-1.5 py-0.5 text-xs bg-white/10 rounded">
            {tools.length}
          </span>
        </button>
      </div>

      {/* Content */}
      {activeTab === 'servers' ? (
        <ServersTab
          servers={servers}
          presets={presets}
          showAddServer={showAddServer}
          setShowAddServer={setShowAddServer}
          onRefresh={loadData}
        />
      ) : (
        <ToolsTab
          tools={filteredTools}
          categories={toolCategories}
          selectedCategory={selectedCategory}
          setSelectedCategory={setSelectedCategory}
          selectedSource={selectedSource}
          setSelectedSource={setSelectedSource}
          toolSearch={toolSearch}
          setToolSearch={setToolSearch}
        />
      )}
    </div>
  );
}

// Servers Tab Component
function ServersTab({
  servers,
  presets,
  showAddServer,
  setShowAddServer,
  onRefresh,
}: {
  servers: MCPServer[];
  presets: MCPPreset[];
  showAddServer: boolean;
  setShowAddServer: (show: boolean) => void;
  onRefresh: () => void;
}) {
  const [connecting, setConnecting] = useState<string | null>(null);
  const [removing, setRemoving] = useState<string | null>(null);

  const handleConnect = async (serverName: string) => {
    setConnecting(serverName);
    try {
      await connectServer(serverName);
      toast.success(`Connected to ${serverName}`);
      onRefresh();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || `Failed to connect to ${serverName}`);
    } finally {
      setConnecting(null);
    }
  };

  const handleDisconnect = async (serverName: string) => {
    setConnecting(serverName);
    try {
      await disconnectServer(serverName);
      toast.success(`Disconnected from ${serverName}`);
      onRefresh();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || `Failed to disconnect from ${serverName}`);
    } finally {
      setConnecting(null);
    }
  };

  const handleRemove = async (serverName: string) => {
    if (!confirm(`Are you sure you want to remove ${serverName}?`)) return;

    setRemoving(serverName);
    try {
      await removeServer(serverName);
      toast.success(`Removed ${serverName}`);
      onRefresh();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || `Failed to remove ${serverName}`);
    } finally {
      setRemoving(null);
    }
  };

  const handleConnectAll = async () => {
    try {
      const result = await connectAllServers();
      toast.success(`Connected to ${result.connected} servers`);
      if (result.failed > 0) {
        toast.error(`Failed to connect to ${result.failed} servers`);
      }
      onRefresh();
    } catch (error: any) {
      toast.error('Failed to connect to servers');
    }
  };

  return (
    <div className="space-y-4">
      {/* Actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setShowAddServer(!showAddServer)}
          className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            showAddServer
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
              : 'bg-white/5 text-slate-300 hover:bg-white/10 border border-white/10'
          )}
        >
          <Plus className="w-4 h-4" />
          Add Server
        </button>

        {servers.length > 0 && (
          <button
            onClick={handleConnectAll}
            className="flex items-center gap-2 px-3 py-2 bg-green-500/20 text-green-300 border border-green-500/30 rounded-lg text-sm font-medium hover:bg-green-500/30 transition-colors"
          >
            <Power className="w-4 h-4" />
            Connect All
          </button>
        )}
      </div>

      {/* Add Server Form */}
      {showAddServer && (
        <AddServerForm
          presets={presets}
          onSuccess={() => {
            setShowAddServer(false);
            onRefresh();
          }}
          onCancel={() => setShowAddServer(false)}
        />
      )}

      {/* Server List */}
      {servers.length === 0 ? (
        <div className="bg-white/5 border border-white/10 rounded-lg p-8 text-center">
          <Plug className="w-12 h-12 mx-auto mb-4 text-slate-500" />
          <h4 className="text-white font-medium mb-2">No servers configured</h4>
          <p className="text-sm text-slate-400 mb-4">
            Add MCP servers to give your AI agents access to external tools and services.
          </p>
          <button
            onClick={() => setShowAddServer(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Your First Server
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {servers.map((server) => (
            <div
              key={server.name}
              className={cn(
                'bg-white/5 border rounded-lg p-4 transition-colors',
                server.connected ? 'border-green-500/30' : 'border-white/10'
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      'w-10 h-10 rounded-lg flex items-center justify-center',
                      server.connected ? 'bg-green-500/20' : 'bg-white/10'
                    )}
                  >
                    {(() => {
                      if (server.preset) {
                        const preset = presets.find((p) => p.name === server.preset);
                        if (preset?.icon) {
                          return <ProviderIcon provider={preset.icon} size="md" className="w-6 h-6" />;
                        }
                        return <span className="text-lg">{getCategoryIcon(preset?.category || 'general')}</span>;
                      }
                      return <span className="text-lg">🔌</span>;
                    })()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-white">{server.display_name}</h4>
                      {server.connected && (
                        <span className="px-1.5 py-0.5 text-xs bg-green-500/20 text-green-300 rounded">
                          Connected
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-400">{server.description}</p>
                    {server.connected && server.tools_count > 0 && (
                      <p className="text-xs text-slate-500 mt-1">
                        {server.tools_count} tools available
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {server.connected ? (
                    <button
                      onClick={() => handleDisconnect(server.name)}
                      disabled={connecting === server.name}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/20 text-red-300 border border-red-500/30 rounded-lg text-sm hover:bg-red-500/30 transition-colors disabled:opacity-50"
                    >
                      {connecting === server.name ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <PowerOff className="w-3.5 h-3.5" />
                      )}
                      Disconnect
                    </button>
                  ) : (
                    <button
                      onClick={() => handleConnect(server.name)}
                      disabled={connecting === server.name}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/20 text-green-300 border border-green-500/30 rounded-lg text-sm hover:bg-green-500/30 transition-colors disabled:opacity-50"
                    >
                      {connecting === server.name ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Power className="w-3.5 h-3.5" />
                      )}
                      Connect
                    </button>
                  )}

                  <button
                    onClick={() => handleRemove(server.name)}
                    disabled={removing === server.name}
                    className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors disabled:opacity-50"
                    title="Remove server"
                  >
                    {removing === server.name ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Add Server Form Component
function AddServerForm({
  presets,
  onSuccess,
  onCancel,
}: {
  presets: MCPPreset[];
  onSuccess: () => void;
  onCancel: () => void;
}) {
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [envValues, setEnvValues] = useState<Record<string, string>>({});
  const [customName, setCustomName] = useState('');
  const [adding, setAdding] = useState(false);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  // Group presets by category
  const presetsByCategory = presets.reduce(
    (acc, preset) => {
      if (!acc[preset.category]) {
        acc[preset.category] = [];
      }
      acc[preset.category].push(preset);
      return acc;
    },
    {} as Record<string, MCPPreset[]>
  );

  const selectedPresetData = presets.find((p) => p.name === selectedPreset);

  const handleAdd = async () => {
    if (!selectedPreset) {
      toast.error('Please select a server type');
      return;
    }

    // Validate required env vars
    const preset = presets.find((p) => p.name === selectedPreset);
    if (preset) {
      for (const envVar of preset.env_vars) {
        if (!envValues[envVar]) {
          toast.error(`Please provide ${envVar}`);
          return;
        }
      }
    }

    setAdding(true);
    try {
      await addServerFromPreset(selectedPreset, envValues, customName || undefined);
      toast.success('Server added successfully');
      onSuccess();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to add server');
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="bg-white/5 border border-white/10 rounded-lg p-4 space-y-4">
      <h4 className="font-medium text-white flex items-center gap-2">
        <Plus className="w-4 h-4" />
        Add MCP Server
      </h4>

      {/* Preset Selection */}
      <div className="space-y-2">
        <label className="text-sm text-slate-300">Select Server Type</label>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {Object.entries(presetsByCategory).map(([category, categoryPresets]) => (
            <div key={category} className="border border-white/10 rounded-lg overflow-hidden">
              <button
                onClick={() =>
                  setExpandedCategory(expandedCategory === category ? null : category)
                }
                className="w-full flex items-center justify-between px-3 py-2 bg-white/5 hover:bg-white/10 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span>{getCategoryIcon(category)}</span>
                  <span className="text-sm font-medium text-white capitalize">{category}</span>
                  <span className="text-xs text-slate-500">({categoryPresets.length})</span>
                </div>
                {expandedCategory === category ? (
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                )}
              </button>

              {expandedCategory === category && (
                <div className="p-2 space-y-1">
                  {categoryPresets.map((preset) => (
                    <button
                      key={preset.name}
                      onClick={() => {
                        setSelectedPreset(preset.name);
                        setEnvValues({});
                      }}
                      className={cn(
                        'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors',
                        selectedPreset === preset.name
                          ? 'bg-amber-500/20 border border-amber-500/30'
                          : 'hover:bg-white/5 border border-transparent'
                      )}
                    >
                      <div className="flex-1">
                        <div className="text-sm font-medium text-white">{preset.display_name}</div>
                        <div className="text-xs text-slate-400">{preset.description}</div>
                      </div>
                      {selectedPreset === preset.name && (
                        <Check className="w-4 h-4 text-amber-400" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Configuration */}
      {selectedPresetData && (
        <div className="space-y-3 pt-3 border-t border-white/10">
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <span>Configure {selectedPresetData.display_name}</span>
          </div>

          {/* Environment Variables */}
          {selectedPresetData.env_vars.map((envVar) => (
            <div key={envVar}>
              <label className="block text-xs text-slate-400 mb-1">{envVar}</label>
              <input
                type="password"
                value={envValues[envVar] || ''}
                onChange={(e) => setEnvValues({ ...envValues, [envVar]: e.target.value })}
                placeholder={`Enter ${envVar}`}
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
          ))}

          {/* Custom Name (optional) */}
          <div>
            <label className="block text-xs text-slate-400 mb-1">Custom Name (optional)</label>
            <input
              type="text"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              placeholder={selectedPresetData.name}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-end gap-2 pt-3 border-t border-white/10">
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm text-slate-400 hover:text-slate-300 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleAdd}
          disabled={adding || !selectedPreset}
          className="flex items-center gap-2 px-4 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {adding ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Adding...
            </>
          ) : (
            <>
              <Plus className="w-4 h-4" />
              Add Server
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// Tools Tab Component
function ToolsTab({
  tools,
  categories,
  selectedCategory,
  setSelectedCategory,
  selectedSource,
  setSelectedSource,
  toolSearch,
  setToolSearch,
}: {
  tools: MCPTool[];
  categories: string[];
  selectedCategory: string;
  setSelectedCategory: (category: string) => void;
  selectedSource: string;
  setSelectedSource: (source: string) => void;
  toolSearch: string;
  setToolSearch: (search: string) => void;
}) {
  const [expandedTool, setExpandedTool] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={toolSearch}
            onChange={(e) => setToolSearch(e.target.value)}
            placeholder="Search tools..."
            className="w-full pl-9 pr-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        </div>

        {/* Source Filter */}
        <select
          value={selectedSource}
          onChange={(e) => setSelectedSource(e.target.value)}
          className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
        >
          <option value="all">All Sources</option>
          <option value="internal">Built-in AI Tools</option>
          <option value="mcp">MCP Integrations</option>
        </select>

        {/* Category Filter */}
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
        >
          <option value="all">All Categories</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {getCategoryIcon(cat)} {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Tools List */}
      {tools.length === 0 ? (
        <div className="bg-white/5 border border-white/10 rounded-lg p-8 text-center">
          <Wrench className="w-12 h-12 mx-auto mb-4 text-slate-500" />
          <h4 className="text-white font-medium mb-2">No tools found</h4>
          <p className="text-sm text-slate-400">
            {toolSearch
              ? 'Try a different search term'
              : 'Connect MCP servers to add more tools'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {tools.map((tool) => (
            <div
              key={tool.name}
              className="bg-white/5 border border-white/10 rounded-lg overflow-hidden"
            >
              <button
                onClick={() => setExpandedTool(expandedTool === tool.name ? null : tool.name)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      'w-8 h-8 rounded-lg flex items-center justify-center text-sm',
                      tool.source === 'internal'
                        ? 'bg-amber-500/20 text-amber-300'
                        : 'bg-blue-500/20 text-blue-300'
                    )}
                  >
                    {getCategoryIcon(tool.category)}
                  </div>
                  <div className="text-left">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-white">{tool.name}</span>
                      <span
                        className={cn(
                          'px-1.5 py-0.5 text-xs rounded',
                          tool.source === 'internal'
                            ? 'bg-amber-500/20 text-amber-300'
                            : 'bg-blue-500/20 text-blue-300'
                        )}
                      >
                        {tool.source === 'internal' ? 'AI' : 'MCP'}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400">{tool.description}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 capitalize">{tool.category}</span>
                  {expandedTool === tool.name ? (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  )}
                </div>
              </button>

              {expandedTool === tool.name && (
                <div className="px-4 pb-4 pt-2 border-t border-white/10 bg-black/20">
                  <div className="space-y-3">
                    <div>
                      <div className="text-xs text-slate-500 mb-1">Source</div>
                      <div className="text-sm text-slate-300">
                        {tool.source === 'internal'
                          ? `NodeAI Built-in (${tool.node_type})`
                          : `MCP Server (${tool.server_name})`}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs text-slate-500 mb-1">Usage in Agent Config</div>
                      <pre className="p-2 bg-black/40 rounded text-xs text-green-300 overflow-x-auto">
                        {`"mcp_tools": ["${tool.name}"]`}
                      </pre>
                    </div>

                    {tool.input_schema && Object.keys(tool.input_schema).length > 0 && (
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Input Parameters</div>
                        <pre className="p-2 bg-black/40 rounded text-xs text-slate-300 overflow-x-auto max-h-32">
                          {JSON.stringify(tool.input_schema, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Help Text */}
      <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
        <h4 className="text-sm font-medium text-amber-300 mb-2">How to use tools in agents</h4>
        <p className="text-xs text-slate-400 mb-2">
          Add tools to your CrewAI agents by specifying them in the agent configuration:
        </p>
        <pre className="p-2 bg-black/40 rounded text-xs text-green-300 overflow-x-auto">
{`{
  "role": "Research Analyst",
  "goal": "Research and analyze data",
  "mcp_tools": ["all"]  // or ["internal"], ["mcp"], or specific tool names
}`}
        </pre>
      </div>
    </div>
  );
}
