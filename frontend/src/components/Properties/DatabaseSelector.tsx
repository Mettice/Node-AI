/**
 * Database Selector Component
 * Displays database types with icons in a dropdown
 */

import { SelectWithIcons } from '@/components/common/SelectWithIcons';

interface DatabaseSelectorProps {
  currentDatabase: string;
  onChange: (database: string) => void;
}

// Database type options with icons
const DATABASE_OPTIONS = [
  { value: 'sqlite', label: 'SQLite', icon: 'sqlite' },
  { value: 'postgresql', label: 'PostgreSQL', icon: 'postgresql' },
  { value: 'mysql', label: 'MySQL', icon: 'mysql' },
];

export function DatabaseSelector({
  currentDatabase,
  onChange,
}: DatabaseSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
        Database Type <span className="text-red-400">*</span>
      </label>
      <p className="text-xs text-slate-400 -mt-1">
        Select the database type
      </p>
      <SelectWithIcons
        value={currentDatabase || 'sqlite'}
        onChange={onChange}
        options={DATABASE_OPTIONS}
        placeholder="Select a database type..."
      />
    </div>
  );
}

