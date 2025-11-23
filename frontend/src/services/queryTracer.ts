/**
 * Query Tracer Service
 * 
 * Provides functions to fetch and analyze RAG query traces.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface QueryTraceStep {
  step_type: string;
  node_id: string;
  node_type: string;
  timestamp: string;
  data: Record<string, any>;
  cost: number;
  duration_ms: number;
}

export interface QueryTrace {
  execution_id: string;
  query: string;
  workflow_id: string;
  started_at: string;
  completed_at: string | null;
  total_cost: number;
  total_duration_ms: number;
  steps: QueryTraceStep[];
}

export interface QueryTraceSummary {
  execution_id: string;
  query: string;
  workflow_id: string;
  started_at: string;
  completed_at: string | null;
  total_cost: number;
  total_duration_ms: number;
  chunks_retrieved: number;
  chunks_reranked: number;
  chunks_final: number;
  llm_tokens: Record<string, number>;
  has_reranking: boolean;
}

/**
 * Get a complete query trace by execution ID.
 */
export async function getTrace(executionId: string): Promise<QueryTrace> {
  const response = await axios.get<QueryTrace>(
    `${API_BASE_URL}/api/v1/traces/${executionId}`
  );
  return response.data;
}

/**
 * Get a summary of a query trace.
 */
export async function getTraceSummary(executionId: string): Promise<QueryTraceSummary> {
  const response = await axios.get<QueryTraceSummary>(
    `${API_BASE_URL}/api/v1/traces/${executionId}/summary`
  );
  return response.data;
}

/**
 * List query traces, optionally filtered by workflow.
 */
export async function listTraces(
  workflowId?: string,
  limit: number = 100
): Promise<{ traces: QueryTrace[]; count: number }> {
  const params = new URLSearchParams();
  if (workflowId) {
    params.append('workflow_id', workflowId);
  }
  params.append('limit', limit.toString());
  
  const response = await axios.get<{ traces: QueryTrace[]; count: number }>(
    `${API_BASE_URL}/api/v1/traces?${params.toString()}`
  );
  return response.data;
}

