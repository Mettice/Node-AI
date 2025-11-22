/**
 * RAG Optimization API services
 */

import { apiClient } from '@/utils/api';

export interface OptimizationSuggestion {
  node_id: string;
  node_type: string;
  parameter: string;
  current_value: any;
  suggested_value: any;
  expected_improvement: string;
  reasoning: string;
  confidence: number;
}

export interface RAGOptimizationAnalysis {
  analysis_id: string;
  workflow_id: string;
  execution_id?: string;
  suggestions: OptimizationSuggestion[];
  current_metrics: Record<string, any>;
  created_at: string;
}

export interface OptimizationRequest {
  workflow: any;
  execution_id?: string;
  evaluation_id?: string;
}

/**
 * Analyze and optimize a RAG workflow
 */
export async function analyzeRAGWorkflow(request: OptimizationRequest): Promise<RAGOptimizationAnalysis> {
  const response = await apiClient.post<RAGOptimizationAnalysis>('/rag-optimize/analyze', request);
  return response.data;
}

/**
 * Get optimization analysis results
 */
export async function getOptimizationAnalysis(analysisId: string): Promise<RAGOptimizationAnalysis> {
  const response = await apiClient.get<RAGOptimizationAnalysis>(`/rag-optimize/${analysisId}`);
  return response.data;
}

