/**
 * Dashboard Workflows Tab
 * 
 * Full workflow management interface:
 * - List all workflows
 * - Search and filter
 * - Deploy/Undeploy actions
 * - View, Edit, Delete workflows
 * - Create new workflow
 */

import { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  Plus,
  MoreVertical,
  Play,
  Square,
  Eye,
  Edit,
  Trash2,
  Copy,
  BarChart3,
} from 'lucide-react';
import { listWorkflows, deleteWorkflow, deployWorkflow, undeployWorkflow, type WorkflowListItem } from '@/services/workflowManagement';
import { useWorkflowStore } from '@/store/workflowStore';
import { useUIStore } from '@/store/uiStore';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';

interface DashboardWorkflowsProps {
  selectedWorkflowId: string | null;
  onSelectWorkflow: (workflowId: string) => void;
}

type FilterType = 'all' | 'deployed' | 'drafts';

export function DashboardWorkflows({ selectedWorkflowId, onSelectWorkflow }: DashboardWorkflowsProps) {
  const { setWorkflow } = useWorkflowStore();
  const { setActiveUtility } = useUIStore();
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<FilterType>('all');
  const [actionMenuOpen, setActionMenuOpen] = useState<string | null>(null);
  const [deploying, setDeploying] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    setLoading(true);
    try {
      const response = await listWorkflows({ limit: 100 });
      setWorkflows(response.workflows);
    } catch (error: any) {
      console.error('Error loading workflows:', error);
      toast.error('Failed to load workflows');
    } finally {
      setLoading(false);
    }
  };

  const handleDeploy = async (workflowId: string) => {
    setDeploying(workflowId);
    try {
      await deployWorkflow(workflowId);
      toast.success('Workflow deployed');
      loadWorkflows();
    } catch (error: any) {
      toast.error('Failed to deploy workflow');
    } finally {
      setDeploying(null);
    }
  };

  const handleUndeploy = async (workflowId: string) => {
    setDeploying(workflowId);
    try {
      await undeployWorkflow(workflowId);
      toast.success('Workflow undeployed');
      loadWorkflows();
    } catch (error: any) {
      toast.error('Failed to undeploy workflow');
    } finally {
      setDeploying(null);
    }
  };

  const handleDelete = async (workflowId: string, workflowName: string) => {
    if (!confirm(`Are you sure you want to delete "${workflowName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await deleteWorkflow(workflowId);
      toast.success('Workflow deleted');
      loadWorkflows();
    } catch (error: any) {
      toast.error('Failed to delete workflow');
    }
  };

  const handleView = async (workflowId: string) => {
    try {
      const { getWorkflow } = await import('@/services/workflowManagement');
      const workflow = await getWorkflow(workflowId);
      
      // Convert to frontend format
      const safeNodes = workflow?.nodes || [];
      const safeEdges = workflow?.edges || [];
      const nodes = safeNodes.map((node: any) => ({
        id: node.id,
        type: node.type,
        position: node.position,
        data: {
          label: node.type,
          config: node.data,
        },
      }));

      const edges = safeEdges.map((edge: any) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle,
        targetHandle: edge.targetHandle,
      }));

      setWorkflow({
        id: workflow.id,
        name: workflow.name,
        nodes,
        edges,
      });

      // Close dashboard and go to canvas
      setActiveUtility(null);
      toast.success(`Workflow "${workflow.name}" loaded`);
    } catch (error: any) {
      toast.error('Failed to load workflow');
    }
  };

  const handleViewMetrics = (workflowId: string) => {
    onSelectWorkflow(workflowId);
    // Switch to metrics tab - handled by parent
    window.dispatchEvent(new CustomEvent('dashboard:switch-tab', { detail: 'metrics' }));
  };

  const safeWorkflows = workflows || [];
  const filteredWorkflows = safeWorkflows.filter((workflow) => {
    // Search filter
    const matchesSearch = workflow.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      workflow.description?.toLowerCase().includes(searchQuery.toLowerCase());

    // Status filter
    const matchesFilter =
      filter === 'all' ||
      (filter === 'deployed' && workflow.is_deployed) ||
      (filter === 'drafts' && !workflow.is_deployed);

    return matchesSearch && matchesFilter;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading workflows...</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4 overflow-y-auto h-full">
      {/* Header with Search and Actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search workflows..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div className="flex items-center gap-2">
          {/* Filter Dropdown */}
          <div className="relative">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as FilterType)}
              className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all hover:bg-white/8 hover:border-white/20 appearance-none cursor-pointer"
            >
              <option value="all" className="bg-slate-800 text-white">All Workflows</option>
              <option value="deployed" className="bg-slate-800 text-white">Deployed</option>
              <option value="drafts" className="bg-slate-800 text-white">Drafts</option>
            </select>
          </div>

          {/* New Workflow Button */}
          <button
            onClick={() => {
              setActiveUtility(null); // Close dashboard
              // Clear workflow to start fresh
              useWorkflowStore.getState().clearWorkflow();
            }}
            className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>New Workflow</span>
          </button>
        </div>
      </div>

      {/* Workflows List */}
      {filteredWorkflows.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-slate-400">
          <Search className="w-12 h-12 mb-4 opacity-50" />
          <p>No workflows found</p>
          {searchQuery && (
            <p className="text-sm mt-1">Try adjusting your search or filters</p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredWorkflows.map((workflow) => (
            <div
              key={workflow.id}
              className={cn(
                'bg-white/5 border rounded-lg p-4 transition-all',
                selectedWorkflowId === workflow.id
                  ? 'border-purple-500 bg-purple-500/10'
                  : 'border-white/10 hover:border-white/20 hover:bg-white/10'
              )}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-white mb-1">{workflow.name}</h3>
                  {workflow.description && (
                    <p className="text-sm text-slate-400 line-clamp-2">{workflow.description}</p>
                  )}
                </div>
                <div className="relative">
                  <button
                    onClick={() =>
                      setActionMenuOpen(actionMenuOpen === workflow.id ? null : workflow.id)
                    }
                    className="p-1 hover:bg-white/5 rounded transition-colors"
                  >
                    <MoreVertical className="w-4 h-4 text-slate-400" />
                  </button>

                  {/* Action Menu */}
                  {actionMenuOpen === workflow.id && (
                    <>
                      <div
                        className="fixed inset-0 z-10"
                        onClick={() => setActionMenuOpen(null)}
                      />
                      <div className="absolute right-0 top-8 bg-slate-800 border border-white/10 rounded-lg shadow-xl z-20 min-w-[180px]">
                        <button
                          onClick={() => {
                            handleView(workflow.id);
                            setActionMenuOpen(null);
                          }}
                          className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5 transition-colors flex items-center gap-2"
                        >
                          <Eye className="w-4 h-4" />
                          <span>View</span>
                        </button>
                        <button
                          onClick={() => {
                            handleView(workflow.id);
                            setActionMenuOpen(null);
                          }}
                          className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5 transition-colors flex items-center gap-2"
                        >
                          <Edit className="w-4 h-4" />
                          <span>Edit</span>
                        </button>
                        <button
                          onClick={() => {
                            handleViewMetrics(workflow.id);
                            setActionMenuOpen(null);
                          }}
                          className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5 transition-colors flex items-center gap-2"
                        >
                          <BarChart3 className="w-4 h-4" />
                          <span>Metrics</span>
                        </button>
                        <div className="border-t border-white/10 my-1" />
                        {workflow.is_deployed ? (
                          <button
                            onClick={() => {
                              handleUndeploy(workflow.id);
                              setActionMenuOpen(null);
                            }}
                            disabled={deploying === workflow.id}
                            className="w-full px-3 py-2 text-left text-sm text-orange-300 hover:bg-white/5 transition-colors flex items-center gap-2 disabled:opacity-50"
                          >
                            <Square className="w-4 h-4" />
                            <span>{deploying === workflow.id ? 'Undeploying...' : 'Undeploy'}</span>
                          </button>
                        ) : (
                          <button
                            onClick={() => {
                              handleDeploy(workflow.id);
                              setActionMenuOpen(null);
                            }}
                            disabled={deploying === workflow.id}
                            className="w-full px-3 py-2 text-left text-sm text-green-300 hover:bg-white/5 transition-colors flex items-center gap-2 disabled:opacity-50"
                          >
                            <Play className="w-4 h-4" />
                            <span>{deploying === workflow.id ? 'Deploying...' : 'Deploy'}</span>
                          </button>
                        )}
                        <div className="border-t border-white/10 my-1" />
                        <button
                          onClick={() => {
                            handleDelete(workflow.id, workflow.name);
                            setActionMenuOpen(null);
                          }}
                          className="w-full px-3 py-2 text-left text-sm text-red-400 hover:bg-red-500/10 transition-colors flex items-center gap-2"
                        >
                          <Trash2 className="w-4 h-4" />
                          <span>Delete</span>
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Status Badge */}
              <div className="flex items-center gap-2 mb-3">
                {workflow.is_deployed ? (
                  <span className="px-2 py-1 text-xs bg-green-500/20 text-green-400 rounded flex items-center gap-1">
                    <div className="w-2 h-2 bg-green-400 rounded-full" />
                    Deployed
                  </span>
                ) : (
                  <span className="px-2 py-1 text-xs bg-slate-500/20 text-slate-400 rounded">
                    Draft
                  </span>
                )}
                {workflow.is_template && (
                  <span className="px-2 py-1 text-xs bg-purple-500/20 text-purple-400 rounded">
                    Template
                  </span>
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between text-xs text-slate-500 pt-3 border-t border-white/10">
                <span>Updated {new Date(workflow.updated_at).toLocaleDateString()}</span>
                <button
                  onClick={() => handleViewMetrics(workflow.id)}
                  className="text-purple-400 hover:text-purple-300 transition-colors"
                >
                  View Metrics →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

