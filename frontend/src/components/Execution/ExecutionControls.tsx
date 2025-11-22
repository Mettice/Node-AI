/**
 * Execution controls component - Run/Stop/Clear buttons
 */

import { useCallback } from 'react';
import { Play, Square, RotateCcw } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { useWorkflowStore } from '@/store/workflowStore';
import { useExecutionStore } from '@/store/executionStore';
import { useUIStore } from '@/store/uiStore';
import { executeWorkflow } from '@/services/workflows';
import { toast } from 'react-hot-toast';
import { validateWorkflow } from '@/utils/workflowValidation';

export function ExecutionControls() {
  const { nodes, edges, workflowName } = useWorkflowStore();
  const { status, startExecution, stopExecution, clearExecution } = useExecutionStore();
  const { toggleExecutionLogs, executionLogsOpen } = useUIStore();

  // Handle run workflow
  const handleRun = useCallback(async () => {
    // Validate workflow
    const validation = validateWorkflow({ nodes, edges });
    if (!validation.valid) {
      toast.error(`Workflow validation failed: ${validation.errors.join(', ')}`);
      return;
    }

    try {
      // Build workflow object
      const workflow = {
        name: workflowName,
        nodes: nodes.map((node) => ({
          id: node.id,
          type: node.type || 'default',
          position: node.position,
          // Backend expects config directly in data, not nested under data.config
          data: node.data?.config || node.data || {},
        })),
        edges: edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle || undefined,
          targetHandle: edge.targetHandle || undefined,
        })),
      };

      // Calculate execution order based on dependencies (topological sort)
      // Only set root nodes (nodes with no dependencies) to pending initially
      const dependencies = new Map<string, Set<string>>(); // node -> set of dependencies
      
      // Initialize maps
      nodes.forEach(node => {
        dependencies.set(node.id, new Set());
      });
      
      // Build dependency graph from edges
      edges.forEach(edge => {
        dependencies.get(edge.target)?.add(edge.source);
      });
      
      // Find root nodes (nodes with no dependencies)
      const rootNodes = nodes.filter(node => dependencies.get(node.id)?.size === 0);
      
      console.log('[ExecutionControls] Total nodes:', nodes.length);
      console.log('[ExecutionControls] Root nodes (no dependencies):', rootNodes.map(n => `${n.data?.label || n.type} (${n.id})`));
      console.log('[ExecutionControls] All nodes:', nodes.map(n => `${n.data?.label || n.type} (${n.id})`));
      console.log('[ExecutionControls] Dependencies:', Array.from(dependencies.entries()).map(([id, deps]) => 
        `${nodes.find(n => n.id === id)?.data?.label || id}: [${Array.from(deps).map(depId => nodes.find(n => n.id === depId)?.data?.label || depId).join(', ')}]`
      ));
      
      // Only set root nodes to pending initially - others will be set when their dependencies complete
      const { updateNodeStatuses } = useExecutionStore.getState();
      const initialStatuses: Record<string, 'pending'> = {};
      rootNodes.forEach((node) => {
        initialStatuses[node.id] = 'pending';
        console.log('[ExecutionControls] Setting root node to pending:', node.data?.label || node.type, node.id);
      });
      updateNodeStatuses(initialStatuses);
      
      // Execute workflow
      const response = await executeWorkflow(workflow);
      
      // Start execution tracking
      startExecution(response.execution_id);
      
      // Don't auto-open sidebar - let user open it via status bar if needed
      // Status bar will show at bottom during execution
      
      toast.success('Workflow execution started');
      
      // Poll for updates
      pollExecutionStatus(response.execution_id);
    } catch (error: any) {
      toast.error(error.message || 'Failed to execute workflow');
      console.error('Execution error:', error);
    }
  }, [nodes, edges, workflowName, startExecution, executionLogsOpen, toggleExecutionLogs]);

  // Poll execution status
  const pollExecutionStatus = useCallback(async (execId: string) => {
    const { updateStatus, updateTrace, updateCost, updateDuration, updateNodeResult } = useExecutionStore.getState();
    const { getExecutionStatus: getStatus, getExecutionTrace: getTrace } = await import('@/services/executions');
    
    let isPolling = true;
    
    const poll = async () => {
      if (!isPolling) return;
      
      try {
        const statusResponse = await getStatus(execId);
        updateStatus(statusResponse.status);
        updateCost(statusResponse.total_cost);
        updateDuration(statusResponse.duration_ms);

        // Get trace for node-level updates
        const traceResponse = await getTrace(execId);
        updateTrace(traceResponse.trace || []);
        
        // Update individual node results from execution.results (not trace)
        // IMPORTANT: Don't override SSE statuses during execution - only update when execution is complete
        if (statusResponse.results && typeof statusResponse.results === 'object') {
          const currentState = useExecutionStore.getState();
          
          Object.entries(statusResponse.results).forEach(([nodeId, result]: [string, any]) => {
            const hasSSEStatus = currentState.nodeStatuses[nodeId];
            
            // Only update status from polling if:
            // 1. Execution is complete/failed (final state), OR
            // 2. Node has no SSE status yet (SSE events haven't arrived)
            // This prevents polling from overriding real-time SSE statuses
            if (!hasSSEStatus || statusResponse.status === 'completed' || statusResponse.status === 'failed') {
              updateNodeResult(nodeId, {
                node_id: nodeId,
                status: result.status,
                output: result.output,
                error: result.error,
                cost: result.cost,
                duration_ms: result.duration_ms,
              });
            } else {
              // Still update result data (output, cost, duration), but preserve SSE status
              const preservedStatus = currentState.nodeStatuses[nodeId];
              useExecutionStore.getState().updateNodeResult(nodeId, {
                node_id: nodeId,
                status: preservedStatus as 'pending' | 'running' | 'completed' | 'failed',
                output: result.output,
                error: result.error,
                cost: result.cost,
                duration_ms: result.duration_ms,
              });
            }
          });
        }

        if (statusResponse.status === 'running' || statusResponse.status === 'pending') {
          // Continue polling
          setTimeout(poll, 500);
        } else {
          // Execution completed or failed
          isPolling = false;
        }
      } catch (error) {
        console.error('Polling error:', error);
        updateStatus('failed');
        isPolling = false;
      }
    };

    poll();
    
    // Return cleanup function
    return () => {
      isPolling = false;
    };
  }, [toggleExecutionLogs]);

  // Handle stop execution
  const handleStop = useCallback(() => {
    stopExecution();
    toast('Execution stopped', { icon: '⏹️' });
  }, [stopExecution]);

  // Handle clear results
  const handleClear = useCallback(() => {
    clearExecution();
    toast.success('Results cleared');
  }, [clearExecution]);

  const isRunning = status === 'running' || status === 'pending';

  return (
    <div className="flex items-center gap-3">
      <Button
        variant="primary"
        size="sm"
        onClick={handleRun}
        disabled={isRunning || nodes.length === 0}
        isLoading={status === 'pending'}
      >
        <Play className="w-4 h-4 mr-1" />
        Run Workflow
      </Button>

      {isRunning && (
        <Button
          variant="danger"
          size="sm"
          onClick={handleStop}
        >
          <Square className="w-4 h-4 mr-1" />
          Stop
        </Button>
      )}

      <Button
        variant="secondary"
        size="sm"
        onClick={handleClear}
        disabled={status === 'idle'}
      >
        <RotateCcw className="w-4 h-4 mr-1" />
        Clear
      </Button>
    </div>
  );
}

