/**
 * Deployment management API services
 */

import { apiClient } from '@/utils/api';

export interface DeploymentVersion {
  id: string;
  workflow_id: string;
  version_number: number;
  deployed_at: string;
  workflow_snapshot: Record<string, any>;
  status: 'active' | 'inactive' | 'rolled_back' | 'failed';
  deployed_by?: string;
  description?: string;
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  avg_response_time_ms?: number;
  total_cost: number;
  rolled_back_at?: string;
  rolled_back_to_version?: number;
}

export interface DeploymentListResponse {
  workflow_id: string;
  versions: DeploymentVersion[];
  total: number;
}

export interface DeploymentHealth {
  status: string;
  healthy: boolean;
  version_number?: number;
  deployed_at?: string;
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  success_rate: number;
  avg_response_time_ms?: number;
  total_cost: number;
}

/**
 * List all deployment versions for a workflow
 */
export async function listDeploymentVersions(workflowId: string): Promise<DeploymentListResponse> {
  const response = await apiClient.get<DeploymentListResponse>(`/workflows/${workflowId}/deployments`);
  return response.data;
}

/**
 * Get a specific deployment version
 */
export async function getDeploymentVersion(workflowId: string, versionNumber: number): Promise<DeploymentVersion> {
  const response = await apiClient.get<DeploymentVersion>(`/workflows/${workflowId}/deployments/${versionNumber}`);
  return response.data;
}

/**
 * Rollback to a previous deployment version
 */
export async function rollbackDeployment(workflowId: string, versionNumber: number): Promise<{
  message: string;
  deployment: DeploymentVersion;
  workflow: Record<string, any>;
}> {
  const response = await apiClient.post(`/workflows/${workflowId}/deployments/${versionNumber}/rollback`);
  return response.data;
}

/**
 * Get deployment health metrics
 */
export async function getDeploymentHealth(workflowId: string): Promise<DeploymentHealth> {
  const response = await apiClient.get<DeploymentHealth>(`/workflows/${workflowId}/deployments/health`);
  return response.data;
}

