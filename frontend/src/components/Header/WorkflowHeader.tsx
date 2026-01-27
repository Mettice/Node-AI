/**
 * Workflow Header - Top bar with logo, workflow management, and version
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Save, Undo2, Redo2, Download, FileDown, ChevronDown, Rocket, Power } from 'lucide-react';
import { useWorkflowStore } from '@/store/workflowStore';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';
import { APP_VERSION } from '@/constants';
import { saveWorkflow, deployWorkflow, undeployWorkflow, getWorkflow, deleteWorkflow, createWorkflow } from '@/services/workflowManagement';
import { WorkflowLoader } from '@/components/Workflow/WorkflowLoader';
import { UserProfileDropdown } from '@/components/User/UserProfileDropdown';

export function WorkflowHeader() {
  const { 
    workflowName, 
    setWorkflowName, 
    nodes, 
    edges, 
    workflowId, 
    setWorkflowId,
    undo,
    redo,
    canUndo,
    canRedo,
    clearWorkflow,
    setWorkflow,
  } = useWorkflowStore();
  const [showNameMenu, setShowNameMenu] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState(workflowName);
  const [isSaving, setIsSaving] = useState(false);
  const [showWorkflowLoader, setShowWorkflowLoader] = useState(false);
  const [isDeployed, setIsDeployed] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const nameButtonRef = useRef<HTMLButtonElement>(null);
  const exportButtonRef = useRef<HTMLButtonElement>(null);
  const [nameMenuPosition, setNameMenuPosition] = useState({ top: 0, left: 0 });
  const [exportMenuPosition, setExportMenuPosition] = useState({ top: 0, left: 0 });

  const handleSave = useCallback(async () => {
    if (nodes.length === 0) {
      toast.error('Cannot save empty workflow');
      return;
    }

    setIsSaving(true);
    try {
      // Build workflow object matching backend format
      const workflow = {
        id: workflowId || undefined,
        name: workflowName,
        nodes: nodes.map((node) => ({
          id: node.id,
          type: node.type || 'default',
          position: node.position,
          data: node.data?.config || node.data || {},
        })),
        edges: edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle || undefined,
          targetHandle: edge.targetHandle || undefined,
        })),
      };

      const savedWorkflow = await saveWorkflow(workflow);
      setWorkflowId(savedWorkflow.id || null);
      
      // Fetch deployment status
      if (savedWorkflow.id) {
        try {
          const fullWorkflow = await getWorkflow(savedWorkflow.id);
          setIsDeployed(fullWorkflow.is_deployed || false);
        } catch (err) {
          // Ignore errors fetching deployment status
        }
      }
      
      toast.success(`Workflow "${savedWorkflow.name}" saved successfully`);
    } catch (error: any) {
      console.error('Error saving workflow:', error);
      toast.error(error.response?.data?.detail?.message || error.message || 'Failed to save workflow');
    } finally {
      setIsSaving(false);
    }
  }, [nodes, edges, workflowName, workflowId, setWorkflowId]);

  // Fetch deployment status when workflowId changes
  useEffect(() => {
    if (workflowId) {
      getWorkflow(workflowId)
        .then((workflow) => {
          setIsDeployed(workflow.is_deployed || false);
        })
        .catch(() => {
          // Ignore errors
        });
    } else {
      setIsDeployed(false);
    }
  }, [workflowId]);

  const handleDeploy = useCallback(async () => {
    if (!workflowId) {
      toast.error('Please save the workflow before deploying');
      return;
    }

    setIsDeploying(true);
    try {
      await deployWorkflow(workflowId);
      setIsDeployed(true);
      toast.success('Workflow deployed successfully');
    } catch (error: any) {
      console.error('Error deploying workflow:', error);
      toast.error(error.response?.data?.detail?.message || error.message || 'Failed to deploy workflow');
    } finally {
      setIsDeploying(false);
    }
  }, [workflowId]);

  const handleUndeploy = useCallback(async () => {
    if (!workflowId) {
      return;
    }

    setIsDeploying(true);
    try {
      await undeployWorkflow(workflowId);
      setIsDeployed(false);
      toast.success('Workflow undeployed successfully');
    } catch (error: any) {
      console.error('Error undeploying workflow:', error);
      toast.error(error.response?.data?.detail?.message || error.message || 'Failed to undeploy workflow');
    } finally {
      setIsDeploying(false);
    }
  }, [workflowId]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+S or Cmd+S to save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (nodes.length > 0 && !isSaving) {
          handleSave();
        }
      }
      // Ctrl+Z or Cmd+Z to undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (canUndo()) {
          undo();
        }
      }
      // Ctrl+Y or Cmd+Shift+Z to redo
      if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        if (canRedo()) {
          redo();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleSave, nodes.length, isSaving, undo, redo, canUndo, canRedo]);

  const handleUndo = () => {
    if (canUndo()) {
      undo();
    }
  };

  const handleRedo = () => {
    if (canRedo()) {
      redo();
    }
  };

  const handleExportJSON = () => {
    const workflow = {
      name: workflowName,
      nodes,
      edges,
    };
    const blob = new Blob([JSON.stringify(workflow, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${workflowName.replace(/\s+/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Workflow exported');
    setShowExportMenu(false);
  };

  const handleDownload = () => {
    handleExportJSON();
  };

  const handleRename = () => {
    if (newName.trim()) {
      setWorkflowName(newName.trim());
      setIsRenaming(false);
      setShowNameMenu(false);
      toast.success('Workflow renamed');
    }
  };

  const handleNewWorkflow = useCallback(async () => {
    // Clear current workflow and create a new one
    clearWorkflow();
    setWorkflowId(null);
    setIsDeployed(false);
    setShowNameMenu(false);
    toast.success('New workflow created');
  }, [clearWorkflow, setWorkflowId]);

  const handleDuplicate = useCallback(async () => {
    if (!workflowId) {
      toast.error('Please save the workflow before duplicating');
      setShowNameMenu(false);
      return;
    }

    try {
      // Get current workflow
      const currentWorkflow = await getWorkflow(workflowId);
      
      // Create a duplicate with a new name (explicitly not deployed)
      const duplicateWorkflow = await createWorkflow({
        name: `${currentWorkflow.name} (Copy)`,
        description: currentWorkflow.description,
        nodes: currentWorkflow.nodes,
        edges: currentWorkflow.edges,
        tags: currentWorkflow.tags,
        is_template: false,
      });

      // Ensure the duplicate is not deployed (even if backend sets it, we override)
      if (duplicateWorkflow.is_deployed) {
        try {
          await undeployWorkflow(duplicateWorkflow.id!);
          duplicateWorkflow.is_deployed = false;
        } catch (err) {
          // Ignore errors - the workflow might not be deployed anyway
        }
      }

      // Load the duplicate into the editor
      setWorkflow({
        id: duplicateWorkflow.id || undefined,
        name: duplicateWorkflow.name,
        nodes: duplicateWorkflow.nodes.map((node: any) => ({
          id: node.id,
          type: node.type,
          position: node.position,
          data: { config: node.data },
        })),
        edges: duplicateWorkflow.edges,
      });
      setWorkflowId(duplicateWorkflow.id || null);
      setIsDeployed(false); // Explicitly set as undeployed
      setShowNameMenu(false);
      toast.success(`Workflow "${duplicateWorkflow.name}" duplicated successfully`);
    } catch (error: any) {
      console.error('Error duplicating workflow:', error);
      toast.error(error.response?.data?.detail?.message || error.message || 'Failed to duplicate workflow');
    }
  }, [workflowId, getWorkflow, createWorkflow, undeployWorkflow, setWorkflow, setWorkflowId]);

  const handleDelete = useCallback(async () => {
    if (!workflowId) {
      toast.error('No workflow to delete');
      setShowNameMenu(false);
      return;
    }

    // Confirm deletion
    const confirmed = window.confirm(
      `Are you sure you want to delete "${workflowName}"? This action cannot be undone.`
    );

    if (!confirmed) {
      setShowNameMenu(false);
      return;
    }

    try {
      await deleteWorkflow(workflowId);
      // Clear the workflow from the editor
      clearWorkflow();
      setWorkflowId(null);
      setIsDeployed(false);
      setShowNameMenu(false);
      toast.success('Workflow deleted successfully');
    } catch (error: any) {
      console.error('Error deleting workflow:', error);
      toast.error(error.response?.data?.detail?.message || error.message || 'Failed to delete workflow');
    }
  }, [workflowId, workflowName, deleteWorkflow, clearWorkflow, setWorkflowId]);

  // Calculate dropdown positions when they open
  const handleNameMenuToggle = () => {
    if (!showNameMenu && nameButtonRef.current) {
      const rect = nameButtonRef.current.getBoundingClientRect();
      setNameMenuPosition({
        top: rect.bottom + 4,
        left: rect.left,
      });
    }
    setShowNameMenu(!showNameMenu);
  };

  const handleExportMenuToggle = () => {
    if (!showExportMenu && exportButtonRef.current) {
      const rect = exportButtonRef.current.getBoundingClientRect();
      setExportMenuPosition({
        top: rect.bottom + 4,
        left: rect.left,
      });
    }
    setShowExportMenu(!showExportMenu);
  };

  return (
    <header className="h-14 px-3 md:px-6 border-b border-white/10 bg-slate-800/80 backdrop-blur-sm glass-strong flex items-center justify-between">
      {/* Left: Logo */}
      <div className="flex items-center">
        <h1 className="text-lg md:text-xl font-bold text-white">NodeAI</h1>
      </div>

      {/* Center: Workflow Management Controls */}
      <div className="flex items-center gap-1 md:gap-3 flex-1 justify-center overflow-hidden">
        {/* Workflow Name Dropdown */}
        <div className="relative">
          {isRenaming ? (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleRename();
                  if (e.key === 'Escape') {
                    setIsRenaming(false);
                    setNewName(workflowName);
                  }
                }}
                className="px-3 py-1.5 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                autoFocus
              />
              <button
                onClick={handleRename}
                className="px-2 py-1 text-xs bg-amber-500 hover:bg-amber-600 text-white rounded transition-colors"
              >
                Save
              </button>
            </div>
          ) : (
            <>
              <button
                ref={nameButtonRef}
                onClick={handleNameMenuToggle}
                className="flex items-center gap-1 md:gap-1.5 px-2 md:px-3 py-1.5 text-xs md:text-sm font-medium text-white hover:bg-white/5 rounded transition-colors max-w-[120px] md:max-w-none"
              >
                <span className="truncate">{workflowName}</span>
                <ChevronDown className="w-3 md:w-4 h-3 md:h-4 flex-shrink-0" />
              </button>
              {showNameMenu && createPortal(
                <>
                  <div
                    className="fixed inset-0 z-[9999]"
                    onClick={() => setShowNameMenu(false)}
                    style={{ pointerEvents: 'auto' }}
                  />
                  <div 
                    className="fixed bg-slate-800 border border-white/10 rounded-md shadow-xl z-[10000] py-1"
                    style={{
                      top: `${nameMenuPosition.top}px`,
                      left: `${nameMenuPosition.left}px`,
                      pointerEvents: 'auto',
                      width: 'max-content',
                    }}
                  >
                    <button
                      onClick={() => {
                        setIsRenaming(true);
                        setShowNameMenu(false);
                      }}
                      className="block w-full px-2 py-1 text-left text-xs text-slate-300 hover:bg-white/5 transition-colors whitespace-nowrap"
                    >
                      Rename
                    </button>
                    <button
                      onClick={() => {
                        setShowWorkflowLoader(true);
                        setShowNameMenu(false);
                      }}
                      className="block w-full px-2 py-1 text-left text-xs text-slate-300 hover:bg-white/5 transition-colors border-t border-white/10 whitespace-nowrap"
                    >
                      Load Workflow
                    </button>
                    <button
                      onClick={handleNewWorkflow}
                      className="block w-full px-2 py-1 text-left text-xs text-slate-300 hover:bg-white/5 transition-colors border-t border-white/10 whitespace-nowrap"
                    >
                      New Workflow
                    </button>
                    <button
                      onClick={handleDuplicate}
                      className="block w-full px-2 py-1 text-left text-xs text-slate-300 hover:bg-white/5 transition-colors border-t border-white/10 whitespace-nowrap"
                    >
                      Duplicate
                    </button>
                    <button
                      onClick={handleDelete}
                      className="block w-full px-2 py-1 text-left text-xs text-red-400 hover:bg-red-500/10 transition-colors border-t border-white/10 whitespace-nowrap"
                    >
                      Delete
                    </button>
                  </div>
                </>,
                document.body
              )}
            </>
          )}
        </div>

        <div className="h-6 w-px bg-white/10 hidden md:block" />

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={isSaving || nodes.length === 0}
          className={cn(
            'flex items-center gap-1 md:gap-1.5 px-2 md:px-3 py-1.5 text-xs md:text-sm font-medium',
            'text-slate-300 hover:text-white hover:bg-white/5 rounded transition-colors',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
          title="Save Workflow (Ctrl+S)"
        >
          <Save className="w-3 md:w-4 h-3 md:h-4" />
          <span className="hidden sm:inline">{isSaving ? 'Saving...' : 'Save'}</span>
        </button>

        {/* Undo Button */}
        <button
          onClick={handleUndo}
          disabled={!canUndo()}
          className={cn(
            'flex items-center gap-1 md:gap-1.5 px-2 md:px-3 py-1.5 text-xs md:text-sm font-medium',
            'text-slate-300 hover:text-white hover:bg-white/5 rounded transition-colors',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
          title="Undo (Ctrl+Z)"
        >
          <Undo2 className="w-3 md:w-4 h-3 md:h-4" />
        </button>

        {/* Redo Button */}
        <button
          onClick={handleRedo}
          disabled={!canRedo()}
          className={cn(
            'flex items-center gap-1 md:gap-1.5 px-2 md:px-3 py-1.5 text-xs md:text-sm font-medium',
            'text-slate-300 hover:text-white hover:bg-white/5 rounded transition-colors',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
          title="Redo (Ctrl+Y)"
        >
          <Redo2 className="w-3 md:w-4 h-3 md:h-4" />
        </button>

        {/* Deploy/Undeploy Button */}
        {workflowId && (
          <button
            onClick={isDeployed ? handleUndeploy : handleDeploy}
            disabled={isDeploying}
            className={cn(
              'flex items-center gap-1 md:gap-1.5 px-2 md:px-3 py-1.5 text-xs md:text-sm font-medium rounded transition-colors',
              isDeploying
                ? 'text-slate-400 cursor-not-allowed opacity-50'
                : isDeployed
                ? 'text-orange-300 hover:text-orange-200 hover:bg-orange-500/10'
                : 'text-green-300 hover:text-green-200 hover:bg-green-500/10'
            )}
            title={isDeployed ? 'Undeploy workflow' : 'Deploy workflow'}
          >
            {isDeployed ? (
              <>
                <Power className="w-3 md:w-4 h-3 md:h-4" />
                <span className="hidden sm:inline">{isDeploying ? 'Undeploying...' : 'Undeploy'}</span>
              </>
            ) : (
              <>
                <Rocket className="w-3 md:w-4 h-3 md:h-4" />
                <span className="hidden sm:inline">{isDeploying ? 'Deploying...' : 'Deploy'}</span>
              </>
            )}
          </button>
        )}

        <div className="h-6 w-px bg-white/10 hidden md:block" />

        {/* Export Dropdown - Hidden on mobile */}
        <div className="relative hidden md:block">
          <button
            ref={exportButtonRef}
            onClick={handleExportMenuToggle}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium',
              'text-slate-300 hover:text-white hover:bg-white/5 rounded transition-colors'
            )}
            title="Export Workflow"
          >
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
          {showExportMenu && createPortal(
            <>
              <div
                className="fixed inset-0 z-[9999]"
                onClick={() => setShowExportMenu(false)}
                style={{ pointerEvents: 'auto' }}
              />
              <div 
                className="fixed bg-slate-800 border border-white/10 rounded-md shadow-xl z-[10000] py-1"
                style={{
                  top: `${exportMenuPosition.top}px`,
                  left: `${exportMenuPosition.left}px`,
                  pointerEvents: 'auto',
                  width: 'max-content',
                }}
              >
                <button
                  onClick={handleExportJSON}
                  className="block w-full px-2 py-1 text-left text-xs text-slate-300 hover:bg-white/5 transition-colors whitespace-nowrap"
                >
                  Export as JSON
                </button>
                <button
                  onClick={() => {
                    toast('Export as Template coming soon', { icon: 'ℹ️' });
                    setShowExportMenu(false);
                  }}
                  className="block w-full px-2 py-1 text-left text-xs text-slate-300 hover:bg-white/5 transition-colors border-t border-white/10 whitespace-nowrap"
                >
                  Export as Template
                </button>
                </div>
              </>,
              document.body
            )}
          </div>

        {/* Download Button - Hidden on mobile */}
        <button
          onClick={handleDownload}
          className={cn(
            'hidden md:flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium',
            'text-slate-300 hover:text-white hover:bg-white/5 rounded transition-colors'
          )}
          title="Download Workflow"
        >
          <FileDown className="w-4 h-4" />
          <span>Download</span>
        </button>
      </div>

      {/* Right: User Profile & Version */}
      <div className="flex items-center gap-2 md:gap-4">
        <div className="hidden md:flex items-center gap-2">
          <span className="text-xs md:text-sm text-slate-400">v{APP_VERSION}</span>
          <div className="h-2 w-2 bg-green-500 rounded-full"></div>
        </div>
        <UserProfileDropdown />
      </div>

      {/* Workflow Loader Modal */}
      <WorkflowLoader
        isOpen={showWorkflowLoader}
        onClose={() => setShowWorkflowLoader(false)}
      />
    </header>
  );
}

