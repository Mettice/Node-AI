/**
 * Enhanced Reddit Node Form Component
 * Provides OAuth connection and Reddit operation configuration
 */

import { useState, useEffect, useRef } from 'react';
import { SelectWithIcons } from '@/components/common/SelectWithIcons';
import { ProviderIcon } from '@/components/common/ProviderIcon';
import { initOAuthFlow, exchangeOAuthCode, listOAuthTokens, deleteOAuthToken } from '@/services/oauth';
import { APIKeyInput } from './APIKeyInput';
import { Search, MessageSquare, FileText, List } from 'lucide-react';

interface RedditNodeFormProps {
  initialData: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
  schema?: Record<string, any>;
}

const REDDIT_OPERATIONS = [
  { value: 'fetch_posts', label: 'Fetch Posts', icon: 'reddit' },
  { value: 'fetch_comments', label: 'Fetch Comments', icon: 'reddit' },
  { value: 'search', label: 'Search Reddit', icon: 'reddit' },
  { value: 'get_post', label: 'Get Post', icon: 'reddit' },
];

const REDDIT_SCOPES = [
  'read',
  'identity',
];

const SORT_OPTIONS = [
  { value: 'hot', label: 'Hot', icon: 'api' },
  { value: 'new', label: 'New', icon: 'api' },
  { value: 'top', label: 'Top', icon: 'api' },
  { value: 'rising', label: 'Rising', icon: 'api' },
  { value: 'relevance', label: 'Relevance', icon: 'api' },
  { value: 'comments', label: 'Comments', icon: 'api' },
];

const COMMENT_SORT_OPTIONS = [
  { value: 'top', label: 'Top', icon: 'api' },
  { value: 'best', label: 'Best', icon: 'api' },
  { value: 'new', label: 'New', icon: 'api' },
  { value: 'controversial', label: 'Controversial', icon: 'api' },
  { value: 'old', label: 'Old', icon: 'api' },
];

const TIME_FILTER_OPTIONS = [
  { value: 'hour', label: 'Hour', icon: 'api' },
  { value: 'day', label: 'Day', icon: 'api' },
  { value: 'week', label: 'Week', icon: 'api' },
  { value: 'month', label: 'Month', icon: 'api' },
  { value: 'year', label: 'Year', icon: 'api' },
  { value: 'all', label: 'All Time', icon: 'api' },
];

