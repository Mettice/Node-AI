/**
 * Embeddable NodAI Widget
 * 
 * This component can be embedded in external websites to query deployed workflows.
 * 
 * Usage:
 * ```tsx
 * <NodAIWidget
 *   apiKey="nk_..."
 *   workflowId="workflow-id"
 *   apiUrl="https://api.nodai.io"
 * />
 * ```
 */

import { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface NodAIWidgetProps {
  apiKey: string;
  workflowId: string;
  apiUrl?: string; // Optional: defaults to current origin
  placeholder?: string;
  buttonText?: string;
  className?: string;
}

export function NodAIWidget({
  apiKey,
  workflowId,
  apiUrl,
  placeholder = 'Ask a question...',
  buttonText = 'Send',
  className = '',
}: NodAIWidgetProps) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      // Use custom API URL if provided
      const baseURL = apiUrl || window.location.origin;
      
      // Make request with API key
      const response = await fetch(`${baseURL}/api/v1/workflows/${workflowId}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({
          input: {
            query: query.trim(),
          },
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Request failed' }));
        throw new Error(errorData.detail?.message || errorData.message || `HTTP ${response.status}`);
      }

      const data = await response.json();
      
      // Extract the final response (usually from the last node)
      // This is a simplified extraction - adjust based on your workflow structure
      const results = data.results || {};
      const lastNodeResult = Object.values(results).pop();
      const finalResponse = typeof lastNodeResult === 'string' 
        ? lastNodeResult 
        : (lastNodeResult && typeof lastNodeResult === 'object' && ('output' in lastNodeResult || 'text' in lastNodeResult))
          ? (lastNodeResult as any).output || (lastNodeResult as any).text || JSON.stringify(lastNodeResult)
          : JSON.stringify(lastNodeResult);
      
      setResponse(finalResponse);
      setQuery(''); // Clear input after successful query
    } catch (err: any) {
      setError(err.message || 'Failed to get response');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`nodai-widget ${className}`}>
      <style>{`
        .nodai-widget {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          max-width: 600px;
          margin: 0 auto;
        }
        .nodai-widget * {
          box-sizing: border-box;
        }
      `}</style>
      
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            disabled={loading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                {buttonText}
              </>
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {response && (
        <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="text-sm text-gray-600 mb-2">Response:</div>
          <div className="text-gray-900 whitespace-pre-wrap">{response}</div>
        </div>
      )}

      {/* Powered by NodeAI */}
      <div className="mt-4 text-center">
        <a
          href="https://nodai.io"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
        >
          Powered by <span className="font-semibold">NodAI</span>
        </a>
      </div>
    </div>
  );
}

