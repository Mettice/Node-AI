/**
 * Input component
 */

import { forwardRef } from 'react';
import type { InputHTMLAttributes } from 'react';
import { cn } from '@/utils/cn';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, value = '', ...props }, ref) => {
    return (
      <div>
        <input
          ref={ref}
          value={value}
          className={cn(
            'w-full px-3 py-2.5 rounded-lg transition-all',
            'bg-white/5 border border-white/10 text-slate-200 placeholder-slate-500',
            'focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white/8',
            'hover:bg-white/8 hover:border-white/20',
            error
              ? 'border-red-500/50 focus:ring-red-500'
              : '',
            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1 text-xs text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

