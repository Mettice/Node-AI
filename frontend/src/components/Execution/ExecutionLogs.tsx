/**
 * Execution logs component
 */

import { useExecutionStore } from '@/store/executionStore';
import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { ExecutionStep } from '@/types/api';

const statusIcons = {
  pending: Clock,
  running: Loader2,
  completed: CheckCircle2,
  failed: XCircle,
};

const statusColors = {
  pending: 'text-slate-400',
  running: 'text-blue-400',
  completed: 'text-green-400',
  failed: 'text-red-400',
  error: 'text-red-400',
};

export function ExecutionLogs() {
  const { trace, status, results, nodeEvents } = useExecutionStore();

  const formatTime = (timestamp?: string) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleTimeString();
  };

  if (status === 'idle' || trace.length === 0) {
    return (
      <div className="p-4 text-center text-slate-400">
        <p>No execution logs yet</p>
        <p className="text-sm mt-1">Run a workflow to see execution logs</p>
      </div>
    );
  }

  // Flatten all node events into a single chronological list
  const allEvents = Object.entries(nodeEvents).flatMap(([nodeId, events]) =>
    events.map((event, idx) => ({
      ...event,
      nodeId,
      uniqueKey: `${nodeId}-${event.event_type}-${event.timestamp}-${idx}`,
    }))
  ).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  return (
    <div className="p-4 space-y-4">
      {/* Real-time Event Feed */}
      {allEvents.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Live Activity Feed</h3>
          <div className="space-y-1.5 max-h-96 overflow-y-auto">
            {allEvents.map((event) => {
              const isProgress = event.event_type === 'node_progress';
              const isAgentEvent = event.event_type.startsWith('agent_');
              const isTaskEvent = event.event_type.startsWith('task_');
              const isNodeEvent = event.event_type.startsWith('node_');

              return (
                <div
                  key={event.uniqueKey}
                  className={cn(
                    'flex items-start gap-2 p-2 rounded text-xs',
                    isProgress && 'bg-blue-500/5 border border-blue-500/20',
                    isAgentEvent && 'bg-purple-500/5 border border-purple-500/20',
                    isTaskEvent && 'bg-green-500/5 border border-green-500/20',
                    isNodeEvent && !isProgress && 'bg-slate-500/5 border border-slate-500/20'
                  )}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {isProgress && event.progress !== undefined && (
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                    )}
                    {isAgentEvent && <div className="text-purple-400">🤖</div>}
                    {isTaskEvent && <div className="text-green-400">📋</div>}
                    {isNodeEvent && !isProgress && <div className="w-1.5 h-1.5 rounded-full bg-slate-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-300 truncate">{event.nodeId}</span>
                      {event.progress !== undefined && (
                        <span className="text-blue-400 font-medium">
                          {Math.round(event.progress * 100)}%
                        </span>
                      )}
                    </div>
                    {event.message && (
                      <div className="text-slate-400 mt-0.5">{event.message}</div>
                    )}
                  </div>
                  <span className="text-xs text-slate-500 flex-shrink-0">
                    {formatTime(event.timestamp)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Traditional Trace Logs */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-slate-200 mb-3">Execution Trace</h3>
        {trace.map((step: ExecutionStep, index: number) => {
        // Extract status from step.data.status or default to action
        const status = (step.data?.status || step.action || 'pending') as keyof typeof statusIcons;
        const StatusIcon = statusIcons[status] || Clock;
        const statusColor = statusColors[status as keyof typeof statusColors] || 'text-slate-400';
        const isRunning = status === 'running';
        
        // Get actual node output from results (not from trace)
        const nodeResult = results[step.node_id];
        const hasOutput = nodeResult?.output && Object.keys(nodeResult.output).length > 0;
        
        // Create unique key using node_id, action, and timestamp
        const uniqueKey = `${step.node_id}-${step.action}-${step.timestamp}-${index}`;

        return (
          <div
            key={uniqueKey}
            className={cn(
              'flex items-start gap-3 p-3 rounded-lg border glass',
              status === 'completed' && 'border-green-500/30 bg-green-500/10',
              (status === 'failed' || step.action === 'error') && 'border-red-500/30 bg-red-500/10',
              status === 'running' && 'border-blue-500/30 bg-blue-500/10',
              status === 'pending' && 'border-slate-500/30 bg-slate-500/10'
            )}
          >
            <StatusIcon
              className={cn(
                'w-5 h-5 mt-0.5 flex-shrink-0',
                statusColor,
                isRunning && 'animate-spin'
              )}
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-200">
                  Node: {step.node_id}
                </span>
                {step.timestamp && (
                  <span className="text-xs text-slate-400">
                    {formatTime(step.timestamp)}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className={cn('text-xs font-medium', statusColor)}>
                  {String(status).toUpperCase()}
                </span>
              </div>
              {(step.data?.error || nodeResult?.error) && (
                <div className="mt-2 text-xs text-red-300 bg-red-900/30 border border-red-500/30 p-2 rounded">
                  {step.data?.error || nodeResult?.error}
                </div>
              )}
              {hasOutput && status === 'completed' && (
                <div className="mt-2 text-xs text-slate-300">
                  <details className="cursor-pointer">
                    <summary className="font-medium hover:text-slate-200">▶ View Output</summary>
                    <div className="mt-2 space-y-2">
                      {/* Special handling for CrewAI output */}
                      {nodeResult.output?.output && typeof nodeResult.output.output === 'string' && (
                        <div className="p-3 bg-white/5 border border-white/10 rounded">
                          <div className="text-xs font-semibold text-purple-400 mb-2">CrewAI Report</div>
                          <div className="text-sm text-slate-200 whitespace-pre-wrap max-h-96 overflow-y-auto">
                            {nodeResult.output.output}
                          </div>
                          {/* Metadata */}
                          {(nodeResult.output.agents || nodeResult.output.tasks || nodeResult.output.tokens_used) && (
                            <div className="mt-3 pt-3 border-t border-white/10 space-y-1 text-xs">
                              {nodeResult.output.agents && (
                                <div>
                                  <span className="text-slate-400">Agents: </span>
                                  <span className="text-slate-200">{nodeResult.output.agents.join(', ')}</span>
                                </div>
                              )}
                              {nodeResult.output.tasks && (
                                <div>
                                  <span className="text-slate-400">Tasks: </span>
                                  <span className="text-slate-200">{nodeResult.output.tasks.length} completed</span>
                                </div>
                              )}
                              {nodeResult.output.tokens_used && nodeResult.output.tokens_used.total > 0 && (
                                <div>
                                  <span className="text-slate-400">Tokens: </span>
                                  <span className="text-slate-200">
                                    {nodeResult.output.tokens_used.total.toLocaleString()} 
                                    ({nodeResult.output.tokens_used.input.toLocaleString()} in / {nodeResult.output.tokens_used.output.toLocaleString()} out)
                                  </span>
                                </div>
                              )}
                              {nodeResult.output.provider && nodeResult.output.model && (
                                <div>
                                  <span className="text-slate-400">Model: </span>
                                  <span className="text-slate-200">{nodeResult.output.provider}/{nodeResult.output.model}</span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                      {/* Generic JSON view for other nodes or full data */}
                      <details className="cursor-pointer">
                        <summary className="text-xs font-medium hover:text-slate-200">📋 View Full Data (JSON)</summary>
                        <pre className="mt-2 p-2 bg-white/5 border border-white/10 rounded text-xs overflow-auto max-h-64 text-slate-300">
                          {JSON.stringify(nodeResult.output, null, 2)}
                        </pre>
                      </details>
                    </div>
                  </details>
                </div>
              )}
              {nodeResult?.cost !== undefined && nodeResult.cost > 0 && (
                <div className="mt-1 text-xs text-blue-400">
                  Cost: ${nodeResult.cost.toFixed(4)}
                </div>
              )}
            </div>
          </div>
        );
      })}
      </div>
    </div>
  );
}

