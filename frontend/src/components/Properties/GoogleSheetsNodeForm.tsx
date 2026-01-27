/**
 * Google Sheets Node Form Component
 * Provides OAuth connection and Google Sheets configuration (read/write/append/update)
 */

import { useState, useEffect, useRef } from 'react';
import { ProviderIcon } from '@/components/common/ProviderIcon';
import { initOAuthFlow, exchangeOAuthCode, listOAuthTokens, deleteOAuthToken } from '@/services/oauth';
import { FileSpreadsheet, Upload, Download } from 'lucide-react';

interface GoogleSheetsNodeFormProps {
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
  schema?: Record<string, any>;
}

const GOOGLE_SCOPES = [
  'https://www.googleapis.com/auth/spreadsheets',
];

export function GoogleSheetsNodeForm({ initialData, onChange }: GoogleSheetsNodeFormProps) {
  const [operation, setOperation] = useState(initialData.operation || 'read');
  const [spreadsheetId, setSpreadsheetId] = useState(initialData.spreadsheet_id || '');
  const [sheetName, setSheetName] = useState(initialData.sheet_name || 'Sheet1');
  const [range, setRange] = useState(initialData.range || '');
  const [hasHeader, setHasHeader] = useState(initialData.has_header !== false);
  const [clearExisting, setClearExisting] = useState(initialData.clear_existing || false);
  const [includeHeader, setIncludeHeader] = useState(initialData.include_header !== false);
  const [tokenId, setTokenId] = useState(initialData.oauth_token_id || '');
  
  // OAuth connection state
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [redirectUri, setRedirectUri] = useState(window.location.origin + '/oauth/callback');
  const [availableTokens, setAvailableTokens] = useState<any[]>([]);
  const [isConnecting, setIsConnecting] = useState(false);
  
  const onChangeRef = useRef(onChange);
  
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  // Handle OAuth callback from redirect
  const handleOAuthCallback = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const service = urlParams.get('service');
    const error = urlParams.get('error');

    // Only handle Google callbacks
    if (service !== 'google' && !code && !state) {
      return;
    }

    if (error) {
      alert(`OAuth error: ${error}`);
      window.history.replaceState({}, '', window.location.pathname);
      return;
    }

    if (code && state) {
      const storedState = sessionStorage.getItem('google_oauth_state');
      const clientId = sessionStorage.getItem('google_client_id');
      const clientSecret = sessionStorage.getItem('google_client_secret');
      const redirectUri = sessionStorage.getItem('google_redirect_uri');

      if (state !== storedState) {
        alert('Invalid OAuth state. Please try again.');
        sessionStorage.removeItem('google_oauth_state');
        sessionStorage.removeItem('google_client_id');
        sessionStorage.removeItem('google_client_secret');
        sessionStorage.removeItem('google_redirect_uri');
        window.history.replaceState({}, '', window.location.pathname);
        return;
      }

      if (!clientId || !clientSecret || !redirectUri) {
        alert('OAuth session expired. Please try connecting again.');
        window.history.replaceState({}, '', window.location.pathname);
        return;
      }

      try {
        const result = await exchangeOAuthCode({
          service: 'google',
          code,
          state,
          client_id: clientId,
          client_secret: clientSecret,
          redirect_uri: redirectUri,
        });

        if (result.success && result.token_id) {
          setTokenId(result.token_id);
          await loadTokens();
          alert('Google connected successfully!');
        } else {
          alert(`Failed to connect: ${result.message || 'Unknown error'}`);
        }
      } catch (error: any) {
        alert(`Failed to exchange OAuth code: ${error.message}`);
      } finally {
        sessionStorage.removeItem('google_oauth_state');
        sessionStorage.removeItem('google_client_id');
        sessionStorage.removeItem('google_client_secret');
        sessionStorage.removeItem('google_redirect_uri');
        window.history.replaceState({}, '', window.location.pathname);
      }
    }
  };

  // Load available tokens on mount and handle OAuth callback
  useEffect(() => {
    loadTokens();
    handleOAuthCallback();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update parent when form changes
  useEffect(() => {
    const config: Record<string, any> = {
      operation,
      spreadsheet_id: spreadsheetId,
      sheet_name: sheetName,
      oauth_token_id: tokenId,
    };

    if (range) config.range = range;
    
    if (operation === 'read') {
      config.has_header = hasHeader;
    } else {
      config.clear_existing = clearExisting;
      config.include_header = includeHeader;
    }

    onChangeRef.current(config);
  }, [operation, spreadsheetId, sheetName, range, hasHeader, clearExisting, includeHeader, tokenId]);

  const loadTokens = async () => {
    try {
      const tokens = await listOAuthTokens('google');
      setAvailableTokens(tokens);
      if (!tokenId && tokens.length > 0) {
        const validToken = tokens.find(t => t.is_valid);
        if (validToken) {
          setTokenId(validToken.token_id);
        }
      }
    } catch (error) {
      console.error('Failed to load Google tokens:', error);
    }
  };

  const handleConnectGoogle = async () => {
    if (!clientId) {
      alert('Please enter Google Client ID');
      return;
    }

    setIsConnecting(true);
    try {
      const result = await initOAuthFlow({
        service: 'google',
        client_id: clientId,
        redirect_uri: redirectUri,
        scopes: GOOGLE_SCOPES,
      });

      // Store OAuth data in sessionStorage for callback
      sessionStorage.setItem('google_oauth_state', result.state);
      sessionStorage.setItem('google_client_id', clientId);
      sessionStorage.setItem('google_client_secret', clientSecret);
      sessionStorage.setItem('google_redirect_uri', redirectUri);

      // Redirect to Google OAuth
      window.location.href = result.authorization_url;
    } catch (error: any) {
      alert(`Failed to initiate OAuth: ${error.message}`);
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!tokenId) return;
    
    if (confirm('Are you sure you want to disconnect this Google account?')) {
      try {
        await deleteOAuthToken(tokenId);
        setTokenId('');
        await loadTokens();
      } catch (error) {
        alert('Failed to disconnect Google account');
      }
    }
  };

  const selectedToken = availableTokens.find(t => t.token_id === tokenId);

  return (
    <div className="space-y-4">
      {/* OAuth Connection */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <ProviderIcon provider="google" size="sm" />
          <h3 className="text-sm font-semibold text-white">Google Connection</h3>
        </div>

        {tokenId && selectedToken ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-green-500/10 border border-green-500/30 rounded">
              <div className="flex items-center gap-2">
                <ProviderIcon provider="google" size="sm" />
                <div>
                  <p className="text-sm text-white font-medium">Connected</p>
                  <p className="text-xs text-slate-400">
                    {selectedToken.is_valid ? 'Token valid' : 'Token expired'}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleDisconnect}
                className="px-3 py-1 text-xs bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded transition-all"
              >
                Disconnect
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-slate-400">
              Connect your Google account to read from Google Sheets. You'll need to create a Google Cloud project and get OAuth credentials.
            </p>
            
            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                Client ID <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                placeholder="1234567890-abc123.apps.googleusercontent.com"
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                Client Secret <span className="text-red-400">*</span>
              </label>
              <input
                type="password"
                value={clientSecret}
                onChange={(e) => setClientSecret(e.target.value)}
                placeholder="GOCSPX-..."
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
              />
            </div>

            <button
              type="button"
              onClick={handleConnectGoogle}
              disabled={isConnecting || !clientId || !clientSecret}
              className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg transition-all text-sm font-medium flex items-center justify-center gap-2"
            >
              {isConnecting ? (
                <>Connecting...</>
              ) : (
                <>
                  <ProviderIcon provider="google" size="sm" />
                  Connect Google Account
                </>
              )}
            </button>
          </div>
        )}

        {availableTokens.length > 1 && (
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Select Connection
            </label>
            <select
              value={tokenId}
              onChange={(e) => setTokenId(e.target.value)}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
            >
              <option value="">Select a connection...</option>
              {availableTokens.map((token) => (
                <option key={token.token_id} value={token.token_id}>
                  {token.is_valid ? '✓' : '✗'} {token.created_at ? new Date(token.created_at).toLocaleDateString() : 'Unknown'}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Operation Selector */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4" />
          Operation
        </h3>
        
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Operation Type
          </label>
          <select
            value={operation}
            onChange={(e) => setOperation(e.target.value)}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          >
            <option value="read">Read</option>
            <option value="write">Write (Overwrite)</option>
            <option value="append">Append</option>
            <option value="update">Update</option>
          </select>
        </div>
      </div>

      {/* Spreadsheet Configuration */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          {operation === 'read' ? (
            <Download className="w-4 h-4" />
          ) : (
            <Upload className="w-4 h-4" />
          )}
          Spreadsheet Configuration
        </h3>
        
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Spreadsheet ID <span className="text-red-400">*</span>
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            From the Google Sheets URL: /spreadsheets/d/{'{ID}'}/edit
          </p>
          <input
            type="text"
            value={spreadsheetId}
            onChange={(e) => setSpreadsheetId(e.target.value)}
            placeholder="1abc123def456..."
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Sheet Name
          </label>
          <input
            type="text"
            value={sheetName}
            onChange={(e) => setSheetName(e.target.value)}
            placeholder="Sheet1"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
            Range (Optional)
          </label>
          <p className="text-xs text-slate-400 -mt-1">
            {operation === 'read' 
              ? 'Specific range to read (e.g., A1:C100). Leave empty for entire sheet.'
              : 'Starting cell (e.g., A1). Leave empty to start at A1 (or append for append operation).'}
          </p>
          <input
            type="text"
            value={range}
            onChange={(e) => setRange(e.target.value)}
            placeholder={operation === 'read' ? 'A1:C100' : 'A1'}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
          />
        </div>

        {operation === 'read' ? (
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="hasHeader"
              checked={hasHeader}
              onChange={(e) => setHasHeader(e.target.checked)}
              className="w-4 h-4 rounded bg-white/5 border-white/10 text-amber-600 focus:ring-amber-500"
            />
            <label htmlFor="hasHeader" className="text-xs text-slate-300">
              First row contains headers
            </label>
          </div>
        ) : (
          <>
            {operation === 'write' && (
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="clearExisting"
                  checked={clearExisting}
                  onChange={(e) => setClearExisting(e.target.checked)}
                  className="w-4 h-4 rounded bg-white/5 border-white/10 text-amber-600 focus:ring-amber-500"
                />
                <label htmlFor="clearExisting" className="text-xs text-slate-300">
                  Clear existing data before writing
                </label>
              </div>
            )}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="includeHeader"
                checked={includeHeader}
                onChange={(e) => setIncludeHeader(e.target.checked)}
                className="w-4 h-4 rounded bg-white/5 border-white/10 text-amber-600 focus:ring-amber-500"
              />
              <label htmlFor="includeHeader" className="text-xs text-slate-300">
                Include header row
              </label>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
