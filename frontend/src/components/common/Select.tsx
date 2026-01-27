/**
 * Select component
 */

import { forwardRef } from 'react';
import type { SelectHTMLAttributes } from 'react';
import { cn } from '@/utils/cn';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'onChange'> {
  options: SelectOption[];
  error?: string;
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, options, error, onChange, value, ...props }, ref) => {
    // Ensure value is never null - convert to empty string
    const safeValue = value ?? '';
    
    return (
      <div>
        <select
          ref={ref}
          value={safeValue}
          onChange={onChange}
          className={cn(
            'w-full px-3 py-2.5 rounded-lg transition-all',
            'bg-white/5 border border-white/10 text-slate-200',
            'focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent focus:bg-white/8',
            'hover:bg-white/8 hover:border-white/20',
            error
              ? 'border-red-500/50 focus:ring-red-500'
              : '',
            className
          )}
          {...props}
        >
          {!safeValue && <option value="" className="bg-slate-800 text-slate-300">Select an option...</option>}
          {options.map((option) => (
            <option key={option.value} value={option.value} className="bg-slate-800 text-slate-200">
              {option.label}
            </option>
          ))}
        </select>
        {error && (
          <p className="mt-1 text-xs text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';

