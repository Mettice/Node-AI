/**
 * Provider selector component for generic nodes
 */

import { SelectWithIcons } from '@/components/common/SelectWithIcons';

interface ProviderSelectorProps {
  nodeType: string;
  currentProvider: string;
  onChange: (provider: string) => void;
  /**
   * Providers the node's backend supports (its schema's `provider` enum). When given, only
   * these are offered, so every choice has matching model fields and actually runs.
   */
  allowedProviders?: string[];
}

// Labels and icons for known providers
const PROVIDER_META: Record<string, { label: string; icon: string }> = {
  openai: { label: 'OpenAI', icon: 'openai' },
  azure_openai: { label: 'Azure OpenAI', icon: 'microsoftazure' },
  anthropic: { label: 'Anthropic', icon: 'anthropic' },
  gemini: { label: 'Google Gemini', icon: 'gemini' },
  huggingface: { label: 'HuggingFace', icon: 'huggingface' },
  cohere: { label: 'Cohere', icon: 'cohere' },
  voyage_ai: { label: 'Voyage AI', icon: 'voyage_ai' },
  faiss: { label: 'FAISS', icon: 'faiss' },
  pinecone: { label: 'Pinecone', icon: 'pinecone' },
  azure_cognitive_search: { label: 'Azure Cognitive Search', icon: 'microsoftazure' },
  gemini_file_search: { label: 'Gemini File Search', icon: 'gemini_file_search' },
  local: { label: 'Local', icon: 'local' },
};

// Used only when the node's schema does not list its providers
const DEFAULT_LLM_PROVIDERS = ['openai', 'anthropic', 'gemini'];

function toOption(value: string) {
  const meta = PROVIDER_META[value];
  return {
    value,
    label: meta?.label ?? value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    icon: meta?.icon ?? value,
  };
}

export function ProviderSelector({
  nodeType,
  currentProvider,
  onChange,
  allowedProviders,
}: ProviderSelectorProps) {
  const options = (allowedProviders?.length ? allowedProviders : DEFAULT_LLM_PROVIDERS).map(toOption);

  if (options.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
        Provider <span className="text-red-400">*</span>
      </label>
      <p className="text-xs text-slate-400 -mt-1">
        Select the provider for this {nodeType} node
      </p>
      <SelectWithIcons
        value={currentProvider}
        onChange={onChange}
        options={options}
        placeholder="Select a provider..."
      />
    </div>
  );
}
