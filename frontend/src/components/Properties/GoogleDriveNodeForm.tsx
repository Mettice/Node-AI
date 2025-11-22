/**
 * Enhanced Google Drive Node Form Component
 * Provides OAuth connection and Google Drive operation configuration
 */

import { useState, useEffect, useRef } from 'react';
import { SelectWithIcons } from '@/components/common/SelectWithIcons';
import { ProviderIcon } from '@/components/common/ProviderIcon';
import { initOAuthFlow, exchangeOAuthCode, listOAuthTokens, deleteOAuthToken } from '@/services/oauth';
import { Upload, Download, Folder, Share2, List } from 'lucide-react';

interface GoogleDriveNodeFormProps {
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
  schema?: Record<string, any>;
}

const GOOGLE_DRIVE_OPERATIONS = [
  { value: 'list', label: 'List Files', icon: 'googledrive' },
  { value: 'upload', label: 'Upload File', icon: 'googledrive' },
  { value: 'download', label: 'Download File', icon: 'googledrive' },
  { value: 'share', label: 'Share File', icon: 'googledrive' },
  { value: 'create_folder', label: 'Create Folder', icon: 'googledrive' },
];

const GOOGLE_DRIVE_SCOPES = [
  'https://www.googleapis.com/auth/drive.file',
  'https://www.googleapis.com/auth/drive.readonly',
];

const SHARE_ROLES = [
  { value: 'reader', label: 'Reader', icon: 'api' },
  { value: 'writer', label: 'Writer', icon: 'api' },
  { value: 'commenter', label: 'Commenter', icon: 'api' },
];

const SHARE_TYPES = [
  { value: 'user', label: 'User', icon: 'api' },
  { value: 'group', label: 'Group', icon: 'api' },
  { value: 'domain', label: 'Domain', icon: 'api' },
  { value: 'anyone', label: 'Anyone', icon: 'api' },
];

