/**
 * Observability Settings API client
 */

import { apiClient } from '@/utils/api';

export interface ObservabilitySettings {
  langsmith_api_key?: string | null;
  langsmith_project?: string;
  langfuse_public_key?: string | null;
  langfuse_secret_key?: string | null;
  langfuse_host?: string;
  enabled: boolean;
}

export interface ObservabilitySettingsUpdate {
  langsmith_api_key?: string | null;
  langsmith_project?: string;
  langfuse_public_key?: string | null;
  langfuse_secret_key?: string | null;
  langfuse_host?: string;
  enabled?: boolean;
}

export const observabilityApi = {
  get: async (): Promise<ObservabilitySettings> => {
    const response = await apiClient.get<ObservabilitySettings>('/observability/settings');
    return response.data;
  },

  update: async (settings: ObservabilitySettingsUpdate): Promise<ObservabilitySettings> => {
    const response = await apiClient.put<ObservabilitySettings>('/observability/settings', settings);
    return response.data;
  },
};

