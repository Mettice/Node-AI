/**
 * IntegrationsPanel - Quick access to MCP integrations from canvas
 *
 * Provides a dropdown/panel for users to quickly connect external services
 * like Slack, Gmail, Airtable, etc. via MCP servers.
 */

import { useState, useEffect } from 'react';
import {
  Plug,
  Check,
  X,
  Loader2,
  Settings,
  ChevronRight,
  AlertCircle,
  Plus,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import type { MCPServer, MCPPreset, MCPStatus } from '@/services/mcp';
import {
  getMCPServers,
  getMCPPresets,
  getMCPStatus,
  connectServer,
  disconnectServer,
  addServerFromPreset,
  addCustomServer,
  getCategoryIcon,
} from '@/services/mcp';
import { ProviderIcon } from '@/components/common/ProviderIcon';

interface IntegrationsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenSettings: () => void;
}

// Popular integrations to show first (must match backend MCP_SERVER_PRESETS)
const FEATURED_INTEGRATIONS = [
  'slack',
  'gmail',
  'github',
  'airtable',
  'notion',
  'google-drive',
  'postgres',
  'brave-search',
];

export function IntegrationsPanel({ isOpen, onClose, onOpenSettings }: IntegrationsPanelProps) {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [presets, setPresets] = useState<MCPPreset[]>([]);
  const [status, setStatus] = useState<MCPStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connectingServer, setConnectingServer] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState<string | null>(null);
  const [envValues, setEnvValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  // Fetch data on open
  useEffect(() => {
    if (isOpen) {
      fetchData();
    }
  }, [isOpen]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [serversRes, presetsRes, statusRes] = await Promise.all([
        getMCPServers().catch(() => ({ servers: [] })),
        getMCPPresets().catch(() => ({ presets: [], categories: [] })),
        getMCPStatus().catch(() => null),
      ]);
      setServers(serversRes.servers || []);
      setPresets(presetsRes.presets || []);
      setStatus(statusRes);
    } catch (err) {
      console.error('Failed to load integrations:', err);
    } finally {
      setLoading(false);
    }
  };

  // Check if a preset is connected
  const isPresetConnected = (presetName: string): MCPServer | undefined => {
    return servers.find((s) => s.preset === presetName && s.connected);
  };

  const isPresetConfigured = (presetName: string): MCPServer | undefined => {
    return servers.find((s) => s.preset === presetName);
  };

  // Handle quick connect for preset
  const handleQuickConnect = async (preset: MCPPreset) => {
    const existingServer = isPresetConfigured(preset.name);

    if (existingServer) {
      // Already configured, just connect/disconnect
      setConnectingServer(existingServer.name);
      try {
        if (existingServer.connected) {
          await disconnectServer(existingServer.name);
        } else {
          await connectServer(existingServer.name);
        }
        await fetchData();
      } catch (err: any) {
        console.error('Connection error:', err);
        // Extract error message from axios error
        const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to connect to server';
        setError(errorMessage);
        // Clear error after 5 seconds
        setTimeout(() => setError(null), 5000);
      } finally {
        setConnectingServer(null);
      }
    } else {
      // Need to configure first
      if (preset.env_vars.length > 0) {
        setShowAddForm(preset.name);
        setEnvValues({});
      } else {
        // No config needed, add directly
        setConnectingServer(preset.name);
        try {
          await addServerFromPreset(preset.name, {});
          await fetchData();
        } catch (err: any) {
          console.error('Failed to add server:', err);
          const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to add server';
          setError(errorMessage);
          setTimeout(() => setError(null), 5000);
        } finally {
          setConnectingServer(null);
        }
      }
    }
  };

  // Handle add server with config
  const handleAddServer = async (presetName: string) => {
    setConnectingServer(presetName);
    try {
      const preset = presets.find((p) => p.name === presetName);
      const executablePath = envValues['_EXECUTABLE_PATH'];

      // If executable server with custom path, use custom server API
      if (preset?.server_type === 'executable' && executablePath) {
        // Remove the internal field before sending
        const envVarsToSend = { ...envValues };
        delete envVarsToSend['_EXECUTABLE_PATH'];

        await addCustomServer({
          name: presetName,
          display_name: preset.display_name,
          description: preset.description,
          command: executablePath,
          args: [],
          env: envVarsToSend,
        });
      } else {
        // Regular preset-based server
        const envVarsToSend = { ...envValues };
        delete envVarsToSend['_EXECUTABLE_PATH'];
        await addServerFromPreset(presetName, envVarsToSend);
      }

      setShowAddForm(null);
      setEnvValues({});
      await fetchData();
    } catch (err: any) {
      console.error('Failed to add server:', err);
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to add server';
      setError(errorMessage);
      setTimeout(() => setError(null), 5000);
    } finally {
      setConnectingServer(null);
    }
  };

  // Get featured presets
  const featuredPresets = presets.filter((p) =>
    FEATURED_INTEGRATIONS.includes(p.name)
  );

  // Get other presets
  const otherPresets = presets.filter(
    (p) => !FEATURED_INTEGRATIONS.includes(p.name)
  );

  if (!isOpen) return null;

  return (
    <div className="absolute top-12 left-0 z-50 w-80 max-h-[70vh] overflow-hidden rounded-xl border border-white/10 bg-slate-900/95 backdrop-blur-xl shadow-2xl">
      {/* Error Banner */}
      {error && (
        <div className="p-3 bg-red-500/20 border-b border-red-500/30 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-red-400">Connection Failed</p>
            <p className="text-xs text-red-300/80 mt-1 break-words">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="p-0.5 hover:bg-red-500/20 rounded flex-shrink-0"
          >
            <X className="w-3 h-3 text-red-400" />
          </button>
        </div>
      )}
      
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-white/10">
        <div className="flex items-center gap-2">
          <Plug className="w-4 h-4 text-blue-400" />
          <span className="font-semibold text-white">MCP Integrations</span>
          {status && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-green-500/20 text-green-400">
              {status.servers.connected} connected
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={fetchData}
            disabled={loading}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className={cn('w-4 h-4 text-slate-400', loading && 'animate-spin')} />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="overflow-y-auto max-h-[calc(70vh-100px)]">
        {loading ? (
          <div className="p-8 text-center">
            <Loader2 className="w-6 h-6 animate-spin text-amber-500 mx-auto mb-2" />
            <p className="text-xs text-slate-400">Loading integrations...</p>
          </div>
        ) : (
          <div className="p-2">
            {/* Featured Integrations */}
            {featuredPresets.length > 0 && (
              <div className="mb-3">
                <p className="text-xs text-slate-500 uppercase tracking-wide px-2 mb-2">
                  Popular Integrations
                </p>
                <div className="grid grid-cols-2 gap-1.5">
                  {featuredPresets.map((preset) => {
                    const server = isPresetConfigured(preset.name);
                    const connected = server?.connected;
                    const isConnecting = connectingServer === preset.name || connectingServer === server?.name;
                    const isExecutable = preset.server_type === 'executable';
                    const isOAuth = preset.auth_type === 'oauth';

                    return (
                      <button
                        key={preset.name}
                        onClick={() => handleQuickConnect(preset)}
                        disabled={isConnecting}
                        className={cn(
                          'flex items-center gap-2 p-2.5 rounded-lg text-left transition-all',
                          connected
                            ? 'bg-green-500/10 border border-green-500/30'
                            : isExecutable
                            ? 'bg-blue-500/5 border border-blue-500/20 hover:bg-blue-500/10'
                            : 'bg-white/5 border border-transparent hover:bg-white/10 hover:border-white/10'
                        )}
                      >
                        {preset.icon ? (
                          <ProviderIcon provider={preset.icon} size="sm" className="w-5 h-5" />
                        ) : (
                          <span className="text-lg">{getCategoryIcon(preset.category)}</span>
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1">
                            <p className="text-xs font-medium text-white truncate">
                              {preset.display_name}
                            </p>
                            {isExecutable && (
                              <span className="text-[8px] px-1 py-0.5 bg-blue-500/20 text-blue-400 rounded">
                                BUILD
                              </span>
                            )}
                            {isOAuth && !isExecutable && (
                              <span className="text-[8px] px-1 py-0.5 bg-amber-500/20 text-amber-400 rounded">
                                OAuth
                              </span>
                            )}
                          </div>
                          {connected && (
                            <p className="text-[10px] text-green-400">Connected</p>
                          )}
                        </div>
                        {isConnecting ? (
                          <Loader2 className="w-3 h-3 animate-spin text-slate-400" />
                        ) : connected ? (
                          <Check className="w-3 h-3 text-green-400" />
                        ) : (
                          <Plus className="w-3 h-3 text-slate-500" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Add Form (when configuring) */}
            {showAddForm && (() => {
              const currentPreset = presets.find((p) => p.name === showAddForm);
              const isExecutable = currentPreset?.server_type === 'executable';
              const isOAuth = currentPreset?.auth_type === 'oauth';

              return (
                <div className="mb-3 p-3 bg-white/5 border border-white/10 rounded-lg">
                  <p className="text-sm font-medium text-white mb-2">
                    Configure {currentPreset?.display_name}
                  </p>

                  {/* OAuth/Setup Warning */}
                  {isOAuth && (
                    <div className="mb-3 p-2 bg-amber-500/10 border border-amber-500/30 rounded text-xs">
                      <p className="text-amber-400 font-medium mb-1">OAuth Setup Required</p>
                      <p className="text-amber-300/80">
                        This integration requires OAuth. You'll need to set up credentials first.
                      </p>
                      {currentPreset?.setup_url && (
                        <a
                          href={currentPreset.setup_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block mt-1 text-blue-400 hover:text-blue-300 underline"
                        >
                          Open Setup Page →
                        </a>
                      )}
                    </div>
                  )}

                  {/* Executable Server Warning */}
                  {isExecutable && (
                    <div className="mb-3 p-2 bg-blue-500/10 border border-blue-500/30 rounded text-xs">
                      <p className="text-blue-400 font-medium mb-1">Custom Executable Required</p>
                      <p className="text-blue-300/80 mb-2">
                        This server needs to be built locally. You must provide the path to the executable.
                      </p>
                      {currentPreset?.setup_instructions && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-blue-400 hover:text-blue-300">
                            Setup Instructions
                          </summary>
                          <pre className="mt-2 text-[10px] text-slate-400 whitespace-pre-wrap">
                            {currentPreset.setup_instructions.trim()}
                          </pre>
                        </details>
                      )}

                      {/* Executable Path Input */}
                      <div className="mt-3">
                        <label className="block text-xs text-slate-400 mb-1">
                          Executable Path
                        </label>
                        <input
                          type="text"
                          value={envValues['_EXECUTABLE_PATH'] || ''}
                          onChange={(e) =>
                            setEnvValues({ ...envValues, '_EXECUTABLE_PATH': e.target.value })
                          }
                          placeholder="C:/path/to/server.exe"
                          className="w-full px-2 py-1.5 text-xs bg-white/5 border border-white/10 rounded text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                        />
                      </div>
                    </div>
                  )}

                  {/* Environment Variables */}
                  {currentPreset?.env_vars.map((envVar) => (
                    <div key={envVar} className="mb-2">
                      <label className="block text-xs text-slate-400 mb-1">
                        {envVar.replace(/_/g, ' ')}
                      </label>
                      <input
                        type={envVar.toLowerCase().includes('secret') || envVar.toLowerCase().includes('key') || envVar.toLowerCase().includes('token') ? 'password' : 'text'}
                        value={envValues[envVar] || ''}
                        onChange={(e) =>
                          setEnvValues({ ...envValues, [envVar]: e.target.value })
                        }
                        placeholder={`Enter ${envVar}`}
                        className="w-full px-2 py-1.5 text-xs bg-white/5 border border-white/10 rounded text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                      />
                    </div>
                  ))}

                  {/* Setup URL for API key servers */}
                  {currentPreset?.setup_url && !isOAuth && (
                    <a
                      href={currentPreset.setup_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block mb-3 text-xs text-blue-400 hover:text-blue-300 underline"
                    >
                      Get API credentials →
                    </a>
                  )}

                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => handleAddServer(showAddForm)}
                      disabled={connectingServer === showAddForm}
                      className="flex-1 px-3 py-1.5 text-xs bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                      {connectingServer === showAddForm ? 'Connecting...' : 'Connect'}
                    </button>
                    <button
                      onClick={() => {
                        setShowAddForm(null);
                        setEnvValues({});
                      }}
                      className="px-3 py-1.5 text-xs bg-white/10 hover:bg-white/20 text-slate-300 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              );
            })()}

            {/* Connected Servers */}
            {servers.filter((s) => s.connected).length > 0 && (
              <div className="mb-3">
                <p className="text-xs text-slate-500 uppercase tracking-wide px-2 mb-2">
                  Active Connections
                </p>
                <div className="space-y-1">
                  {servers
                    .filter((s) => s.connected)
                    .map((server) => (
                      <div
                        key={server.name}
                        className="flex items-center justify-between p-2 bg-green-500/5 border border-green-500/20 rounded-lg"
                      >
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                          <span className="text-xs text-white">{server.display_name}</span>
                          <span className="text-[10px] text-slate-500">
                            {server.tools_count} tools
                          </span>
                        </div>
                        <button
                          onClick={() => handleQuickConnect(presets.find((p) => p.name === server.preset)!)}
                          className="text-xs text-red-400 hover:text-red-300"
                        >
                          Disconnect
                        </button>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Other Integrations */}
            {otherPresets.length > 0 && (
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide px-2 mb-2">
                  More Integrations
                </p>
                <div className="space-y-1">
                  {otherPresets.slice(0, 6).map((preset) => {
                    const server = isPresetConfigured(preset.name);
                    const connected = server?.connected;

                    return (
                      <button
                        key={preset.name}
                        onClick={() => handleQuickConnect(preset)}
                        className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-white/5 transition-colors text-left"
                      >
                        {preset.icon ? (
                          <ProviderIcon provider={preset.icon} size="sm" className="w-4 h-4" />
                        ) : (
                          <span className="text-sm">{getCategoryIcon(preset.category)}</span>
                        )}
                        <span className="flex-1 text-xs text-slate-300">{preset.display_name}</span>
                        {connected && <Check className="w-3 h-3 text-green-400" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Empty State */}
            {presets.length === 0 && (
              <div className="p-6 text-center">
                <AlertCircle className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p className="text-xs text-slate-400 mb-1">No integrations available</p>
                <p className="text-[10px] text-slate-500">
                  MCP server presets not loaded
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-2 border-t border-white/10">
        <button
          onClick={onOpenSettings}
          className="w-full flex items-center justify-center gap-2 p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
        >
          <Settings className="w-4 h-4 text-slate-400" />
          <span className="text-xs text-slate-300">Manage All Integrations</span>
          <ChevronRight className="w-3 h-3 text-slate-500" />
        </button>
      </div>
    </div>
  );
}
