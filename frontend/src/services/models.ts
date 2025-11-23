/**
 * Model Registry API services
 */

import { apiClient } from '@/utils/api';

export interface FineTunedModel {
  id: string;
  job_id: string;
  model_id: string;
  name: string;
  description?: string;
  base_model: string;
  provider: string;
  status: 'training' | 'ready' | 'failed' | 'deleted';
  training_examples: number;
  validation_examples?: number;
  epochs: number;
  training_file_id?: string;
  validation_file_id?: string;
  estimated_cost?: number;
  actual_cost?: number;
  usage_count: number;
  last_used_at?: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

export interface ModelUsage {
  id: string;
  model_id: string;
  used_at: string;
  node_type?: string;
  execution_id?: string;
  tokens_used?: number;
  cost?: number;
}

export interface CreateModelRequest {
  job_id: string;
  model_id: string;
  name: string;
  description?: string;
  base_model: string;
  provider: string;
  training_examples: number;
  validation_examples?: number;
  epochs: number;
  training_file_id?: string;
  validation_file_id?: string;
  estimated_cost?: number;
  actual_cost?: number;
  metadata?: Record<string, any>;
}

export interface UpdateModelRequest {
  name?: string;
  description?: string;
  metadata?: Record<string, any>;
}

/**
 * List all fine-tuned models
 */
export async function listModels(params?: {
  status?: string;
  provider?: string;
  base_model?: string;
  sort_by?: string;
  order?: 'asc' | 'desc';
}): Promise<FineTunedModel[]> {
  const response = await apiClient.get<FineTunedModel[]>('/models', { params });
  return response.data;
}

/**
 * Get a specific model
 */
export async function getModel(modelId: string): Promise<FineTunedModel> {
  const response = await apiClient.get<FineTunedModel>(`/models/${modelId}`);
  return response.data;
}

/**
 * Create/register a new model
 */
export async function createModel(request: CreateModelRequest): Promise<FineTunedModel> {
  const response = await apiClient.post<FineTunedModel>('/models', request);
  return response.data;
}

/**
 * Update model metadata
 */
export async function updateModel(
  modelId: string,
  request: UpdateModelRequest
): Promise<FineTunedModel> {
  const response = await apiClient.patch<FineTunedModel>(`/models/${modelId}`, request);
  return response.data;
}

/**
 * Delete a model
 */
export async function deleteModel(
  modelId: string,
  deleteFromProvider = false
): Promise<{ message: string; model_id: string }> {
  const response = await apiClient.delete<{ message: string; model_id: string }>(
    `/models/${modelId}`,
    { params: { delete_from_provider: deleteFromProvider } }
  );
  return response.data;
}

/**
 * Record model usage
 */
export async function recordModelUsage(
  modelId: string,
  params?: {
    node_type?: string;
    execution_id?: string;
    tokens_used?: number;
    cost?: number;
  }
): Promise<{ message: string; model_id: string }> {
  const response = await apiClient.post<{ message: string; model_id: string }>(
    `/models/${modelId}/usage`,
    params
  );
  return response.data;
}

/**
 * Get model usage history
 */
export async function getModelUsage(
  modelId: string,
  limit = 50
): Promise<ModelUsage[]> {
  const response = await apiClient.get<ModelUsage[]>(`/models/${modelId}/usage`, {
    params: { limit },
  });
  return response.data;
}

/**
 * Get available fine-tuned models for a provider
 */
export async function getAvailableModels(
  provider: string,
  status = 'ready'
): Promise<FineTunedModel[]> {
  const response = await apiClient.get<FineTunedModel[]>(`/models/available/${provider}`, {
    params: { status },
  });
  return response.data;
}

