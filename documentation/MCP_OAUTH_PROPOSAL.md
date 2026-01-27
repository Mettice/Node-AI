# MCP OAuth Integration Proposal

## 🎯 Goal

Enable **one-click OAuth authentication** for MCP integrations (like Claude's code integrations), eliminating the need for users to manually enter API keys.

**Current Flow:**
```
User → Enter API Key → Save → Connect
```

**Proposed Flow (Like Claude):**
```
User → Click "Connect" → OAuth Popup → Grant Permission → Connected ✅
```

---

## 📊 Current State Analysis

### ✅ What You Already Have

1. **OAuth Infrastructure**
   - `backend/api/oauth.py` - OAuth API endpoints
   - `backend/core/oauth.py` - OAuth manager
   - OAuth flows for Google, Slack, Reddit (in node forms)
   - Token storage system

2. **MCP Server Presets**
   - Already marked with `auth_type: "oauth"` for:
     - `google-drive` (OAuth)
     - `gmail` (OAuth)
     - `google-calendar` (OAuth)
   - Currently still requires manual credentials

3. **Frontend OAuth Components**
   - `GoogleDriveNodeForm.tsx` - Has OAuth connect button
   - `SlackNodeForm.tsx` - Has OAuth connect button
   - `GoogleSheetsNodeForm.tsx` - Has OAuth connect button

### ❌ What's Missing

1. **MCP-Specific OAuth Flow**
   - No OAuth integration in MCP server connection
   - Still requires `env_values` (API keys) in `AddServerFromPresetRequest`
   - No "Connect" button in MCP UI

2. **Service-Specific OAuth Handlers**
   - Need OAuth handlers for each MCP service
   - Need to convert OAuth tokens to MCP server env vars
   - Need token refresh logic for MCP servers

3. **Frontend MCP UI**
   - MCP server list doesn't show OAuth connect option
   - No OAuth callback handling for MCP connections

---

## 🏗️ Proposed Architecture

### **1. OAuth Flow for MCP Servers**

```
┌─────────────────────────────────────────────────────────────┐
│                    User Clicks "Connect"                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend: Check auth_type                                    │
│  - If "oauth" → Initiate OAuth flow                         │
│  - If "api_key" → Show API key form (current behavior)      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼ (OAuth path)
┌─────────────────────────────────────────────────────────────┐
│  Frontend: Open OAuth popup/redirect                         │
│  - Google: Redirect to Google OAuth                          │
│  - Slack: Redirect to Slack OAuth                            │
│  - Calendar: Redirect to Google OAuth (Calendar scopes)     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  User Grants Permission                                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  OAuth Callback → Exchange Code for Tokens                   │
│  - Store tokens in oauth_tokens table                        │
│  - Link token_id to MCP server config                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Convert OAuth Tokens to MCP Server Env Vars                │
│  - Google: access_token → GDRIVE_CREDENTIALS_PATH           │
│  - Gmail: access_token → GMAIL_ACCESS_TOKEN                 │
│  - Calendar: access_token → GOOGLE_CALENDAR_TOKEN            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Connect MCP Server with OAuth Credentials                   │
│  - Server starts with OAuth tokens as env vars               │
│  - Tools become available                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Plan

### **Phase 1: Backend OAuth Integration**

#### **1.1 Extend MCP Server Presets**

Update `backend/core/mcp/server_manager.py`:

```python
MCP_SERVER_PRESETS = {
    "google-drive": {
        # ... existing config ...
        "auth_type": "oauth",
        "oauth_service": "google",  # NEW: Which OAuth service to use
        "oauth_scopes": [  # NEW: Required OAuth scopes
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/drive.metadata.readonly",
        ],
        "oauth_to_env_mapping": {  # NEW: How to convert OAuth token to env vars
            "access_token": "GDRIVE_ACCESS_TOKEN",
            "refresh_token": "GDRIVE_REFRESH_TOKEN",
            # OR for credential files:
            "credential_file": "GDRIVE_CREDENTIALS_PATH",
        },
    },
    "gmail": {
        # ... existing config ...
        "auth_type": "oauth",
        "oauth_service": "google",
        "oauth_scopes": [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
        ],
        "oauth_to_env_mapping": {
            "access_token": "GMAIL_ACCESS_TOKEN",
            "refresh_token": "GMAIL_REFRESH_TOKEN",
        },
    },
    "google-calendar": {
        # ... existing config ...
        "auth_type": "oauth",
        "oauth_service": "google",
        "oauth_scopes": [
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events",
        ],
        "oauth_to_env_mapping": {
            "access_token": "GOOGLE_CALENDAR_ACCESS_TOKEN",
            "refresh_token": "GOOGLE_CALENDAR_REFRESH_TOKEN",
        },
    },
    "slack": {
        # ... existing config ...
        "auth_type": "oauth",  # Change from "api_key"
        "oauth_service": "slack",
        "oauth_scopes": [
            "channels:read",
            "chat:write",
            "users:read",
        ],
        "oauth_to_env_mapping": {
            "access_token": "SLACK_BOT_TOKEN",
            "team_id": "SLACK_TEAM_ID",  # From metadata
        },
    },
}
```

#### **1.2 New API Endpoint: OAuth Connect for MCP**

Add to `backend/api/mcp.py`:

```python
@router.post("/servers/{server_name}/oauth/connect")
async def connect_mcp_with_oauth(
    server_name: str,
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """
    Initiate OAuth flow for an MCP server.
    
    Returns authorization URL for user to grant permission.
    """
    manager = get_server_manager(user_id)
    preset = MCP_SERVER_PRESETS.get(server_name)
    
    if not preset:
        raise HTTPException(404, f"Server {server_name} not found")
    
    if preset.get("auth_type") != "oauth":
        raise HTTPException(400, f"Server {server_name} does not support OAuth")
    
    # Get OAuth service and scopes from preset
    oauth_service = preset.get("oauth_service")
    oauth_scopes = preset.get("oauth_scopes", [])
    
    # Generate OAuth state (store server_name in state)
    state = f"mcp_{server_name}_{generate_random_string()}"
    
    # Store state in session/cache (link to server_name and user_id)
    await store_oauth_state(state, {
        "server_name": server_name,
        "user_id": user_id,
        "preset": preset,
    })
    
    # Get authorization URL
    auth_url = OAuthManager.get_authorization_url(
        service=oauth_service,
        client_id=get_oauth_client_id(oauth_service),  # From config/env
        redirect_uri=f"{settings.frontend_url}/mcp/oauth/callback",
        scopes=oauth_scopes,
        state=state,
    )
    
    return {
        "authorization_url": auth_url,
        "state": state,
    }


@router.get("/oauth/callback")
async def mcp_oauth_callback(
    code: str,
    state: str,
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> Dict[str, Any]:
    """
    Handle OAuth callback for MCP server connection.
    
    Exchanges code for tokens and configures MCP server.
    """
    # Retrieve state data
    state_data = await retrieve_oauth_state(state)
    if not state_data:
        raise HTTPException(400, "Invalid or expired OAuth state")
    
    server_name = state_data["server_name"]
    preset = state_data["preset"]
    oauth_service = preset.get("oauth_service")
    
    # Exchange code for tokens
    token_data = await exchange_oauth_code(
        service=oauth_service,
        code=code,
        redirect_uri=f"{settings.frontend_url}/mcp/oauth/callback",
    )
    
    # Store OAuth token
    token_id = OAuthManager.store_token(
        service=oauth_service,
        user_id=user_id,
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        expires_in=token_data.get("expires_in"),
        metadata={
            "mcp_server": server_name,
            **token_data.get("metadata", {}),
        },
    )
    
    # Convert OAuth tokens to MCP server env vars
    env_vars = convert_oauth_to_mcp_env(
        preset=preset,
        token_data=token_data,
        token_id=token_id,
    )
    
    # Add/update MCP server with OAuth credentials
    manager = get_server_manager(user_id)
    connection = manager.add_server_from_preset(
        preset_name=server_name,
        env_values=env_vars,  # OAuth-derived env vars
        custom_name=None,
    )
    
    # Auto-connect
    await manager.connect_server(server_name)
    
    return {
        "success": True,
        "server": {
            "name": connection.name,
            "connected": connection.connected,
            "tools_count": connection.tools_count,
        },
        "token_id": token_id,
    }
```

#### **1.3 Helper Functions**

```python
def convert_oauth_to_mcp_env(
    preset: Dict[str, Any],
    token_data: Dict[str, Any],
    token_id: str,
) -> Dict[str, str]:
    """
    Convert OAuth token data to MCP server environment variables.
    
    Handles different token formats:
    - Direct access tokens (Gmail, Calendar)
    - Credential files (Google Drive)
    - Token + metadata (Slack)
    """
    mapping = preset.get("oauth_to_env_mapping", {})
    env_vars = {}
    
    # For Google Drive: Create credentials file
    if preset["name"] == "google-drive":
        credentials_path = create_google_credentials_file(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_id=token_id,
        )
        env_vars["GDRIVE_CREDENTIALS_PATH"] = credentials_path
    
    # For Gmail/Calendar: Direct token
    elif preset["name"] in ["gmail", "google-calendar"]:
        env_vars["ACCESS_TOKEN"] = token_data["access_token"]
        if token_data.get("refresh_token"):
            env_vars["REFRESH_TOKEN"] = token_data["refresh_token"]
    
    # For Slack: Token + team_id
    elif preset["name"] == "slack":
        env_vars["SLACK_BOT_TOKEN"] = token_data["access_token"]
        if "team_id" in token_data.get("metadata", {}):
            env_vars["SLACK_TEAM_ID"] = token_data["metadata"]["team_id"]
    
    return env_vars
```

---

### **Phase 2: Frontend UI Changes**

#### **2.1 MCP Server List Component**

Update `frontend/src/components/MCP/MCPServerList.tsx`:

```tsx
interface MCPServerCardProps {
  server: MCPServerPreset;
  isConnected: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
}

function MCPServerCard({ server, isConnected, onConnect, onDisconnect }: MCPServerCardProps) {
  const [isConnecting, setIsConnecting] = useState(false);
  
  const handleConnect = async () => {
    if (server.auth_type === 'oauth') {
      // OAuth flow
      setIsConnecting(true);
      try {
        const response = await fetch(`/api/v1/mcp/servers/${server.name}/oauth/connect`, {
          method: 'POST',
        });
        const data = await response.json();
        
        // Redirect to OAuth provider
        window.location.href = data.authorization_url;
      } catch (error) {
        alert('Failed to initiate OAuth flow');
        setIsConnecting(false);
      }
    } else {
      // API key flow (show form)
      onConnect();
    }
  };
  
  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div>
          <h3>{server.display_name}</h3>
          <p className="text-sm text-gray-500">{server.description}</p>
        </div>
        
        {server.auth_type === 'oauth' ? (
          // OAuth Connect Button
          <button
            onClick={handleConnect}
            disabled={isConnecting || isConnected}
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
            {isConnecting ? 'Connecting...' : isConnected ? 'Connected ✓' : 'Connect'}
          </button>
        ) : (
          // API Key Form (existing)
          <button onClick={onConnect}>Configure</button>
        )}
      </div>
    </div>
  );
}
```

#### **2.2 OAuth Callback Handler**

Create `frontend/src/pages/MCPOAuthCallback.tsx`:

```tsx
export function MCPOAuthCallback() {
  useEffect(() => {
    const handleCallback = async () => {
      const params = new URLSearchParams(window.location.search);
      const code = params.get('code');
      const state = params.get('state');
      
      if (!code || !state) {
        alert('OAuth callback missing parameters');
        return;
      }
      
      try {
        // Backend handles token exchange and MCP server setup
        const response = await fetch(`/api/v1/mcp/oauth/callback?code=${code}&state=${state}`);
        const data = await response.json();
        
        if (data.success) {
          // Redirect to MCP servers page with success message
          window.location.href = '/mcp/servers?connected=true';
        } else {
          alert('OAuth connection failed');
        }
      } catch (error) {
        alert('Failed to complete OAuth flow');
      }
    };
    
    handleCallback();
  }, []);
  
  return <div>Connecting...</div>;
}
```

---

### **Phase 3: Service-Specific OAuth Handlers**

#### **3.1 Google Services (Drive, Gmail, Calendar)**

```python
# backend/core/mcp/oauth_handlers.py

async def handle_google_oauth_for_mcp(
    preset_name: str,
    token_data: Dict[str, Any],
) -> Dict[str, str]:
    """
    Handle OAuth tokens for Google MCP servers.
    
    Different servers need different formats:
    - Google Drive: Credentials JSON file
    - Gmail: Direct access token
    - Calendar: Direct access token
    """
    if preset_name == "google-drive":
        # Create credentials file for Google Drive MCP server
        credentials = {
            "type": "authorized_user",
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": token_data["refresh_token"],
        }
        
        # Save to file
        credentials_path = save_credentials_file(
            credentials,
            filename=f"gdrive_{token_id}.json",
        )
        
        return {"GDRIVE_CREDENTIALS_PATH": credentials_path}
    
    elif preset_name == "gmail":
        return {
            "GMAIL_ACCESS_TOKEN": token_data["access_token"],
            "GMAIL_REFRESH_TOKEN": token_data.get("refresh_token", ""),
        }
    
    elif preset_name == "google-calendar":
        return {
            "GOOGLE_CALENDAR_ACCESS_TOKEN": token_data["access_token"],
            "GOOGLE_CALENDAR_REFRESH_TOKEN": token_data.get("refresh_token", ""),
        }
```

#### **3.2 Slack OAuth**

```python
async def handle_slack_oauth_for_mcp(
    token_data: Dict[str, Any],
) -> Dict[str, str]:
    """
    Handle OAuth tokens for Slack MCP server.
    
    Slack returns team_id in metadata.
    """
    metadata = token_data.get("metadata", {})
    
    return {
        "SLACK_BOT_TOKEN": token_data["access_token"],
        "SLACK_TEAM_ID": metadata.get("team_id", ""),
    }
```

---

## 🎨 UI/UX Flow

### **Before (Current)**
```
1. User sees MCP server list
2. Clicks "Add Server"
3. Sees form: "Enter API Key"
4. User goes to service website
5. Creates API key
6. Copies and pastes key
7. Saves
8. Connects
```

### **After (Proposed)**
```
1. User sees MCP server list
2. Clicks "Connect" button
3. OAuth popup opens (Google/Slack/etc.)
4. User grants permission
5. Automatically connected ✅
```

---

## 📋 Implementation Checklist

### **Backend**
- [ ] Extend `MCP_SERVER_PRESETS` with OAuth config
- [ ] Add `oauth_service`, `oauth_scopes`, `oauth_to_env_mapping` to presets
- [ ] Create `/api/v1/mcp/servers/{name}/oauth/connect` endpoint
- [ ] Create `/api/v1/mcp/oauth/callback` endpoint
- [ ] Implement `convert_oauth_to_mcp_env()` function
- [ ] Add OAuth state management (session/cache)
- [ ] Create service-specific OAuth handlers
- [ ] Handle token refresh for MCP servers
- [ ] Update database schema to link OAuth tokens to MCP servers

### **Frontend**
- [ ] Update MCP server list to show "Connect" button for OAuth
- [ ] Create OAuth callback page (`/mcp/oauth/callback`)
- [ ] Add OAuth flow handling in MCP components
- [ ] Show connection status (Connected/Disconnected)
- [ ] Add "Disconnect" button (revoke OAuth)
- [ ] Handle OAuth errors gracefully

### **Configuration**
- [ ] Add OAuth client IDs/secrets to settings
- [ ] Configure redirect URIs for each service
- [ ] Set up OAuth scopes per service
- [ ] Test OAuth flows for each service

---

## 🔐 Security Considerations

1. **OAuth State Validation**
   - Use cryptographically secure random state
   - Store state server-side (not just client)
   - Validate state on callback

2. **Token Storage**
   - Encrypt tokens in database
   - Use vault encryption key
   - Store refresh tokens securely

3. **Token Refresh**
   - Auto-refresh expired tokens
   - Handle refresh failures gracefully
   - Notify user if refresh fails

4. **Scope Management**
   - Request minimum required scopes
   - Show user what permissions are requested
   - Allow scope updates if needed

---

## 🚀 Benefits

1. **Better UX**
   - One-click connection
   - No manual API key management
   - Familiar OAuth flow

2. **Security**
   - No API keys in user's clipboard
   - Tokens stored securely
   - Easy revocation

3. **Maintenance**
   - Less support for "where do I get API key?"
   - Automatic token refresh
   - Better error handling

4. **Competitive**
   - Matches Claude's UX
   - Industry standard approach
   - Professional feel

---

## 📝 Example: Google Drive Connection

### **Current Flow:**
```
1. User: "I want to connect Google Drive"
2. System: "Enter GDRIVE_CREDENTIALS_PATH"
3. User: "What's that? Where do I get it?"
4. User: *Goes to Google Cloud Console*
5. User: *Creates OAuth credentials*
6. User: *Downloads JSON file*
7. User: *Uploads file*
8. User: *Enters path*
9. System: "Connected"
```

### **Proposed Flow:**
```
1. User: "I want to connect Google Drive"
2. User: *Clicks "Connect"*
3. System: *Opens Google OAuth*
4. User: *Grants permission*
5. System: "Connected ✅"
```

---

## 🎯 Next Steps

1. **Review this proposal** - Confirm approach
2. **Prioritize services** - Which OAuth services first?
   - Google (Drive, Gmail, Calendar) - High priority
   - Slack - High priority
   - Others - Lower priority
3. **Implement Phase 1** - Backend OAuth integration
4. **Implement Phase 2** - Frontend UI
5. **Test with real services** - Verify OAuth flows
6. **Deploy** - Roll out to users

---

**This proposal enables one-click OAuth authentication for MCP servers, matching Claude's user experience!** 🚀
