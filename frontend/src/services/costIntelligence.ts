/**
 * Cost Intelligence API services
 */

import { apiClient } from '@/utils/api';

export interface CostBreakdown {
  node_type: string;
  node_id: string;
  cost: number;
  tokens_used?: {
    input?: number;
    output?: number;
    total?: number;
  };
  model?: string;
  provider?: string;
  config?: Record<string, any>;
}

export interface CostAnalysis {
  execution_id: string;
  total_cost: number;
  breakdown: CostBreakdown[];
  top_cost_nodes: CostBreakdown[];
  cost_by_category: Record<string, number>;
  cost_by_provider: Record<string, number>;
  cost_by_model: Record<string, number>;
  suggestions: CostSuggestion[];
}

export interface CostSuggestion {
  type: string;
  node_id: string;
  message: string;
  current_cost: number;
  estimated_savings: number;
  impact: 'low' | 'medium' | 'high';
}

export interface CostPrediction {
  estimated_cost_per_run: number;
  estimated_cost_100_runs: number;
  estimated_cost_1000_runs: number;
  confidence: number;
  assumptions: string[];
}

export interface OptimizationSuggestion {
  node_id: string;
  node_type: string;
  current_config: Record<string, any>;
  suggested_config: Record<string, any>;
  current_cost: number;
  estimated_new_cost: number;
  savings_percentage: number;
  quality_impact: 'minimal' | 'low' | 'medium' | 'high';
  reasoning: string;
  priority?: 'low' | 'medium' | 'high';
}

export interface CostForecast {
  daily_costs: Array<{ date: string; cost: number; runs: number }>;
  weekly_trend: 'increasing' | 'decreasing' | 'stable';
  monthly_estimate: number;
  projected_monthly_cost: number;
  growth_rate: number;
}

export interface BudgetConfig {
  workflow_id: string;
  monthly_budget: number;
  alert_threshold?: number;
  enabled?: boolean;
}

export interface BudgetStatus {
  workflow_id: string;
  monthly_budget: number;
  current_spend: number;
  remaining: number;
  percentage_used: number;
  days_remaining: number;
  projected_monthly_spend: number;
  status: 'ok' | 'warning' | 'exceeded';
  alerts: string[];
}

export interface ROICalculation {
  workflow_id: string;
  total_cost: number;
  time_saved_hours?: number;
  hourly_rate?: number;
  value_generated?: number;
  roi_percentage: number;
  payback_period_days?: number;
  break_even_runs?: number;
}

/**
 * Analyze cost for a specific execution
 */
export async function analyzeExecutionCost(executionId: string): Promise<CostAnalysis> {
  const response = await apiClient.get<CostAnalysis>(`/cost/analyze/${executionId}`);
  return response.data;
}

/**
 * Predict cost for future workflow runs
 */
export async function predictWorkflowCost(params?: {
  execution_id?: string;
  workflow_id?: string;
  num_runs?: number;
}): Promise<CostPrediction> {
  const response = await apiClient.get<CostPrediction>('/cost/predict', { params });
  return response.data;
}

/**
 * Get cost optimization suggestions
 */
export async function getCostOptimizations(executionId: string): Promise<OptimizationSuggestion[]> {
  const response = await apiClient.get<OptimizationSuggestion[]>(`/cost/optimize/${executionId}`);
  return response.data;
}

/**
 * Get cost forecast for a workflow
 */
export async function getCostForecast(workflowId: string, days: number = 30): Promise<CostForecast> {
  const response = await apiClient.get<CostForecast>(`/cost/forecast/${workflowId}`, {
    params: { days },
  });
  return response.data;
}

/**
 * Set budget for a workflow
 */
export async function setBudget(config: BudgetConfig): Promise<BudgetConfig> {
  const response = await apiClient.post<BudgetConfig>('/cost/budget', config);
  return response.data;
}

/**
 * Get budget status for a workflow
 */
export async function getBudgetStatus(workflowId: string): Promise<BudgetStatus> {
  const response = await apiClient.get<BudgetStatus>(`/cost/budget/${workflowId}`);
  return response.data;
}

/**
 * Calculate ROI for a workflow
 */
export async function calculateROI(params: {
  workflow_id: string;
  time_saved_hours?: number;
  hourly_rate?: number;
  value_generated?: number;
}): Promise<ROICalculation> {
  const response = await apiClient.post<ROICalculation>('/cost/roi', params);
  return response.data;
}

