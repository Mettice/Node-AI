/**
 * Insights Panel - Expanded Output Display
 *
 * Provides a clean, expanded view of execution results similar to Claude/Perplexity,
 * while maintaining access to traces, costs, and logs.
 */

import { useState, useMemo, useEffect, useRef } from 'react';
import {
  X, ChevronDown, ChevronRight, Copy, Check, Download,
  FileText, BarChart3, Clock, DollarSign, Zap,
  Maximize2, Minimize2, Settings, Eye, List, Search,
  ChevronLeft, ExternalLink, Brain, Cpu, Database
} from 'lucide-react';
import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { useUIStore } from '@/store/uiStore';
import { cn } from '@/utils/cn';
import { NODE_CATEGORY_COLORS } from '@/constants';
import { toast } from 'react-hot-toast';
import { MarkdownRenderer } from './MarkdownRenderer';

// Node tier mapping for styling
const NODE_TIER_MAP: Record<string, number> = {
  llm: 1, agent: 1, memory: 1, chat: 1, vision: 1, langchain_agent: 1, crewai_agent: 1,
  processing: 2, embedding: 2, tool: 2, training: 2, chunk: 2, embed: 2, rerank: 2, ocr: 2,
  input: 3, retrieval: 3, text_input: 3, file_loader: 3, webhook_input: 3,
  storage: 4, data: 4, vector_store: 4, database: 4, s3: 4, knowledge_graph: 4,
};

interface InsightsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function InsightsPanel({ isOpen, onClose }: InsightsPanelProps) {
  const { status, cost, duration, results, trace } = useExecutionStore();
  const { nodes } = useWorkflowStore();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'insights' | 'trace' | 'raw'>('insights');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  // Get nodes with outputs
  const nodesWithOutputs = useMemo(() => {
    return nodes
      .filter(node => {
        const result = results[node.id];
        if (!result?.output) return false;
        const output = result.output as unknown;
        if (typeof output === 'string' && (output as string).trim().length > 0) return true;
        if (typeof output === 'object' && output !== null) {
          if (Object.keys(output as object).length > 0) return true;
        }
        return false;
      })
      .map(node => {
        const result = results[node.id];
        const category = node.data?.category || node.type || 'default';
        const categoryColor = NODE_CATEGORY_COLORS[category as keyof typeof NODE_CATEGORY_COLORS] || '#9ca3af';
        let tier = NODE_TIER_MAP[node.type || ''] || NODE_TIER_MAP[category] || 3;
        if (category === 'intelligence') tier = 1;

        return {
          node,
          result,
          category,
          categoryColor,
          tier,
          name: node.data?.label || node.type || node.id,
        };
      });
  }, [nodes, results]);

  // Auto-select first node with output
  useEffect(() => {
    if (isOpen && nodesWithOutputs.length > 0 && !selectedNodeId) {
      // Prefer AI/Intelligence tier nodes
      const priorityNode = nodesWithOutputs.find(n => n.tier === 1) || nodesWithOutputs[0];
      setSelectedNodeId(priorityNode.node.id);
    }
  }, [isOpen, nodesWithOutputs, selectedNodeId]);

  // Get selected node data
  const selectedNode = useMemo(() => {
    if (!selectedNodeId) return null;
    return nodesWithOutputs.find(n => n.node.id === selectedNodeId);
  }, [selectedNodeId, nodesWithOutputs]);

