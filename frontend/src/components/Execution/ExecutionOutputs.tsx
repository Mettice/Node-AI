/**
 * Execution Outputs View - Final results from execution
 */

import { useState } from 'react';
import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { FileText, ChevronDown, ChevronRight } from 'lucide-react';

export function ExecutionOutputs() {
  const { results } = useExecutionStore();
  const { nodes } = useWorkflowStore();
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  // Get nodes with outputs
  const nodesWithOutputs = nodes
    .map((node) => {
      const result = results[node.id];
      const hasOutput = result?.output && Object.keys(result.output).length > 0;
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
      <h3 className="text-sm font-semibold text-slate-200 mb-3">Final Outputs</h3>
      
      {nodesWithOutputs.map(({ node, result }) => {
        const nodeName = node.data?.label || node.type || node.id;
        const isExpanded = expandedNodes.has(node.id);

        return (
          <div
            key={node.id}
            className="glass rounded-lg border border-white/10 overflow-hidden"
          >
            <button
              onClick={() => toggleNode(node.id)}
              className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
                )}
                <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                <span className="text-sm font-medium text-slate-200 truncate">
                  {nodeName}
                </span>
              </div>
              <span className="text-xs text-slate-400 flex-shrink-0 ml-2">
                {Object.keys(result.output || {}).length} output{Object.keys(result.output || {}).length !== 1 ? 's' : ''}
              </span>
            </button>

            {isExpanded && (
              <div className="px-4 pb-4 border-t border-white/10 pt-3">
                {/* Special handling for CrewAI output */}
                {result.output?.output && typeof result.output.output === 'string' && (
                  <div className="mb-3">
                    <div className="text-xs font-semibold text-purple-400 mb-2">CrewAI Report</div>
                    <div className="p-3 bg-white/5 border border-white/10 rounded text-sm text-slate-200 whitespace-pre-wrap max-h-96 overflow-y-auto">
                      {result.output.output}
                    </div>
                    {/* Metadata */}
                    {(result.output.agents || result.output.tasks || result.output.tokens_used) && (
                      <div className="mt-2 pt-2 border-t border-white/10 space-y-1 text-xs text-slate-400">
                        {result.output.agents && (
                          <div>
                            <span className="font-medium">Agents: </span>
                            {result.output.agents.join(', ')}
                          </div>
                        )}
                        {result.output.tasks && (
                          <div>
                            <span className="font-medium">Tasks: </span>
                            {result.output.tasks.length} completed
                          </div>
                        )}
                        {result.output.tokens_used && result.output.tokens_used.total > 0 && (
                          <div>
                            <span className="font-medium">Tokens: </span>
                            {result.output.tokens_used.total.toLocaleString()}
                            {' '}({result.output.tokens_used.input.toLocaleString()} in / {result.output.tokens_used.output.toLocaleString()} out)
                          </div>
                        )}
                      </div>
                    )}
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
        );
      })}
    </div>
  );
}

