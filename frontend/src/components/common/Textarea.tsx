/**
 * Textarea component
 */

import { forwardRef } from 'react';
import type { TextareaHTMLAttributes } from 'react';
import { cn } from '@/utils/cn';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, value = '', ...props }, ref) => {
    return (
      <div>
        <textarea
          ref={ref}
          value={value}
          className={cn(
            'w-full min-w-0 px-3 py-2.5 rounded-lg transition-all',
            'bg-white/5 border border-white/10 text-slate-200 placeholder-slate-500',
            'focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white/8',
            'hover:bg-white/8 hover:border-white/20',
            'resize-y overflow-x-auto',
            'break-words whitespace-pre-wrap',
            error
              ? 'border-red-500/50 focus:ring-red-500'
              : '',
            className
          )}
          style={{
            wordWrap: 'break-word',
            overflowWrap: 'break-word',
          }}
          {...props}
        />
        {error && (
          <p className="mt-1 text-xs text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

