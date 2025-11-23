/**
 * Streaming service for real-time execution updates.
 * 
 * Uses Server-Sent Events (SSE) with polling fallback.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface StreamEvent {
  event_type: string;
  node_id: string;
  execution_id?: string;
  agent?: string;
  task?: string;
  // Progress and message can be at top level (for node_progress events) or in data
  progress?: number;
  message?: string;
  data: {
    message?: string;
    progress?: number;
    output?: any;
    thought?: string;
    tool?: string;
    [key: string]: any;
  };
  timestamp: string;
}

export type StreamEventHandler = (event: StreamEvent) => void;

class StreamClient {
  private eventSource: EventSource | null = null;
  private handlers: Set<StreamEventHandler> = new Set();
  private isConnected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  /**
   * Connect to SSE stream for an execution.
   */
  connect(executionId: string): void {
    if (this.eventSource) {
      this.disconnect();
    }

    const url = `${API_BASE_URL}/api/v1/executions/${executionId}/stream`;
    
    try {
      this.eventSource = new EventSource(url);
      
      this.eventSource.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        console.log(`[Stream] Connected to execution ${executionId}`);
      };

      this.eventSource.onmessage = (e) => {
        try {
          const event: StreamEvent = JSON.parse(e.data);
          this.handleEvent(event);
        } catch (error) {
          console.error('[Stream] Error parsing event:', error);
        }
      };

      this.eventSource.addEventListener('connected', (e: any) => {
        console.log('[Stream] Connection confirmed');
      });

      this.eventSource.addEventListener('complete', (e: any) => {
        console.log('[Stream] Stream complete');
        this.disconnect();
      });

      this.eventSource.addEventListener('error', (e: any) => {
        console.error('[Stream] SSE error:', e);
        this.handleReconnect(executionId);
      });

      this.eventSource.onerror = () => {
        if (this.eventSource?.readyState === EventSource.CLOSED) {
          this.handleReconnect(executionId);
        }
      };
    } catch (error) {
      console.error('[Stream] Failed to create EventSource:', error);
      // Fallback to polling if SSE not supported
      this.startPolling(executionId);
    }
  }

  /**
   * Handle reconnection logic.
   */
  private handleReconnect(executionId: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[Stream] Max reconnection attempts reached, falling back to polling');
      this.disconnect();
      this.startPolling(executionId);
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;

    console.log(`[Stream] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      if (!this.isConnected) {
        this.connect(executionId);
      }
    }, delay);
  }

  /**
   * Fallback to polling if SSE is not available.
   */
  private startPolling(executionId: string): void {
    console.log('[Stream] Starting polling fallback');
    
    let lastEventTime = Date.now();
    const pollInterval = 500; // Poll every 500ms

    const poll = async () => {
      try {
        // Get execution status (which includes latest events via trace)
        const response = await fetch(`${API_BASE_URL}/api/v1/executions/${executionId}`);
        if (!response.ok) {
          return;
        }

        const execution = await response.json();
        
        // Check if execution is complete
        if (execution.status === 'completed' || execution.status === 'failed') {
          return; // Stop polling
        }

        // Continue polling
        setTimeout(poll, pollInterval);
      } catch (error) {
        console.error('[Stream] Polling error:', error);
        setTimeout(poll, pollInterval);
      }
    };

    poll();
  }

  /**
   * Subscribe to stream events.
   */
  subscribe(handler: StreamEventHandler): () => void {
    this.handlers.add(handler);
    
    // Return unsubscribe function
    return () => {
      this.handlers.delete(handler);
    };
  }

  /**
   * Handle incoming event and notify all handlers.
   */
  private handleEvent(event: StreamEvent): void {
    this.handlers.forEach((handler) => {
      try {
        handler(event);
      } catch (error) {
        console.error('[Stream] Error in event handler:', error);
      }
    });
  }

  /**
   * Disconnect from stream.
   */
  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.isConnected = false;
    this.handlers.clear();
  }

  /**
   * Check if currently connected.
   */
  get connected(): boolean {
    return this.isConnected;
  }
}

// Singleton instance
export const streamClient = new StreamClient();

