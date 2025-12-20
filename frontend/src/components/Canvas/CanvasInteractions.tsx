/**
 * Canvas Interactions Enhancement - "Living Intelligence" UX
 * 
 * Features:
 * - Smart snapping with alignment guides
 * - Auto-layout algorithms (horizontal, vertical, radial)
 * - Grouping/frames system
 * - Comments/sticky notes
 * - Quick actions toolbar for multi-selection
 */

import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import type { Node, Edge, ReactFlowInstance } from 'reactflow';
import { 
  LayoutGrid, 
  Square, 
  MessageSquare, 
  Trash2, 
  Copy, 
  Move, 
  AlignLeft, 
  AlignCenter,
  Group,
  Ungroup,
  RotateCcw,
  StickyNote,
  Zap,
  ArrowRight,
  ArrowDown,
  Circle,
  Network,
  Maximize2
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useWorkflowStore } from '@/store/workflowStore';

// Smart snapping configuration
const SNAP_DISTANCE = 20;
const GRID_SIZE = 20;

// Alignment guide data
interface AlignmentGuide {
  id: string;
  type: 'horizontal' | 'vertical';
  position: number;
  nodeIds: string[];
}

// Group/Frame data
export interface NodeGroup {
  id: string;
  label: string;
  nodeIds: string[];
  position: { x: number; y: number };
  size: { width: number; height: number };
  color: string;
  collapsed: boolean;
  labelPosition?: { x: number; y: number }; // Absolute position for draggable label
  labelOffset?: { x: number; y: number }; // Offset from first node's top-right (for following nodes)
}

// Comment/Sticky Note data
export interface StickyNote {
  id: string;
  position: { x: number; y: number };
  content: string;
  color: string;
  size: { width: number; height: number };
}

// Auto-layout options
export type LayoutType = 'horizontal' | 'vertical' | 'radial' | 'hierarchical';

interface CanvasInteractionsProps {
  reactFlowInstance: ReactFlowInstance | null;
  nodes: Node[];
  edges: Edge[];
  selectedNodes: string[];
}