  // Extract primary text content from output
  const extractTextContent = (output: any): string => {
    if (!output) return '';
    if (typeof output === 'string') return output;

    // CrewAI agent outputs - extract ALL agent outputs with proper formatting
    if (output.agent_outputs && typeof output.agent_outputs === 'object') {
      const parts: string[] = [];
      Object.entries(output.agent_outputs).forEach(([role, outputs]: [string, any]) => {
        if (Array.isArray(outputs)) {
          outputs.forEach((o: any, idx: number) => {
            if (o.output) {
              const taskInfo = o.task ? `\n*Task: ${o.task}*\n` : '';
              parts.push(`## ${role}${taskInfo}\n${o.output}`);
            }
          });
        } else if (typeof outputs === 'object' && outputs.output) {
          parts.push(`## ${role}\n\n${outputs.output}`);
        }
      });
      if (parts.length > 0) {
        // Add a summary header if there's also a final output
        const finalOutput = output.output || output.report || output.result;
        if (finalOutput && typeof finalOutput === 'string') {
          return `# Final Output\n\n${finalOutput}\n\n---\n\n# Agent Contributions\n\n${parts.join('\n\n---\n\n')}`;
        }
        return parts.join('\n\n---\n\n');
      }
    }

    // Check common output fields
    const textFields = ['output', 'text', 'content', 'summary', 'response', 'message', 'report', 'translated'];
    for (const field of textFields) {
      if (output[field] && typeof output[field] === 'string') {
        return output[field];
      }
    }

    // Nested output
    if (output.output && typeof output.output === 'object') {
      return extractTextContent(output.output);
    }

    return '';
  };

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      toast.success('Copied to clipboard');
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      toast.error('Failed to copy');
    }
  };

  const downloadContent = (text: string, filename: string) => {
    const blob = new Blob([text], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('Downloaded');
  };

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

  if (!isOpen) return null;

  const primaryContent = selectedNode ? extractTextContent(selectedNode.result.output) : '';
  const hasCharts = selectedNode?.result?.output?.charts || selectedNode?.result?.output?.visual_charts;

  return (
    <div
      className={cn(
        "fixed inset-0 z-50 flex transition-all duration-300",
        isFullscreen ? "bg-[#0a0a0f]" : "bg-black/60 backdrop-blur-sm"
      )}
      onClick={(e) => {
        if (e.target === e.currentTarget && !isFullscreen) onClose();
      }}
    >
      <div
        className={cn(
          "flex flex-col bg-[#0d0d12] border-l border-white/10 transition-all duration-300 ml-auto",
          isFullscreen ? "w-full" : "w-[70%] max-w-5xl"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-black/40">
          <div className="flex items-center gap-4">
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors text-slate-400 hover:text-white"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>
            <div>
              <h2 className="text-lg font-semibold text-white">Execution Insights</h2>
              <div className="flex items-center gap-4 text-sm text-slate-400 mt-0.5">
                <span className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5" />
                  {formatDuration(duration)}
                </span>
                <span className="flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5" />
                  {formatCost(cost)}
                </span>
                <span className="flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5" />
                  {nodesWithOutputs.length} outputs
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Tab Switcher */}
            <div className="flex items-center bg-white/5 rounded-lg p-1 mr-4">
              {[
                { id: 'insights', label: 'Insights', icon: Eye },
                { id: 'trace', label: 'Trace', icon: Search },
                { id: 'raw', label: 'Raw', icon: FileText },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors",
                    activeTab === tab.id
                      ? "bg-blue-500/20 text-blue-400"
                      : "text-slate-400 hover:text-slate-300"
                  )}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </div>

            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors text-slate-400 hover:text-white"
              title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
            >
              {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex flex-1 min-h-0">
          {/* Node Selector Sidebar */}
          <div className="w-64 border-r border-white/10 bg-black/20 flex flex-col">
            <div className="px-4 py-3 border-b border-white/10">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Results</h3>
            </div>
            <div className="flex-1 overflow-y-auto py-2">
              {nodesWithOutputs.map(({ node, name, categoryColor, tier, result }) => (
                <button
                  key={node.id}
                  onClick={() => setSelectedNodeId(node.id)}
                  className={cn(
                    "w-full px-4 py-3 flex items-start gap-3 transition-colors text-left",
                    selectedNodeId === node.id
                      ? "bg-white/10 border-l-2"
                      : "hover:bg-white/5 border-l-2 border-transparent"
                  )}
                  style={{ borderLeftColor: selectedNodeId === node.id ? categoryColor : 'transparent' }}
                >
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ background: `${categoryColor}20` }}
                  >
                    {tier === 1 ? (
                      <Brain className="w-4 h-4" style={{ color: categoryColor }} />
                    ) : tier === 4 ? (
                      <Database className="w-4 h-4" style={{ color: categoryColor }} />
                    ) : (
                      <Cpu className="w-4 h-4" style={{ color: categoryColor }} />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-slate-200 truncate">{name}</div>
                    <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                      <span>{node.type}</span>
                      {(result.cost ?? 0) > 0 && (
                        <span className="text-amber-500/70">{formatCost(result.cost ?? 0)}</span>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 flex flex-col min-w-0">
            {selectedNode ? (
              <>
                {/* Content Header */}
                <div className="px-6 py-4 border-b border-white/10 bg-black/20 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center"
                      style={{
                        background: `${selectedNode.categoryColor}20`,
                        boxShadow: `0 0 20px ${selectedNode.categoryColor}30`
                      }}
                    >
                      {selectedNode.tier === 1 ? (
                        <Brain className="w-5 h-5" style={{ color: selectedNode.categoryColor }} />
                      ) : (
                        <FileText className="w-5 h-5" style={{ color: selectedNode.categoryColor }} />
                      )}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">{selectedNode.name}</h3>
                      <div className="flex items-center gap-3 text-xs text-slate-500 mt-0.5">
                        <span>{selectedNode.node.type}</span>
                        {selectedNode.result.duration_ms && (
                          <span className="text-amber-400">{formatDuration(selectedNode.result.duration_ms)}</span>
                        )}
                        {(selectedNode.result.cost ?? 0) > 0 && (
                          <span className="text-amber-400">{formatCost(selectedNode.result.cost ?? 0)}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => copyToClipboard(primaryContent, 'content')}
                      className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-slate-400 hover:text-white transition-colors"
                    >
                      {copiedId === 'content' ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                      Copy
                    </button>
                    <button
                      onClick={() => downloadContent(primaryContent, `${selectedNode.name}_output.md`)}
                      className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-slate-400 hover:text-white transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </button>
                  </div>
                </div>

                {/* Scrollable Content */}
                <div ref={contentRef} className="flex-1 overflow-y-auto">
                  {activeTab === 'insights' && (
                    <div className="p-6">
                      {/* Charts if available */}
                      {hasCharts && selectedNode.result.output && (
                        <ChartsSection
                          charts={(selectedNode.result.output as any).charts || (selectedNode.result.output as any).visual_charts || []}
                        />
                      )}

                      {/* Main Content - Rendered Markdown */}
                      {primaryContent ? (
                        <div className="prose prose-invert prose-lg max-w-none">
                          <MarkdownRenderer content={primaryContent} />
                        </div>
                      ) : (
                        <div className="text-center text-slate-500 py-12">
                          <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                          <p>No text content available</p>
                          <p className="text-sm mt-1">View raw output for full data</p>
                        </div>
                      )}

                      {/* Token Usage if available */}
                      {selectedNode.result.output?.tokens_used && (
                        <TokenUsageCard usage={selectedNode.result.output.tokens_used} />
                      )}
                    </div>
                  )}

                  {activeTab === 'trace' && (
                    <div className="p-6">
                      <TraceView trace={trace} nodeId={selectedNode.node.id} />
                    </div>
                  )}

                  {activeTab === 'raw' && (
                    <div className="p-6">
                      <pre className="bg-black/40 p-4 rounded-xl border border-white/10 overflow-auto text-sm text-slate-300 font-mono">
                        {JSON.stringify(selectedNode.result.output, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-slate-500">
                <div className="text-center">
                  <FileText className="w-16 h-16 mx-auto mb-4 opacity-30" />
                  <p className="text-lg">Select a result to view</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Charts Section Component
function ChartsSection({ charts }: { charts: any[] }) {
  if (!charts || charts.length === 0) return null;

  return (
    <div className="mb-8">
      <h3 className="text-sm font-semibold text-blue-400 flex items-center gap-2 mb-4">
        <BarChart3 className="w-4 h-4" />
        Generated Charts ({charts.length})
      </h3>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {charts.map((chart: any, idx: number) => (
          <div key={chart.id || idx} className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
            <div className="px-4 py-3 border-b border-white/10">
              <h4 className="text-sm font-medium text-white">{chart.title || `Chart ${idx + 1}`}</h4>
              <p className="text-xs text-slate-500 mt-0.5">
                {chart.type} • {chart.data?.x?.length || 0} data points
              </p>
            </div>
            <div className="p-4">
              {chart.image_base64 ? (
                <img
                  src={chart.image_base64}
                  alt={chart.title}
                  className="w-full h-auto rounded-lg"
                  style={{ maxHeight: '400px', objectFit: 'contain' }}
                />
              ) : (
                <div className="text-sm text-slate-500 text-center py-8">
                  Chart visualization not available
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Token Usage Card
function TokenUsageCard({ usage }: { usage: { input: number; output: number; total: number } }) {
  const contextWindow = 128000;
  const usagePercent = Math.min((usage.total / contextWindow) * 100, 100);

  return (
    <div className="mt-8 p-4 bg-white/5 rounded-xl border border-white/10">
      <h3 className="text-sm font-semibold text-emerald-400 flex items-center gap-2 mb-4">
        <Zap className="w-4 h-4" />
        Token Usage
      </h3>
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="text-xs text-slate-500 mb-1">Input</div>
          <div className="text-lg font-mono text-blue-400">{usage.input.toLocaleString()}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-slate-500 mb-1">Output</div>
          <div className="text-lg font-mono text-emerald-400">{usage.output.toLocaleString()}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-slate-500 mb-1">Total</div>
          <div className="text-lg font-mono text-amber-400">{usage.total.toLocaleString()}</div>
        </div>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-slate-500">
          <span>Context Usage</span>
          <span>{usagePercent.toFixed(1)}%</span>
        </div>
        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all",
              usagePercent > 80 ? "bg-red-500" : usagePercent > 60 ? "bg-yellow-500" : "bg-emerald-500"
            )}
            style={{ width: `${usagePercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// Trace View Component
function TraceView({ trace, nodeId }: { trace: any[]; nodeId: string }) {
  const nodeTraces = trace.filter(t => t.node_id === nodeId);

  if (nodeTraces.length === 0) {
    return (
      <div className="text-center text-slate-500 py-12">
        <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No trace data available for this node</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {nodeTraces.map((t, idx) => (
        <div key={idx} className="p-4 bg-white/5 rounded-xl border border-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-white">{t.event || 'Event'}</span>
            <span className="text-xs text-slate-500">{t.timestamp}</span>
          </div>
          {t.data && (
            <pre className="text-xs text-slate-400 font-mono overflow-auto">
              {JSON.stringify(t.data, null, 2)}
            </pre>
          )}
        </div>
      ))}
    </div>
  );
}

export default InsightsPanel;
