/**
 * Execution status and trace API services
 */

import { apiClient } from '@/utils/api';
import type { ExecutionResponse, ExecutionTrace } from '@/types/api';

/**
 * Get execution status
 */
export async function getExecutionStatus(executionId: string): Promise<ExecutionResponse> {
  // Use longer timeout for execution status polling (60 seconds)
  // Workflows can take time, especially CrewAI agents
  const response = await apiClient.get<ExecutionResponse>(`/executions/${executionId}`, {
    timeout: 60000, // 60 seconds - longer timeout for status polling
  });
  return response.data;
}

/**
 * Get execution trace (detailed steps)
 */
export async function getExecutionTrace(executionId: string): Promise<ExecutionTrace> {
  const response = await apiClient.get<ExecutionTrace>(`/executions/${executionId}/trace`);
  return response.data;
}

/**
 * List all executions (optional)
 */
export async function listExecutions(): Promise<ExecutionResponse[]> {
  const response = await apiClient.get<ExecutionResponse[]>('/executions');
  return response.data;
}