export function useCanvasInteractions({ 
  reactFlowInstance, 
  nodes, 
  edges, 
  selectedNodes 
}: CanvasInteractionsProps) {
  const [alignmentGuides, setAlignmentGuides] = useState<AlignmentGuide[]>([]);
  const [showGuides, setShowGuides] = useState(false);
  const [nodeGroups, setNodeGroups] = useState<NodeGroup[]>([]);
  const [stickyNotes, setStickyNotes] = useState<StickyNote[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  
  const { updateNodePosition } = useWorkflowStore();

  // Smart snapping functionality
  const calculateSnapPosition = useCallback((nodeId: string, position: { x: number; y: number }) => {
    if (!reactFlowInstance) return position;

    const otherNodes = nodes.filter(n => n.id !== nodeId);
    const guides: AlignmentGuide[] = [];
    let snappedPosition = { ...position };
    let hasAlignment = false;

    // Check for horizontal alignment (Y-axis snapping)
    otherNodes.forEach(node => {
      const yDiff = Math.abs(position.y - node.position.y);
      if (yDiff < SNAP_DISTANCE) {
        snappedPosition.y = node.position.y;
        hasAlignment = true;
        guides.push({
          id: `h-${node.id}`,
          type: 'horizontal',
          position: node.position.y,
          nodeIds: [nodeId, node.id]
        });
      }
    });

    // Check for vertical alignment (X-axis snapping)
    otherNodes.forEach(node => {
      const xDiff = Math.abs(position.x - node.position.x);
      if (xDiff < SNAP_DISTANCE) {
        snappedPosition.x = node.position.x;
        hasAlignment = true;
        guides.push({
          id: `v-${node.id}`,
          type: 'vertical',
          position: node.position.x,
          nodeIds: [nodeId, node.id]
        });
      }
    });

    // Grid snapping - only apply if no alignment guides are active
    // This prevents grid snapping from overriding alignment
    if (!hasAlignment) {
      snappedPosition.x = Math.round(snappedPosition.x / GRID_SIZE) * GRID_SIZE;
      snappedPosition.y = Math.round(snappedPosition.y / GRID_SIZE) * GRID_SIZE;
    }

    setAlignmentGuides(guides);
    setShowGuides(guides.length > 0);

    return snappedPosition;
  }, [nodes, reactFlowInstance]);

  // Auto-layout algorithms
  const applyAutoLayout = useCallback((layoutType: LayoutType) => {
    if (!reactFlowInstance) return;

    const updatedNodes = [...nodes];
    const padding = 150; // Reduced padding to match smaller node sizes

    switch (layoutType) {
      case 'horizontal':
        updatedNodes.forEach((node, index) => {
          node.position = {
            x: index * (190 + padding), // Updated for Tier 1 node width (190px)
            y: 100
          };
        });
        break;

      case 'vertical':
        updatedNodes.forEach((node, index) => {
          node.position = {
            x: 100,
            y: index * (140 + padding)
          };
        });
        break;

      case 'radial':
        const centerX = 400;
        const centerY = 300;
        const radius = 300;
        
        updatedNodes.forEach((node, index) => {
          const angle = (index / updatedNodes.length) * 2 * Math.PI;
          node.position = {
            x: centerX + radius * Math.cos(angle),
            y: centerY + radius * Math.sin(angle)
          };
        });
        break;

      case 'hierarchical':
        // Simple hierarchical layout based on node dependencies
        const levels: Node[][] = [];
        const processed = new Set<string>();
        
        // Find root nodes (no incoming edges)
        const rootNodes = updatedNodes.filter(node => 
          !edges.some(edge => edge.target === node.id)
        );
        
        if (rootNodes.length > 0) {
          levels.push(rootNodes);
          rootNodes.forEach(node => processed.add(node.id));
        }

        // Build levels based on dependencies
        while (processed.size < updatedNodes.length) {
          const nextLevel = updatedNodes.filter(node => 
            !processed.has(node.id) && 
            edges.filter(edge => edge.target === node.id)
              .every(edge => processed.has(edge.source))
          );

          if (nextLevel.length === 0) break; // Prevent infinite loop
          
          levels.push(nextLevel);
          nextLevel.forEach(node => processed.add(node.id));
        }

        // Position nodes by levels
        levels.forEach((level, levelIndex) => {
          level.forEach((node, nodeIndex) => {
            node.position = {
              x: nodeIndex * (190 + padding) - (level.length - 1) * (190 + padding) / 2, // Updated for Tier 1 node width (190px)
              y: levelIndex * (140 + padding)
            };
          });
        });
        break;
    }

    // Update all node positions
    updatedNodes.forEach(node => {
      updateNodePosition(node.id, node.position);
    });

    // Fit view to show all nodes
    setTimeout(() => {
      reactFlowInstance.fitView({ padding: 50 });
    }, 100);
  }, [nodes, edges, reactFlowInstance, updateNodePosition]);

  // Group management
  const createGroup = useCallback((nodeIds: string[], label: string = 'New Group') => {
    if (nodeIds.length === 0) return;

    const groupNodes = nodes.filter(node => nodeIds.includes(node.id));
    
    // Calculate group bounds
    const minX = Math.min(...groupNodes.map(n => n.position.x)) - 20;
    const minY = Math.min(...groupNodes.map(n => n.position.y)) - 40;
    const maxX = Math.max(...groupNodes.map(n => n.position.x + 280)) + 20;
    const maxY = Math.max(...groupNodes.map(n => n.position.y + 140)) + 20;

    // Cycle through colors for different groups
    const GROUP_COLORS = [
      '#3b82f6', // Blue
      '#10b981', // Emerald
      '#f59e0b', // Amber
      '#ef4444', // Red
      '#8b5cf6', // Violet
      '#ec4899', // Pink
      '#06b6d4', // Cyan
      '#84cc16', // Lime
    ];
    
    // Get next color that's not already used (or cycle if all used)
    setNodeGroups(prev => {
      const usedColors = prev.map(g => g.color);
      const availableColor = GROUP_COLORS.find(c => !usedColors.includes(c)) || 
                            GROUP_COLORS[prev.length % GROUP_COLORS.length];
      
      // Position label on top-right of the first node by default
      const firstNode = groupNodes[0];
      const defaultLabelPosition = {
        x: firstNode.position.x + 170, // Top-right of first node (190px width - 20px offset)
        y: firstNode.position.y - 5
      };

      const newGroup: NodeGroup = {
        id: `group-${Date.now()}`,
        label,
        nodeIds,
        position: { x: minX, y: minY },
        size: { width: maxX - minX, height: maxY - minY },
        color: availableColor,
        collapsed: false,
        labelPosition: defaultLabelPosition
      };

      return [...prev, newGroup];
    });
  }, [nodes]);

  const updateGroup = useCallback((groupId: string, updates: Partial<NodeGroup>) => {
    setNodeGroups(prev => prev.map(group => 
      group.id === groupId ? { ...group, ...updates } : group
    ));
  }, []);

  // Recalculate group positions based on current node positions
  const updateGroupPositions = useCallback(() => {
    setNodeGroups(prev => prev.map(group => {
      const groupNodes = nodes.filter(node => group.nodeIds.includes(node.id));
      if (groupNodes.length === 0) return group; // Skip if no nodes in group
      
      // Calculate group bounds from current node positions
      const minX = Math.min(...groupNodes.map(n => n.position.x)) - 20;
      const minY = Math.min(...groupNodes.map(n => n.position.y)) - 40;
      const maxX = Math.max(...groupNodes.map(n => n.position.x + 190)) + 20; // Updated for Tier 1 node width (190px)
      const maxY = Math.max(...groupNodes.map(n => n.position.y + 140)) + 20;
      
      // Update label position to follow first node using stored offset
      const firstNode = groupNodes[0];
      let labelPosition = group.labelPosition;
      let labelOffset = group.labelOffset;
      
      if (labelOffset) {
        // Apply stored offset to new base position
        const newBaseX = firstNode.position.x + 200; // Updated for Tier 1 node width (220px)
        const newBaseY = firstNode.position.y - 5;
        labelPosition = {
          x: newBaseX + labelOffset.x,
          y: newBaseY + labelOffset.y
        };
      } else if (labelPosition) {
        // Fallback: calculate offset from current position
        const newBaseX = firstNode.position.x + 200; // Updated for Tier 1 node width (220px)
        const newBaseY = firstNode.position.y - 5;
        labelOffset = {
          x: labelPosition.x - newBaseX,
          y: labelPosition.y - newBaseY
        };
        labelPosition = {
          x: newBaseX + labelOffset.x,
          y: newBaseY + labelOffset.y
        };
      } else {
        // Default position on top-right of first node
        labelPosition = {
          x: firstNode.position.x + 260,
          y: firstNode.position.y - 5
        };
      }
      
      return {
        ...group,
        position: { x: minX, y: minY },
        size: { width: maxX - minX, height: maxY - minY },
        labelPosition,
        labelOffset: labelOffset || group.labelOffset,
      };
    }));
  }, [nodes]);

  const deleteGroup = useCallback((groupId: string) => {
    setNodeGroups(prev => prev.filter(group => group.id !== groupId));
  }, []);

  // Ungroup selected nodes - remove them from their groups
  const ungroupSelectedNodes = useCallback((nodeIds: string[]) => {
    setNodeGroups(prev => prev.map(group => {
      // Remove selected nodes from this group
      const remainingNodeIds = group.nodeIds.filter(id => !nodeIds.includes(id));
      
      // If group becomes empty or has only one node, delete it
      if (remainingNodeIds.length <= 1) {
        return null; // Mark for deletion
      }
      
      // Update group with remaining nodes
      return {
        ...group,
        nodeIds: remainingNodeIds
      };
    }).filter(group => group !== null) as NodeGroup[]);
  }, []);

  // Sticky notes management
  const addStickyNote = useCallback((position: { x: number; y: number }) => {
    const newNote: StickyNote = {
      id: `note-${Date.now()}`,
      position,
      content: 'New note',
      color: '#fef3c7', // Soft yellow
      size: { width: 200, height: 150 }
    };

    setStickyNotes(prev => [...prev, newNote]);
  }, []);

  const updateStickyNote = useCallback((noteId: string, updates: Partial<StickyNote>) => {
    setStickyNotes(prev => prev.map(note => 
      note.id === noteId ? { ...note, ...updates } : note
    ));
  }, []);

  const deleteStickyNote = useCallback((noteId: string) => {
    setStickyNotes(prev => prev.filter(note => note.id !== noteId));
  }, []);

  // Multi-selection actions
  const alignSelectedNodes = useCallback((alignment: 'left' | 'center' | 'right' | 'top' | 'middle' | 'bottom') => {
    if (selectedNodes.length < 2) return;

    const selectedNodeObjects = nodes.filter(node => selectedNodes.includes(node.id));
    
    switch (alignment) {
      case 'left':
        const leftX = Math.min(...selectedNodeObjects.map(n => n.position.x));
        selectedNodeObjects.forEach(node => {
          updateNodePosition(node.id, { ...node.position, x: leftX });
        });
        break;
        
      case 'center':
        const avgX = selectedNodeObjects.reduce((sum, n) => sum + n.position.x, 0) / selectedNodeObjects.length;
        selectedNodeObjects.forEach(node => {
          updateNodePosition(node.id, { ...node.position, x: avgX });
        });
        break;
        
      case 'top':
        const topY = Math.min(...selectedNodeObjects.map(n => n.position.y));
        selectedNodeObjects.forEach(node => {
          updateNodePosition(node.id, { ...node.position, y: topY });
        });
        break;
        
      case 'middle':
        const avgY = selectedNodeObjects.reduce((sum, n) => sum + n.position.y, 0) / selectedNodeObjects.length;
        selectedNodeObjects.forEach(node => {
          updateNodePosition(node.id, { ...node.position, y: avgY });
        });
        break;
    }
  }, [selectedNodes, nodes, updateNodePosition]);

  const distributeSelectedNodes = useCallback((direction: 'horizontal' | 'vertical') => {
    if (selectedNodes.length < 3) return;

    const selectedNodeObjects = nodes.filter(node => selectedNodes.includes(node.id));
    
    if (direction === 'horizontal') {
      selectedNodeObjects.sort((a, b) => a.position.x - b.position.x);
      const totalWidth = selectedNodeObjects[selectedNodeObjects.length - 1].position.x - selectedNodeObjects[0].position.x;
      const spacing = totalWidth / (selectedNodeObjects.length - 1);
      
      selectedNodeObjects.forEach((node, index) => {
        const newX = selectedNodeObjects[0].position.x + (spacing * index);
        updateNodePosition(node.id, { ...node.position, x: newX });
      });
    } else {
      selectedNodeObjects.sort((a, b) => a.position.y - b.position.y);
      const totalHeight = selectedNodeObjects[selectedNodeObjects.length - 1].position.y - selectedNodeObjects[0].position.y;
      const spacing = totalHeight / (selectedNodeObjects.length - 1);
      
      selectedNodeObjects.forEach((node, index) => {
        const newY = selectedNodeObjects[0].position.y + (spacing * index);
        updateNodePosition(node.id, { ...node.position, y: newY });
      });
    }
  }, [selectedNodes, nodes, updateNodePosition]);

  return {
    // Snapping
    calculateSnapPosition,
    alignmentGuides,
    showGuides,
    setShowGuides,
    isDragging,
    setIsDragging,
    
    // Auto-layout
    applyAutoLayout,
    
    // Groups
    nodeGroups,
    createGroup,
    updateGroup,
    deleteGroup,
    ungroupSelectedNodes,
    updateGroupPositions,
    
    // Sticky notes
    stickyNotes,
    addStickyNote,
    updateStickyNote,
    deleteStickyNote,
    
    // Multi-selection actions
    alignSelectedNodes,
    distributeSelectedNodes
  };
}

// Alignment Guides Component
export function AlignmentGuides({ 
  guides, 
  showGuides 
}: { 
  guides: AlignmentGuide[]; 
  showGuides: boolean; 
}) {
  if (!showGuides || guides.length === 0) return null;

  return (
    <div className="absolute inset-0 pointer-events-none z-10">
      {guides.map(guide => (
        <div
          key={guide.id}
          className={cn(
            "absolute bg-blue-400/60 transition-opacity duration-200",
            guide.type === 'horizontal' ? "w-full h-0.5" : "w-0.5 h-full"
          )}
          style={{
            [guide.type === 'horizontal' ? 'top' : 'left']: guide.position,
            [guide.type === 'horizontal' ? 'left' : 'top']: 0
          }}
        />
      ))}
    </div>
  );
}

// Auto-Layout Toolbar Component
export function AutoLayoutToolbar({ 
  onLayoutApply,
  reactFlowInstance
}: { 
  onLayoutApply: (layout: LayoutType) => void;
  reactFlowInstance: ReactFlowInstance | null;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const layouts = [
    { 
      type: 'horizontal' as LayoutType, 
      label: 'Horizontal Flow', 
      icon: ArrowRight,
      description: 'Arrange nodes left to right'
    },
    { 
      type: 'vertical' as LayoutType, 
      label: 'Vertical Flow', 
      icon: ArrowDown,
      description: 'Arrange nodes top to bottom'
    },
    { 
      type: 'radial' as LayoutType, 
      label: 'Radial (AI Center)', 
      icon: Circle,
      description: 'Arrange nodes in a circle'
    },
    { 
      type: 'hierarchical' as LayoutType, 
      label: 'Hierarchical', 
      icon: Network,
      description: 'Arrange by dependencies'
    },
  ];

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (
        dropdownRef.current &&
        buttonRef.current &&
        !dropdownRef.current.contains(target) &&
        !buttonRef.current.contains(target)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Smart positioning: open upward if near bottom, downward if near top
  const [dropdownPosition, setDropdownPosition] = useState<'top' | 'bottom'>('top');
  
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const spaceBelow = viewportHeight - rect.bottom;
      const spaceAbove = rect.top;
      const dropdownHeight = 250; // Approximate dropdown height
      
      // Open upward if not enough space below, otherwise open downward
      setDropdownPosition(spaceBelow < dropdownHeight && spaceAbove > spaceBelow ? 'top' : 'bottom');
    }
  }, [isOpen]);

  const handleFitView = () => {
    if (reactFlowInstance) {
      reactFlowInstance.fitView({ padding: 50, duration: 300 });
      setIsOpen(false);
    }
  };

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="glass p-2 rounded-lg hover:bg-white/10 transition-colors text-slate-300 hover:text-white"
        title="Auto Layout"
      >
        <LayoutGrid className="w-5 h-5" />
      </button>
      
      {isOpen && (
        <div
          ref={dropdownRef}
          className={cn(
            "absolute left-0 glass border border-white/10 rounded-lg p-2 space-y-1 z-50",
            "bg-slate-900/95 backdrop-blur-xl shadow-2xl",
            dropdownPosition === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'
          )}
          style={{
            maxHeight: 'calc(100vh - 200px)',
            overflowY: 'auto',
          }}
        >
          {/* Icon-only layout buttons with hover tooltips */}
          <div className="flex flex-col gap-1">
            {layouts.map(layout => {
              const IconComponent = layout.icon;
              return (
                <button
                  key={layout.type}
                  onClick={() => {
                    onLayoutApply(layout.type);
                    setIsOpen(false);
                  }}
                  className="relative group p-2.5 rounded-md text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200 flex items-center justify-center"
                  title={layout.label}
                >
                  <IconComponent className="w-5 h-5" />
                  {/* Hover tooltip */}
                  <div className="absolute left-full ml-2 px-2 py-1 bg-slate-800/95 backdrop-blur-sm border border-white/10 rounded text-xs text-white whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 z-50 shadow-lg">
                    {layout.label}
                    <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-slate-800/95" />
                  </div>
                </button>
              );
            })}
          </div>
          
          {/* Separator */}
          <div className="border-t border-white/10 my-1" />
          
          {/* Fit View button */}
          <button
            onClick={handleFitView}
            className="relative group w-full p-2.5 rounded-md text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200 flex items-center justify-center"
            title="Fit View"
          >
            <Maximize2 className="w-5 h-5" />
            {/* Hover tooltip */}
            <div className="absolute left-full ml-2 px-2 py-1 bg-slate-800/95 backdrop-blur-sm border border-white/10 rounded text-xs text-white whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 z-50 shadow-lg">
              Fit View
              <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-slate-800/95" />
            </div>
          </button>
        </div>
      )}
    </div>
  );
}

