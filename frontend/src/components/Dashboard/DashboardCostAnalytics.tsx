/**
 * Cost Analytics Dashboard
 * 
 * Historical cost tracking and analytics:
 * - Daily/Weekly/Monthly cost statistics
 * - Cost breakdowns by category, provider, model
 * - Time series charts
 * - Cost history with pagination
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Calendar,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Filter,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import {
  getCostStats,
  getCostHistory,
  getCostBreakdown,
  type CostStats,
  type CostHistoryRecord,
  type CostBreakdownResponse,
} from '@/services/costIntelligence';
import { listWorkflows } from '@/services/workflowManagement';

interface DashboardCostAnalyticsProps {
  workflowId?: string | null;
}

type Period = 'daily' | 'weekly' | 'monthly';
type GroupBy = 'category' | 'provider' | 'model';

export function DashboardCostAnalytics({ workflowId }: DashboardCostAnalyticsProps) {
  const [period, setPeriod] = useState<Period>('daily');
  const [days, setDays] = useState(30);
  const [groupBy, setGroupBy] = useState<GroupBy>('category');
  const [historyPage, setHistoryPage] = useState(0);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(workflowId || null);

  // Fetch workflows for filter
  const { data: workflowsData } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => listWorkflows(),
  });

  // Fetch cost statistics
  const { data: stats, isLoading: statsLoading } = useQuery<CostStats>({
    queryKey: ['cost-stats', selectedWorkflowId, period, days],
    queryFn: () => getCostStats({ workflow_id: selectedWorkflowId || undefined, period, days }),
  });

  // Fetch cost breakdown
  const { data: breakdown, isLoading: breakdownLoading } = useQuery<CostBreakdownResponse>({
    queryKey: ['cost-breakdown', selectedWorkflowId, groupBy, days],
    queryFn: () => getCostBreakdown({ workflow_id: selectedWorkflowId || undefined, group_by: groupBy, days }),
  });

  // Fetch cost history
  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['cost-history', selectedWorkflowId, historyPage],
    queryFn: () => getCostHistory({ workflow_id: selectedWorkflowId || undefined, limit: 20, offset: historyPage * 20 }),
  });

  const workflows = workflowsData?.workflows || [];

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/10 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white mb-1">Cost Analytics</h2>
            <p className="text-sm text-slate-400">
              Historical cost tracking and detailed breakdowns
            </p>
          </div>
          <DollarSign className="w-6 h-6 text-green-400" />
        </div>
      </div>

      {/* Filters */}
      <div className="px-6 py-4 border-b border-white/10 flex-shrink-0 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {/* Workflow Filter */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 flex items-center gap-1">
              <Filter className="w-3 h-3" />
              Workflow
            </label>
            <select
              value={selectedWorkflowId || ''}
              onChange={(e) => setSelectedWorkflowId(e.target.value || null)}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="">All Workflows</option>
              {workflows.map((wf) => (
                <option key={wf.id} value={wf.id}>
                  {wf.name || 'Untitled'}
                </option>
              ))}
            </select>
          </div>

          {/* Period Filter */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              Period
            </label>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value as Period)}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          {/* Days Filter */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Time Range</label>
            <select
              value={days}
              onChange={(e) => setDays(parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
              <option value={365}>Last year</option>
            </select>
          </div>

          {/* Group By Filter */}
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 flex items-center gap-1">
              <PieChart className="w-3 h-3" />
              Group By
            </label>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value as GroupBy)}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:border-blue-500"
            >
              <option value="category">Category</option>
              <option value="provider">Provider</option>
              <option value="model">Model</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Summary Cards */}
        {statsLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
          </div>
        ) : stats ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <SummaryCard
                label="Total Cost"
                value={`$${(stats.total_cost || 0).toFixed(2)}`}
                icon={DollarSign}
                color="green"
              />
              <SummaryCard
                label="Total Executions"
                value={(stats.total_executions || 0).toLocaleString()}
                icon={BarChart3}
                color="blue"
              />
              <SummaryCard
                label="Total Records"
                value={(stats.total_records || 0).toLocaleString()}
                icon={TrendingUp}
                color="purple"
              />
            </div>

            {/* Breakdown Chart */}
            <div className="glass rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <PieChart className="w-5 h-5" />
                Cost Breakdown by {groupBy.charAt(0).toUpperCase() + groupBy.slice(1)}
              </h3>
              {breakdownLoading ? (
                <div className="flex items-center justify-center h-48">
                  <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
                </div>
              ) : breakdown ? (
                <BreakdownChart breakdown={breakdown.breakdown} totalCost={breakdown.total_cost} />
              ) : (
                <p className="text-slate-400 text-center py-8">No breakdown data available</p>
              )}
            </div>

            {/* Time Series Chart */}
            <div className="glass rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Cost Over Time ({period})
              </h3>
              {stats.period_data && stats.period_data.length > 0 ? (
                <TimeSeriesChart data={stats.period_data} period={period} />
              ) : (
                <p className="text-slate-400 text-center py-8">No time series data available</p>
              )}
            </div>

            {/* Cost History Table */}
            <div className="glass rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold text-white mb-4">Recent Cost Records</h3>
              {historyLoading ? (
                <div className="flex items-center justify-center h-48">
                  <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
                </div>
              ) : history && history.records.length > 0 ? (
                <>
                  <CostHistoryTable records={history.records} />
                  <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/10">
                    <button
                      onClick={() => setHistoryPage(Math.max(0, historyPage - 1))}
                      disabled={historyPage === 0}
                      className="px-4 py-2 bg-white/5 border border-white/10 rounded text-sm text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 flex items-center gap-2"
                    >
                      <ChevronLeft className="w-4 h-4" />
                      Previous
                    </button>
                    <span className="text-sm text-slate-400">
                      Page {historyPage + 1} • {history.count} total records
                    </span>
                    <button
                      onClick={() => setHistoryPage(historyPage + 1)}
                      disabled={history.count <= (historyPage + 1) * 20}
                      className="px-4 py-2 bg-white/5 border border-white/10 rounded text-sm text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 flex items-center gap-2"
                    >
                      Next
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </>
              ) : (
                <p className="text-slate-400 text-center py-8">No cost history available</p>
              )}
            </div>
          </>
        ) : (
          <div className="glass rounded-lg p-8 border border-white/10 text-center">
            <DollarSign className="w-12 h-12 text-slate-400 mx-auto mb-4 opacity-50" />
            <p className="text-slate-400">No cost data available for the selected period</p>
          </div>
        )}
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string;
  icon: any;
  color: 'green' | 'blue' | 'purple';
}) {
  const colorClasses = {
    green: 'text-green-400 bg-green-500/10 border-green-500/30',
    blue: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
    purple: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
  };

  return (
    <div className="glass rounded-lg p-6 border border-white/10">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-slate-400">{label}</span>
        <div className={cn('p-2 rounded', colorClasses[color])}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  );
}

