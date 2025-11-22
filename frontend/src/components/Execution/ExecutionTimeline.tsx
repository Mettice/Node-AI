/**
 * Visual Timeline Component - Shows execution flow
 */

import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { CheckCircle2, XCircle, Clock, Loader2 } from 'lucide-react';
import { cn } from '@/utils/cn';

export function ExecutionTimeline() {
  const { results, trace } = useExecutionStore();
  const { nodes, edges } = useWorkflowStore();

  // Build execution order from trace
  const executionOrder = trace
    .filter((step) => step.action === 'started' || step.action === 'completed')
    .map((step) => step.node_id)
    .filter((id, index, arr) => arr.indexOf(id) === index); // Unique nodes

  // Get node info
  const timelineNodes = executionOrder.map((nodeId) => {
    const node = nodes.find((n) => n.id === nodeId);
    const result = results[nodeId];
    const nodeName = node?.data?.label || node?.type || nodeId;
    
    return {
      id: nodeId,
      name: nodeName,
      status: result?.status || 'pending',
      duration: result?.duration_ms || 0,
    };
  });

  if (timelineNodes.length === 0) {
    return (
      <div className="p-4 text-center text-slate-400 text-sm">
        <Clock className="w-6 h-6 mx-auto mb-2 opacity-50" />
        <p>Execution timeline will appear here</p>
      </div>
    );
  }

  const statusConfig = {
    completed: { icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-500/20', border: 'border-green-500' },
    failed: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/20', border: 'border-red-500' },
    running: { icon: Loader2, color: 'text-blue-400', bg: 'bg-blue-500/20', border: 'border-blue-500' },
    pending: { icon: Clock, color: 'text-slate-400', bg: 'bg-slate-500/20', border: 'border-slate-500' },
  };

  return (
    <div className="p-4">
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-white/10" />

        {/* Timeline nodes */}
        <div className="space-y-4">
          {timelineNodes.map((item, index) => {
            const config = statusConfig[item.status as keyof typeof statusConfig] || statusConfig.pending;
            const Icon = config.icon;
            const isLast = index === timelineNodes.length - 1;

            return (
              <div key={item.id} className="relative flex items-start gap-3">
                {/* Timeline dot */}
                <div className={cn(
                  'relative z-10 flex items-center justify-center w-8 h-8 rounded-full border-2',
                  config.bg,
                  config.border
                )}>
                  <Icon className={cn('w-4 h-4', config.color, item.status === 'running' && 'animate-spin')} />
                </div>

                {/* Node info */}
                <div className="flex-1 min-w-0 pt-1">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-medium text-slate-200 truncate">
                      {item.name}
                    </div>
                    {item.duration > 0 && (
                      <div className="text-xs text-slate-400 flex-shrink-0">
                        {item.duration < 1000 ? `${item.duration}ms` : `${(item.duration / 1000).toFixed(2)}s`}
                      </div>
                    )}
                  </div>
                  <div className={cn('text-xs mt-0.5', config.color)}>
                    {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

