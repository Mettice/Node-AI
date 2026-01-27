/**
 * Fine-tuning API services
 */

import { apiClient } from '@/utils/api';

export interface FineTuneJobStatus {
  job_id: string;
  status: 'validating_training_file' | 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  progress?: number; // 0.0 to 1.0
  model_id?: string;
  error?: string;
  training_file_id?: string;
  validation_file_id?: string;
  created_at: string;
  updated_at: string;
  estimated_cost?: number;
  actual_cost?: number;
  training_examples?: number;
  validation_examples?: number;
  epochs?: number;
  base_model?: string;
  provider?: string;
}

/**
 * Get status of a fine-tuning job
 */
export async function getFinetuneStatus(jobId: string): Promise<FineTuneJobStatus> {
  const response = await apiClient.get<FineTuneJobStatus>(`/finetune/${jobId}/status`);
  return response.data;
}

/**
 * List all fine-tuning jobs
 */
export async function listFinetuneJobs(params?: {
  status?: string;
  provider?: string;
}): Promise<FineTuneJobStatus[]> {
  const response = await apiClient.get<FineTuneJobStatus[]>('/finetune/jobs', { params });
  return response.data;
}

/**
 * Register a fine-tuned model in the model registry
 */
export async function registerFinetunedModel(jobId: string): Promise<{ success: boolean; message: string; model_id: string }> {
  const response = await apiClient.post<{ success: boolean; message: string; model_id: string }>(`/finetune/${jobId}/register-model`);
  return response.data;
}