export function RedditNodeForm({ initialData, onChange }: RedditNodeFormProps) {
  const [operation, setOperation] = useState(initialData.reddit_operation || 'fetch_posts');
  const [tokenId, setTokenId] = useState(initialData.reddit_token_id || '');
  const [apiKey, setApiKey] = useState(initialData.reddit_api_key || '');
  const [subreddit, setSubreddit] = useState(initialData.reddit_subreddit || '');
  const [postId, setPostId] = useState(initialData.reddit_post_id || '');
  const [searchQuery, setSearchQuery] = useState(initialData.reddit_search_query || '');
  const [sort, setSort] = useState(initialData.reddit_sort || 'hot');
  const [commentSort, setCommentSort] = useState(initialData.reddit_comment_sort || 'top');
  const [timeFilter, setTimeFilter] = useState(initialData.reddit_time_filter || 'day');
  const [limit, setLimit] = useState(initialData.reddit_limit || 25);
  
  // OAuth connection state
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [redirectUri, setRedirectUri] = useState(window.location.origin + '/oauth/callback');
  const [availableTokens, setAvailableTokens] = useState<any[]>([]);
  const [isConnecting, setIsConnecting] = useState(false);
  const [authMethod, setAuthMethod] = useState<'oauth' | 'apikey'>(
    initialData.reddit_token_id ? 'oauth' : initialData.reddit_api_key ? 'apikey' : 'oauth'
  );
  
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

    // Only handle Reddit callbacks
    if (service !== 'reddit' && !code && !state) {
      return;
    }

    if (error) {
      alert(`OAuth error: ${error}`);
      window.history.replaceState({}, '', window.location.pathname);
      return;
    }

    if (code && state) {
      const storedState = sessionStorage.getItem('reddit_oauth_state');
      const clientId = sessionStorage.getItem('reddit_client_id');
      const clientSecret = sessionStorage.getItem('reddit_client_secret');
      const redirectUri = sessionStorage.getItem('reddit_redirect_uri');

      if (state !== storedState) {
        alert('Invalid OAuth state. Please try again.');
        sessionStorage.removeItem('reddit_oauth_state');
        sessionStorage.removeItem('reddit_client_id');
        sessionStorage.removeItem('reddit_client_secret');
        sessionStorage.removeItem('reddit_redirect_uri');
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
          service: 'reddit',
          code,
          state,
          client_id: clientId,
          client_secret: clientSecret,
          redirect_uri: redirectUri,
        });

        if (result.success && result.token_id) {
          setTokenId(result.token_id);
          setAuthMethod('oauth');
          await loadTokens();
          alert('Reddit connected successfully!');
        } else {
          alert(`Failed to connect: ${result.message || 'Unknown error'}`);
        }
      } catch (error: any) {
        alert(`Failed to exchange OAuth code: ${error.message}`);
      } finally {
        sessionStorage.removeItem('reddit_oauth_state');
        sessionStorage.removeItem('reddit_client_id');
        sessionStorage.removeItem('reddit_client_secret');
        sessionStorage.removeItem('reddit_redirect_uri');
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
      reddit_operation: operation,
    };

    // Add authentication
    if (authMethod === 'oauth' && tokenId) {
      config.reddit_token_id = tokenId;
    } else if (authMethod === 'apikey' && apiKey) {
      config.reddit_api_key = apiKey;
    }

    // Add operation-specific fields
    if (operation === 'fetch_posts' || operation === 'search') {
      if (subreddit) config.reddit_subreddit = subreddit;
      config.reddit_sort = sort;
      if (sort === 'top') {
        config.reddit_time_filter = timeFilter;
      }
      config.reddit_limit = limit;
    } else if (operation === 'fetch_comments' || operation === 'get_post') {
      if (postId) config.reddit_post_id = postId;
      if (operation === 'fetch_comments') {
        config.reddit_comment_sort = commentSort;
        config.reddit_limit = limit;
      }
    } else if (operation === 'search') {
      if (searchQuery) config.reddit_search_query = searchQuery;
      config.reddit_sort = sort;
      if (sort === 'top') {
        config.reddit_time_filter = timeFilter;
      }
      config.reddit_limit = limit;
    }

    onChangeRef.current(config);
  }, [operation, tokenId, apiKey, authMethod, subreddit, postId, searchQuery, sort, commentSort, timeFilter, limit]);

  const loadTokens = async () => {
    try {
      const tokens = await listOAuthTokens('reddit');
      setAvailableTokens(tokens);
      if (!tokenId && tokens.length > 0) {
        const validToken = tokens.find(t => t.is_valid);
        if (validToken) {
          setTokenId(validToken.token_id);
          setAuthMethod('oauth');
        }
      }
    } catch (error) {
      console.error('Failed to load Reddit tokens:', error);
    }
  };

  const handleConnectReddit = async () => {
    if (!clientId) {
      alert('Please enter Reddit Client ID');
      return;
    }

    setIsConnecting(true);
    try {
      const result = await initOAuthFlow({
        service: 'reddit',
        client_id: clientId,
        redirect_uri: redirectUri,
        scopes: REDDIT_SCOPES,
      });

      sessionStorage.setItem('reddit_oauth_state', result.state);
      sessionStorage.setItem('reddit_client_id', clientId);
      sessionStorage.setItem('reddit_client_secret', clientSecret);
      sessionStorage.setItem('reddit_redirect_uri', redirectUri);

      window.location.href = result.authorization_url;
    } catch (error: any) {
      alert(`Failed to initiate OAuth: ${error.message}`);
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!tokenId) return;
    
    if (confirm('Are you sure you want to disconnect this Reddit account?')) {
      try {
        await deleteOAuthToken(tokenId);
        setTokenId('');
        setAuthMethod('apikey');
        await loadTokens();
      } catch (error) {
        alert('Failed to disconnect Reddit account');
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
          options={REDDIT_OPERATIONS}
          placeholder="Select operation..."
        />
      </div>

      {/* Authentication Method */}
      <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <ProviderIcon provider="reddit" size="sm" />
          <h3 className="text-sm font-semibold text-white">Authentication</h3>
        </div>

        <div className="flex gap-2 mb-3">
          <button
            type="button"
            onClick={() => setAuthMethod('oauth')}
            className={`flex-1 px-3 py-2 rounded-lg transition-all text-sm font-medium ${
              authMethod === 'oauth'
                ? 'bg-purple-600 text-white'
                : 'bg-white/5 text-slate-300 hover:bg-white/10'
            }`}
          >
            OAuth
          </button>
          <button
            type="button"
            onClick={() => setAuthMethod('apikey')}
            className={`flex-1 px-3 py-2 rounded-lg transition-all text-sm font-medium ${
              authMethod === 'apikey'
                ? 'bg-purple-600 text-white'
                : 'bg-white/5 text-slate-300 hover:bg-white/10'
            }`}
          >
            API Key
          </button>
        </div>

        {authMethod === 'oauth' ? (
          <>
            {tokenId && selectedToken ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 bg-green-500/10 border border-green-500/30 rounded">
                  <div className="flex items-center gap-2">
                    <ProviderIcon provider="reddit" size="sm" />
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
                  Connect your Reddit account using OAuth. You'll need to create a Reddit app and get OAuth credentials.
                </p>
                
                <div className="space-y-2">
                  <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                    Client ID <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    value={clientId}
                    onChange={(e) => setClientId(e.target.value)}
                    placeholder="Your_Reddit_Client_ID"
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
                    placeholder="Enter Reddit Client Secret"
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
                  onClick={handleConnectReddit}
                  disabled={isConnecting || !clientId || !clientSecret}
                  className="w-full px-3 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg transition-all text-sm font-medium flex items-center justify-center gap-2"
                >
                  {isConnecting ? (
                    <>Connecting...</>
                  ) : (
                    <>
                      <ProviderIcon provider="reddit" size="sm" />
                      Connect Reddit Account
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
          </>
        ) : (
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              API Key <span className="text-red-400">*</span>
            </label>
            <p className="text-xs text-slate-400 -mt-1">
              Reddit API key for read-only access (simpler setup, no OAuth required)
            </p>
            <APIKeyInput
              value={apiKey}
              onChange={setApiKey}
              placeholder="Enter Reddit API key"
            />
          </div>
        )}
      </div>

      {/* Operation-Specific Fields */}
      {(operation === 'fetch_posts' || operation === 'search') && (
        <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            {operation === 'fetch_posts' ? <List className="w-4 h-4" /> : <Search className="w-4 h-4" />}
            {operation === 'fetch_posts' ? 'Posts Configuration' : 'Search Configuration'}
          </h3>
          
          {operation === 'search' && (
            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                Search Query <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="python programming"
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              />
            </div>
          )}

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Subreddit {operation === 'fetch_posts' && <span className="text-red-400">*</span>}
            </label>
            <p className="text-xs text-slate-400 -mt-1">
              Subreddit name without r/ prefix (leave empty to search all of Reddit)
            </p>
            <input
              type="text"
              value={subreddit}
              onChange={(e) => setSubreddit(e.target.value)}
              placeholder="python or leave empty for all"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                Sort
              </label>
              <SelectWithIcons
                value={sort}
                onChange={setSort}
                options={SORT_OPTIONS}
                placeholder="Select sort..."
              />
            </div>

            {sort === 'top' && (
              <div className="space-y-2">
                <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                  Time Filter
                </label>
                <SelectWithIcons
                  value={timeFilter}
                  onChange={setTimeFilter}
                  options={TIME_FILTER_OPTIONS}
                  placeholder="Select time..."
                />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Limit
            </label>
            <input
              type="number"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value) || 25)}
              min={1}
              max={100}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>
        </div>
      )}

      {operation === 'fetch_comments' && (
        <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Comments Configuration
          </h3>
          
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Post ID <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={postId}
              onChange={(e) => setPostId(e.target.value)}
              placeholder="abc123 or t3_abc123"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                Comment Sort
              </label>
              <SelectWithIcons
                value={commentSort}
                onChange={setCommentSort}
                options={COMMENT_SORT_OPTIONS}
                placeholder="Select sort..."
              />
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                Limit
              </label>
              <input
                type="number"
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value) || 25)}
                min={1}
                max={100}
                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              />
            </div>
          </div>
        </div>
      )}

      {operation === 'get_post' && (
        <div className="space-y-3 p-3 bg-white/5 border border-white/10 rounded-lg">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Post Configuration
          </h3>
          
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
              Post ID <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={postId}
              onChange={(e) => setPostId(e.target.value)}
              placeholder="abc123 or t3_abc123"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
            />
          </div>
        </div>
      )}
    </div>
  );
}

