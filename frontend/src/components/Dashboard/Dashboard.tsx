/**
 * Main Dashboard Component - Tabbed interface for workflow management and metrics
 * 
 * Tabs:
 * - Overview: Quick stats and recent activity
 * - Workflows: Full workflow management (list, deploy, undeploy, etc.)
 * - Metrics: Production metrics for selected workflow
 * - Analytics: Version comparison and advanced analytics
 */

import { useState, useEffect } from 'react';
import { BarChart3, LayoutDashboard, Workflow, TrendingUp, Search, Key, GitBranch, Activity, DollarSign } from 'lucide-react';
import { cn } from '@/utils/cn';
import { DashboardOverview } from './DashboardOverview';
import { DashboardWorkflows } from './DashboardWorkflows';
import { DashboardMetrics } from './DashboardMetrics';
import { DashboardAnalytics } from './DashboardAnalytics';
import { DashboardQuery } from './DashboardQuery';
import { DashboardTraces } from './DashboardTraces';
import { DashboardCostForecast } from './DashboardCostForecast';
import { APIKeyManager } from '@/components/APIKeys/APIKeyManager';
import { DeploymentManager } from '@/components/Deployment/DeploymentManager';
import { useQuery } from '@tanstack/react-query';
import { getWorkflow } from '@/services/workflowManagement';

// Deployment Tab Component
function DeploymentTab({
  selectedWorkflowId,
  onWorkflowChange,
}: {
  selectedWorkflowId: string | null;
  onWorkflowChange: (id: string | null) => void;
}) {
  const { data: workflow } = useQuery({
    queryKey: ['workflow', selectedWorkflowId],
    queryFn: () => getWorkflow(selectedWorkflowId!),
    enabled: !!selectedWorkflowId,
  });

  const { data: workflowsData } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => import('@/services/workflowManagement').then(m => m.listWorkflows({ limit: 100 })),
  });

  const workflows = (workflowsData?.workflows || []);

  if (!selectedWorkflowId && (workflows?.length || 0) > 0) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white mb-2">Deployment Management</h2>
          <p className="text-slate-400">Select a workflow to view and manage its deployment versions</p>
        </div>
        <div className="glass rounded-lg p-6 border border-white/10">
          <label className="block text-sm font-medium text-slate-300 mb-2">Select Workflow</label>
          <select
            value=""
            onChange={(e) => {
              if (e.target.value) {
                onWorkflowChange(e.target.value);
              }
            }}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Choose a workflow...</option>
            {(workflows || []).map((w) => (
              <option key={w.id} value={w.id} className="bg-slate-800 text-white">
                {w.name}
              </option>
            ))}
          </select>
        </div>
      </div>
    );
  }

  if (!selectedWorkflowId) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-400 p-8">
        <GitBranch className="w-16 h-16 mb-4 opacity-50" />
        <p className="text-lg mb-2">No workflows available</p>
        <p className="text-sm text-center max-w-md">
          Create a workflow first, then come back to manage its deployments
        </p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">{workflow?.name || 'Deployment Management'}</h2>
          <p className="text-slate-400">Manage deployment versions, health, and rollback</p>
        </div>
        {(workflows?.length || 0) > 1 && (
          <select
            value={selectedWorkflowId}
            onChange={(e) => onWorkflowChange(e.target.value)}
            className="px-3 py-2 bg-white/5 border border-white/10 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            {(workflows || []).map((w) => (
              <option key={w.id} value={w.id} className="bg-slate-800 text-white">
                {w.name}
              </option>
            ))}
          </select>
        )}
      </div>
      <DeploymentManager workflowId={selectedWorkflowId} workflowName={workflow?.name || 'Workflow'} />
    </div>
  );
}

type DashboardTab = 'overview' | 'workflows' | 'metrics' | 'analytics' | 'query' | 'api-keys' | 'deployments' | 'traces' | 'cost-forecast';

interface DashboardProps {
  workflowId?: string; // Optional: pre-select a workflow
}

export function Dashboard({ workflowId }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<DashboardTab>(workflowId ? 'metrics' : 'overview');
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(workflowId || null);

  // Listen for tab switch events from child components
  useEffect(() => {
    const handleTabSwitch = (e: CustomEvent) => {
      setActiveTab(e.detail as DashboardTab);
    };
    window.addEventListener('dashboard:switch-tab', handleTabSwitch as EventListener);
    return () => window.removeEventListener('dashboard:switch-tab', handleTabSwitch as EventListener);
  }, []);

  const tabs: Array<{ id: DashboardTab; label: string; icon: typeof LayoutDashboard }> = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'workflows', label: 'Workflows', icon: Workflow },
    { id: 'query', label: 'Query', icon: Search },
    { id: 'traces', label: 'Traces', icon: Activity },
    { id: 'cost-forecast', label: 'Cost Forecast', icon: DollarSign },
    { id: 'api-keys', label: 'API Keys', icon: Key },
    { id: 'deployments', label: 'Deployments', icon: GitBranch },
    { id: 'metrics', label: 'Metrics', icon: BarChart3 },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <DashboardOverview onSelectWorkflow={setSelectedWorkflowId} />;
      case 'workflows':
        return (
          <DashboardWorkflows
            selectedWorkflowId={selectedWorkflowId}
            onSelectWorkflow={(id: string) => {
              setSelectedWorkflowId(id);
              setActiveTab('metrics'); // Switch to metrics when workflow selected
            }}
          />
        );
      case 'metrics':
        return (
          <DashboardMetrics
            workflowId={selectedWorkflowId}
            onWorkflowChange={setSelectedWorkflowId}
          />
        );
      case 'query':
        return <DashboardQuery />;
      case 'api-keys':
        return <APIKeyManager />;
      case 'analytics':
        return <DashboardAnalytics selectedWorkflowId={selectedWorkflowId} />;
      case 'deployments':
        return <DeploymentTab selectedWorkflowId={selectedWorkflowId} onWorkflowChange={setSelectedWorkflowId} />;
      case 'traces':
        return <DashboardTraces workflowId={selectedWorkflowId} />;
      case 'cost-forecast':
        return <DashboardCostForecast workflowId={selectedWorkflowId} />;
      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Tab Navigation */}
      <div className="border-b border-white/10 bg-slate-800/50 flex-shrink-0">
        <div className="flex items-center gap-0.5 px-2 overflow-x-auto scrollbar-hide" style={{ scrollbarWidth: 'thin' }}>
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium transition-colors relative whitespace-nowrap flex-shrink-0',
                  isActive
                    ? 'text-purple-400'
                    : 'text-slate-400 hover:text-slate-300'
                )}
                title={tab.label}
              >
                <Icon className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{tab.label}</span>
                {isActive && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-400" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
        {renderContent()}
      </div>
    </div>
  );
}

