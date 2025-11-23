/**
 * S3 Action Selector Component
 * Displays S3 action types in a dropdown
 */

import { SelectWithIcons } from '@/components/common/SelectWithIcons';

interface S3ActionSelectorProps {
  currentAction: string;
  onChange: (action: string) => void;
}

// S3 action options with icons
const S3_ACTION_OPTIONS = [
  { value: 'list', label: 'List Objects', icon: 'database' },
  { value: 'download', label: 'Download', icon: 'database' },
  { value: 'upload', label: 'Upload', icon: 'database' },
  { value: 'delete', label: 'Delete', icon: 'database' },
  { value: 'get_url', label: 'Get URL', icon: 'database' },
];

export function S3ActionSelector({
  currentAction,
  onChange,
}: S3ActionSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
        Action <span className="text-red-400">*</span>
      </label>
      <p className="text-xs text-slate-400 -mt-1">
        Select the S3 operation to perform
      </p>
      <SelectWithIcons
        value={currentAction || 'list'}
        onChange={onChange}
        options={S3_ACTION_OPTIONS}
        placeholder="Select an action..."
      />
    </div>
  );
}

