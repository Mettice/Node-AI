/**
 * API Key Management Service
 */

import { apiClient } from '@/utils/api';

export interface APIKey {
  key_id: string;
  workflow_id: string | null;
  name: string;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
  rate_limit: number | null;
  cost_limit: number | null;
}

export interface APIKeyCreateRequest {
  workflow_id?: string;
  name: string;
  rate_limit?: number;
  cost_limit?: number;
}

export interface APIKeyCreateResponse {
  api_key: string; // Only shown once!
  key_id: string;
  workflow_id: string | null;
  name: string;
  created_at: string;
  rate_limit: number | null;
  cost_limit: number | null;
  message: string;
}

export interface APIKeyUpdateRequest {
  name?: string;
  is_active?: boolean;
  rate_limit?: number;
  cost_limit?: number;
}

export interface UsageStats {
  key_id: string;
  total_requests: number;
  total_cost: number;
  last_used_at: string | null;
  requests_today: number;
  cost_today: number;
}

/**
 * Create a new API key
 */
export async function createAPIKey(request: APIKeyCreateRequest): Promise<APIKeyCreateResponse> {
  const response = await apiClient.post<APIKeyCreateResponse>('/api-keys', request);
  return response.data;
}

/**
 * List all API keys
 */
export async function listAPIKeys(workflowId?: string): Promise<APIKey[]> {
  const params = workflowId ? { workflow_id: workflowId } : {};
  const response = await apiClient.get<APIKey[]>('/api-keys', { params });
  return response.data;
}

/**
 * Get an API key by ID
 */
export async function getAPIKey(keyId: string): Promise<APIKey> {
  const response = await apiClient.get<APIKey>(`/api-keys/${keyId}`);
  return response.data;
}

/**
 * Update an API key
 */
export async function updateAPIKey(keyId: string, request: APIKeyUpdateRequest): Promise<APIKey> {
  const response = await apiClient.put<APIKey>(`/api-keys/${keyId}`, request);
  return response.data;
}

/**
 * Delete an API key
 */
export async function deleteAPIKey(keyId: string): Promise<void> {
  await apiClient.delete(`/api-keys/${keyId}`);
}

/**
 * Get usage statistics for an API key
 */
export async function getAPIKeyUsage(keyId: string): Promise<UsageStats> {
  const response = await apiClient.get<UsageStats>(`/api-keys/${keyId}/usage`);
  return response.data;
}

