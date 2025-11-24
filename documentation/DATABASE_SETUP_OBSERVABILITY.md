# Database Setup for Observability & Cost Forecasting

## Overview

This guide provides SQL commands to set up the database tables needed for:
- **Observability**: Traces and spans storage
- **Cost Forecasting**: Historical data analysis
- **User Settings**: Observability configuration

## Prerequisites

- PostgreSQL database (Supabase or self-hosted)
- Access to SQL editor or psql
- Existing `profiles` table (from migration 001)

## Migration Order

Run migrations in this order:
1. `001_initial_schema.sql` - Base tables (if not already run)
2. `002_add_profile_settings.sql` - User settings column
3. `003_add_observability_tables.sql` - Traces and spans tables
4. `004_add_observability_rls.sql` - Row Level Security (optional, for Supabase)

## Quick Setup Commands

### Step 1: Add Settings Column to Profiles

```sql
-- Add settings column to profiles table
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;

-- Create index for settings queries
CREATE INDEX IF NOT EXISTS idx_profiles_settings ON profiles USING GIN (settings);

-- Add comment
COMMENT ON COLUMN profiles.settings IS 'User settings and preferences including observability configuration';
```

### Step 2: Create Traces Table

```sql
-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create traces table
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_traces_workflow_id ON traces(workflow_id);
CREATE INDEX IF NOT EXISTS idx_traces_execution_id ON traces(execution_id);
CREATE INDEX IF NOT EXISTS idx_traces_user_id ON traces(user_id);
CREATE INDEX IF NOT EXISTS idx_traces_started_at ON traces(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
CREATE INDEX IF NOT EXISTS idx_traces_workflow_started ON traces(workflow_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_traces_metadata_gin ON traces USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_traces_total_tokens_gin ON traces USING GIN (total_tokens);
```

### Step 3: Create Spans Table

```sql
-- Create spans table
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_parent_span_id ON spans(parent_span_id);
CREATE INDEX IF NOT EXISTS idx_spans_span_type ON spans(span_type);
CREATE INDEX IF NOT EXISTS idx_spans_status ON spans(status);
CREATE INDEX IF NOT EXISTS idx_spans_started_at ON spans(started_at);
CREATE INDEX IF NOT EXISTS idx_spans_trace_started ON spans(trace_id, started_at);
CREATE INDEX IF NOT EXISTS idx_spans_tokens_gin ON spans USING GIN (tokens);
CREATE INDEX IF NOT EXISTS idx_spans_metadata_gin ON spans USING GIN (metadata);
```

### Step 4: Add Row Level Security (Optional - for Supabase)

If using Supabase and want multi-tenant security:

```sql
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
```

## Verification

After running the migrations, verify the tables exist:

```sql
-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('traces', 'spans', 'profiles');

-- Check if settings column exists
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'profiles' 
AND column_name = 'settings';

-- Check indexes
SELECT indexname, tablename 
FROM pg_indexes 
WHERE tablename IN ('traces', 'spans') 
ORDER BY tablename, indexname;
```

## What Each Table Stores

### `traces` Table
- **Purpose**: End-to-end workflow execution traces
- **Key Fields**: `trace_id`, `workflow_id`, `execution_id`, `user_id`, `query`, `total_cost`, `total_tokens`
- **Use Cases**: Cost forecasting, trace listing, workflow analysis

### `spans` Table
- **Purpose**: Individual atomic actions within traces
- **Key Fields**: `span_id`, `trace_id`, `span_type`, `cost`, `tokens`, `evaluation`
- **Use Cases**: Span-level analysis, performance debugging, cost breakdown

### `profiles.settings` Column
- **Purpose**: User preferences including observability API keys
- **Structure**: JSONB with `observability` key containing LangSmith/LangFuse config
- **Use Cases**: User-specific observability configuration

## Next Steps

1. **Update ObservabilityManager** to use database instead of in-memory storage
2. **Test** by executing a workflow and checking if traces are stored
3. **Monitor** table sizes and consider retention policies for old traces

## Optional: Cleanup Function

To automatically clean up old traces (e.g., older than 90 days):

```sql
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

-- Run cleanup (manually or via cron)
-- SELECT cleanup_old_traces(90);
```

## Notes

- **Current State**: Observability system uses in-memory storage by default
- **Migration Path**: Tables are ready, but code still uses in-memory storage
- **Future**: Update `ObservabilityManager` to persist to database (see plan in `OBSERVABILITY_ROBUST_PLAN.md`)

