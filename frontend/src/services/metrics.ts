/**
 * Metrics API services
 */

import { apiClient } from '@/utils/api';

export interface ExecutionRecord {
  execution_id: string;
  workflow_id: string;
  workflow_version?: string;
  status: string;
  started_at: string;
  completed_at?: string;
  duration_ms: number;
  total_cost: number;
  cost_breakdown: Record<string, number>;
  error?: string;
  metadata: Record<string, any>;
}

export interface MetricsResponse {
  workflow_id: string;
  time_range: string;
  total_queries: number;
  success_rate: number;
  avg_response_time_ms: number;
  total_cost: number;
  cost_per_query: number;
  cost_breakdown: Record<string, number>;
  quality_metrics: {
    avg_relevance_score?: number;
    failed_queries: number;
    failure_rate: number;
    error_breakdown: Record<string, number>;
  };
  alerts: Array<{
    type: string;
    message: string;
  }>;
  performance_trends: Array<{
    timestamp: string;
    avg_response_time_ms: number;
    query_count: number;
    total_cost: number;
  }>;
}

export interface VersionComparison {
  current_version: string;
  previous_version?: string;
  current_metrics: {
    total_queries: number;
    success_rate: number;
    avg_response_time_ms: number;
    total_cost: number;
    cost_per_query: number;
  };
  previous_metrics?: {
    total_queries: number;
    success_rate: number;
    avg_response_time_ms: number;
    total_cost: number;
    cost_per_query: number;
  };
  comparison: {
    response_time_change_pct?: number;
    cost_change_pct?: number;
    success_rate_change_pct?: number;
  };
}

/**
 * Get metrics for a workflow
 */
export async function getWorkflowMetrics(
  workflowId: string,
  hours: number = 24
): Promise<MetricsResponse> {
  const response = await apiClient.get<MetricsResponse>(
    `/workflows/${workflowId}/metrics`,
    { params: { hours } }
  );
  return response.data;
}

/**
 * Compare workflow versions
 */
export async function compareWorkflowVersions(
  workflowId: string,
  currentVersion: string,
  previousVersion?: string,
  hours: number = 24
): Promise<VersionComparison> {
  const params: any = { current_version: currentVersion, hours };
  if (previousVersion) {
    params.previous_version = previousVersion;
  }
  
  const response = await apiClient.get<VersionComparison>(
    `/workflows/${workflowId}/versions/compare`,
    { params }
  );
  return response.data;
}

/**
 * Record an execution for metrics tracking
 */
export async function recordExecution(
  executionId: string,
  execution: any,
  workflowVersion?: string,
  costBreakdown?: Record<string, number>,
  metadata?: Record<string, any>
): Promise<void> {
  await apiClient.post(`/executions/${executionId}/record`, {
    execution,
    workflow_version: workflowVersion,
    cost_breakdown: costBreakdown,
    metadata,
  });
}

