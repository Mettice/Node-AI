/**
 * Execution Summary View - Enhanced with visual hierarchy
 * Features:
 * - Node Result Cards with color-coded borders
 * - Expandable Output Preview
 * - Visual Timeline with animated dots
 * - Cost Breakdown Visualization
 * - Token Usage Display
 */

import { useState, useMemo, useEffect } from 'react';
import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { 
  CheckCircle, XCircle, Clock, DollarSign, Zap, TrendingUp, 
  ChevronDown, ChevronRight, FileText, Copy, Maximize2, Loader2,
  AlertTriangle, Brain, Cpu, MessageSquare, BarChart3, Info, Lightbulb, Database
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { NODE_CATEGORY_COLORS } from '@/constants';
import { toast } from 'react-hot-toast';

// Node tier for shape echo styling
const NODE_TIER_MAP: Record<string, number> = {
  llm: 1, agent: 1, memory: 1, chat: 1, vision: 1, langchain_agent: 1, crewai_agent: 1,
  processing: 2, embedding: 2, tool: 2, training: 2, chunk: 2, embed: 2, rerank: 2, ocr: 2,
  input: 3, retrieval: 3, text_input: 3, file_loader: 3, webhook_input: 3,
  storage: 4, data: 4, vector_store: 4, database: 4, s3: 4, knowledge_graph: 4,
};

export function ExecutionSummary() {
  const { status, cost, duration, results, nodeStatuses } = useExecutionStore();
  const { nodes } = useWorkflowStore();
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const safeResults = results || {};
  const safeNodes = nodes || [];

  // Auto-expand nodes with charts when they become available (only once when execution completes)
  // Also fetch full results from API if execution is complete and we have chart nodes
  useEffect(() => {
    // Only auto-expand when execution just completed, and only if node hasn't been manually toggled
    if (status !== 'completed' && status !== 'failed') return;

    setExpandedNodes(prev => {
      const newExpanded: Record<string, boolean> = { ...prev };
      let hasChanges = false;

      safeNodes.forEach(node => {
        const result = safeResults[node.id];
        if (!result?.output) return;

        // Auto-expand auto_chart_generator nodes that have charts
        // Only if the node hasn't been manually toggled (undefined means not set yet)
        if (node.type === 'auto_chart_generator') {
          // Check multiple possible locations for charts
          const charts = result.output.charts || result.output.visual_charts || 
                        result.output.output?.charts || result.output.output?.visual_charts || [];
          if (Array.isArray(charts) && charts.length > 0 && newExpanded[node.id] === undefined) {
            // Only auto-expand if user hasn't manually toggled it (undefined = not set)
            newExpanded[node.id] = true;
            hasChanges = true;
          }
        }
      });

      return hasChanges ? newExpanded : prev;
    });

    // If execution is complete and we have auto_chart_generator nodes, ensure we have full results
    // The polling in ExecutionControls should handle this, but we can trigger a refresh here too
    const chartNodes = safeNodes.filter(n => n.type === 'auto_chart_generator');
    if (chartNodes.length > 0) {
      const { executionId } = useExecutionStore.getState();
      if (executionId) {
        // Check if any chart node has truncated or missing chart data
        const needsRefresh = chartNodes.some(node => {
          const result = safeResults[node.id];
          if (!result?.output) return false;
          const output = result.output;
          // Check if charts exist but might be truncated (check for _truncated key or empty arrays when metadata says there should be charts)
          const hasTruncated = output._truncated !== undefined;
          const metadata = output.metadata || output.output?.metadata;
          const expectedCharts = metadata?.total_charts || metadata?.visual_charts_generated || 0;
          const actualCharts = (output.charts || output.visual_charts || []).length;
          return hasTruncated || (expectedCharts > 0 && actualCharts === 0);
        });

        if (needsRefresh) {
          // Fetch full results from API
          import('@/services/executions').then(({ getExecutionStatus }) => {
            getExecutionStatus(executionId).then(response => {
              if (response.results) {
                const { updateNodeResult } = useExecutionStore.getState();
                Object.entries(response.results).forEach(([nodeId, result]: [string, any]) => {
                  updateNodeResult(nodeId, {
                    node_id: nodeId,
                    status: result.status,
                    output: result.output, // This should have full charts data
                    error: result.error,
                    cost: result.cost,
                    duration_ms: result.duration_ms,
                  });
                });
              }
            }).catch(err => console.error('[ExecutionSummary] Failed to refresh results:', err));
          });
        }
      }
    }
  }, [safeNodes, safeResults, status]); // Only re-run when status changes, NOT when expandedNodes changes

  const toggleNodeExpanded = (nodeId: string) => {
    setExpandedNodes(prev => {
      const newState = { ...prev, [nodeId]: !prev[nodeId] };
      console.log(`[ExecutionSummary] Toggling node ${nodeId}:`, { 
        wasExpanded: prev[nodeId], 
        nowExpanded: newState[nodeId] 
      });
      return newState;
    });
  };

  const copyToClipboard = async (text: string, nodeId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(nodeId);
      toast.success('Copied to clipboard');
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      toast.error('Failed to copy');
    }
  };

  // Format helpers
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
    return `${(ms / 60000).toFixed(2)}m`;
  };

  const formatCost = (cost: number) => {
    if (cost === 0) return '$0.00';
    if (cost < 0.01) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(2)}`;
  };

  // Build node breakdown with all metadata
  const nodeBreakdown = useMemo(() => {
    return safeNodes.map((node) => {
      const result = safeResults[node.id];
      const nodeType = node.data?.label || node.type || node.id;
      const nodeStatus = result?.status || nodeStatuses[node.id] || 'pending';
      const category = node.data?.category || node.type || 'default';
      const categoryColor = NODE_CATEGORY_COLORS[category as keyof typeof NODE_CATEGORY_COLORS] || '#9ca3af';
      // Map intelligence category nodes to tier 1
      let tier = NODE_TIER_MAP[node.type || ''] || NODE_TIER_MAP[category] || 3;
      if (category === 'intelligence') tier = 1;
      
      // Extract output preview - handle various output formats
      let outputPreview = '';
      if (result?.output) {
        const output = result.output;
        
        // String output
        if (typeof output === 'string') {
          outputPreview = output;
        }
        // Object output - check common fields
        else if (typeof output === 'object' && output !== null) {
          // Check for specific output fields first
          if (output.report) outputPreview = typeof output.report === 'string' ? output.report : JSON.stringify(output.report, null, 2);
          else if (output.output) outputPreview = typeof output.output === 'string' ? output.output : JSON.stringify(output.output, null, 2);
          else if (output.text) outputPreview = typeof output.text === 'string' ? output.text : JSON.stringify(output.text, null, 2);
          else if (output.response) outputPreview = typeof output.response === 'string' ? output.response : JSON.stringify(output.response, null, 2);
          else if (output.message) outputPreview = typeof output.message === 'string' ? output.message : JSON.stringify(output.message, null, 2);
          else if (output.content) outputPreview = typeof output.content === 'string' ? output.content : JSON.stringify(output.content, null, 2);
          // For auto_chart_generator and similar nodes, show charts/data_summary
          else if (output.charts || output.data_summary || output.chart_recommendations || output.metadata) {
            const parts: string[] = [];
            if (output.data_summary) {
              const summary = typeof output.data_summary === 'string' ? output.data_summary : JSON.stringify(output.data_summary, null, 2);
              parts.push(`📊 Data Summary:\n${summary}`);
            }
            if (output.charts && Array.isArray(output.charts)) {
              parts.push(`📈 Charts Generated: ${output.charts.length}`);
              // Show first chart title if available
              if (output.charts.length > 0 && output.charts[0]?.title) {
                parts.push(`   First chart: ${output.charts[0].title}`);
              }
            }
            if (output.chart_recommendations) {
              const recs = typeof output.chart_recommendations === 'string' ? output.chart_recommendations : JSON.stringify(output.chart_recommendations, null, 2);
              parts.push(`💡 Recommendations:\n${recs}`);
            }
            if (output.metadata) {
              const meta = typeof output.metadata === 'string' ? output.metadata : JSON.stringify(output.metadata, null, 2);
              parts.push(`ℹ️ Metadata:\n${meta}`);
            }
            outputPreview = parts.length > 0 ? parts.join('\n\n') : JSON.stringify(output, null, 2);
          }
          // Fallback to JSON stringify
          else {
            outputPreview = JSON.stringify(output, null, 2);
          }
        }
      }

      // Token usage for LLM nodes (access from result output)
      const tokenUsage = (result?.output as Record<string, unknown>)?.usage || null;
      
      return {
        id: node.id,
        name: nodeType,
        type: node.type,
        category,
        categoryColor,
        tier,
        status: nodeStatus,
        duration: result?.duration_ms || 0,
        cost: result?.cost || 0,
        error: result?.error,
        hasOutput: (() => {
          if (!result?.output) return false;
          const output: any = result.output;
          // String output
          if (typeof output === 'string' && output.trim().length > 0) return true;
          // Object output
          if (typeof output === 'object' && output !== null && !Array.isArray(output)) {
            const keys = Object.keys(output);
            if (keys.length > 0) return true;
            // Check nested output fields - including charts and visual_charts
            if (output.output || output.charts || output.visual_charts || output.data_summary || output.summary || output.text || output.content) {
              // For charts, check if array has items
              if (output.charts && Array.isArray(output.charts) && output.charts.length > 0) return true;
              if (output.visual_charts && Array.isArray(output.visual_charts) && output.visual_charts.length > 0) return true;
              return true;
            }
          }
          // Array output
          if (Array.isArray(output) && output.length > 0) return true;
          return false;
        })(),
        outputPreview,
        tokenUsage,
        result, // Include full result object for chart rendering
      };
    });
  }, [safeNodes, safeResults, nodeStatuses]);

  // Calculate statistics
  const totalNodes = safeNodes.length;
  const completedNodes = nodeBreakdown.filter((n) => n.status === 'completed').length;
  const failedNodes = nodeBreakdown.filter((n) => n.status === 'failed').length;
  const successRate = totalNodes > 0 ? Math.round((completedNodes / totalNodes) * 100) : 0;

  // Cost breakdown data for visualization
  const costBreakdown = useMemo(() => {
    const nodesWithCost = nodeBreakdown.filter(n => n.cost > 0);
    const maxCost = Math.max(...nodesWithCost.map(n => n.cost), 0.001);
    return nodesWithCost.map(n => ({
      ...n,
      costPercentage: (n.cost / maxCost) * 100,
      isHighest: n.cost === maxCost && maxCost > 0,
    }));
  }, [nodeBreakdown]);

  // Get nodes with outputs for Results section
  const nodesWithOutputs = nodeBreakdown.filter(node => {
    const hasOutput = node.hasOutput && node.outputPreview;
    // Debug logging for auto_chart_generator and similar nodes
    if (node.type === 'auto_chart_generator' || node.type?.includes('chart') || node.type?.includes('analyzer')) {
      console.log(`[ExecutionSummary] Node ${node.id} (${node.type}):`, {
        hasOutput: node.hasOutput,
        hasOutputPreview: !!node.outputPreview,
        outputPreviewLength: node.outputPreview?.length || 0,
        outputPreviewPreview: node.outputPreview?.substring(0, 100),
        result: safeResults[node.id],
      });
    }
    return hasOutput;
  });

  // Get tier-based CSS class matching nodedesign.html
  const getTierCardClass = (tier: number) => {
    switch (tier) {
      case 1: return 'result-card-tier-1'; // AI - Gradient border
      case 2: return 'result-card-tier-2'; // Processing - Frosted glass
      case 3: return 'result-card-tier-3'; // I/O - Wireframe
      case 4: return 'result-card-tier-4'; // Storage - Stack effect
      default: return 'result-card-tier-3';
    }
  };

  return (
    <div className="space-y-4">
      {/* Results Section - Prominent node outputs */}
      {nodesWithOutputs.length > 0 && (status === 'completed' || status === 'failed') && (
        <div className="space-y-2.5">
          <h3 className="text-xs font-medium text-slate-300 flex items-center gap-2">
            <FileText className="w-3.5 h-3.5" />
            Results
          </h3>
          <div className="space-y-2.5">
            {nodesWithOutputs.map((node) => {
              const isExpanded = expandedNodes[node.id];
              const previewLines = node.outputPreview.split('\n').slice(0, 3).join('\n');
              const hasMore = node.outputPreview.split('\n').length > 3;
              const tierClass = getTierCardClass(node.tier);
              
              // Tier 1 uses wrapper pattern
              if (node.tier === 1) {
                return (
                  <div key={node.id} className={tierClass}>
                    <div className="result-card-tier-1-inner">
                      <ResultCardContent 
                        node={node}
                        result={node.result || safeResults[node.id]}
                        isExpanded={isExpanded}
                        previewLines={previewLines}
                        hasMore={hasMore}
                        copiedId={copiedId}
                        onCopy={copyToClipboard}
                        onToggle={toggleNodeExpanded}
                        formatDuration={formatDuration}
                        formatCost={formatCost}
                      />
                    </div>
                  </div>
                );
              }

              // Other tiers use direct styling
              return (
                <div key={node.id} className={tierClass} style={{ borderLeftColor: node.categoryColor, borderLeftWidth: '4px' }}>
                  <ResultCardContent 
                    node={node}
                    result={safeResults[node.id]}
                    isExpanded={isExpanded}
                    previewLines={previewLines}
                    hasMore={hasMore}
                    copiedId={copiedId}
                    onCopy={copyToClipboard}
                    onToggle={toggleNodeExpanded}
                    formatDuration={formatDuration}
                    formatCost={formatCost}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Visual Timeline */}
      <VisualTimeline nodes={nodeBreakdown} />

      {/* Cost Breakdown Visualization */}
      {costBreakdown.length > 0 && (
        <div className="space-y-2.5">
          <h3 className="text-xs font-medium text-slate-300 flex items-center gap-2">
            <DollarSign className="w-3.5 h-3.5" />
            Cost Breakdown
          </h3>
          {/* Borderless glassmorphism container */}
          <div className="bg-white/[0.01] backdrop-blur-sm rounded-lg p-3 space-y-2.5">
            {/* Total Cost Header */}
            <div className="flex items-center justify-between pb-2">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">Total Cost</span>
              <span className="text-sm font-medium text-amber-500/80">{formatCost(cost)}</span>
            </div>
            
            {/* Cost Bars - Borderless */}
            <div className="space-y-2">
              {costBreakdown.map((node) => (
                <div key={node.id} className="space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <div className="flex items-center gap-1.5">
                      <div 
                        className="w-1.5 h-1.5 rounded-full opacity-70"
                        style={{ backgroundColor: node.categoryColor }}
                      />
                      <span className={cn(
                        "text-slate-400 font-normal",
                        node.isHighest && "text-amber-500/80"
                      )}>
                        {node.name}
                      </span>
                      {node.isHighest && (
                        <span className="text-[8px] bg-amber-500/15 text-amber-500/70 px-1 py-0.5 rounded font-normal">
                          HIGHEST
                        </span>
                      )}
                    </div>
                    <span className="text-amber-500/80 font-mono text-[10px]">{formatCost(node.cost)}</span>
                  </div>
                  <div className="h-1.5 bg-slate-800/50 rounded-full overflow-hidden">
                    <div 
                      className="h-full rounded-full transition-all duration-500"
                      style={{ 
                        width: `${node.costPercentage}%`,
                        background: `linear-gradient(90deg, ${node.categoryColor}, ${node.categoryColor}80)`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Overall Statistics */}
      <div className="space-y-2.5">
        <h3 className="text-xs font-medium text-slate-300 flex items-center gap-2">
          <TrendingUp className="w-3.5 h-3.5" />
          Statistics
        </h3>
        
        <div className="grid grid-cols-2 gap-2">
          <StatCard
            label="Status"
            value={status.charAt(0).toUpperCase() + status.slice(1)}
            icon={status === 'completed' ? CheckCircle : status === 'failed' ? XCircle : Clock}
            color={
              status === 'completed' ? 'text-green-500/80' :
              status === 'failed' ? 'text-red-500/80' :
              status === 'running' ? 'text-blue-500/80' : 'text-yellow-500/80'
            }
          />
          <StatCard
            label="Success Rate"
            value={`${successRate}%`}
            subtitle={`${completedNodes}/${totalNodes} nodes`}
            icon={TrendingUp}
            color="text-slate-300"
          />
          <StatCard
            label="Duration"
            value={duration > 0 ? formatDuration(duration) : status === 'completed' || status === 'failed' ? 'N/A' : '...'}
            icon={Zap}
            color="text-purple-500/80"
          />
          {(cost > 0 || status === 'completed' || status === 'failed') && (
            <StatCard
              label="Total Cost"
              value={formatCost(cost)}
              icon={DollarSign}
              color="text-amber-500/80"
            />
          )}
        </div>
      </div>

      {/* Error Summary */}
      {failedNodes > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-medium text-red-500/80 flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5" />
            Errors
          </h3>
          <div className="bg-red-500/5 backdrop-blur-sm rounded-lg p-2.5">
            <div className="text-[11px] text-red-500/70 font-normal">
              {failedNodes} node{failedNodes > 1 ? 's' : ''} failed during execution.
            </div>
            <div className="text-[9px] text-slate-500 mt-1">
              Check the Logs tab for detailed error information.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Visual Timeline Component with animated dots and flowing particles
function VisualTimeline({ nodes }: { nodes: Array<{ id: string; name: string; status: string; categoryColor: string; tier: number; duration: number }> }) {
  const hasActivity = nodes.some(n => n.status === 'running' || n.status === 'completed' || n.status === 'failed');
  const hasRunning = nodes.some(n => n.status === 'running');
  
  if (!hasActivity) return null;

  return (
      <div className="space-y-2.5">
        <h3 className="text-xs font-medium text-slate-300 flex items-center gap-2">
          <MessageSquare className="w-3.5 h-3.5" />
          Execution Flow
        </h3>
      <div className="relative pl-8">
        {/* Vertical Timeline Line with gradient - muted */}
        <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-500/30 via-purple-500/20 to-emerald-500/30 rounded-full" />
        
        {/* Flowing Particles - only show when running - muted */}
        {hasRunning && (
          <div className="absolute left-2.5 top-0 bottom-0 flex flex-col items-center pointer-events-none">
            <div className="timeline-particle w-1 h-1 rounded-full bg-blue-500/60 shadow-[0_0_3px_theme(colors.blue.500/40)]" />
            <div className="timeline-particle w-1 h-1 rounded-full bg-cyan-500/60 shadow-[0_0_3px_theme(colors.cyan.500/40)]" />
            <div className="timeline-particle w-1 h-1 rounded-full bg-purple-500/60 shadow-[0_0_3px_theme(colors.purple.500/40)]" />
          </div>
        )}
        
        {/* Timeline Items */}
        <div className="space-y-1.5">
          {nodes.map((node, index) => {
            const isRunning = node.status === 'running';
            const isCompleted = node.status === 'completed';
            const isFailed = node.status === 'failed';
            const isPending = node.status === 'pending';
            
            return (
              <div key={node.id} className="relative flex items-start gap-3">
                {/* Simple colored dot - muted colors */}
                <div 
                  className={cn(
                    "absolute left-[-10px] w-2.5 h-2.5 rounded-full transition-all duration-300 z-10",
                    isCompleted && "bg-green-500/70 shadow-[0_0_4px_theme(colors.green.500/30)]",
                    isFailed && "bg-red-500/70 shadow-[0_0_4px_theme(colors.red.500/30)]",
                    isRunning && "bg-blue-500/70 timeline-dot-active shadow-[0_0_6px_theme(colors.blue.500/40)]",
                    isPending && "bg-slate-600"
                  )}
                >
                  {isRunning && (
                    <div className="absolute inset-0 rounded-full bg-blue-500/30 animate-ping" />
                  )}
                </div>

                {/* Connection line to next completed node */}
                {isCompleted && index < nodes.length - 1 && nodes[index + 1]?.status !== 'pending' && (
                  <div 
                    className="absolute left-[-8px] top-5 w-0.5 h-[calc(100%+8px)]"
                    style={{ 
                      background: `linear-gradient(to bottom, ${node.categoryColor}80, ${nodes[index + 1]?.categoryColor || node.categoryColor}40)`
                    }}
                  />
                )}

                {/* Node Info - Borderless with glassmorphism */}
                <div 
                  className={cn(
                    "flex-1 rounded-lg px-2.5 py-1.5 transition-all duration-200 backdrop-blur-sm",
                    isRunning && "bg-blue-500/5",
                    isCompleted && "bg-white/[0.01]",
                    isFailed && "bg-red-500/5",
                    isPending && "bg-white/[0.005] opacity-50"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        "text-[11px] font-normal",
                        isCompleted && "text-green-500/80",
                        isFailed && "text-red-500/80",
                        isRunning && "text-blue-500/80",
                        isPending && "text-slate-500"
                      )}>
                        {node.name}
                      </span>
                      {isRunning && (
                        <Loader2 className="w-2.5 h-2.5 text-blue-500/70 animate-spin" />
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {node.duration > 0 && (
                        <span className="text-[9px] text-slate-600 font-mono">
                          {node.duration < 1000 ? `${node.duration}ms` : `${(node.duration / 1000).toFixed(1)}s`}
                        </span>
                      )}
                    </div>
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

// Result Card Content Component - shared between tiers
function ResultCardContent({
  node,
  result,
  isExpanded,
  previewLines,
  hasMore,
  copiedId,
  onCopy,
  onToggle,
  formatDuration,
  formatCost,
}: {
  node: { id: string; name: string; type?: string; tier: number; categoryColor: string; duration: number; cost: number; outputPreview: string; tokenUsage: unknown };
  result?: { output?: any };
  isExpanded: boolean;
  previewLines: string;
  hasMore: boolean;
  copiedId: string | null;
  onCopy: (text: string, id: string) => void;
  onToggle: (id: string) => void;
  formatDuration: (ms: number) => string;
  formatCost: (cost: number) => string;
}) {
  // Get charts for auto_chart_generator nodes - check multiple possible locations
  let charts: any[] = [];
  if (node.type === 'auto_chart_generator' && result?.output) {
    const output = result.output;
    // Check direct properties
    if (Array.isArray(output.charts)) charts = output.charts;
    else if (Array.isArray(output.visual_charts)) charts = output.visual_charts;
    // Check if output is nested (result.output.output.charts)
    else if (output.output && typeof output.output === 'object') {
      if (Array.isArray(output.output.charts)) charts = output.output.charts;
      else if (Array.isArray(output.output.visual_charts)) charts = output.output.visual_charts;
    }
  }

  // Debug logging for chart detection
  if (node.type === 'auto_chart_generator') {
    console.log(`[ResultCardContent] Node ${node.id}:`, {
      hasResult: !!result,
      resultKeys: result ? Object.keys(result) : [],
      hasOutput: !!result?.output,
      outputType: typeof result?.output,
      outputKeys: result?.output ? Object.keys(result.output) : [],
      chartsExists: !!(result?.output?.charts),
      visualChartsExists: !!(result?.output?.visual_charts),
      nestedOutputExists: !!(result?.output?.output),
      nestedChartsExists: !!(result?.output?.output?.charts),
      nestedVisualChartsExists: !!(result?.output?.output?.visual_charts),
      chartsLength: result?.output?.charts?.length || 0,
      visualChartsLength: result?.output?.visual_charts?.length || 0,
      nestedChartsLength: result?.output?.output?.charts?.length || 0,
      finalChartsArrayLength: charts.length,
      firstChart: charts[0] ? { id: charts[0].id, title: charts[0].title, hasImage: !!charts[0].image_base64, imageBase64Length: charts[0].image_base64?.length || 0 } : null,
      fullResult: result,
      fullOutput: result?.output,
    });
  }

  return (
    <>
      {/* Card Header */}
      <div 
        className="px-3 py-2 flex items-center justify-between border-b border-white/5"
        style={{ background: `${node.categoryColor}08` }}
      >
        <div className="flex items-center gap-2.5">
          <div 
            className="w-6 h-6 rounded-lg flex items-center justify-center"
            style={{ 
              background: `${node.categoryColor}15`,
              boxShadow: `0 0 8px ${node.categoryColor}20`
            }}
          >
            {node.tier === 1 ? (
              <Brain className="w-3 h-3" style={{ color: node.categoryColor, opacity: 0.8 }} />
            ) : node.tier === 2 ? (
              <Cpu className="w-3 h-3" style={{ color: node.categoryColor, opacity: 0.8 }} />
            ) : (
              <FileText className="w-3 h-3" style={{ color: node.categoryColor, opacity: 0.8 }} />
            )}
          </div>
          <div>
            <span className="text-[11px] font-normal text-slate-300">{node.name}</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="text-[9px] text-slate-500">{formatDuration(node.duration)}</span>
              {node.cost > 0 && (
                <span className="text-[9px] text-amber-500/80 font-normal">{formatCost(node.cost)}</span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => onCopy(node.outputPreview, node.id)}
            className="p-1 rounded-md hover:bg-white/5 transition-colors text-slate-500 hover:text-slate-400"
            title="Copy output"
          >
            {copiedId === node.id ? (
              <CheckCircle className="w-3 h-3 text-green-500/70" />
            ) : (
              <Copy className="w-3 h-3" />
            )}
          </button>
          {(hasMore || charts.length > 1 || (node.type === 'auto_chart_generator' && result?.output)) && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggle(node.id);
              }}
              className="p-1 rounded-md hover:bg-white/5 transition-colors text-slate-500 hover:text-slate-400"
              title={isExpanded ? "Collapse" : "Expand"}
            >
              {isExpanded ? (
                <ChevronDown className="w-3 h-3" />
              ) : (
                <Maximize2 className="w-3 h-3" />
              )}
            </button>
          )}
        </div>
      </div>
      
      {/* Chart Visualization for auto_chart_generator - Show when expanded or always show first chart */}
      {node.type === 'auto_chart_generator' && Array.isArray(charts) && charts.length > 0 && (
        <div className="p-3 bg-black/10 space-y-4 border-t border-white/5">
          <div className="text-xs font-semibold text-blue-400 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Generated Charts ({charts.length})
          </div>
          
          <div className="grid grid-cols-1 gap-4">
            {(isExpanded ? charts : charts.slice(0, 1)).map((chart: any, idx: number) => {
              // Log each chart for debugging
              if (idx === 0) {
                console.log(`[ResultCardContent] Rendering chart ${idx}:`, {
                  id: chart.id,
                  title: chart.title,
                  type: chart.type,
                  hasImageBase64: !!chart.image_base64,
                  hasChartHtml: !!chart.chart_html,
                  hasPlotlyJson: !!chart.plotly_json,
                  imageBase64Length: chart.image_base64?.length || 0,
                  keys: Object.keys(chart),
                });
              }
              
              return (
                <div key={chart.id || idx} className="bg-white/5 rounded-lg border border-white/10 overflow-hidden">
                  <div className="px-4 py-3 border-b border-white/10 bg-white/5">
                    <h4 className="text-sm font-medium text-slate-200">{chart.title || `Chart ${idx + 1}`}</h4>
                    <p className="text-xs text-slate-400 mt-1">
                      {chart.type} • {chart.data?.x?.length || chart.data?.labels?.length || chart.metadata?.rows || 0} data points
                    </p>
                  </div>
                  
                  <div className="p-4">
                    {chart.image_base64 ? (
                      <img 
                        src={chart.image_base64} 
                        alt={chart.title || `Chart ${idx + 1}`}
                        className="w-full h-auto max-w-full rounded-lg bg-white/5"
                        style={{ maxHeight: '400px', objectFit: 'contain' }}
                        onError={(e) => {
                          console.error(`[ResultCardContent] Failed to load chart image ${idx}:`, e);
                        }}
                        onLoad={() => {
                          console.log(`[ResultCardContent] Successfully loaded chart image ${idx}`);
                        }}
                      />
                    ) : chart.chart_html ? (
                      <div 
                        className="w-full bg-white/5 rounded-lg"
                        dangerouslySetInnerHTML={{ __html: chart.chart_html }}
                      />
                    ) : chart.plotly_json ? (
                      <div className="text-xs text-slate-400 p-4 bg-white/5 rounded border-2 border-dashed border-white/20">
                        Interactive chart available (Plotly JSON)
                      </div>
                    ) : (
                      <div className="text-xs text-slate-400 p-4 bg-white/5 rounded border-2 border-dashed border-white/20">
                        Chart data available but visualization not generated
                        {chart.chart_error && (
                          <div className="mt-2 text-red-400">Error: {chart.chart_error}</div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          {!isExpanded && charts.length > 1 && (
            <button 
              onClick={() => onToggle(node.id)}
              className="mt-2 text-[10px] text-blue-500/70 hover:text-blue-500/90 flex items-center gap-1 font-normal w-full justify-center py-1"
            >
              Show {charts.length - 1} more chart{charts.length - 1 > 1 ? 's' : ''} <ChevronDown className="w-2.5 h-2.5" />
            </button>
          )}
        </div>
      )}
      
      {/* Output Content - Special formatting for auto_chart_generator */}
      {node.type === 'auto_chart_generator' && result?.output ? (
        <FormattedChartGeneratorOutput output={result.output} isExpanded={isExpanded} onToggle={() => onToggle(node.id)} />
      ) : node.outputPreview ? (
        <div className="p-3 bg-black/10">
          <div className={cn(
            "text-[10px] text-slate-400 whitespace-pre-wrap font-mono transition-all duration-200",
            !isExpanded && "line-clamp-3"
          )}>
            {isExpanded ? node.outputPreview : previewLines}
          </div>
          {hasMore && !isExpanded && (
            <button 
              onClick={() => onToggle(node.id)}
              className="mt-1.5 text-[10px] text-blue-500/70 hover:text-blue-500/90 flex items-center gap-1 font-normal"
            >
              Show more <ChevronDown className="w-2.5 h-2.5" />
            </button>
          )}
        </div>
      ) : null}

      {/* Token Usage for LLM nodes */}
      {node.tokenUsage && (
        <TokenUsageDisplay usage={node.tokenUsage as { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number }} categoryColor={node.categoryColor} />
      )}
    </>
  );
}

// Token Usage Display Component
function TokenUsageDisplay({ usage, categoryColor }: { usage: { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number } | null; categoryColor: string }) {
  if (!usage) return null;
  
  const promptTokens = usage.prompt_tokens || 0;
  const completionTokens = usage.completion_tokens || 0;
  const totalTokens = usage.total_tokens || promptTokens + completionTokens;
  
  // Estimate context window usage (assuming 128k context)
  const contextWindow = 128000;
  const usagePercent = Math.min((totalTokens / contextWindow) * 100, 100);
  const isNearLimit = usagePercent > 80;
  
  if (totalTokens === 0) return null;

  return (
    <div className="px-3 py-2 border-t border-white/5 bg-slate-900/30">
      <div className="flex items-center gap-1.5 mb-1.5">
        <Brain className="w-3 h-3 text-purple-500/70" />
        <span className="text-[10px] font-normal text-slate-400">Token Usage</span>
        {isNearLimit && (
          <AlertTriangle className="w-2.5 h-2.5 text-amber-500/70" />
        )}
      </div>
      <div className="grid grid-cols-3 gap-1.5 text-center mb-1.5">
        <div>
          <div className="text-[9px] text-slate-600">Input</div>
          <div className="text-[10px] font-mono text-slate-400">{promptTokens.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-[9px] text-slate-600">Output</div>
          <div className="text-[10px] font-mono text-slate-400">{completionTokens.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-[9px] text-slate-600">Total</div>
          <div className="text-[10px] font-mono text-purple-500/80 font-normal">{totalTokens.toLocaleString()}</div>
        </div>
      </div>
      {/* Context Window Bar */}
      <div className="h-1 bg-slate-800/50 rounded-full overflow-hidden">
        <div 
          className={cn(
            "h-full rounded-full transition-all duration-500",
            isNearLimit ? "bg-amber-500/70" : "bg-purple-500/70"
          )}
          style={{ width: `${usagePercent}%` }}
        />
      </div>
      <div className="flex justify-between text-[9px] text-slate-600 mt-0.5">
        <span>{usagePercent.toFixed(1)}% of context</span>
        <span>{contextWindow.toLocaleString()} max</span>
      </div>
    </div>
  );
}

// Formatted Chart Generator Output Component
function FormattedChartGeneratorOutput({ output, isExpanded, onToggle }: { output: any; isExpanded: boolean; onToggle?: () => void }) {
  const dataSummary = output.data_summary || output.output?.data_summary;
  const recommendations = output.chart_recommendations || output.output?.chart_recommendations || [];
  const metadata = output.metadata || output.output?.metadata;

  // Determine what to show when collapsed
  const showFullSummary = isExpanded;
  const showAllRecommendations = isExpanded;
  const showFullMetadata = isExpanded;

  return (
    <div className="p-3 bg-black/10 space-y-3 border-t border-white/5">
      {/* Data Summary */}
      {dataSummary && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold text-blue-400">
              <Database className="w-3.5 h-3.5" />
              Data Summary
            </div>
            {!showFullSummary && (dataSummary.key_insights || dataSummary.numerical_columns || dataSummary.categorical_columns) && onToggle && (
              <button
                onClick={onToggle}
                className="text-[10px] text-blue-500/70 hover:text-blue-500/90 flex items-center gap-1"
              >
                Show more <ChevronDown className="w-2.5 h-2.5" />
              </button>
            )}
          </div>
          <div className="bg-white/5 rounded-lg p-3 space-y-2 text-[11px]">
            {dataSummary.shape && (
              <div className="flex items-center gap-2">
                <span className="text-slate-500 min-w-[120px]">Shape:</span>
                <span className="text-slate-300 font-mono">[{dataSummary.shape.join(', ')}]</span>
              </div>
            )}
            {dataSummary.columns && Array.isArray(dataSummary.columns) && (
              <div className="flex items-start gap-2">
                <span className="text-slate-500 min-w-[120px]">Columns:</span>
                <div className="flex flex-wrap gap-1">
                  {dataSummary.columns.map((col: string, idx: number) => (
                    <span key={idx} className="px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded text-[10px] font-mono">
                      {col}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {dataSummary.data_overview && (
              <div className="pt-2 border-t border-white/10">
                <p className="text-slate-300 leading-relaxed">{dataSummary.data_overview}</p>
              </div>
            )}
            {dataSummary.key_insights && Array.isArray(dataSummary.key_insights) && dataSummary.key_insights.length > 0 && (
              <div className="pt-2 border-t border-white/10">
                <div className="text-slate-400 mb-1.5 font-medium">Key Insights:</div>
                <ul className="space-y-1">
                  {(showFullSummary ? dataSummary.key_insights : dataSummary.key_insights.slice(0, 2)).map((insight: string, idx: number) => (
                    <li key={idx} className="text-slate-300 flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span>{insight}</span>
                    </li>
                  ))}
                  {!showFullSummary && dataSummary.key_insights.length > 2 && (
                    <li className="text-[10px] text-slate-500 italic">
                      + {dataSummary.key_insights.length - 2} more insights
                    </li>
                  )}
                </ul>
              </div>
            )}
            {dataSummary.data_quality && typeof dataSummary.data_quality === 'string' && (
              <div className="pt-2 border-t border-white/10">
                <div className="text-slate-400 mb-1 font-medium">Data Quality:</div>
                <p className="text-slate-300 text-[10px]">{dataSummary.data_quality}</p>
              </div>
            )}
            {showFullSummary && dataSummary.missing_values && typeof dataSummary.missing_values === 'object' && !Array.isArray(dataSummary.missing_values) && (
              <div className="pt-2 border-t border-white/10">
                <div className="text-slate-400 mb-1 font-medium">Missing Values:</div>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(dataSummary.missing_values).map(([col, count]: [string, any]) => (
                    <span key={col} className="px-2 py-0.5 bg-orange-500/20 text-orange-300 rounded text-[10px] font-mono">
                      {col}: {String(count)}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {showFullSummary && dataSummary.dtypes && typeof dataSummary.dtypes === 'object' && !Array.isArray(dataSummary.dtypes) && (
              <div className="pt-2 border-t border-white/10">
                <div className="text-slate-400 mb-1 font-medium">Data Types:</div>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(dataSummary.dtypes).map(([col, dtype]: [string, any]) => (
                    <span key={col} className="px-2 py-0.5 bg-cyan-500/20 text-cyan-300 rounded text-[10px] font-mono">
                      {col}: {String(dtype)}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {showFullSummary && dataSummary.outliers && typeof dataSummary.outliers === 'object' && !Array.isArray(dataSummary.outliers) && (
              <div className="pt-2 border-t border-white/10">
                <div className="text-slate-400 mb-1 font-medium">Outliers:</div>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(dataSummary.outliers).map(([col, count]: [string, any]) => (
                    <span key={col} className="px-2 py-0.5 bg-red-500/20 text-red-300 rounded text-[10px] font-mono">
                      {col}: {String(count)}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {showFullSummary && dataSummary.numerical_columns && Array.isArray(dataSummary.numerical_columns) && (
              <div className="pt-2 border-t border-white/10">
                <div className="text-slate-400 mb-1 font-medium">Numerical Columns:</div>
                <div className="flex flex-wrap gap-1">
                  {dataSummary.numerical_columns.map((col: string, idx: number) => (
                    <span key={idx} className="px-2 py-0.5 bg-green-500/20 text-green-300 rounded text-[10px] font-mono">
                      {col}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {showFullSummary && dataSummary.categorical_columns && Array.isArray(dataSummary.categorical_columns) && (
              <div className="pt-2 border-t border-white/10">
                <div className="text-slate-400 mb-1 font-medium">Categorical Columns:</div>
                <div className="flex flex-wrap gap-1">
                  {dataSummary.categorical_columns.map((col: string, idx: number) => (
                    <span key={idx} className="px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded text-[10px] font-mono">
                      {col}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {Array.isArray(recommendations) && recommendations.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-amber-400">
            <Lightbulb className="w-3.5 h-3.5" />
            Recommendations ({recommendations.length})
          </div>
          <div className="space-y-2">
            {recommendations.slice(0, showAllRecommendations ? recommendations.length : 3).map((rec: any, idx: number) => (
              <div key={idx} className="bg-white/5 rounded-lg p-2.5 border border-amber-500/20">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      "px-1.5 py-0.5 rounded text-[9px] font-medium",
                      rec.priority === 'high' && "bg-red-500/20 text-red-300",
                      rec.priority === 'medium' && "bg-yellow-500/20 text-yellow-300",
                      rec.priority === 'low' && "bg-blue-500/20 text-blue-300"
                    )}>
                      {rec.priority || 'medium'}
                    </span>
                    <span className="text-[10px] text-slate-400">{rec.type || 'general'}</span>
                  </div>
                </div>
                <p className="text-[11px] text-slate-300 mb-1.5">{rec.message}</p>
                {rec.action && (
                  <p className="text-[10px] text-slate-400 italic">💡 {rec.action}</p>
                )}
              </div>
            ))}
            {!showAllRecommendations && recommendations.length > 3 && (
              <button
                onClick={onToggle}
                className="text-[10px] text-amber-500/70 hover:text-amber-500/90 text-center py-1 w-full flex items-center justify-center gap-1"
              >
                Show {recommendations.length - 3} more recommendations <ChevronDown className="w-2.5 h-2.5" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Metadata */}
      {metadata && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
            <Info className="w-3.5 h-3.5" />
            Metadata
          </div>
          <div className="bg-white/5 rounded-lg p-2.5 text-[10px] space-y-1">
            {metadata.total_charts !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Total Charts:</span>
                <span className="text-slate-300 font-mono">{metadata.total_charts}</span>
              </div>
            )}
            {metadata.visual_charts_generated !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Visual Charts:</span>
                <span className="text-slate-300 font-mono">{metadata.visual_charts_generated}</span>
              </div>
            )}
            {metadata.data_points !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Data Points:</span>
                <span className="text-slate-300 font-mono">{metadata.data_points}</span>
              </div>
            )}
            {metadata.llm_provider && (
              <div className="flex items-center justify-between">
                <span className="text-slate-500">LLM Provider:</span>
                <span className="text-slate-300">{metadata.llm_provider}</span>
              </div>
            )}
            {metadata.chart_types_generated && Array.isArray(metadata.chart_types_generated) && (
              <div className="flex items-start gap-2 pt-1 border-t border-white/10">
                <span className="text-slate-500 min-w-[100px]">Chart Types:</span>
                <div className="flex flex-wrap gap-1">
                  {metadata.chart_types_generated.map((type: string, idx: number) => (
                    <span key={idx} className="px-1.5 py-0.5 bg-slate-700/50 text-slate-300 rounded text-[9px]">
                      {type}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Stat Card Component - Borderless glassmorphism
function StatCard({ 
  label, 
  value, 
  subtitle, 
  icon: Icon, 
  color 
}: { 
  label: string; 
  value: string; 
  subtitle?: string; 
  icon: React.ComponentType<{ className?: string }>; 
  color: string;
}) {
  return (
    <div className="bg-white/[0.01] backdrop-blur-sm rounded-lg p-2.5">
      <div className="text-[10px] text-slate-500 mb-1 flex items-center gap-1">
        <Icon className="w-2.5 h-2.5" />
        {label}
      </div>
      <div className={cn('text-xs font-normal flex items-center gap-1.5', color)}>
        {value}
      </div>
      {subtitle && (
        <div className="text-[9px] text-slate-600 mt-0.5">{subtitle}</div>
      )}
    </div>
  );
}
