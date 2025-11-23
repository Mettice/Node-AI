/**
 * Dashboard Overview Tab
 * 
 * Shows:
 * - Quick stats (total workflows, active, total queries)
 * - Active workflows list
 * - Recent activity feed
 */

import { useState, useEffect } from 'react';
import { Activity, Workflow as WorkflowIcon, TrendingUp, Clock, ArrowRight } from 'lucide-react';
import { listWorkflows, type WorkflowListItem } from '@/services/workflowManagement';
import { getWorkflowMetrics } from '@/services/metrics';
import toast from 'react-hot-toast';

interface DashboardOverviewProps {
  onSelectWorkflow: (workflowId: string) => void;
}

export function DashboardOverview({ onSelectWorkflow }: DashboardOverviewProps) {
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalQueries, setTotalQueries] = useState(0);
  const [activeWorkflows, setActiveWorkflows] = useState<WorkflowListItem[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load all workflows
      const workflowsResponse = await listWorkflows({ limit: 100 });
      const safeWorkflows = (workflowsResponse?.workflows || []);
      setWorkflows(safeWorkflows);
      
      // Filter active (deployed) workflows
      const deployed = (safeWorkflows || []).filter(w => w.is_deployed);
      setActiveWorkflows(deployed);

      // Calculate total queries from all deployed workflows
      let total = 0;
      for (const workflow of deployed) {
        try {
          const metrics = await getWorkflowMetrics(workflow.id, 24);
          total += metrics?.total_queries || 0;
        } catch (err) {
          // Ignore errors for individual workflows
        }
      }
      setTotalQueries(total);
    } catch (error: any) {
      console.error('Error loading dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading dashboard...</div>
      </div>
    );
  }

  const safeWorkflows = workflows || [];
  const safeActiveWorkflows = activeWorkflows || [];
  const totalWorkflows = safeWorkflows.length;
  const deployedCount = safeActiveWorkflows.length;
  const draftCount = totalWorkflows - deployedCount;

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Total Workflows</span>
            <WorkflowIcon className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-white">{totalWorkflows}</div>
          <div className="text-xs text-slate-500 mt-1">
            {deployedCount} deployed, {draftCount} drafts
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Active Workflows</span>
            <Activity className="w-4 h-4 text-green-400" />
          </div>
          <div className="text-2xl font-bold text-white">{deployedCount}</div>
          <div className="text-xs text-slate-500 mt-1">Currently deployed</div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Total Queries (24h)</span>
            <TrendingUp className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-white">{totalQueries.toLocaleString()}</div>
          <div className="text-xs text-slate-500 mt-1">Across all workflows</div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Recent Activity</span>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {(safeWorkflows || []).filter(w => {
              const updated = new Date(w.updated_at);
              const hoursAgo = (Date.now() - updated.getTime()) / (1000 * 60 * 60);
              return hoursAgo < 24;
            }).length}
          </div>
          <div className="text-xs text-slate-500 mt-1">Updated in last 24h</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Workflows */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Active Workflows</h3>
            <button
              onClick={() => {
                // Switch to workflows tab - handled by parent
                window.dispatchEvent(new CustomEvent('dashboard:switch-tab', { detail: 'workflows' }));
              }}
              className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
            >
              View All <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          {(safeActiveWorkflows?.length || 0) > 0 ? (
            <div className="space-y-3">
              {(safeActiveWorkflows || []).slice(0, 5).map((workflow) => (
                <button
                  key={workflow.id}
                  onClick={() => onSelectWorkflow(workflow.id)}
                  className="w-full text-left p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors group"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-white group-hover:text-purple-400 transition-colors">
                      {workflow.name}
                    </span>
                    <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded">
                      Deployed
                    </span>
                  </div>
                  {workflow.description && (
                    <p className="text-xs text-slate-400 line-clamp-1">{workflow.description}</p>
                  )}
                  <div className="text-xs text-slate-500 mt-2">
                    Updated {new Date(workflow.updated_at).toLocaleDateString()}
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-400">
              <WorkflowIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No active workflows</p>
              <p className="text-xs mt-1">Deploy a workflow to see it here</p>
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
          {(safeWorkflows?.length || 0) > 0 ? (
            <div className="space-y-3">
              {(safeWorkflows || [])
                .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
                .slice(0, 5)
                .map((workflow) => {
                  const updated = new Date(workflow.updated_at);
                  const hoursAgo = (Date.now() - updated.getTime()) / (1000 * 60 * 60);
                  const timeAgo = hoursAgo < 1 
                    ? `${Math.round(hoursAgo * 60)}m ago`
                    : hoursAgo < 24
                    ? `${Math.round(hoursAgo)}h ago`
                    : `${Math.round(hoursAgo / 24)}d ago`;

                  return (
                    <button
                      key={workflow.id}
                      onClick={() => onSelectWorkflow(workflow.id)}
                      className="w-full text-left p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors group"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-white group-hover:text-purple-400 transition-colors">
                          {workflow.name}
                        </span>
                        <span className="text-xs text-slate-500">{timeAgo}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {workflow.is_deployed ? (
                          <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded">
                            Deployed
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 text-xs bg-slate-500/20 text-slate-400 rounded">
                            Draft
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-400">
              <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No recent activity</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

