/**
 * Workflow Loader Component - Modal for loading saved workflows
 */

import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X, Search, FileText, Clock, Tag, Upload } from 'lucide-react';
import { cn } from '@/utils/cn';
import { listWorkflows, getWorkflow, createWorkflow, type WorkflowListItem } from '@/services/workflowManagement';
import { useWorkflowStore } from '@/store/workflowStore';
import { errorToast, successToast, loadingToast } from '@/components/common/ErrorToast';
import { ErrorDisplay, LoadingError } from '@/components/common/ErrorDisplay';
import { parseAPIError, type APIErrorResponse } from '@/utils/api';
import type { Node as RFNode, Edge as RFEdge } from 'reactflow';

interface WorkflowLoaderProps {
  isOpen: boolean;
  onClose: () => void;
}

export function WorkflowLoader({ isOpen, onClose }: WorkflowLoaderProps) {
  const { setWorkflow, setWorkflowId } = useWorkflowStore();
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showTemplates, setShowTemplates] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [loadError, setLoadError] = useState<APIErrorResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load workflows when modal opens
  useEffect(() => {
    if (isOpen) {
      loadWorkflows();
    }
  }, [isOpen, showTemplates]);

  const loadWorkflows = async () => {
    setLoading(true);
    setLoadError(null);
    
    try {
      const response = await listWorkflows({
        limit: 100,
        is_template: showTemplates ? true : undefined,
      });
      setWorkflows(response.workflows);
    } catch (error: any) {
      console.error('Error loading workflows:', error);
      const parsedError = parseAPIError(error);
      setLoadError(parsedError);
      
      // Show toast with specific error handling
      if (parsedError.error_code === 'AUTHENTICATION_REQUIRED') {
        errorToast.auth();
      } else if (parsedError.error_code === 'RATE_LIMIT_EXCEEDED') {
        errorToast.rateLimit();
      } else {
        errorToast.show(parsedError, {
          showSuggestions: true,
          showRetry: true,
          onRetry: loadWorkflows,
          retryLabel: 'Reload Workflows'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLoadWorkflow = async (workflowId: string) => {
    try {
      const workflow = await getWorkflow(workflowId);
      
      // Convert backend workflow format to frontend format
      const nodes: RFNode[] = workflow.nodes.map((node: any) => ({
        id: node.id,
        type: node.type || 'default',
        position: node.position,
        data: {
          label: node.type || 'default',
          config: node.data, // Store config in data.config for frontend
        },
      }));

      const edges: RFEdge[] = workflow.edges.map((edge: any) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle || undefined,
        targetHandle: edge.targetHandle || undefined,
      }));

      // Set workflow in store
      // CustomNode expects data structure: { label, category, status, config }
      setWorkflow({
        id: workflow.id,
        name: workflow.name,
        nodes: nodes.map((node) => ({
          id: node.id,
          type: node.type || 'default',
          position: node.position,
          data: {
            label: node.data?.label || node.type || 'default',
            category: node.data?.category,
            status: node.data?.status || 'idle',
            // If config has a nested config, use that. Otherwise use the config directly
            config: node.data?.config?.config || node.data?.config || {},
          },
        })),
        edges: edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle || undefined,
          targetHandle: edge.targetHandle || undefined,
        })),
      });
      
      if (workflow.id) {
        setWorkflowId(workflow.id);
      }

      successToast.show(`Workflow "${workflow.name}" loaded successfully`);
      onClose();
    } catch (error: any) {
      console.error('Error loading workflow:', error);
      const parsedError = parseAPIError(error);
      
      errorToast.show(parsedError, {
        showSuggestions: true,
        showRetry: true,
        onRetry: () => handleLoadWorkflow(workflowId),
        retryLabel: 'Try Loading Again'
      });
    }
  };

  const handleUploadTemplate = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.json')) {
      errorToast.show('Please upload a JSON file');
      return;
    }

    setUploading(true);
    try {
      const text = await file.text();
      const workflowData = JSON.parse(text);

      // Validate required fields
      if (!workflowData.name || !workflowData.nodes || !workflowData.edges) {
        errorToast.show('Invalid workflow file. Missing required fields (name, nodes, edges)');
        return;
      }

      // Convert frontend format to backend format
      const nodes = workflowData.nodes.map((node: any) => {
        // Ensure position is an object with x and y
        let position = { x: 0, y: 0 };
        if (node.position) {
          if (typeof node.position === 'object' && 'x' in node.position && 'y' in node.position) {
            position = { x: Number(node.position.x) || 0, y: Number(node.position.y) || 0 };
          }
        }
        
        // Extract data - handle both old and new formats
        let nodeData = {};
        if (node.data) {
          if (node.data.config) {
            nodeData = node.data.config;
          } else {
            nodeData = node.data;
          }
        }
        
        return {
          id: node.id || `node_${Math.random().toString(36).substr(2, 9)}`,
          type: node.type || 'default',
          position: position,
          data: nodeData,
        };
      });

      const edges = workflowData.edges.map((edge: any) => ({
        id: edge.id || `edge_${Math.random().toString(36).substr(2, 9)}`,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle || undefined,
        targetHandle: edge.targetHandle || undefined,
      }));

      // Validate template before creation
      const validationData = {
        name: workflowData.name,
        description: workflowData.description || `Template: ${workflowData.name}`,
        nodes: nodes.map((node: any) => ({
          id: node.id,
          type: node.type,
          position: node.position,
          data: node.data
        })),
        edges: edges.map((edge: any) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle,
          targetHandle: edge.targetHandle
        })),
        tags: workflowData.tags || ['template', 'imported'],
        is_template: true,
      };

      // First validate the workflow
      const validationResponse = await fetch('/api/v1/workflows/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(validationData),
      });

      const validationResult = await validationResponse.json();

      if (!validationResult.compatible) {
        // Template has missing node types
        const missingNodes = validationResult.missing_nodes || [];
        const suggestions = validationResult.suggestions || [];
        
        let errorMessage = `Template cannot be uploaded: ${validationResult.message}`;
        if (suggestions.length > 0) {
          errorMessage += `\n\nTo use this template:\n${suggestions.map((s: string) => `• ${s}`).join('\n')}`;
        }
        
        errorToast.show(errorMessage);
        return;
      }

      if (!validationResult.valid) {
        // Template structure is invalid
        const errors = validationResult.errors || [];
        let errorMessage = `Template validation failed: ${validationResult.message}`;
        if (errors.length > 0) {
          errorMessage += `\n\nIssues found:\n${errors.map((e: string) => `• ${e}`).join('\n')}`;
        }
        
        errorToast.show(errorMessage);
        return;
      }

      // Create workflow as template (validation passed)
      const newWorkflow = await createWorkflow({
        name: workflowData.name,
        description: workflowData.description || `Template: ${workflowData.name}`,
        nodes,
        edges,
        tags: workflowData.tags || ['template', 'imported'],
        is_template: true,
      });

      successToast.show(`Template "${newWorkflow.name}" uploaded successfully`);
      loadWorkflows(); // Refresh the list
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error: any) {
      console.error('Error uploading template:', error);
      if (error instanceof SyntaxError) {
        errorToast.show('Invalid JSON file. Please check the file format.');
      } else {
        // Check if it's a validation error from the API
        const errorResponse = error.response?.data;
        if (errorResponse?.error_code === 'VALIDATION_ERROR') {
          const details = errorResponse.details || error.message || 'Unknown validation error';
          const suggestions = errorResponse.suggestions || [];
          
          let errorMessage = `Template upload failed: ${errorResponse.message || details}`;
          if (suggestions.length > 0) {
            errorMessage += `\n\nSuggestions:\n${suggestions.map((s: string) => `• ${s}`).join('\n')}`;
          }
          
          errorToast.show(errorMessage, {
            duration: 8000,
            showSuggestions: true
          });
        } else {
          // Generic error handling
          const message = errorResponse?.message || errorResponse?.detail?.message || error.message || 'Failed to upload template';
          errorToast.show(message);
        }
      }
    } finally {
      setUploading(false);
    }
  };

  const filteredWorkflows = workflows.filter((workflow) =>
    workflow.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    workflow.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!isOpen) return null;

  const modalContent = (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-20 pb-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-slate-800 border border-white/10 rounded-lg shadow-2xl w-full max-w-4xl max-h-[calc(100vh-120px)] flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h2 className="text-xl font-semibold text-white">Load Workflow</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/5 rounded transition-colors"
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* Search and Filters */}
        <div className="p-4 border-b border-white/10 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search workflows..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowTemplates(!showTemplates)}
              className={cn(
                'px-3 py-1.5 text-sm rounded transition-colors',
                showTemplates
                  ? 'bg-purple-500 text-white'
                  : 'bg-white/5 text-slate-300 hover:bg-white/10'
              )}
            >
              Templates Only
            </button>
            <button
              onClick={handleUploadTemplate}
              disabled={uploading}
              className={cn(
                'px-3 py-1.5 text-sm rounded transition-colors flex items-center gap-2',
                'bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 border border-purple-500/50',
                uploading && 'opacity-50 cursor-not-allowed'
              )}
            >
              <Upload className="w-4 h-4" />
              {uploading ? 'Uploading...' : 'Upload Template'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        </div>

        {/* Workflow List */}
        <div className="flex-1 overflow-y-auto p-4">
          {loadError ? (
            <LoadingError 
              error={loadError} 
              onRetry={loadWorkflows}
              retryLabel="Reload Workflows"
              className="py-8"
            />
          ) : loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-slate-400">Loading workflows...</div>
            </div>
          ) : filteredWorkflows.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <FileText className="w-12 h-12 mb-4 opacity-50" />
              <p>No workflows found</p>
              {searchQuery && (
                <p className="text-sm mt-2">Try adjusting your search or clearing filters</p>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {filteredWorkflows.map((workflow) => (
                <button
                  key={workflow.id}
                  onClick={() => handleLoadWorkflow(workflow.id)}
                  className="text-left p-4 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 hover:border-white/20 transition-all group"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-medium text-white group-hover:text-purple-400 transition-colors">
                      {workflow.name}
                    </h3>
                    {workflow.is_template && (
                      <Tag className="w-4 h-4 text-purple-400 flex-shrink-0 ml-2" />
                    )}
                  </div>
                  {workflow.description && (
                    <p className="text-sm text-slate-400 mb-3 line-clamp-2">
                      {workflow.description}
                    </p>
                  )}
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>
                        {new Date(workflow.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                    {workflow.tags.length > 0 && (
                      <div className="flex items-center gap-1">
                        {workflow.tags.slice(0, 2).map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Render modal using portal to escape any parent stacking contexts
  return createPortal(modalContent, document.body);
}

