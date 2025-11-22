/**
 * Tool Type Selector Component
 * Displays tool types with icons in a dropdown
 */

import { SelectWithIcons } from '@/components/common/SelectWithIcons';

interface ToolTypeSelectorProps {
  currentToolType: string;
  onChange: (toolType: string) => void;
}

// Tool type options with icons (matching ProviderIcon tool type icons)
const TOOL_TYPE_OPTIONS = [
  { value: 'calculator', label: 'Calculator', icon: 'calculator' },
  { value: 'web_search', label: 'Web Search', icon: 'search' },
  { value: 'web_scraping', label: 'Web Scraping', icon: 'web_scraping' },
  { value: 'rss_feed', label: 'RSS Feed', icon: 'rss_feed' },
  { value: 's3_storage', label: 'S3 Storage', icon: 's3' },
  { value: 'code_execution', label: 'Code Execution', icon: 'code' },
  { value: 'database_query', label: 'Database Query', icon: 'database' },
  { value: 'api_call', label: 'API Call', icon: 'api' },
  { value: 'email', label: 'Email', icon: 'email' },
  { value: 'custom', label: 'Custom', icon: 'wrench' },
];

export function ToolTypeSelector({
  currentToolType,
  onChange,
}: ToolTypeSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
        Tool Type <span className="text-red-400">*</span>
      </label>
      <p className="text-xs text-slate-400 -mt-1">
        Select the type of tool to create
      </p>
      <SelectWithIcons
        value={currentToolType || 'calculator'}
        onChange={onChange}
        options={TOOL_TYPE_OPTIONS}
        placeholder="Select a tool type..."
      />
    </div>
  );
}

