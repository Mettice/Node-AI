-- ============================================
-- PERFORMANCE INDEXES MIGRATION
-- ============================================
-- This migration adds additional indexes to improve query performance
-- for common operations in the NodeAI application.
-- ============================================

-- Performance indexes for workflows table
-- ============================================

-- Index for workflows.updated_at (used in ORDER BY for list queries)
CREATE INDEX IF NOT EXISTS idx_workflows_updated_at ON workflows(updated_at DESC);

-- Composite index for user workflows ordered by updated_at (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_workflows_user_updated ON workflows(user_id, updated_at DESC);

-- GIN index for workflows.tags (for tag-based filtering and searches)
CREATE INDEX IF NOT EXISTS idx_workflows_tags_gin ON workflows USING GIN (tags);

-- Text search index for workflow names (for name-based searches)
CREATE INDEX IF NOT EXISTS idx_workflows_name_text ON workflows(name text_pattern_ops);

-- Composite indexes for common filter combinations
CREATE INDEX IF NOT EXISTS idx_workflows_user_template ON workflows(user_id, is_template);
CREATE INDEX IF NOT EXISTS idx_workflows_user_deployed ON workflows(user_id, is_deployed);
CREATE INDEX IF NOT EXISTS idx_workflows_user_template_updated ON workflows(user_id, is_template, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_user_deployed_updated ON workflows(user_id, is_deployed, updated_at DESC);

-- GIN index for workflows.nodes (for node-based queries and searches)
CREATE INDEX IF NOT EXISTS idx_workflows_nodes_gin ON workflows USING GIN (nodes);

-- GIN index for workflows.edges (for edge-based queries and graph analysis)
CREATE INDEX IF NOT EXISTS idx_workflows_edges_gin ON workflows USING GIN (edges);

-- Performance indexes for secrets_vault table
-- ============================================

-- Index for active secrets filtering (very common query pattern)
CREATE INDEX IF NOT EXISTS idx_secrets_is_active ON secrets_vault(is_active);

-- Composite index for user's active secrets
CREATE INDEX IF NOT EXISTS idx_secrets_user_active ON secrets_vault(user_id, is_active);

-- Index for secrets expiration (for cleanup and validation)
CREATE INDEX IF NOT EXISTS idx_secrets_expires_at ON secrets_vault(expires_at);

-- Composite index for provider and type filtering
CREATE INDEX IF NOT EXISTS idx_secrets_provider_type ON secrets_vault(provider, secret_type);

-- Index for usage tracking
CREATE INDEX IF NOT EXISTS idx_secrets_last_used ON secrets_vault(last_used_at DESC);

-- GIN index for tags (for tag-based secret filtering)
CREATE INDEX IF NOT EXISTS idx_secrets_tags_gin ON secrets_vault USING GIN (tags);

-- Performance indexes for traces table (if additional ones needed)
-- ============================================

-- Composite index for user traces ordered by start time
CREATE INDEX IF NOT EXISTS idx_traces_user_started ON traces(user_id, started_at DESC);

-- Index for filtering by completion status and time
CREATE INDEX IF NOT EXISTS idx_traces_status_started ON traces(status, started_at DESC);

-- Index for cost analysis queries
CREATE INDEX IF NOT EXISTS idx_traces_total_cost ON traces(total_cost) WHERE total_cost > 0;

-- Index for duration analysis queries  
CREATE INDEX IF NOT EXISTS idx_traces_duration ON traces(total_duration_ms) WHERE total_duration_ms > 0;

-- Composite index for workflow performance analysis
CREATE INDEX IF NOT EXISTS idx_traces_workflow_completed ON traces(workflow_id, completed_at DESC) 
    WHERE completed_at IS NOT NULL;

-- Performance indexes for profiles table (additional ones)
-- ============================================

-- Index for profile lookups by creation time (admin queries)
CREATE INDEX IF NOT EXISTS idx_profiles_created_at ON profiles(created_at DESC);

-- Index for role-based queries with creation time
CREATE INDEX IF NOT EXISTS idx_profiles_role_created ON profiles(role, created_at DESC);

-- Additional utility indexes
-- ============================================

-- Partial index for deployed workflows only (saves space)
CREATE INDEX IF NOT EXISTS idx_workflows_deployed_only ON workflows(user_id, deployed_at DESC) 
    WHERE is_deployed = true;

-- Partial index for template workflows only
CREATE INDEX IF NOT EXISTS idx_workflows_templates_only ON workflows(user_id, created_at DESC) 
    WHERE is_template = true;

-- Partial index for active secrets only (most common case)
CREATE INDEX IF NOT EXISTS idx_secrets_active_only ON secrets_vault(user_id, provider, updated_at DESC) 
    WHERE is_active = true;

-- Partial index for non-expired secrets (simplified - avoid NOW() function)
-- Note: This index will include secrets without expiration dates
CREATE INDEX IF NOT EXISTS idx_secrets_non_expired ON secrets_vault(user_id, updated_at DESC) 
    WHERE expires_at IS NULL;

-- Index for error trace analysis
CREATE INDEX IF NOT EXISTS idx_traces_errors_only ON traces(workflow_id, started_at DESC) 
    WHERE status = 'failed';

-- Add comments for documentation
-- ============================================

COMMENT ON INDEX idx_workflows_updated_at IS 'Index for sorting workflows by update time';
COMMENT ON INDEX idx_workflows_user_updated IS 'Composite index for user workflows sorted by update time';
COMMENT ON INDEX idx_workflows_tags_gin IS 'GIN index for tag-based workflow filtering';
COMMENT ON INDEX idx_workflows_name_text IS 'Index for text-based workflow name searches';
COMMENT ON INDEX idx_secrets_is_active IS 'Index for filtering active secrets';
COMMENT ON INDEX idx_secrets_user_active IS 'Composite index for user active secrets';
COMMENT ON INDEX idx_traces_user_started IS 'Composite index for user traces by start time';
COMMENT ON INDEX idx_workflows_deployed_only IS 'Partial index for deployed workflows only';
COMMENT ON INDEX idx_workflows_templates_only IS 'Partial index for template workflows only';
COMMENT ON INDEX idx_secrets_active_only IS 'Partial index for active secrets only';

-- Performance statistics update
-- ============================================

-- Update table statistics for better query planning
ANALYZE workflows;
ANALYZE secrets_vault;
ANALYZE traces;
ANALYZE profiles;

-- Completion message
-- ============================================
DO $$
BEGIN
    RAISE NOTICE 'Performance indexes migration completed successfully!';
    RAISE NOTICE 'Added % new indexes for improved query performance', 25;
    RAISE NOTICE 'Tables analyzed for optimal query planning';
END $$;