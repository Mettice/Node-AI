/**
 * Execution status icon component - displays on canvas
 */

import { useExecutionStore } from '@/store/executionStore';
import { CheckCircle2, XCircle, Loader2, Circle } from 'lucide-react';
import { cn } from '@/utils/cn';

export function ExecutionStatusIcon() {
  const { status } = useExecutionStore();

  const statusConfig = {
    idle: { icon: Circle, color: 'text-gray-400', bg: 'bg-gray-100', label: 'Ready' },
    pending: { icon: Loader2, color: 'text-yellow-600', bg: 'bg-yellow-100', label: 'Pending' },
    running: { icon: Loader2, color: 'text-blue-600', bg: 'bg-blue-100', label: 'Running' },
    completed: { icon: CheckCircle2, color: 'text-green-600', bg: 'bg-green-100', label: 'Completed' },
    failed: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-100', label: 'Failed' },
  };

  const config = statusConfig[status] || statusConfig.idle;
  const Icon = config.icon;
  const isSpinning = status === 'running' || status === 'pending';
  const isIdle = status === 'idle';

  return (
    <div
      className={cn(
        'flex items-center gap-0.5 px-1 py-0.5 rounded shadow-sm border',
        'bg-slate-800/70 backdrop-blur-sm',
        config.color,
        'border-white/15 opacity-75 hover:opacity-100 transition-all duration-200',
        'hover:shadow-md hover:scale-105'
      )}
      title={config.label}
    >
      {isIdle ? (
        <div className="relative flex items-center">
          <div className="w-1 h-1 bg-green-500 rounded-full animate-pulse shadow-[0_0_4px_rgba(34,197,94,0.6)]" />
        </div>
      ) : (
        <Icon
          className={cn('w-1 h-1', isSpinning && 'animate-spin')}
        />
      )}
      <span className="text-[6px] font-medium">{config.label}</span>
    </div>
  );
}

