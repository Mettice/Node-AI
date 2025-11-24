-- ============================================
-- Complete Observability Database Setup
-- ============================================
-- Run this file in your SQL editor to set up all observability tables
-- Make sure you've already run 001_initial_schema.sql first!

-- ============================================
-- Step 1: Add Settings Column to Profiles
-- ============================================
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_profiles_settings ON profiles USING GIN (settings);

COMMENT ON COLUMN profiles.settings IS 'User settings and preferences including observability configuration';

-- ============================================
-- Step 2: Create Traces Table
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    error TEXT,
    
    -- Metrics
    total_cost DECIMAL(10, 6) DEFAULT 0.0,
    total_tokens JSONB DEFAULT '{}'::jsonb,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

-- Traces Indexes
CREATE INDEX IF NOT EXISTS idx_traces_workflow_id ON traces(workflow_id);
CREATE INDEX IF NOT EXISTS idx_traces_execution_id ON traces(execution_id);
CREATE INDEX IF NOT EXISTS idx_traces_user_id ON traces(user_id);
CREATE INDEX IF NOT EXISTS idx_traces_started_at ON traces(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
CREATE INDEX IF NOT EXISTS idx_traces_workflow_started ON traces(workflow_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_traces_metadata_gin ON traces USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_traces_total_tokens_gin ON traces USING GIN (total_tokens);

-- ============================================
-- Step 3: Create Spans Table
-- ============================================
CREATE TABLE IF NOT EXISTS spans (
    span_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
    parent_span_id UUID REFERENCES spans(span_id) ON DELETE SET NULL,
    
    -- Identification
    span_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER DEFAULT 0,
    
    -- Inputs/Outputs
    inputs JSONB DEFAULT '{}'::jsonb,
    outputs JSONB DEFAULT '{}'::jsonb,
    
    -- GenAI-specific metadata
    tokens JSONB DEFAULT '{}'::jsonb,
    cost DECIMAL(10, 6) DEFAULT 0.0,
    model VARCHAR(255),
    provider VARCHAR(100),
    
    -- Error tracking
    error TEXT,
    error_type VARCHAR(100),
    error_stack TEXT,
    
    -- API-specific metadata
    api_limits JSONB DEFAULT '{}'::jsonb,
    retry_count INTEGER DEFAULT 0,
    timeout INTEGER,
    
    -- Evaluation metadata
    evaluation JSONB DEFAULT '{}'::jsonb,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Child spans
    child_spans TEXT[] DEFAULT '{}',
    
    CONSTRAINT valid_span_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Spans Indexes
CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_parent_span_id ON spans(parent_span_id);
CREATE INDEX IF NOT EXISTS idx_spans_span_type ON spans(span_type);
CREATE INDEX IF NOT EXISTS idx_spans_status ON spans(status);
CREATE INDEX IF NOT EXISTS idx_spans_started_at ON spans(started_at);
CREATE INDEX IF NOT EXISTS idx_spans_trace_started ON spans(trace_id, started_at);
CREATE INDEX IF NOT EXISTS idx_spans_tokens_gin ON spans USING GIN (tokens);
CREATE INDEX IF NOT EXISTS idx_spans_metadata_gin ON spans USING GIN (metadata);

-- ============================================
-- Step 4: Add Comments
-- ============================================
COMMENT ON TABLE traces IS 'Stores end-to-end workflow execution traces for observability';
COMMENT ON TABLE spans IS 'Stores individual spans (atomic actions) within traces';
COMMENT ON COLUMN traces.total_tokens IS 'Token usage: {input: int, output: int, total: int}';
COMMENT ON COLUMN spans.tokens IS 'Token usage: {input_tokens: int, output_tokens: int, total_tokens: int}';
COMMENT ON COLUMN spans.api_limits IS 'API rate limit info: {rate_limit: int, remaining: int, reset_at: timestamp}';
COMMENT ON COLUMN spans.evaluation IS 'Span-level evaluation metrics (quality, performance, etc.)';

-- ============================================
-- Step 5: Row Level Security (Optional - for Supabase)
-- ============================================
-- Uncomment the following if you're using Supabase and want RLS enabled

/*
-- Enable RLS
ALTER TABLE traces ENABLE ROW LEVEL SECURITY;
ALTER TABLE spans ENABLE ROW LEVEL SECURITY;

-- Users can view their own traces
CREATE POLICY "Users can view their own traces"
    ON traces FOR SELECT
    USING (user_id = auth.uid() OR user_id IS NULL);

-- Users can insert their own traces
CREATE POLICY "Users can insert their own traces"
    ON traces FOR INSERT
    WITH CHECK (user_id = auth.uid() OR user_id IS NULL);

-- Users can update their own traces
CREATE POLICY "Users can update their own traces"
    ON traces FOR UPDATE
    USING (user_id = auth.uid() OR user_id IS NULL);

-- Users can view spans from their own traces
CREATE POLICY "Users can view spans from their own traces"
    ON spans FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM traces
            WHERE traces.trace_id = spans.trace_id
            AND (traces.user_id = auth.uid() OR traces.user_id IS NULL)
        )
    );

-- Users can insert spans to their own traces
CREATE POLICY "Users can insert spans to their own traces"
    ON spans FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM traces
            WHERE traces.trace_id = spans.trace_id
            AND (traces.user_id = auth.uid() OR traces.user_id IS NULL)
        )
    );

-- Users can update spans in their own traces
CREATE POLICY "Users can update spans in their own traces"
    ON spans FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM traces
            WHERE traces.trace_id = spans.trace_id
            AND (traces.user_id = auth.uid() OR traces.user_id IS NULL)
        )
    );
*/

-- ============================================
-- Verification Queries
-- ============================================
-- Run these to verify everything was created correctly:

-- Check tables exist
SELECT 'Tables created:' as status;
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('traces', 'spans', 'profiles')
ORDER BY table_name;

-- Check settings column
SELECT 'Settings column:' as status;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'profiles' 
AND column_name = 'settings';

-- Check indexes
SELECT 'Indexes created:' as status;
SELECT indexname, tablename 
FROM pg_indexes 
WHERE tablename IN ('traces', 'spans') 
ORDER BY tablename, indexname;

-- ============================================
-- Done! Your observability tables are ready.
-- ============================================
-- Note: The observability system currently uses in-memory storage.
-- To enable database persistence, update ObservabilityManager to use these tables.

