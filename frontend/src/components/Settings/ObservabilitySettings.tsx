/**
 * Observability Settings Component - Configure LangSmith/LangFuse
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, Eye, EyeOff, CheckCircle2, XCircle, Info, ExternalLink } from 'lucide-react';
import { observabilityApi, type ObservabilitySettings } from '@/services/observability';
import toast from 'react-hot-toast';
import { cn } from '@/utils/cn';

export function ObservabilitySettings() {
  const queryClient = useQueryClient();
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [formData, setFormData] = useState<Partial<ObservabilitySettings>>({});
  const [hasChanges, setHasChanges] = useState(false);

  const { data: settings, isLoading } = useQuery({
    queryKey: ['observability-settings'],
    queryFn: () => observabilityApi.get(),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<ObservabilitySettings>) => observabilityApi.update(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['observability-settings'] });
      toast.success('Observability settings saved successfully');
      setHasChanges(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    },
  });

  useEffect(() => {
    if (settings) {
      setFormData({
        langsmith_api_key: settings.langsmith_api_key || '',
        langsmith_project: settings.langsmith_project || 'nodeflow',
        langfuse_public_key: settings.langfuse_public_key || '',
        langfuse_secret_key: settings.langfuse_secret_key || '',
        langfuse_host: settings.langfuse_host || 'https://cloud.langfuse.com',
        enabled: settings.enabled ?? true,
      });
    }
  }, [settings]);

  const handleChange = (field: keyof ObservabilitySettings, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const handleSave = () => {
    updateMutation.mutate(formData);
  };

  const toggleKeyVisibility = (key: string) => {
    setShowKeys((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const isKeyMasked = (value?: string | null) => {
    if (!value) return false;
    return value.startsWith('•') || value.length <= 4;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white mb-1">Observability Settings</h3>
        <p className="text-sm text-slate-400">
          Configure LangSmith or LangFuse for tracing and monitoring your workflows
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-6">
        {/* Enable/Disable Toggle */}
        <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-white mb-1">Enable Observability</h4>
              <p className="text-xs text-slate-400">
                Track and monitor your workflow executions with LangSmith or LangFuse
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formData.enabled ?? true}
                onChange={(e) => handleChange('enabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-purple-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-500"></div>
            </label>
          </div>
        </div>

        {/* LangSmith Settings */}
        <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-white mb-1">LangSmith</h4>
              <p className="text-xs text-slate-400">
                LangChain's observability platform for tracing and monitoring
              </p>
            </div>
            <a
              href="https://smith.langchain.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
            >
              Get API Key <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                API Key
              </label>
              <div className="relative">
                <input
                  type={showKeys.langsmith ? 'text' : 'password'}
                  value={formData.langsmith_api_key || ''}
                  onChange={(e) => handleChange('langsmith_api_key', e.target.value)}
                  placeholder="ls-..."
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleKeyVisibility('langsmith')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-white"
                >
                  {showKeys.langsmith ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              {isKeyMasked(formData.langsmith_api_key) && (
                <p className="mt-1 text-xs text-slate-500">
                  Enter a new key to replace the existing one
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Project Name
              </label>
              <input
                type="text"
                value={formData.langsmith_project || 'nodeflow'}
                onChange={(e) => handleChange('langsmith_project', e.target.value)}
                placeholder="nodeflow"
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
        </div>

        {/* LangFuse Settings */}
        <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-white mb-1">LangFuse</h4>
              <p className="text-xs text-slate-400">
                Open-source observability platform for LLM applications
              </p>
            </div>
            <a
              href="https://langfuse.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
            >
              Get API Keys <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Public Key
              </label>
              <div className="relative">
                <input
                  type={showKeys.langfuse_public ? 'text' : 'password'}
                  value={formData.langfuse_public_key || ''}
                  onChange={(e) => handleChange('langfuse_public_key', e.target.value)}
                  placeholder="pk-..."
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleKeyVisibility('langfuse_public')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-white"
                >
                  {showKeys.langfuse_public ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              {isKeyMasked(formData.langfuse_public_key) && (
                <p className="mt-1 text-xs text-slate-500">
                  Enter a new key to replace the existing one
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Secret Key
              </label>
              <div className="relative">
                <input
                  type={showKeys.langfuse_secret ? 'text' : 'password'}
                  value={formData.langfuse_secret_key || ''}
                  onChange={(e) => handleChange('langfuse_secret_key', e.target.value)}
                  placeholder="sk-..."
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleKeyVisibility('langfuse_secret')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-white"
                >
                  {showKeys.langfuse_secret ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              {isKeyMasked(formData.langfuse_secret_key) && (
                <p className="mt-1 text-xs text-slate-500">
                  Enter a new key to replace the existing one
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Host URL
              </label>
              <input
                type="text"
                value={formData.langfuse_host || 'https://cloud.langfuse.com'}
                onChange={(e) => handleChange('langfuse_host', e.target.value)}
                placeholder="https://cloud.langfuse.com"
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <p className="mt-1 text-xs text-slate-500">
                Use your self-hosted URL if applicable
              </p>
            </div>
          </div>
        </div>

        {/* Info Box */}
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-slate-300 space-y-1">
              <p className="font-medium">About Observability</p>
              <p className="text-slate-400">
                Observability tools help you track workflow executions, monitor costs, debug issues,
                and analyze performance. You can use either LangSmith or LangFuse (or both).
                Settings are stored securely and only used for your workflows.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="mt-6 pt-4 border-t border-white/10">
        <button
          onClick={handleSave}
          disabled={!hasChanges || updateMutation.isPending}
          className={cn(
            'flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600',
            'text-white rounded-lg transition-colors',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          <Save className="w-4 h-4" />
          <span>{updateMutation.isPending ? 'Saving...' : 'Save Settings'}</span>
        </button>
      </div>
    </div>
  );
}

