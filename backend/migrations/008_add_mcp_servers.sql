-- Migration: Add MCP server configurations table
-- This enables per-user MCP server configurations for multi-tenant production deployment

-- ============================================
-- MCP Server Configurations Table
-- ============================================
CREATE TABLE IF NOT EXISTS mcp_server_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Server identification
    name VARCHAR(100) NOT NULL,
    preset VARCHAR(100),  -- Name of preset if using one (e.g., 'slack', 'airtable')
    display_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Connection configuration
    command VARCHAR(500) NOT NULL,  -- Command to run (e.g., 'npx', '/path/to/exe')
    args JSONB NOT NULL DEFAULT '[]',  -- Command arguments
    env_encrypted TEXT,  -- Encrypted environment variables (contains API keys)

    -- Server type and category
    server_type VARCHAR(20) NOT NULL DEFAULT 'npx',  -- 'npx', 'executable', 'http'
    category VARCHAR(50) DEFAULT 'integration',

    -- Status
    enabled BOOLEAN NOT NULL DEFAULT true,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_connected_at TIMESTAMPTZ,

    -- Ensure unique server names per user
    CONSTRAINT unique_user_server_name UNIQUE (user_id, name)
);

-- Index for fast user lookups
CREATE INDEX IF NOT EXISTS idx_mcp_server_configs_user_id ON mcp_server_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_server_configs_preset ON mcp_server_configs(preset);

-- ============================================
-- MCP Connection Log (for auditing)
-- ============================================
CREATE TABLE IF NOT EXISTS mcp_connection_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_config_id UUID REFERENCES mcp_server_configs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    action VARCHAR(20) NOT NULL,  -- 'connect', 'disconnect', 'error'
    status VARCHAR(20) NOT NULL,  -- 'success', 'failure'
    error_message TEXT,
    tools_count INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mcp_connection_log_user_id ON mcp_connection_log(user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_connection_log_server ON mcp_connection_log(server_config_id);

-- ============================================
-- Row Level Security (RLS)
-- ============================================

-- Enable RLS
ALTER TABLE mcp_server_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_connection_log ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own MCP configs" ON mcp_server_configs;
DROP POLICY IF EXISTS "Users can insert their own MCP configs" ON mcp_server_configs;
DROP POLICY IF EXISTS "Users can update their own MCP configs" ON mcp_server_configs;
DROP POLICY IF EXISTS "Users can delete their own MCP configs" ON mcp_server_configs;
DROP POLICY IF EXISTS "Service role has full access to MCP configs" ON mcp_server_configs;

DROP POLICY IF EXISTS "Users can view their own MCP logs" ON mcp_connection_log;
DROP POLICY IF EXISTS "Users can insert their own MCP logs" ON mcp_connection_log;
DROP POLICY IF EXISTS "Service role has full access to MCP logs" ON mcp_connection_log;

-- MCP Server Configs - User policies
CREATE POLICY "Users can view their own MCP configs"
    ON mcp_server_configs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own MCP configs"
    ON mcp_server_configs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own MCP configs"
    ON mcp_server_configs FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own MCP configs"
    ON mcp_server_configs FOR DELETE
    USING (auth.uid() = user_id);

-- Service role policy (for backend operations)
CREATE POLICY "Service role has full access to MCP configs"
    ON mcp_server_configs FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- MCP Connection Log - User policies
CREATE POLICY "Users can view their own MCP logs"
    ON mcp_connection_log FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own MCP logs"
    ON mcp_connection_log FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role has full access to MCP logs"
    ON mcp_connection_log FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- ============================================
-- Updated trigger for updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_mcp_server_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_mcp_server_configs_updated_at ON mcp_server_configs;
CREATE TRIGGER trigger_mcp_server_configs_updated_at
    BEFORE UPDATE ON mcp_server_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_mcp_server_configs_updated_at();

-- ============================================
-- Comments
-- ============================================
COMMENT ON TABLE mcp_server_configs IS 'Per-user MCP server configurations for multi-tenant production';
COMMENT ON COLUMN mcp_server_configs.env_encrypted IS 'Encrypted JSON containing environment variables (API keys, tokens)';
COMMENT ON COLUMN mcp_server_configs.server_type IS 'Type of server: npx (npm package), executable (custom binary), http (remote server)';
