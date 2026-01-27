/**
 * Select component with icons in dropdown options
 * Custom dropdown that displays icons for each option
 */

import { useState, useRef, useEffect } from 'react';
import { ProviderIcon } from './ProviderIcon';
import { cn } from '@/utils/cn';
import { ChevronDown } from 'lucide-react';

interface SelectOption {
  value: string;
  label: string;
  icon?: string; // Provider name for icon lookup
}

interface SelectWithIconsProps {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  className?: string;
  error?: string;
}

export function SelectWithIcons({
  value,
  onChange,
  options,
  placeholder = 'Select an option...',
  className,
  error,
}: SelectWithIconsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((opt) => opt.value === value);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  return (
    <div className={cn('relative', className)} ref={containerRef}>
      {/* Selected value button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'w-full px-3 py-2 pl-10 bg-white/5 border rounded-lg text-left',
          'focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent',
          'transition-all flex items-center justify-between',
          error
            ? 'border-red-500/50 focus:ring-red-500'
            : 'border-white/10 hover:bg-white/8 hover:border-white/20',
          isOpen && 'ring-2 ring-amber-500 border-transparent'
        )}
      >
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {selectedOption && selectedOption.icon && (
            <div className="flex-shrink-0">
              <ProviderIcon provider={selectedOption.icon} size="sm" />
            </div>
          )}
          <span className={cn('text-sm truncate', selectedOption ? 'text-white' : 'text-slate-400')}>
            {selectedOption ? selectedOption.label : placeholder}
          </span>
        </div>
        <ChevronDown
          className={cn(
            'w-4 h-4 text-slate-400 flex-shrink-0 transition-transform',
            isOpen && 'transform rotate-180'
          )}
        />
      </button>

      {/* Dropdown menu */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Options list */}
          <div className="absolute z-50 w-full mt-1 bg-slate-800 border border-white/10 rounded-lg shadow-xl max-h-60 overflow-auto">
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
                className={cn(
                  'w-full px-3 py-2 flex items-center gap-2 text-left',
                  'hover:bg-white/10 transition-colors',
                  'first:rounded-t-lg last:rounded-b-lg',
                  value === option.value && 'bg-amber-500/20'
                )}
              >
                {option.icon && (
                  <div className="flex-shrink-0">
                    <ProviderIcon provider={option.icon} size="sm" />
                  </div>
                )}
                <span className="text-sm text-white flex-1">{option.label}</span>
                {value === option.value && (
                  <svg
                    className="w-4 h-4 text-amber-400 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </>
      )}

      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  );
}

