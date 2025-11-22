/**
 * Workflow Management Toolbar - Top bar for workflow controls
 */

import { useState } from 'react';
import { Save, Undo2, Redo2, Download, FileDown, ChevronDown } from 'lucide-react';
import { useWorkflowStore } from '@/store/workflowStore';
import { cn } from '@/utils/cn';
import toast from 'react-hot-toast';

export function WorkflowToolbar() {
  const { workflowName, setWorkflowName, nodes, edges } = useWorkflowStore();
  const [showNameMenu, setShowNameMenu] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState(workflowName);

  const handleSave = () => {
    // TODO: Implement actual save functionality
    toast.success('Workflow saved');
  };

  const handleUndo = () => {
    // TODO: Implement undo functionality
    toast.info('Undo not yet implemented');
  };

  const handleRedo = () => {
    // TODO: Implement redo functionality
    toast.info('Redo not yet implemented');
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

  const handleNewWorkflow = () => {
    // TODO: Implement new workflow
    toast.info('New workflow not yet implemented');
    setShowNameMenu(false);
  };

  const handleDuplicate = () => {
    // TODO: Implement duplicate
    toast.info('Duplicate not yet implemented');
    setShowNameMenu(false);
  };

  const handleDelete = () => {
    // TODO: Implement delete with confirmation
    toast.info('Delete not yet implemented');
    setShowNameMenu(false);
  };

  return (
    <div className="h-12 px-4 border-b border-white/10 bg-slate-800/50 flex items-center gap-2">
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
              className="px-3 py-1.5 bg-white/5 border border-white/10 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              autoFocus
            />
            <button
              onClick={handleRename}
              className="px-2 py-1 text-xs bg-purple-500 hover:bg-purple-600 text-white rounded"
            >
              Save
            </button>
          </div>
        ) : (
          <>
            <button
              onClick={() => setShowNameMenu(!showNameMenu)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white hover:bg-white/5 rounded transition-colors"
            >
              <span>{workflowName}</span>
              <ChevronDown className="w-4 h-4" />
            </button>
            {showNameMenu && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowNameMenu(false)}
                />
                <div className="absolute top-full left-0 mt-1 bg-slate-800 border border-white/10 rounded-lg shadow-xl z-20 min-w-[180px]">
                  <button
                    onClick={() => {
                      setIsRenaming(true);
                      setShowNameMenu(false);
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5 transition-colors"
                  >
                    Rename
                  </button>
                  <button
                    onClick={handleNewWorkflow}
                    className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5 transition-colors border-t border-white/10"
                  >
                    New Workflow
                  </button>
                  <button
                    onClick={handleDuplicate}
                    className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5 transition-colors border-t border-white/10"
                  >
                    Duplicate
                  </button>
                  <button
                    onClick={handleDelete}
                    className="w-full px-3 py-2 text-left text-sm text-red-400 hover:bg-red-500/10 transition-colors border-t border-white/10"
                  >
                    Delete
                  </button>
                </div>
              </>
            )}
          </>
        )}
      </div>

      <div className="h-6 w-px bg-white/10" />

      {/* Save Button */}
      <button
        onClick={handleSave}
        className={cn(
          'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium',
          'text-slate-300 hover:text-white hover:bg-white/5 rounded transition-colors',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
        title="Save Workflow (Ctrl+S)"
      >
        <Save className="w-4 h-4" />
        <span>Save</span>
      </button>

      {/* Undo Button */}
      <button
        onClick={handleUndo}
        className={cn(
          'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium',
          'text-slate-300 hover:text-white hover:bg-white/5 rounded transition-colors',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
        title="Undo (Ctrl+Z)"
        disabled
      >
        <Undo2 className="w-4 h-4" />
      </button>

      {/* Redo Button */}
      <button
        onClick={handleRedo}
        className={cn(
          'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium',
          'text-slate-300 hover:text-white hover:bg-white/5 rounded transition-colors',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
        title="Redo (Ctrl+Y)"
        disabled
      >
        <Redo2 className="w-4 h-4" />
      </button>

      <div className="h-6 w-px bg-white/10" />

      {/* Export Dropdown */}
      <div className="relative">
        <button
          onClick={() => setShowExportMenu(!showExportMenu)}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium',
            'text-slate-300 hover:text-white hover:bg-white/5 rounded transition-colors'
          )}
          title="Export Workflow"
        >
          <Download className="w-4 h-4" />
          <span>Export</span>
        </button>
        {showExportMenu && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setShowExportMenu(false)}
            />
            <div className="absolute top-full left-0 mt-1 bg-slate-800 border border-white/10 rounded-lg shadow-xl z-20 min-w-[180px]">
              <button
                onClick={handleExportJSON}
                className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5 transition-colors"
              >
                Export as JSON
              </button>
              <button
                onClick={() => {
                  toast.info('Export as Template coming soon');
                  setShowExportMenu(false);
                }}
                className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5 transition-colors border-t border-white/10"
              >
                Export as Template
              </button>
            </div>
          </>
        )}
      </div>

      {/* Download Button */}
      <button
        onClick={handleDownload}
        className={cn(
          'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium',
          'text-slate-300 hover:text-white hover:bg-white/5 rounded transition-colors'
        )}
        title="Download Workflow"
      >
        <FileDown className="w-4 h-4" />
        <span>Download</span>
      </button>
    </div>
  );
}

