/**
 * Execution Outputs View - Final results from execution
 */

import { useState, useEffect } from 'react';
import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { NODE_CATEGORY_COLORS } from '@/constants';
import { FileText, ChevronDown, ChevronRight, Copy, CheckCircle2, ExternalLink, BarChart3, AlertTriangle, Settings } from 'lucide-react';
import { cn } from '@/utils/cn';
import { UnifiedNodeOutput } from './UnifiedNodeOutput';

// Node tier mapping (same as in CustomNode.tsx)
const NODE_TIER_MAP = {
  // Tier 1 - AI/Intelligence
  llm: 1,
  agent: 1,
  memory: 1,
  
  // Tier 2 - Processing
  processing: 2,
  embedding: 2,
  tool: 2,
  training: 2,
  
  // Tier 3 - Input/Output
  input: 3,
  retrieval: 3,
  
  // Tier 4 - Storage/Infrastructure
  storage: 4,
  data: 4,
} as const;

// Get node tier based on type and category
const getNodeTier = (nodeType: string, category: string) => {
  let tier = NODE_TIER_MAP[category as keyof typeof NODE_TIER_MAP];
  
  if (!tier) {
    // Tier 1: AI/Intelligence nodes
    if (nodeType === 'chat' || nodeType === 'llm' || nodeType === 'vision' || 
        nodeType === 'langchain_agent' || nodeType === 'crewai_agent' || 
        nodeType === 'memory' || nodeType === 'agent') {
      tier = 1;
    }
    // Tier 2: Processing nodes
    else if (nodeType === 'chunk' || nodeType === 'embed' || nodeType === 'rerank' || 
             nodeType === 'ocr' || nodeType === 'transcribe' || nodeType === 'video_frames' ||
             nodeType === 'advanced_nlp' || nodeType === 'tool' || nodeType === 'finetune') {
      tier = 2;
    }
    // Tier 4: Storage nodes
    else if (nodeType === 'vector_store' || nodeType === 'database' || nodeType === 's3' ||
             nodeType === 'knowledge_graph' || nodeType === 'google_drive' || 
             nodeType === 'azure_blob') {
      tier = 4;
    }
    // Tier 3: Input/Output (default)
    else {
      tier = 3;
    }
  }
  
  return tier;
};

// Get shape classes based on tier
const getTierCardClass = (tier: number) => {
  switch (tier) {
    case 1: return 'result-card-tier-1'; // Gradient border like node-double-border
    case 2: return 'result-card-tier-2'; // Frosted glass like node-frosted
    case 3: return 'result-card-tier-3'; // Wireframe like node-wireframe
    case 4: return 'result-card-tier-4'; // Stack effect
    default: return 'result-card-tier-2';
  }
};

