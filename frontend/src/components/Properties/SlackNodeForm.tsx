/**
 * Enhanced Slack Node Form Component
 * Provides OAuth connection and Slack operation configuration
 */

import { useState, useEffect, useRef } from 'react';
import { SelectWithIcons } from '@/components/common/SelectWithIcons';
import { ProviderIcon } from '@/components/common/ProviderIcon';
import { initOAuthFlow, exchangeOAuthCode, listOAuthTokens, deleteOAuthToken } from '@/services/oauth';
import { MessageSquare, Hash, Upload } from 'lucide-react';

interface SlackNodeFormProps {
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
  schema?: Record<string, any>;
}

const SLACK_OPERATIONS = [
  { value: 'send_message', label: 'Send Message', icon: 'slack' },
  { value: 'create_channel', label: 'Create Channel', icon: 'slack' },
  { value: 'post_to_channel', label: 'Post to Channel', icon: 'slack' },
  { value: 'upload_file', label: 'Upload File', icon: 'slack' },
];

const SLACK_SCOPES = [
  'chat:write',
  'channels:write',
  'files:write',
  'users:read',
];

export function SlackNodeForm({ initialData, onChange }: SlackNodeFormProps) {
  const [operation, setOperation] = useState(initialData.slack_operation || 'send_message');
  const [tokenId, setTokenId] = useState(initialData.slack_token_id || '');
  const [channel, setChannel] = useState(initialData.slack_channel || '');
  const [message, setMessage] = useState(initialData.slack_message || '');
  const [channelName, setChannelName] = useState(initialData.slack_channel_name || '');
  const [isPrivate, setIsPrivate] = useState(initialData.slack_is_private || false);
  const [filename, setFilename] = useState(initialData.slack_filename || '');
  const [fileContent, setFileContent] = useState(initialData.slack_file_content || '');
  const [fileTitle, setFileTitle] = useState(initialData.slack_file_title || '');
  const [initialComment, setInitialComment] = useState(initialData.slack_initial_comment || '');
  
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

    // Only handle Slack callbacks
    if (service !== 'slack' && !code && !state) {
      return;
    }

    if (error) {
      alert(`OAuth error: ${error}`);
      // Clean up URL
      window.history.replaceState({}, '', window.location.pathname);
      return;
    }

    if (code && state) {
      // Get stored OAuth data
      const storedState = sessionStorage.getItem('slack_oauth_state');
      const clientId = sessionStorage.getItem('slack_client_id');
      const clientSecret = sessionStorage.getItem('slack_client_secret');
      const redirectUri = sessionStorage.getItem('slack_redirect_uri');

      if (state !== storedState) {
        alert('Invalid OAuth state. Please try again.');
        // Clean up
        sessionStorage.removeItem('slack_oauth_state');
        sessionStorage.removeItem('slack_client_id');
        sessionStorage.removeItem('slack_client_secret');
        sessionStorage.removeItem('slack_redirect_uri');
        window.history.replaceState({}, '', window.location.pathname);
        return;
      }

      if (!clientId || !clientSecret || !redirectUri) {
        alert('OAuth session expired. Please try connecting again.');
        window.history.replaceState({}, '', window.location.pathname);
        return;
      }

      try {
        // Exchange code for token
        const result = await exchangeOAuthCode({
          service: 'slack',
          code,
          state,
          client_id: clientId,
          client_secret: clientSecret,
          redirect_uri: redirectUri,
        });

        if (result.success && result.token_id) {
          setTokenId(result.token_id);
          await loadTokens();
          alert('Slack connected successfully!');
        } else {
          alert(`Failed to connect: ${result.message || 'Unknown error'}`);
        }
      } catch (error: any) {
        alert(`Failed to exchange OAuth code: ${error.message}`);
      } finally {
        // Clean up
        sessionStorage.removeItem('slack_oauth_state');
        sessionStorage.removeItem('slack_client_id');
        sessionStorage.removeItem('slack_client_secret');
        sessionStorage.removeItem('slack_redirect_uri');
        // Clean up URL
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
      slack_operation: operation,
      slack_token_id: tokenId,
    };

    // Add operation-specific fields
    if (operation === 'send_message' || operation === 'post_to_channel') {
      if (channel) config.slack_channel = channel;
      if (message) config.slack_message = message;
    } else if (operation === 'create_channel') {
      if (channelName) config.slack_channel_name = channelName;
      config.slack_is_private = isPrivate;
    } else if (operation === 'upload_file') {
      if (channel) config.slack_channel = channel;
      if (filename) config.slack_filename = filename;
      if (fileContent) config.slack_file_content = fileContent;
      if (fileTitle) config.slack_file_title = fileTitle;
      if (initialComment) config.slack_initial_comment = initialComment;
    }

    onChangeRef.current(config);
  }, [operation, tokenId, channel, message, channelName, isPrivate, filename, fileContent, fileTitle, initialComment]);

  const loadTokens = async () => {
    try {
      const tokens = await listOAuthTokens('slack');
      setAvailableTokens(tokens);
      // Auto-select first valid token if none selected
      if (!tokenId && tokens.length > 0) {
        const validToken = tokens.find(t => t.is_valid);
        if (validToken) {
          setTokenId(validToken.token_id);
        }
      }
    } catch (error) {
      console.error('Failed to load Slack tokens:', error);
    }
  };

  const handleConnectSlack = async () => {
    if (!clientId) {
      alert('Please enter Slack Client ID');
      return;
    }

    setIsConnecting(true);
    try {
      const result = await initOAuthFlow({
        service: 'slack',
        client_id: clientId,
        redirect_uri: redirectUri,
        scopes: SLACK_SCOPES,
      });

      // Store client secret in sessionStorage for callback
      sessionStorage.setItem('slack_oauth_state', result.state);
      sessionStorage.setItem('slack_client_id', clientId);
      sessionStorage.setItem('slack_client_secret', clientSecret);
      sessionStorage.setItem('slack_redirect_uri', redirectUri);

      // Redirect to Slack OAuth
      window.location.href = result.authorization_url;
    } catch (error: any) {
      alert(`Failed to initiate OAuth: ${error.message}`);
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!tokenId) return;
    
    if (confirm('Are you sure you want to disconnect this Slack account?')) {
      try {
        await deleteOAuthToken(tokenId);
        setTokenId('');
        await loadTokens();
      } catch (error) {
        alert('Failed to disconnect Slack account');
      }
    }
  };

  const selectedToken = availableTokens.find(t => t.token_id === tokenId);

  return (
    <div className="space-y-4">
      {/* Operation Selector */}
      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          Operation <span className="text-red-400">*</span>
        </label>
        <SelectWithIcons
          value={operation}
          onChange={setOperation}
          options={SLACK_OPERATIONS}
          placeholder="Select operation..."
        />
      </div>

      {/* OAuth Connection */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <ProviderIcon provider="slack" size="sm" />
          <h3 className="text-sm font-semibold text-white">Slack Connection</h3>
        </div>

        {tokenId && selectedToken ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-green-500/10 border border-green-500/30 rounded">
              <div className="flex items-center gap-2">
                <ProviderIcon provider="slack" size="sm" />
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
              Connect your Slack workspace to use Slack operations. You'll need to create a Slack App and get OAuth credentials.
            </p>
            
            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                Client ID <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                placeholder="1234567890.1234567890123"
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
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
                placeholder="Enter Slack Client Secret"
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                Redirect URI
              </label>
              <input
                type="text"
                value={redirectUri}
                onChange={(e) => setRedirectUri(e.target.value)}
                placeholder={window.location.origin + '/oauth/callback'}
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all text-xs"
              />
            </div>

            <button
              type="button"
              onClick={handleConnectSlack}
              disabled={isConnecting || !clientId || !clientSecret}
              className="w-full px-3 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg transition-all text-sm font-medium flex items-center justify-center gap-2"
            >
              {isConnecting ? (
                <>Connecting...</>
              ) : (
                <>
                  <ProviderIcon provider="slack" size="sm" />
                  Connect Slack Workspace
                </>
              )}
            </button>
          </div>
        )}

        {/* Token Selector (if multiple tokens) */}
        {availableTokens.length > 1 && (
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Select Connection
            </label>
            <select
              value={tokenId}
              onChange={(e) => setTokenId(e.target.value)}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
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

      {/* Operation-Specific Fields */}
      {(operation === 'send_message' || operation === 'post_to_channel') && (
        <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Message Configuration
          </h3>
          
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Channel/User ID <span className="text-red-400">*</span>
            </label>
            <p className="text-xs text-slate-400 -mt-1">
              Slack channel ID (e.g., C1234567890) or user ID (e.g., U1234567890)
            </p>
            <input
              type="text"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              placeholder="C1234567890 or U1234567890"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Message <span className="text-red-400">*</span>
            </label>
            <p className="text-xs text-slate-400 -mt-1">
              Message text (can also come from previous node)
            </p>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Your message here..."
              rows={6}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>
        </div>
      )}

      {operation === 'create_channel' && (
        <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Hash className="w-4 h-4" />
            Channel Configuration
          </h3>
          
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Channel Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={channelName}
              onChange={(e) => setChannelName(e.target.value)}
              placeholder="my-channel"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="slack_is_private"
              checked={isPrivate}
              onChange={(e) => setIsPrivate(e.target.checked)}
              className="w-4 h-4 rounded bg-white/5 border-white/10 text-purple-600 focus:ring-purple-500"
            />
            <label htmlFor="slack_is_private" className="text-sm text-slate-300">
              Create as private channel
            </label>
          </div>
        </div>
      )}

      {operation === 'upload_file' && (
        <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Upload className="w-4 h-4" />
            File Upload Configuration
          </h3>
          
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Channel ID <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              placeholder="C1234567890"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Filename <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              placeholder="document.pdf"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              File Content <span className="text-red-400">*</span>
            </label>
            <p className="text-xs text-slate-400 -mt-1">
              File content (text or base64 encoded) - can also come from previous node
            </p>
            <textarea
              value={fileContent}
              onChange={(e) => setFileContent(e.target.value)}
              placeholder="File content here..."
              rows={8}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all font-mono text-sm"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              File Title (Optional)
            </label>
            <input
              type="text"
              value={fileTitle}
              onChange={(e) => setFileTitle(e.target.value)}
              placeholder="Document Title"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Initial Comment (Optional)
            </label>
            <textarea
              value={initialComment}
              onChange={(e) => setInitialComment(e.target.value)}
              placeholder="Comment to post with file..."
              rows={3}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>
        </div>
      )}
    </div>
  );
}

