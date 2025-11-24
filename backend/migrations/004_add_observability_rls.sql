-- Migration: Add Row Level Security (RLS) for Observability Tables
-- Description: Adds RLS policies for traces and spans to ensure users can only access their own data
-- Created: 2025-01-XX
-- Dependencies: 003_add_observability_tables.sql

-- Enable RLS on traces table
ALTER TABLE traces ENABLE ROW LEVEL SECURITY;

-- Enable RLS on spans table
ALTER TABLE spans ENABLE ROW LEVEL SECURITY;

-- ============================================
-- RLS Policies for Traces
-- ============================================

-- Policy: Users can view their own traces
CREATE POLICY "Users can view their own traces"
    ON traces
    FOR SELECT
    USING (
        user_id = auth.uid() OR
        user_id IS NULL  -- Allow viewing traces without user_id (backward compatibility)
    );

-- Policy: Users can insert their own traces
CREATE POLICY "Users can insert their own traces"
    ON traces
    FOR INSERT
    WITH CHECK (
        user_id = auth.uid() OR
        user_id IS NULL  -- Allow inserting traces without user_id (backward compatibility)
    );

-- Policy: Users can update their own traces
CREATE POLICY "Users can update their own traces"
    ON traces
    FOR UPDATE
    USING (
        user_id = auth.uid() OR
        user_id IS NULL
    );

-- Policy: Admins can view all traces
CREATE POLICY "Admins can view all traces"
    ON traces
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

-- ============================================
-- RLS Policies for Spans
-- ============================================

-- Policy: Users can view spans from their own traces
CREATE POLICY "Users can view spans from their own traces"
    ON spans
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM traces
            WHERE traces.trace_id = spans.trace_id
            AND (
                traces.user_id = auth.uid() OR
                traces.user_id IS NULL
            )
        )
    );

-- Policy: Users can insert spans to their own traces
CREATE POLICY "Users can insert spans to their own traces"
    ON spans
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM traces
            WHERE traces.trace_id = spans.trace_id
            AND (
                traces.user_id = auth.uid() OR
                traces.user_id IS NULL
            )
        )
    );

-- Policy: Users can update spans in their own traces
CREATE POLICY "Users can update spans in their own traces"
    ON spans
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM traces
            WHERE traces.trace_id = spans.trace_id
            AND (
                traces.user_id = auth.uid() OR
                traces.user_id IS NULL
            )
        )
    );

-- Policy: Admins can view all spans
CREATE POLICY "Admins can view all spans"
    ON spans
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'admin'
        )
    );

