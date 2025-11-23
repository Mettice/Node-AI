/**
 * Mobile connection mode for linking nodes with touch gestures
 */

import { useState, useEffect, useCallback } from 'react';
import { Link, X, CheckCircle } from 'lucide-react';
import { useWorkflowStore } from '@/store/workflowStore';
import { cn } from '@/utils/cn';

interface MobileConnectionModeProps {
  isActive: boolean;
  onToggle: () => void;
  onConnectionCreated: (sourceId: string, targetId: string) => void;
}

interface ConnectionStep {
  step: 'source' | 'target' | 'complete';
  sourceNodeId?: string;
  targetNodeId?: string;
}

export function MobileConnectionMode({ 
  isActive, 
  onToggle, 
  onConnectionCreated 
}: MobileConnectionModeProps) {
  const [connectionStep, setConnectionStep] = useState<ConnectionStep>({ step: 'source' });
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
  const { nodes, addEdge } = useWorkflowStore();

  // Reset when mode is toggled off
  useEffect(() => {
    if (!isActive) {
      setConnectionStep({ step: 'source' });
      setHighlightedNodes(new Set());
    }
  }, [isActive]);

  // Handle node click in connection mode
  const handleNodeClick = useCallback((nodeId: string) => {
    if (!isActive) return;

    if (connectionStep.step === 'source') {
      setConnectionStep({ step: 'target', sourceNodeId: nodeId });
      // Highlight valid target nodes (exclude source and already connected)
      const validTargets = nodes
        .filter(node => node.id !== nodeId)
        .map(node => node.id);
      setHighlightedNodes(new Set(validTargets));
      
    } else if (connectionStep.step === 'target' && connectionStep.sourceNodeId) {
      if (nodeId === connectionStep.sourceNodeId) {
        // Clicked source again - cancel
        setConnectionStep({ step: 'source' });
        setHighlightedNodes(new Set());
        return;
      }
      
      // Create connection
      const edgeId = `e${connectionStep.sourceNodeId}-${nodeId}`;
      const newEdge = {
        id: edgeId,
        source: connectionStep.sourceNodeId,
        target: nodeId,
      };
      
      addEdge(newEdge);
      onConnectionCreated(connectionStep.sourceNodeId, nodeId);
      
      // Show completion feedback
      setConnectionStep({ 
        step: 'complete', 
        sourceNodeId: connectionStep.sourceNodeId, 
        targetNodeId: nodeId 
      });
      
      // Auto-reset after brief delay
      setTimeout(() => {
        setConnectionStep({ step: 'source' });
        setHighlightedNodes(new Set());
      }, 1000);
    }
  }, [isActive, connectionStep, nodes, addEdge, onConnectionCreated]);

  // Add click listeners to nodes when in connection mode
  useEffect(() => {
    if (!isActive) return;

    const handleClickEvent = (e: Event) => {
      const nodeElement = (e.target as HTMLElement).closest('.react-flow__node');
      if (nodeElement) {
        const nodeId = nodeElement.getAttribute('data-id');
        if (nodeId) {
          handleNodeClick(nodeId);
        }
      }
    };

    const canvas = document.querySelector('.react-flow__pane');
    canvas?.addEventListener('click', handleClickEvent);

    return () => {
      canvas?.removeEventListener('click', handleClickEvent);
    };
  }, [isActive, handleNodeClick]);

  // Add visual indicators to nodes
  useEffect(() => {
    if (!isActive) {
      // Remove all indicators
      document.querySelectorAll('.react-flow__node').forEach(node => {
        node.classList.remove('mobile-connection-source', 'mobile-connection-target', 'mobile-connection-highlighted');
      });
      return;
    }

    // Add appropriate classes to nodes
    document.querySelectorAll('.react-flow__node').forEach(node => {
      const nodeId = node.getAttribute('data-id');
      if (!nodeId) return;

      node.classList.remove('mobile-connection-source', 'mobile-connection-target', 'mobile-connection-highlighted');

      if (connectionStep.sourceNodeId === nodeId) {
        node.classList.add('mobile-connection-source');
      } else if (highlightedNodes.has(nodeId)) {
        node.classList.add('mobile-connection-highlighted');
      }
    });
  }, [isActive, connectionStep, highlightedNodes]);

  const getInstructions = () => {
    switch (connectionStep.step) {
      case 'source':
        return 'Tap a node to start connecting';
      case 'target':
        return `Connecting from ${nodes.find(n => n.id === connectionStep.sourceNodeId)?.data?.label || 'node'}. Tap target node.`;
      case 'complete':
        return 'Connection created!';
      default:
        return '';
    }
  };

  const getIcon = () => {
    switch (connectionStep.step) {
      case 'complete':
        return CheckCircle;
      default:
        return Link;
    }
  };

  if (!isActive) return null;

  const Icon = getIcon();

  return (
    <>
      {/* Connection Mode Overlay */}
      <div className="fixed inset-0 z-40 pointer-events-none">
        <div className="absolute inset-0 bg-purple-500/10 backdrop-blur-sm" />
      </div>

      {/* Instruction Panel */}
      <div className="fixed top-20 left-4 right-4 z-50 md:hidden">
        <div className="bg-slate-800/95 backdrop-blur-lg border border-white/10 rounded-xl p-4 shadow-xl">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-10 h-10 rounded-full flex items-center justify-center",
              connectionStep.step === 'complete' 
                ? "bg-green-500/20 text-green-400"
                : "bg-purple-500/20 text-purple-400"
            )}>
              <Icon className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-white">Connection Mode</h3>
              <p className="text-xs text-slate-400">{getInstructions()}</p>
            </div>
            <button
              onClick={onToggle}
              className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          
          {connectionStep.step === 'target' && (
            <div className="mt-3 pt-3 border-t border-white/10">
              <p className="text-xs text-slate-500">
                Tip: Tap the source node again to cancel
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="fixed bottom-24 left-4 right-4 z-50 md:hidden">
        <div className="bg-slate-800/95 backdrop-blur-lg border border-white/10 rounded-lg px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className={cn(
                  "w-2 h-2 rounded-full",
                  connectionStep.step === 'source' ? "bg-purple-400" : "bg-green-400"
                )}>
                </span>
                <span className="text-xs text-slate-300">Source</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={cn(
                  "w-2 h-2 rounded-full",
                  connectionStep.step === 'target' ? "bg-purple-400" : 
                  connectionStep.step === 'complete' ? "bg-green-400" : "bg-slate-600"
                )}>
                </span>
                <span className="text-xs text-slate-300">Target</span>
              </div>
            </div>
            
            {connectionStep.sourceNodeId && (
              <div className="text-right">
                <div className="text-xs text-slate-400">From:</div>
                <div className="text-xs font-medium text-white truncate max-w-[100px]">
                  {nodes.find(n => n.id === connectionStep.sourceNodeId)?.data?.label || 'Node'}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}