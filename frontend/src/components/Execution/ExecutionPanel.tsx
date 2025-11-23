/**
 * Execution Panel - Slides up from bottom during workflow execution
 * Shows real-time progress, timeline, logs, and stats
 */

import { useEffect, useRef, useState } from 'react';
import { ChevronDown, Copy, CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react';
import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { cn } from '@/utils/cn';
import { toast } from 'react-hot-toast';
import type { ExecutionStep } from '@/types/api';

interface ExecutionPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

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
};

// Node type abbreviations for timeline
const nodeTypeAbbr: Record<string, string> = {
  text_input: 'T',
  file_loader: 'F',
  chunk: 'C',
  embed: 'E',
  vector_store: 'S',
  vector_search: 'V',
  chat: 'L',
};

export function ExecutionPanel({ isOpen, onClose }: ExecutionPanelProps) {
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const [copied, setCopied] = useState(false);

  const { status, trace, cost, duration, results } = useExecutionStore();
  const { nodes } = useWorkflowStore();

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (isOpen && !isMinimized) {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [trace, isOpen, isMinimized]);

  // Calculate progress
  const calculateProgress = () => {
    if (status === 'idle') return 0;
    if (status === 'completed') return 100;
    if (status === 'failed') return 100;

    const safeTrace = trace || [];
    const safeNodes = nodes || [];
    const completedNodes = safeTrace.filter(
      (step) => step.action === 'completed' || step.data?.status === 'completed'
    ).length;
    const totalNodes = safeNodes.length;
    
    if (totalNodes === 0) return 0;
    return Math.round((completedNodes / totalNodes) * 100);
  };

  const progress = calculateProgress();

  // Get current executing node
  const getCurrentNode = () => {
    const safeTrace = trace || [];
    const safeNodes = nodes || [];
    const runningStep = safeTrace.find(
      (step) => step.action === 'started' || step.data?.status === 'running'
    );
    if (runningStep) {
      const node = safeNodes.find((n) => n.id === runningStep.node_id);
      return node?.type || runningStep.node_id;
    }
    return null;
  };

  const currentNode = getCurrentNode();
  const safeTrace = trace || [];
  const completedCount = safeTrace.filter(
    (step) => step.action === 'completed' || step.data?.status === 'completed'
  ).length;

  // Helper functions (defined before use)
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatCost = (cost: number) => {
    if (cost === 0) return '$0.00';
    if (cost < 0.01) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(2)}`;
  };

  // Build timeline data
  const buildTimeline = () => {
    const safeNodes = nodes || [];
    const safeTrace = trace || [];
    const timelineNodes = safeNodes.map((node) => {
      const nodeSteps = safeTrace.filter((step) => step.node_id === node.id);
      const latestStep = nodeSteps[nodeSteps.length - 1];
      
      let nodeStatus: 'pending' | 'running' | 'completed' | 'failed' = 'pending';
      if (latestStep) {
        if (latestStep.action === 'completed' || latestStep.data?.status === 'completed') {
          nodeStatus = 'completed';
        } else if (latestStep.action === 'error' || latestStep.data?.status === 'failed') {
          nodeStatus = 'failed';
        } else if (latestStep.action === 'started' || latestStep.data?.status === 'running') {
          nodeStatus = 'running';
        }
      }

      return {
        id: node.id,
        type: node.type || 'default',
        status: nodeStatus,
        abbreviation: nodeTypeAbbr[node.type || ''] || '?',
      };
    });

    return timelineNodes;
  };

  const timelineNodes = buildTimeline();

  // Format logs for display
  const formatLogs = () => {
    const safeNodes = nodes || [];
    const safeTrace = trace || [];
    const safeResults = results || {};
    return safeTrace.map((step: ExecutionStep) => {
      const node = safeNodes.find((n) => n.id === step.node_id);
      const nodeResult = safeResults[step.node_id];
      const nodeType = node?.type || step.node_id;
      
      const stepStatus = step.data?.status || step.action || 'pending';
      const StatusIcon = statusIcons[stepStatus as keyof typeof statusIcons] || Clock;
      const statusColor = statusColors[stepStatus as keyof typeof statusColors] || 'text-slate-400';
      const isRunning = stepStatus === 'running';

      let message = '';
      let details = '';

      if (stepStatus === 'completed') {
        message = `${nodeType} completed`;
        if (nodeResult?.duration_ms) {
          details = `(${formatDuration(nodeResult.duration_ms)})`;
        }
        if (nodeResult?.output) {
          // Add output summary
          const outputKeys = Object.keys(nodeResult.output);
          if (outputKeys.length > 0) {
            const firstKey = outputKeys[0];
            const firstValue = nodeResult.output[firstKey];
            if (Array.isArray(firstValue)) {
              details += ` → ${firstValue.length} ${firstKey} created`;
            } else if (typeof firstValue === 'string' && firstValue.length > 0) {
              details += ` → ${firstValue.length} chars`;
            }
          }
        }
        if (nodeResult?.cost && nodeResult.cost > 0) {
          details += `, $${nodeResult.cost.toFixed(4)}`;
        }
      } else if (stepStatus === 'failed' || stepStatus === 'error') {
        message = `${nodeType} failed`;
        if (step.data?.error || nodeResult?.error) {
          details = `: ${step.data?.error || nodeResult?.error}`;
        }
      } else if (stepStatus === 'running') {
        message = `${nodeType} running...`;
      } else {
        message = `${nodeType} pending`;
      }

      return {
        step,
        message,
        details,
        StatusIcon,
        statusColor,
        isRunning,
      };
    });
  };

  const logs = formatLogs();

  // Copy logs to clipboard
  const handleCopyLogs = async () => {
    const logsText = logs
      .map((log) => `${log.message} ${log.details}`)
      .join('\n');
    
    try {
      await navigator.clipboard.writeText(logsText);
      setCopied(true);
      toast.success('Logs copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy logs');
    }
  };

  // Don't render if not executing
  if (!isOpen || status === 'idle') {
    return null;
  }

  return (
    <div
      className={cn(
        'fixed bottom-0 left-0 right-0 z-50 transition-all duration-300 ease-out',
        isMinimized ? 'translate-y-[calc(100%-60px)]' : 'translate-y-0'
      )}
    >
      <div className="glass-strong border-t border-white/20 shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Loader2
                className={cn(
                  'w-5 h-5',
                  status === 'running' || status === 'pending'
                    ? 'text-blue-400 animate-spin'
                    : status === 'completed'
                    ? 'text-green-400'
                    : 'text-red-400'
                )}
              />
              <h2 className="text-lg font-semibold text-white">
                {status === 'running' || status === 'pending'
                  ? 'Executing Workflow'
                  : status === 'completed'
                  ? 'Execution Completed'
                  : 'Execution Failed'}
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyLogs}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors text-slate-400 hover:text-white"
              title="Copy logs"
            >
              {copied ? (
                <CheckCircle2 className="w-4 h-4 text-green-400" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors text-slate-400 hover:text-white"
              title={isMinimized ? 'Expand' : 'Minimize'}
            >
              <ChevronDown
                className={cn(
                  'w-4 h-4 transition-transform',
                  isMinimized && 'rotate-180'
                )}
              />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors text-slate-400 hover:text-white"
              title="Close"
            >
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        {!isMinimized && (
          <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-300 font-medium">
                  Progress: {progress}%
                </span>
                <span className="text-slate-400">
                  {currentNode ? `Node ${completedCount + 1}/${nodes.length}` : `${completedCount}/${nodes.length} nodes completed`}
                </span>
              </div>
              <div className="w-full h-3 bg-white/5 rounded-full overflow-hidden border border-white/10">
                <div
                  className={cn(
                    'h-full transition-all duration-300 ease-out',
                    status === 'completed'
                      ? 'bg-gradient-to-r from-green-500 to-green-400'
                      : status === 'failed'
                      ? 'bg-gradient-to-r from-red-500 to-red-400'
                      : 'bg-gradient-to-r from-blue-500 to-blue-400'
                  )}
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Timeline */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-300">Timeline</h3>
              <div className="relative">
                {/* Timeline line */}
                <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-white/10 -translate-y-1/2" />
                
                {/* Timeline nodes */}
                <div className="relative flex items-center justify-between px-2">
                  {timelineNodes.map((node) => {
                    const StatusIcon = statusIcons[node.status];
                    const isActive = node.status === 'running';
                    
                    return (
                      <div
                        key={node.id}
                        className="relative flex flex-col items-center gap-1"
                        style={{ flex: 1 }}
                      >
                        <div
                          className={cn(
                            'w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all',
                            node.status === 'completed'
                              ? 'bg-green-500/20 border-green-500 text-green-400'
                              : node.status === 'failed'
                              ? 'bg-red-500/20 border-red-500 text-red-400'
                              : node.status === 'running'
                              ? 'bg-blue-500/20 border-blue-500 text-blue-400 animate-pulse'
                              : 'bg-slate-500/20 border-slate-500 text-slate-400'
                          )}
                        >
                          {isActive ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <StatusIcon className="w-4 h-4" />
                          )}
                        </div>
                        <span className="text-xs text-slate-400 font-mono">
                          {node.abbreviation}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Logs */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-300">Logs</h3>
                <span className="text-xs text-slate-400">{logs.length} entries</span>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-lg p-4 max-h-64 overflow-y-auto space-y-2">
                {logs.length === 0 ? (
                  <div className="text-center py-4 text-slate-400 text-sm">
                    No logs yet
                  </div>
                ) : (
                  <>
                    {logs.map((log, index) => (
                      <div
                        key={`${log.step.node_id}-${log.step.timestamp}-${index}`}
                        className="flex items-start gap-2 text-sm"
                      >
                        <log.StatusIcon
                          className={cn(
                            'w-4 h-4 mt-0.5 flex-shrink-0',
                            log.statusColor,
                            log.isRunning && 'animate-spin'
                          )}
                        />
                        <div className="flex-1 min-w-0">
                          <span className="text-slate-200">{log.message}</span>
                          {log.details && (
                            <span className="text-slate-400 ml-1">{log.details}</span>
                          )}
                        </div>
                      </div>
                    ))}
                    <div ref={logsEndRef} />
                  </>
                )}
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/10">
              <div className="text-center">
                <div className="text-xs text-slate-400 mb-1">Cost</div>
                <div className="text-lg font-bold text-blue-400">
                  {formatCost(cost)}
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs text-slate-400 mb-1">Duration</div>
                <div className="text-lg font-bold text-purple-400">
                  {duration > 0 ? formatDuration(duration) : '-'}
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs text-slate-400 mb-1">Status</div>
                <div
                  className={cn(
                    'text-lg font-bold',
                    status === 'completed'
                      ? 'text-green-400'
                      : status === 'failed'
                      ? 'text-red-400'
                      : 'text-blue-400'
                  )}
                >
                  {status.toUpperCase()}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
