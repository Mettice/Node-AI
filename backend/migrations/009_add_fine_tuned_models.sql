-- Migration: Add fine_tuned_models table
-- Description: Stores fine-tuned model registry entries
-- Date: 2026-01-21

-- Create fine_tuned_models table
CREATE TABLE IF NOT EXISTS fine_tuned_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    base_model TEXT NOT NULL,
    provider TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ready',
    
    -- Training metadata
    training_examples INTEGER NOT NULL DEFAULT 0,
    validation_examples INTEGER DEFAULT 0,
    epochs INTEGER NOT NULL DEFAULT 3,
    training_file_id TEXT,
    validation_file_id TEXT,
    
    -- Cost tracking
    estimated_cost DECIMAL(10, 4),
    actual_cost DECIMAL(10, 4),
    
    -- Usage tracking
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    
    -- Metadata (JSON)
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('training', 'ready', 'failed', 'deleted')),
    CONSTRAINT valid_provider CHECK (provider IN ('openai', 'anthropic', 'custom'))
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_fine_tuned_models_status ON fine_tuned_models(status);
CREATE INDEX IF NOT EXISTS idx_fine_tuned_models_provider ON fine_tuned_models(provider);
CREATE INDEX IF NOT EXISTS idx_fine_tuned_models_base_model ON fine_tuned_models(base_model);
CREATE INDEX IF NOT EXISTS idx_fine_tuned_models_created_at ON fine_tuned_models(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fine_tuned_models_job_id ON fine_tuned_models(job_id);
CREATE INDEX IF NOT EXISTS idx_fine_tuned_models_model_id ON fine_tuned_models(model_id);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_fine_tuned_models_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_fine_tuned_models_updated_at
    BEFORE UPDATE ON fine_tuned_models
    FOR EACH ROW
    EXECUTE FUNCTION update_fine_tuned_models_updated_at();

-- Add RLS policies (if RLS is enabled)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename = 'fine_tuned_models'
        AND rowsecurity = true
    ) THEN
        -- Allow all operations for authenticated users (adjust based on your auth setup)
        -- This is a basic policy - you may want to add user_id column for multi-tenancy
        DROP POLICY IF EXISTS "Users can view all models" ON fine_tuned_models;
        CREATE POLICY "Users can view all models" ON fine_tuned_models
            FOR SELECT USING (true);
        
        DROP POLICY IF EXISTS "Users can insert models" ON fine_tuned_models;
        CREATE POLICY "Users can insert models" ON fine_tuned_models
            FOR INSERT WITH CHECK (true);
        
        DROP POLICY IF EXISTS "Users can update models" ON fine_tuned_models;
        CREATE POLICY "Users can update models" ON fine_tuned_models
            FOR UPDATE USING (true);
        
        DROP POLICY IF EXISTS "Users can delete models" ON fine_tuned_models;
        CREATE POLICY "Users can delete models" ON fine_tuned_models
            FOR DELETE USING (true);
    END IF;
END $$;

-- Add comment
COMMENT ON TABLE fine_tuned_models IS 'Registry of fine-tuned LLM models';
COMMENT ON COLUMN fine_tuned_models.job_id IS 'Fine-tuning job ID from provider (e.g., OpenAI)';
COMMENT ON COLUMN fine_tuned_models.model_id IS 'Provider model ID (e.g., ft:gpt-3.5-turbo:org:model:id)';
COMMENT ON COLUMN fine_tuned_models.status IS 'Model status: training, ready, failed, or deleted';
