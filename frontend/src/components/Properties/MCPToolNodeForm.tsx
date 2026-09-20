/**
 * MCP Tool Node Form
 *
 * Pick a configured MCP server, then one of the tools it exposes. Tools are read from the
 * server itself, so any MCP server works without NodeAI knowing about it.
 */

import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertCircle, Plug } from 'lucide-react';
import { getMCPServers, getMCPTools, connectServer } from '@/services/mcp';
import { Textarea } from '@/components/common/Textarea';
import { SelectWithIcons } from '@/components/common/SelectWithIcons';
import toast from 'react-hot-toast';

/** Message from an axios-style error, without using `any`. */
function errorMessage(error: unknown, fallback: string): string {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail || fallback;
}

interface MCPToolNodeFormProps {
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
}

export function MCPToolNodeForm({ initialData, onChange }: MCPToolNodeFormProps) {
  const [server, setServer] = useState<string>(initialData.server || '');
  const [tool, setTool] = useState<string>(initialData.tool || '');
  const [argumentsText, setArgumentsText] = useState<string>(() =>
    typeof initialData.arguments === 'string'
      ? initialData.arguments
      : JSON.stringify(initialData.arguments ?? {}, null, 2)
  );
  const [connecting, setConnecting] = useState(false);

  const serversQuery = useQuery({ queryKey: ['mcp-servers'], queryFn: getMCPServers });
  const toolsQuery = useQuery({ queryKey: ['mcp-tools'], queryFn: () => getMCPTools() });

  const servers = serversQuery.data?.servers ?? [];
  const selectedServer = servers.find((s) => s.name === server);

  const tools = useMemo(
    () => (toolsQuery.data?.tools ?? []).filter((t) => t.server_name === server),
    [toolsQuery.data, server]
  );

  useEffect(() => {
    let parsed: Record<string, any> | string = argumentsText;
    try {
      parsed = argumentsText.trim() ? JSON.parse(argumentsText) : {};
    } catch {
      // keep the raw text; the backend reports invalid JSON when the node runs
    }
    onChange({ ...initialData, server, tool, arguments: parsed });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [server, tool, argumentsText]);

  const handleConnect = async () => {
    if (!server) return;
    setConnecting(true);
    try {
      await connectServer(server);
      toast.success('Connected');
      await Promise.all([serversQuery.refetch(), toolsQuery.refetch()]);
    } catch (error: unknown) {
      toast.error(errorMessage(error, 'Could not connect to the server'));
    } finally {
      setConnecting(false);
    }
  };

  let argumentsError: string | null = null;
  if (argumentsText.trim()) {
    try {
      JSON.parse(argumentsText);
    } catch (e: unknown) {
      argumentsError = e instanceof Error ? e.message : 'Invalid JSON';
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          MCP Server <span className="text-red-400">*</span>
        </label>
        {servers.length === 0 && !serversQuery.isLoading ? (
          <p className="text-xs text-slate-400">
            No MCP servers configured yet. Add one under Settings &gt; MCP.
          </p>
        ) : (
          <SelectWithIcons
            value={server}
            onChange={(value) => {
              setServer(value);
              setTool('');
            }}
            options={servers.map((s) => ({
              value: s.name,
              label: `${s.display_name}${s.connected ? '' : ' (not connected)'}`,
              icon: s.preset || 'mcp',
            }))}
            placeholder="Select a server..."
          />
        )}
      </div>

      {selectedServer && !selectedServer.connected && (
        <button
          type="button"
          onClick={handleConnect}
          disabled={connecting}
          className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-200 hover:bg-amber-500/30 disabled:opacity-60"
        >
          <Plug className="w-4 h-4" />
          {connecting ? 'Connecting...' : 'Connect to load tools'}
        </button>
      )}

      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          Tool <span className="text-red-400">*</span>
        </label>
        {server && tools.length === 0 ? (
          <p className="text-xs text-slate-400">
            {selectedServer?.connected
              ? 'This server exposes no tools.'
              : 'Connect the server to see its tools.'}
          </p>
        ) : (
          <SelectWithIcons
            value={tool}
            onChange={setTool}
            options={tools.map((t) => ({ value: t.name, label: t.name, icon: 'mcp' }))}
            placeholder={server ? 'Select a tool...' : 'Select a server first'}
          />
        )}
        {tool && (
          <p className="text-xs text-slate-400">
            {tools.find((t) => t.name === tool)?.description}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          Arguments (JSON)
        </label>
        <p className="text-xs text-slate-400 -mt-1">
          Use <code>{'{input}'}</code> for the value coming from the previous node, e.g.{' '}
          <code>{'{"query": "{input}"}'}</code>
        </p>
        <Textarea
          value={argumentsText}
          onChange={(e) => setArgumentsText(e.target.value)}
          rows={6}
          className="font-mono text-xs"
          placeholder={'{\n  "query": "{input}"\n}'}
        />
        {argumentsError && (
          <p className="flex items-center gap-1 text-xs text-red-400">
            <AlertCircle className="w-3 h-3" />
            {argumentsError}
          </p>
        )}
      </div>
    </div>
  );
}
