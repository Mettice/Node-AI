/**
 * Multi-select dropdown component with tags/chips display
 * Similar to SelectWithIcons but allows multiple selections
 */

import { useState, useRef, useEffect } from 'react';
import { ProviderIcon } from './ProviderIcon';
import { cn } from '@/utils/cn';
import { ChevronDown, X } from 'lucide-react';

interface MultiSelectOption {
  value: string;
  label: string;
  icon?: string; // Provider name for icon lookup
}

interface MultiSelectDropdownProps {
  value: string[];
  onChange: (value: string[]) => void;
  options: MultiSelectOption[];
  placeholder?: string;
  className?: string;
  error?: string;
  maxSelections?: number;
}

export function MultiSelectDropdown({
  value = [],
  onChange,
  options,
  placeholder = 'Select options...',
  className,
  error,
  maxSelections,
}: MultiSelectDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [dropdownPosition, setDropdownPosition] = useState<'bottom' | 'top'>('bottom');
  const containerRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const selectedOptionRef = useRef<HTMLButtonElement>(null);

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

  // Calculate dropdown position and scroll to selected option when dropdown opens
  useEffect(() => {
    if (isOpen && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom;
      const spaceAbove = rect.top;
      const dropdownHeight = 240; // max-h-60 = 240px
      
      // Position dropdown above if not enough space below
      if (spaceBelow < dropdownHeight && spaceAbove > spaceBelow) {
        setDropdownPosition('top');
      } else {
        setDropdownPosition('bottom');
      }

      // Scroll to selected option
      if (selectedOptionRef.current && dropdownRef.current) {
        setTimeout(() => {
          selectedOptionRef.current?.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
          });
        }, 100);
      }
    }
  }, [isOpen, value]);

  const handleToggle = (optionValue: string) => {
    const currentValue = value || [];
    if (currentValue.includes(optionValue)) {
      // Remove if already selected
      onChange(currentValue.filter((v) => v !== optionValue));
    } else {
      // Add if not selected (check max selections)
      if (maxSelections && currentValue.length >= maxSelections) {
        return; // Don't add if max reached
      }
      onChange([...currentValue, optionValue]);
    }
  };

  const handleRemove = (optionValue: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const currentValue = value || [];
    onChange(currentValue.filter((v) => v !== optionValue));
  };

  const selectedOptions = options.filter((opt) => value?.includes(opt.value));
  const displayText = selectedOptions.length > 0 
    ? `${selectedOptions.length} selected`
    : placeholder;

  return (
    <div className={cn('relative', className)} ref={containerRef}>
      {/* Selected values button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'w-full min-h-[42px] px-3 py-2 bg-white/5 border rounded-lg text-left',
          'focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent',
          'transition-all flex items-center justify-between gap-2',
          error
            ? 'border-red-500/50 focus:ring-red-500'
            : 'border-white/10 hover:bg-white/8 hover:border-white/20',
          isOpen && 'ring-2 ring-purple-500 border-transparent'
        )}
      >
        <div className="flex-1 min-w-0 flex flex-wrap gap-1.5 items-center">
          {selectedOptions.length > 0 ? (
            selectedOptions.map((option) => (
              <span
                key={option.value}
                className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-500/20 border border-purple-500/30 rounded text-xs text-purple-200"
              >
                {option.icon && (
                  <ProviderIcon provider={option.icon} size="sm" />
                )}
                <span className="truncate max-w-[120px]">{option.label}</span>
                <span
                  role="button"
                  tabIndex={0}
                  onClick={(e) => handleRemove(option.value, e)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleRemove(option.value, e as any);
                    }
                  }}
                  className="ml-0.5 hover:text-red-300 transition-colors cursor-pointer focus:outline-none focus:ring-1 focus:ring-red-300 rounded"
                  aria-label={`Remove ${option.label}`}
                >
                  <X className="w-3 h-3" />
                </span>
              </span>
            ))
          ) : (
            <span className="text-sm text-slate-400">{displayText}</span>
          )}
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
          <div 
            ref={dropdownRef}
            className={cn(
              "absolute z-50 w-full bg-slate-800 border border-white/10 rounded-lg shadow-xl max-h-60 overflow-auto",
              dropdownPosition === 'top' ? 'bottom-full mb-1' : 'top-full mt-1'
            )}
            style={{ scrollBehavior: 'smooth' }}
          >
            {options.map((option) => {
              const isSelected = value?.includes(option.value);
              const isDisabled = !!(maxSelections && !isSelected && (value?.length || 0) >= maxSelections);
              
              return (
                <button
                  key={option.value}
                  ref={isSelected ? selectedOptionRef : null}
                  type="button"
                  onClick={() => handleToggle(option.value)}
                  disabled={isDisabled}
                  className={cn(
                    'w-full px-3 py-2 flex items-center gap-2 text-left',
                    'transition-colors',
                    'first:rounded-t-lg last:rounded-b-lg',
                    isDisabled
                      ? 'opacity-50 cursor-not-allowed'
                      : 'hover:bg-white/10',
                    isSelected && 'bg-purple-500/20'
                  )}
                >
                  {/* Checkbox indicator */}
                  <div className={cn(
                    'w-4 h-4 border rounded flex items-center justify-center flex-shrink-0',
                    isSelected
                      ? 'bg-purple-500 border-purple-500'
                      : 'border-white/20'
                  )}>
                    {isSelected && (
                      <svg
                        className="w-3 h-3 text-white"
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
                  </div>
                  
                  {option.icon && (
                    <div className="flex-shrink-0">
                      <ProviderIcon provider={option.icon} size="sm" />
                    </div>
                  )}
                  
                  <span className="text-sm text-white flex-1">{option.label}</span>
                </button>
              );
            })}
          </div>
        </>
      )}

      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
      {maxSelections && (
        <p className="mt-1 text-xs text-slate-500">
          {value?.length || 0} / {maxSelections} selected
        </p>
      )}
    </div>
  );
}

