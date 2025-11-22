/**
 * Properties panel component - displays node configuration form
 */

import { useMemo, useCallback } from 'react';
import { useWorkflowStore } from '@/store/workflowStore';
import { useQuery } from '@tanstack/react-query';
import { getNodeSchema } from '@/services/nodes';
import { SchemaForm } from './SchemaForm';
import { EmptyState } from './EmptyState';

export function PropertiesPanel() {
  const { nodes, selectedNodeId, updateNode } = useWorkflowStore();

  // Get selected node
  const selectedNode = useMemo(() => {
    return nodes.find((n) => n.id === selectedNodeId) || null;
  }, [nodes, selectedNodeId]);

  // Fetch node schema
  const { data: schema, isLoading } = useQuery({
    queryKey: ['node-schema', selectedNode?.type],
    queryFn: () => {
      if (!selectedNode?.type) {
        throw new Error('Node type is required');
      }
      return getNodeSchema(selectedNode.type);
    },
    enabled: !!selectedNode?.type,
  });

  // Handle form change (memoized to prevent infinite loops)
  const handleFormChange = useCallback((config: Record<string, any>) => {
    if (selectedNode) {
      // Only update if config actually changed
      const currentConfig = selectedNode.data?.config || {};
      const configChanged = JSON.stringify(currentConfig) !== JSON.stringify(config);
      
      if (configChanged) {
        // For tool nodes, auto-update the node label based on tool_type and tool_name
        let updatedData: any = {
          ...selectedNode.data,
          config,
        };
        
        if (selectedNode.type === 'tool' && config.tool_type) {
          // Generate label from tool_name or tool_type
          const toolName = (config.tool_name || '').trim();
          const toolTypeLabel = config.tool_type
            .split('_')
            .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
          
          // Use tool_name if provided and different from tool_type, otherwise use formatted tool_type
          const newLabel: string = (toolName && toolName !== config.tool_type) ? toolName : toolTypeLabel;
          if (newLabel) {
            updatedData.label = newLabel;
          }
        }
        
        updateNode(selectedNode.id, {
          data: updatedData,
        });
      }
    }
  }, [selectedNode, updateNode]);

  if (!selectedNode) {
    return (
      <div className="h-full bg-white border-l border-gray-200">
        <EmptyState />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white border-l border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Properties</h2>
          <p className="text-sm text-gray-500">{selectedNode.type}</p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && selectedNode.type !== 'webhook_input' ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <SchemaForm
            schema={schema?.config_schema || {}}
            nodeType={selectedNode.type || ''}
            initialData={selectedNode.data?.config || {}}
            onChange={handleFormChange}
          />
        )}
      </div>
    </div>
  );
}

