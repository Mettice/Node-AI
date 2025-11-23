/**
 * Card component
 */

import type { ReactNode } from 'react';
import { cn } from '@/utils/cn';

interface CardProps {
  children: ReactNode;
  className?: string;
  header?: ReactNode;
  footer?: ReactNode;
}

export function Card({ children, className, header, footer }: CardProps) {
  return (
    <div className={cn('bg-white rounded-lg shadow-md border border-gray-200', className)}>
      {header && (
        <div className="px-4 py-3 border-b border-gray-200">
          {header}
        </div>
      )}
      <div className="p-4">
        {children}
      </div>
      {footer && (
        <div className="px-4 py-3 border-t border-gray-200">
          {footer}
        </div>
      )}
    </div>
  );
}

