/**
 * MCP Service - API client for MCP server management
 */

import { apiClient } from '@/utils/api';

// Types

export interface MCPPreset {
  name: string;
  display_name: string;
  description: string;
  category: string;
  env_vars: string[];
  server_type: 'npx' | 'executable' | 'http';
  auth_type: 'api_key' | 'oauth' | 'none';
  setup_url?: string;
  setup_instructions?: string;
  icon?: string; // Service name for ProviderIcon (e.g., 'slack', 'airtable', 'github')
}

export interface MCPServer {
  name: string;
  preset: string | null;
  display_name: string;
  description: string;
  enabled: boolean;
  connected: boolean;
  tools_count: number;
}

export interface MCPTool {
  name: string;
  description: string;
  source: 'mcp' | 'internal';
  server_name: string | null;
  node_type: string | null;
  category: string;
  input_schema?: Record<string, any>;
}

export interface MCPStatus {
  servers: {
    total: number;
    connected: number;
    enabled: number;
  };
  tools: {
    total: number;
    mcp: number;
    internal: number;
  };
}

// API Functions

/**
 * Get all available MCP server presets
 */
export async function getMCPPresets(): Promise<{ presets: MCPPreset[]; categories: string[] }> {
  const response = await apiClient.get('/mcp/presets');
  return response.data;
}

/**
 * Get all configured MCP servers
 */
export async function getMCPServers(): Promise<{ servers: MCPServer[] }> {
  const response = await apiClient.get('/mcp/servers');
  return response.data;
}

/**
 * Add a server from a preset
 */
export async function addServerFromPreset(
  presetName: string,
  envValues: Record<string, string>,
  customName?: string
): Promise<{ success: boolean; server: MCPServer; message: string }> {
  const response = await apiClient.post('/mcp/servers/preset', {
    preset_name: presetName,
    env_values: envValues,
    custom_name: customName,
  });
  return response.data;
}

/**
 * Add a custom MCP server
 */
export async function addCustomServer(config: {
  name: string;
  display_name: string;
  description: string;
  command: string;
  args: string[];
  env: Record<string, string>;
}): Promise<{ success: boolean; server: MCPServer }> {
  const response = await apiClient.post('/mcp/servers/custom', config);
  return response.data;
}

/**
 * Connect to an MCP server
 */
export async function connectServer(
  serverName: string
): Promise<{ success: boolean; server: MCPServer }> {
  const response = await apiClient.post(`/mcp/servers/${serverName}/connect`);
  return response.data;
}

/**
 * Disconnect from an MCP server
 */
export async function disconnectServer(
  serverName: string
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post(`/mcp/servers/${serverName}/disconnect`);
  return response.data;
}

/**
 * Remove an MCP server configuration
 */
export async function removeServer(
  serverName: string
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.delete(`/mcp/servers/${serverName}`);
  return response.data;
}

/**
 * Enable an MCP server
 */
export async function enableServer(serverName: string): Promise<{ success: boolean }> {
  const response = await apiClient.post(`/mcp/servers/${serverName}/enable`);
  return response.data;
}

/**
 * Disable an MCP server
 */
export async function disableServer(serverName: string): Promise<{ success: boolean }> {
  const response = await apiClient.post(`/mcp/servers/${serverName}/disable`);
  return response.data;
}

/**
 * Get all available tools
 */
export async function getMCPTools(params?: {
  category?: string;
  source?: 'mcp' | 'internal';
}): Promise<{ tools: MCPTool[]; total: number; categories: string[] }> {
  const response = await apiClient.get('/mcp/tools', { params });
  return response.data;
}

/**
 * Get details for a specific tool
 */
export async function getMCPTool(toolName: string): Promise<{ tool: MCPTool }> {
  const response = await apiClient.get(`/mcp/tools/${toolName}`);
  return response.data;
}

/**
 * Connect to all enabled servers
 */
export async function connectAllServers(): Promise<{
  results: Record<string, boolean>;
  connected: number;
  failed: number;
}> {
  const response = await apiClient.post('/mcp/connect-all');
  return response.data;
}

/**
 * Disconnect from all servers
 */
export async function disconnectAllServers(): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post('/mcp/disconnect-all');
  return response.data;
}

/**
 * Get overall MCP status
 */
export async function getMCPStatus(): Promise<MCPStatus> {
  const response = await apiClient.get('/mcp/status');
  return response.data;
}

// Category icons mapping
export const CATEGORY_ICONS: Record<string, string> = {
  communication: '💬',
  storage: '📁',
  database: '🗄️',
  productivity: '📅',
  development: '💻',
  search: '🔍',
  business: '💼',
  content: '📝',
  sales: '💰',
  intelligence: '🧠',
  safety: '🛡️',
  knowledge: '📚',
  llm: '🤖',
  integration: '🔗',
  ai: '✨',
  general: '⚙️',
};

// Get icon for category
export function getCategoryIcon(category: string): string {
  return CATEGORY_ICONS[category] || CATEGORY_ICONS.general;
}
