/**
 * Deployment Manager Component
 * 
 * Manages deployment versions, health, and rollback for workflows
 */

import { useState, useEffect } from 'react';
import {
  Clock,
  CheckCircle,
  XCircle,
  RotateCcw,
  Activity,
  TrendingUp,
  DollarSign,
  AlertCircle,
  Loader2,
  GitBranch,
  History,
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listDeploymentVersions,
  rollbackDeployment,
  getDeploymentHealth,
  type DeploymentVersion,
  type DeploymentHealth,
} from '@/services/deployment';
import { deployWorkflow } from '@/services/workflowManagement';
import toast from 'react-hot-toast';
import { cn } from '@/utils/cn';

interface DeploymentManagerProps {
  workflowId: string;
  workflowName: string;
}

export function DeploymentManager({ workflowId, workflowName }: DeploymentManagerProps) {
  const queryClient = useQueryClient();
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);

  // Fetch deployment versions
  const { data: deployments, isLoading: loadingVersions } = useQuery({
    queryKey: ['deployments', workflowId],
    queryFn: () => listDeploymentVersions(workflowId),
    enabled: !!workflowId,
  });

  // Fetch deployment health
  const { data: health, isLoading: loadingHealth } = useQuery({
    queryKey: ['deployment-health', workflowId],
    queryFn: () => getDeploymentHealth(workflowId),
    enabled: !!workflowId,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Rollback mutation
  const rollbackMutation = useMutation({
    mutationFn: ({ versionNumber }: { versionNumber: number }) =>
      rollbackDeployment(workflowId, versionNumber),
    onSuccess: () => {
      toast.success('Deployment rolled back successfully');
      queryClient.invalidateQueries({ queryKey: ['deployments', workflowId] });
      queryClient.invalidateQueries({ queryKey: ['deployment-health', workflowId] });
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to rollback deployment');
    },
  });

  const handleRollback = (versionNumber: number) => {
    if (!confirm(`Rollback to version ${versionNumber}? This will restore the workflow to that deployment state.`)) {
      return;
    }
    rollbackMutation.mutate({ versionNumber });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'inactive':
        return <XCircle className="w-4 h-4 text-slate-400" />;
      case 'rolled_back':
        return <RotateCcw className="w-4 h-4 text-orange-400" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'inactive':
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
      case 'rolled_back':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'failed':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  if (loadingVersions || loadingHealth) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
      </div>
    );
  }

  const versions = deployments?.versions || [];
  const activeVersion = versions.find(v => v.status === 'active');

  return (
    <div className="space-y-6">
      {/* Health Status Card */}
      {health && health.status !== 'not_deployed' && (
        <div className="glass rounded-lg p-6 border border-white/10">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white mb-1">Deployment Health</h3>
              <p className="text-sm text-slate-400">Current deployment status and metrics</p>
            </div>
            <div className={cn(
              'px-3 py-1 rounded-lg text-sm font-medium border flex items-center gap-2',
              health.healthy
                ? 'bg-green-500/20 text-green-400 border-green-500/30'
                : 'bg-red-500/20 text-red-400 border-red-500/30'
            )}>
              {health.healthy ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  <span>Healthy</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4" />
                  <span>Unhealthy</span>
                </>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="glass rounded-lg p-4 border border-white/10">
              <div className="flex items-center gap-2 text-slate-400 mb-1">
                <Activity className="w-4 h-4" />
                <span className="text-xs">Success Rate</span>
              </div>
              <div className="text-2xl font-bold text-white">{health.success_rate.toFixed(1)}%</div>
              <div className="text-xs text-slate-500 mt-1">
                {health.successful_queries} / {health.total_queries} queries
              </div>
            </div>

            <div className="glass rounded-lg p-4 border border-white/10">
              <div className="flex items-center gap-2 text-slate-400 mb-1">
                <Clock className="w-4 h-4" />
                <span className="text-xs">Avg Response</span>
              </div>
              <div className="text-2xl font-bold text-white">
                {health.avg_response_time_ms ? `${(health.avg_response_time_ms / 1000).toFixed(2)}s` : 'N/A'}
              </div>
              <div className="text-xs text-slate-500 mt-1">Response time</div>
            </div>

            <div className="glass rounded-lg p-4 border border-white/10">
              <div className="flex items-center gap-2 text-slate-400 mb-1">
                <TrendingUp className="w-4 h-4" />
                <span className="text-xs">Total Queries</span>
              </div>
              <div className="text-2xl font-bold text-white">{health.total_queries}</div>
              <div className="text-xs text-slate-500 mt-1">All time</div>
            </div>

            <div className="glass rounded-lg p-4 border border-white/10">
              <div className="flex items-center gap-2 text-slate-400 mb-1">
                <DollarSign className="w-4 h-4" />
                <span className="text-xs">Total Cost</span>
              </div>
              <div className="text-2xl font-bold text-white">${health.total_cost.toFixed(4)}</div>
              <div className="text-xs text-slate-500 mt-1">Cumulative</div>
            </div>
          </div>

          {health.version_number && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <GitBranch className="w-4 h-4" />
                <span>Active Version: v{health.version_number}</span>
                {health.deployed_at && (
                  <>
                    <span className="mx-2">•</span>
                    <span>Deployed: {new Date(health.deployed_at).toLocaleString()}</span>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Deployment Versions */}
      <div className="glass rounded-lg p-6 border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white mb-1">Deployment Versions</h3>
            <p className="text-sm text-slate-400">Version history and rollback options</p>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <History className="w-4 h-4" />
            <span>{versions.length} version{versions.length !== 1 ? 's' : ''}</span>
          </div>
        </div>

        {versions.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <GitBranch className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm">No deployment versions yet</p>
            <p className="text-xs mt-1">Deploy this workflow to create the first version</p>
          </div>
        ) : (
          <div className="space-y-3">
            {versions.map((version) => (
              <div
                key={version.id}
                className={cn(
                  'glass rounded-lg p-4 border transition-all',
                  version.status === 'active'
                    ? 'border-green-500/30 bg-green-500/5'
                    : 'border-white/10',
                  selectedVersion === version.version_number && 'ring-2 ring-blue-500/50'
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      {getStatusIcon(version.status)}
                      <span className="font-semibold text-white">Version {version.version_number}</span>
                      <span className={cn('px-2 py-0.5 rounded text-xs border', getStatusColor(version.status))}>
                        {version.status}
                      </span>
                      {version.status === 'active' && (
                        <span className="px-2 py-0.5 rounded text-xs bg-blue-500/20 text-blue-400 border border-blue-500/30">
                          Current
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 text-sm">
                      <div>
                        <div className="text-slate-400 text-xs mb-1">Deployed</div>
                        <div className="text-white">
                          {new Date(version.deployed_at).toLocaleString()}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400 text-xs mb-1">Queries</div>
                        <div className="text-white">
                          {version.total_queries} ({version.successful_queries} success)
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400 text-xs mb-1">Avg Response</div>
                        <div className="text-white">
                          {version.avg_response_time_ms
                            ? `${(version.avg_response_time_ms / 1000).toFixed(2)}s`
                            : 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400 text-xs mb-1">Cost</div>
                        <div className="text-white">${version.total_cost.toFixed(4)}</div>
                      </div>
                    </div>

                    {version.description && (
                      <div className="mt-2 text-sm text-slate-400">{version.description}</div>
                    )}

                    {version.rolled_back_at && (
                      <div className="mt-2 text-xs text-orange-400 flex items-center gap-1">
                        <RotateCcw className="w-3 h-3" />
                        <span>Rolled back on {new Date(version.rolled_back_at).toLocaleString()}</span>
                      </div>
                    )}
                  </div>

                  <div className="ml-4 flex items-center gap-2">
                    {version.status !== 'active' && version.status !== 'failed' && (
                      <button
                        onClick={() => handleRollback(version.version_number)}
                        disabled={rollbackMutation.isPending}
                        className="px-3 py-1.5 text-sm bg-orange-500/20 text-orange-400 border border-orange-500/30 rounded-lg hover:bg-orange-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                      >
                        {rollbackMutation.isPending ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Rolling back...</span>
                          </>
                        ) : (
                          <>
                            <RotateCcw className="w-4 h-4" />
                            <span>Rollback</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

