/**
 * Cost Forecasting API client
 */

import { apiClient } from '@/utils/api';

export interface CostForecast {
  workflow_id: string;
  expected_queries: number;
  forecast_period_days: number;
  avg_cost_per_query: number;
  forecasted_total_cost: number;
  forecasted_daily_cost: number;
  forecasted_monthly_cost: number;
  confidence: 'low' | 'medium' | 'high' | 'none';
  sample_size: number;
  message?: string;
}

export interface CostForecastRequest {
  workflow_id: string;
  expected_queries: number;
  days?: number;
}

export interface CostTrend {
  workflow_id: string;
  period_days: number;
  daily_costs: Array<{
    date: string;
    avg_cost: number;
    query_count: number;
  }>;
  weekly_costs: Array<{
    week: string;
    avg_cost: number;
  }>;
  trend: 'increasing' | 'decreasing' | 'stable' | 'insufficient_data';
  total_queries: number;
  total_cost: number;
}

export interface CostBreakdown {
  workflow_id: string;
  period_days: number;
  breakdown: Record<string, {
    total_cost: number;
    avg_cost: number;
    count: number;
    percentage: number;
  }>;
  total_cost: number;
  total_queries: number;
}

export const costForecastingApi = {
  forecast: async (request: CostForecastRequest): Promise<CostForecast> => {
    const response = await apiClient.post<CostForecast>('/cost-forecast', {
      workflow_id: request.workflow_id,
      expected_queries: request.expected_queries,
      days: request.days || 30,
    });
    return response.data;
  },

  getTrends: async (workflowId: string, days: number = 30): Promise<CostTrend> => {
    const response = await apiClient.get<CostTrend>(`/cost-forecast/${workflowId}/trends`, {
      params: { days },
    });
    return response.data;
  },

  getBreakdown: async (workflowId: string, days: number = 30): Promise<CostBreakdown> => {
    const response = await apiClient.get<CostBreakdown>(`/cost-forecast/${workflowId}/breakdown`, {
      params: { days },
    });
    return response.data;
  },
};

