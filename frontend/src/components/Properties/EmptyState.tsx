/**
 * Empty state component for properties panel
 */

import { FileText } from 'lucide-react';

export function EmptyState() {
  return (
    <div className="h-full flex items-center justify-center p-8">
      <div className="text-center">
        <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          No Node Selected
        </h3>
        <p className="text-sm text-gray-600">
          Select a node from the canvas to configure its properties
        </p>
      </div>
    </div>
  );
}

