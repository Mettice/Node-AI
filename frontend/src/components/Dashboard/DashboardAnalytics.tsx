/**
 * Dashboard Analytics Tab
 * 
 * Advanced analytics:
 * - Version comparison
 * - Performance trends across workflows
 * - Cost analysis
 * - Usage patterns
 * - Cross-workflow insights
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  TrendingUp, 
  BarChart3, 
  DollarSign, 
  GitCompare,
  Activity,
  Loader2,
  ArrowUpRight,
  ArrowDownRight,
  Minus
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { 
  compareWorkflowVersions, 
  type VersionComparison 
} from '@/services/metrics';
import { 
  getQualityTrends, 
  type QualityTrends 
} from '@/services/ragEvaluation';
import { listWorkflows } from '@/services/workflowManagement';

interface DashboardAnalyticsProps {
  selectedWorkflowId: string | null;
}

type AnalyticsView = 'overview' | 'version-comparison' | 'quality-trends' | 'cross-workflow';

export function DashboardAnalytics({ selectedWorkflowId }: DashboardAnalyticsProps) {
  const [view, setView] = useState<AnalyticsView>('overview');
  const [selectedWorkflow] = useState<string | null>(selectedWorkflowId);
  const [currentVersion, setCurrentVersion] = useState<string>('v2.1');
  const [previousVersion, setPreviousVersion] = useState<string>('v2.0');

  const { data: workflowsData } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => listWorkflows(),
    retry: false,
  });

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/10 flex-shrink-0">
        <h2 className="text-xl font-semibold text-white mb-2">Analytics</h2>
        <p className="text-sm text-slate-400">
          Advanced analytics, version comparison, and cross-workflow insights
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-white/10 flex-shrink-0">
        <button
          onClick={() => setView('overview')}
          className={cn(
            'px-4 py-3 text-sm font-medium transition-colors flex items-center gap-2',
            view === 'overview'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-slate-400 hover:text-slate-300'
          )}
        >
          <BarChart3 className="w-4 h-4" />
          Overview
        </button>
        <button
          onClick={() => setView('version-comparison')}
          className={cn(
            'px-4 py-3 text-sm font-medium transition-colors flex items-center gap-2',
            view === 'version-comparison'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-slate-400 hover:text-slate-300'
          )}
        >
          <GitCompare className="w-4 h-4" />
          Version Comparison
        </button>
        <button
          onClick={() => setView('quality-trends')}
          className={cn(
            'px-4 py-3 text-sm font-medium transition-colors flex items-center gap-2',
            view === 'quality-trends'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-slate-400 hover:text-slate-300'
          )}
        >
          <TrendingUp className="w-4 h-4" />
          Quality Trends
        </button>
        <button
          onClick={() => setView('cross-workflow')}
          className={cn(
            'px-4 py-3 text-sm font-medium transition-colors flex items-center gap-2',
            view === 'cross-workflow'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-slate-400 hover:text-slate-300'
          )}
        >
          <Activity className="w-4 h-4" />
          Cross-Workflow
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {view === 'overview' && (
          <OverviewView selectedWorkflowId={selectedWorkflow} />
        )}
        {view === 'version-comparison' && (
          <VersionComparisonView
            workflowId={selectedWorkflow}
            currentVersion={currentVersion}
            previousVersion={previousVersion}
            onCurrentVersionChange={setCurrentVersion}
            onPreviousVersionChange={setPreviousVersion}
          />
        )}
        {view === 'quality-trends' && (
          <QualityTrendsView workflowId={selectedWorkflow} />
        )}
        {view === 'cross-workflow' && (
          <CrossWorkflowView workflows={Array.isArray(workflowsData) ? workflowsData : (workflowsData?.workflows || [])} />
        )}
      </div>
    </div>
  );
}

function OverviewView({ selectedWorkflowId }: { selectedWorkflowId: string | null }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass rounded-lg p-6 border border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-white">Version Comparison</h3>
            <GitCompare className="w-5 h-5 text-purple-400" />
          </div>
          <p className="text-sm text-slate-400 mb-4">
            Compare workflow versions side-by-side
          </p>
          <div className="text-2xl font-bold text-white">Available</div>
        </div>

        <div className="glass rounded-lg p-6 border border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-white">Performance Trends</h3>
            <TrendingUp className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-sm text-slate-400 mb-4">
            Track quality metrics over time
          </p>
          <div className="text-2xl font-bold text-white">Available</div>
        </div>

        <div className="glass rounded-lg p-6 border border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-white">Cost Analysis</h3>
            <DollarSign className="w-5 h-5 text-green-400" />
          </div>
          <p className="text-sm text-slate-400 mb-4">
            Cross-workflow cost insights
          </p>
          <div className="text-2xl font-bold text-white">Available</div>
        </div>
      </div>

      {!selectedWorkflowId && (
        <div className="glass rounded-lg p-8 border border-white/10 text-center">
          <BarChart3 className="w-12 h-12 text-slate-400 mx-auto mb-4 opacity-50" />
          <p className="text-slate-400">
            Select a workflow from the Metrics tab to view detailed analytics
          </p>
        </div>
      )}
    </div>
  );
}

function VersionComparisonView({
  workflowId,
  currentVersion,
  previousVersion,
  onCurrentVersionChange,
  onPreviousVersionChange,
}: {
  workflowId: string | null;
  currentVersion: string;
  previousVersion: string;
  onCurrentVersionChange: (v: string) => void;
  onPreviousVersionChange: (v: string) => void;
}) {
  const { data: comparison, isLoading, error } = useQuery<VersionComparison>({
    queryKey: ['version-comparison', workflowId, currentVersion, previousVersion],
    queryFn: () => {
      if (!workflowId) throw new Error('No workflow selected');
      return compareWorkflowVersions(workflowId, currentVersion, previousVersion);
    },
    enabled: !!workflowId && !!currentVersion,
    retry: false, // Don't retry on validation errors
  });

  if (!workflowId) {
    return (
      <div className="glass rounded-lg p-8 border border-white/10 text-center">
        <GitCompare className="w-12 h-12 text-slate-400 mx-auto mb-4 opacity-50" />
        <p className="text-slate-400">Select a workflow to compare versions</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass rounded-lg p-8 border border-red-500/50 text-center">
        <p className="text-red-400 mb-2">Error loading version comparison</p>
        <p className="text-slate-400 text-sm">
          {error instanceof Error ? error.message : 'Unknown error occurred'}
        </p>
      </div>
    );
  }

  if (!comparison) {
    return (
      <div className="glass rounded-lg p-8 border border-white/10 text-center">
        <p className="text-slate-400">No version comparison data available</p>
      </div>
    );
  }

  const formatChange = (value: number | undefined | null, isPercent: boolean = false) => {
    if (value === undefined || value === null || isNaN(value)) return null;
    const absValue = Math.abs(value);
    const sign = value > 0 ? '+' : value < 0 ? '-' : '';
    const formatted = isPercent ? `${absValue.toFixed(1)}%` : absValue.toFixed(2);
    return { sign, value: formatted, isPositive: value > 0, isNegative: value < 0 };
  };

  const responseTimeChange = formatChange(comparison.comparison.response_time_change_pct, true);
  const costChange = formatChange(comparison.comparison.cost_change_pct, true);
  const successRateChange = formatChange(comparison.comparison.success_rate_change_pct, true);

  return (
    <div className="space-y-6">
      {/* Version Selectors */}
      <div className="glass rounded-lg p-4 border border-white/10">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-slate-400 mb-2">Current Version</label>
            <input
              type="text"
              value={currentVersion}
              onChange={(e) => onCurrentVersionChange(e.target.value)}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:border-blue-500"
              placeholder="v2.1"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-2">Previous Version</label>
            <input
              type="text"
              value={previousVersion}
              onChange={(e) => onPreviousVersionChange(e.target.value)}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:border-blue-500"
              placeholder="v2.0"
            />
          </div>
        </div>
      </div>

      {/* Comparison Results */}
      <div className="grid grid-cols-2 gap-6">
        {/* Current Version */}
        <div className="glass rounded-lg p-6 border border-blue-500/50 bg-blue-500/5">
          <h3 className="font-semibold text-white mb-4">Current: {comparison.current_version || 'N/A'}</h3>
          {comparison.current_metrics ? (
            <div className="space-y-4">
              <MetricCard
                label="Avg Response Time"
                value={`${((comparison.current_metrics?.avg_response_time_ms ?? 0) || 0).toFixed(0)}ms`}
              />
              <MetricCard
                label="Cost per Query"
                value={`$${((comparison.current_metrics?.cost_per_query ?? 0) || 0).toFixed(4)}`}
              />
              <MetricCard
                label="Success Rate"
                value={`${((comparison.current_metrics?.success_rate ?? 0) || 0).toFixed(1)}%`}
              />
              <MetricCard
                label="Total Queries"
                value={((comparison.current_metrics?.total_queries ?? 0) || 0).toString()}
              />
            </div>
          ) : (
            <p className="text-slate-400 text-sm">No current version data</p>
          )}
        </div>

        {/* Previous Version */}
        <div className="glass rounded-lg p-6 border border-white/10">
          <h3 className="font-semibold text-white mb-4">
            Previous: {comparison.previous_version || 'N/A'}
          </h3>
          {comparison.previous_metrics ? (
            <div className="space-y-4">
              <MetricCard
                label="Avg Response Time"
                value={`${((comparison.previous_metrics?.avg_response_time_ms ?? 0) || 0).toFixed(0)}ms`}
              />
              <MetricCard
                label="Cost per Query"
                value={`$${((comparison.previous_metrics?.cost_per_query ?? 0) || 0).toFixed(4)}`}
              />
              <MetricCard
                label="Success Rate"
                value={`${((comparison.previous_metrics?.success_rate ?? 0) || 0).toFixed(1)}%`}
              />
              <MetricCard
                label="Total Queries"
                value={((comparison.previous_metrics?.total_queries ?? 0) || 0).toString()}
              />
            </div>
          ) : (
            <p className="text-slate-400 text-sm">No previous version data</p>
          )}
        </div>
      </div>

      {/* Changes Summary */}
      {comparison.previous_metrics && (
        <div className="glass rounded-lg p-6 border border-white/10">
          <h3 className="font-semibold text-white mb-4">Changes Summary</h3>
          <div className="grid grid-cols-3 gap-4">
            {responseTimeChange && (
              <ChangeCard
                label="Response Time"
                change={responseTimeChange}
                isPositive={!responseTimeChange.isNegative}
              />
            )}
            {costChange && (
              <ChangeCard
                label="Cost per Query"
                change={costChange}
                isPositive={costChange.isNegative}
              />
            )}
            {successRateChange && (
              <ChangeCard
                label="Success Rate"
                change={successRateChange}
                isPositive={successRateChange.isPositive}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function QualityTrendsView({ workflowId }: { workflowId: string | null }) {
  const [days, setDays] = useState(30);

  const { data: trends, isLoading } = useQuery<QualityTrends>({
    queryKey: ['quality-trends', workflowId, days],
    queryFn: () => getQualityTrends(workflowId || undefined, days),
    enabled: !!workflowId,
  });

  if (!workflowId) {
    return (
      <div className="glass rounded-lg p-8 border border-white/10 text-center">
        <TrendingUp className="w-12 h-12 text-slate-400 mx-auto mb-4 opacity-50" />
        <p className="text-slate-400">Select a workflow to view quality trends</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="glass rounded-lg p-4 border border-white/10">
        <label className="block text-xs text-slate-400 mb-2">Time Range</label>
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

      {/* Trends Display */}
      {trends && trends.trends && Array.isArray(trends.trends) && trends.trends.length > 0 ? (
        <div className="space-y-4">
          {trends.trends.map((trend, idx) => (
            <div key={idx} className="glass rounded-lg p-4 border border-white/10">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-white">{trend.date || 'N/A'}</span>
                <span className="text-xs text-slate-400">{trend.evaluation_count || 0} evaluations</span>
              </div>
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-slate-400 mb-1">Accuracy</div>
                  <div className="text-white font-semibold">{((trend.avg_accuracy || 0) * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <div className="text-slate-400 mb-1">Relevance</div>
                  <div className="text-white font-semibold">{((trend.avg_relevance || 0) * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <div className="text-slate-400 mb-1">Latency</div>
                  <div className="text-white font-semibold">
                    {(trend.avg_latency_ms || 0) > 1000
                      ? `${((trend.avg_latency_ms || 0) / 1000).toFixed(1)}s`
                      : `${(trend.avg_latency_ms || 0).toFixed(0)}ms`}
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 mb-1">Cost/Query</div>
                  <div className="text-white font-semibold">${(trend.avg_cost_per_query || 0).toFixed(4)}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="glass rounded-lg p-8 border border-white/10 text-center">
          <p className="text-slate-400">No quality trend data available</p>
        </div>
      )}
    </div>
  );
}

function CrossWorkflowView({ workflows }: { workflows: any[] }) {
  const safeWorkflows = Array.isArray(workflows) ? workflows : [];
  return (
    <div className="space-y-6">
      <div className="glass rounded-lg p-6 border border-white/10">
        <h3 className="font-semibold text-white mb-4">Cross-Workflow Analysis</h3>
        <p className="text-slate-400 text-sm mb-4">
          Compare performance across all workflows
        </p>
        {safeWorkflows.length > 0 ? (
          <div className="space-y-3">
            {safeWorkflows.map((workflow) => (
              <div
                key={workflow.id}
                className="p-4 bg-white/5 rounded border border-white/10"
              >
                <div className="flex items-center justify-between">
                  <span className="text-white font-medium">{workflow.name || 'Untitled'}</span>
                  <span className="text-xs text-slate-400">View metrics →</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 text-sm">No workflows available</p>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className="text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

function ChangeCard({
  label,
  change,
  isPositive,
}: {
  label: string;
  change: { sign: string; value: string; isPositive: boolean; isNegative: boolean };
  isPositive: boolean;
}) {
  const Icon = isPositive ? ArrowUpRight : change.sign === '-' ? ArrowDownRight : Minus;
  const colorClass = isPositive ? 'text-green-400' : change.sign === '-' ? 'text-red-400' : 'text-slate-400';

  return (
    <div className="p-4 bg-white/5 rounded border border-white/10">
      <div className="text-xs text-slate-400 mb-2">{label}</div>
      <div className={cn('flex items-center gap-2 text-lg font-semibold', colorClass)}>
        <Icon className="w-4 h-4" />
        <span>
          {change.sign}
          {change.value}
        </span>
      </div>
    </div>
  );
}
