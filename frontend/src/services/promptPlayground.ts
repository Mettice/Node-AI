/**
 * Prompt Playground API services
 */

import { apiClient } from '@/utils/api';

export interface PromptTestRequest {
  prompt: string;
  provider?: string;
  model?: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
  test_inputs?: string[];
}

export interface PromptTestResult {
  test_id: string;
  prompt: string;
  provider: string;
  model: string;
  input_text: string;
  output: string;
  tokens_used: {
    input: number;
    output: number;
    total: number;
  };
  cost: number;
  latency_ms: number;
  created_at: string;
}

export interface ABTestRequest {
  prompt_a: string;
  prompt_b: string;
  provider?: string;
  model?: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
  test_inputs: string[];
}

export interface ABTestResult {
  test_id: string;
  prompt_a_result: PromptTestResult;
  prompt_b_result: PromptTestResult;
  winner?: 'a' | 'b' | null;
  comparison_metrics: {
    avg_cost_a: number;
    avg_cost_b: number;
    avg_latency_a: number;
    avg_latency_b: number;
    cost_savings: number;
    latency_diff: number;
  };
  created_at: string;
}

export interface PromptVersion {
  version_id: string;
  prompt: string;
  system_prompt?: string;
  provider: string;
  model: string;
  temperature: number;
  max_tokens?: number;
  test_results: PromptTestResult[];
  average_cost: number;
  average_latency_ms: number;
  created_at: string;
  notes?: string;
}

/**
 * Test a prompt
 */
export async function testPrompt(request: PromptTestRequest): Promise<PromptTestResult> {
  const response = await apiClient.post<PromptTestResult>('/prompt/test', request);
  return response.data;
}

/**
 * Test a prompt with multiple inputs (batch)
 */
export async function testPromptBatch(request: PromptTestRequest): Promise<PromptTestResult[]> {
  const response = await apiClient.post<PromptTestResult[]>('/prompt/test/batch', request);
  return response.data;
}

/**
 * Run A/B test between two prompts
 */
export async function abTestPrompts(request: ABTestRequest): Promise<ABTestResult> {
  const response = await apiClient.post<ABTestResult>('/prompt/ab-test', request);
  return response.data;
}

/**
 * Create a prompt version
 */
export async function createPromptVersion(params: {
  prompt: string;
  provider: string;
  model: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
  notes?: string;
}): Promise<{ version_id: string; message: string }> {
  const response = await apiClient.post<{ version_id: string; message: string }>(
    '/prompt/version',
    params
  );
  return response.data;
}

/**
 * List all prompt versions
 */
export async function listPromptVersions(): Promise<PromptVersion[]> {
  const response = await apiClient.get<PromptVersion[]>('/prompt/versions');
  return response.data;
}

/**
 * Get a specific prompt test result
 */
export async function getPromptTest(testId: string): Promise<PromptTestResult> {
  const response = await apiClient.get<PromptTestResult>(`/prompt/test/${testId}`);
  return response.data;
}

/**
 * Get available base models from pricing system
 */
export interface BaseModel {
  model_id: string;
  description: string;
  max_tokens?: number;
  pricing: {
    input_per_1k?: number;
    output_per_1k?: number;
    cached_input_per_1k?: number;
    per_1k_tokens?: number;
    batch_per_1k_tokens?: number;
    per_1k_units?: number;
  };
}

export interface BaseModelsResponse {
  provider: string;
  model_type: string;
  models: BaseModel[];
}

export async function getBaseModels(
  provider: string,
  modelType: 'llm' | 'embedding' | 'reranking' = 'llm'
): Promise<BaseModelsResponse> {
  const response = await apiClient.get<BaseModelsResponse>(`/models/base/${provider}`, {
    params: { model_type: modelType },
  });
  return response.data;
}

