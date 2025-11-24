/**
 * Traces Dashboard Component - Visualize workflow execution traces
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, Clock, DollarSign, AlertCircle, CheckCircle2, XCircle, Eye, ChevronRight } from 'lucide-react';
import { tracesApi, type TraceListItem, type TraceDetail } from '@/services/traces';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';

interface DashboardTracesProps {
  workflowId?: string | null;
}

export function DashboardTraces({ workflowId }: DashboardTracesProps) {
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const { data: tracesData, isLoading } = useQuery({
    queryKey: ['traces', workflowId, filterStatus],
    queryFn: () => tracesApi.list({
      workflow_id: workflowId || undefined,
      limit: 100,
      status: filterStatus !== 'all' ? filterStatus : undefined,
    }),
  });

  const traces = Array.isArray(tracesData) ? tracesData : [];

  const { data: traceDetail } = useQuery({
    queryKey: ['trace', selectedTraceId],
    queryFn: () => tracesApi.get(selectedTraceId!),
    enabled: !!selectedTraceId,
  });

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
    return `${(ms / 60000).toFixed(2)}m`;
  };

  const formatCost = (cost: number) => {
    if (cost < 0.01) return `$${(cost * 1000).toFixed(2)}m`;
    return `$${cost.toFixed(4)}`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
      case 'running':
        return <Activity className="w-4 h-4 text-blue-400 animate-pulse" />;
      default:
        return <AlertCircle className="w-4 h-4 text-slate-400" />;
    }
  };

  if (selectedTraceId && traceDetail) {
    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSelectedTraceId(null)}
              className="text-slate-400 hover:text-white"
            >
              ← Back
            </button>
            <h2 className="text-lg font-semibold text-white">Trace Details</h2>
          </div>
          {getStatusIcon(traceDetail.status)}
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Trace Summary */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
              <div className="text-xs text-slate-400 mb-1">Total Cost</div>
              <div className="text-lg font-semibold text-white">{formatCost(traceDetail.total_cost)}</div>
            </div>
            <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
              <div className="text-xs text-slate-400 mb-1">Duration</div>
              <div className="text-lg font-semibold text-white">{formatDuration(traceDetail.total_duration_ms)}</div>
            </div>
            <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
              <div className="text-xs text-slate-400 mb-1">Spans</div>
              <div className="text-lg font-semibold text-white">{traceDetail.span_count}</div>
            </div>
            <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
              <div className="text-xs text-slate-400 mb-1">Tokens</div>
              <div className="text-lg font-semibold text-white">
                {traceDetail.total_tokens.total?.toLocaleString() || 'N/A'}
              </div>
            </div>
          </div>

          {/* Query */}
          {traceDetail.query && (
            <div className="bg-slate-800/50 border border-white/10 rounded-lg p-4">
              <div className="text-xs text-slate-400 mb-2">Query</div>
              <div className="text-sm text-white">{traceDetail.query}</div>
            </div>
          )}

          {/* Error */}
          {traceDetail.error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
              <div className="text-xs text-red-400 mb-2">Error</div>
              <div className="text-sm text-red-300">{traceDetail.error}</div>
            </div>
          )}

          {/* Spans */}
          <div>
            <h3 className="text-sm font-semibold text-white mb-4">Spans</h3>
            <div className="space-y-2">
              {traceDetail.spans.map((span, idx) => (
                <div
                  key={span.span_id}
                  className="bg-slate-800/50 border border-white/10 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs px-2 py-1 bg-purple-500/20 text-purple-300 rounded">
                        {span.span_type}
                      </span>
                      <span className="text-sm font-medium text-white">{span.name}</span>
                      {getStatusIcon(span.status)}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-400">
                      <span>{formatDuration(span.duration_ms)}</span>
                      <span>{formatCost(span.cost)}</span>
                    </div>
                  </div>
                  
                  {span.error && (
                    <div className="mt-2 text-xs text-red-400 bg-red-500/10 rounded p-2">
                      {span.error}
                    </div>
                  )}

                  {span.evaluation && (
                    <div className="mt-2 text-xs text-slate-400">
                      Evaluation: {JSON.stringify(span.evaluation, null, 2)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <h2 className="text-lg font-semibold text-white">Execution Traces</h2>
        <div className="flex items-center gap-2">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white"
          >
            <option value="all">All Status</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="running">Running</option>
          </select>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-slate-400">Loading traces...</div>
          </div>
        ) : traces.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <Activity className="w-12 h-12 text-slate-500 mb-4" />
            <p className="text-slate-400 mb-2">No traces found</p>
            <p className="text-sm text-slate-500">
              {workflowId ? 'Execute this workflow to see traces' : 'Execute workflows to see traces'}
            </p>
          </div>
        ) : (
          <div className="p-4 space-y-2">
            {traces.map((trace) => (
              <button
                key={trace.trace_id}
                onClick={() => setSelectedTraceId(trace.trace_id)}
                className="w-full text-left bg-slate-800/50 border border-white/10 rounded-lg p-4 hover:border-white/20 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {getStatusIcon(trace.status)}
                      <span className="text-sm font-medium text-white">
                        {trace.query || trace.execution_id}
                      </span>
                      <span className="text-xs text-slate-500">
                        {new Date(trace.started_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDuration(trace.total_duration_ms)}
                      </span>
                      <span className="flex items-center gap-1">
                        <DollarSign className="w-3 h-3" />
                        {formatCost(trace.total_cost)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Activity className="w-3 h-3" />
                        {trace.span_count} spans
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-400" />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

