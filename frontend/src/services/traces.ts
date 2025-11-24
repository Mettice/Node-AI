/**
 * Traces API client
 */

import { apiClient } from '@/utils/api';

export interface TraceListItem {
  trace_id: string;
  workflow_id: string;
  execution_id: string;
  query?: string;
  started_at: string;
  completed_at?: string;
  status: string;
  total_cost: number;
  total_tokens: {
    input?: number;
    output?: number;
    total?: number;
  };
  total_duration_ms: number;
  span_count: number;
}

export interface TraceSpan {
  span_id: string;
  trace_id: string;
  span_type: string;
  name: string;
  parent_span_id?: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  duration_ms: number;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  tokens: Record<string, number>;
  cost: number;
  model?: string;
  provider?: string;
  error?: string;
  error_type?: string;
  evaluation?: Record<string, any>;
  metadata: Record<string, any>;
}

export interface TraceDetail {
  trace_id: string;
  workflow_id: string;
  execution_id: string;
  query?: string;
  started_at: string;
  completed_at?: string;
  status: string;
  error?: string;
  total_cost: number;
  total_tokens: {
    input?: number;
    output?: number;
    total?: number;
  };
  total_duration_ms: number;
  spans: TraceSpan[];
  span_count: number;
}

export const tracesApi = {
  list: async (params?: {
    workflow_id?: string;
    limit?: number;
    status?: string;
  }): Promise<TraceListItem[]> => {
    const response = await apiClient.get<TraceListItem[]>('/traces', { params });
    return response.data;
  },

  get: async (traceId: string): Promise<TraceDetail> => {
    const response = await apiClient.get<TraceDetail>(`/traces/${traceId}`);
    return response.data;
  },

  getWorkflowTraces: async (workflowId: string, limit: number = 100): Promise<TraceListItem[]> => {
    const response = await apiClient.get<TraceListItem[]>(`/workflows/${workflowId}/traces`, {
      params: { limit },
    });
    return response.data;
  },
};

