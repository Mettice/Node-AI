/**
 * Execution state management (Zustand)
 */

import { create } from 'zustand';
import type { NodeResult, ExecutionStep } from '@/types/api';
import { useWorkflowStore } from './workflowStore';

type ExecutionStatus = 'idle' | 'pending' | 'running' | 'completed' | 'failed';

interface NodeSSEEvent {
  event_type: string;
  message: string;
  timestamp: string;
  progress?: number;
  agent?: string; // Agent name/role from SSE event
  task?: string; // Task name from SSE event
  input_tokens?: number; // Input tokens used
  output_tokens?: number; // Output tokens used
  total_tokens?: number; // Total tokens used
  data?: {
    thought?: string;
    tool?: string;
    tokens_used?: {
      input_tokens?: number;
      output_tokens?: number;
      total_tokens?: number;
    };
    [key: string]: any;
  };
}

interface ExecutionState {
  // Execution data
  executionId: string | null;
  status: ExecutionStatus;
  results: Record<string, NodeResult>;
  trace: ExecutionStep[];
  cost: number;
  duration: number;
  error: string | null;
  nodeEvents: Record<string, NodeSSEEvent[]>; // SSE events per node
  currentNodeId: string | null; // Currently executing node
  nodeStatuses: Record<string, 'pending' | 'running' | 'completed' | 'failed' | 'idle'>; // Real-time node statuses from SSE

  // Actions
  startExecution: (executionId: string) => void;
  stopExecution: () => void;
  updateStatus: (status: ExecutionStatus) => void;
  updateNodeResult: (nodeId: string, result: NodeResult) => void;
  updateTrace: (trace: ExecutionStep[]) => void;
  updateCost: (cost: number) => void;
  updateDuration: (duration: number) => void;
  setError: (error: string | null) => void;
  addNodeEvent: (nodeId: string, event: NodeSSEEvent) => void;
  setCurrentNode: (nodeId: string | null) => void;
  updateNodeStatuses: (statuses: Record<string, 'pending' | 'running' | 'completed' | 'failed' | 'idle'>) => void;
  clearExecution: () => void;
  getExecutionStatus: (executionId: string) => Promise<any>;
  getExecutionTrace: (executionId: string) => Promise<any>;
}

