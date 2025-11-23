/**
 * Metrics Dashboard Component
 * 
 * Displays production metrics, performance trends, cost breakdown,
 * quality metrics, and alerts for deployed workflows.
 */

import { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  DollarSign,
  BarChart3,
  Activity,
  Download,
  RefreshCw,
  ArrowLeft
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { getWorkflowMetrics, type MetricsResponse } from '@/services/metrics';
import toast from 'react-hot-toast';

interface MetricsDashboardProps {
  workflowId: string;
  onBack?: () => void;
}

export function MetricsDashboard({ workflowId, onBack }: MetricsDashboardProps) {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(24); // hours

  const loadMetrics = async () => {
    setLoading(true);
    try {
      const data = await getWorkflowMetrics(workflowId, timeRange);
      setMetrics(data);
    } catch (error: any) {
      console.error('Error loading metrics:', error);
      toast.error('Failed to load metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (workflowId) {
      loadMetrics();
    }
  }, [workflowId, timeRange]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading metrics...</div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-slate-400">
        <BarChart3 className="w-12 h-12 mb-4 opacity-50" />
        <p>No metrics available</p>
      </div>
    );
  }

  const formatCurrency = (value: number | undefined | null) => {
    if (value === undefined || value === null || isNaN(value)) return '$0.00';
    return `$${value.toFixed(2)}`;
  };
  const formatPercent = (value: number | undefined | null) => {
    if (value === undefined || value === null || isNaN(value)) return '0.0%';
    return `${value.toFixed(1)}%`;
  };
  const formatTime = (ms: number | undefined | null) => {
    if (ms === undefined || ms === null || isNaN(ms)) return '0ms';
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  // Calculate cost breakdown percentages
  const costBreakdown = metrics.cost_breakdown || {};
  const totalCostBreakdown = Object.values(costBreakdown).reduce((a, b) => (a || 0) + (b || 0), 0);
  const costBreakdownEntries = Object.entries(costBreakdown)
    .map(([category, cost]) => ({
      category: category.charAt(0).toUpperCase() + category.slice(1).replace('_', ' '),
      cost: cost || 0,
      percentage: totalCostBreakdown > 0 ? ((cost || 0) / totalCostBreakdown) * 100 : 0,
    }))
    .sort((a, b) => b.cost - a.cost);

  // Get top error
  const qualityMetrics = metrics.quality_metrics || {};
  const errorBreakdown = qualityMetrics.error_breakdown || {};
  const errorEntries = Object.entries(errorBreakdown);
  const topError = errorEntries.length > 0 
    ? errorEntries.sort((a, b) => (b[1] || 0) - (a[1] || 0))[0]
    : null;

  return (
    <div className="p-6 space-y-6 min-h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors text-slate-400 hover:text-white"
              title="Back to workflow list"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div>
            <h2 className="text-2xl font-bold text-white">Production Dashboard</h2>
            <p className="text-sm text-slate-400 mt-1">
              Metrics for the last {timeRange} hours
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all hover:bg-white/8 hover:border-white/20 appearance-none cursor-pointer"
          >
            <option value={24} className="bg-slate-800 text-white">Last 24 Hours</option>
            <option value={168} className="bg-slate-800 text-white">Last 7 Days</option>
            <option value={720} className="bg-slate-800 text-white">Last 30 Days</option>
          </select>
          <button
            onClick={loadMetrics}
            className="p-2 hover:bg-white/5 rounded transition-colors"
            title="Refresh metrics"
          >
            <RefreshCw className="w-5 h-5 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Queries */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Total Queries</span>
            <Activity className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {metrics.total_queries.toLocaleString()}
          </div>
        </div>

        {/* Success Rate */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Success Rate</span>
            <CheckCircle className="w-4 h-4 text-green-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {formatPercent(metrics.success_rate ?? 0)}
          </div>
        </div>

        {/* Avg Response Time */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Avg Response Time</span>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {formatTime(metrics.avg_response_time_ms ?? 0)}
          </div>
        </div>

        {/* Total Cost */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Total Cost</span>
            <DollarSign className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {formatCurrency(metrics.total_cost ?? 0)}
          </div>
        </div>

        {/* Cost per Query */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Cost per Query</span>
            <DollarSign className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {formatCurrency(metrics.cost_per_query ?? 0)}
          </div>
        </div>
      </div>

      {/* Performance Trends & Cost Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Trends */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Performance Trends</h3>
          {metrics.performance_trends && metrics.performance_trends.length > 0 ? (
            <div className="space-y-3">
              {/* Simple line chart representation */}
              <div className="h-48 flex items-end gap-2">
                {metrics.performance_trends.slice(-12).map((trend, idx) => {
                  const trends = metrics.performance_trends || [];
                  const maxTime = Math.max(...trends.map(t => t?.avg_response_time_ms || 0), 1);
                  const trendTime = trend?.avg_response_time_ms || 0;
                  const height = maxTime > 0 ? (trendTime / maxTime) * 100 : 0;
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center">
                      <div
                        className="w-full bg-purple-500 rounded-t transition-all hover:bg-purple-400"
                        style={{ height: `${height}%` }}
                        title={`${trend?.timestamp ? new Date(trend.timestamp).toLocaleTimeString() : 'N/A'}: ${formatTime(trendTime)}`}
                      />
                    </div>
                  );
                })}
              </div>
              <div className="text-xs text-slate-400 text-center">
                Response time over time (last 12 hours)
              </div>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-slate-400">
              No performance data available
            </div>
          )}
        </div>

        {/* Cost Breakdown */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Cost Breakdown</h3>
          {costBreakdownEntries.length > 0 ? (
            <div className="space-y-3">
              {costBreakdownEntries.map((item) => (
                <div key={item.category}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-slate-300">{item.category}</span>
                    <span className="text-sm font-medium text-white">
                      {formatCurrency(item.cost)} ({formatPercent(item.percentage)})
                    </span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-slate-400">No cost data available</div>
          )}
        </div>
      </div>

      {/* Quality Metrics & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quality Metrics */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Quality Metrics</h3>
          <div className="space-y-4">
            {qualityMetrics.avg_relevance_score !== null && qualityMetrics.avg_relevance_score !== undefined && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-400">Avg Relevance Score</span>
                  <span className="text-lg font-semibold text-white">
                    {(qualityMetrics.avg_relevance_score ?? 0).toFixed(2)}
                  </span>
                </div>
                <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500"
                    style={{ width: `${(qualityMetrics.avg_relevance_score ?? 0) * 100}%` }}
                  />
                </div>
              </div>
            )}
            
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">Failed Queries</span>
                <span className="text-lg font-semibold text-red-400">
                  {qualityMetrics.failed_queries ?? 0} ({formatPercent(qualityMetrics.failure_rate ?? 0)})
                </span>
              </div>
              {topError && (
                <div className="mt-2 text-xs text-slate-400">
                  <span className="text-slate-500">Top failure:</span> "{topError[0]}" ({topError[1]} cases)
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Alerts */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Alerts</h3>
          {metrics.alerts && metrics.alerts.length > 0 ? (
            <div className="space-y-3">
              {metrics.alerts.map((alert, idx) => (
                <div
                  key={idx}
                  className={cn(
                    "flex items-start gap-3 p-3 rounded-lg",
                    alert?.type === "warning" 
                      ? "bg-orange-500/10 border border-orange-500/20"
                      : "bg-blue-500/10 border border-blue-500/20"
                  )}
                >
                  <AlertTriangle className={cn(
                    "w-5 h-5 flex-shrink-0 mt-0.5",
                    alert?.type === "warning" ? "text-orange-400" : "text-blue-400"
                  )} />
                  <span className="text-sm text-slate-300">{alert?.message || 'Alert'}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-slate-400">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <span>No alerts - all systems operational</span>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => {
            // TODO: Implement export
            toast('Export functionality coming soon', { icon: 'ℹ️' });
          }}
          className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-white transition-colors"
        >
          <Download className="w-4 h-4" />
          <span>Export Report</span>
        </button>
        <button
          onClick={() => {
            // TODO: Navigate to full analytics
            toast('Full analytics view coming soon', { icon: 'ℹ️' });
          }}
          className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-white transition-colors"
        >
          <BarChart3 className="w-4 h-4" />
          <span>View Full Analytics</span>
        </button>
      </div>
    </div>
  );
}

