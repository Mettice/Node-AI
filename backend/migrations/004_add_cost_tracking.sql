-- Migration: Add Cost Tracking Tables
-- Description: Creates tables for persistent cost tracking with detailed breakdowns
-- Created: 2025-01-XX
-- Dependencies: 001_initial_schema.sql, 003_add_observability_tables.sql

-- ============================================
-- Cost Records Table (Detailed Node-Level Costs)
-- ============================================
CREATE TABLE IF NOT EXISTS cost_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id TEXT NOT NULL,
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    
    -- Node Information
    node_id TEXT NOT NULL,
    node_type TEXT NOT NULL, -- 'chat', 'embed', 'rerank', 'vector_search', etc.
    
    -- Cost Details
    cost DECIMAL(10, 6) NOT NULL DEFAULT 0.0,
    tokens_used JSONB DEFAULT '{}'::jsonb, -- {input: int, output: int, total: int}
    duration_ms INTEGER DEFAULT 0,
    
    -- Provider & Model Information
    provider TEXT, -- 'openai', 'anthropic', 'gemini', 'cohere', etc.
    model TEXT, -- 'gpt-4o-mini', 'claude-sonnet-4', etc.
    
    -- Category (for aggregation)
    category TEXT NOT NULL, -- 'llm', 'embedding', 'rerank', 'vector_search', 'other'
    
    -- Metadata
    config JSONB DEFAULT '{}'::jsonb, -- Node configuration
    metadata JSONB DEFAULT '{}'::jsonb, -- Additional metadata
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_category CHECK (category IN ('llm', 'embedding', 'rerank', 'vector_search', 'other'))
);

