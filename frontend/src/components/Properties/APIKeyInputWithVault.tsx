/**
 * Enhanced API Key Input Component with Vault Integration
 * Supports both direct entry and vault selection
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Eye, EyeOff, CheckCircle2, XCircle, Loader2, Plug, Key, Database } from 'lucide-react';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';
import { secretsApi } from '@/services/secrets';

interface APIKeyInputWithVaultProps {
  value: string;
  onChange: (value: string, secretId?: string) => void;
  onConnectionChange?: (connected: boolean) => void;
  placeholder?: string;
  label?: string;
  description?: string;
  required?: boolean;
  testConnection?: (apiKey: string) => Promise<boolean>;
  serviceName?: string;
  provider?: string; // Provider name for vault filtering (e.g., 'openai', 'anthropic')
  secretType?: string; // Secret type (default: 'api_key')
  secretId?: string; // Secret ID from config (if key is from vault)
}

export function APIKeyInputWithVault({
  value,
  onChange,
  onConnectionChange,
  placeholder = 'Enter API key...',
  label = 'API Key',
  description,
  required = false,
  testConnection,
  serviceName = 'API',
  provider,
  secretType = 'api_key',
  secretId: initialSecretId,
}: APIKeyInputWithVaultProps) {
  const [showKey, setShowKey] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [useVault, setUseVault] = useState(!!initialSecretId);
  const [selectedSecretId, setSelectedSecretId] = useState<string>(initialSecretId || '');
  const [saveToVault, setSaveToVault] = useState(true);
  const queryClient = useQueryClient();

  // Fetch secrets from vault if provider is specified (always fetch to show available secrets)
  const { data: secrets = [] } = useQuery({
    queryKey: ['secrets', provider, secretType],
    queryFn: async () => {
      if (!provider) return [];
      const list = await secretsApi.list({ provider, secret_type: secretType, is_active: true });
      // Fetch decrypted values for each secret
      const secretsWithValues = await Promise.all(
        list.map(async (secret) => {
          try {
            const decrypted = await secretsApi.get(secret.id, true);
            return { ...secret, value: decrypted.value };
          } catch {
            return secret;
          }
        })
      );
      return secretsWithValues;
    },
    enabled: !!provider, // Always fetch if provider is specified
  });

  // Check if current value is from vault (has secret_id in config or matches a vault secret)
  useEffect(() => {
    // If secret_id is provided, use vault mode
    if (initialSecretId) {
      setUseVault(true);
      setSelectedSecretId(initialSecretId);
      // Load the secret value if not already loaded
      if (!value && initialSecretId) {
        secretsApi.get(initialSecretId, true)
          .then((secret) => {
            if (secret.value) {
              onChange(secret.value, initialSecretId);
            }
          })
          .catch((err) => {
            // Secret not found or access denied - clear the secret_id reference
            if (err.response?.status === 404) {
              console.warn(`Secret ${initialSecretId} not found, clearing reference`);
              onChange('', undefined);
              setUseVault(false);
              setSelectedSecretId('');
            } else {
              console.error('Failed to load secret from vault:', err);
            }
          });
      }
    } else if (value && secrets.length > 0) {
      // If value exists and we have secrets, check if it matches a vault secret
      const matchingSecret = secrets.find((s) => s.value === value);
      if (matchingSecret) {
        setUseVault(true);
        setSelectedSecretId(matchingSecret.id);
      }
    }
  }, [value, secrets, initialSecretId, onChange]);

  const createSecretMutation = useMutation({
    mutationFn: (keyValue: string) =>
      secretsApi.create({
        name: `${serviceName} API Key`,
        provider: provider || '',
        secret_type: secretType,
        value: keyValue,
      }),
    onSuccess: (secret) => {
      queryClient.invalidateQueries({ queryKey: ['secrets'] });
      setUseVault(true);
      setSelectedSecretId(secret.id);
      onChange(secret.value || '', secret.id);
      toast.success('API key saved to vault');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to save to vault');
    },
  });

  const handleConnect = async () => {
    let keyToTest = value;
    
    if (useVault && selectedSecretId) {
      try {
        const secret = await secretsApi.get(selectedSecretId, true);
        keyToTest = secret.value || '';
      } catch (error) {
        toast.error('Failed to load secret from vault');
        return;
      }
    }

    if (!keyToTest.trim()) {
      toast.error('Please enter or select an API key first');
      return;
    }

    if (!testConnection) {
      setIsConnected(true);
      onConnectionChange?.(true);
      toast.success('API key saved');
      return;
    }

    setIsConnecting(true);
    try {
      const connected = await testConnection(keyToTest.trim());
      setIsConnected(connected);
      onConnectionChange?.(connected);

      if (connected) {
        toast.success(`${serviceName} connection successful!`);
        
        // If using direct entry and saveToVault is checked, save to vault
        if (!useVault && saveToVault && value && provider) {
          createSecretMutation.mutate(value);
        }
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

  const handleVaultSelection = async (secretId: string) => {
    if (!secretId) {
      setSelectedSecretId('');
      onChange('', undefined);
      setIsConnected(null);
      onConnectionChange?.(false);
      return;
    }

    try {
      // Fetch decrypted value
      const secret = await secretsApi.get(secretId, true);
      if (secret.value) {
        setSelectedSecretId(secretId);
        onChange(secret.value, secretId);
        setIsConnected(null);
        onConnectionChange?.(false);
      }
    } catch (error) {
      toast.error('Failed to load secret from vault');
    }
  };

  const handleDirectEntry = (newValue: string) => {
    onChange(newValue);
    if (isConnected !== null) {
      setIsConnected(null);
      onConnectionChange?.(false);
    }
  };


  return (
    <div className="space-y-3">
      <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
        {label}
        {required && <span className="text-red-400 ml-1">*</span>}
      </label>

      {description && (
        <p className="text-xs text-slate-400 -mt-2">{description}</p>
      )}

      {/* Vault Toggle (only show if provider is specified) */}
      {provider && secrets.length > 0 && (
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => {
              setUseVault(false);
              setSelectedSecretId('');
            }}
            className={cn(
              'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors',
              !useVault
                ? 'bg-purple-500/20 border border-purple-500/50 text-purple-300'
                : 'bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10'
            )}
          >
            <Key className="w-4 h-4" />
            <span>Enter New Key</span>
          </button>
          <button
            type="button"
            onClick={() => setUseVault(true)}
            className={cn(
              'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors',
              useVault
                ? 'bg-purple-500/20 border border-purple-500/50 text-purple-300'
                : 'bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10'
            )}
          >
            <Database className="w-4 h-4" />
            <span>Use from Vault</span>
            {secrets.length > 0 && (
              <span className="text-xs bg-purple-500/30 px-1.5 py-0.5 rounded">
                {secrets.length}
              </span>
            )}
          </button>
        </div>
      )}

      {/* Vault Selection */}
      {useVault && provider && secrets.length > 0 ? (
        <div className="space-y-2">
          <select
            value={selectedSecretId}
            onChange={(e) => {
              handleVaultSelection(e.target.value);
            }}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 [&>option]:bg-slate-800 [&>option]:text-white"
            style={{ colorScheme: 'dark' }}
          >
            <option value="">Select from vault...</option>
            {secrets.map((secret) => (
              <option key={secret.id} value={secret.id}>
                {secret.name} {secret.last_used_at && `(Last used: ${new Date(secret.last_used_at).toLocaleDateString()})`}
              </option>
            ))}
          </select>
          {selectedSecretId && (
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Database className="w-3 h-3" />
              <span>Using secret from vault</span>
            </div>
          )}
        </div>
      ) : (
        /* Direct Entry */
        <div className="space-y-2">
          <div className="relative flex-1">
            <input
              type={showKey ? 'text' : 'password'}
              value={value}
              onChange={(e) => handleDirectEntry(e.target.value)}
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

            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              className="absolute right-12 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-300 transition-colors"
              title={showKey ? 'Hide API key' : 'Show API key'}
            >
              {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>

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

          {/* Save to Vault checkbox (only show if provider is specified and not using vault) */}
          {provider && !useVault && (
            <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
              <input
                type="checkbox"
                checked={saveToVault}
                onChange={(e) => setSaveToVault(e.target.checked)}
                className="w-4 h-4 rounded bg-white/5 border-white/10 text-purple-500 focus:ring-purple-500"
              />
              <span>Save to Secrets Vault for reuse</span>
            </label>
          )}
        </div>
      )}

      {/* Connect button */}
        <button
          type="button"
          onClick={handleConnect}
          disabled={isConnecting || (!value.trim() && !selectedSecretId)}
        className={cn(
          'w-full px-4 py-2 rounded-lg transition-all flex items-center justify-center gap-2',
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

      {/* Status messages */}
      {isConnected === true && (
        <p className="text-xs text-green-400 flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3" />
          {serviceName} connection verified
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

