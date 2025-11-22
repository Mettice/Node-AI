/**
 * API response type definitions
 */

export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface ExecutionResponse {
  execution_id: string;
  status: ExecutionStatus;
  started_at: string;
  completed_at?: string;
  total_cost: number;
  duration_ms: number;
  results?: Record<string, NodeResult>;  // Add results to ExecutionResponse
}

export interface NodeResult {
  node_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  output?: Record<string, any>;
  error?: string;
  cost?: number;
  duration_ms?: number;
}

export interface ExecutionStep {
  node_id: string;
  timestamp: string;
  action: string;  // "completed", "error", "started"
  data?: {
    status?: string;
    error?: string;
    [key: string]: any;
  };
}

export interface ExecutionTrace {
  execution_id: string;
  status: ExecutionStatus;
  trace: ExecutionStep[];  // Backend returns "trace", not "steps"
  total_cost: number;
  duration_ms: number;
}