-- Indexes for cost_records
CREATE INDEX IF NOT EXISTS idx_cost_records_execution_id ON cost_records(execution_id);
CREATE INDEX IF NOT EXISTS idx_cost_records_workflow_id ON cost_records(workflow_id);
CREATE INDEX IF NOT EXISTS idx_cost_records_user_id ON cost_records(user_id);
CREATE INDEX IF NOT EXISTS idx_cost_records_created_at ON cost_records(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cost_records_category ON cost_records(category);
CREATE INDEX IF NOT EXISTS idx_cost_records_provider ON cost_records(provider);
CREATE INDEX IF NOT EXISTS idx_cost_records_model ON cost_records(model);
CREATE INDEX IF NOT EXISTS idx_cost_records_workflow_created ON cost_records(workflow_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cost_records_user_created ON cost_records(user_id, created_at DESC);

-- ============================================
-- Cost Aggregations Table (Daily/Weekly/Monthly Summaries)
-- ============================================
CREATE TABLE IF NOT EXISTS cost_aggregations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    
    -- Time Period
    period_type TEXT NOT NULL, -- 'daily', 'weekly', 'monthly'
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    -- Aggregated Costs
    total_cost DECIMAL(10, 6) NOT NULL DEFAULT 0.0,
    total_executions INTEGER DEFAULT 0,
    total_tokens JSONB DEFAULT '{}'::jsonb, -- {input: bigint, output: bigint, total: bigint}
    
    -- Cost Breakdowns
    cost_by_category JSONB DEFAULT '{}'::jsonb, -- {llm: 0.05, embedding: 0.001, ...}
    cost_by_provider JSONB DEFAULT '{}'::jsonb, -- {openai: 0.04, anthropic: 0.01, ...}
    cost_by_model JSONB DEFAULT '{}'::jsonb, -- {gpt-4o-mini: 0.03, claude-sonnet: 0.01, ...}
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_period_type CHECK (period_type IN ('daily', 'weekly', 'monthly')),
    UNIQUE(workflow_id, user_id, period_type, period_start)
);

-- Indexes for cost_aggregations
CREATE INDEX IF NOT EXISTS idx_cost_agg_workflow_id ON cost_aggregations(workflow_id);
CREATE INDEX IF NOT EXISTS idx_cost_agg_user_id ON cost_aggregations(user_id);
CREATE INDEX IF NOT EXISTS idx_cost_agg_period ON cost_aggregations(period_type, period_start DESC);
CREATE INDEX IF NOT EXISTS idx_cost_agg_workflow_period ON cost_aggregations(workflow_id, period_type, period_start DESC);
CREATE INDEX IF NOT EXISTS idx_cost_agg_user_period ON cost_aggregations(user_id, period_type, period_start DESC);

-- ============================================
-- Function to Update Cost Aggregations
-- ============================================
CREATE OR REPLACE FUNCTION update_cost_aggregations()
RETURNS TRIGGER AS $$
DECLARE
    period_start_daily TIMESTAMP;
    period_start_weekly TIMESTAMP;
    period_start_monthly TIMESTAMP;
    period_end_daily TIMESTAMP;
    period_end_weekly TIMESTAMP;
    period_end_monthly TIMESTAMP;
    workflow_uuid UUID;
    user_uuid UUID;
BEGIN
    -- Get workflow_id and user_id from the cost record
    workflow_uuid := NEW.workflow_id;
    user_uuid := NEW.user_id;
    
    -- Calculate period boundaries
    period_start_daily := DATE_TRUNC('day', NEW.created_at);
    period_end_daily := period_start_daily + INTERVAL '1 day';
    
    period_start_weekly := DATE_TRUNC('week', NEW.created_at);
    period_end_weekly := period_start_weekly + INTERVAL '1 week';
    
    period_start_monthly := DATE_TRUNC('month', NEW.created_at);
    period_end_monthly := period_start_monthly + INTERVAL '1 month';
    
    -- Update daily aggregation
    INSERT INTO cost_aggregations (
        workflow_id, user_id, period_type, period_start, period_end,
        total_cost, total_executions, cost_by_category, cost_by_provider, cost_by_model
    )
    VALUES (
        workflow_uuid, user_uuid, 'daily', period_start_daily, period_end_daily,
        NEW.cost, 1,
        jsonb_build_object(NEW.category, NEW.cost),
        CASE WHEN NEW.provider IS NOT NULL THEN jsonb_build_object(NEW.provider, NEW.cost) ELSE '{}'::jsonb END,
        CASE WHEN NEW.model IS NOT NULL THEN jsonb_build_object(NEW.model, NEW.cost) ELSE '{}'::jsonb END
    )
    ON CONFLICT (workflow_id, user_id, period_type, period_start)
    DO UPDATE SET
        total_cost = cost_aggregations.total_cost + NEW.cost,
        total_executions = cost_aggregations.total_executions + 1,
        cost_by_category = cost_aggregations.cost_by_category || jsonb_build_object(
            NEW.category,
            COALESCE((cost_aggregations.cost_by_category->>NEW.category)::numeric, 0) + NEW.cost
        ),
        cost_by_provider = CASE 
            WHEN NEW.provider IS NOT NULL THEN 
                cost_aggregations.cost_by_provider || jsonb_build_object(
                    NEW.provider,
                    COALESCE((cost_aggregations.cost_by_provider->>NEW.provider)::numeric, 0) + NEW.cost
                )
            ELSE cost_aggregations.cost_by_provider
        END,
        cost_by_model = CASE 
            WHEN NEW.model IS NOT NULL THEN 
                cost_aggregations.cost_by_model || jsonb_build_object(
                    NEW.model,
                    COALESCE((cost_aggregations.cost_by_model->>NEW.model)::numeric, 0) + NEW.cost
                )
            ELSE cost_aggregations.cost_by_model
        END,
        updated_at = NOW();
    
    -- Update weekly aggregation (similar logic)
    INSERT INTO cost_aggregations (
        workflow_id, user_id, period_type, period_start, period_end,
        total_cost, total_executions, cost_by_category, cost_by_provider, cost_by_model
    )
    VALUES (
        workflow_uuid, user_uuid, 'weekly', period_start_weekly, period_end_weekly,
        NEW.cost, 1,
        jsonb_build_object(NEW.category, NEW.cost),
        CASE WHEN NEW.provider IS NOT NULL THEN jsonb_build_object(NEW.provider, NEW.cost) ELSE '{}'::jsonb END,
        CASE WHEN NEW.model IS NOT NULL THEN jsonb_build_object(NEW.model, NEW.cost) ELSE '{}'::jsonb END
    )
    ON CONFLICT (workflow_id, user_id, period_type, period_start)
    DO UPDATE SET
        total_cost = cost_aggregations.total_cost + NEW.cost,
        total_executions = cost_aggregations.total_executions + 1,
        cost_by_category = cost_aggregations.cost_by_category || jsonb_build_object(
            NEW.category,
            COALESCE((cost_aggregations.cost_by_category->>NEW.category)::numeric, 0) + NEW.cost
        ),
        cost_by_provider = CASE 
            WHEN NEW.provider IS NOT NULL THEN 
                cost_aggregations.cost_by_provider || jsonb_build_object(
                    NEW.provider,
                    COALESCE((cost_aggregations.cost_by_provider->>NEW.provider)::numeric, 0) + NEW.cost
                )
            ELSE cost_aggregations.cost_by_provider
        END,
        cost_by_model = CASE 
            WHEN NEW.model IS NOT NULL THEN 
                cost_aggregations.cost_by_model || jsonb_build_object(
                    NEW.model,
                    COALESCE((cost_aggregations.cost_by_model->>NEW.model)::numeric, 0) + NEW.cost
                )
            ELSE cost_aggregations.cost_by_model
        END,
        updated_at = NOW();
    
    -- Update monthly aggregation (similar logic)
    INSERT INTO cost_aggregations (
        workflow_id, user_id, period_type, period_start, period_end,
        total_cost, total_executions, cost_by_category, cost_by_provider, cost_by_model
    )
    VALUES (
        workflow_uuid, user_uuid, 'monthly', period_start_monthly, period_end_monthly,
        NEW.cost, 1,
        jsonb_build_object(NEW.category, NEW.cost),
        CASE WHEN NEW.provider IS NOT NULL THEN jsonb_build_object(NEW.provider, NEW.cost) ELSE '{}'::jsonb END,
        CASE WHEN NEW.model IS NOT NULL THEN jsonb_build_object(NEW.model, NEW.cost) ELSE '{}'::jsonb END
    )
    ON CONFLICT (workflow_id, user_id, period_type, period_start)
    DO UPDATE SET
        total_cost = cost_aggregations.total_cost + NEW.cost,
        total_executions = cost_aggregations.total_executions + 1,
        cost_by_category = cost_aggregations.cost_by_category || jsonb_build_object(
            NEW.category,
            COALESCE((cost_aggregations.cost_by_category->>NEW.category)::numeric, 0) + NEW.cost
        ),
        cost_by_provider = CASE 
            WHEN NEW.provider IS NOT NULL THEN 
                cost_aggregations.cost_by_provider || jsonb_build_object(
                    NEW.provider,
                    COALESCE((cost_aggregations.cost_by_provider->>NEW.provider)::numeric, 0) + NEW.cost
                )
            ELSE cost_aggregations.cost_by_provider
        END,
        cost_by_model = CASE 
            WHEN NEW.model IS NOT NULL THEN 
                cost_aggregations.cost_by_model || jsonb_build_object(
                    NEW.model,
                    COALESCE((cost_aggregations.cost_by_model->>NEW.model)::numeric, 0) + NEW.cost
                )
            ELSE cost_aggregations.cost_by_model
        END,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update aggregations when cost records are inserted
CREATE TRIGGER trigger_update_cost_aggregations
    AFTER INSERT ON cost_records
    FOR EACH ROW
    EXECUTE FUNCTION update_cost_aggregations();

