-- Migration: Add Observability Tables (Traces & Spans)
-- Description: Creates tables for storing workflow execution traces and spans for observability
-- Created: 2025-01-XX
-- Dependencies: 001_initial_schema.sql, 002_add_profile_settings.sql

-- ============================================
-- Traces Table
-- ============================================
CREATE TABLE IF NOT EXISTS traces (
    trace_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) NOT NULL,
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    
    -- Query/Input
    query TEXT,
    
    -- Timing
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    total_duration_ms INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'running', -- 'running', 'completed', 'failed', 'cancelled'
    error TEXT,
    
    -- Metrics
    total_cost DECIMAL(10, 6) DEFAULT 0.0,
    total_tokens JSONB DEFAULT '{}'::jsonb, -- {input: int, output: int, total: int}
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

-- Indexes for traces
CREATE INDEX IF NOT EXISTS idx_traces_workflow_id ON traces(workflow_id);
CREATE INDEX IF NOT EXISTS idx_traces_execution_id ON traces(execution_id);
CREATE INDEX IF NOT EXISTS idx_traces_user_id ON traces(user_id);
CREATE INDEX IF NOT EXISTS idx_traces_started_at ON traces(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
CREATE INDEX IF NOT EXISTS idx_traces_workflow_started ON traces(workflow_id, started_at DESC);

-- ============================================
-- Spans Table
-- ============================================
CREATE TABLE IF NOT EXISTS spans (
    span_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
    parent_span_id UUID REFERENCES spans(span_id) ON DELETE SET NULL,
    
    -- Identification
    span_type VARCHAR(50) NOT NULL, -- 'query_input', 'embedding', 'vector_search', 'llm', etc.
    name VARCHAR(255) NOT NULL,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER DEFAULT 0,
    
    -- Inputs/Outputs
    inputs JSONB DEFAULT '{}'::jsonb,
    outputs JSONB DEFAULT '{}'::jsonb,
    
    -- GenAI-specific metadata
    tokens JSONB DEFAULT '{}'::jsonb, -- {input_tokens: int, output_tokens: int, total_tokens: int}
    cost DECIMAL(10, 6) DEFAULT 0.0,
    model VARCHAR(255),
    provider VARCHAR(100),
    
    -- Error tracking
    error TEXT,
    error_type VARCHAR(100),
    error_stack TEXT,
    
    -- API-specific metadata
    api_limits JSONB DEFAULT '{}'::jsonb, -- {rate_limit: int, remaining: int, reset_at: timestamp}
    retry_count INTEGER DEFAULT 0,
    timeout INTEGER,
    
    -- Evaluation metadata
    evaluation JSONB DEFAULT '{}'::jsonb,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Child spans (for nested spans)
    child_spans TEXT[] DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT valid_span_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Indexes for spans
CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_parent_span_id ON spans(parent_span_id);
CREATE INDEX IF NOT EXISTS idx_spans_span_type ON spans(span_type);
CREATE INDEX IF NOT EXISTS idx_spans_status ON spans(status);
CREATE INDEX IF NOT EXISTS idx_spans_started_at ON spans(started_at);
CREATE INDEX IF NOT EXISTS idx_spans_trace_started ON spans(trace_id, started_at);

-- GIN indexes for JSONB columns (for efficient querying)
CREATE INDEX IF NOT EXISTS idx_spans_tokens_gin ON spans USING GIN (tokens);
CREATE INDEX IF NOT EXISTS idx_spans_metadata_gin ON spans USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_traces_metadata_gin ON traces USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_traces_total_tokens_gin ON traces USING GIN (total_tokens);

-- Comments
COMMENT ON TABLE traces IS 'Stores end-to-end workflow execution traces for observability';
COMMENT ON TABLE spans IS 'Stores individual spans (atomic actions) within traces';
COMMENT ON COLUMN traces.total_tokens IS 'Token usage: {input: int, output: int, total: int}';
COMMENT ON COLUMN spans.tokens IS 'Token usage: {input_tokens: int, output_tokens: int, total_tokens: int}';
COMMENT ON COLUMN spans.api_limits IS 'API rate limit info: {rate_limit: int, remaining: int, reset_at: timestamp}';
COMMENT ON COLUMN spans.evaluation IS 'Span-level evaluation metrics (quality, performance, etc.)';

-- ============================================
-- Retention Policy (Optional - for cleanup)
-- ============================================
-- You can create a function to clean up old traces (e.g., older than 90 days)
-- This is optional and can be run manually or via a scheduled job

-- Example cleanup function (commented out - uncomment if needed):
/*
CREATE OR REPLACE FUNCTION cleanup_old_traces(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM traces
    WHERE started_at < NOW() - (retention_days || ' days')::INTERVAL
    AND status = 'completed';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
*/

