/**
 * Health check API service
 */

import { apiClient } from '@/utils/api';

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
}

