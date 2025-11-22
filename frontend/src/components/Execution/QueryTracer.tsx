/**
 * Query Tracer Component
 * 
 * Visualizes RAG query execution traces, showing:
 * - Query input
 * - Chunking details
 * - Embedding details
 * - Vector search results (chunks, scores)
 * - Reranking results
 * - LLM input/output
 * - Final response
 */

import { useEffect, useState } from 'react';
import { Search, FileText, Layers, Database, ArrowRight, Sparkles, MessageSquare, CheckCircle2, Clock, DollarSign } from 'lucide-react';
import { getTrace, type QueryTrace, type QueryTraceStep } from '@/services/queryTracer';
import { useExecutionStore } from '@/store/executionStore';
import { cn } from '@/utils/cn';

interface QueryTracerProps {
  executionId?: string;
}

const stepTypeIcons = {
  query_input: Search,
  chunking: FileText,
  embedding: Layers,
  vector_search: Database,
  reranking: Sparkles,
  llm: MessageSquare,
  final_output: CheckCircle2,
};

const stepTypeLabels = {
  query_input: 'Query Input',
  chunking: 'Chunking',
  embedding: 'Embedding',
  vector_search: 'Vector Search',
  reranking: 'Reranking',
  llm: 'LLM Response',
  final_output: 'Final Output',
};

const stepTypeColors = {
  query_input: 'text-blue-400 border-blue-400/20 bg-blue-400/10',
  chunking: 'text-purple-400 border-purple-400/20 bg-purple-400/10',
  embedding: 'text-indigo-400 border-indigo-400/20 bg-indigo-400/10',
  vector_search: 'text-green-400 border-green-400/20 bg-green-400/10',
  reranking: 'text-yellow-400 border-yellow-400/20 bg-yellow-400/10',
  llm: 'text-pink-400 border-pink-400/20 bg-pink-400/10',
  final_output: 'text-emerald-400 border-emerald-400/20 bg-emerald-400/10',
};

