/**
 * Dashboard Query Component
 * 
 * Allows users to query deployed workflows directly from the Dashboard
 */

import { useState, useEffect } from 'react';
import { Search, Play, Loader2, CheckCircle, AlertCircle, Copy, ExternalLink, DollarSign, Clock } from 'lucide-react';
import { listWorkflows, queryWorkflow, type WorkflowListItem, type WorkflowQueryResponse } from '@/services/workflowManagement';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { cn } from '@/utils/cn';

export function DashboardQuery() {
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [queryInput, setQueryInput] = useState<Record<string, string>>({});
  const [querying, setQuerying] = useState(false);
  const [lastResult, setLastResult] = useState<WorkflowQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch deployed workflows
  const { data: workflowsData, isLoading } = useQuery({
    queryKey: ['workflows', 'deployed'],
    queryFn: () => listWorkflows({ limit: 100 }),
  });

  const deployedWorkflows = (workflowsData?.workflows || []).filter(w => w.is_deployed);

  // Auto-select first deployed workflow if available
  useEffect(() => {
    if (deployedWorkflows.length > 0 && !selectedWorkflowId) {
      setSelectedWorkflowId(deployedWorkflows[0].id);
    }
  }, [deployedWorkflows, selectedWorkflowId]);

  const selectedWorkflow = deployedWorkflows.find(w => w.id === selectedWorkflowId);

  const handleQuery = async () => {
    if (!selectedWorkflowId) {
      toast.error('Please select a workflow');
      return;
    }

    setQuerying(true);
    setError(null);
    setLastResult(null);

    try {
      const result = await queryWorkflow(selectedWorkflowId, {
        input: queryInput,
      });
      setLastResult(result);
      toast.success('Query executed successfully');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail?.message || err.message || 'Failed to execute query';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setQuerying(false);
    }
  };

  const copyApiEndpoint = () => {
    if (!selectedWorkflowId) return;
    const endpoint = `${window.location.origin}/api/v1/workflows/${selectedWorkflowId}/query`;
    navigator.clipboard.writeText(endpoint);
    toast.success('API endpoint copied to clipboard');
  };

  const copyExampleCode = () => {
    if (!selectedWorkflowId) return;
    const example = `curl -X POST ${window.location.origin}/api/v1/workflows/${selectedWorkflowId}/query \\
  -H "Content-Type: application/json" \\
  -d '{
    "input": {
      "query": "Your question here"
    }
  }'`;
    navigator.clipboard.writeText(example);
    toast.success('Example code copied to clipboard');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin mr-2" />
        <span>Loading deployed workflows...</span>
      </div>
    );
  }

  if (deployedWorkflows.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-400">
        <Search className="w-16 h-16 mb-4 opacity-50" />
        <p className="text-lg mb-2">No deployed workflows</p>
        <p className="text-sm mb-6">Deploy a workflow to start querying it</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto w-full space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Query Deployed Workflows</h2>
          <p className="text-sm text-slate-400">
            Test and interact with your deployed workflows
          </p>
        </div>

        {/* Workflow Selector */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <label className="block text-sm font-semibold text-slate-300 mb-2">
            Select Workflow
          </label>
          <select
            value={selectedWorkflowId || ''}
            onChange={(e) => {
              setSelectedWorkflowId(e.target.value);
              setQueryInput({});
              setLastResult(null);
              setError(null);
            }}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all hover:bg-white/8 hover:border-white/20 appearance-none cursor-pointer"
          >
            {deployedWorkflows.map((workflow) => (
              <option key={workflow.id} value={workflow.id} className="bg-slate-800 text-white">
                {workflow.name}
              </option>
            ))}
          </select>
          {selectedWorkflow?.description && (
            <p className="text-xs text-slate-400 mt-2">{selectedWorkflow.description}</p>
          )}
        </div>

        {/* Query Input */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4 space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Query Input
            </label>
            <p className="text-xs text-slate-400 mb-3">
              Enter input data for your workflow (e.g., query, file_id, etc.)
            </p>
            
            {/* Simple query input (most common case) */}
            <div className="space-y-2">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Query</label>
                <input
                  type="text"
                  value={queryInput.query || ''}
                  onChange={(e) => setQueryInput({ ...queryInput, query: e.target.value })}
                  placeholder="Enter your question or query..."
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                      handleQuery();
                    }
                  }}
                />
              </div>
              
              {/* Additional inputs */}
              <details className="text-xs text-slate-400">
                <summary className="cursor-pointer hover:text-slate-300 mb-2">Advanced: Add more input fields</summary>
                <div className="space-y-2 mt-2">
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">File ID (optional)</label>
                    <input
                      type="text"
                      value={queryInput.file_id || ''}
                      onChange={(e) => setQueryInput({ ...queryInput, file_id: e.target.value })}
                      placeholder="file_id"
                      className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Context (optional)</label>
                    <textarea
                      value={queryInput.context || ''}
                      onChange={(e) => setQueryInput({ ...queryInput, context: e.target.value })}
                      placeholder="Additional context..."
                      rows={3}
                      className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm resize-none"
                    />
                  </div>
                </div>
              </details>
            </div>
          </div>

          <button
            onClick={handleQuery}
            disabled={querying || !queryInput.query}
            className={cn(
              "flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed",
              querying && "cursor-wait"
            )}
          >
            {querying ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Querying...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Execute Query</span>
              </>
            )}
          </button>
        </div>

        {/* API Info */}
        {selectedWorkflowId && (
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-blue-300">API Endpoint</h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={copyApiEndpoint}
                  className="p-1.5 text-blue-400 hover:text-blue-300 hover:bg-blue-500/20 rounded transition-colors"
                  title="Copy endpoint"
                >
                  <Copy className="w-4 h-4" />
                </button>
                <button
                  onClick={copyExampleCode}
                  className="p-1.5 text-blue-400 hover:text-blue-300 hover:bg-blue-500/20 rounded transition-colors"
                  title="Copy example code"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            </div>
            <code className="text-xs text-blue-200 break-all">
              POST {window.location.origin}/api/v1/workflows/{selectedWorkflowId}/query
            </code>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <h3 className="text-sm font-semibold text-red-300">Error</h3>
            </div>
            <p className="text-sm text-red-200">{error}</p>
          </div>
        )}

        {/* Results Display */}
        {lastResult && (
          <div className="bg-white/5 border border-white/10 rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <h3 className="text-lg font-semibold text-white">Query Results</h3>
              </div>
              <div className="flex items-center gap-4 text-sm text-slate-400">
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  <span>{lastResult.duration_ms || 0}ms</span>
                </div>
                <div className="flex items-center gap-1">
                  <DollarSign className="w-4 h-4" />
                  <span>${(lastResult.total_cost || 0).toFixed(6)}</span>
                </div>
              </div>
            </div>

            {/* Results Content - Show only final response by default */}
            <div className="space-y-3">
              {(() => {
                // Find the final response (usually from chat node)
                const chatNodeId = Object.keys(lastResult.results).find(
                  key => key.toLowerCase().includes('chat') || 
                         (typeof lastResult.results[key] === 'object' && 
                          lastResult.results[key] !== null && 
                          'response' in lastResult.results[key])
                );
                
                // Show final response prominently
                if (chatNodeId && lastResult.results[chatNodeId]) {
                  const chatResult = lastResult.results[chatNodeId];
                  const response = typeof chatResult === 'object' && chatResult !== null && 'response' in chatResult
                    ? chatResult.response
                    : typeof chatResult === 'string' ? chatResult : JSON.stringify(chatResult);
                  
                  return (
                    <>
                      <div className="bg-white/5 border border-white/10 rounded p-4">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-semibold text-white">Response</span>
                          {typeof chatResult === 'object' && chatResult !== null && 'cost' in chatResult && (
                            <span className="text-xs text-slate-400">${(chatResult.cost as number).toFixed(6)}</span>
                          )}
                        </div>
                        <div className="text-sm text-slate-200 whitespace-pre-wrap">
                          {response}
                        </div>
                        {typeof chatResult === 'object' && chatResult !== null && 'citations' in chatResult && Array.isArray(chatResult.citations) && (
                          <div className="mt-3 pt-3 border-t border-white/10">
                            <p className="text-xs text-slate-400 mb-2">Citations:</p>
                            <div className="space-y-1">
                              {chatResult.citations.map((citation: any, idx: number) => (
                                <div key={idx} className="text-xs text-slate-400">
                                  {citation?.file_name || citation?.uri || `Citation ${idx + 1}`}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {/* Show other node results in collapsible section */}
                      {lastResult.results && typeof lastResult.results === 'object' && Object.keys(lastResult.results).length > 1 && (
                        <details className="bg-white/5 border border-white/10 rounded p-3">
                          <summary className="cursor-pointer text-xs font-semibold text-slate-400 hover:text-slate-300 mb-2">
                            Show all node results ({Object.keys(lastResult.results).length - 1} more)
                          </summary>
                          <div className="space-y-2 mt-2">
                            {Object.entries(lastResult.results)
                              .filter(([key]) => key !== chatNodeId)
                              .map(([nodeId, result]) => (
                                <div key={nodeId} className="bg-black/20 border border-white/5 rounded p-2">
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-semibold text-purple-300 uppercase">{nodeId}</span>
                                    {typeof result === 'object' && result !== null && 'cost' in result && (
                                      <span className="text-xs text-slate-500">${(result.cost as number).toFixed(6)}</span>
                                    )}
                                  </div>
                                  <div className="text-xs text-slate-400">
                                    {typeof result === 'object' && result !== null ? (
                                      <pre className="whitespace-pre-wrap font-mono text-xs bg-black/20 p-2 rounded overflow-x-auto max-h-32 overflow-y-auto">
                                        {JSON.stringify(result, null, 2)}
                                      </pre>
                                    ) : (
                                      <p className="truncate">{String(result)}</p>
                                    )}
                                  </div>
                                </div>
                              ))}
                          </div>
                        </details>
                      )}
                    </>
                  );
                }
                
                // Fallback: show all results if no chat node found
                return lastResult.results && typeof lastResult.results === 'object' 
                  ? Object.entries(lastResult.results).map(([nodeId, result]) => (
                  <div key={nodeId} className="bg-white/5 border border-white/10 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-purple-300 uppercase">{nodeId}</span>
                      {typeof result === 'object' && result !== null && 'cost' in result && (
                        <span className="text-xs text-slate-400">${(result.cost as number).toFixed(6)}</span>
                      )}
                    </div>
                    <div className="text-sm text-slate-300">
                      {typeof result === 'object' && result !== null ? (
                        <pre className="whitespace-pre-wrap font-mono text-xs bg-black/20 p-2 rounded overflow-x-auto">
                          {JSON.stringify(result, null, 2)}
                        </pre>
                      ) : (
                        <p>{String(result)}</p>
                      )}
                    </div>
                  </div>
                ))
                  : <div className="text-slate-400 text-sm">No results available</div>;
              })()}
            </div>

            {/* Execution Info */}
            <div className="pt-3 border-t border-white/10 text-xs text-slate-400">
              <p>Execution ID: {lastResult.execution_id}</p>
              <p>Status: <span className="text-green-400 capitalize">{lastResult.status}</span></p>
              {lastResult.completed_at && (
                <p>Completed: {new Date(lastResult.completed_at).toLocaleString()}</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