function BreakdownChart({
  breakdown,
  totalCost,
}: {
  breakdown: Record<string, { cost: number; count: number }>;
  totalCost: number;
}) {
  const entries = Object.entries(breakdown).sort((a, b) => b[1].cost - a[1].cost);

  return (
    <div className="space-y-3">
      {entries.map(([key, data]) => {
        const percentage = totalCost > 0 ? (data.cost / totalCost) * 100 : 0;
        return (
          <div key={key} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-white font-medium capitalize">{key}</span>
              <div className="flex items-center gap-3">
                <span className="text-slate-400">{data.count} records</span>
                <span className="text-white font-semibold">${data.cost.toFixed(2)}</span>
                <span className="text-slate-500 text-xs">({percentage.toFixed(1)}%)</span>
              </div>
            </div>
            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-300"
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        );
      })}
      {entries.length === 0 && (
        <p className="text-slate-400 text-center py-4">No breakdown data</p>
      )}
    </div>
  );
}

function TimeSeriesChart({
  data,
  period,
}: {
  data: Array<{ period: string; total_cost: number; executions: number }>;
  period: Period;
}) {
  const maxCost = Math.max(...data.map((d) => d.total_cost), 1);

  return (
    <div className="space-y-4">
      <div className="flex items-end gap-2 h-48">
        {data.map((item, idx) => {
          const height = (item.total_cost / maxCost) * 100;
          const date = new Date(item.period);
          const label =
            period === 'daily'
              ? date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
              : period === 'weekly'
              ? `Week ${Math.floor((date.getDate() - 1) / 7) + 1}`
              : date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

          return (
            <div key={idx} className="flex-1 flex flex-col items-center group relative">
              <div
                className="w-full bg-gradient-to-t from-blue-500 to-cyan-500 rounded-t transition-all duration-300 hover:opacity-80 cursor-pointer"
                style={{ height: `${height}%` }}
                title={`${label}: $${item.total_cost.toFixed(2)}`}
              />
              <div className="mt-2 text-xs text-slate-400 text-center transform -rotate-45 origin-top-left whitespace-nowrap">
                {label}
              </div>
              <div className="absolute bottom-full mb-2 hidden group-hover:block bg-slate-800 border border-white/10 rounded px-2 py-1 text-xs text-white whitespace-nowrap z-10">
                ${item.total_cost.toFixed(2)}
                <br />
                {item.executions} execs
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CostHistoryTable({ records }: { records: CostHistoryRecord[] }) {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/10">
            <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase">Date</th>
            <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase">Node</th>
            <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase">Category</th>
            <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase">Provider</th>
            <th className="text-left py-3 px-4 text-xs font-semibold text-slate-400 uppercase">Model</th>
            <th className="text-right py-3 px-4 text-xs font-semibold text-slate-400 uppercase">Cost</th>
            <th className="text-right py-3 px-4 text-xs font-semibold text-slate-400 uppercase">Duration</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.id} className="border-b border-white/5 hover:bg-white/5">
              <td className="py-3 px-4 text-sm text-slate-300">{formatDate(record.created_at)}</td>
              <td className="py-3 px-4 text-sm text-white font-medium">{record.node_type}</td>
              <td className="py-3 px-4 text-sm text-slate-300 capitalize">{record.category}</td>
              <td className="py-3 px-4 text-sm text-slate-300">{record.provider || '-'}</td>
              <td className="py-3 px-4 text-sm text-slate-300">{record.model || '-'}</td>
              <td className="py-3 px-4 text-sm text-green-400 font-semibold text-right">
                ${record.cost.toFixed(6)}
              </td>
              <td className="py-3 px-4 text-sm text-slate-400 text-right">
                {record.duration_ms > 1000
                  ? `${(record.duration_ms / 1000).toFixed(2)}s`
                  : `${record.duration_ms}ms`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

