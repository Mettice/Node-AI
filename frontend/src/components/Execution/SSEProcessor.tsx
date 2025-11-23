/**
 * Background SSE Processor - Processes SSE events even when sidebar is closed
 * This ensures node animations and status updates work during execution
 */

import { useEffect } from 'react';
import { useExecutionStore } from '@/store/executionStore';
import { useWorkflowStore } from '@/store/workflowStore';
import { streamClient } from '@/services/streaming';
import type { StreamEvent } from '@/services/streaming';

export function SSEProcessor() {
  const { executionId, addNodeEvent, setCurrentNode } = useExecutionStore();

  useEffect(() => {
    if (!executionId) {
      return;
    }

    // Connect to stream
    streamClient.connect(executionId);

    // Format event message helper
    const formatEventMessage = (event: StreamEvent): string => {
      const { event_type, data, agent, task } = event;

      switch (event_type) {
        case 'node_started':
          return data.message || `Starting...`;
        case 'node_completed':
          return data.message || `Completed`;
        case 'node_failed':
          return data.message || `Failed`;
        case 'node_progress':
          // Progress can be at top level or in data
          const progressValue = event.progress ?? data.progress ?? 0;
          const progress = Math.round(progressValue * 100);
          return event.message || data.message || `Progress: ${progress}%`;
        case 'agent_started':
          return `🤖 ${agent || 'Agent'} started`;
        case 'agent_thinking':
          return `💭 ${agent || 'Agent'} thinking...`;
        case 'agent_tool_called':
          return `🔧 ${agent || 'Agent'} using tool: ${data.tool || 'unknown'}`;
        case 'agent_output':
          return `✍️ ${agent || 'Agent'} output`;
        case 'agent_completed':
          return `✅ ${agent || 'Agent'} completed`;
        case 'task_started':
          return `📋 Task: ${task || data.task || 'unknown'}`;
        case 'task_completed':
          return `✅ Task completed: ${task || data.task || 'unknown'}`;
        case 'log':
          return data.message || 'Log message';
        case 'error':
          return `❌ Error: ${data.message || 'Unknown error'}`;
        default:
          return data.message || `${event_type}`;
      }
    };

    // Subscribe to events
    const unsubscribe = streamClient.subscribe((event: StreamEvent) => {
      // Event logging - ENABLED FOR DEBUGGING
      console.log('[SSEProcessor] Received event:', {
        event_type: event.event_type,
        node_id: event.node_id,
        progress: event.progress,
        message: event.message,
        data_progress: event.data?.progress,
        data_message: event.data?.message,
      });
      
      // Handle workflow-level events (completion)
      if (event.node_id === 'workflow' && event.event_type === 'log') {
        const message = event.data?.message || '';
        if (message.toLowerCase().includes('completed') || message.toLowerCase().includes('failed')) {
          console.log('[SSEProcessor] Workflow completion detected:', message);
          // Clear current node when workflow completes
          setCurrentNode(null);
          // Clear all node statuses to stop animations
          const { updateNodeStatuses } = useExecutionStore.getState();
          const { nodes } = useWorkflowStore.getState();
          const allNodeIds = (nodes || []).map(n => n.id);
          const completedStatuses: Record<string, 'completed'> = {};
          allNodeIds.forEach(nodeId => {
            completedStatuses[nodeId] = 'completed';
          });
          // Update all nodes to completed status to stop animations
          updateNodeStatuses(completedStatuses);
        }
      }
      
      // Update execution store with node events
      // Process ALL events that have a node_id (including node_progress, node_output, etc.)
      if (event.node_id && event.node_id !== 'workflow') {
        
        // Add event to node's event list FIRST - this updates node statuses
        // This ensures the status is set before we update currentNodeId
        const message = formatEventMessage(event);
        addNodeEvent(event.node_id, {
          event_type: event.event_type,
          message,
          timestamp: event.timestamp,
          // Progress can be at top level (new format) or in data (legacy)
          progress: event.progress ?? event.data?.progress,
        });

        // Update current node AFTER adding the event
        // This ensures status is already set to 'running' when we set currentNodeId
        const currentState = useExecutionStore.getState();
        
        if (event.event_type === 'node_started') {
          setCurrentNode(event.node_id);
        } else if (event.event_type === 'node_progress') {
          // Progress events also indicate the node is running
          // Make sure it's set as current if it's not already
          if (!currentState.currentNodeId || currentState.currentNodeId !== event.node_id) {
            setCurrentNode(event.node_id);
          }
        } else if (event.event_type === 'node_completed' || event.event_type === 'node_failed') {
          // Clear current node if this node completed
          if (currentState.currentNodeId === event.node_id) {
            setCurrentNode(null);
          }
        } else if (event.event_type === 'log' || event.event_type === 'node_output') {
          // Log and output events indicate the node is actively running
          // If we receive these events and the node isn't already current, set it as current
          // This handles cases where node_started might have been missed
          const nodeStatus = currentState.nodeStatuses[event.node_id];
          if (nodeStatus === 'running' || nodeStatus === 'pending') {
            if (!currentState.currentNodeId || currentState.currentNodeId !== event.node_id) {
              setCurrentNode(event.node_id);
            }
          }
        }
      }
    });

    // Cleanup on unmount
    return () => {
      unsubscribe();
      streamClient.disconnect();
    };
  }, [executionId, addNodeEvent, setCurrentNode]);

  // This component doesn't render anything
  return null;
}

