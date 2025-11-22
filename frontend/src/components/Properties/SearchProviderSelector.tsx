/**
 * Search Provider Selector Component
 * Displays search providers with icons in a dropdown
 */

import { SelectWithIcons } from '@/components/common/SelectWithIcons';

interface SearchProviderSelectorProps {
  currentProvider: string;
  onChange: (provider: string) => void;
}

// Search provider options with icons
const SEARCH_PROVIDER_OPTIONS = [
  { value: 'duckduckgo', label: 'DuckDuckGo', icon: 'duckduckgo' },
  { value: 'serpapi', label: 'SerpAPI', icon: 'serpapi' },
  { value: 'brave', label: 'Brave Search', icon: 'brave' },
  { value: 'serper', label: 'Serper', icon: 'serper' },
  { value: 'perplexity', label: 'Perplexity', icon: 'perplexity' },
];

export function SearchProviderSelector({
  currentProvider,
  onChange,
}: SearchProviderSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
        Search Provider <span className="text-red-400">*</span>
      </label>
      <p className="text-xs text-slate-400 -mt-1">
        Select the web search provider to use
      </p>
      <SelectWithIcons
        value={currentProvider || 'duckduckgo'}
        onChange={onChange}
        options={SEARCH_PROVIDER_OPTIONS}
        placeholder="Select a search provider..."
      />
    </div>
  );
}

