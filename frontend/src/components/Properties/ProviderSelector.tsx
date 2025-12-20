/**
 * Provider selector component for generic nodes
 */

import { SelectWithIcons } from '@/components/common/SelectWithIcons';

interface ProviderSelectorProps {
  nodeType: string;
  currentProvider: string;
  onChange: (provider: string) => void;
}

// Default LLM provider options (used for nodes with LLM config)
const DEFAULT_LLM_PROVIDERS = [
  { value: 'openai', label: 'OpenAI', icon: 'openai' },
  { value: 'azure_openai', label: 'Azure OpenAI', icon: 'microsoftazure' },
  { value: 'anthropic', label: 'Anthropic', icon: 'anthropic' },
  { value: 'gemini', label: 'Google Gemini', icon: 'gemini' },
];

// Provider options by node type (with icon references)
const PROVIDER_OPTIONS: Record<string, Array<{ value: string; label: string; icon: string }>> = {
  embed: [
    { value: 'openai', label: 'OpenAI', icon: 'openai' },
    { value: 'azure_openai', label: 'Azure OpenAI', icon: 'microsoftazure' },
    { value: 'huggingface', label: 'HuggingFace', icon: 'huggingface' },
    { value: 'cohere', label: 'Cohere', icon: 'cohere' },
    { value: 'voyage_ai', label: 'Voyage AI', icon: 'voyage_ai' },
    { value: 'gemini', label: 'Google Gemini', icon: 'gemini' },
  ],
  vector_store: [
    { value: 'faiss', label: 'FAISS', icon: 'faiss' },
    { value: 'pinecone', label: 'Pinecone', icon: 'pinecone' },
    { value: 'azure_cognitive_search', label: 'Azure Cognitive Search', icon: 'microsoftazure' },
    { value: 'gemini_file_search', label: 'Gemini File Search', icon: 'gemini_file_search' },
  ],
  vector_search: [
    { value: 'faiss', label: 'FAISS', icon: 'faiss' },
    { value: 'pinecone', label: 'Pinecone', icon: 'pinecone' },
    { value: 'azure_cognitive_search', label: 'Azure Cognitive Search', icon: 'microsoftazure' },
  ],
  chat: DEFAULT_LLM_PROVIDERS,
  vision: DEFAULT_LLM_PROVIDERS,
  langchain_agent: DEFAULT_LLM_PROVIDERS,
  crewai_agent: DEFAULT_LLM_PROVIDERS,
  // New LLM nodes using LLMConfigMixin
  smart_data_analyzer: DEFAULT_LLM_PROVIDERS,
  blog_generator: DEFAULT_LLM_PROVIDERS,
  proposal_generator: DEFAULT_LLM_PROVIDERS,
  // Add other LLM nodes as needed
};

export function ProviderSelector({
  nodeType,
  currentProvider,
  onChange,
}: ProviderSelectorProps) {
  const options = PROVIDER_OPTIONS[nodeType] || DEFAULT_LLM_PROVIDERS;

  if (options.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
        LLM Provider <span className="text-red-400">*</span>
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

