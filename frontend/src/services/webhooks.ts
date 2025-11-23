/**
 * Webhooks API services
 */

import { apiClient } from '@/utils/api';

export interface Webhook {
  id: string;
  workflow_id: string;
  name?: string;
  webhook_id: string;
  webhook_url: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  last_called_at?: string;
}

export interface CreateWebhookRequest {
  workflow_id: string;
  name?: string;
  secret?: string;
  method?: string;
  headers_required?: Record<string, string>;
  payload_mapping?: Record<string, string>;
}

export interface UpdateWebhookRequest {
  name?: string;
  enabled?: boolean;
  secret?: string;
  method?: string;
  headers_required?: Record<string, string>;
  payload_mapping?: Record<string, string>;
}

/**
 * Create a webhook for a workflow
 */
export async function createWebhook(
  request: CreateWebhookRequest,
  baseUrl?: string
): Promise<Webhook> {
  const headers: Record<string, string> = {};
  if (baseUrl) {
    headers['X-Base-URL'] = baseUrl;
  }
  
  const response = await apiClient.post<Webhook>('/webhooks', request, { headers });
  return response.data;
}

/**
 * List all webhooks
 */
export async function listWebhooks(workflowId?: string, baseUrl?: string): Promise<Webhook[]> {
  const headers: Record<string, string> = {};
  if (baseUrl) {
    headers['X-Base-URL'] = baseUrl;
  }
  
  const params = workflowId ? { workflow_id: workflowId } : {};
  const response = await apiClient.get<Webhook[]>('/webhooks', { params, headers });
  return response.data;
}

/**
 * Get a webhook by ID
 */
export async function getWebhook(webhookId: string, baseUrl?: string): Promise<Webhook> {
  const headers: Record<string, string> = {};
  if (baseUrl) {
    headers['X-Base-URL'] = baseUrl;
  }
  
  const response = await apiClient.get<Webhook>(`/webhooks/${webhookId}`, { headers });
  return response.data;
}

/**
 * Update a webhook
 */
export async function updateWebhook(
  webhookId: string,
  request: UpdateWebhookRequest,
  baseUrl?: string
): Promise<Webhook> {
  const headers: Record<string, string> = {};
  if (baseUrl) {
    headers['X-Base-URL'] = baseUrl;
  }
  
  const response = await apiClient.put<Webhook>(`/webhooks/${webhookId}`, request, { headers });
  return response.data;
}

/**
 * Delete a webhook
 */
export async function deleteWebhook(webhookId: string): Promise<void> {
  await apiClient.delete(`/webhooks/${webhookId}`);
}

/**
 * Get all webhooks for a workflow
 */
export async function getWorkflowWebhooks(
  workflowId: string,
  baseUrl?: string
): Promise<Webhook[]> {
  const headers: Record<string, string> = {};
  if (baseUrl) {
    headers['X-Base-URL'] = baseUrl;
  }
  
  const response = await apiClient.get<Webhook[]>(`/workflows/${workflowId}/webhooks`, { headers });
  return response.data;
}

