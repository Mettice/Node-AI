/**
 * Node-related API services
 */

import { apiClient } from '@/utils/api';
import type { NodeMetadata } from '@/types/node';

export interface NodeSchemaResponse {
  type: string;
  name: string;
  description: string;
  category: string;
  config_schema: Record<string, any>;
}

/**
 * Get list of all available nodes
 */
export async function listNodes(): Promise<NodeMetadata[]> {
  const response = await apiClient.get<NodeMetadata[]>('/nodes');
  return response.data || [];
}

/**
 * Get schema for a specific node type
 */
export async function getNodeSchema(nodeType: string): Promise<NodeSchemaResponse> {
  const response = await apiClient.get<NodeSchemaResponse>(`/nodes/${nodeType}`);
  return response.data;
}

/**
 * Get nodes grouped by category
 */
export async function getNodesByCategory(): Promise<Record<string, NodeMetadata[]>> {
  const response = await apiClient.get<Record<string, NodeMetadata[]>>('/nodes/categories');
  return response.data;
}

/**
 * Test API key connection for search providers
 */
export async function testSearchProviderConnection(
  provider: string,
  apiKey: string
): Promise<boolean> {
  try {
    const response = await apiClient.post<{ connected: boolean; message?: string }>(
      '/tools/test-connection',
      {
        service: 'web_search',
        provider,
        api_key: apiKey,
      }
    );
    return response.data.connected;
  } catch (error: any) {
    console.error('Connection test failed:', error);
    return false;
  }
}

/**
 * Test database connection
 */
export async function testDatabaseConnection(
  databaseType: string,
  connectionString: string
): Promise<boolean> {
  try {
    const response = await apiClient.post<{ connected: boolean; message?: string }>(
      '/tools/test-connection',
      {
        service: 'database',
        provider: databaseType,
        connection_string: connectionString,
      }
    );
    return response.data.connected;
  } catch (error: any) {
    console.error('Database connection test failed:', error);
    return false;
  }
}

/**
 * Test LLM API key connection
 */
export async function testLLMConnection(
  provider: string,
  apiKey: string
): Promise<boolean> {
  try {
    console.log('Testing LLM connection:', { provider, apiKey: apiKey ? '***' : 'missing' });
    const response = await apiClient.post<{ connected: boolean; message?: string }>(
      '/tools/test-connection',
      {
        service: 'llm',
        provider,
        api_key: apiKey,
      }
    );
    console.log('LLM test response:', response.data);
    console.log('Connected status:', response.data.connected);
    return response.data.connected;
  } catch (error: any) {
    console.error('LLM connection test failed:', error);
    console.error('Error details:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    });
    return false;
  }
}

/**
 * Test email provider API key connection
 */
export async function testEmailConnection(
  provider: string,
  apiKey: string
): Promise<boolean> {
  try {
    const response = await apiClient.post<{ connected: boolean; message?: string }>(
      '/tools/test-connection',
      {
        service: 'email',
        provider,
        api_key: apiKey,
      }
    );
    return response.data.connected;
  } catch (error: any) {
    console.error('Email connection test failed:', error);
    return false;
  }
}

/**
 * Test S3 connection
 */
export async function testS3Connection(
  accessKeyId: string,
  secretAccessKey: string,
  bucket: string,
  region: string = 'us-east-1'
): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await apiClient.post<{ connected: boolean; message?: string }>(
      '/tools/test-connection',
      {
        service: 's3',
        api_key: accessKeyId,
        connection_string: JSON.stringify({
          secret_access_key: secretAccessKey,
          bucket,
          region,
        }),
        bucket,
        region,
      }
    );
    return {
      success: response.data.connected,
      error: response.data.message,
    };
  } catch (error: any) {
    console.error('S3 connection test failed:', error);
    return {
      success: false,
      error: error.response?.data?.message || error.message || 'Connection test failed',
    };
  }
}