export const useExecutionStore = create<ExecutionState>((set) => ({
  // Initial state
  executionId: null,
  status: 'idle',
  results: {},
  trace: [],
  cost: 0,
  duration: 0,
  error: null,
  nodeEvents: {},
  currentNodeId: null,
  nodeStatuses: {},

  // Actions
  startExecution: (executionId) =>
    set({
      executionId,
      status: 'running',
      results: {},
      trace: [],
      cost: 0,
      duration: 0,
      error: null,
      nodeEvents: {},
      currentNodeId: null,
      nodeStatuses: {}, // Clear previous node statuses when starting new execution
    }),

  stopExecution: () =>
    set((state) => ({
      status: state.status === 'running' ? 'failed' : state.status,
      error: state.status === 'running' ? 'Execution stopped by user' : state.error,
      nodeStatuses: {}, // Clear node statuses when stopping
    })),

  updateStatus: (status) => {
    set({ status });
    
    // Auto-open sidebar when execution completes or fails
    if (status === 'completed' || status === 'failed') {
      // Import and open sidebar
      import('@/store/uiStore').then(({ useUIStore }) => {
        useUIStore.getState().setExecutionLogsOpen(true);
      });
    }
  },

  updateNodeResult: (nodeId, result) =>
    set((state) => {
      // Don't override SSE statuses with polling results if execution is still running
      // Only update status from polling if:
      // 1. No SSE status exists for this node, OR
      // 2. Execution is completed/failed (final state), OR
      // 3. Polling result is 'completed' and SSE status is not 'completed' (finalize completed status)
      const currentSSEStatus = state.nodeStatuses[nodeId];
      const shouldUpdateStatus = !currentSSEStatus || 
                                 state.status === 'completed' || 
                                 state.status === 'failed' ||
                                 (result.status === 'completed' && currentSSEStatus !== 'completed' && currentSSEStatus !== 'failed');
      
      // Determine final status: prefer completed over failed, prefer backend result over SSE if execution is done
      // Convert 'idle' to 'pending' for consistency
      const normalizedSSEStatus = (currentSSEStatus === 'idle' ? 'pending' : currentSSEStatus) as 'pending' | 'running' | 'completed' | 'failed';
      let finalStatus: 'pending' | 'running' | 'completed' | 'failed' = result.status || normalizedSSEStatus || 'pending';
      if (state.status === 'completed' || state.status === 'failed') {
        // When execution is done, trust backend results
        finalStatus = result.status || normalizedSSEStatus || 'pending';
        // But never allow failed to overwrite completed
        if (normalizedSSEStatus === 'completed' && result.status === 'failed') {
          finalStatus = 'completed';
        }
      } else if (normalizedSSEStatus === 'completed' && result.status === 'failed') {
        // Never allow failed to overwrite completed (even during execution)
        finalStatus = 'completed';
      } else if (shouldUpdateStatus) {
        finalStatus = result.status || normalizedSSEStatus || 'pending';
      } else {
        finalStatus = normalizedSSEStatus || 'pending';
      }
      
      return {
        results: {
          ...state.results,
          [nodeId]: result,
        },
        // Update status based on logic above
        nodeStatuses: {
          ...state.nodeStatuses,
          [nodeId]: finalStatus,
        },
      };
    }),

  updateTrace: (trace) =>
    set({
      trace,
    }),

  updateCost: (cost) =>
    set({
      cost,
    }),

  updateDuration: (duration) =>
    set({
      duration,
    }),

  setError: (error) =>
    set({
      error,
      status: 'failed',
    }),

  addNodeEvent: (nodeId, event) =>
    set((state) => {
      // Status update logging - ENABLED FOR DEBUGGING
      console.log('[ExecutionStore] addNodeEvent:', nodeId, event.event_type, 'progress:', event.progress, 'current status:', state.nodeStatuses[nodeId]);
      
      // Update node status based on event type
      const updatedStatuses: Record<string, 'pending' | 'running' | 'completed' | 'failed' | 'idle'> = {};
      
      if (event.event_type === 'node_started') {
        // Always set to running when node_started event arrives
        // If it was pending, it transitions to running
        updatedStatuses[nodeId] = 'running';
      } else if (event.event_type === 'node_completed') {
        // Get dependents BEFORE updating status
        const { edges } = useWorkflowStore.getState();
        const dependents = edges
          .filter(e => e.source === nodeId)
          .map(e => e.target);
        
        // Set dependents to pending immediately (only if they're not already running)
        dependents.forEach(depId => {
          const depStatus = state.nodeStatuses[depId];
          // Only set to pending if not already running or completed
          // This prevents overwriting a node that's already started
          if (!depStatus || depStatus === 'idle') {
            updatedStatuses[depId] = 'pending';
          }
        });
        
        // Set to completed immediately - animations will handle the visual feedback
        // IMPORTANT: Don't allow failed to overwrite completed (completed is final state)
        updatedStatuses[nodeId] = 'completed';
      } else if (event.event_type === 'node_failed') {
        // Only set to failed if node is not already completed
        // This prevents failed events from overwriting completed status
        const currentStatus = state.nodeStatuses[nodeId];
        if (currentStatus !== 'completed') {
          updatedStatuses[nodeId] = 'failed';
        }
        // If already completed, preserve completed status (don't overwrite)
      } else if (event.event_type === 'node_progress') {
        // Progress events always mean the node is running
        // Set to running regardless of current status (unless already completed/failed)
        const currentStatus = state.nodeStatuses[nodeId];
        if (currentStatus !== 'completed' && currentStatus !== 'failed') {
          updatedStatuses[nodeId] = 'running';
        } else {
          // Preserve completed/failed status
          updatedStatuses[nodeId] = currentStatus;
        }
      } else if (event.event_type === 'log' && event.progress !== undefined) {
        // Log events with progress data should be treated as progress updates
        // This handles cases where backend sends progress in log events
        const currentStatus = state.nodeStatuses[nodeId];
        if (currentStatus !== 'completed' && currentStatus !== 'failed') {
          updatedStatuses[nodeId] = 'running';
        } else {
          updatedStatuses[nodeId] = currentStatus;
        }
      } else {
        // For other event types (node_output, log without progress, etc.), preserve current status
        // But if status is idle and we get any event, assume it's running
        const currentStatus = state.nodeStatuses[nodeId];
        if (!currentStatus || currentStatus === 'idle') {
          // Any event for an idle node suggests it's running
          updatedStatuses[nodeId] = 'running';
        } else {
          updatedStatuses[nodeId] = currentStatus;
        }
      }

      return {
        nodeEvents: {
          ...state.nodeEvents,
          [nodeId]: [...(state.nodeEvents[nodeId] || []), event], // Keep ALL events for analytics
        },
        nodeStatuses: {
          ...state.nodeStatuses,
          ...updatedStatuses,
        },
      };
    }),

  setCurrentNode: (nodeId) =>
    set((state) => ({
      currentNodeId: nodeId,
      // Mark node as running when it becomes current
      // This ensures the node shows as running even if node_started event hasn't been processed yet
      nodeStatuses: nodeId ? {
        ...state.nodeStatuses,
        [nodeId]: 'running',
      } : state.nodeStatuses,
    })),

  updateNodeStatuses: (statuses) =>
    set((state) => ({
      nodeStatuses: {
        ...state.nodeStatuses,
        ...statuses,
      },
    })),

  clearExecution: () =>
    set({
      executionId: null,
      status: 'idle',
      results: {},
      trace: [],
      cost: 0,
      duration: 0,
      error: null,
      nodeEvents: {},
      currentNodeId: null,
      nodeStatuses: {},
    }),

  getExecutionStatus: async (executionId: string) => {
    const { getExecutionStatus: getStatus } = await import('@/services/executions');
    return getStatus(executionId);
  },

  getExecutionTrace: async (executionId: string) => {
    const { getExecutionTrace: getTrace } = await import('@/services/executions');
    return getTrace(executionId);
  },
}));

