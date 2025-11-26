/**
 * Error Display Components
 * 
 * Provides comprehensive error display components that integrate with
 * the backend's standardized APIError format for user-friendly error handling.
 */

import React from 'react';
import { AlertCircle, X, RefreshCw, HelpCircle, ExternalLink } from 'lucide-react';
import { cn } from '@/utils/cn';

// Types matching our backend APIError format
export interface ErrorDetail {
  code: string;
  message: string;
  details?: string;
  suggestions?: string[];
  field?: string;
}

export interface APIErrorResponse {
  error: string;
  error_code: string;
  message: string;
  details?: string;
  suggestions?: string[];
  timestamp: string;
  request_id?: string;
  validation_errors?: ErrorDetail[];
}

interface ErrorDisplayProps {
  error: APIErrorResponse | Error | string | null;
  title?: string;
  variant?: 'alert' | 'banner' | 'modal' | 'inline';
  showSuggestions?: boolean;
  showRetry?: boolean;
  showRequestId?: boolean;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

interface ErrorBannerProps {
  error: APIErrorResponse | Error | string;
  onDismiss?: () => void;
  className?: string;
}

interface ErrorToastProps {
  error: APIErrorResponse | Error | string;
  duration?: number;
  onDismiss?: () => void;
}

interface ValidationErrorsProps {
  errors: ErrorDetail[];
  className?: string;
}

// Helper function to normalize errors
function normalizeError(error: APIErrorResponse | Error | string | null): APIErrorResponse | null {
  if (!error) return null;

  if (typeof error === 'string') {
    return {
      error: 'Error',
      error_code: 'UNKNOWN_ERROR',
      message: error,
      timestamp: new Date().toISOString()
    };
  }

  if (error instanceof Error) {
    return {
      error: 'Error',
      error_code: 'JAVASCRIPT_ERROR',
      message: error.message,
      timestamp: new Date().toISOString()
    };
  }

  // Already an APIErrorResponse
  return error;
}

// Main Error Display Component
export function ErrorDisplay({
  error,
  title,
  variant = 'alert',
  showSuggestions = true,
  showRetry = false,
  showRequestId = false,
  onRetry,
  onDismiss,
  className
}: ErrorDisplayProps) {
  const normalizedError = normalizeError(error);
  
  if (!normalizedError) return null;

  const baseClasses = "rounded-lg border p-4";
  const variantClasses = {
    alert: "bg-red-50 border-red-200 text-red-800",
    banner: "bg-red-100 border-red-300 text-red-900",
    modal: "bg-white border-red-200 shadow-lg",
    inline: "bg-red-25 border-red-100 text-red-700"
  };

  return (
    <div className={cn(baseClasses, variantClasses[variant], className)}>
      <div className="flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0 text-red-500" />
        
        <div className="flex-1 min-w-0">
          {/* Error Header */}
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className="text-sm font-medium">
                {title || normalizedError.error}
              </h3>
              <p className="mt-1 text-sm text-gray-600">
                {normalizedError.message}
              </p>
            </div>
            
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="ml-2 text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Error Details */}
          {normalizedError.details && (
            <div className="mt-2 text-xs text-gray-500 bg-gray-50 rounded px-2 py-1">
              {normalizedError.details}
            </div>
          )}

          {/* Validation Errors */}
          {normalizedError.validation_errors && (
            <ValidationErrors 
              errors={normalizedError.validation_errors} 
              className="mt-3"
            />
          )}

          {/* Suggestions */}
          {showSuggestions && normalizedError.suggestions && normalizedError.suggestions.length > 0 && (
            <div className="mt-3">
              <h4 className="text-xs font-medium text-gray-700 mb-1 flex items-center">
                <HelpCircle className="w-3 h-3 mr-1" />
                Suggestions:
              </h4>
              <ul className="space-y-1">
                {normalizedError.suggestions.map((suggestion, index) => (
                  <li key={index} className="text-xs text-gray-600 flex items-start">
                    <span className="text-gray-400 mr-2">•</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Actions */}
          <div className="mt-3 flex items-center space-x-3">
            {showRetry && onRetry && (
              <button
                onClick={onRetry}
                className="inline-flex items-center text-xs text-red-700 hover:text-red-900 font-medium"
              >
                <RefreshCw className="w-3 h-3 mr-1" />
                Try Again
              </button>
            )}

            {showRequestId && normalizedError.request_id && (
              <span className="text-xs text-gray-400">
                ID: {normalizedError.request_id}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Error Banner Component (for page-level errors)
export function ErrorBanner({ error, onDismiss, className }: ErrorBannerProps) {
  return (
    <ErrorDisplay
      error={error}
      variant="banner"
      showSuggestions={true}
      showRetry={false}
      onDismiss={onDismiss}
      className={className}
    />
  );
}

// Validation Errors Component
export function ValidationErrors({ errors, className }: ValidationErrorsProps) {
  if (!errors || errors.length === 0) return null;

  return (
    <div className={cn("space-y-2", className)}>
      <h4 className="text-xs font-medium text-red-700">Validation Errors:</h4>
      {errors.map((error, index) => (
        <div key={index} className="text-xs bg-red-25 rounded p-2 border-l-2 border-red-300">
          <div className="flex items-center justify-between">
            <span className="font-medium text-red-800">
              {error.field && `${error.field}: `}{error.message}
            </span>
          </div>
          
          {error.details && (
            <p className="mt-1 text-red-600">{error.details}</p>
          )}
          
          {error.suggestions && error.suggestions.length > 0 && (
            <ul className="mt-2 space-y-1">
              {error.suggestions.map((suggestion, suggestionIndex) => (
                <li key={suggestionIndex} className="text-red-600 flex items-start">
                  <span className="text-red-400 mr-2">•</span>
                  {suggestion}
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}

// Error Card Component (for dashboard/list views)
interface ErrorCardProps {
  error: APIErrorResponse | Error | string;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export function ErrorCard({ error, icon, actions, className }: ErrorCardProps) {
  const normalizedError = normalizeError(error);
  if (!normalizedError) return null;

  return (
    <div className={cn("bg-white border border-red-200 rounded-lg p-4 shadow-sm", className)}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          {icon || <AlertCircle className="w-6 h-6 text-red-500" />}
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-gray-900">
            {normalizedError.error}
          </h3>
          
          <p className="mt-1 text-sm text-gray-600">
            {normalizedError.message}
          </p>
          
          {normalizedError.suggestions && normalizedError.suggestions.length > 0 && (
            <div className="mt-2">
              <p className="text-xs font-medium text-gray-700">What you can try:</p>
              <ul className="mt-1 space-y-1">
                {normalizedError.suggestions.slice(0, 2).map((suggestion, index) => (
                  <li key={index} className="text-xs text-gray-600 flex items-start">
                    <span className="text-gray-400 mr-2">•</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {actions && (
            <div className="mt-3">
              {actions}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Loading Error Component (for async operations)
interface LoadingErrorProps {
  error: APIErrorResponse | Error | string;
  onRetry: () => void;
  retryLabel?: string;
  className?: string;
}

export function LoadingError({ 
  error, 
  onRetry, 
  retryLabel = "Retry",
  className 
}: LoadingErrorProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center p-8 text-center", className)}>
      <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
      
      <ErrorDisplay
        error={error}
        variant="inline"
        showSuggestions={false}
        className="mb-4 text-left"
      />
      
      <button
        onClick={onRetry}
        className="inline-flex items-center px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
      >
        <RefreshCw className="w-4 h-4 mr-2" />
        {retryLabel}
      </button>
    </div>
  );
}

// Hook to extract error information
export function useErrorInfo(error: unknown) {
  const normalizedError = normalizeError(error as any);
  
  return {
    error: normalizedError,
    isRetryable: normalizedError?.error_code?.includes('RETRYABLE') || 
                 normalizedError?.error_code?.includes('RATE_LIMIT') ||
                 normalizedError?.error_code?.includes('TIMEOUT'),
    isValidationError: normalizedError?.validation_errors && normalizedError.validation_errors.length > 0,
    hasRequestId: Boolean(normalizedError?.request_id),
    hasSuggestions: normalizedError?.suggestions && normalizedError.suggestions.length > 0
  };
}