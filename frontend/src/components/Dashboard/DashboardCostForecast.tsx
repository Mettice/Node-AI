/**
 * Cost Forecasting Dashboard Component
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { DollarSign, TrendingUp, TrendingDown, Minus, BarChart3, PieChart, Calendar } from 'lucide-react';
import { costForecastingApi, type CostForecast, type CostTrend, type CostBreakdown } from '@/services/costForecasting';
import { listWorkflows } from '@/services/workflowManagement';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';

interface DashboardCostForecastProps {
  workflowId?: string | null;
}

export function DashboardCostForecast({ workflowId }: DashboardCostForecastProps) {
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(workflowId || null);
  const [expectedQueries, setExpectedQueries] = useState<number>(1000);
  const [forecastDays, setForecastDays] = useState<number>(30);

  const { data: workflows } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => listWorkflows({ limit: 100 }),
  });

  const { data: forecast, isLoading: forecastLoading } = useQuery({
    queryKey: ['cost-forecast', selectedWorkflowId, expectedQueries, forecastDays],
    queryFn: () => costForecastingApi.forecast({
      workflow_id: selectedWorkflowId!,
      expected_queries: expectedQueries,
      days: forecastDays,
    }),
    enabled: !!selectedWorkflowId,
  });

  const { data: trends } = useQuery({
    queryKey: ['cost-trends', selectedWorkflowId],
    queryFn: () => costForecastingApi.getTrends(selectedWorkflowId!, 30),
    enabled: !!selectedWorkflowId,
  });

  const { data: breakdown } = useQuery({
    queryKey: ['cost-breakdown', selectedWorkflowId],
    queryFn: () => costForecastingApi.getBreakdown(selectedWorkflowId!, 30),
    enabled: !!selectedWorkflowId,
  });

  const formatCost = (cost: number) => {
    if (cost < 0.01) return `$${(cost * 1000).toFixed(2)}m`;
    if (cost < 1) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(2)}`;
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return 'text-green-400';
      case 'medium':
        return 'text-yellow-400';
      case 'low':
        return 'text-orange-400';
      default:
        return 'text-slate-400';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUp className="w-4 h-4 text-red-400" />;
      case 'decreasing':
        return <TrendingDown className="w-4 h-4 text-green-400" />;
      default:
        return <Minus className="w-4 h-4 text-slate-400" />;
    }
  };

  if (!selectedWorkflowId) {
    return (
      <div className="h-full flex flex-col p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Cost Forecasting</h2>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <DollarSign className="w-12 h-12 text-slate-500 mx-auto mb-4" />
            <p className="text-slate-400 mb-2">Select a workflow to view cost forecasts</p>
            {workflows?.workflows && workflows.workflows.length > 0 && (
              <select
                value={selectedWorkflowId || ''}
                onChange={(e) => setSelectedWorkflowId(e.target.value || null)}
                className="mt-4 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white"
              >
                <option value="">Select workflow...</option>
                {workflows.workflows.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name || w.id}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Cost Forecasting</h2>
          <select
            value={selectedWorkflowId}
            onChange={(e) => setSelectedWorkflowId(e.target.value || null)}
            className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white"
          >
            {workflows?.workflows?.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name || w.id}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Expected Queries</label>
            <input
              type="number"
              value={expectedQueries}
              onChange={(e) => setExpectedQueries(parseInt(e.target.value) || 0)}
              className="w-32 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white"
              min="1"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Forecast Period (days)</label>
            <input
              type="number"
              value={forecastDays}
              onChange={(e) => setForecastDays(parseInt(e.target.value) || 30)}
              className="w-32 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white"
              min="1"
              max="365"
            />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {forecastLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-slate-400">Calculating forecast...</div>
          </div>
        ) : forecast ? (
          <>
            {/* Forecast Summary */}
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
                <div className="text-xs text-slate-400 mb-1">Avg Cost/Query</div>
                <div className="text-lg font-semibold text-white">
                  {formatCost(forecast.avg_cost_per_query)}
                </div>
              </div>
              <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
                <div className="text-xs text-slate-400 mb-1">Forecasted Total</div>
                <div className="text-lg font-semibold text-white">
                  {formatCost(forecast.forecasted_total_cost)}
                </div>
              </div>
              <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
                <div className="text-xs text-slate-400 mb-1">Daily Cost</div>
                <div className="text-lg font-semibold text-white">
                  {formatCost(forecast.forecasted_daily_cost)}
                </div>
              </div>
              <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
                <div className="text-xs text-slate-400 mb-1">Confidence</div>
                <div className={cn("text-lg font-semibold", getConfidenceColor(forecast.confidence))}>
                  {forecast.confidence.toUpperCase()}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {forecast.sample_size} samples
                </div>
              </div>
            </div>

            {forecast.message && (
              <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 text-sm text-blue-300">
                {forecast.message}
              </div>
            )}

            {/* Cost Trends */}
            {trends && (
              <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <BarChart3 className="w-4 h-4" />
                    Cost Trends (Last 30 Days)
                  </h3>
                  <div className="flex items-center gap-2">
                    {getTrendIcon(trends.trend)}
                    <span className="text-xs text-slate-400 capitalize">{trends.trend}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  {trends.daily_costs.slice(-7).map((day) => (
                    <div key={day.date} className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">{new Date(day.date).toLocaleDateString()}</span>
                      <div className="flex items-center gap-4">
                        <span className="text-slate-300">{day.query_count} queries</span>
                        <span className="text-white font-medium">{formatCost(day.avg_cost)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Cost Breakdown */}
            {breakdown && breakdown.total_cost > 0 && (
              <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <PieChart className="w-4 h-4" />
                  Cost Breakdown by Span Type
                </h3>
                <div className="space-y-3">
                  {Object.entries(breakdown.breakdown)
                    .sort(([, a], [, b]) => b.total_cost - a.total_cost)
                    .map(([spanType, data]) => (
                      <div key={spanType}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-slate-300 capitalize">{spanType.replace('_', ' ')}</span>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="text-slate-400">{data.count} spans</span>
                            <span className="text-white font-medium">{formatCost(data.total_cost)}</span>
                            <span className="text-slate-500">({data.percentage.toFixed(1)}%)</span>
                          </div>
                        </div>
                        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-purple-500 rounded-full"
                            style={{ width: `${data.percentage}%` }}
                          />
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <DollarSign className="w-12 h-12 text-slate-500 mb-4" />
            <p className="text-slate-400 mb-2">No forecast data available</p>
            <p className="text-sm text-slate-500">
              Execute this workflow to generate historical data for forecasting
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

