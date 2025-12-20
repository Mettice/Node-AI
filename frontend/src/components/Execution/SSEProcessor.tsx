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
  const { executionId, addNodeEvent, setCurrentNode, updateNodeStatuses } = useExecutionStore();

  useEffect(() => {
    if (!executionId) {
      return;
    }

    // Track processed node_output events to prevent duplicates
    // Clear on new execution to avoid cross-execution conflicts
    const processedNodeOutputs = new Set<string>();

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
      // Event logging - ENABLED FOR DEBUGGING - Show ALL fields
      // Only log agent-related events to reduce noise
      if (event.event_type?.includes('agent') || event.event_type?.includes('task') || event.agent || event.task) {
        console.log('[SSEProcessor] Agent/Task event:', {
          event_type: event.event_type,
          node_id: event.node_id,
          agent: event.agent,
          task: event.task,
          message: event.message,
          data_thought: event.data?.thought,
          data_tool: event.data?.tool,
        });
      }
      
      // Handle workflow-level events (completion)
      if (event.node_id === 'workflow' && event.event_type === 'log') {
        const message = event.data?.message || '';
        if (message.toLowerCase().includes('completed') || message.toLowerCase().includes('failed')) {
          console.log('[SSEProcessor] Workflow completion detected:', message);
          const { updateStatus, updateNodeStatuses } = useExecutionStore.getState();
          // Update execution status to completed/failed
          if (message.toLowerCase().includes('completed')) {
            updateStatus('completed');
          } else if (message.toLowerCase().includes('failed')) {
            updateStatus('failed');
          }
          // Clear current node when workflow completes
          setCurrentNode(null);
          // Clear all node statuses to stop animations
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
        // Extract token information from event data (check multiple locations)
        const tokensUsed = event.data?.tokens_used || {};
        const inputTokens = event.data?.input_tokens || 
                          tokensUsed.input_tokens || 
                          tokensUsed.input ||
                          event.input_tokens || 
                          undefined;
        const outputTokens = event.data?.output_tokens || 
                           tokensUsed.output_tokens || 
                           tokensUsed.output ||
                           event.output_tokens || 
                           undefined;
        const totalTokens = event.data?.total_tokens || 
                          tokensUsed.total_tokens || 
                          tokensUsed.total ||
                          event.total_tokens || 
                          (inputTokens !== undefined && outputTokens !== undefined ? inputTokens + outputTokens : undefined);
        
        addNodeEvent(event.node_id, {
          event_type: event.event_type,
          message,
          timestamp: event.timestamp,
          // Progress can be at top level (new format) or in data (legacy)
          progress: event.progress ?? event.data?.progress,
          // Include agent and task info for Agent Room visualization
          agent: event.agent,
          task: event.task,
          // Include token information
          input_tokens: inputTokens,
          output_tokens: outputTokens,
          total_tokens: totalTokens,
          data: event.data,
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
          
          // If node completed and we have output data in the event, store it
          // Some nodes send output in the completion event rather than a separate node_output event
          if (event.event_type === 'node_completed' && event.data) {
            const { updateNodeResult } = useExecutionStore.getState();
            const outputData = event.data.output;
            
            // Always update result from completion event (it has the final state)
            // This ensures we have the output even if node_output event wasn't sent
            const nodeResult = {
              node_id: event.node_id,
              status: 'completed' as const,
              output: outputData || (currentState.results[event.node_id]?.output), // Preserve existing output if new one is missing
              error: undefined,
              cost: event.data.cost || currentState.results[event.node_id]?.cost || 0,
              duration_ms: event.data.duration_ms || currentState.results[event.node_id]?.duration_ms || 0,
            };
            
            console.log('[SSEProcessor] Storing node result from node_completed event:', {
              node_id: event.node_id,
              has_output: !!outputData,
              output_keys: outputData ? (typeof outputData === 'object' ? Object.keys(outputData) : ['string']) : [],
              output_type: typeof outputData,
            });
            
            updateNodeResult(event.node_id, nodeResult);
          }
        } else if (event.event_type === 'log' || event.event_type === 'node_output') {
          // Log and output events indicate the node is actively running
          // If we receive these events and the node isn't already current, set it as current
          // This handles cases where node_started might have been missed
          const nodeStatus = currentState.nodeStatuses[event.node_id];
          // If node has no status yet but we're receiving events, it's likely running
          if (!nodeStatus || nodeStatus === 'idle') {
            const { updateNodeStatuses: updateStatuses } = useExecutionStore.getState();
            updateStatuses({
              [event.node_id]: 'running',
            });
          }
          if (nodeStatus === 'running' || nodeStatus === 'pending' || !nodeStatus) {
            if (!currentState.currentNodeId || currentState.currentNodeId !== event.node_id) {
              setCurrentNode(event.node_id);
            }
          }
          
          // Handle node_output events - update the result in the store
          // Deduplicate: only process the first node_output event per node
          if (event.event_type === 'node_output' && event.data) {
            const eventKey = `${event.node_id}-${event.event_type}`;
            
            // Skip if we've already processed this node_output event
            if (processedNodeOutputs.has(eventKey)) {
              console.log('[SSEProcessor] Skipping duplicate node_output event:', event.node_id);
              return;
            }
            
            // Mark as processed
            processedNodeOutputs.add(eventKey);
            
            const { updateNodeResult, updateNodeStatuses: updateNodeStatusesFromStore } = useExecutionStore.getState();
            const outputData = event.data.output || event.data;
            const agentOutputs = event.data.agent_outputs;
            
            // Create a NodeResult from the event data
            const nodeResult = {
              node_id: event.node_id,
              status: 'completed' as const,
              output: {
                output: outputData,
                ...(agentOutputs && { agent_outputs: agentOutputs }),
                ...(event.data.agents && { agents: event.data.agents }),
                ...(event.data.tasks && { tasks: event.data.tasks }),
                ...(event.data.tokens_used && { tokens_used: event.data.tokens_used }),
                ...(event.data.per_agent_tokens && { per_agent_tokens: event.data.per_agent_tokens }),
              },
              cost: 0, // Will be updated from polling
              duration_ms: 0, // Will be updated from polling
            };
            
            console.log('[SSEProcessor] Updating node result from node_output event:', {
              node_id: event.node_id,
              has_agent_outputs: !!agentOutputs,
              agent_outputs_keys: agentOutputs ? Object.keys(agentOutputs) : [],
              output_keys: Object.keys(nodeResult.output || {}),
            });
            
            updateNodeResult(event.node_id, nodeResult);
            // Also update node status to completed
            updateNodeStatusesFromStore({
              [event.node_id]: 'completed',
            });
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

