-- ============================================
-- PERFORMANCE INDEXES MIGRATION (CORRECTED)
-- ============================================
-- This migration adds additional indexes to improve query performance
-- for common operations in the NodeAI application.
-- Fixed: Column name mismatches and IMMUTABLE function issues
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
CREATE INDEX IF NOT EXISTS idx_secrets_expires_at ON secrets_vault(expires_at) WHERE expires_at IS NOT NULL;

-- Composite index for provider and type filtering
CREATE INDEX IF NOT EXISTS idx_secrets_provider_type ON secrets_vault(provider, secret_type);

-- Index for usage tracking
CREATE INDEX IF NOT EXISTS idx_secrets_last_used ON secrets_vault(last_used_at DESC) WHERE last_used_at IS NOT NULL;

-- GIN index for tags (for tag-based secret filtering)
CREATE INDEX IF NOT EXISTS idx_secrets_tags_gin ON secrets_vault USING GIN (tags);

-- Performance indexes for traces table
-- ============================================

-- Composite index for user traces ordered by start time
CREATE INDEX IF NOT EXISTS idx_traces_user_started ON traces(user_id, started_at DESC) WHERE user_id IS NOT NULL;

-- Index for filtering by completion status and time
CREATE INDEX IF NOT EXISTS idx_traces_status_started ON traces(status, started_at DESC);

-- Index for cost analysis queries
CREATE INDEX IF NOT EXISTS idx_traces_total_cost ON traces(total_cost, started_at DESC) WHERE total_cost > 0;

-- Index for duration analysis queries  
CREATE INDEX IF NOT EXISTS idx_traces_duration ON traces(total_duration_ms, started_at DESC) WHERE total_duration_ms > 0;

-- Composite index for workflow performance analysis
CREATE INDEX IF NOT EXISTS idx_traces_workflow_completed ON traces(workflow_id, completed_at DESC) 
    WHERE completed_at IS NOT NULL;

-- Performance indexes for spans table (if exists)
-- ============================================

-- Only create spans indexes if the table exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'spans') THEN
        -- Composite index for span hierarchy queries
        CREATE INDEX IF NOT EXISTS idx_spans_trace_parent ON spans(trace_id, parent_span_id) WHERE parent_span_id IS NOT NULL;
        
        -- Index for span performance analysis
        CREATE INDEX IF NOT EXISTS idx_spans_duration ON spans(duration_ms, started_at) WHERE duration_ms > 0;
        
        -- Index for error span analysis
        CREATE INDEX IF NOT EXISTS idx_spans_errors ON spans(trace_id, status, started_at) WHERE status = 'failed';
        
        RAISE NOTICE 'Created indexes for spans table';
    ELSE
        RAISE NOTICE 'Spans table does not exist, skipping span indexes';
    END IF;
END $$;

-- Performance indexes for profiles table
-- ============================================

-- Index for profile lookups by creation time (admin queries)
CREATE INDEX IF NOT EXISTS idx_profiles_created_at ON profiles(created_at DESC);

-- Index for role-based queries with creation time
CREATE INDEX IF NOT EXISTS idx_profiles_role_created ON profiles(role, created_at DESC);

-- Performance indexes for api_keys table (using correct column names)
-- ============================================

-- Index for enabled API keys (api_keys uses 'enabled', not 'is_active')
CREATE INDEX IF NOT EXISTS idx_api_keys_enabled_created ON api_keys(enabled, created_at DESC);

-- Composite index for user's enabled API keys
CREATE INDEX IF NOT EXISTS idx_api_keys_user_enabled ON api_keys(user_id, enabled, created_at DESC);

-- Index for API key expiration
CREATE INDEX IF NOT EXISTS idx_api_keys_expires_at ON api_keys(expires_at) WHERE expires_at IS NOT NULL;

-- Performance indexes for knowledge_bases table (if exists)
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'knowledge_bases') THEN
        -- Composite index for user knowledge bases
        CREATE INDEX IF NOT EXISTS idx_knowledge_bases_user ON knowledge_bases(user_id, created_at DESC);
        
        -- Check if status column exists
        IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'knowledge_bases' AND column_name = 'status') THEN
            CREATE INDEX IF NOT EXISTS idx_knowledge_bases_status ON knowledge_bases(status, updated_at DESC);
            RAISE NOTICE 'Created status index for knowledge_bases table';
        END IF;
        
        RAISE NOTICE 'Created indexes for knowledge_bases table';
    ELSE
        RAISE NOTICE 'Knowledge_bases table does not exist, skipping knowledge_bases indexes';
    END IF;
END $$;

-- Performance indexes for deployments table (using correct column names)
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'deployments') THEN
        -- Composite index for workflow deployments
        CREATE INDEX IF NOT EXISTS idx_deployments_workflow ON deployments(workflow_id, deployed_at DESC);
        
        -- Index for deployment status (deployments uses 'status', not 'is_active')
        CREATE INDEX IF NOT EXISTS idx_deployments_status_time ON deployments(status, deployed_at DESC);
        
        -- Index for active deployments (status = 'active')
        CREATE INDEX IF NOT EXISTS idx_deployments_active_only ON deployments(workflow_id, deployed_at DESC) 
            WHERE status = 'active';
            
        RAISE NOTICE 'Created indexes for deployments table';
    ELSE
        RAISE NOTICE 'Deployments table does not exist, skipping deployment indexes';
    END IF;
END $$;

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

-- Partial index for non-expired secrets (simplified - no NOW() function)
CREATE INDEX IF NOT EXISTS idx_secrets_non_expired ON secrets_vault(user_id, updated_at DESC) 
    WHERE expires_at IS NULL;

-- Index for error trace analysis
CREATE INDEX IF NOT EXISTS idx_traces_errors_only ON traces(workflow_id, started_at DESC) 
    WHERE status = 'failed';

-- Partial index for enabled API keys only
CREATE INDEX IF NOT EXISTS idx_api_keys_enabled_only ON api_keys(user_id, created_at DESC) 
    WHERE enabled = true;

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
COMMENT ON INDEX idx_api_keys_enabled_only IS 'Partial index for enabled API keys only';

-- Performance statistics update
-- ============================================

-- Update table statistics for better query planning
ANALYZE workflows;
ANALYZE secrets_vault;
ANALYZE traces;
ANALYZE profiles;
ANALYZE api_keys;

-- Analyze optional tables if they exist
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'spans') THEN
        EXECUTE 'ANALYZE spans';
        RAISE NOTICE 'Analyzed spans table';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'knowledge_bases') THEN
        EXECUTE 'ANALYZE knowledge_bases';
        RAISE NOTICE 'Analyzed knowledge_bases table';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'deployments') THEN
        EXECUTE 'ANALYZE deployments';
        RAISE NOTICE 'Analyzed deployments table';
    END IF;
END $$;

-- Final completion message
-- ============================================
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    -- Count indexes created in this migration
    SELECT COUNT(*) INTO index_count 
    FROM pg_indexes 
    WHERE indexname LIKE 'idx_%' 
    AND (indexname LIKE '%workflows%' OR indexname LIKE '%secrets%' OR indexname LIKE '%traces%' OR indexname LIKE '%api_keys%');
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Performance indexes migration completed successfully!';
    RAISE NOTICE 'Created indexes for improved query performance';
    RAISE NOTICE 'Fixed column name mismatches and IMMUTABLE issues';
    RAISE NOTICE 'Tables analyzed for optimal query planning';
    RAISE NOTICE 'Total indexes: %', index_count;
    RAISE NOTICE '========================================';
END $$;