/**
 * RAG Optimization Panel - Auto-tune your RAG workflow
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useWorkflowStore } from '@/store/workflowStore';
import { useExecutionStore } from '@/store/executionStore';
import {
  analyzeRAGWorkflow,
  type RAGOptimizationAnalysis,
  type OptimizationSuggestion,
} from '@/services/ragOptimization';
import { Spinner } from '@/components/common/Spinner';
import { Button } from '@/components/common/Button';
import {
  Sparkles,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  Lightbulb,
} from 'lucide-react';

export function RAGOptimizationPanel() {
  const { nodes, edges } = useWorkflowStore();
  const { executionId } = useExecutionStore();
  const { updateNode } = useWorkflowStore();
  const workflowId = 'current';
  const [analysis, setAnalysis] = useState<RAGOptimizationAnalysis | null>(null);

  // Analyze mutation
  const analyzeMutation = useMutation({
    mutationFn: analyzeRAGWorkflow,
    onSuccess: (data) => {
      setAnalysis(data);
    },
  });

  const handleAnalyze = () => {
    if (nodes.length === 0) return;

    const workflow = {
      id: workflowId,
      name: 'RAG Optimization',
      nodes: nodes,
      edges: edges,
    };

    analyzeMutation.mutate({
      workflow,
      execution_id: executionId || undefined,
    });
  };

  const handleApplySuggestion = (suggestion: OptimizationSuggestion) => {
    // Find the node and update its config
    const node = nodes.find((n) => n.id === suggestion.node_id);
    if (!node) return;

    const currentConfig = node.data?.config || {};
    const updatedConfig = {
      ...currentConfig,
      [suggestion.parameter]: suggestion.suggested_value,
    };

    updateNode(suggestion.node_id, {
      data: {
        ...node.data,
        config: updatedConfig,
      },
    });
  };

  return (
    <div className="h-full flex flex-col glass-strong border-r border-white/10">
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <h2 className="text-lg font-semibold text-white mb-2">Auto-tune RAG</h2>
        <p className="text-sm text-slate-400">
          Analyze your workflow and get optimization suggestions
        </p>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">

      {/* Analyze Button */}
      <div className="glass rounded-lg p-4 border border-white/10">
        <Button
          onClick={handleAnalyze}
          disabled={analyzeMutation.isPending || nodes.length === 0}
          className="w-full"
        >
          {analyzeMutation.isPending ? (
            <>
              <Spinner size="sm" className="mr-2" />
              Analyzing...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              Analyze Workflow
            </>
          )}
        </Button>
        {nodes.length === 0 && (
          <p className="text-xs text-yellow-400 mt-2 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            Add nodes to your workflow first
          </p>
        )}
      </div>

      {/* Current Metrics */}
      {analysis && Object.keys(analysis.current_metrics).length > 0 && (
        <div className="glass rounded-lg p-4 border border-white/10">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Current Configuration</h3>
          <div className="space-y-2">
            {Object.entries(analysis.current_metrics).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between text-sm">
                <span className="text-slate-400 capitalize">{key.replace('_', ' ')}</span>
                <span className="text-slate-200 font-medium">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Optimization Suggestions */}
      {analysis && analysis.suggestions.length > 0 && (
        <div className="glass rounded-lg p-4 border border-yellow-500/30 bg-yellow-500/10">
          <h3 className="text-sm font-semibold text-yellow-300 mb-3 flex items-center gap-2">
            <Lightbulb className="w-4 h-4" />
            Optimization Suggestions
          </h3>
          <div className="space-y-3">
            {analysis.suggestions.map((suggestion, idx) => (
              <div
                key={idx}
                className="p-3 bg-white/5 rounded border border-white/10"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-slate-200 mb-1">
                      {suggestion.node_type} • {suggestion.parameter}
                    </div>
                    <div className="text-xs text-slate-400 mb-2">
                      {suggestion.reasoning}
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                      <span className="text-slate-400">
                        Current: <span className="text-slate-300">{String(suggestion.current_value)}</span>
                      </span>
                      <span className="text-slate-400">→</span>
                      <span className="text-green-400 font-medium">
                        Suggested: {String(suggestion.suggested_value)}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <TrendingUp className="w-3 h-3 text-green-400" />
                      <span className="text-xs text-green-400 font-medium">
                        Expected: {suggestion.expected_improvement}
                      </span>
                      <span className="text-xs text-slate-500">
                        (Confidence: {Math.round(suggestion.confidence * 100)}%)
                      </span>
                    </div>
                  </div>
                </div>
                <Button
                  onClick={() => handleApplySuggestion(suggestion)}
                  className="mt-2 w-full text-xs"
                  size="sm"
                >
                  Apply Suggestion
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {analysis && analysis.suggestions.length === 0 && (
        <div className="glass rounded-lg p-4 border border-green-500/30 bg-green-500/10 text-center">
          <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-green-400" />
          <p className="text-sm text-slate-200">No optimization suggestions</p>
          <p className="text-xs text-slate-400 mt-1">Your RAG workflow is already optimized!</p>
        </div>
      )}
      </div>
    </div>
  );
}

