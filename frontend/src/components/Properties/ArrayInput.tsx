/**
 * Array input component for managing lists of strings
 */

import { Plus, X } from 'lucide-react';

interface ArrayInputProps {
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  label?: string;
}

export function ArrayInput({ value = [], onChange, placeholder = 'Enter value', label }: ArrayInputProps) {
  const handleAdd = () => {
    onChange([...value, '']);
  };

  const handleRemove = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  const handleChange = (index: number, newValue: string) => {
    const updated = [...value];
    updated[index] = newValue;
    onChange(updated);
  };

  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          {label}
        </label>
      )}
      <div className="space-y-2">
        {value.map((item, index) => (
          <div key={index} className="flex items-center gap-2">
            <input
              type="text"
              value={item}
              onChange={(e) => handleChange(index, e.target.value)}
              placeholder={placeholder}
              className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
            />
            <button
              type="button"
              onClick={() => handleRemove(index)}
              className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={handleAdd}
          className="flex items-center gap-2 px-3 py-2 text-sm text-purple-300 hover:text-purple-200 hover:bg-purple-500/10 rounded transition-colors border border-purple-500/20"
        >
          <Plus className="w-4 h-4" />
          <span>Add Item</span>
        </button>
        {value.length === 0 && (
          <p className="text-xs text-slate-500 italic">No items. Click "Add Item" to add one.</p>
        )}
      </div>
    </div>
  );
}

