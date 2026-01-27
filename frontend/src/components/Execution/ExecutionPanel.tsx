/**
 * Execution Panel - Slides up from bottom during workflow execution
 * Shows real-time progress, timeline, logs, and stats
 */

import { useEffect, useRef, useState } from 'react';
import { ChevronDown, Copy, CheckCircle, XCircle, Loader2, Clock, Activity, DollarSign, FileText, BarChart3 } from 'lucide-react';
import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { cn } from '@/utils/cn';
import { toast } from 'react-hot-toast';
import type { ExecutionStep } from '@/types/api';
import { CostIntelligence } from './CostIntelligence';

interface ExecutionPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const statusIcons = {
  pending: Clock,
  running: Loader2,
  completed: CheckCircle,
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
  llm: 'L',
  agent: 'A',
};

type TabType = 'summary' | 'logs' | 'metrics' | 'cost';

export function ExecutionPanel({ isOpen, onClose }: ExecutionPanelProps) {
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('summary');

  const { status, trace, cost, duration, results } = useExecutionStore();
  const { nodes } = useWorkflowStore();

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (isOpen && !isMinimized && activeTab === 'logs') {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [trace, isOpen, isMinimized, activeTab]);

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

  // Helper functions
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
        abbreviation: nodeTypeAbbr[node.type || ''] || (node.type ? node.type.charAt(0).toUpperCase() : '?'),
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
    
    // Reverse trace to show newest first
    return [...safeTrace].reverse().map((step: ExecutionStep) => {
      const node = safeNodes.find((n) => n.id === step.node_id);
      const nodeResult = safeResults[step.node_id];
      // Use label or type, fallback to truncated ID
      const nodeLabel = node?.data?.label || node?.type || (step.node_id.length > 12 ? `${step.node_id.substring(0, 8)}...` : step.node_id);
      
      const stepStatus = step.data?.status || step.action || 'pending';
      const StatusIcon = statusIcons[stepStatus as keyof typeof statusIcons] || Clock;
      const statusColor = statusColors[stepStatus as keyof typeof statusColors] || 'text-slate-400';
      const isRunning = stepStatus === 'running';

      let message = nodeLabel;
      let details = '';

      if (stepStatus === 'completed') {
        if (nodeResult?.duration_ms) {
          details = `${formatDuration(nodeResult.duration_ms)}`;
        }
        if (nodeResult?.output) {
          const outputKeys = Object.keys(nodeResult.output);
          if (outputKeys.length > 0) {
            const firstKey = outputKeys[0];
            const firstValue = nodeResult.output[firstKey];
            if (Array.isArray(firstValue)) {
              details += ` • ${firstValue.length} ${firstKey}`;
            } else if (typeof firstValue === 'string' && firstValue.length > 0) {
              details += ` • ${firstValue.length} chars`;
            }
          }
        }
      } else if (stepStatus === 'failed' || stepStatus === 'error') {
        if (step.data?.error || nodeResult?.error) {
          details = `${step.data?.error || nodeResult?.error}`;
        } else {
          details = 'Failed';
        }
      } else if (stepStatus === 'running' || stepStatus === 'started') {
        details = 'Started...';
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
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className={cn(
                "p-2 rounded-full",
                status === 'running' || status === 'pending' ? "bg-blue-500/20" : 
                status === 'completed' ? "bg-green-500/20" : "bg-red-500/20"
              )}>
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
              </div>
              <div>
                <h2 className="text-base font-semibold text-white tracking-tight">Execution Results</h2>
                <p className="text-xs text-slate-400">Live workflow output</p>
              </div>
            </div>
            
            {/* Tabs */}
            {!isMinimized && (
              <div className="hidden md:flex items-center bg-black/20 rounded-lg p-1 ml-4">
                <button
                  onClick={() => setActiveTab('summary')}
                  className={cn(
                    "px-4 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-2",
                    activeTab === 'summary' ? "bg-amber-500/20 text-amber-400 shadow-sm" : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                  )}
                >
                  <Activity className="w-3.5 h-3.5" />
                  Summary
                </button>
                <button
                  onClick={() => setActiveTab('logs')}
                  className={cn(
                    "px-4 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-2",
                    activeTab === 'logs' ? "bg-amber-500/20 text-amber-400 shadow-sm" : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                  )}
                >
                  <FileText className="w-3.5 h-3.5" />
                  Logs
                  <span className="bg-white/10 px-1.5 rounded text-[10px] ml-0.5">{logs.length}</span>
                </button>
                <button
                  onClick={() => setActiveTab('metrics')}
                  className={cn(
                    "px-4 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-2",
                    activeTab === 'metrics' ? "bg-amber-500/20 text-amber-400 shadow-sm" : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                  )}
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  Metrics
                </button>
                <button
                  onClick={() => setActiveTab('cost')}
                  className={cn(
                    "px-4 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-2",
                    activeTab === 'cost' ? "bg-amber-500/20 text-amber-400 shadow-sm" : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                  )}
                >
                  <DollarSign className="w-3.5 h-3.5" />
                  Cost
                </button>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {activeTab === 'logs' && (
              <button
                onClick={handleCopyLogs}
                className="p-2 rounded-lg hover:bg-white/10 transition-colors text-slate-400 hover:text-white"
                title="Copy logs"
              >
                {copied ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            )}
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
          <div className="h-[350px] overflow-y-auto bg-black/20">
            {activeTab === 'summary' && (
              <div className="p-6 space-y-8">
                {/* Progress Section */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-300 font-medium">Workflow Progress</span>
                      <span className="bg-white/10 px-2 py-0.5 rounded text-xs text-slate-400 font-mono">{progress}%</span>
                    </div>
                    <span className="text-xs text-slate-400 font-mono">
                      {currentNode ? `Executing: Node ${completedCount + 1}/${nodes.length}` : `${completedCount}/${nodes.length} nodes completed`}
                    </span>
                  </div>
                  <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden border border-white/10">
                    <div
                      className={cn(
                        'h-full transition-all duration-500 ease-out shadow-[0_0_10px_rgba(0,0,0,0.3)]',
                        status === 'completed'
                          ? 'bg-gradient-to-r from-green-500 to-emerald-400'
                          : status === 'failed'
                          ? 'bg-gradient-to-r from-red-500 to-orange-400'
                          : 'bg-gradient-to-r from-blue-500 to-cyan-400 relative overflow-hidden'
                      )}
                      style={{ width: `${progress}%` }}
                    >
                      {(status === 'running' || status === 'pending') && (
                        <div className="absolute inset-0 bg-white/30 animate-[shimmer_2s_infinite] skew-x-12" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Enhanced Timeline Section with Flowing Dots */}
                <div className="space-y-4">
                  <h3 className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Execution Timeline</h3>
                  <div className="relative pt-4 pb-2 overflow-x-auto">
                    {/* Timeline connector line */}
                    <div className="absolute top-[28px] left-0 right-0 h-[2px] bg-white/5" />
                    
                    {/* Animated flowing dots */}
                    {status === 'running' && (
                      <>
                        <div className="absolute top-[27px] left-0 w-1 h-1 bg-blue-400 rounded-full animate-[timelineFlow_3s_linear_infinite] shadow-[0_0_4px_rgba(59,130,246,0.8)]" />
                        <div className="absolute top-[27px] left-0 w-1 h-1 bg-cyan-400 rounded-full animate-[timelineFlow_3s_linear_infinite_1s] shadow-[0_0_4px_rgba(34,211,238,0.8)]" />
                        <div className="absolute top-[27px] left-0 w-1 h-1 bg-amber-400 rounded-full animate-[timelineFlow_3s_linear_infinite_2s] shadow-[0_0_4px_rgba(167,139,250,0.8)]" />
                      </>
                    )}
                    
                    <div className="flex items-start justify-between min-w-max gap-4 px-2">
                      {timelineNodes.map((node, index) => {
                        const StatusIcon = statusIcons[node.status];
                        const isActive = node.status === 'running';
                        const isCompleted = node.status === 'completed';
                        const currentlyExecuting = timelineNodes.findIndex(n => n.status === 'running');
                        const shouldShowProgress = currentlyExecuting >= 0 && index <= currentlyExecuting;
                        
                        return (
                          <div
                            key={node.id}
                            className="relative flex flex-col items-center gap-2 z-10"
                          >
                            {/* Enhanced node indicator with glow */}
                            <div
                              className={cn(
                                'w-8 h-8 rounded-full flex items-center justify-center border-[2px] transition-all duration-500 relative',
                                node.status === 'completed'
                                  ? 'bg-green-500/15 border-green-500 text-green-400 shadow-[0_0_15px_rgba(34,197,94,0.3)]'
                                  : node.status === 'failed'
                                  ? 'bg-red-500/15 border-red-500 text-red-400 shadow-[0_0_15px_rgba(239,68,68,0.3)]'
                                  : node.status === 'running'
                                  ? 'bg-blue-500/15 border-blue-500 text-blue-400 shadow-[0_0_20px_rgba(59,130,246,0.4)] scale-110'
                                  : shouldShowProgress 
                                    ? 'bg-slate-700/50 border-slate-600 text-slate-400'
                                    : 'bg-slate-800/30 border-slate-700/50 text-slate-500'
                              )}
                            >
                              {/* Pulse ring for active nodes */}
                              {isActive && (
                                <div className="absolute -inset-2 border border-blue-400/30 rounded-full animate-ping" />
                              )}
                              
                              {/* Completed check mark glow */}
                              {isCompleted && (
                                <div className="absolute -inset-1 bg-green-400/20 rounded-full animate-pulse" />
                              )}
                              
                              {isActive ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <StatusIcon className="w-4 h-4" fill={isCompleted || node.status === 'failed' ? "currentColor" : "none"} />
                              )}
                            </div>
                            
                            {/* Enhanced node labels */}
                            <div className="flex flex-col items-center">
                              <span className={cn(
                                "text-[10px] font-bold uppercase tracking-wider transition-colors",
                                isActive ? "text-blue-400" : 
                                isCompleted ? "text-green-400" :
                                node.status === 'failed' ? "text-red-400" :
                                shouldShowProgress ? "text-slate-400" : "text-slate-500"
                              )}>
                                {node.abbreviation}
                              </span>
                              <span className={cn(
                                "text-[9px] font-mono transition-colors",
                                isActive ? "text-blue-300" : 
                                isCompleted ? "text-green-300" :
                                "text-slate-600"
                              )}>
                                {index + 1}
                              </span>
                            </div>
                            
                            {/* Progress connection line to next node */}
                            {index < timelineNodes.length - 1 && shouldShowProgress && (
                              <div 
                                className="absolute top-4 left-8 h-[2px] bg-gradient-to-r from-blue-400/60 to-transparent transition-all duration-1000"
                                style={{ 
                                  width: 'calc(100% + 16px)',
                                  opacity: currentlyExecuting > index ? 1 : 0.3
                                }}
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'logs' && (
              <div className="p-4">
                 <div className="bg-black/20 rounded-lg p-4 min-h-[300px] space-y-0 font-mono text-xs">
                  {logs.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                      <FileText className="w-8 h-8 mx-auto mb-2 opacity-20" />
                      No logs generated yet
                    </div>
                  ) : (
                    <>
                      {logs.map((log, index) => (
                        <div
                          key={`${log.step.node_id}-${log.step.timestamp}-${index}`}
                          className={cn(
                            "flex items-center gap-3 p-2 rounded transition-colors border-b border-white/5 last:border-0",
                            "hover:bg-white/5"
                          )}
                        >
                          <span className="text-slate-500 shrink-0 w-16 text-[10px] font-mono">
                            {new Date(log.step.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                          </span>
                          <div className={cn("p-1 rounded-full bg-white/5", log.statusColor.replace('text-', 'bg-').replace('400', '500/10'))}>
                            <log.StatusIcon
                              className={cn(
                                'w-3.5 h-3.5',
                                log.statusColor,
                                log.isRunning && 'animate-spin'
                              )}
                            />
                          </div>
                          <div className="flex items-center gap-2 min-w-0 flex-1">
                            <span className="text-slate-200 font-medium truncate max-w-[120px]">{log.message}</span>
                            {log.details && (
                              <span className="text-slate-500 text-xs truncate flex-1">{log.details}</span>
                            )}
                          </div>
                        </div>
                      ))}
                      <div ref={logsEndRef} />
                    </>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'metrics' && (
              <div className="p-6">
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="glass-light p-4 rounded-xl border border-white/10 text-center">
                    <div className="text-xs text-slate-400 mb-1 uppercase tracking-wider">Total Cost</div>
                    <div className="text-2xl font-bold text-amber-400 drop-shadow-sm">
                      {formatCost(cost)}
                    </div>
                  </div>
                  <div className="glass-light p-4 rounded-xl border border-white/10 text-center">
                    <div className="text-xs text-slate-400 mb-1 uppercase tracking-wider">Duration</div>
                    <div className="text-2xl font-bold text-amber-400 drop-shadow-sm">
                      {duration > 0 ? formatDuration(duration) : '-'}
                    </div>
                  </div>
                  <div className="glass-light p-4 rounded-xl border border-white/10 text-center">
                    <div className="text-xs text-slate-400 mb-1 uppercase tracking-wider">Status</div>
                    <div
                      className={cn(
                        'text-2xl font-bold drop-shadow-sm',
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
                
                {/* Node Performance Breakdown */}
                <h3 className="text-sm font-semibold text-slate-300 mb-3 pl-1">Performance Breakdown</h3>
                <div className="space-y-2">
                  {timelineNodes.filter(n => n.status === 'completed').map(node => {
                    const result = results[node.id];
                    if (!result) return null;
                    
                    return (
                      <div key={node.id} className="glass-light p-3 rounded-lg border border-white/5 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-[10px] font-bold text-slate-400 border border-white/10">
                            {node.abbreviation}
                          </div>
                          <span className="text-sm text-slate-200">{node.type}</span>
                        </div>
                        <div className="flex items-center gap-4 text-xs font-mono">
                          <span className="text-amber-300">{result.duration_ms ? formatDuration(result.duration_ms) : '-'}</span>
                          <span className="text-amber-400 w-16 text-right">{result.cost ? formatCost(result.cost) : '$0.00'}</span>
                        </div>
                      </div>
                    );
                  })}
                  {timelineNodes.filter(n => n.status === 'completed').length === 0 && (
                    <div className="text-center py-8 text-slate-500 text-sm">
                      No performance data available yet
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'cost' && (
              <div className="p-0">
                 <CostIntelligence />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}