/**
 * Execution Summary View - Clean overview of execution results
 */

import { useState } from 'react';
import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { CheckCircle2, XCircle, Clock, DollarSign, Zap, TrendingUp, GitBranch, ChevronDown, ChevronRight, FileText } from 'lucide-react';
import { cn } from '@/utils/cn';
import { ExecutionTimeline } from './ExecutionTimeline';

export function ExecutionSummary() {
  const { status, cost, duration, results } = useExecutionStore();
  const { nodes } = useWorkflowStore();
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});

  // Ensure results is always an object
  const safeResults = results || {};

  const toggleNodeExpanded = (nodeId: string) => {
    setExpandedNodes(prev => ({ ...prev, [nodeId]: !prev[nodeId] }));
  };

  // Calculate statistics
  const totalNodes = nodes.length;
  const resultsArray = Object.values(safeResults);
  const completedNodes = resultsArray.filter((r) => r.status === 'completed').length;
  const failedNodes = resultsArray.filter((r) => r.status === 'failed').length;
  const successRate = totalNodes > 0 ? Math.round((completedNodes / totalNodes) * 100) : 0;

  // Format duration
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
    return `${(ms / 60000).toFixed(2)}m`;
  };

  // Format cost
  const formatCost = (cost: number) => {
    if (cost < 0.01) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(2)}`;
  };

  // Get node breakdown
  const nodeBreakdown = nodes.map((node) => {
    const result = safeResults[node.id];
    const nodeType = node.data?.label || node.type || node.id;
    
    // Extract output preview
    let outputPreview = '';
    if (result?.output) {
      // For CrewAI/agent nodes, look for report or output field
      if (result.output.report) {
        outputPreview = result.output.report;
      } else if (result.output.output && typeof result.output.output === 'string') {
        outputPreview = result.output.output;
      } else if (typeof result.output === 'string') {
        outputPreview = result.output;
      } else if (result.output.text) {
        outputPreview = result.output.text;
      }
    }
    
    return {
      id: node.id,
      name: nodeType,
      type: node.type,
      status: result?.status || 'pending',
      duration: result?.duration_ms || 0,
      cost: result?.cost || 0,
      error: result?.error,
      hasOutput: result?.output && Object.keys(result.output).length > 0,
      outputPreview: outputPreview,
    };
  });

  // Get nodes with outputs for Results section
  const nodesWithOutputs = nodeBreakdown.filter(node => node.hasOutput && node.outputPreview);

  return (
    <div className="p-4 space-y-6">
      {/* Results Section - Show outputs prominently */}
      {nodesWithOutputs.length > 0 && (status === 'completed' || status === 'failed') && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Results
          </h3>
          <div className="space-y-3">
            {nodesWithOutputs.map((node) => (
              <div key={node.id} className="glass rounded-lg border border-blue-500/30 bg-blue-500/5">
                <div className="p-3 border-b border-blue-500/20">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    <span className="text-sm font-medium text-slate-200">{node.name}</span>
                    {node.cost > 0 && (
                      <span className="ml-auto text-xs text-green-400">{formatCost(node.cost)}</span>
                    )}
                  </div>
                </div>
                <div className="p-4">
                  <div className="text-xs text-slate-300 whitespace-pre-wrap max-h-96 overflow-y-auto">
                    {node.outputPreview}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Overall Statistics */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <TrendingUp className="w-4 h-4" />
          Overall Statistics
        </h3>
        
        <div className="grid grid-cols-2 gap-3">
          {/* Status */}
          <div className="glass rounded-lg p-3 border border-white/10">
            <div className="text-xs text-slate-400 mb-1">Status</div>
            <div className={cn(
              'text-sm font-semibold flex items-center gap-1.5',
              status === 'completed' && 'text-green-400',
              status === 'failed' && 'text-red-400',
              status === 'running' && 'text-blue-400',
              status === 'pending' && 'text-yellow-400'
            )}>
              {status === 'completed' && <CheckCircle2 className="w-4 h-4" />}
              {status === 'failed' && <XCircle className="w-4 h-4" />}
              {(status === 'running' || status === 'pending') && <Clock className="w-4 h-4" />}
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </div>
          </div>

          {/* Success Rate */}
          <div className="glass rounded-lg p-3 border border-white/10">
            <div className="text-xs text-slate-400 mb-1">Success Rate</div>
            <div className="text-sm font-semibold text-slate-200">
              {successRate}%
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {completedNodes}/{totalNodes} nodes
            </div>
          </div>

          {/* Duration */}
          <div className="glass rounded-lg p-3 border border-white/10">
            <div className="text-xs text-slate-400 mb-1 flex items-center gap-1">
              <Zap className="w-3 h-3" />
              Duration
            </div>
            <div className="text-sm font-semibold text-slate-200">
              {duration > 0 ? formatDuration(duration) : status === 'completed' || status === 'failed' ? 'N/A' : '...'}
            </div>
          </div>

          {/* Cost */}
          {cost > 0 && (
            <div className="glass rounded-lg p-3 border border-white/10">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1">
                <DollarSign className="w-3 h-3" />
                Total Cost
              </div>
              <div className="text-sm font-semibold text-green-400">
                {formatCost(cost)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Node Breakdown */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-slate-200">Node Breakdown</h3>
        
        <div className="space-y-2">
          {nodeBreakdown.map((node) => {
            const statusConfig = {
              completed: { icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/30' },
              failed: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' },
              running: { icon: Clock, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30' },
              pending: { icon: Clock, color: 'text-slate-400', bg: 'bg-slate-500/10', border: 'border-slate-500/30' },
            };

            const config = statusConfig[node.status as keyof typeof statusConfig] || statusConfig.pending;
            const StatusIcon = config.icon;

            const isExpanded = expandedNodes[node.id];
            const hasPreview = node.outputPreview && node.outputPreview.length > 0;

            return (
              <div
                key={node.id}
                className={cn(
                  'glass rounded-lg border',
                  config.border,
                  config.bg
                )}
              >
                <div className="p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2 flex-1 min-w-0">
                      <StatusIcon className={cn('w-4 h-4 mt-0.5 flex-shrink-0', config.color)} />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-slate-200 truncate">
                          {node.name}
                        </div>
                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                          {node.duration > 0 && (
                            <span>{formatDuration(node.duration)}</span>
                          )}
                          {node.cost > 0 && (
                            <span className="text-green-400">{formatCost(node.cost)}</span>
                          )}
                          {hasPreview && (
                            <button
                              onClick={() => toggleNodeExpanded(node.id)}
                              className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors"
                            >
                              <FileText className="w-3 h-3" />
                              {isExpanded ? 'Hide' : 'View'} Output
                              {isExpanded ? (
                                <ChevronDown className="w-3 h-3" />
                              ) : (
                                <ChevronRight className="w-3 h-3" />
                              )}
                            </button>
                          )}
                        </div>
                        {node.error && (
                          <div className="mt-2 text-xs text-red-300 bg-red-900/30 border border-red-500/30 p-2 rounded">
                            {node.error}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className={cn('text-xs font-medium px-2 py-1 rounded', config.color, config.bg)}>
                      {node.status}
                    </div>
                  </div>
                </div>

                {/* Output Preview */}
                {hasPreview && isExpanded && (
                  <div className="px-3 pb-3">
                    <div className="mt-2 p-3 bg-slate-900/50 border border-slate-700/50 rounded text-xs text-slate-300 max-h-96 overflow-y-auto">
                      <div className="whitespace-pre-wrap">{node.outputPreview}</div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Execution Timeline */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <GitBranch className="w-4 h-4" />
          Execution Timeline
        </h3>
        <div className="glass rounded-lg border border-white/10 overflow-hidden">
          <ExecutionTimeline />
        </div>
      </div>

      {/* Error Summary */}
      {failedNodes > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-red-400">Errors</h3>
          <div className="glass rounded-lg p-3 border border-red-500/30 bg-red-500/10">
            <div className="text-sm text-slate-200">
              {failedNodes} node{failedNodes > 1 ? 's' : ''} failed during execution.
            </div>
            <div className="text-xs text-slate-400 mt-1">
              Check the Logs tab for detailed error information.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