// Quick Actions Toolbar for Node Selection
export function QuickActionsToolbar({
  selectedNodes,
  onAlign,
  onDistribute,
  onGroup,
  onUngroup,
  onDelete,
  onDuplicate,
  onDisconnect
}: {
  selectedNodes: string[];
  onAlign: (alignment: 'left' | 'center' | 'right' | 'top' | 'middle' | 'bottom') => void;
  onDistribute: (direction: 'horizontal' | 'vertical') => void;
  onGroup: () => void;
  onUngroup?: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
  onDisconnect: () => void;
}) {
  if (selectedNodes.length === 0) return null;

  const isSingleSelection = selectedNodes.length === 1;
  const isMultiSelection = selectedNodes.length > 1;

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 glass border border-white/10 rounded-lg p-2 flex items-center gap-2 z-20">
      <div className="text-xs text-slate-400 px-2">
        {selectedNodes.length} selected
      </div>
      
      <div className="w-px h-6 bg-white/10" />

      {/* Single node actions */}
      {isSingleSelection && (
        <>
          <button
            onClick={onDisconnect}
            className="p-2 hover:bg-white/10 rounded text-slate-400 hover:text-white transition-colors"
            title="Disconnect all edges"
          >
            <Ungroup className="w-4 h-4" />
          </button>
          <button
            onClick={onDuplicate}
            className="p-2 hover:bg-white/10 rounded text-slate-400 hover:text-white transition-colors"
            title="Duplicate node"
          >
            <Copy className="w-4 h-4" />
          </button>
        </>
      )}
      
      {/* Multi-selection actions */}
      {isMultiSelection && (
        <>
          <button
            onClick={() => onAlign('left')}
            className="p-2 hover:bg-white/10 rounded text-slate-400 hover:text-white transition-colors"
            title="Align left"
          >
            <AlignLeft className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => onAlign('center')}
            className="p-2 hover:bg-white/10 rounded text-slate-400 hover:text-white transition-colors"
            title="Align center"
          >
            <AlignCenter className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => onDistribute('horizontal')}
            className="p-2 hover:bg-white/10 rounded text-slate-400 hover:text-white transition-colors"
            title="Distribute horizontally"
          >
            <Move className="w-4 h-4" />
          </button>
          
          <div className="w-px h-6 bg-white/10" />
          
          <button
            onClick={onGroup}
            className="p-2 hover:bg-white/10 rounded text-slate-400 hover:text-white transition-colors"
            title="Group nodes"
          >
            <Group className="w-4 h-4" />
          </button>
          {onUngroup && (
            <button
              onClick={onUngroup}
              className="p-2 hover:bg-white/10 rounded text-slate-400 hover:text-white transition-colors"
              title="Ungroup nodes"
            >
              <Ungroup className="w-4 h-4" />
            </button>
          )}
          
          <button
            onClick={onDuplicate}
            className="p-2 hover:bg-white/10 rounded text-slate-400 hover:text-white transition-colors"
            title="Duplicate nodes"
          >
            <Copy className="w-4 h-4" />
          </button>
        </>
      )}
      
      {/* Common actions */}
      <button
        onClick={onDelete}
        className="p-2 hover:bg-red-500/20 rounded text-slate-400 hover:text-red-400 transition-colors"
        title={isSingleSelection ? "Delete node" : "Delete nodes"}
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  );
}