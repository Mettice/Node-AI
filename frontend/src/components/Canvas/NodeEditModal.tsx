/**
 * Inline edit modal for nodes
 */

import { useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X, Sparkles } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getNodeSchema } from '@/services/nodes';
import { SchemaForm } from '@/components/Properties/SchemaForm';
import { useWorkflowStore } from '@/store/workflowStore';
import { useUIStore } from '@/store/uiStore';
import type { Node } from 'reactflow';

interface NodeEditModalProps {
  node: Node;
  onClose: () => void;
}

export function NodeEditModal({ node, onClose }: NodeEditModalProps) {
  const { updateNode, removeNode } = useWorkflowStore();
  const { setSidebarTab, toggleNodePalette } = useUIStore();
  const [config, setConfig] = useState(node.data?.config || {});
  const configRef = useRef(node.data?.config || {});
  
  // Check if this is an LLM node that supports prompt testing
  const isLLMNode = node.type === 'chat' || node.type === 'langchain_agent' || node.type === 'crewai_agent';
  const currentPrompt = config?.prompt || config?.system_prompt || '';

  // Fetch node schema
  const { data: schema, isLoading } = useQuery({
    queryKey: ['node-schema', node.type],
    queryFn: () => getNodeSchema(node.type || ''),
    enabled: !!node.type,
  });

  // Handle form change
  const handleFormChange = (newConfig: Record<string, any>) => {
    configRef.current = newConfig; // Update ref immediately
    setConfig(newConfig); // Update state for rendering
  };

  // Handle save
  const handleSave = () => {
    // Use ref value (always up-to-date) instead of state (may be stale due to debounce)
    const finalConfig = configRef.current;
    
    const updatedData = {
      ...node.data,
      config: { ...finalConfig }, // Ensure it's a new object
    };
    
    updateNode(node.id, {
      data: updatedData,
    });
    
    // Small delay to ensure state updates before closing modal
    setTimeout(() => {
      onClose();
    }, 50);
  };

  // Handle delete
  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this node?')) {
      removeNode(node.id);
      onClose();
    }
  };
  
  // Handle test prompt
  const handleTestPrompt = () => {
    if (currentPrompt) {
      // Open sidebar if closed, switch to prompt tab, and load the prompt
      toggleNodePalette(); // Ensure sidebar is open
      setSidebarTab('prompt', currentPrompt);
      onClose(); // Close the edit modal
    }
  };

  const modalContent = (
    <div 
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div 
        className="glass-strong rounded-xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-hidden flex flex-col border border-white/20"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Edit Node</h2>
            <p className="text-sm text-slate-400">{node.type}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading && node.type !== 'webhook_input' ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : (
            <SchemaForm
              schema={schema?.config_schema}
              nodeType={node.type || ''}
              initialData={config}
              onChange={handleFormChange}
            />
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-white/10 flex items-center justify-between gap-2">
          <button
            onClick={handleDelete}
            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 transition-all"
          >
            Delete
          </button>
          <div className="flex gap-2">
            {isLLMNode && currentPrompt && (
              <button
                onClick={handleTestPrompt}
                className="px-3 py-1.5 rounded-lg text-sm font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30 transition-all flex items-center gap-1.5"
                title="Test this prompt in the Prompt Playground"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Test Prompt
              </button>
            )}
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-white/5 text-slate-300 border border-white/10 hover:bg-white/10 transition-all"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-blue-500 text-white hover:bg-blue-600 transition-all"
            >
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}

