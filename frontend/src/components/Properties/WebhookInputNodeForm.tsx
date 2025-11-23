/**
 * Webhook Input Node Form
 * 
 * Special form for webhook input nodes that:
 * - Shows webhook URL
 * - Allows creating/updating webhook
 * - Displays webhook statistics
 */

import { useState, useEffect } from 'react';
import { Copy, CheckCircle2, ExternalLink, Loader2, ToggleLeft, ToggleRight } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cn } from '@/utils/cn';
import {
  createWebhook,
  updateWebhook,
  getWebhook,
  type Webhook,
  type CreateWebhookRequest,
} from '@/services/webhooks';
import { useWorkflowStore } from '@/store/workflowStore';
import toast from 'react-hot-toast';

interface WebhookInputNodeFormProps {
  initialData: {
    webhook_id?: string;
    webhook_url?: string;
    name?: string;
    method?: string;
    enabled?: boolean;
    secret?: string;
  };
  onChange: (data: any) => void;
}

export function WebhookInputNodeForm({
  initialData,
  onChange,
}: WebhookInputNodeFormProps) {
  const { workflowId, selectedNodeId } = useWorkflowStore();
  const nodeId = selectedNodeId || '';
  const [copied, setCopied] = useState(false);
  const [webhookName, setWebhookName] = useState(initialData.name || '');
  const [httpMethod, setHttpMethod] = useState(initialData.method || 'POST');
  const [enabled, setEnabled] = useState(initialData.enabled !== false);
  const queryClient = useQueryClient();

  // Sync local state when initialData changes (e.g., after webhook creation)
  useEffect(() => {
    if (initialData.name) setWebhookName(initialData.name);
    if (initialData.method) setHttpMethod(initialData.method);
    if (initialData.enabled !== undefined) setEnabled(initialData.enabled);
  }, [initialData.name, initialData.method, initialData.enabled]);

  // Get base URL from window location
  const baseUrl = typeof window !== 'undefined' 
    ? `${window.location.protocol}//${window.location.host}`
    : 'http://localhost:8000';

  // Fetch webhook if webhook_id exists
  const { data: webhook, isLoading, error: webhookError } = useQuery<Webhook>({
    queryKey: ['webhook', initialData.webhook_id],
    queryFn: () => getWebhook(initialData.webhook_id!, baseUrl),
    enabled: !!initialData.webhook_id,
    retry: false, // Don't retry on 404
  });

  // Silently handle 404 - webhook might not exist yet
  useEffect(() => {
    if (webhookError && (webhookError as any)?.response?.status !== 404) {
      console.error('Error fetching webhook:', webhookError);
    }
  }, [webhookError]);

  const createMutation = useMutation({
    mutationFn: (request: CreateWebhookRequest) => createWebhook(request, baseUrl),
    onSuccess: (data) => {
      // Update node with webhook info - merge with existing config
      const newConfig = {
        ...initialData,
        webhook_id: data.webhook_id,
        webhook_url: data.webhook_url,
        name: data.name || webhookName,
        method: httpMethod,
        enabled: true,
      };
      onChange(newConfig);
      // Update local state immediately so form shows the URL
      setWebhookName(data.name || webhookName);
      queryClient.invalidateQueries({ queryKey: ['webhook', data.webhook_id] });
      toast.success('Webhook created successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create webhook');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: any }) =>
      updateWebhook(id, updates, baseUrl),
    onSuccess: (data) => {
      onChange({
        ...initialData,
        webhook_id: data.webhook_id,
        webhook_url: data.webhook_url,
        name: data.name,
        method: httpMethod,
        enabled: data.enabled,
      });
      queryClient.invalidateQueries({ queryKey: ['webhook', data.webhook_id] });
      toast.success('Webhook updated');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update webhook');
    },
  });

  // Auto-create webhook when node is first added (if no webhook_id)
  useEffect(() => {
    if (!initialData.webhook_id && workflowId && !createMutation.isPending && !createMutation.isSuccess) {
      // Small delay to ensure component is fully mounted
      const timer = setTimeout(() => {
        createMutation.mutate({
          workflow_id: workflowId,
          name: webhookName || `Webhook for ${nodeId.slice(0, 8)}`,
          method: httpMethod,
        });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [workflowId, initialData.webhook_id, createMutation.isPending, createMutation.isSuccess]); // Re-run if workflowId or webhook_id changes

  const handleCopyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopied(true);
    toast.success('Webhook URL copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleUpdate = () => {
    if (initialData.webhook_id) {
      const updates: any = {};
      if (webhookName !== initialData.name) updates.name = webhookName;
      if (httpMethod !== initialData.method) updates.method = httpMethod;
      if (enabled !== initialData.enabled) updates.enabled = enabled;
      
      if (Object.keys(updates).length > 0) {
        updateMutation.mutate({
          id: initialData.webhook_id,
          updates,
        });
      }
    }
  };

  // Auto-save when method or enabled changes
  useEffect(() => {
    if (initialData.webhook_id && (httpMethod !== initialData.method || enabled !== initialData.enabled)) {
      const timer = setTimeout(() => handleUpdate(), 500);
      return () => clearTimeout(timer);
    }
  }, [httpMethod, enabled]);

  // Get webhook URL from multiple sources - prioritize mutation result, then webhook data, then initialData
  const webhookUrl = createMutation.data?.webhook_url || webhook?.webhook_url || initialData.webhook_url || '';
  // Show webhook config if: webhook exists in node config, was fetched, or was just created
  const hasWebhook = !!initialData.webhook_id || !!webhook?.webhook_id || !!createMutation.data?.webhook_id;
  // Show URL section if we have a URL, are creating, or just created
  const showUrlSection = !!webhookUrl || createMutation.isPending || createMutation.isSuccess;

  return (
    <div className="space-y-4">
      {/* Webhook Name */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Webhook Name
        </label>
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={webhookName}
            onChange={(e) => setWebhookName(e.target.value)}
            onBlur={handleUpdate}
            placeholder="My Webhook"
            className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          {updateMutation.isPending && (
            <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
          )}
        </div>
      </div>

      {/* Webhook URL - Show if we have a URL, are creating, or just created */}
      {showUrlSection && (
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Webhook URL
          </label>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={webhookUrl || (createMutation.isPending ? 'Creating...' : '')}
              readOnly
              className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded text-white font-mono text-sm"
            />
            {webhookUrl && !createMutation.isPending && (
              <>
                <button
                  onClick={() => handleCopyUrl(webhookUrl)}
                  className={cn(
                    'p-2 rounded transition-colors',
                    copied
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                  )}
                  title="Copy URL"
                >
                  {copied ? <CheckCircle2 className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </button>
                <a
                  href={webhookUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 rounded transition-colors"
                  title="Test webhook"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </>
            )}
          </div>
          {webhookUrl && (
            <p className="text-xs text-slate-400 mt-1">
              Send HTTP {httpMethod} requests to this URL to trigger the workflow
            </p>
          )}
        </div>
      )}

      {/* HTTP Method - Always show */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          HTTP Method
        </label>
        <select
          value={httpMethod}
          onChange={(e) => setHttpMethod(e.target.value)}
          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500 [&>option]:bg-slate-800 [&>option]:text-white"
          style={{ colorScheme: 'dark' }}
        >
          <option value="POST" className="bg-slate-800 text-white">POST</option>
          <option value="GET" className="bg-slate-800 text-white">GET</option>
        </select>
      </div>

      {/* Enable/Disable - Show if webhook exists */}
      {hasWebhook && (
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-slate-300">
            Enabled
          </label>
          <button
            onClick={() => {
              setEnabled(!enabled);
              if (initialData.webhook_id) {
                updateMutation.mutate({
                  id: initialData.webhook_id,
                  updates: { enabled: !enabled },
                });
              }
            }}
            className={cn(
              'flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors',
              enabled
                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                : 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
            )}
          >
            {enabled ? (
              <>
                <ToggleRight className="w-5 h-5" />
                <span className="text-sm">Enabled</span>
              </>
            ) : (
              <>
                <ToggleLeft className="w-5 h-5" />
                <span className="text-sm">Disabled</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Webhook Status */}
      {isLoading ? (
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Loading webhook...</span>
        </div>
      ) : webhook && !webhookError ? (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Status:</span>
            <span className={cn(
              'px-2 py-0.5 rounded text-xs',
              webhook.enabled
                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                : 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
            )}>
              {webhook.enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Total Calls:</span>
            <span className="text-white">{webhook.total_calls}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Success Rate:</span>
            <span className="text-white">
              {webhook.total_calls > 0
                ? `${((webhook.successful_calls / webhook.total_calls) * 100).toFixed(1)}%`
                : 'N/A'}
            </span>
          </div>
          {webhook.last_called_at && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Last Called:</span>
              <span className="text-white text-xs">
                {new Date(webhook.last_called_at).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      ) : createMutation.isPending ? (
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Creating webhook...</span>
        </div>
      ) : !hasWebhook && !createMutation.isSuccess && !createMutation.isPending ? (
        <div className="space-y-2">
          <div className="text-sm text-slate-400">
            Webhook will be created automatically, or click below to create now
          </div>
          <button
            onClick={() => {
              if (workflowId) {
                createMutation.mutate({
                  workflow_id: workflowId,
                  name: webhookName || `Webhook for ${nodeId.slice(0, 8)}`,
                  method: httpMethod,
                });
              } else {
                toast.error('Workflow ID not available. Please save the workflow first.');
              }
            }}
            disabled={!workflowId || createMutation.isPending}
            className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            title={!workflowId ? 'Please save the workflow first to create a webhook' : ''}
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Creating...</span>
              </>
            ) : !workflowId ? (
              <>
                <span>Save Workflow First</span>
              </>
            ) : (
              <span>Create Webhook</span>
            )}
          </button>
        </div>
      ) : null}
    </div>
  );
}

