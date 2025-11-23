/**
 * RAG Evaluation Panel - Test your RAG workflow quality
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useWorkflowStore } from '@/store/workflowStore';
import {
  uploadTestDataset,
  evaluateRAGWorkflow,
  listEvaluations,
} from '@/services/ragEvaluation';
import { Spinner } from '@/components/common/Spinner';
import { Button } from '@/components/common/Button';
import { 
  Upload, 
  Play, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  DollarSign,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/utils/cn';

export function RAGEvaluationPanel() {
  const { nodes, edges } = useWorkflowStore();
  const workflowId = 'current'; // Use 'current' as workflow ID for now
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [maxQueries, setMaxQueries] = useState<number | undefined>(undefined);

  // Upload dataset mutation
  const uploadMutation = useMutation({
    mutationFn: uploadTestDataset,
    onSuccess: (data) => {
      setDatasetId(data.dataset_id);
    },
  });

  // Evaluate workflow mutation
  const evaluateMutation = useMutation({
    mutationFn: evaluateRAGWorkflow,
  });

  // List evaluations
  const { data: evaluations, refetch: refetchEvaluations } = useQuery({
    queryKey: ['rag-evaluations', workflowId],
    queryFn: () => listEvaluations(workflowId || undefined),
    enabled: !!workflowId,
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = () => {
    if (!selectedFile) return;
    uploadMutation.mutate(selectedFile);
  };

  const handleEvaluate = () => {
    if (!datasetId || nodes.length === 0) return;

    // Build workflow object
    const workflow = {
      id: workflowId,
      name: 'RAG Evaluation',
      nodes: nodes,
      edges: edges,
    };

    evaluateMutation.mutate(
      {
        workflow,
        test_dataset_id: datasetId,
        max_queries: maxQueries,
      },
      {
        onSuccess: () => {
          refetchEvaluations();
        },
      }
    );
  };

  const latestEvaluation = evaluations && evaluations.length > 0 ? evaluations[0] : null;

  return (
    <div className="h-full flex flex-col glass-strong border-r border-white/10">
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <h2 className="text-lg font-semibold text-white mb-2">RAG Evaluation</h2>
        <p className="text-sm text-slate-400">
          Upload test Q&A pairs and evaluate your RAG workflow quality
        </p>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">

      {/* Upload Test Dataset */}
      <div className="glass rounded-lg p-4 border border-white/10">
        <h3 className="text-sm font-semibold text-slate-200 mb-3">1. Upload Test Dataset</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-slate-400 mb-2">
              Upload JSON or JSONL file with Q&A pairs
            </label>
            <input
              type="file"
              accept=".json,.jsonl"
              onChange={handleFileSelect}
              className="block w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-500 file:text-white hover:file:bg-blue-600"
            />
            <p className="text-xs text-slate-500 mt-1">
              Format: [{'{'} "question": "...", "expected_answer": "...", "context": "..." {'}'}]
            </p>
          </div>
          {selectedFile && (
            <div className="flex items-center gap-2 text-sm text-slate-300">
              <FileText className="w-4 h-4" />
              <span>{selectedFile.name}</span>
            </div>
          )}
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || uploadMutation.isPending}
            className="w-full"
          >
            {uploadMutation.isPending ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Upload Dataset
              </>
            )}
          </Button>
          {uploadMutation.isSuccess && (
            <div className="text-sm text-green-400 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Dataset uploaded: {uploadMutation.data.num_pairs} pairs
            </div>
          )}
        </div>
      </div>

      {/* Run Evaluation */}
      {datasetId && (
        <div className="glass rounded-lg p-4 border border-white/10">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">2. Run Evaluation</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-slate-400 mb-2">
                Max queries to test (optional, leave empty for all)
              </label>
              <input
                type="number"
                value={maxQueries || ''}
                onChange={(e) => setMaxQueries(e.target.value ? parseInt(e.target.value) : undefined)}
                placeholder="All queries"
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-slate-200 placeholder-slate-500"
              />
            </div>
            <Button
              onClick={handleEvaluate}
              disabled={evaluateMutation.isPending || nodes.length === 0}
              className="w-full"
            >
              {evaluateMutation.isPending ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Evaluating...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Run Evaluation
                </>
              )}
            </Button>
            {nodes.length === 0 && (
              <p className="text-xs text-yellow-400 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Add nodes to your workflow first
              </p>
            )}
          </div>
        </div>
      )}

      {/* Evaluation Results */}
      {latestEvaluation && (
        <div className="glass rounded-lg p-4 border border-white/10">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Latest Results</h3>
          
          {/* Summary Stats */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-white/5 rounded p-3">
              <div className="text-xs text-slate-400 mb-1">Accuracy</div>
              <div className="text-2xl font-bold text-green-400">
                {(latestEvaluation.accuracy * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {latestEvaluation.correct_answers}/{latestEvaluation.total_queries} correct
              </div>
            </div>
            <div className="bg-white/5 rounded p-3">
              <div className="text-xs text-slate-400 mb-1">Avg Relevance</div>
              <div className="text-2xl font-bold text-blue-400">
                {(latestEvaluation.average_relevance * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-white/5 rounded p-3">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Avg Latency
              </div>
              <div className="text-lg font-semibold text-slate-200">
                {latestEvaluation.average_latency_ms}ms
              </div>
            </div>
            <div className="bg-white/5 rounded p-3">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1">
                <DollarSign className="w-3 h-3" />
                Cost per Query
              </div>
              <div className="text-lg font-semibold text-green-400">
                ${latestEvaluation.cost_per_query.toFixed(4)}
              </div>
            </div>
          </div>

          {/* Failed Queries */}
          {latestEvaluation.failed_queries > 0 && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded">
              <div className="text-sm text-red-400 flex items-center gap-2">
                <XCircle className="w-4 h-4" />
                {latestEvaluation.failed_queries} query{latestEvaluation.failed_queries > 1 ? 'ies' : 'y'} failed
              </div>
            </div>
          )}

          {/* Results List */}
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {latestEvaluation.results.slice(0, 10).map((result, idx) => (
              <div
                key={idx}
                className={cn(
                  'p-3 rounded border',
                  result.is_correct
                    ? 'bg-green-500/10 border-green-500/30'
                    : 'bg-white/5 border-white/10'
                )}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-slate-200 mb-1">
                      Q: {result.question}
                    </div>
                    <div className="text-xs text-slate-400 mb-1">
                      Expected: {result.expected_answer}
                    </div>
                    <div className="text-xs text-slate-300">
                      Got: {result.actual_answer || '(no answer)'}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {result.is_correct ? (
                      <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-500">
                  <span>Relevance: {(result.relevance_score * 100).toFixed(1)}%</span>
                  <span>Latency: {result.latency_ms}ms</span>
                  <span>Cost: ${result.cost.toFixed(4)}</span>
                </div>
                {result.error && (
                  <div className="mt-2 text-xs text-red-400 bg-red-900/30 p-2 rounded">
                    Error: {result.error}
                  </div>
                )}
              </div>
            ))}
            {latestEvaluation.results.length > 10 && (
              <div className="text-xs text-slate-500 text-center py-2">
                Showing first 10 of {latestEvaluation.results.length} results
              </div>
            )}
          </div>
        </div>
      )}
      </div>
    </div>
  );
}

