/**
 * API Key Input Component with Vault Integration
 * Supports both direct key entry and vault selection
 */

import { useState, useEffect } from 'react';
import { Eye, EyeOff, CheckCircle2, XCircle, Loader2, Plug, Key, Database, ChevronDown } from 'lucide-react';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';
import { secretsApi, type Secret } from '@/services/secrets';

interface VaultAPIKeyInputProps {
  value: string;
  secretId?: string;
  onChange: (value: string) => void;
  onSecretIdChange?: (secretId: string | undefined) => void;
  onConnectionChange?: (connected: boolean) => void;
  placeholder?: string;
  label?: string;
  description?: string;
  required?: boolean;
  testConnection?: (apiKey: string) => Promise<boolean>;
  serviceName?: string;
  provider?: string; // Provider name for filtering vault secrets (e.g., 'openai', 'anthropic', 'gemini')
  secretType?: string; // Secret type for vault (e.g., 'api_key')
}

export function VaultAPIKeyInput({
  value,
  secretId,
  onChange,
  onSecretIdChange,
  onConnectionChange,
  placeholder = 'Enter API key...',
  label = 'API Key',
  description,
  required = false,
  testConnection,
  serviceName = 'API',
  provider = 'openai',
  secretType = 'api_key',
}: VaultAPIKeyInputProps) {
  const [showKey, setShowKey] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [inputMode, setInputMode] = useState<'new' | 'vault'>('new');
  const [showVaultDropdown, setShowVaultDropdown] = useState(false);
  const [vaultSecrets, setVaultSecrets] = useState<Secret[]>([]);
  const [loadingSecrets, setLoadingSecrets] = useState(false);
  const [saveToVault, setSaveToVault] = useState(false);

  // Load vault secrets when switching to vault mode
  useEffect(() => {
    if (inputMode === 'vault' && vaultSecrets.length === 0 && !loadingSecrets) {
      loadVaultSecrets();
    }
  }, [inputMode]);

  // Load vault secrets on mount if secretId is set
  useEffect(() => {
    if (secretId) {
      setInputMode('vault');
      loadVaultSecrets();
    }
  }, [secretId]);

  const loadVaultSecrets = async () => {
    setLoadingSecrets(true);
    try {
      const secrets = await secretsApi.list({
        provider,
        secret_type: secretType,
        is_active: true,
      });
      setVaultSecrets(secrets);
    } catch (error: any) {
      console.error('Failed to load vault secrets:', error);
      toast.error('Failed to load vault secrets');
    } finally {
      setLoadingSecrets(false);
    }
  };

  const handleConnect = async () => {
    if (!value.trim()) {
      toast.error('Please enter an API key first');
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
      const connected = await testConnection(value.trim());
      setIsConnected(connected);
      onConnectionChange?.(connected);
      
      if (connected) {
        toast.success(`${serviceName} connection successful!`);
        
        // If save to vault is checked, save the key to vault
        if (saveToVault && inputMode === 'new') {
          await saveKeyToVault(value.trim());
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

  const saveKeyToVault = async (apiKey: string) => {
    try {
      const secret = await secretsApi.create({
        name: `${serviceName} API Key`,
        provider,
        secret_type: secretType,
        value: apiKey,
        description: `API key for ${serviceName}`,
      });
      toast.success('API key saved to vault');
      // Reload secrets to include the new one
      await loadVaultSecrets();
      // Optionally switch to vault mode and select the new secret
      setInputMode('vault');
      onSecretIdChange?.(secret.id);
      onChange(''); // Clear direct value since we're using vault
    } catch (error: any) {
      console.error('Failed to save to vault:', error);
      toast.error('Failed to save API key to vault');
    }
  };

  const handleVaultSecretSelect = async (selectedSecretId: string) => {
    setShowVaultDropdown(false);
    onSecretIdChange?.(selectedSecretId);
    
    try {
      const secret = await secretsApi.get(selectedSecretId, true); // decrypt = true
      if (secret.value) {
        onChange(secret.value);
        setInputMode('vault');
      }
    } catch (error: any) {
      console.error('Failed to load secret from vault:', error);
      toast.error('Failed to load secret from vault');
    }
  };

  const handleKeyChange = (newValue: string) => {
    onChange(newValue);
    // Clear secret ID when manually entering a key
    if (inputMode === 'new' && secretId) {
      onSecretIdChange?.(undefined);
    }
    // Reset connection status when key changes
    if (isConnected !== null) {
      setIsConnected(null);
      onConnectionChange?.(false);
    }
  };

  const handleModeSwitch = (mode: 'new' | 'vault') => {
    setInputMode(mode);
    if (mode === 'vault') {
      loadVaultSecrets();
    } else {
      // Clear vault selection when switching to new key mode
      onSecretIdChange?.(undefined);
    }
  };

  return (
    <div className="space-y-3">
      {description && (
        <p className="text-xs text-slate-400">{description}</p>
      )}

      {/* Mode Selection Buttons */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => handleModeSwitch('new')}
          className={cn(
            'flex-1 px-3 py-2 rounded-lg transition-all text-sm font-medium flex items-center justify-center gap-2',
            inputMode === 'new'
              ? 'bg-purple-500/20 border border-purple-500/50 text-purple-300'
              : 'bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10'
          )}
        >
          <Key className="w-4 h-4" />
          Enter New Key
        </button>
        <div className="relative flex-1">
          <button
            type="button"
            onClick={() => {
              setShowVaultDropdown(!showVaultDropdown);
              if (!showVaultDropdown) {
                loadVaultSecrets();
              }
            }}
            className={cn(
              'w-full px-3 py-2 rounded-lg transition-all text-sm font-medium flex items-center justify-center gap-2',
              inputMode === 'vault' || secretId
                ? 'bg-purple-500/20 border border-purple-500/50 text-purple-300'
                : 'bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10'
            )}
          >
            <Database className="w-4 h-4" />
            Use from Vault {vaultSecrets.length > 0 && `(${vaultSecrets.length})`}
            <ChevronDown className={cn('w-4 h-4 transition-transform', showVaultDropdown && 'rotate-180')} />
          </button>

          {/* Vault Dropdown */}
          {showVaultDropdown && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowVaultDropdown(false)}
              />
              <div className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-white/10 rounded-lg shadow-xl z-20 max-h-60 overflow-y-auto">
                {loadingSecrets ? (
                  <div className="p-4 text-center text-slate-400 text-sm">
                    <Loader2 className="w-4 h-4 animate-spin mx-auto mb-2" />
                    Loading secrets...
                  </div>
                ) : vaultSecrets.length === 0 ? (
                  <div className="p-4 text-center text-slate-400 text-sm">
                    No secrets found in vault
                  </div>
                ) : (
                  vaultSecrets.map((secret) => (
                    <button
                      key={secret.id}
                      type="button"
                      onClick={() => handleVaultSecretSelect(secret.id)}
                      className={cn(
                        'w-full px-4 py-2 text-left hover:bg-white/5 transition-colors text-sm',
                        secretId === secret.id && 'bg-purple-500/10'
                      )}
                    >
                      <div className="font-medium text-white">{secret.name}</div>
                      {secret.description && (
                        <div className="text-xs text-slate-400 mt-0.5">{secret.description}</div>
                      )}
                    </button>
                  ))
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* API Key Input */}
      {inputMode === 'new' && (
        <>
          <div className="relative">
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

          {/* Save to Vault Checkbox */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={saveToVault}
              onChange={(e) => setSaveToVault(e.target.checked)}
              className="h-4 w-4 text-purple-500 focus:ring-purple-500 border-white/20 rounded bg-white/5"
            />
            <span className="text-sm text-slate-300">Save to Secrets Vault for reuse</span>
          </label>
        </>
      )}

      {/* Connect Button */}
      <button
        type="button"
        onClick={handleConnect}
        disabled={isConnecting || !value.trim()}
        className={cn(
          'w-full px-4 py-2 rounded-lg transition-all flex items-center justify-center gap-2',
          'bg-purple-600 text-white font-medium text-sm',
          'hover:bg-purple-700',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          isConnected === true && 'bg-green-600 hover:bg-green-700',
          isConnected === false && 'bg-red-600 hover:bg-red-700'
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

