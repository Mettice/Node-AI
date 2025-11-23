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

