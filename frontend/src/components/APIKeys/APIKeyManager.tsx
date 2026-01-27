/**
 * API Key Management Component
 */

import { useState, useEffect } from 'react';
import { Plus, Trash2, Key, Activity, DollarSign, Clock } from 'lucide-react';
import { createAPIKey, listAPIKeys, deleteAPIKey, getAPIKeyUsage, type APIKey, type UsageStats } from '@/services/apiKeys';
import { useWorkflowStore } from '@/store/workflowStore';
import toast from 'react-hot-toast';

export function APIKeyManager() {
  const { workflowId } = useWorkflowStore();
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [usageStats, setUsageStats] = useState<Record<string, UsageStats>>({});
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKey, setNewKey] = useState<{ name: string; rate_limit: string; cost_limit: string }>({
    name: '',
    rate_limit: '',
    cost_limit: '',
  });

  const loadKeys = async () => {
    setLoading(true);
    try {
      const workflowKeys = workflowId ? await listAPIKeys(workflowId) : await listAPIKeys();
      setKeys(workflowKeys);
      
      // Load usage stats for all keys
      const stats: Record<string, UsageStats> = {};
      for (const key of workflowKeys) {
        try {
          stats[key.key_id] = await getAPIKeyUsage(key.key_id);
        } catch (err) {
          // Ignore errors loading stats
        }
      }
      setUsageStats(stats);
    } catch (error: any) {
      toast.error(error.response?.data?.detail?.message || 'Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKeys();
  }, [workflowId]);

  const handleCreate = async () => {
    if (!newKey.name.trim()) {
      toast.error('Please enter a name for the API key');
      return;
    }

    try {
      const response = await createAPIKey({
        workflow_id: workflowId || undefined,
        name: newKey.name.trim(),
        rate_limit: newKey.rate_limit ? parseInt(newKey.rate_limit) : undefined,
        cost_limit: newKey.cost_limit ? parseFloat(newKey.cost_limit) : undefined,
      });

      // Show the new key in a modal/alert (user must copy it)
      const keyToShow = response.api_key;
      const confirmed = window.confirm(
        `API Key Created!\n\n` +
        `Your API key (shown only once):\n${keyToShow}\n\n` +
        `Copy this key now. It will not be shown again.\n\n` +
        `Click OK to copy to clipboard.`
      );

      if (confirmed) {
        navigator.clipboard.writeText(keyToShow);
        toast.success('API key copied to clipboard!');
      }

      setShowCreateModal(false);
      setNewKey({ name: '', rate_limit: '', cost_limit: '' });
      await loadKeys();
    } catch (error: any) {
      toast.error(error.response?.data?.detail?.message || 'Failed to create API key');
    }
  };

  const handleDelete = async (keyId: string) => {
    if (!window.confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return;
    }

    try {
      await deleteAPIKey(keyId);
      toast.success('API key deleted');
      await loadKeys();
    } catch (error: any) {
      toast.error(error.response?.data?.detail?.message || 'Failed to delete API key');
    }
  };

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">API Keys</h2>
          <p className="text-sm text-slate-400">
            Manage API keys for accessing your deployed workflows
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create API Key
        </button>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-800 border border-white/10 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-white mb-4">Create New API Key</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={newKey.name}
                  onChange={(e) => setNewKey({ ...newKey, name: e.target.value })}
                  placeholder="e.g., Production Key, Test Key"
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Rate Limit (requests/hour)
                </label>
                <input
                  type="number"
                  value={newKey.rate_limit}
                  onChange={(e) => setNewKey({ ...newKey, rate_limit: e.target.value })}
                  placeholder="Optional - e.g., 1000"
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Cost Limit ($/month)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={newKey.cost_limit}
                  onChange={(e) => setNewKey({ ...newKey, cost_limit: e.target.value })}
                  placeholder="Optional - e.g., 100.00"
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewKey({ name: '', rate_limit: '', cost_limit: '' });
                }}
                className="flex-1 px-4 py-2 bg-white/5 hover:bg-white/10 text-slate-300 rounded transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className="flex-1 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded transition-colors"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* API Keys List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-400">Loading API keys...</div>
        </div>
      ) : keys.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <Key className="w-12 h-12 text-slate-600 mb-4" />
          <p className="text-slate-400 mb-2">No API keys yet</p>
          <p className="text-sm text-slate-500">Create your first API key to start using deployed workflows</p>
        </div>
      ) : (
        <div className="space-y-3">
          {keys.map((key) => {
            const stats = usageStats[key.key_id];
            return (
              <div
                key={key.key_id}
                className="bg-white/5 border border-white/10 rounded-lg p-4"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-white">{key.name}</h3>
                      {key.is_active ? (
                        <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded">Active</span>
                      ) : (
                        <span className="px-2 py-0.5 text-xs bg-slate-500/20 text-slate-400 rounded">Inactive</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 font-mono">{key.key_id}</p>
                    {key.workflow_id && (
                      <p className="text-xs text-slate-500 mt-1">Workflow: {key.workflow_id}</p>
                    )}
                  </div>
                  <button
                    onClick={() => handleDelete(key.key_id)}
                    className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                    title="Delete API key"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {/* Usage Stats */}
                {stats && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3 pt-3 border-t border-white/10">
                    <div>
                      <div className="flex items-center gap-1 text-xs text-slate-400 mb-1">
                        <Activity className="w-3 h-3" />
                        Total Requests
                      </div>
                      <p className="text-sm font-semibold text-white">{stats.total_requests}</p>
                    </div>
                    <div>
                      <div className="flex items-center gap-1 text-xs text-slate-400 mb-1">
                        <DollarSign className="w-3 h-3" />
                        Total Cost
                      </div>
                      <p className="text-sm font-semibold text-white">${stats.total_cost.toFixed(4)}</p>
                    </div>
                    <div>
                      <div className="flex items-center gap-1 text-xs text-slate-400 mb-1">
                        <Clock className="w-3 h-3" />
                        Today
                      </div>
                      <p className="text-sm font-semibold text-white">{stats.requests_today} req</p>
                    </div>
                    <div>
                      <div className="flex items-center gap-1 text-xs text-slate-400 mb-1">
                        <DollarSign className="w-3 h-3" />
                        Cost Today
                      </div>
                      <p className="text-sm font-semibold text-white">${stats.cost_today.toFixed(4)}</p>
                    </div>
                  </div>
                )}

                {/* Limits */}
                <div className="flex items-center gap-4 text-xs text-slate-500 pt-2 border-t border-white/5">
                  {key.rate_limit && (
                    <span>Rate Limit: {key.rate_limit}/hour</span>
                  )}
                  {key.cost_limit && (
                    <span>Cost Limit: ${key.cost_limit.toFixed(2)}/month</span>
                  )}
                  {!key.rate_limit && !key.cost_limit && (
                    <span>No limits set</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

