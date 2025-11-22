/**
 * Execution status display component
 */

import { useExecutionStore } from '@/store/executionStore';
import { cn } from '@/utils/cn';

const statusConfig = {
  idle: { label: 'Ready', color: 'text-slate-300', bg: 'bg-slate-500/20 border border-slate-500/30' },
  pending: { label: 'Pending...', color: 'text-yellow-300', bg: 'bg-yellow-500/20 border border-yellow-500/30' },
  running: { label: 'Running...', color: 'text-blue-300', bg: 'bg-blue-500/20 border border-blue-500/30' },
  completed: { label: 'Completed', color: 'text-green-300', bg: 'bg-green-500/20 border border-green-500/30' },
  failed: { label: 'Failed', color: 'text-red-300', bg: 'bg-red-500/20 border border-red-500/30' },
};

export function ExecutionStatus() {
  const { status, duration, error } = useExecutionStore();
  const config = statusConfig[status] || statusConfig.idle;

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
    return `${(ms / 60000).toFixed(2)}m`;
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-400">Status:</span>
        <span className={cn('px-2 py-1 rounded text-sm font-medium', config.color, config.bg)}>
          {config.label}
        </span>
      </div>

      {error && (
        <div className="mt-2 p-2 bg-red-900/30 border border-red-500/30 rounded">
          <span className="text-sm text-red-300">{error}</span>
        </div>
      )}
    </div>
  );
}

