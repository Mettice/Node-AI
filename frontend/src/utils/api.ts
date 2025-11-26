/**
 * API client setup and utilities
 */

import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import { API_BASE_URL, API_PREFIX } from '@/constants';

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor
apiClient.interceptors.request.use(
  async (config) => {
    // Add auth token from Supabase if available
    // Use shared Supabase client to avoid multiple instances
    try {
      const { getSupabaseClient } = await import('./supabase');
      const supabase = getSupabaseClient();
      
      if (supabase) {
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.access_token) {
          config.headers.Authorization = `Bearer ${session.access_token}`;
        }
      }
    } catch (error) {
      // Silently fail if Supabase is not configured
      console.debug('Could not add auth token:', error);
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle common errors
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as any;
      
      switch (status) {
        case 400:
          console.error('Bad Request:', data);
          break;
        case 401:
          console.error('Unauthorized - redirecting to login');
          // Redirect to login on 401
          if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
            window.location.href = '/login';
          }
          break;
        case 404:
          console.error('Not Found');
          break;
        case 500:
          console.error('Server Error:', data);
          break;
        default:
          console.error('API Error:', error.message);
      }
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error: No response from server');
    } else {
      // Error setting up request
      console.error('Request Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Enhanced error handling types
export interface APIErrorResponse {
  error: string;
  error_code: string;
  message: string;
  details?: string;
  suggestions?: string[];
  timestamp: string;
  request_id?: string;
  validation_errors?: Array<{
    code: string;
    message: string;
    details?: string;
    suggestions?: string[];
    field?: string;
  }>;
}

// Helper function to get error message
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    if (axiosError.response?.data) {
      const data = axiosError.response.data as any;
      return data.message || data.detail || 'An error occurred';
    }
    return axiosError.message || 'Network error';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unknown error occurred';
}

// Enhanced error parsing function
export function parseAPIError(error: unknown): APIErrorResponse {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    
    // Check if response has our standardized error format
    if (axiosError.response?.data) {
      const data = axiosError.response.data as any;
      
      // If it's already in our APIError format, return it
      if (data.error_code && data.message) {
        return data as APIErrorResponse;
      }
      
      // Convert old format to new format
      if (data.detail || data.message) {
        return {
          error: getErrorNameFromStatus(axiosError.response.status),
          error_code: getErrorCodeFromStatus(axiosError.response.status),
          message: data.message || data.detail || 'An error occurred',
          details: typeof data.detail === 'object' ? JSON.stringify(data.detail) : data.details,
          suggestions: generateSuggestions(axiosError.response.status, data),
          timestamp: new Date().toISOString(),
          request_id: axiosError.response.headers['x-request-id']
        };
      }
    }
    
    // Network or request error
    return {
      error: 'Network Error',
      error_code: 'NETWORK_ERROR',
      message: axiosError.message || 'Unable to connect to server',
      suggestions: [
        'Check your internet connection',
        'Try refreshing the page',
        'Contact support if the issue persists'
      ],
      timestamp: new Date().toISOString()
    };
  }
  
  // JavaScript error
  if (error instanceof Error) {
    return {
      error: 'Application Error',
      error_code: 'JAVASCRIPT_ERROR', 
      message: error.message,
      timestamp: new Date().toISOString()
    };
  }
  
  // Unknown error
  return {
    error: 'Unknown Error',
    error_code: 'UNKNOWN_ERROR',
    message: String(error) || 'An unknown error occurred',
    timestamp: new Date().toISOString()
  };
}

// Helper functions for error conversion
function getErrorNameFromStatus(status: number): string {
  const errorNames: Record<number, string> = {
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    409: 'Conflict',
    422: 'Validation Error',
    429: 'Rate Limited',
    500: 'Internal Server Error',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout'
  };
  return errorNames[status] || 'Error';
}

function getErrorCodeFromStatus(status: number): string {
  const errorCodes: Record<number, string> = {
    400: 'INVALID_INPUT',
    401: 'AUTHENTICATION_REQUIRED',
    403: 'INSUFFICIENT_PERMISSIONS',
    404: 'NOT_FOUND',
    409: 'CONFLICT',
    422: 'VALIDATION_ERROR',
    429: 'RATE_LIMIT_EXCEEDED',
    500: 'INTERNAL_ERROR',
    502: 'SERVICE_UNAVAILABLE',
    503: 'SERVICE_UNAVAILABLE',
    504: 'GATEWAY_TIMEOUT'
  };
  return errorCodes[status] || 'UNKNOWN_ERROR';
}

function generateSuggestions(status: number, data: any): string[] {
  const suggestions: Record<number, string[]> = {
    400: [
      'Check your input parameters',
      'Ensure all required fields are provided',
      'Verify data format is correct'
    ],
    401: [
      'Please log in to continue',
      'Check that your session hasn\'t expired',
      'Try refreshing the page'
    ],
    403: [
      'You don\'t have permission for this action',
      'Contact an administrator for access',
      'Check that you\'re logged in with the correct account'
    ],
    404: [
      'The requested item was not found',
      'Check that the ID or URL is correct',
      'The item may have been deleted'
    ],
    422: [
      'Please check your input and try again',
      'Some fields may be missing or invalid',
      'Review the validation errors below'
    ],
    429: [
      'You are making requests too quickly',
      'Wait a moment before trying again',
      'Consider upgrading for higher rate limits'
    ],
    500: [
      'Something went wrong on our end',
      'Try again in a few moments',
      'Contact support if the issue persists'
    ],
    503: [
      'Service is temporarily unavailable',
      'Try again in a few minutes',
      'Check if there\'s a maintenance notice'
    ]
  };
  
  return suggestions[status] || [
    'Try again in a moment',
    'Contact support if the issue persists'
  ];
}

// API call wrapper with enhanced error handling
export async function apiCall<T>(
  requestFn: () => Promise<T>,
  options: {
    retries?: number;
    retryDelay?: number;
    onError?: (error: APIErrorResponse) => void;
    suppressToast?: boolean;
  } = {}
): Promise<T> {
  const { retries = 0, retryDelay = 1000, onError, suppressToast = false } = options;
  let lastError: APIErrorResponse;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = parseAPIError(error);
      
      // Don't retry on client errors (4xx except 429)
      if (lastError.error_code === 'RATE_LIMIT_EXCEEDED' || 
          lastError.error_code.startsWith('5') || 
          lastError.error_code === 'NETWORK_ERROR') {
        
        // Wait before retry (except on last attempt)
        if (attempt < retries) {
          await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)));
          continue;
        }
      }
      
      // Call error handler if provided
      if (onError) {
        onError(lastError);
      }
      
      // Show toast unless suppressed
      if (!suppressToast) {
        const { errorToast } = await import('@/components/common/ErrorToast');
        errorToast.show(lastError);
      }
      
      throw lastError;
    }
  }
  
  throw lastError!;
}

