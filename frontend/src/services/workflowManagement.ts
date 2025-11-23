/**
 * Workflow management API services
 */

import { apiClient } from '@/utils/api';

export interface Workflow {
  id?: string;
  name: string;
  description?: string;
  nodes: Array<{
    id: string;
    type: string;
    position: { x: number; y: number };
    data: Record<string, any>;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    sourceHandle?: string;
    targetHandle?: string;
  }>;
  tags?: string[];
  is_template?: boolean;
  is_deployed?: boolean;
  created_at?: string;
  updated_at?: string;
  deployed_at?: string;
}

export interface WorkflowListItem {
  id: string;
  name: string;
  description?: string;
  tags: string[];
  is_template: boolean;
  is_deployed?: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkflowListResponse {
  workflows: WorkflowListItem[];
  total: number;
}

/**
 * Create a new workflow
 */
export async function createWorkflow(workflow: Omit<Workflow, 'id' | 'created_at' | 'updated_at'>): Promise<Workflow> {
  const response = await apiClient.post<Workflow>('/workflows', workflow);
  return response.data;
}

/**
 * Update an existing workflow
 */
export async function updateWorkflow(
  workflowId: string,
  updates: Partial<Omit<Workflow, 'id' | 'created_at' | 'updated_at'>>
): Promise<Workflow> {
  const response = await apiClient.put<Workflow>(`/workflows/${workflowId}`, updates);
  return response.data;
}

/**
 * Save a workflow (create if new, update if exists)
 */
export async function saveWorkflow(workflow: Workflow): Promise<Workflow> {
  if (workflow.id) {
    // Update existing workflow
    return updateWorkflow(workflow.id, {
      name: workflow.name,
      description: workflow.description,
      nodes: workflow.nodes,
      edges: workflow.edges,
      tags: workflow.tags,
      is_template: workflow.is_template,
    });
  } else {
    // Create new workflow
    return createWorkflow({
      name: workflow.name,
      description: workflow.description,
      nodes: workflow.nodes,
      edges: workflow.edges,
      tags: workflow.tags,
      is_template: workflow.is_template,
    });
  }
}

/**
 * Get a workflow by ID
 */
export async function getWorkflow(workflowId: string): Promise<Workflow> {
  const response = await apiClient.get<Workflow>(`/workflows/${workflowId}`);
  return response.data;
}

/**
 * List all workflows
 */
export async function listWorkflows(options?: {
  limit?: number;
  offset?: number;
  is_template?: boolean;
}): Promise<WorkflowListResponse> {
  const params = new URLSearchParams();
  if (options?.limit) params.append('limit', options.limit.toString());
  if (options?.offset) params.append('offset', options.offset.toString());
  if (options?.is_template !== undefined) params.append('is_template', options.is_template.toString());
  
  const queryString = params.toString();
  const url = `/workflows${queryString ? `?${queryString}` : ''}`;
  
  const response = await apiClient.get<WorkflowListResponse>(url);
  return response.data;
}

/**
 * Delete a workflow
 */
export async function deleteWorkflow(workflowId: string): Promise<void> {
  await apiClient.delete(`/workflows/${workflowId}`);
}

/**
 * Deploy a workflow (make it available for queries)
 */
export async function deployWorkflow(workflowId: string): Promise<Workflow> {
  const response = await apiClient.post<Workflow>(`/workflows/${workflowId}/deploy`);
  return response.data;
}

/**
 * Undeploy a workflow (make it unavailable for queries)
 */
export async function undeployWorkflow(workflowId: string): Promise<Workflow> {
  const response = await apiClient.post<Workflow>(`/workflows/${workflowId}/undeploy`);
  return response.data;
}

/**
 * Query a deployed workflow
 */
export interface WorkflowQueryRequest {
  input: Record<string, any>;
}

export interface WorkflowQueryResponse {
  execution_id: string;
  status: string;
  started_at: string;
  completed_at?: string;
  total_cost: number;
  duration_ms: number;
  results: Record<string, any>;
}

export async function queryWorkflow(
  workflowId: string,
  request: WorkflowQueryRequest
): Promise<WorkflowQueryResponse> {
  const response = await apiClient.post<WorkflowQueryResponse>(
    `/workflows/${workflowId}/query`,
    request
  );
  return response.data;
}

