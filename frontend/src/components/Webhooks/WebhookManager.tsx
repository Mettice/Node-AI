/**
 * Webhook Manager Component
 * 
 * Manages webhooks for workflows: create, view, edit, delete, test
 */

import { useState } from 'react';
import { 
  Plus, 
  Copy, 
  CheckCircle2, 
  Trash2, 
  Edit2, 
  ExternalLink,
  Loader2
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cn } from '@/utils/cn';
import {
  listWebhooks,
  createWebhook,
  updateWebhook,
  deleteWebhook,
  type Webhook,
  type CreateWebhookRequest,
  type UpdateWebhookRequest,
} from '@/services/webhooks';
import toast from 'react-hot-toast';

interface WebhookManagerProps {
  workflowId: string;
}

export function WebhookManager({ workflowId }: WebhookManagerProps) {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState<Webhook | null>(null);
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Get base URL from window location
  const baseUrl = typeof window !== 'undefined' 
    ? `${window.location.protocol}//${window.location.host}`
    : 'http://localhost:8000';

  const { data: webhooks, isLoading } = useQuery({
    queryKey: ['webhooks', workflowId],
    queryFn: () => listWebhooks(workflowId, baseUrl),
  });

  const createMutation = useMutation({
    mutationFn: (request: CreateWebhookRequest) => createWebhook(request, baseUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks', workflowId] });
      toast.success('Webhook created successfully');
      setShowCreateModal(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create webhook');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ webhookId, request }: { webhookId: string; request: UpdateWebhookRequest }) =>
      updateWebhook(webhookId, request, baseUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks', workflowId] });
      toast.success('Webhook updated successfully');
      setEditingWebhook(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update webhook');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteWebhook,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks', workflowId] });
      toast.success('Webhook deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete webhook');
    },
  });

  const handleCopyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopiedUrl(url);
    toast.success('Webhook URL copied to clipboard');
    setTimeout(() => setCopiedUrl(null), 2000);
  };

  const handleDelete = (webhookId: string, webhookName?: string) => {
    if (!window.confirm(`Delete webhook "${webhookName || webhookId}"? This action cannot be undone.`)) {
      return;
    }
    deleteMutation.mutate(webhookId);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Webhooks</h3>
          <p className="text-sm text-slate-400 mt-1">
            Create webhooks to trigger this workflow from external systems
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Create Webhook</span>
        </button>
      </div>

      {/* Webhooks List */}
      {!webhooks || webhooks.length === 0 ? (
        <div className="glass rounded-lg p-8 border border-white/10 text-center">
          <ExternalLink className="w-12 h-12 text-slate-400 mx-auto mb-4 opacity-50" />
          <p className="text-slate-400 mb-2">No webhooks yet</p>
          <p className="text-sm text-slate-500 mb-4">
            Create a webhook to allow external systems to trigger this workflow
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors"
          >
            Create Your First Webhook
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {webhooks.map((webhook) => (
            <WebhookCard
              key={webhook.id}
              webhook={webhook}
              onCopyUrl={handleCopyUrl}
              onEdit={() => setEditingWebhook(webhook)}
              onDelete={() => handleDelete(webhook.webhook_id, webhook.name)}
              copied={copiedUrl === webhook.webhook_url}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <WebhookCreateModal
          workflowId={workflowId}
          onClose={() => setShowCreateModal(false)}
          onCreate={(request) => createMutation.mutate(request)}
          isLoading={createMutation.isPending}
        />
      )}

      {/* Edit Modal */}
      {editingWebhook && (
        <WebhookEditModal
          webhook={editingWebhook}
          onClose={() => setEditingWebhook(null)}
          onUpdate={(request) => updateMutation.mutate({ webhookId: editingWebhook.webhook_id, request })}
          isLoading={updateMutation.isPending}
        />
      )}
    </div>
  );
}

function WebhookCard({
  webhook,
  onCopyUrl,
  onEdit,
  onDelete,
  copied,
}: {
  webhook: Webhook;
  onCopyUrl: (url: string) => void;
  onEdit: () => void;
  onDelete: () => void;
  copied: boolean;
}) {
  return (
    <div className="glass rounded-lg p-4 border border-white/10">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-semibold text-white">
              {webhook.name || `Webhook ${webhook.webhook_id.slice(-8)}`}
            </h4>
            <div className={cn(
              'px-2 py-0.5 rounded text-xs',
              webhook.enabled
                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                : 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
            )}>
              {webhook.enabled ? 'Enabled' : 'Disabled'}
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
            <span>{webhook.total_calls} calls</span>
            <span>•</span>
            <span className="text-green-400">{webhook.successful_calls} success</span>
            {webhook.failed_calls > 0 && (
              <>
                <span>•</span>
                <span className="text-red-400">{webhook.failed_calls} failed</span>
              </>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={onEdit}
            className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded transition-colors"
            title="Edit"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={onDelete}
            className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Webhook URL */}
      <div className="mb-3">
        <label className="block text-xs text-slate-400 mb-1">Webhook URL</label>
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={webhook.webhook_url}
            readOnly
            className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white font-mono"
          />
          <button
            onClick={() => onCopyUrl(webhook.webhook_url)}
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
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-2 border-t border-white/10">
        <a
          href={webhook.webhook_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded transition-colors"
        >
          <ExternalLink className="w-3 h-3" />
          <span>Test</span>
        </a>
        {webhook.last_called_at && (
          <span className="text-xs text-slate-500">
            Last called: {new Date(webhook.last_called_at).toLocaleString()}
          </span>
        )}
      </div>
    </div>
  );
}

function WebhookCreateModal({
  workflowId,
  onClose,
  onCreate,
  isLoading,
}: {
  workflowId: string;
  onClose: () => void;
  onCreate: (request: CreateWebhookRequest) => void;
  isLoading: boolean;
}) {
  const [name, setName] = useState('');
  const [secret, setSecret] = useState('');
  const [generateSecret, setGenerateSecret] = useState(true);

  const handleCreate = () => {
    onCreate({
      workflow_id: workflowId,
      name: name.trim() || undefined,
      secret: generateSecret ? undefined : secret.trim() || undefined,
    });
  };

  return (
    <>
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
        onClick={onClose}
      />
      <div className="fixed inset-0 z-[101] flex items-center justify-center p-4">
        <div
          className="bg-slate-800 border border-white/10 rounded-lg shadow-2xl w-full max-w-md"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="p-6 border-b border-white/10">
            <h3 className="text-lg font-semibold text-white">Create Webhook</h3>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Name (optional)
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Webhook"
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={generateSecret}
                  onChange={(e) => setGenerateSecret(e.target.checked)}
                  className="w-4 h-4 text-amber-600 bg-white/5 border-white/20 rounded focus:ring-amber-500"
                />
                <span className="text-sm text-slate-300">Auto-generate secret</span>
              </label>
              {!generateSecret && (
                <input
                  type="text"
                  value={secret}
                  onChange={(e) => setSecret(e.target.value)}
                  placeholder="Enter secret key"
                  className="w-full mt-2 px-3 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              )}
            </div>
          </div>
          <div className="p-6 border-t border-white/10 flex items-center justify-end gap-3">
            <button
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 text-sm text-slate-300 hover:text-white transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={isLoading}
              className="px-4 py-2 text-sm bg-amber-600 hover:bg-amber-700 text-white rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
              <span>Create</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

function WebhookEditModal({
  webhook,
  onClose,
  onUpdate,
  isLoading,
}: {
  webhook: Webhook;
  onClose: () => void;
  onUpdate: (request: UpdateWebhookRequest) => void;
  isLoading: boolean;
}) {
  const [name, setName] = useState(webhook.name || '');
  const [enabled, setEnabled] = useState(webhook.enabled);

  const handleUpdate = () => {
    onUpdate({
      name: name.trim() || undefined,
      enabled,
    });
  };

  return (
    <>
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
        onClick={onClose}
      />
      <div className="fixed inset-0 z-[101] flex items-center justify-center p-4">
        <div
          className="bg-slate-800 border border-white/10 rounded-lg shadow-2xl w-full max-w-md"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="p-6 border-b border-white/10">
            <h3 className="text-lg font-semibold text-white">Edit Webhook</h3>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Webhook name"
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enabled}
                  onChange={(e) => setEnabled(e.target.checked)}
                  className="w-4 h-4 text-amber-600 bg-white/5 border-white/20 rounded focus:ring-amber-500"
                />
                <span className="text-sm text-slate-300">Enabled</span>
              </label>
            </div>
          </div>
          <div className="p-6 border-t border-white/10 flex items-center justify-end gap-3">
            <button
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 text-sm text-slate-300 hover:text-white transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleUpdate}
              disabled={isLoading}
              className="px-4 py-2 text-sm bg-amber-600 hover:bg-amber-700 text-white rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
              <span>Save</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

