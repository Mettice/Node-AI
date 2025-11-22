/**
 * API Key Input Component with masking and connection testing
 */

import { useState } from 'react';
import { Eye, EyeOff, CheckCircle2, XCircle, Loader2, Plug } from 'lucide-react';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';

interface APIKeyInputProps {
  value: string;
  onChange: (value: string) => void;
  onConnectionChange?: (connected: boolean) => void;
  placeholder?: string;
  label?: string;
  description?: string;
  required?: boolean;
  testConnection?: (apiKey: string) => Promise<boolean>; // Optional function to test connection
  serviceName?: string; // Name of the service (e.g., "SerpAPI", "Brave Search")
}

export function APIKeyInput({
  value,
  onChange,
  onConnectionChange,
  placeholder = 'Enter API key...',
  label = 'API Key',
  description,
  required = false,
  testConnection,
  serviceName = 'API',
}: APIKeyInputProps) {
  const [showKey, setShowKey] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState<boolean | null>(null); // null = not tested, true = connected, false = failed

  const handleConnect = async () => {
    if (!value.trim()) {
      toast.error('Please enter an API key first');
      return;
    }

    if (!testConnection) {
      // If no test function provided, just mark as saved
      setIsConnected(true);
      onConnectionChange?.(true);
      toast.success('API key saved');
      return;
    }

    setIsConnecting(true);
    try {
      const connected = await testConnection(value.trim());
      setIsConnected(connected);
      onConnectionChange?.(connected);
      
      if (connected) {
        toast.success(`${serviceName} connection successful!`);
      } else {
        toast.error(`${serviceName} connection failed. Please check your API key.`);
      }
    } catch (error: any) {
      setIsConnected(false);
      onConnectionChange?.(false);
      toast.error(error.message || `${serviceName} connection failed`);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleKeyChange = (newValue: string) => {
    onChange(newValue);
    // Reset connection status when key changes
    if (isConnected !== null) {
      setIsConnected(null);
      onConnectionChange?.(false);
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
        {label}
        {required && <span className="text-red-400 ml-1">*</span>}
      </label>
      
      {description && (
        <p className="text-xs text-slate-400 -mt-1">{description}</p>
      )}

      <div className="flex gap-2">
        <div className="relative flex-1">
          <input
            type={showKey ? 'text' : 'password'}
            value={value}
            onChange={(e) => handleKeyChange(e.target.value)}
            placeholder={placeholder}
            className={cn(
              'w-full px-3 py-2 pr-20 rounded-lg transition-all',
              'bg-white/5 border border-white/10 text-slate-200 text-sm',
              'focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white/8',
              'hover:bg-white/8 hover:border-white/20',
              'placeholder:text-slate-500',
              isConnected === true && 'border-green-500/50',
              isConnected === false && 'border-red-500/50'
            )}
          />
          
          {/* Show/Hide toggle button */}
          <button
            type="button"
            onClick={() => setShowKey(!showKey)}
            className="absolute right-12 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-300 transition-colors"
            title={showKey ? 'Hide API key' : 'Show API key'}
          >
            {showKey ? (
              <EyeOff className="w-4 h-4" />
            ) : (
              <Eye className="w-4 h-4" />
            )}
          </button>

          {/* Connection status indicator */}
          {isConnected !== null && (
            <div className="absolute right-2 top-1/2 -translate-y-1/2" title={isConnected ? "Connected" : "Connection failed"}>
              {isConnected ? (
                <CheckCircle2 className="w-4 h-4 text-green-500" />
              ) : (
                <XCircle className="w-4 h-4 text-red-500" />
              )}
            </div>
          )}
        </div>

        {/* Connect button */}
        <button
          type="button"
          onClick={handleConnect}
          disabled={isConnecting || !value.trim()}
          className={cn(
            'px-4 py-2 rounded-lg transition-all flex items-center gap-2',
            'bg-purple-500/20 border border-purple-500/50 text-purple-300',
            'hover:bg-purple-500/30 hover:border-purple-500',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'text-sm font-medium',
            isConnected === true && 'bg-green-500/20 border-green-500/50 text-green-300',
            isConnected === false && 'bg-red-500/20 border-red-500/50 text-red-300'
          )}
        >
          {isConnecting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Testing...</span>
            </>
          ) : isConnected === true ? (
            <>
              <CheckCircle2 className="w-4 h-4" />
              <span>Connected</span>
            </>
          ) : (
            <>
              <Plug className="w-4 h-4" />
              <span>Connect</span>
            </>
          )}
        </button>
      </div>

      {/* Connection status message */}
      {isConnected === true && (
        <p className="text-xs text-green-400 flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3" />
          {serviceName} connection verified and saved
        </p>
      )}
      {isConnected === false && (
        <p className="text-xs text-red-400 flex items-center gap-1">
          <XCircle className="w-3 h-3" />
          Connection failed. Please check your API key and try again.
        </p>
      )}
    </div>
  );
}

