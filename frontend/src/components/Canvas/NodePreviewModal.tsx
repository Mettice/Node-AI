/**
 * Node preview modal - shows execution details, cost, output, etc.
 */

import { X, Clock, CheckCircle2, XCircle, Loader2, Pencil } from 'lucide-react';
import { createPortal } from 'react-dom';
import { useExecutionStore } from '@/store/executionStore';
import { Button } from '@/components/common/Button';
import { cn } from '@/utils/cn';
import type { Node } from 'reactflow';

interface NodePreviewModalProps {
  node: Node;
  onClose: () => void;
  onEdit: () => void;
}

export function NodePreviewModal({ node, onClose, onEdit }: NodePreviewModalProps) {
  const { results, trace } = useExecutionStore();
  const executionResult = results[node.id];
  const executionStep = trace.find((step) => step.node_id === node.id);

  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const statusConfig = {
    pending: { icon: Loader2, color: 'text-yellow-600', label: 'Pending' },
    running: { icon: Loader2, color: 'text-blue-600', label: 'Running' },
    completed: { icon: CheckCircle2, color: 'text-green-600', label: 'Completed' },
    failed: { icon: XCircle, color: 'text-red-600', label: 'Failed' },
    idle: { icon: Clock, color: 'text-gray-600', label: 'Idle' },
  };

  const status = executionResult?.status || executionStep?.status || 'idle';
  const config = statusConfig[status] || statusConfig.idle;
  const StatusIcon = config.icon;
  const isSpinning = status === 'running' || status === 'pending';

  const modalContent = (
    <div className="fixed inset-0 z-[50] flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={config.color}>
              <StatusIcon className={cn('w-5 h-5', isSpinning && 'animate-spin')} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">{node.data?.label || node.type}</h2>
              <p className="text-sm text-gray-500">Node ID: {node.id}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={onEdit}
            >
              <Pencil className="w-4 h-4 mr-1" />
              Edit
            </Button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors p-1"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Execution Status */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Execution Status</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-gray-500 mb-1">Status</div>
                <div className={cn('flex items-center gap-2', config.color)}>
                  <StatusIcon className={cn('w-4 h-4', isSpinning && 'animate-spin')} />
                  <span className="text-sm font-medium">{config.label}</span>
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Duration</div>
                <div className="text-sm font-medium text-gray-900">
                  {formatDuration(executionResult?.duration_ms || executionStep?.duration_ms)}
                </div>
              </div>
            </div>
          </div>


          {/* Configuration */}
          {node.data?.config && Object.keys(node.data.config).length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Configuration</h3>
              <div className="space-y-1 text-xs">
                {Object.entries(node.data.config).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600">{key}:</span>
                    <span className="text-gray-900 font-medium">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Output */}
          {(executionResult?.output || executionStep?.output) && (
            <div className="bg-green-50 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Output</h3>
              <details className="cursor-pointer">
                <summary className="text-sm font-medium text-gray-700 mb-2">
                  View Output ({Object.keys(executionResult?.output || executionStep?.output || {}).length} keys)
                </summary>
                <pre className="mt-2 p-3 bg-white rounded text-xs overflow-auto max-h-64 border border-gray-200">
                  {JSON.stringify(executionResult?.output || executionStep?.output, null, 2)}
                </pre>
              </details>
            </div>
          )}

          {/* Error */}
          {(executionResult?.error || executionStep?.error) && (
            <div className="bg-red-50 rounded-lg p-4 border border-red-200">
              <h3 className="text-sm font-semibold text-red-700 mb-2">Error</h3>
              <p className="text-sm text-red-600">{executionResult?.error || executionStep?.error}</p>
            </div>
          )}

          {/* Execution Timeline */}
          {(executionStep?.started_at || executionStep?.completed_at) && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Execution Timeline</h3>
              <div className="space-y-2 text-xs">
                {executionStep?.started_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Started:</span>
                    <span className="text-gray-900">
                      {new Date(executionStep.started_at).toLocaleString()}
                    </span>
                  </div>
                )}
                {executionStep?.completed_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Completed:</span>
                    <span className="text-gray-900">
                      {new Date(executionStep.completed_at).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {!executionResult && !executionStep && (
            <div className="text-center py-8 text-gray-500">
              <p>No execution data available</p>
              <p className="text-sm mt-1">Run the workflow to see execution details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}