export function GoogleDriveNodeForm({ initialData, onChange }: GoogleDriveNodeFormProps) {
  const [operation, setOperation] = useState(initialData.google_drive_operation || 'list');
  const [tokenId, setTokenId] = useState(initialData.google_drive_token_id || '');
  const [fileId, setFileId] = useState(initialData.google_drive_file_id || '');
  const [filename, setFilename] = useState(initialData.google_drive_filename || '');
  const [fileContent, setFileContent] = useState(initialData.google_drive_file_content || '');
  const [folderId, setFolderId] = useState(initialData.google_drive_folder_id || 'root');
  const [folderName, setFolderName] = useState(initialData.google_drive_folder_name || '');
  const [parentFolderId, setParentFolderId] = useState(initialData.google_drive_parent_folder_id || 'root');
  const [mimeType, setMimeType] = useState(initialData.google_drive_mime_type || 'text/plain');
  const [query, setQuery] = useState(initialData.google_drive_query || '');
  const [maxResults, setMaxResults] = useState(initialData.google_drive_max_results || 100);
  const [shareEmail, setShareEmail] = useState(initialData.google_drive_share_email || '');
  const [shareRole, setShareRole] = useState(initialData.google_drive_share_role || 'reader');
  const [shareType, setShareType] = useState(initialData.google_drive_share_type || 'user');
  
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
          alert('Google Drive connected successfully!');
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
      google_drive_operation: operation,
      google_drive_token_id: tokenId,
    };

    // Add operation-specific fields
    if (operation === 'upload') {
      if (filename) config.google_drive_filename = filename;
      if (fileContent) config.google_drive_file_content = fileContent;
      if (folderId) config.google_drive_folder_id = folderId;
      if (mimeType) config.google_drive_mime_type = mimeType;
    } else if (operation === 'download' || operation === 'share') {
      if (fileId) config.google_drive_file_id = fileId;
      if (operation === 'share') {
        if (shareEmail) config.google_drive_share_email = shareEmail;
        config.google_drive_share_role = shareRole;
        config.google_drive_share_type = shareType;
      }
    } else if (operation === 'list') {
      if (folderId) config.google_drive_folder_id = folderId;
      if (query) config.google_drive_query = query;
      config.google_drive_max_results = maxResults;
    } else if (operation === 'create_folder') {
      if (folderName) config.google_drive_folder_name = folderName;
      if (parentFolderId) config.google_drive_parent_folder_id = parentFolderId;
    }

    onChangeRef.current(config);
  }, [operation, tokenId, fileId, filename, fileContent, folderId, folderName, parentFolderId, mimeType, query, maxResults, shareEmail, shareRole, shareType]);

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
        scopes: GOOGLE_DRIVE_SCOPES,
      });

      sessionStorage.setItem('google_oauth_state', result.state);
      sessionStorage.setItem('google_client_id', clientId);
      sessionStorage.setItem('google_client_secret', clientSecret);
      sessionStorage.setItem('google_redirect_uri', redirectUri);

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
      {/* Operation Selector */}
      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
          Operation <span className="text-red-400">*</span>
        </label>
        <SelectWithIcons
          value={operation}
          onChange={setOperation}
          options={GOOGLE_DRIVE_OPERATIONS}
          placeholder="Select operation..."
        />
      </div>

      {/* OAuth Connection */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <ProviderIcon provider="googledrive" size="sm" />
          <h3 className="text-sm font-semibold text-white">Google Drive Connection</h3>
        </div>

        {tokenId && selectedToken ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-green-500/10 border border-green-500/30 rounded">
              <div className="flex items-center gap-2">
                <ProviderIcon provider="googledrive" size="sm" />
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
              Connect your Google account to use Google Drive operations. You'll need to create a Google Cloud project and OAuth credentials.
            </p>
            
            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                Client ID <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                placeholder="1234567890-abc123def456.apps.googleusercontent.com"
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
                placeholder="Enter Google Client Secret"
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
              onClick={handleConnectGoogle}
              disabled={isConnecting || !clientId || !clientSecret}
              className="w-full px-3 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg transition-all text-sm font-medium flex items-center justify-center gap-2"
            >
              {isConnecting ? (
                <>Connecting...</>
              ) : (
                <>
                  <ProviderIcon provider="googledrive" size="sm" />
                  Connect Google Account
                </>
              )}
            </button>
          </div>
        )}

        {/* Token Selector */}
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
      {operation === 'list' && (
        <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <List className="w-4 h-4" />
            List Configuration
          </h3>
          
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Folder ID
            </label>
            <p className="text-xs text-slate-400 -mt-1">
              Google Drive folder ID (default: 'root' for My Drive)
            </p>
            <input
              type="text"
              value={folderId}
              onChange={(e) => setFolderId(e.target.value)}
              placeholder="root or folder_id"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Search Query (Optional)
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="name contains 'document'"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Max Results
            </label>
            <input
              type="number"
              value={maxResults}
              onChange={(e) => setMaxResults(parseInt(e.target.value) || 100)}
              min={1}
              max={1000}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>
        </div>
      )}

      {operation === 'upload' && (
        <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Upload className="w-4 h-4" />
            Upload Configuration
          </h3>
          
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

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                Folder ID
              </label>
              <input
                type="text"
                value={folderId}
                onChange={(e) => setFolderId(e.target.value)}
                placeholder="root"
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                MIME Type
              </label>
              <input
                type="text"
                value={mimeType}
                onChange={(e) => setMimeType(e.target.value)}
                placeholder="text/plain"
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              />
            </div>
          </div>
        </div>
      )}

      {(operation === 'download' || operation === 'share') && (
        <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            {operation === 'download' ? <Download className="w-4 h-4" /> : <Share2 className="w-4 h-4" />}
            {operation === 'download' ? 'Download' : 'Share'} Configuration
          </h3>
          
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              File ID <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={fileId}
              onChange={(e) => setFileId(e.target.value)}
              placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>

          {operation === 'share' && (
            <>
              <div className="space-y-2">
                <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                  Email (for user sharing)
                </label>
                <input
                  type="email"
                  value={shareEmail}
                  onChange={(e) => setShareEmail(e.target.value)}
                  placeholder="user@example.com"
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                    Share Role
                  </label>
                  <SelectWithIcons
                    value={shareRole}
                    onChange={setShareRole}
                    options={SHARE_ROLES}
                    placeholder="Select role..."
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                    Share Type
                  </label>
                  <SelectWithIcons
                    value={shareType}
                    onChange={setShareType}
                    options={SHARE_TYPES}
                    placeholder="Select type..."
                  />
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {operation === 'create_folder' && (
        <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Folder className="w-4 h-4" />
            Folder Configuration
          </h3>
          
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Folder Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              placeholder="My Folder"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Parent Folder ID
            </label>
            <p className="text-xs text-slate-400 -mt-1">
              Parent folder ID (default: 'root' for My Drive)
            </p>
            <input
              type="text"
              value={parentFolderId}
              onChange={(e) => setParentFolderId(e.target.value)}
              placeholder="root"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>
        </div>
      )}
    </div>
  );
}

