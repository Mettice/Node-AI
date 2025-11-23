/**
 * Model Selector component for selecting fine-tuned models
 */

import { useQuery } from '@tanstack/react-query';
import { getAvailableModels } from '@/services/models';
import { Spinner } from '@/components/common/Spinner';
import { GraduationCap } from 'lucide-react';

interface ModelSelectorProps {
  provider: string;
  value: string;
  onChange: (modelId: string) => void;
  disabled?: boolean;
}

export function ModelSelector({ provider, value, onChange, disabled }: ModelSelectorProps) {
  const { data: models = [], isLoading, error } = useQuery({
    queryKey: ['available-models', provider],
    queryFn: () => getAvailableModels(provider, 'ready'),
    enabled: !!provider,
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-slate-400 text-sm">
        <Spinner size="sm" />
        <span>Loading models...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-400 text-sm">
        Failed to load models. Make sure you have fine-tuned models available.
      </div>
    );
  }

  if (models.length === 0) {
    return (
      <div className="text-slate-400 text-sm flex items-center gap-2">
        <GraduationCap className="w-4 h-4" />
        <span>No fine-tuned models available. Train a model first.</span>
      </div>
    );
  }

  return (
    <select
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <option value="">Select a fine-tuned model...</option>
      {models.map((model) => (
        <option key={model.id} value={model.id}>
          {model.name} ({model.base_model})
        </option>
      ))}
    </select>
  );
}

