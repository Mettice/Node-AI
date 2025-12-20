/**
 * Execution controls component - Run/Stop/Clear buttons
 */

import { useCallback, useState, useEffect } from 'react';
import { Play, Square, RotateCcw, Sparkles, DollarSign } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { useWorkflowStore } from '@/store/workflowStore';
import { useExecutionStore } from '@/store/executionStore';
import { useUIStore } from '@/store/uiStore';
import { executeWorkflow } from '@/services/workflows';
import { toast } from 'react-hot-toast';
import { validateWorkflow } from '@/utils/workflowValidation';
import { cn } from '@/utils/cn';

export function ExecutionControls() {
  const { nodes, edges, workflowName } = useWorkflowStore();
  const { status, startExecution, stopExecution, clearExecution } = useExecutionStore();
  const { toggleExecutionLogs, executionLogsOpen } = useUIStore();
  const [isMobile, setIsMobile] = useState(false);
  const [useIntelligentRouting, setUseIntelligentRouting] = useState(true); // Default: enabled
  const [estimatedCost, setEstimatedCost] = useState<number | null>(null);
  const [showCelebration, setShowCelebration] = useState(false);
  const [isStarting, setIsStarting] = useState(false); // Track if execution is starting

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Calculate estimated cost based on nodes
  useEffect(() => {
    if (nodes.length > 0) {
      // Simple cost estimation: $0.01 per node + $0.02 per LLM node
      const baseCost = nodes.length * 0.01;
      const llmNodes = nodes.filter(node => 
        node.type === 'chat' || node.type === 'langchain_agent' || node.type === 'crewai_agent'
      );
      const llmCost = llmNodes.length * 0.02;
      setEstimatedCost(baseCost + llmCost);
    } else {
      setEstimatedCost(null);
    }
  }, [nodes]);

  // Show celebration when execution completes
  useEffect(() => {
    if (status === 'completed') {
      setShowCelebration(true);
      // Hide celebration after animation
      const timer = setTimeout(() => setShowCelebration(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [status]);

  // Handle run workflow
  const handleRun = useCallback(async () => {
    // Ensure nodes and edges are defined
    const safeNodes = nodes || [];
    const safeEdges = edges || [];
    
    // Validate workflow
    const validation = validateWorkflow({ nodes: safeNodes, edges: safeEdges });
    if (!validation.valid) {
      toast.error(`Workflow validation failed: ${validation.errors.join(', ')}`);
      return;
    }

    // IMMEDIATE visual feedback: Set status to pending and show starting state
    setIsStarting(true);
    const { updateStatus } = useExecutionStore.getState();
    updateStatus('pending');

    try {
      // Build workflow object
      const workflow = {
        name: workflowName,
        nodes: safeNodes.map((node) => ({
          id: node.id,
          type: node.type || 'default',
          position: node.position,
          // Backend expects config directly in data, not nested under data.config
          data: node.data?.config || node.data || {},
        })),
        edges: safeEdges.map((edge) => ({
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
      safeNodes.forEach(node => {
        dependencies.set(node.id, new Set());
      });
      
      // Build dependency graph from edges
      safeEdges.forEach(edge => {
        dependencies.get(edge.target)?.add(edge.source);
      });
      
      // Find root nodes (nodes with no dependencies)
      const rootNodes = safeNodes.filter(node => dependencies.get(node.id)?.size === 0);
      
      console.log('[ExecutionControls] Total nodes:', safeNodes.length);
      console.log('[ExecutionControls] Root nodes (no dependencies):', rootNodes.map(n => `${n.data?.label || n.type} (${n.id})`));
      console.log('[ExecutionControls] All nodes:', safeNodes.map(n => `${n.data?.label || n.type} (${n.id})`));
      console.log('[ExecutionControls] Dependencies:', Array.from(dependencies.entries()).map(([id, deps]) => 
        `${safeNodes.find(n => n.id === id)?.data?.label || id}: [${Array.from(deps).map(depId => safeNodes.find(n => n.id === depId)?.data?.label || depId).join(', ')}]`
      ));
      
      // Only set root nodes to pending initially - others will be set when their dependencies complete
      const { updateNodeStatuses } = useExecutionStore.getState();
      const initialStatuses: Record<string, 'pending'> = {};
      rootNodes.forEach((node) => {
        initialStatuses[node.id] = 'pending';
        console.log('[ExecutionControls] Setting root node to pending:', node.data?.label || node.type, node.id);
      });
      updateNodeStatuses(initialStatuses);
      
      // Execute workflow with intelligent routing option
      const response = await executeWorkflow(workflow, {
        use_intelligent_routing: useIntelligentRouting,
      });
      
      // Start execution tracking
      startExecution(response.execution_id);
      setIsStarting(false); // Clear starting state once execution actually starts
      
      // Don't auto-open sidebar - let user open it via status bar if needed
      // Status bar will show at bottom during execution
      
      // Show toast with intelligent routing status
      if (useIntelligentRouting) {
        toast.success(
          (t) => (
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <div>
                <div className="font-medium">Workflow started with AI Routing</div>
                <div className="text-xs text-slate-400">Intelligent data mapping enabled</div>
              </div>
            </div>
          ),
          { duration: 3000 }
        );
      } else {
        toast.success('Workflow execution started');
      }
      
      // Log intelligent routing status for debugging
      console.log('[ExecutionControls] Workflow execution started', {
        execution_id: response.execution_id,
        intelligent_routing: useIntelligentRouting,
        node_count: safeNodes.length,
        edge_count: safeEdges.length
      });
      
      // Poll for updates
      pollExecutionStatus(response.execution_id);
    } catch (error: any) {
      setIsStarting(false); // Clear starting state on error
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
          // Continue polling (2 second interval to avoid rate limiting)
          setTimeout(poll, 2000);
        } else {
          // Execution completed or failed - ensure final results are updated
          // Force update all node results from backend when execution is complete
          if (statusResponse.results && typeof statusResponse.results === 'object') {
            Object.entries(statusResponse.results).forEach(([nodeId, result]: [string, any]) => {
              updateNodeResult(nodeId, {
                node_id: nodeId,
                status: result.status,
                output: result.output,
                error: result.error,
                cost: result.cost,
                duration_ms: result.duration_ms,
              });
            });
          }
          
          // Ensure duration is updated from the execution response (final update)
          // Duration should already be updated from line 191, but ensure it's set if missing
          if (statusResponse.duration_ms !== undefined && statusResponse.duration_ms !== null) {
            updateDuration(statusResponse.duration_ms);
          }
          
          isPolling = false;
        }
      } catch (error: any) {
        console.error('Polling error:', error);
        
        // Handle 422 errors (validation errors) - usually means execution is complete or ID is invalid
        if (error?.response?.status === 422) {
          console.log('Execution may be complete (422), attempting to fetch final results from trace...');
          
          // Try to get final results from trace endpoint (might still work even if status endpoint returns 422)
          try {
            const { getExecutionTrace } = await import('@/services/executions');
            const traceResponse = await getExecutionTrace(execId);
            updateTrace(traceResponse.trace || []);
            
            // Extract results from trace response if available
            if (traceResponse.results && typeof traceResponse.results === 'object') {
              Object.entries(traceResponse.results).forEach(([nodeId, result]: [string, any]) => {
                updateNodeResult(nodeId, {
                  node_id: nodeId,
                  status: result.status || 'completed',
                  output: result.output,
                  error: result.error,
                  cost: result.cost || 0,
                  duration_ms: result.duration_ms || 0,
                });
              });
              console.log('[ExecutionControls] Extracted results from trace response:', Object.keys(traceResponse.results));
            }
            
            // Also try to extract from trace steps if results not in response
            if ((!traceResponse.results || Object.keys(traceResponse.results).length === 0) && traceResponse.trace && Array.isArray(traceResponse.trace)) {
              traceResponse.trace.forEach((step: any) => {
                if (step.output && step.node_id) {
                  const { updateNodeResult } = useExecutionStore.getState();
                  updateNodeResult(step.node_id, {
                    node_id: step.node_id,
                    status: (step.status || step.action === 'completed' ? 'completed' : 'failed') as any,
                    output: step.output,
                    error: step.error,
                    cost: step.cost || 0,
                    duration_ms: step.duration_ms || 0,
                  });
                }
              });
            }
            
            console.log('[ExecutionControls] Fetched trace after 422, trace length:', traceResponse.trace?.length || 0);
          } catch (traceError) {
            console.warn('[ExecutionControls] Could not fetch trace after 422:', traceError);
          }
          
          isPolling = false;
          // Don't update status - keep current status from SSE
          return;
        }
        
        // Don't set status to failed on network errors - just log and continue
        // The execution might still be running or completed, we just couldn't poll
        // Only stop polling if it's a timeout or connection error, otherwise retry
        if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
          // Timeout - continue polling but with longer interval
          console.log('Polling timeout, continuing with longer interval...');
          setTimeout(poll, 5000); // Poll every 5 seconds after timeout
        } else {
          // Other errors - stop polling
          isPolling = false;
        }
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
  const isReady = !isRunning && nodes.length > 0;
  const isEmpty = nodes.length === 0;

  return (
    <div className={cn("flex items-center", isMobile ? "gap-2" : "gap-3")}>
      {/* Intelligent Routing Toggle - Icon only, status shown on hover */}
      {!isMobile && (
        <div className="relative group">
          <label className="cursor-pointer">
            <input
              type="checkbox"
              checked={useIntelligentRouting}
              onChange={(e) => setUseIntelligentRouting(e.target.checked)}
              disabled={isRunning}
              className="sr-only"
            />
            <div className={cn(
              "p-2.5 rounded-lg transition-all duration-200 border",
              "hover:scale-105 focus:ring-2 focus:ring-purple-500/50",
              useIntelligentRouting
                ? "bg-purple-500/20 text-purple-300 border-purple-500/30 shadow-lg shadow-purple-500/20"
                : "bg-slate-700/50 text-slate-400 border-slate-600/50 hover:bg-slate-700/70 hover:text-slate-300",
              isRunning && "opacity-50 cursor-not-allowed"
            )}>
              <Sparkles className="w-4 h-4" />
            </div>
          </label>
          
          {/* Hover tooltip - horizontal, compact design */}
          <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-2.5 py-1.5 bg-slate-800/95 backdrop-blur-sm border border-white/10 rounded-md text-xs text-white whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 z-50 shadow-lg">
            <div className="flex items-center gap-2">
              <span className={cn(
                "px-1.5 py-0.5 text-xs font-semibold rounded border",
                useIntelligentRouting
                  ? "bg-green-500/20 text-green-300 border-green-400/30"
                  : "bg-red-500/20 text-red-300 border-red-400/30"
              )}>
                {useIntelligentRouting ? "ON" : "OFF"}
              </span>
              <span className="text-slate-300">
                {useIntelligentRouting 
                  ? "AI maps data automatically"
                  : "Click to enable AI routing"
                }
              </span>
            </div>
            {/* Arrow */}
            <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800/95" />
          </div>
        </div>
      )}
      
      {/* Enhanced Run Button */}
      <div className="relative">
        {/* Celebration particles */}
        {showCelebration && !isMobile && (
          <div className="absolute inset-0 pointer-events-none">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="absolute w-2 h-2 bg-amber-400 rounded-full animate-celebration"
                style={{
                  left: '50%',
                  top: '50%',
                  animationDelay: `${i * 0.1}s`,
                  '--angle': `${i * 45}deg`
                } as React.CSSProperties}
              />
            ))}
          </div>
        )}
        
        <div className="relative group">
          <button
            onClick={handleRun}
            disabled={isRunning || isEmpty || isStarting}
            className={cn(
              'relative overflow-hidden rounded-lg transition-all duration-300 border',
              'focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:ring-offset-2 focus:ring-offset-slate-900',
              'transform active:scale-95',
              // Compact size - icon only
              'p-2.5',
              // State-based styling
              isEmpty && 'opacity-50 cursor-not-allowed bg-slate-700 border-slate-600 text-slate-400',
              isReady && !isEmpty && cn(
                'bg-gradient-to-br from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400',
                'text-black border-amber-300/40 shadow-lg shadow-amber-500/25',
                'hover:shadow-xl hover:shadow-amber-500/35 hover:scale-105',
                'animate-breathing-ready'
              ),
              (status === 'pending' || isStarting) && cn(
                'bg-gradient-to-br from-amber-400 to-orange-500',
                'text-black border-amber-300/40',
                'animate-pulse shadow-lg shadow-amber-500/50'
              ),
              status === 'running' && cn(
                'bg-gradient-to-br from-amber-400 to-orange-500',
                'text-black border-amber-300/40',
                'animate-pulse shadow-lg shadow-amber-500/60'
              )
            )}
          >
            {/* Background glow */}
            {isReady && !isEmpty && (
              <div className="absolute inset-0 bg-gradient-to-r from-amber-400/0 via-amber-300/20 to-amber-400/0 animate-pulse-slow" />
            )}
            
            {/* Pulsing glow effect for starting/running/pending */}
            {(isStarting || status === 'pending' || status === 'running') && (
              <div className="absolute inset-0 rounded-lg bg-amber-400/40 animate-ping" style={{ animationDuration: '1.5s' }} />
            )}
            
            {/* Progress ring for running state */}
            {(status === 'running' || status === 'pending') && (
              <div className="absolute inset-0 rounded-lg overflow-hidden">
                <svg className="absolute inset-0 w-full h-full">
                  <rect
                    x="1" y="1"
                    width="calc(100% - 2px)" height="calc(100% - 2px)"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeDasharray="60"
                    strokeDashoffset="60"
                    rx="6"
                    className="animate-progress-ring text-amber-200/80"
                  />
                </svg>
              </div>
            )}
            
            {/* Icon only */}
            <div className="relative z-10">
              {(status === 'pending' || status === 'running' || isStarting) ? (
                <div className="animate-spin">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                </div>
              ) : (
                <Play className="w-5 h-5 text-white" />
              )}
            </div>
          </button>
          
          {/* Hover tooltip */}
          <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-3 py-2 bg-slate-800/95 backdrop-blur-sm border border-white/10 rounded-lg text-sm text-white whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 z-50">
            <div className="font-medium">
              {status === 'pending' ? 'Starting...' : status === 'running' ? 'Running...' : 'Run Workflow'}
            </div>
            {estimatedCost !== null && !isRunning && (
              <div className="text-xs text-slate-400 flex items-center gap-1 mt-1">
                <DollarSign className="w-3 h-3" />
                Estimated: ${estimatedCost.toFixed(2)}
              </div>
            )}
            {/* Arrow */}
            <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800/95" />
          </div>
        </div>
      </div>

      {/* Stop Button - Icon only with hover tooltip */}
      {isRunning && (
        <div className="relative group">
          <button
            onClick={handleStop}
            className={cn(
              'p-2.5 rounded-lg transition-all duration-200 border',
              'bg-red-500/20 hover:bg-red-500/30 text-red-400 hover:text-red-300',
              'border-red-500/30 hover:border-red-500/40',
              'shadow-lg shadow-red-500/20 hover:shadow-xl hover:shadow-red-500/30',
              'hover:scale-105 active:scale-95',
              'focus:outline-none focus:ring-2 focus:ring-red-500/50'
            )}
          >
            <Square className="w-4 h-4" />
          </button>
          
          {/* Hover tooltip */}
          <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-3 py-2 bg-slate-800/95 backdrop-blur-sm border border-white/10 rounded-lg text-sm text-white whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 z-50">
            <div className="font-medium">Stop Execution</div>
            <div className="text-xs text-slate-400">Cancel current workflow</div>
            {/* Arrow */}
            <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800/95" />
          </div>
        </div>
      )}

      {/* Clear Button - Icon only with hover tooltip */}
      <div className="relative group">
        <button
          onClick={handleClear}
          disabled={status === 'idle'}
          className={cn(
            'p-2.5 rounded-lg transition-all duration-200 border',
            'bg-slate-700/50 hover:bg-slate-700/70 text-slate-400 hover:text-slate-300',
            'border-slate-600/50 hover:border-slate-600/70',
            'hover:scale-105 active:scale-95',
            'focus:outline-none focus:ring-2 focus:ring-slate-500/50',
            'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'
          )}
        >
          <RotateCcw className="w-4 h-4" />
        </button>
        
        {/* Hover tooltip */}
        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-3 py-2 bg-slate-800/95 backdrop-blur-sm border border-white/10 rounded-lg text-sm text-white whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 z-50">
          <div className="font-medium">Clear Results</div>
          <div className="text-xs text-slate-400">Reset execution state</div>
          {/* Arrow */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800/95" />
        </div>
      </div>
    </div>
  );
}

