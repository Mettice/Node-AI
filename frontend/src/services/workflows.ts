/**
 * Workflow execution API services
 */

import { apiClient, apiCall } from '@/utils/api';
import type { ExecutionResponse } from '@/types/api';

interface WorkflowPayload {
  name: string;
  nodes: Array<{
    id: string;
    type: string;
    position: { x: number; y: number };
    data: Record<string, any>;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    sourceHandle?: string;
    targetHandle?: string;
  }>;
}

/**
 * Execute a workflow with enhanced error handling and retry logic
 */
export async function executeWorkflow(workflow: WorkflowPayload): Promise<ExecutionResponse> {
  return apiCall(
    async () => {
      // Wrap workflow in ExecutionRequest format expected by backend
      const payload = {
        workflow: workflow,
        async_execution: false,
      };
      
      // Use longer timeout for workflow execution (120 seconds)
      // Workflows can take time, especially with large documents
      const response = await apiClient.post<ExecutionResponse>('/workflows/execute', payload, {
        timeout: 120000, // 120 seconds
      });
      
      return response.data;
    },
    {
      retries: 2, // Retry up to 2 times for rate limits or server errors
      retryDelay: 2000, // 2 second delay between retries
      onError: (error) => {
        // Log workflow execution errors with context
        console.error('Workflow execution failed:', {
          workflowName: workflow.name,
          nodeCount: workflow.nodes.length,
          error: error
        });
      }
    }
  );
}