export function ExecutionOutputs() {
  const { results } = useExecutionStore();
  const { nodes } = useWorkflowStore();
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [useUnifiedDisplay, setUseUnifiedDisplay] = useState<boolean>(false);
  
  // Auto-expand nodes with outputs (CrewAI and nodes with significant output)
  useEffect(() => {
    const newExpanded = new Set(expandedNodes);
    
    nodes.forEach(node => {
      const result = results[node.id];
      if (!result?.output) return;
      
      // Auto-expand CrewAI nodes with agent outputs
      if (node.type === 'crewai_agent' && result.output?.agent_outputs && Object.keys(result.output.agent_outputs).length > 0) {
        newExpanded.add(node.id);
      }
      
      // Auto-expand nodes with long text outputs (likely important content)
      const outputText = 
        (result.output?.output && typeof result.output.output === 'string' ? result.output.output : null) ||
        (result.output?.summary && typeof result.output.summary === 'string' ? result.output.summary : null) ||
        (result.output?.text && typeof result.output.text === 'string' ? result.output.text : null);
      
      if (outputText && outputText.length > 200) {
        // Auto-expand if output is substantial (more than 200 chars)
        newExpanded.add(node.id);
      }
    });
    
    if (newExpanded.size > expandedNodes.size) {
      setExpandedNodes(newExpanded);
    }
  }, [nodes, results, expandedNodes]);

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  // Helper function to check if output has data
  const hasOutputData = (output: any, nodeType: string): boolean => {
    if (!output) return false;
    
    // String output
    if (typeof output === 'string' && output.trim().length > 0) return true;
    
    // Object output
    if (typeof output === 'object' && !Array.isArray(output)) {
      // Has keys
      if (Object.keys(output).length > 0) return true;
      
      // Check nested fields
      if ('output' in output) {
        const nested = (output as any).output;
        if (typeof nested === 'string' && nested.trim().length > 0) return true;
        if (typeof nested === 'object' && nested !== null && Object.keys(nested).length > 0) return true;
      }
      
      if ('summary' in output) {
        const summary = (output as any).summary;
        if (typeof summary === 'string' && summary.trim().length > 0) return true;
        if (typeof summary === 'object' && summary !== null && Object.keys(summary).length > 0) return true;
      }
      
      // CrewAI agent outputs
      if (nodeType === 'crewai_agent' && 'agent_outputs' in output) {
        const agentOutputs = (output as any).agent_outputs;
        if (agentOutputs && typeof agentOutputs === 'object' && Object.keys(agentOutputs).length > 0) return true;
      }
    }
    
    return false;
  };

  // Get nodes with outputs
  const nodesWithOutputs = nodes
    .map((node) => {
      const result = results[node.id];
      // Check if result exists and has output data
      const hasOutput = result?.output && hasOutputData(result.output, node.type || '');
      
      // Debug logging for all nodes
      if (result) {
        console.log(`[ExecutionOutputs] Node ${node.id} (${node.type}):`, {
          hasResult: !!result,
          hasOutput: !!result.output,
          outputKeys: result.output ? Object.keys(result.output) : [],
          hasAgentOutputs: !!result.output?.agent_outputs,
          agentOutputsKeys: result.output?.agent_outputs ? Object.keys(result.output.agent_outputs) : [],
          status: result.status,
        });
      }
      
      // Debug logging for CrewAI nodes
      if (hasOutput && node.type === 'crewai_agent') {
        console.log(`[ExecutionOutputs] CrewAI node ${node.id}:`, {
          hasAgentOutputs: !!result.output?.agent_outputs,
          agentOutputsKeys: result.output?.agent_outputs ? Object.keys(result.output.agent_outputs) : [],
          agentOutputsCount: result.output?.agent_outputs ? Object.keys(result.output.agent_outputs).length : 0,
          agentOutputsDetails: result.output?.agent_outputs ? Object.entries(result.output.agent_outputs).map(([role, outputs]: [string, any]) => ({
            role,
            taskCount: Array.isArray(outputs) ? outputs.length : 0,
            hasOutput: Array.isArray(outputs) && outputs.length > 0 && outputs[0]?.output ? true : false,
          })) : [],
          agents: result.output?.agents,
          outputKeys: Object.keys(result.output || {}),
        });
      }
      return hasOutput ? { node, result } : null;
    })
    .filter((item): item is { node: typeof nodes[0]; result: NonNullable<typeof results[string]> } => item !== null);

  if (nodesWithOutputs.length === 0) {
    return (
      <div className="p-4 text-center text-slate-400">
        <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>No outputs available</p>
        <p className="text-sm mt-1">Node outputs will appear here after execution</p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-2">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-200">Final Outputs</h3>
        <button
          onClick={() => setUseUnifiedDisplay(!useUnifiedDisplay)}
          className={cn(
            "flex items-center gap-2 px-2 py-1 rounded text-xs transition-colors",
            useUnifiedDisplay 
              ? "bg-blue-500/20 text-blue-300 border border-blue-500/30" 
              : "bg-white/5 text-slate-400 hover:text-slate-300 border border-white/10"
          )}
          title={useUnifiedDisplay ? "Switch to legacy display" : "Use unified display format"}
        >
          <Settings className="w-3 h-3" />
          {useUnifiedDisplay ? "Unified" : "Legacy"}
        </button>
      </div>
      
      {nodesWithOutputs.map(({ node, result }) => {
        const nodeName = node.data?.label || node.type || node.id;
        const isExpanded = expandedNodes.has(node.id);

        const nodeCategory = node.data?.category || node.type || 'default';
        const nodeTier = getNodeTier(node.type || '', nodeCategory);
        const categoryColor = NODE_CATEGORY_COLORS[nodeCategory as keyof typeof NODE_CATEGORY_COLORS] || '#9ca3af';
        const tierCardClass = getTierCardClass(nodeTier);
        
        // Result card with shape echo
        const resultCard = (
          <div className={cn('result-card-container', tierCardClass)}>
            <div className="result-card-inner">
              <button
                onClick={() => toggleNode(node.id)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors result-card-header"
                style={{
                  background: nodeTier === 1 
                    ? `linear-gradient(135deg, ${categoryColor}20 0%, ${categoryColor}08 100%)`
                    : nodeTier === 2
                      ? `linear-gradient(135deg, ${categoryColor}15 0%, ${categoryColor}05 100%)`
                      : 'transparent',
                  borderBottom: nodeTier === 3 
                    ? '1px solid rgba(255, 255, 255, 0.1)'
                    : `1px solid ${categoryColor}20`,
                }}
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  {/* Tier-based icon styling matching nodedesign.html */}
                  <div 
                    className={cn(
                      "p-1.5 rounded-lg transition-all duration-300",
                      nodeTier === 3 && "bg-transparent border"
                    )}
                    style={{ 
                      color: categoryColor,
                      background: nodeTier === 3 
                        ? 'transparent'
                        : `${categoryColor}20`,
                      borderColor: nodeTier === 3 ? `${categoryColor}80` : undefined,
                      boxShadow: `0 0 ${nodeTier === 1 ? '25px' : nodeTier === 2 ? '20px' : '15px'} ${categoryColor}40`,
                    }}
                  >
                    <FileText className={cn(
                      "flex-shrink-0",
                      nodeTier === 1 ? "w-5 h-5" : nodeTier === 2 ? "w-4 h-4" : "w-3.5 h-3.5",
                      nodeTier === 3 && "stroke-[1.5]"
                    )} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      )}
                      <span className={cn(
                        "font-medium text-slate-200 truncate",
                        nodeTier === 1 ? "text-sm" : "text-sm"
                      )}>
                        {nodeName}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400">
                      {node.type} • {Object.keys(result.output || {}).length} output{Object.keys(result.output || {}).length !== 1 ? 's' : ''}
                    </div>
                  </div>
                </div>
                
                {/* Execution stats matching node tier styling */}
                <div className="flex items-center gap-3 text-xs">
                  {result.cost && result.cost > 0 && (
                    <span className="text-amber-400 font-medium">${result.cost.toFixed(4)}</span>
                  )}
                  {result.duration_ms && (
                    <span className="text-purple-300 font-mono">{result.duration_ms < 1000 ? `${result.duration_ms}ms` : `${(result.duration_ms / 1000).toFixed(2)}s`}</span>
                  )}
                </div>
              </button>

              {isExpanded && (
                <div className="px-4 pb-4 border-t border-white/10 pt-3 result-card-content">
                {/* Conditional Display: Unified or Legacy */}
                {useUnifiedDisplay && result.output?._display_metadata ? (
                  <UnifiedNodeOutput
                    nodeId={node.id}
                    nodeType={node.type || ''}
                    nodeName={nodeName}
                    output={result.output}
                    categoryColor={categoryColor}
                  />
                ) : (
                  <div className="space-y-4">
                    {/* Legacy Enhanced Output Preview */}
                    <div className="text-xs text-slate-500 mb-2">
                      Legacy Display Mode
                    </div>
                  {/* Debug: Log agent_outputs for CrewAI nodes */}
                  {node.type === 'crewai_agent' && process.env.NODE_ENV === 'development' && (
                    <div className="text-xs text-slate-500 mb-2">
                      Debug: agent_outputs keys: {result.output?.agent_outputs ? Object.keys(result.output.agent_outputs).join(', ') : 'none'}
                    </div>
                  )}

                  {/* Debug: Log chart data for auto_chart_generator */}
                  {node.type === 'auto_chart_generator' && (
                    <div className="text-xs text-slate-500 mb-2">
                      Debug: charts exists: {result.output?.charts ? 'YES' : 'NO'}, 
                      visual_charts exists: {result.output?.visual_charts ? 'YES' : 'NO'}, 
                      charts length: {result.output?.charts?.length || 0},
                      visual_charts length: {result.output?.visual_charts?.length || 0}
                      <br />
                      Output keys: {result.output ? Object.keys(result.output).join(', ') : 'none'}
                    </div>
                  )}

                  {/* Chart Visualization for auto_chart_generator */}
                  {(() => {
                    if (node.type !== 'auto_chart_generator') return null;
                    // Check both charts and visual_charts arrays
                    const charts = result.output?.charts || result.output?.visual_charts || [];
                    if (!Array.isArray(charts) || charts.length === 0) return null;
                    
                    return (
                      <div className="space-y-4">
                        <div className="text-xs font-semibold text-blue-400 flex items-center gap-2 mb-3">
                          <BarChart3 className="w-4 h-4" />
                          Generated Charts ({charts.length})
                        </div>
                        
                        <div className="grid grid-cols-1 gap-4">
                          {charts.map((chart: any, idx: number) => (
                            <div key={chart.id || idx} className="bg-white/5 rounded-lg border border-white/10 overflow-hidden">
                              <div className="px-4 py-3 border-b border-white/10 bg-white/5">
                                <h4 className="text-sm font-medium text-slate-200">{chart.title || `Chart ${idx + 1}`}</h4>
                                <p className="text-xs text-slate-400 mt-1">
                                  {chart.type} • {chart.data?.x?.length || chart.metadata?.rows || 0} data points
                                </p>
                              </div>
                              
                              <div className="p-4">
                                {chart.image_base64 ? (
                                  <img 
                                    src={chart.image_base64} 
                                    alt={chart.title || `Chart ${idx + 1}`}
                                    className="w-full h-auto max-w-full rounded-lg bg-white/5"
                                    style={{ maxHeight: '400px', objectFit: 'contain' }}
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
                          ))}
                        </div>
                      </div>
                    );
                  })()}
                  {/* Text/Markdown Output - Check multiple output fields */}
                  {(() => {
                    // Get output text from various possible fields
                    const outputText = 
                      (result.output?.output && typeof result.output.output === 'string' ? result.output.output : null) ||
                      (result.output?.summary && typeof result.output.summary === 'string' ? result.output.summary : null) ||
                      (result.output?.text && typeof result.output.text === 'string' ? result.output.text : null) ||
                      (result.output?.content && typeof result.output.content === 'string' ? result.output.content : null) ||
                      (typeof result.output === 'string' ? result.output : null);
                    
                    if (!outputText) return null;
                    
                    // Clean and render markdown
                    const renderMarkdown = (text: string) => {
                      const lines = text.split('\n');
                      return lines.map((line, idx) => {
                        const trimmedLine = line.trim();
                        
                        // Skip empty lines
                        if (!trimmedLine) {
                          return <div key={idx} className="h-2" />;
                        }
                        
                        // Headers - match ###, ##, # at start of line
                        // Handle cases with or without space after #
                        const h3Match = trimmedLine.match(/^###\s*(.+)$/);
                        if (h3Match && h3Match[1].trim()) {
                          return (
                            <h3 key={idx} className="text-blue-200 font-semibold text-sm mt-4 mb-2">
                              {h3Match[1].trim()}
                            </h3>
                          );
                        }
                        
                        const h2Match = trimmedLine.match(/^##\s*(.+)$/);
                        if (h2Match && h2Match[1].trim()) {
                          return (
                            <h2 key={idx} className="text-blue-300 font-semibold text-base mt-4 mb-2">
                              {h2Match[1].trim()}
                            </h2>
                          );
                        }
                        
                        const h1Match = trimmedLine.match(/^#\s*(.+)$/);
                        if (h1Match && h1Match[1].trim()) {
                          return (
                            <h1 key={idx} className="text-blue-400 font-bold text-lg mt-4 mb-3">
                              {h1Match[1].trim()}
                            </h1>
                          );
                        }
                        
                        // Bold text (**text** or __text__)
                        let processedLine = trimmedLine;
                        processedLine = processedLine.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>');
                        processedLine = processedLine.replace(/__(.+?)__/g, '<strong class="font-semibold text-white">$1</strong>');
                        processedLine = processedLine.replace(/\*(.+?)\*/g, '<em class="italic">$1</em>');
                        processedLine = processedLine.replace(/_(.+?)_/g, '<em class="italic">$1</em>');
                        
                        // Lists - check for - or * at start (with optional spaces)
                        if (trimmedLine.match(/^[-*]\s+/)) {
                          return (
                            <div key={idx} className="text-slate-300 ml-4 mb-1 flex items-start">
                              <span className="mr-2">•</span>
                              <span dangerouslySetInnerHTML={{ __html: processedLine.replace(/^[-*]\s+/, '') }} />
                            </div>
                          );
                        }
                        
                        // Numbered lists
                        if (trimmedLine.match(/^\d+\.\s+/)) {
                          return (
                            <div key={idx} className="text-slate-300 ml-4 mb-1 flex items-start">
                              <span className="mr-2">{trimmedLine.match(/^(\d+)\./)?.[1]}.</span>
                              <span dangerouslySetInnerHTML={{ __html: processedLine.replace(/^\d+\.\s+/, '') }} />
                            </div>
                          );
                        }
                        
                        // Regular paragraph
                        return (
                          <p key={idx} className="text-slate-200 mb-2 leading-relaxed">
                            <span dangerouslySetInnerHTML={{ __html: processedLine }} />
                          </p>
                        );
                      });
                    };
                    
                    return (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="text-xs font-semibold text-purple-400 flex items-center gap-2">
                            <FileText className="w-3.5 h-3.5" />
                            {node.type === 'crewai_agent' ? 'CrewAI Report' : 
                             node.type === 'advanced_nlp' ? 'NLP Result' : 'Output'}
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(outputText);
                              }}
                              className="p-1 hover:bg-white/10 rounded text-slate-400 hover:text-white transition-colors"
                              title="Copy output"
                            >
                              <Copy className="w-3.5 h-3.5" />
                            </button>
                            <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
                          </div>
                        </div>
                        
                        {/* Output with proper markdown rendering */}
                        <div className="relative">
                          <div className="p-4 bg-black/40 border-0 rounded-lg text-sm text-slate-200 max-h-96 overflow-y-auto leading-relaxed scrollbar-thin">
                            {/* Check if it looks like code/JSON */}
                            {outputText.includes('```') || (outputText.trim().startsWith('{') && outputText.trim().endsWith('}')) ? (
                              <pre className="font-mono text-xs whitespace-pre-wrap">
                                <code>{outputText}</code>
                              </pre>
                            ) : (
                              <div className="prose prose-sm prose-invert max-w-none">
                                {renderMarkdown(outputText)}
                              </div>
                            )}
                          </div>
                          
                          {/* Gradient fade for long content */}
                          <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-black/40 to-transparent pointer-events-none rounded-b-lg" />
                        </div>
                      </div>
                    );
                  })()}
                  
                  {/* Token Usage Visualization */}
                  {result.output?.tokens_used && result.output.tokens_used.total > 0 && (
                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-emerald-400 flex items-center gap-2">
                        <BarChart3 className="w-3.5 h-3.5" />
                        Token Usage
                      </div>
                      <div className="space-y-2">
                        {/* Token bars */}
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-400">Input tokens</span>
                            <span className="text-slate-200 font-mono">{result.output.tokens_used.input.toLocaleString()}</span>
                          </div>
                          <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-blue-500"
                              style={{ width: `${(result.output.tokens_used.input / result.output.tokens_used.total) * 100}%` }}
                            />
                          </div>
                        </div>
                        
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-400">Output tokens</span>
                            <span className="text-slate-200 font-mono">{result.output.tokens_used.output.toLocaleString()}</span>
                          </div>
                          <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-emerald-500"
                              style={{ width: `${(result.output.tokens_used.output / result.output.tokens_used.total) * 100}%` }}
                            />
                          </div>
                        </div>
                        
                        {/* Context window usage (if available) */}
                        {result.output.context_window_size && (
                          <div className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-slate-400">Context usage</span>
                              <span className="text-slate-200 font-mono">
                                {((result.output.tokens_used.total / result.output.context_window_size) * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                              <div 
                                className={cn(
                                  'h-full transition-all',
                                  result.output.tokens_used.total / result.output.context_window_size > 0.8 
                                    ? 'bg-red-500' 
                                    : result.output.tokens_used.total / result.output.context_window_size > 0.6
                                      ? 'bg-yellow-500'
                                      : 'bg-green-500'
                                )}
                                style={{ width: `${(result.output.tokens_used.total / result.output.context_window_size) * 100}%` }}
                              />
                            </div>
                            {result.output.tokens_used.total / result.output.context_window_size > 0.8 && (
                              <div className="text-xs text-red-400 flex items-center gap-1">
                                <AlertTriangle className="w-3 h-3" />
                                Approaching context limit
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Agent/Task Metadata */}
                  {(result.output?.agents || result.output?.tasks) && (
                    <div className="grid grid-cols-2 gap-3 text-xs mb-3">
                      {result.output.agents && (
                        <div className="p-3 bg-white/5 rounded-lg border-0">
                          <div className="text-slate-400 mb-1">Agents</div>
                          <div className="text-slate-200 font-medium">
                            {result.output.agents.join(', ')}
                          </div>
                        </div>
                      )}
                      {result.output.tasks && (
                        <div className="p-3 bg-white/5 rounded-lg border-0">
                          <div className="text-slate-400 mb-1">Tasks</div>
                          <div className="text-slate-200 font-medium">
                            {result.output.tasks.length} completed
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Individual Agent Outputs - Always show if available */}
                  {(() => {
                    // Debug: Log the structure
                    console.log('[ExecutionOutputs] agent_outputs:', result.output?.agent_outputs);
                    console.log('[ExecutionOutputs] agent_outputs type:', typeof result.output?.agent_outputs);
                    console.log('[ExecutionOutputs] agent_outputs keys:', result.output?.agent_outputs ? Object.keys(result.output.agent_outputs) : []);
                    
                    const agentOutputs = result.output?.agent_outputs;
                    if (!agentOutputs || (typeof agentOutputs === 'object' && Object.keys(agentOutputs).length === 0)) {
                      return null;
                    }
                    
                    // Handle both object and array formats
                    const entries = Array.isArray(agentOutputs) 
                      ? agentOutputs.map((item: any, idx: number) => [item.agent_role || item.role || `Agent ${idx}`, item.outputs || item])
                      : Object.entries(agentOutputs);
                    
                    return (
                      <div className="mt-4 space-y-3 border-t border-white/10 pt-3">
                        <div className="text-xs font-semibold text-slate-200 mb-3 flex items-center gap-2">
                          <BarChart3 className="w-4 h-4 text-cyan-400" />
                          Individual Agent Outputs
                          <span className="text-[10px] text-slate-400 font-normal">
                            ({entries.length} agents)
                          </span>
                        </div>
                        {entries.map((entry: any, idx: number) => {
                          const [agentRole, outputs] = entry as [string, any];
                          // Debug logging
                          console.log(`[ExecutionOutputs] Rendering agent ${idx}: ${agentRole}`, outputs);
                          return (
                          <div key={agentRole} className="p-3 bg-white/5 rounded-lg border border-white/10">
                            <div className="text-xs font-semibold text-cyan-400 mb-2 flex items-center gap-2">
                              <span>🤖</span>
                              <span>{agentRole}</span>
                              {Array.isArray(outputs) && (
                                <span className="text-[10px] text-slate-500 ml-auto">
                                  {outputs.length} task{outputs.length !== 1 ? 's' : ''}
                                </span>
                              )}
                            </div>
                            {Array.isArray(outputs) && outputs.length > 0 ? (
                              outputs.map((output: any, idx: number) => {
                                const outputText = output.output || output.result || output.content || '';
                                return (
                                  <div key={idx} className="mb-3 last:mb-0 p-3 bg-black/20 rounded border border-white/5">
                                    {output.task && (
                                      <div className="text-[10px] text-slate-400 mb-2 font-medium">Task: {output.task}</div>
                                    )}
                                    <div className="text-xs text-slate-200 whitespace-pre-wrap max-h-96 overflow-y-auto mb-2">
                                      {outputText || 'No output text available'}
                                    </div>
                                    {outputText && (
                                      <div className="mt-2 flex items-center gap-2 pt-2 border-t border-white/10">
                                        <button
                                          onClick={() => {
                                            navigator.clipboard.writeText(outputText);
                                          }}
                                          className="text-[10px] text-blue-400 hover:text-blue-300 flex items-center gap-1 px-2 py-1 rounded hover:bg-blue-500/10 transition-colors"
                                          title="Copy to clipboard"
                                        >
                                          <Copy className="w-3 h-3" />
                                          Copy
                                        </button>
                                        <button
                                          onClick={() => {
                                            const blob = new Blob([outputText], { type: 'text/plain' });
                                            const url = URL.createObjectURL(blob);
                                            const a = document.createElement('a');
                                            a.href = url;
                                            const safeTaskName = (output.task || 'output').replace(/[^a-z0-9]/gi, '_').toLowerCase();
                                            a.download = `${agentRole.replace(/[^a-z0-9]/gi, '_')}_${safeTaskName}_${Date.now()}.txt`;
                                            document.body.appendChild(a);
                                            a.click();
                                            document.body.removeChild(a);
                                            URL.revokeObjectURL(url);
                                          }}
                                          className="text-[10px] text-green-400 hover:text-green-300 flex items-center gap-1 px-2 py-1 rounded hover:bg-green-500/10 transition-colors"
                                          title="Download as file"
                                        >
                                          <ExternalLink className="w-3 h-3" />
                                          Download
                                        </button>
                                      </div>
                                    )}
                                  </div>
                                );
                              })
                            ) : (
                              <div className="text-xs text-slate-500 italic p-2">
                                No outputs available for this agent
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                    );
                  })()}

                {/* Debug warning for missing agent outputs */}
                {!result.output?.agent_outputs && result.output?.agents && result.output?.agents.length > 0 && (
                  <div className="mt-3 p-2 bg-yellow-500/10 border border-yellow-500/20 rounded text-xs text-yellow-400">
                    ⚠️ Agent outputs not available (agents: {result.output.agents.join(', ')}). 
                    Check backend logs for extraction details.
                  </div>
                )}

                {/* Generic JSON view */}
                <details className="cursor-pointer">
                  <summary className="text-xs font-medium text-slate-300 hover:text-slate-200 mb-2">
                    📋 View Full Data (JSON)
                  </summary>
                  <pre className="mt-2 p-3 bg-white/5 border border-white/10 rounded text-xs overflow-auto max-h-64 text-slate-300">
                    {JSON.stringify(result.output, null, 2)}
                  </pre>
                </details>
              </div>
                )}
                </div>
              )}
            </div>
          </div>
        );
        
        // Wrap Tier 1 nodes with gradient border like nodedesign.html
        return (
          <div key={node.id}>
            {nodeTier === 1 ? (
              <div className="result-card-tier-1-wrapper">
                {resultCard}
              </div>
            ) : (
              resultCard
            )}
          </div>
        );
      })}
    </div>
  );
}

