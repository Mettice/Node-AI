/**
 * Error Toast Notifications
 * 
 * Enhanced toast notifications that work with our standardized error format
 * and provide better user experience with actionable error messages.
 */

import React from 'react';
import toast, { type Toast } from 'react-hot-toast';
import { AlertCircle, X, RefreshCw, Info, CheckCircle, AlertTriangle } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { APIErrorResponse } from './ErrorDisplay';

interface ErrorToastOptions {
  duration?: number;
  showSuggestions?: boolean;
  showRetry?: boolean;
  onRetry?: () => void;
  retryLabel?: string;
}

interface CustomToastProps {
  toast: Toast;
  error: APIErrorResponse;
  options: ErrorToastOptions;
}

// Custom Error Toast Component
function CustomErrorToast({ toast: t, error, options }: CustomToastProps) {
  const {
    duration = 6000,
    showSuggestions = true,
    showRetry = false,
    onRetry,
    retryLabel = "Retry"
  } = options;

  const handleRetry = () => {
    if (onRetry) {
      onRetry();
    }
    toast.dismiss(t.id);
  };

  return (
    <div className={cn(
      "max-w-md w-full bg-white shadow-lg rounded-lg pointer-events-auto flex",
      "transform-gpu transition-all duration-300 ease-out",
      t.visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
    )}>
      <div className="flex-1 w-0 p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <AlertCircle className="w-5 h-5 text-red-400" />
          </div>
          
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-gray-900">
              {error.error}
            </p>
            
            <p className="mt-1 text-sm text-gray-500">
              {error.message}
            </p>
            
            {showSuggestions && error.suggestions && error.suggestions.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-medium text-gray-700">
                  Quick fix:
                </p>
                <p className="text-xs text-gray-600 mt-1">
                  {error.suggestions[0]}
                </p>
              </div>
            )}
            
            {showRetry && onRetry && (
              <div className="mt-3">
                <button
                  onClick={handleRetry}
                  className="inline-flex items-center px-2 py-1 text-xs font-medium text-red-700 hover:text-red-900 bg-red-50 hover:bg-red-100 rounded"
                >
                  <RefreshCw className="w-3 h-3 mr-1" />
                  {retryLabel}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
      
      <div className="flex border-l border-gray-200">
        <button
          onClick={() => toast.dismiss(t.id)}
          className="w-full border border-transparent rounded-none rounded-r-lg p-4 flex items-center justify-center text-sm font-medium text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// Success Toast Component
function CustomSuccessToast({ toast: t, message }: { toast: Toast; message: string }) {
  return (
    <div className={cn(
      "max-w-md w-full bg-white shadow-lg rounded-lg pointer-events-auto flex",
      "transform-gpu transition-all duration-300 ease-out",
      t.visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
    )}>
      <div className="flex-1 w-0 p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <CheckCircle className="w-5 h-5 text-green-400" />
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-gray-900">
              Success
            </p>
            <p className="mt-1 text-sm text-gray-500">
              {message}
            </p>
          </div>
        </div>
      </div>
      
      <div className="flex border-l border-gray-200">
        <button
          onClick={() => toast.dismiss(t.id)}
          className="w-full border border-transparent rounded-none rounded-r-lg p-4 flex items-center justify-center text-sm font-medium text-gray-400 hover:text-gray-600"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// Warning Toast Component
function CustomWarningToast({ toast: t, message }: { toast: Toast; message: string }) {
  return (
    <div className={cn(
      "max-w-md w-full bg-white shadow-lg rounded-lg pointer-events-auto flex",
      "transform-gpu transition-all duration-300 ease-out",
      t.visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
    )}>
      <div className="flex-1 w-0 p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-gray-900">
              Warning
            </p>
            <p className="mt-1 text-sm text-gray-500">
              {message}
            </p>
          </div>
        </div>
      </div>
      
      <div className="flex border-l border-gray-200">
        <button
          onClick={() => toast.dismiss(t.id)}
          className="w-full border border-transparent rounded-none rounded-r-lg p-4 flex items-center justify-center text-sm font-medium text-gray-400 hover:text-gray-600"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// Enhanced Toast Functions
export const errorToast = {
  // Show error with full features
  show: (
    error: APIErrorResponse | Error | string,
    options: ErrorToastOptions = {}
  ) => {
    // Normalize error
    let normalizedError: APIErrorResponse;
    
    if (typeof error === 'string') {
      normalizedError = {
        error: 'Error',
        error_code: 'UNKNOWN_ERROR',
        message: error,
        timestamp: new Date().toISOString()
      };
    } else if (error instanceof Error) {
      normalizedError = {
        error: 'Error',
        error_code: 'JAVASCRIPT_ERROR',
        message: error.message,
        timestamp: new Date().toISOString()
      };
    } else {
      normalizedError = error;
    }

    return toast.custom(
      (t) => <CustomErrorToast toast={t} error={normalizedError} options={options} />,
      { 
        duration: options.duration || 6000,
        position: 'top-right'
      }
    );
  },

  // Show simple error message
  simple: (message: string, duration = 4000) => {
    return toast.error(message, { duration });
  },

  // Show network error
  network: (retryFn?: () => void) => {
    const error: APIErrorResponse = {
      error: 'Network Error',
      error_code: 'NETWORK_ERROR',
      message: 'Unable to connect to server',
      suggestions: [
        'Check your internet connection',
        'Try refreshing the page',
        'Contact support if the issue persists'
      ],
      timestamp: new Date().toISOString()
    };

    return errorToast.show(error, {
      duration: 8000,
      showRetry: Boolean(retryFn),
      onRetry: retryFn,
      retryLabel: 'Retry Connection'
    });
  },

  // Show validation error
  validation: (errors: string[] | APIErrorResponse) => {
    let error: APIErrorResponse;
    
    if (Array.isArray(errors)) {
      error = {
        error: 'Validation Error',
        error_code: 'VALIDATION_ERROR',
        message: 'Please check your input and try again',
        suggestions: errors,
        timestamp: new Date().toISOString()
      };
    } else {
      error = errors;
    }

    return errorToast.show(error, {
      duration: 7000,
      showSuggestions: true
    });
  },

  // Show rate limit error
  rateLimit: (retryAfter?: number) => {
    const error: APIErrorResponse = {
      error: 'Rate Limited',
      error_code: 'RATE_LIMIT_EXCEEDED',
      message: 'You are making requests too quickly',
      suggestions: [
        retryAfter ? `Wait ${retryAfter} seconds before trying again` : 'Wait a moment before trying again',
        'Consider upgrading for higher rate limits'
      ],
      timestamp: new Date().toISOString()
    };

    return errorToast.show(error, {
      duration: retryAfter ? (retryAfter + 2) * 1000 : 6000
    });
  },

  // Show authentication error
  auth: () => {
    const error: APIErrorResponse = {
      error: 'Authentication Required',
      error_code: 'AUTHENTICATION_REQUIRED',
      message: 'Please log in to continue',
      suggestions: [
        'Check that you are logged in',
        'Your session may have expired',
        'Try refreshing the page'
      ],
      timestamp: new Date().toISOString()
    };

    return errorToast.show(error, {
      duration: 5000
    });
  }
};

// Enhanced Success Toast
export const successToast = {
  show: (message: string, duration = 4000) => {
    return toast.custom(
      (t) => <CustomSuccessToast toast={t} message={message} />,
      { duration, position: 'top-right' }
    );
  },

  simple: (message: string, duration = 3000) => {
    return toast.success(message, { duration });
  }
};

// Enhanced Warning Toast
export const warningToast = {
  show: (message: string, duration = 5000) => {
    return toast.custom(
      (t) => <CustomWarningToast toast={t} message={message} />,
      { duration, position: 'top-right' }
    );
  },

  simple: (message: string, duration = 4000) => {
    return toast(message, { 
      icon: '⚠️',
      duration 
    });
  }
};

// Loading toast helpers
export const loadingToast = {
  show: (message = 'Loading...') => {
    return toast.loading(message);
  },

  update: (toastId: string, message: string) => {
    return toast.loading(message, { id: toastId });
  },

  success: (toastId: string, message: string) => {
    return toast.success(message, { id: toastId });
  },

  error: (toastId: string, error: APIErrorResponse | Error | string, options: ErrorToastOptions = {}) => {
    toast.dismiss(toastId);
    return errorToast.show(error, options);
  }
};

// Auto-retry toast for failed operations
export const autoRetryToast = (
  operation: () => Promise<void>,
  errorMessage: string,
  maxRetries = 3,
  retryDelay = 2000
) => {
  let retryCount = 0;

  const attempt = async () => {
    try {
      await operation();
      successToast.simple('Operation completed successfully');
    } catch (error) {
      retryCount++;
      
      if (retryCount < maxRetries) {
        warningToast.show(
          `${errorMessage} (Retry ${retryCount}/${maxRetries} in ${retryDelay/1000}s)`
        );
        
        setTimeout(attempt, retryDelay);
      } else {
        errorToast.show(error as any, {
          showSuggestions: true
        });
      }
    }
  };

  attempt();
};