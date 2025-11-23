/**
 * Knowledge Base API services
 */

import { apiClient } from '@/utils/api';

export interface ChunkConfig {
  strategy: string;
  chunk_size: number;
  chunk_overlap: number;
  separators: string[];
  min_chunk_size: number;
  max_chunk_size: number;
  overlap_sentences: number;
}

export interface EmbedConfig {
  provider: string;
  model: string;
  dimensions?: number;
  batch_size: number;
  use_finetuned_model: boolean;
  finetuned_model_id?: string;
}

export interface VectorStoreConfig {
  provider: string;
  index_type: string;
  persist: boolean;
  file_path?: string;
}

export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'deprecated';

export interface KnowledgeBaseVersion {
  id: string;
  kb_id: string;
  version_number: number;
  created_at: string;
  file_ids: string[];
  chunk_config: ChunkConfig;
  embed_config: EmbedConfig;
  vector_store_config: VectorStoreConfig;
  vector_store_id: string;
  vector_store_path?: string;
  vector_count: number;
  status: ProcessingStatus;
  processing_log?: string;
  processing_duration_ms?: number;
  total_cost: number;
  created_by?: string;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  current_version: number;
  default_chunk_config: ChunkConfig;
  default_embed_config: EmbedConfig;
  default_vector_store_config: VectorStoreConfig;
  tags: string[];
  is_shared: boolean;
  versions: KnowledgeBaseVersion[];
}

export interface KnowledgeBaseListItem {
  id: string;
  name: string;
  description?: string;
  current_version: number;
  file_count: number;
  vector_count: number;
  created_at: string;
  updated_at: string;
  tags: string[];
  is_shared: boolean;
}

export interface KnowledgeBaseListResponse {
  knowledge_bases: KnowledgeBaseListItem[];
  total: number;
}

export interface CreateKnowledgeBaseRequest {
  name: string;
  description?: string;
  tags?: string[];
  is_shared?: boolean;
  default_chunk_config?: ChunkConfig;
  default_embed_config?: EmbedConfig;
  default_vector_store_config?: VectorStoreConfig;
}

export interface UpdateKnowledgeBaseRequest {
  name?: string;
  description?: string;
  tags?: string[];
  is_shared?: boolean;
  default_chunk_config?: ChunkConfig;
  default_embed_config?: EmbedConfig;
  default_vector_store_config?: VectorStoreConfig;
}

export interface ProcessKnowledgeBaseRequest {
  file_ids: string[];
  create_new_version?: boolean;
  chunk_config?: ChunkConfig;
  embed_config?: EmbedConfig;
  vector_store_config?: VectorStoreConfig;
}

/**
 * Create a new knowledge base
 */
export async function createKnowledgeBase(
  request: CreateKnowledgeBaseRequest
): Promise<KnowledgeBase> {
  const response = await apiClient.post<KnowledgeBase>('/knowledge-bases', request);
  return response.data;
}

/**
 * List all knowledge bases
 */
export async function listKnowledgeBases(): Promise<KnowledgeBaseListResponse> {
  const response = await apiClient.get<KnowledgeBaseListResponse>('/knowledge-bases');
  return response.data;
}

/**
 * Get a knowledge base by ID
 */
export async function getKnowledgeBase(kbId: string): Promise<KnowledgeBase> {
  const response = await apiClient.get<KnowledgeBase>(`/knowledge-bases/${kbId}`);
  return response.data;
}

/**
 * Update a knowledge base
 */
export async function updateKnowledgeBase(
  kbId: string,
  request: UpdateKnowledgeBaseRequest
): Promise<KnowledgeBase> {
  const response = await apiClient.put<KnowledgeBase>(`/knowledge-bases/${kbId}`, request);
  return response.data;
}

/**
 * Delete a knowledge base
 */
export async function deleteKnowledgeBase(kbId: string): Promise<void> {
  await apiClient.delete(`/knowledge-bases/${kbId}`);
}

/**
 * Process files in a knowledge base
 */
export async function processKnowledgeBase(
  kbId: string,
  request: ProcessKnowledgeBaseRequest
): Promise<KnowledgeBaseVersion> {
  const response = await apiClient.post<KnowledgeBaseVersion>(
    `/knowledge-bases/${kbId}/process`,
    request
  );
  return response.data;
}

/**
 * List all versions of a knowledge base
 */
export async function listKnowledgeBaseVersions(kbId: string): Promise<KnowledgeBaseVersion[]> {
  const response = await apiClient.get<KnowledgeBaseVersion[]>(
    `/knowledge-bases/${kbId}/versions`
  );
  return response.data;
}

/**
 * Get a specific version of a knowledge base
 */
export async function getKnowledgeBaseVersion(
  kbId: string,
  versionNumber: number
): Promise<KnowledgeBaseVersion> {
  const response = await apiClient.get<KnowledgeBaseVersion>(
    `/knowledge-bases/${kbId}/versions/${versionNumber}`
  );
  return response.data;
}

export interface VersionComparison {
  version1: KnowledgeBaseVersion;
  version2: KnowledgeBaseVersion;
  differences: {
    chunk_config?: Record<string, { v1: any; v2: any }>;
    embed_config?: Record<string, { v1: any; v2: any }>;
    vector_store_config?: Record<string, { v1: any; v2: any }>;
    files?: {
      added: string[];
      removed: string[];
      v1_count: number;
      v2_count: number;
    };
    metadata?: Record<string, { v1: any; v2: any }>;
  };
}

/**
 * Compare two versions of a knowledge base
 */
export async function compareVersions(
  kbId: string,
  version1: number,
  version2: number
): Promise<VersionComparison> {
  const response = await apiClient.get<VersionComparison>(
    `/knowledge-bases/${kbId}/versions/compare`,
    {
      params: { version1, version2 },
    }
  );
  return response.data;
}

/**
 * Rollback knowledge base to a specific version
 */
export async function rollbackToVersion(
  kbId: string,
  versionNumber: number
): Promise<KnowledgeBase> {
  const response = await apiClient.post<KnowledgeBase>(
    `/knowledge-bases/${kbId}/versions/${versionNumber}/rollback`
  );
  return response.data;
}

