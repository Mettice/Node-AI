/**
 * Dashboard Metrics Tab
 * 
 * Shows production metrics for selected workflow.
 * If no workflow selected, shows workflow selector.
 */

import { useState, useEffect } from 'react';
import { BarChart3 } from 'lucide-react';
import { MetricsDashboard } from '@/components/Metrics/MetricsDashboard';
import { type WorkflowListItem } from '@/services/workflowManagement';

interface DashboardMetricsProps {
  workflowId: string | null;
  onWorkflowChange: (workflowId: string | null) => void;
}

export function DashboardMetrics({ workflowId, onWorkflowChange }: DashboardMetricsProps) {
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    setLoading(true);
    try {
      const { listWorkflows } = await import('@/services/workflowManagement');
      const response = await listWorkflows({ limit: 100 });
      const safeWorkflows = response?.workflows || [];
      setWorkflows(safeWorkflows.filter(w => w.is_deployed));
    } catch (error) {
      console.error('Error loading workflows:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!workflowId) {
    return (
      <div className="p-6">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-xl font-semibold text-white mb-4">Select a Workflow</h2>
          <p className="text-slate-400 mb-6">
            Choose a deployed workflow to view its production metrics and analytics.
          </p>

          {loading ? (
            <div className="text-center py-12 text-slate-400">Loading workflows...</div>
          ) : workflows.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No deployed workflows</p>
              <p className="text-sm mt-1">Deploy a workflow to view metrics</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {workflows.map((workflow) => (
                <button
                  key={workflow.id}
                  onClick={() => onWorkflowChange(workflow.id)}
                  className="text-left p-4 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 hover:border-purple-500/50 transition-all group"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-medium text-white group-hover:text-purple-400 transition-colors">
                      {workflow.name}
                    </h3>
                    <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded">
                      Deployed
                    </span>
                  </div>
                  {workflow.description && (
                    <p className="text-sm text-slate-400 line-clamp-2 mb-2">
                      {workflow.description}
                    </p>
                  )}
                  <div className="text-xs text-slate-500">
                    Updated {new Date(workflow.updated_at).toLocaleDateString()}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <MetricsDashboard 
        workflowId={workflowId} 
        onBack={() => onWorkflowChange(null)}
      />
    </div>
  );
}

