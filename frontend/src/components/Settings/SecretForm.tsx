/**
 * Secret Form - Add/Edit secret modal
 */

import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Save, Eye, EyeOff } from 'lucide-react';
import { secretsApi } from '@/services/secrets';
import type { Secret, SecretCreate, SecretUpdate } from '@/services/secrets';
import { ProviderIcon } from '@/components/common/ProviderIcon';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';

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

interface SecretFormProps {
  secret?: Secret;
  onClose: () => void;
  onSuccess: () => void;
}

export function SecretForm({ secret, onClose, onSuccess }: SecretFormProps) {
  const isEditing = !!secret;
  const queryClient = useQueryClient();
  const [showValue, setShowValue] = useState(false);

  const [formData, setFormData] = useState({
    name: secret?.name || '',
    provider: secret?.provider || '',
    secret_type: secret?.secret_type || 'api_key',
    value: '',
    description: secret?.description || '',
    tags: secret?.tags?.join(', ') || '',
  });

  // When provider changes, update secret_type
  useEffect(() => {
    const provider = PROVIDERS.find((p) => p.id === formData.provider);
    if (provider) {
      setFormData((prev) => ({ ...prev, secret_type: provider.type }));
    }
  }, [formData.provider]);

  // Auto-fill name when provider is selected
  useEffect(() => {
    if (!isEditing && formData.provider && !formData.name) {
      const provider = PROVIDERS.find((p) => p.id === formData.provider);
      if (provider) {
        setFormData((prev) => ({ ...prev, name: `${provider.name} API Key` }));
      }
    }
  }, [formData.provider, isEditing]);

  const createMutation = useMutation({
    mutationFn: (data: SecretCreate) => secretsApi.create(data),
    onSuccess: () => {
      toast.success('Secret created successfully');
      onSuccess();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create secret');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: SecretUpdate }) =>
      secretsApi.update(id, data),
    onSuccess: () => {
      toast.success('Secret updated successfully');
      onSuccess();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update secret');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.provider || !formData.name) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (!isEditing && !formData.value) {
      toast.error('Please enter the secret value');
      return;
    }

    if (isEditing) {
      updateMutation.mutate({
        id: secret.id,
        data: {
          name: formData.name,
          value: formData.value || undefined,
          description: formData.description || undefined,
          tags: formData.tags
            ? formData.tags.split(',').map((t) => t.trim()).filter(Boolean)
            : undefined,
        },
      });
    } else {
      createMutation.mutate({
        name: formData.name,
        provider: formData.provider,
        secret_type: formData.secret_type,
        value: formData.value,
        description: formData.description || undefined,
        tags: formData.tags
          ? formData.tags.split(',').map((t) => t.trim()).filter(Boolean)
          : undefined,
      });
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-white">
          {isEditing ? 'Edit Secret' : 'Add Secret'}
        </h3>
        <button
          onClick={onClose}
          className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto space-y-4">
        {/* Provider */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Provider <span className="text-red-400">*</span>
          </label>
          <select
            value={formData.provider}
            onChange={(e) => setFormData((prev) => ({ ...prev, provider: e.target.value }))}
            disabled={isEditing}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed [&>option]:bg-slate-800 [&>option]:text-white"
            style={{ colorScheme: 'dark' }}
            required
          >
            <option value="">Select a provider</option>
            {PROVIDERS.map((provider) => (
              <option key={provider.id} value={provider.id}>
                {provider.name}
              </option>
            ))}
          </select>
        </div>

        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="e.g., OpenAI API Key"
            required
          />
        </div>

        {/* Secret Value */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Secret Value {!isEditing && <span className="text-red-400">*</span>}
          </label>
          <div className="relative">
            <input
              type={showValue ? 'text' : 'password'}
              value={formData.value}
              onChange={(e) => setFormData((prev) => ({ ...prev, value: e.target.value }))}
              className="w-full px-3 py-2 pr-10 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono text-sm"
              placeholder={isEditing ? 'Leave empty to keep current value' : 'Enter secret value'}
              required={!isEditing}
            />
            <button
              type="button"
              onClick={() => setShowValue(!showValue)}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-white transition-colors"
            >
              {showValue ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          {isEditing && (
            <p className="mt-1 text-xs text-slate-500">
              Leave empty to keep the current value unchanged
            </p>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            rows={3}
            placeholder="Optional description"
          />
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Tags</label>
          <input
            type="text"
            value={formData.tags}
            onChange={(e) => setFormData((prev) => ({ ...prev, tags: e.target.value }))}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Comma-separated tags (e.g., production, api)"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-4 border-t border-white/10">
          <button
            type="submit"
            disabled={isLoading}
            className={cn(
              'flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600',
              'text-white rounded-lg transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <Save className="w-4 h-4" />
            <span>{isLoading ? 'Saving...' : isEditing ? 'Update Secret' : 'Create Secret'}</span>
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

