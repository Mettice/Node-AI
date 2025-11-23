/**
 * Secrets Vault API client
 */

import { apiClient } from '@/utils/api';

export interface Secret {
  id: string;
  user_id: string;
  name: string;
  provider: string;
  secret_type: string;
  description?: string;
  tags: string[];
  is_active: boolean;
  last_used_at?: string;
  usage_count: number;
  expires_at?: string;
  created_at: string;
  updated_at: string;
  value?: string;
}

export interface SecretCreate {
  name: string;
  provider: string;
  secret_type: string;
  value: string;
  description?: string;
  tags?: string[];
  expires_at?: string;
}

export interface SecretUpdate {
  name?: string;
  value?: string;
  description?: string;
  tags?: string[];
  is_active?: boolean;
  expires_at?: string;
}

export const secretsApi = {
  list: async (params?: {
    provider?: string;
    secret_type?: string;
    is_active?: boolean;
  }): Promise<Secret[]> => {
    const response = await apiClient.get<Secret[]>('/secrets', { params });
    return response.data;
  },

  get: async (secretId: string, decrypt: boolean = false): Promise<Secret> => {
    const response = await apiClient.get<Secret>(`/secrets/${secretId}`, {
      params: { decrypt },
    });
    return response.data;
  },

  create: async (secret: SecretCreate): Promise<Secret> => {
    const response = await apiClient.post<Secret>('/secrets', secret);
    return response.data;
  },

  update: async (secretId: string, updates: SecretUpdate): Promise<Secret> => {
    const response = await apiClient.put<Secret>(`/secrets/${secretId}`, updates);
    return response.data;
  },

  delete: async (secretId: string): Promise<void> => {
    await apiClient.delete(`/secrets/${secretId}`);
  },
};
