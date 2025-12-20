/**
 * Execution logs component - Streamlined view
 */

import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { Loader2, ChevronRight, ChevronDown } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { ExecutionStep } from '@/types/api';
import { useState } from 'react';

const statusColors = {
  pending: 'text-slate-500',
  running: 'text-blue-500',
  completed: 'text-green-500',
  failed: 'text-red-500',
  error: 'text-red-500',
};

export function ExecutionLogs() {
  const { trace, status, results } = useExecutionStore();
  const { nodes } = useWorkflowStore();
  const [expandedLogs, setExpandedNodes] = useState<Record<string, boolean>>({});

  const toggleLogExpanded = (id: string) => {
    setExpandedNodes(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const formatTime = (timestamp?: string) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  if (status === 'idle' || trace.length === 0) {
    return (
      <div className="p-4 text-center text-slate-400 text-sm">
        <p>No execution logs yet</p>
        <p className="text-xs mt-1 opacity-70">Run a workflow to see execution logs</p>
      </div>
    );
  }

  // Reverse trace to show newest first
  const reversedTrace = [...trace].reverse();

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between px-1 mb-1.5">
        <h3 className="text-xs font-medium text-slate-300">Execution Logs</h3>
        <span className="text-[9px] text-slate-600 bg-white/5 px-1.5 py-0.5 rounded">{trace.length} events</span>
      </div>
      
      {/* Borderless container */}
      <div className="execution-logs-container space-y-1">
        {reversedTrace.map((step: ExecutionStep, index: number) => {
          // Extract status
          const stepStatus = (step.data?.status || step.action || 'pending') as keyof typeof statusColors;
          const statusColor = statusColors[stepStatus as keyof typeof statusColors] || 'text-slate-400';
          const isRunning = stepStatus === 'running';
          
          // Get node info
          const node = nodes.find(n => n.id === step.node_id);
          const nodeName = node?.data?.label || node?.type || step.node_id;
          const nodeResult = results[step.node_id];
          
          // Unique key
          const uniqueKey = `${step.node_id}-${step.action}-${step.timestamp}-${index}`;
          const isExpanded = expandedLogs[uniqueKey];
          
          // Has meaningful detail to expand?
          const hasError = step.data?.error || nodeResult?.error;
          
          // Check for output - handle nested structures and various formats
          const hasOutput = (() => {
            if (!nodeResult?.output || stepStatus !== 'completed') return false;
            
            const output: any = nodeResult.output;
            
            // String output
            if (typeof output === 'string' && output.trim().length > 0) return true;
            
            // Object output - check if it has keys
            if (typeof output === 'object' && output !== null && !Array.isArray(output)) {
              const keys = Object.keys(output);
              if (keys.length > 0) return true;
              
              // Check nested output fields
              if (output.output && (typeof output.output === 'string' || (typeof output.output === 'object' && Object.keys(output.output).length > 0))) {
                return true;
              }
              
              // Check for common output fields
              if (output.charts || output.data_summary || output.summary || output.text || output.content) {
                return true;
              }
            }
            
            // Array output
            if (Array.isArray(output) && output.length > 0) return true;
            
            return false;
          })();
          
          const canExpand = hasError || hasOutput;

          return (
            <div
              key={uniqueKey}
              className={cn(
                "px-2.5 py-1.5 rounded-lg transition-colors",
                isExpanded && "bg-white/[0.02]"
              )}
            >
              <div 
                className={cn(
                  "flex items-center gap-3 cursor-pointer",
                  !canExpand && "cursor-default"
                )}
                onClick={() => canExpand && toggleLogExpanded(uniqueKey)}
              >
                <div className="flex-shrink-0 w-12 text-[9px] font-mono text-slate-600">
                  {formatTime(step.timestamp)}
                </div>
                
                {/* Color-coded node name - muted colors */}
                <span className={cn(
                  "text-[11px] font-normal truncate flex-1 min-w-0",
                  stepStatus === 'completed' && "text-green-500/80",
                  (stepStatus === 'failed' || stepStatus === 'error') && "text-red-500/80",
                  stepStatus === 'running' && "text-blue-500/80",
                  stepStatus === 'pending' && "text-slate-500"
                )} title={nodeName}>
                  {nodeName}
                </span>
                
                {/* Status text - only show if not completed/failed (color already indicates) */}
                {stepStatus !== 'completed' && stepStatus !== 'failed' && stepStatus !== 'error' && (
                  <span className={cn("text-[9px] font-normal", statusColor)}>
                    {stepStatus.toUpperCase()}
                  </span>
                )}
                
                {/* Duration for completed nodes */}
                {stepStatus === 'completed' && nodeResult?.duration_ms && (
                  <span className="text-[9px] text-slate-600 font-mono">
                    {formatDuration(nodeResult.duration_ms)}
                  </span>
                )}
                
                {/* Running spinner */}
                {isRunning && (
                  <Loader2 className="w-2.5 h-2.5 text-blue-500/70 animate-spin flex-shrink-0" />
                )}

                {canExpand && (
                  <div className="text-slate-500 flex-shrink-0">
                    {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                  </div>
                )}
              </div>

              {/* Expanded Details - Borderless */}
              {isExpanded && (
                <div className="mt-2 pt-2">
                  {hasError && (
                    <div className="text-red-500/70 bg-red-500/5 backdrop-blur-sm p-2.5 rounded-lg font-mono break-all text-[10px]">
                      {step.data?.error || nodeResult?.error}
                    </div>
                  )}
                  {hasOutput && (
                    <div className="mt-2 space-y-1">
                      <div className="text-[9px] text-slate-500 uppercase tracking-wider font-normal">Output</div>
                      <pre className="p-2.5 bg-black/20 backdrop-blur-sm rounded-lg text-slate-400 font-mono overflow-auto max-h-96 text-[9px] leading-relaxed">
                        {(() => {
                          const output: any = nodeResult.output;
                          // Handle string outputs
                          if (typeof output === 'string') {
                            return output;
                          }
                          // Handle object/array outputs
                          try {
                            return JSON.stringify(output, null, 2);
                          } catch (e) {
                            return String(output);
                          }
                        })()}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
