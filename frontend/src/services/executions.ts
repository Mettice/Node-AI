/**
 * Execution status and trace API services
 */

import { apiClient } from '@/utils/api';
import type { ExecutionResponse, ExecutionTrace } from '@/types/api';

/**
 * Get execution status
 */
export async function getExecutionStatus(executionId: string): Promise<ExecutionResponse> {
  const response = await apiClient.get<ExecutionResponse>(`/executions/${executionId}`);
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

