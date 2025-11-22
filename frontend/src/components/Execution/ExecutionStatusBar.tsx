/**
 * Minimal execution status bar - shows during execution
 * Appears at the bottom of the canvas
 */

import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { useUIStore } from '@/store/uiStore';
import { Loader2, CheckCircle2, XCircle, Clock, ChevronUp } from 'lucide-react';
import { cn } from '@/utils/cn';

export function ExecutionStatusBar() {
  const { status, cost, currentNodeId } = useExecutionStore();
  const { nodes } = useWorkflowStore();
  const { toggleExecutionLogs, executionLogsOpen } = useUIStore();

  // Don't show if idle
  if (status === 'idle') {
    return null;
  }

  // Calculate progress
  const completedNodes = nodes.filter((node) => {
    const result = useExecutionStore.getState().results[node.id];
    return result?.status === 'completed';
  }).length;
  const totalNodes = nodes.length;
  const progress = totalNodes > 0 ? Math.round((completedNodes / totalNodes) * 100) : 0;

  // Get current node name
  const currentNode = currentNodeId ? nodes.find((n) => n.id === currentNodeId) : null;
  const currentNodeName = currentNode?.data?.label || currentNode?.type || currentNodeId || 'Unknown';

  // Status icon and color
  const statusConfig = {
    pending: { icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-500/20', border: 'border-yellow-500/30' },
    running: { icon: Loader2, color: 'text-blue-400', bg: 'bg-blue-500/20', border: 'border-blue-500/30' },
    completed: { icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-500/20', border: 'border-green-500/30' },
    failed: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/20', border: 'border-red-500/30' },
  };

  const config = statusConfig[status] || statusConfig.pending;
  const StatusIcon = config.icon;

  return (
    <div
      className={cn(
        'glass-strong border-t px-4 py-2 flex items-center justify-between gap-4',
        'transition-all duration-300',
        config.border
      )}
    >
      {/* Left: Status and Progress */}
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <div className={cn('flex items-center gap-2 flex-shrink-0', config.color)}>
          <StatusIcon
            className={cn('w-4 h-4', status === 'running' && 'animate-spin')}
          />
          <span className="text-sm font-medium capitalize">{status}</span>
        </div>

        {/* Progress Bar */}
        {status === 'running' || status === 'pending' ? (
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden min-w-[100px]">
              <div
                className={cn('h-full transition-all duration-300', config.bg)}
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-xs text-slate-400 flex-shrink-0">
              {completedNodes}/{totalNodes} nodes
            </span>
          </div>
        ) : null}

        {/* Current Node */}
        {status === 'running' && currentNodeName && (
          <div className="text-xs text-slate-300 truncate flex-shrink-0">
            <span className="text-slate-500">Executing:</span> {currentNodeName}
          </div>
        )}
      </div>

      {/* Right: Cost and Actions */}
      <div className="flex items-center gap-4 flex-shrink-0">
        {/* Cost */}
        {cost > 0 && (
          <div className="text-xs">
            <span className="text-slate-500">Cost:</span>{' '}
            <span className="font-medium text-slate-200">
              ${cost.toFixed(4)}
            </span>
          </div>
        )}

        {/* View Details Button */}
        <button
          onClick={toggleExecutionLogs}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
            'hover:bg-white/10 border border-white/10',
            executionLogsOpen && 'bg-white/10'
          )}
        >
          <span>View Details</span>
          <ChevronUp
            className={cn(
              'w-3 h-3 transition-transform',
              executionLogsOpen && 'rotate-180'
            )}
          />
        </button>
      </div>
    </div>
  );
}