export function QueryTracer({ executionId }: QueryTracerProps) {
  const { executionId: storeExecutionId } = useExecutionStore();
  const [trace, setTrace] = useState<QueryTrace | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

  const effectiveExecutionId = executionId || storeExecutionId;

  useEffect(() => {
    if (!effectiveExecutionId) return;

    const loadTrace = async () => {
      setLoading(true);
      setError(null);
      try {
        const traceData = await getTrace(effectiveExecutionId);
        setTrace(traceData);
        // Auto-expand all steps initially
        setExpandedSteps(new Set(traceData.steps.map(s => s.node_id)));
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to load trace');
      } finally {
        setLoading(false);
      }
    };

    loadTrace();
  }, [effectiveExecutionId]);

  const toggleStep = (nodeId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedSteps(newExpanded);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center space-y-2">
          <Clock className="w-8 h-8 text-blue-400 animate-spin mx-auto" />
          <p className="text-sm text-slate-400">Loading query trace...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center space-y-2">
          <p className="text-sm text-red-400">{error}</p>
          <p className="text-xs text-slate-400">Trace may not be available for this execution</p>
        </div>
      </div>
    );
  }

  if (!trace) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center space-y-2">
          <p className="text-sm text-slate-400">No trace data available</p>
          <p className="text-xs text-slate-500">Execute a RAG workflow to see query traces</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Trace Header */}
      <div className="glass rounded-lg p-4 border border-white/10">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-white mb-1">Query Trace</h3>
            <p className="text-xs text-slate-400">{trace.query}</p>
          </div>
          <div className="text-right space-y-1">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Clock className="w-3 h-3" />
              <span>{trace.total_duration_ms}ms</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <DollarSign className="w-3 h-3" />
              <span>${trace.total_cost.toFixed(4)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Trace Steps */}
      <div className="space-y-3">
        {trace.steps.map((step, index) => {
          const StepIcon = stepTypeIcons[step.step_type as keyof typeof stepTypeIcons] || FileText;
          const stepColor = stepTypeColors[step.step_type as keyof typeof stepTypeColors] || 'text-slate-400';
          const isExpanded = expandedSteps.has(step.node_id);
          const isLast = index === trace.steps.length - 1;

          return (
            <div key={`${step.node_id}-${index}`} className="relative">
              {/* Connection Line */}
              {!isLast && (
                <div className="absolute left-6 top-12 bottom-0 w-0.5 bg-white/10" />
              )}

              {/* Step Card */}
              <div className={cn('glass rounded-lg border overflow-hidden', stepColor)}>
                {/* Step Header */}
                <button
                  onClick={() => toggleStep(step.node_id)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={cn('p-2 rounded-lg border', stepColor)}>
                      <StepIcon className="w-4 h-4" />
                    </div>
                    <div className="text-left">
                      <div className="text-sm font-semibold text-white">
                        {stepTypeLabels[step.step_type as keyof typeof stepTypeLabels] || step.step_type}
                      </div>
                      <div className="text-xs text-slate-400">{step.node_id}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span>{step.duration_ms}ms</span>
                    {step.cost > 0 && <span>${step.cost.toFixed(4)}</span>}
                    <ArrowRight
                      className={cn('w-4 h-4 transition-transform', isExpanded && 'rotate-90')}
                    />
                  </div>
                </button>

                {/* Step Details */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-white/10 pt-3 space-y-3">
                    {renderStepDetails(step)}
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

function renderStepDetails(step: QueryTraceStep) {
  const { step_type, data } = step;

  switch (step_type) {
    case 'query_input':
      return (
        <div className="space-y-2">
          <div className="text-xs text-slate-400">Query Text</div>
          <div className="bg-black/20 rounded p-2 text-sm text-slate-200 font-mono">
            {data.query || 'N/A'}
          </div>
        </div>
      );

    case 'chunking':
      return (
        <div className="grid grid-cols-3 gap-3 text-xs">
          <div>
            <div className="text-slate-400 mb-1">Chunks Created</div>
            <div className="text-white font-semibold">{data.chunks_created || 0}</div>
          </div>
          <div>
            <div className="text-slate-400 mb-1">Chunk Size</div>
            <div className="text-white font-semibold">{data.chunk_size || 0}</div>
          </div>
          <div>
            <div className="text-slate-400 mb-1">Overlap</div>
            <div className="text-white font-semibold">{data.chunk_overlap || 0}</div>
          </div>
        </div>
      );

    case 'embedding':
      return (
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <div className="text-slate-400 mb-1">Embeddings Created</div>
            <div className="text-white font-semibold">{data.embeddings_created || 0}</div>
          </div>
          <div>
            <div className="text-slate-400 mb-1">Model</div>
            <div className="text-white font-semibold">{data.model || 'N/A'}</div>
          </div>
        </div>
      );

    case 'vector_search':
      return (
        <div className="space-y-3">
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div>
              <div className="text-slate-400 mb-1">Results Found</div>
              <div className="text-white font-semibold">{data.results_count || 0}</div>
            </div>
            <div>
              <div className="text-slate-400 mb-1">Top K</div>
              <div className="text-white font-semibold">{data.top_k || 0}</div>
            </div>
            <div>
              <div className="text-slate-400 mb-1">Provider</div>
              <div className="text-white font-semibold">{data.provider || 'N/A'}</div>
            </div>
          </div>
          {data.results && Array.isArray(data.results) && data.results.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs text-slate-400">Retrieved Chunks</div>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {data.results.map((result: any, idx: number) => (
                  <div
                    key={idx}
                    className="bg-black/20 rounded p-2 border border-white/10"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-400">Chunk #{idx + 1}</span>
                      <span className="text-xs text-green-400 font-semibold">
                        Score: {result.score?.toFixed(3) || 'N/A'}
                      </span>
                    </div>
                    <div className="text-xs text-slate-300 line-clamp-3">
                      {result.text || 'No text'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      );

    case 'reranking':
      return (
        <div className="space-y-3">
          <div className="grid grid-cols-4 gap-2 text-xs">
            <div>
              <div className="text-slate-400 mb-1">Reranked</div>
              <div className="text-white font-semibold">{data.reranked_count || 0}</div>
            </div>
            <div>
              <div className="text-slate-400 mb-1">Filtered</div>
              <div className="text-white font-semibold">{data.filtered_count || 0}</div>
            </div>
            <div>
              <div className="text-slate-400 mb-1">Final</div>
              <div className="text-white font-semibold">{data.final_count || 0}</div>
            </div>
            <div>
              <div className="text-slate-400 mb-1">Method</div>
              <div className="text-white font-semibold">{data.method || 'N/A'}</div>
            </div>
          </div>
          {data.results && Array.isArray(data.results) && data.results.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs text-slate-400">Reranked Results</div>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {data.results.map((result: any, idx: number) => (
                  <div
                    key={idx}
                    className="bg-black/20 rounded p-2 border border-white/10"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-400">Rank #{idx + 1}</span>
                      <div className="flex items-center gap-2">
                        {result.original_score !== undefined && (
                          <span className="text-xs text-slate-500">
                            Original: {result.original_score.toFixed(3)}
                          </span>
                        )}
                        <span className="text-xs text-yellow-400 font-semibold">
                          Rerank: {result.rerank_score?.toFixed(3) || 'N/A'}
                        </span>
                      </div>
                    </div>
                    <div className="text-xs text-slate-300 line-clamp-3">
                      {result.text || 'No text'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      );

    case 'llm':
      return (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <div className="text-slate-400 mb-1">Provider</div>
              <div className="text-white font-semibold">{data.provider || 'N/A'}</div>
            </div>
            <div>
              <div className="text-slate-400 mb-1">Model</div>
              <div className="text-white font-semibold">{data.model || 'N/A'}</div>
            </div>
          </div>
          {data.tokens_used && (
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div>
                <div className="text-slate-400 mb-1">Input Tokens</div>
                <div className="text-white font-semibold">
                  {data.tokens_used.input || data.tokens_used.prompt || 0}
                </div>
              </div>
              <div>
                <div className="text-slate-400 mb-1">Output Tokens</div>
                <div className="text-white font-semibold">
                  {data.tokens_used.output || data.tokens_used.completion || 0}
                </div>
              </div>
              <div>
                <div className="text-slate-400 mb-1">Total</div>
                <div className="text-white font-semibold">
                  {data.tokens_used.total || 0}
                </div>
              </div>
            </div>
          )}
          {data.response && (
            <div className="space-y-2">
              <div className="text-xs text-slate-400">Response</div>
              <div className="bg-black/20 rounded p-3 text-sm text-slate-200 whitespace-pre-wrap max-h-64 overflow-y-auto">
                {data.response}
              </div>
            </div>
          )}
        </div>
      );

    default:
      return (
        <div className="text-xs text-slate-400">
          <pre className="bg-black/20 rounded p-2 overflow-x-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      );
  }
}

