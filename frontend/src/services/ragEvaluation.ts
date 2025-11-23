/**
 * RAG Evaluation API services
 */

import { apiClient } from '@/utils/api';

export interface QAPair {
  question: string;
  expected_answer: string;
  context?: string;
}

export interface EvaluationRequest {
  workflow: any; // Workflow object
  test_dataset_id: string;
  max_queries?: number;
  input_node_id?: string;
  output_node_id?: string;
}

export interface EvaluationResult {
  question: string;
  expected_answer: string;
  actual_answer: string;
  is_correct: boolean;
  relevance_score: number;
  latency_ms: number;
  cost: number;
  execution_id?: string;
  error?: string;
}

export interface EvaluationSummary {
  evaluation_id: string;
  workflow_id: string;
  total_queries: number;
  correct_answers: number;
  accuracy: number;
  average_relevance: number;
  average_latency_ms: number;
  total_cost: number;
  cost_per_query: number;
  failed_queries: number;
  results: EvaluationResult[];
  created_at: string;
}

export interface TestDataset {
  dataset_id: string;
  pairs: QAPair[];
  num_pairs: number;
}

/**
 * Upload a test dataset (JSON or JSONL file)
 */
export async function uploadTestDataset(file: File): Promise<{ dataset_id: string; num_pairs: number }> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post<{ dataset_id: string; num_pairs: number; message: string }>(
    '/rag-eval/dataset',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}

/**
 * Get a test dataset
 */
export async function getTestDataset(datasetId: string): Promise<TestDataset> {
  const response = await apiClient.get<TestDataset>(`/rag-eval/dataset/${datasetId}`);
  return response.data;
}

/**
 * Evaluate a RAG workflow
 */
export async function evaluateRAGWorkflow(request: EvaluationRequest): Promise<EvaluationSummary> {
  const response = await apiClient.post<EvaluationSummary>('/rag-eval/evaluate', request);
  return response.data;
}

/**
 * Get evaluation results
 */
export async function getEvaluation(evaluationId: string): Promise<EvaluationSummary> {
  const response = await apiClient.get<EvaluationSummary>(`/rag-eval/${evaluationId}`);
  return response.data;
}

/**
 * List all evaluations
 */
export async function listEvaluations(workflowId?: string): Promise<EvaluationSummary[]> {
  const response = await apiClient.get<EvaluationSummary[]>('/rag-eval', {
    params: workflowId ? { workflow_id: workflowId } : {},
  });
  return response.data;
}

export interface ABTestRequest {
  workflow_a: any;
  workflow_b: any;
  test_dataset_id: string;
  max_queries?: number;
  input_node_id?: string;
  output_node_id?: string;
  test_name?: string;
}

export interface ABTestResult {
  test_id: string;
  test_name?: string;
  workflow_a_id: string;
  workflow_b_id: string;
  evaluation_a: EvaluationSummary;
  evaluation_b: EvaluationSummary;
  comparison: {
    accuracy_diff: number;
    relevance_diff: number;
    latency_diff_ms: number;
    cost_diff: number;
    cost_diff_pct: number;
  };
  winner?: 'a' | 'b' | 'tie';
  created_at: string;
}

/**
 * Run an A/B test comparing two workflow configurations
 */
export async function runABTest(request: ABTestRequest): Promise<ABTestResult> {
  const response = await apiClient.post<ABTestResult>('/rag-eval/ab-test', request);
  return response.data;
}

/**
 * List all A/B tests
 */
export async function listABTests(): Promise<ABTestResult[]> {
  const response = await apiClient.get<ABTestResult[]>('/rag-eval/ab-tests');
  return response.data;
}

export interface QualityTrends {
  workflow_id?: string;
  days: number;
  trends: Array<{
    date: string;
    avg_accuracy: number;
    avg_relevance: number;
    avg_latency_ms: number;
    avg_cost_per_query: number;
    evaluation_count: number;
  }>;
}

/**
 * Get quality trends over time
 */
export async function getQualityTrends(
  workflowId?: string,
  days: number = 30
): Promise<QualityTrends> {
  const response = await apiClient.get<QualityTrends>('/rag-eval/quality-trends', {
    params: {
      ...(workflowId ? { workflow_id: workflowId } : {}),
      days,
    },
  });
  return response.data;
}

