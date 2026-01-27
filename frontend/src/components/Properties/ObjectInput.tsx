/**
 * Object input component for managing key-value pairs
 */

import { Plus, X } from 'lucide-react';

interface ObjectInputProps {
  value: Record<string, any>;
  onChange: (value: Record<string, any>) => void;
  keyPlaceholder?: string;
  valuePlaceholder?: string;
  label?: string;
}

export function ObjectInput({ 
  value = {}, 
  onChange, 
  keyPlaceholder = 'Key',
  valuePlaceholder = 'Value',
  label 
}: ObjectInputProps) {
  const entries = Object.entries(value);

  const handleAdd = () => {
    onChange({ ...value, '': '' });
  };

  const handleRemove = (key: string) => {
    const updated = { ...value };
    delete updated[key];
    onChange(updated);
  };

  const handleKeyChange = (oldKey: string, newKey: string, val: any) => {
    const updated = { ...value };
    delete updated[oldKey];
    if (newKey) {
      updated[newKey] = val;
    }
    onChange(updated);
  };

  const handleValueChange = (key: string, newValue: string) => {
    // Try to parse as number if it looks like a number
    let parsedValue: any = newValue;
    if (newValue !== '' && !isNaN(Number(newValue)) && newValue.trim() !== '') {
      // Check if it's an integer or float
      if (newValue.includes('.')) {
        parsedValue = parseFloat(newValue);
      } else {
        parsedValue = parseInt(newValue, 10);
      }
      // If parsing resulted in NaN, use string
      if (isNaN(parsedValue)) {
        parsedValue = newValue;
      }
    }
    
    onChange({ ...value, [key]: parsedValue });
  };

  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          {label}
        </label>
      )}
      <div className="space-y-2">
        {entries.map(([key, val]) => (
          <div key={key} className="flex items-center gap-2">
            <input
              type="text"
              value={key}
              onChange={(e) => handleKeyChange(key, e.target.value, val)}
              placeholder={keyPlaceholder}
              className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm"
            />
            <input
              type="text"
              value={val}
              onChange={(e) => handleValueChange(key, e.target.value)}
              placeholder={valuePlaceholder}
              className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm"
            />
            <button
              type="button"
              onClick={() => handleRemove(key)}
              className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={handleAdd}
          className="flex items-center gap-2 px-3 py-2 text-sm text-amber-300 hover:text-amber-200 hover:bg-amber-500/10 rounded transition-colors border border-amber-500/20"
        >
          <Plus className="w-4 h-4" />
          <span>Add Key-Value Pair</span>
        </button>
        {entries.length === 0 && (
          <p className="text-xs text-slate-500 italic">No key-value pairs. Click "Add Key-Value Pair" to add one.</p>
        )}
      </div>
    </div>
  );
}

