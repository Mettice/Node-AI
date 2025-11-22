/**
 * Secrets Vault Component - Manage user API keys and secrets
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Edit2, Trash2, Eye, EyeOff, Key, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { secretsApi } from '@/services/secrets';
import type { Secret } from '@/services/secrets';
import { ProviderIcon } from '@/components/common/ProviderIcon';
import toast from 'react-hot-toast';
import { SecretForm } from './SecretForm';

const PROVIDERS = [
  { id: 'openai', name: 'OpenAI', type: 'api_key' },
  { id: 'anthropic', name: 'Anthropic', type: 'api_key' },
  { id: 'google', name: 'Google Gemini', type: 'api_key' },
  { id: 'cohere', name: 'Cohere', type: 'api_key' },
  { id: 'voyage', name: 'Voyage AI', type: 'api_key' },
  { id: 'slack', name: 'Slack', type: 'oauth_token' },
  { id: 'google_drive', name: 'Google Drive', type: 'oauth_token' },
  { id: 'reddit', name: 'Reddit', type: 'oauth_token' },
  { id: 'postgresql', name: 'PostgreSQL', type: 'connection_string' },
  { id: 'mysql', name: 'MySQL', type: 'connection_string' },
  { id: 'pinecone', name: 'Pinecone', type: 'api_key' },
];

export function SecretsVault() {
  const [showForm, setShowForm] = useState(false);
  const [editingSecret, setEditingSecret] = useState<Secret | null>(null);
  const [showValues, setShowValues] = useState<Record<string, boolean>>({});
  const queryClient = useQueryClient();

  const { data: secrets = [], isLoading } = useQuery({
    queryKey: ['secrets'],
    queryFn: () => secretsApi.list(),
  });

  const deleteMutation = useMutation({
    mutationFn: (secretId: string) => secretsApi.delete(secretId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['secrets'] });
      toast.success('Secret deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete secret');
    },
  });

  const toggleValueVisibility = (secretId: string) => {
    setShowValues((prev) => ({
      ...prev,
      [secretId]: !prev[secretId],
    }));
  };

  const handleEdit = (secret: Secret) => {
    setEditingSecret(secret);
    setShowForm(true);
  };

  const handleAdd = () => {
    setEditingSecret(null);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingSecret(null);
  };

  const handleFormSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['secrets'] });
    handleFormClose();
  };

  const maskSecret = (value: string) => {
    if (!value) return '';
    if (value.length <= 4) return '••••';
    return '•'.repeat(value.length - 4) + value.slice(-4);
  };

  const groupedSecrets = secrets.reduce((acc, secret) => {
    const key = secret.provider;
    if (!acc[key]) acc[key] = [];
    acc[key].push(secret);
    return acc;
  }, {} as Record<string, Secret[]>);

  if (showForm) {
    return (
      <SecretForm
        secret={editingSecret || undefined}
        onClose={handleFormClose}
        onSuccess={handleFormSuccess}
      />
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1">Secrets Vault</h3>
          <p className="text-sm text-slate-400">
            Manage your API keys and integration secrets securely
          </p>
        </div>
        <button
          onClick={handleAdd}
          className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Secret</span>
        </button>
      </div>

      {/* Secrets List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-400">Loading secrets...</div>
        </div>
      ) : secrets.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <Key className="w-12 h-12 text-slate-500 mb-4" />
          <p className="text-slate-400 mb-2">No secrets stored yet</p>
          <p className="text-sm text-slate-500 mb-4">
            Add your first API key or integration secret to get started
          </p>
          <button
            onClick={handleAdd}
            className="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors"
          >
            Add Secret
          </button>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-6">
          {Object.entries(groupedSecrets).map(([provider, providerSecrets]) => (
            <div key={provider} className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                <ProviderIcon provider={provider} className="w-4 h-4" />
                <span>{PROVIDERS.find((p) => p.id === provider)?.name || provider}</span>
                <span className="text-slate-500">({providerSecrets.length})</span>
              </div>
              <div className="space-y-2">
                {providerSecrets.map((secret) => (
                  <div
                    key={secret.id}
                    className="bg-slate-800/50 border border-white/10 rounded-lg p-4 hover:border-white/20 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h4 className="text-sm font-medium text-white">{secret.name}</h4>
                          {secret.is_active ? (
                            <CheckCircle2 className="w-4 h-4 text-green-400" />
                          ) : (
                            <XCircle className="w-4 h-4 text-slate-500" />
                          )}
                          <span className="text-xs px-2 py-0.5 bg-slate-700 text-slate-300 rounded">
                            {secret.secret_type}
                          </span>
                        </div>
                        {secret.description && (
                          <p className="text-sm text-slate-400 mb-2">{secret.description}</p>
                        )}
                        <div className="flex items-center gap-4 text-xs text-slate-500">
                          {secret.last_used_at && (
                            <div className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              <span>Last used: {new Date(secret.last_used_at).toLocaleDateString()}</span>
                            </div>
                          )}
                          {secret.usage_count > 0 && (
                            <span>Used {secret.usage_count} times</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => toggleValueVisibility(secret.id)}
                          className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded transition-colors"
                          title={showValues[secret.id] ? 'Hide value' : 'Show value'}
                        >
                          {showValues[secret.id] ? (
                            <EyeOff className="w-4 h-4" />
                          ) : (
                            <Eye className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleEdit(secret)}
                          className="p-2 text-slate-400 hover:text-blue-400 hover:bg-white/5 rounded transition-colors"
                          title="Edit"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            if (confirm(`Delete "${secret.name}"? This cannot be undone.`)) {
                              deleteMutation.mutate(secret.id);
                            }
                          }}
                          className="p-2 text-slate-400 hover:text-red-400 hover:bg-white/5 rounded transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    {showValues[secret.id] && secret.value && (
                      <div className="mt-3 p-2 bg-slate-900/50 rounded text-xs font-mono text-slate-300 break-all">
                        {secret.value}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

