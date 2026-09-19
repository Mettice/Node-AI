-- Migration: RLS hardening for tables the earlier migrations left open
-- Applied to the new Supabase project (Nodai, 2026-09-19) together with 000, 001, 004, 008 and 009.
--
-- In Supabase, a public table without RLS is readable and writable by anyone holding the
-- anon key, which ships in the frontend bundle. The backend uses the service role key,
-- which bypasses RLS, so none of this affects the API. The frontend does not query
-- tables directly.

-- 001: new tables (policies from 002_row_level_security.sql; usage_logs had none)
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE secret_access_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own usage logs" ON usage_logs;
CREATE POLICY "Users can view own usage logs" ON usage_logs FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can manage own webhooks" ON webhooks;
CREATE POLICY "Users can manage own webhooks" ON webhooks FOR ALL
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can view relevant shares" ON workflow_shares;
DROP POLICY IF EXISTS "Users can share own workflows" ON workflow_shares;
DROP POLICY IF EXISTS "Users can update own workflow shares" ON workflow_shares;
DROP POLICY IF EXISTS "Users can delete own workflow shares" ON workflow_shares;
CREATE POLICY "Users can view relevant shares" ON workflow_shares FOR SELECT USING (
    workflow_id IN (SELECT id FROM workflows WHERE user_id = auth.uid()) OR shared_with_user_id = auth.uid());
CREATE POLICY "Users can share own workflows" ON workflow_shares FOR INSERT WITH CHECK (
    workflow_id IN (SELECT id FROM workflows WHERE user_id = auth.uid()) AND shared_by = auth.uid());
CREATE POLICY "Users can update own workflow shares" ON workflow_shares FOR UPDATE USING (
    workflow_id IN (SELECT id FROM workflows WHERE user_id = auth.uid()));
CREATE POLICY "Users can delete own workflow shares" ON workflow_shares FOR DELETE USING (
    workflow_id IN (SELECT id FROM workflows WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can view own secret access logs" ON secret_access_log;
CREATE POLICY "Users can view own secret access logs" ON secret_access_log FOR SELECT USING (
    secret_id IN (SELECT id FROM secrets_vault WHERE user_id = auth.uid()));

-- 004: cost tracking tables had no RLS
ALTER TABLE cost_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_aggregations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view own cost records" ON cost_records;
DROP POLICY IF EXISTS "Users can view own cost aggregations" ON cost_aggregations;
CREATE POLICY "Users can view own cost records" ON cost_records FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can view own cost aggregations" ON cost_aggregations FOR SELECT USING (auth.uid() = user_id);

-- 009: its policies only applied if RLS was already on (it never is on a new table) and were
-- USING (true). The table has no user_id, so restrict it to the backend: RLS on, no policies.
DROP POLICY IF EXISTS "Users can view all models" ON fine_tuned_models;
DROP POLICY IF EXISTS "Users can insert models" ON fine_tuned_models;
DROP POLICY IF EXISTS "Users can update models" ON fine_tuned_models;
DROP POLICY IF EXISTS "Users can delete models" ON fine_tuned_models;
ALTER TABLE fine_tuned_models ENABLE ROW LEVEL SECURITY;

-- Supabase advisor: pin search_path on trigger functions
ALTER FUNCTION public.update_cost_aggregations() SET search_path = public;
ALTER FUNCTION public.update_mcp_server_configs_updated_at() SET search_path = public;
ALTER FUNCTION public.update_fine_tuned_models_updated_at() SET search_path = public;
