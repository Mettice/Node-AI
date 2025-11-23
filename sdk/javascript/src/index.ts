/**
 * NodAI JavaScript/TypeScript SDK
 * 
 * A simple client library for interacting with NodAI workflows.
 */

export interface QueryRequest {
  input: Record<string, any>;
}

export interface QueryResponse {
  execution_id: string;
  status: string;
  started_at: string;
  completed_at?: string;
  total_cost: number;
  duration_ms: number;
  results: Record<string, any>;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  message: string;
}

export class NodAIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'NodAIError';
  }
}

export class NodAIClient {
  private apiKey: string;
  private baseUrl: string;

  /**
   * Create a new NodAI client.
   * 
   * @param apiKey - Your NodAI API key
   * @param baseUrl - Base URL of the NodAI API (default: current origin or localhost)
   */
  constructor(apiKey: string, baseUrl?: string) {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl || (typeof window !== 'undefined' 
      ? window.location.origin 
      : 'http://localhost:8000');
    
    // Remove trailing slash
    this.baseUrl = this.baseUrl.replace(/\/$/, '');
  }

  /**
   * Query a deployed workflow.
   * 
   * @param workflowId - The ID of the deployed workflow
   * @param input - Input data for the workflow (e.g., { query: "..." })
   * @param timeout - Request timeout in milliseconds (default: 60000)
   * @returns Promise resolving to the execution results
   * @throws NodAIError if the request fails
   */
  async queryWorkflow(
    workflowId: string,
    input: Record<string, any>,
    timeout: number = 60000
  ): Promise<QueryResponse> {
    const url = `${this.baseUrl}/api/v1/workflows/${workflowId}/query`;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey,
        },
        body: JSON.stringify({ input }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        let details: any = null;

        try {
          const errorData = await response.json();
          errorMessage = errorData.detail?.message || errorData.message || errorMessage;
          details = errorData;
        } catch {
          // Ignore JSON parse errors
        }

        throw new NodAIError(errorMessage, response.status, details);
      }

      return await response.json();
    } catch (error: any) {
      clearTimeout(timeoutId);
      
      if (error instanceof NodAIError) {
        throw error;
      }
      
      if (error.name === 'AbortError') {
        throw new NodAIError('Request timeout', 408);
      }
      
      throw new NodAIError(`Request failed: ${error.message}`);
    }
  }

  /**
   * Check if the API is healthy.
   * 
   * @returns Promise resolving to health status
   */
  async healthCheck(): Promise<HealthResponse> {
    const url = `${this.baseUrl}/api/v1/health`;
    
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'X-API-Key': this.apiKey,
        },
      });

      if (!response.ok) {
        throw new NodAIError(`Health check failed: HTTP ${response.status}`, response.status);
      }

      return await response.json();
    } catch (error: any) {
      if (error instanceof NodAIError) {
        throw error;
      }
      throw new NodAIError(`Health check failed: ${error.message}`);
    }
  }
}

// Default export
export default NodAIClient;

