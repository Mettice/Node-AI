/**
 * Main workflow canvas component using React Flow
 */

import { useCallback, useRef, useState, useEffect, useMemo } from 'react';
import ReactFlow, {
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Panel,
} from 'reactflow';
import type {
  Node,
  Edge,
  Connection,
  NodeTypes,
  EdgeTypes,
  ReactFlowInstance,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useWorkflowStore } from '@/store/workflowStore';
import { useUIStore } from '@/store/uiStore';
import { NODE_CATEGORY_COLORS } from '@/constants';
import { CustomNode } from './CustomNode';
import { CustomEdge } from './CustomEdge';
import { ExecutionStatusIcon } from './ExecutionStatusIcon';
import { ExecutionControls } from '@/components/Execution/ExecutionControls';
import { ExecutionStatusBar } from '@/components/Execution/ExecutionStatusBar';
import { AddNodeButton } from './AddNodeButton';
import { MobileToolbar } from './MobileToolbar';
import { NodePalettePopup } from './NodePalettePopup';
import { MobileNodeEditor } from './MobileNodeEditor';
import { MobileConnectionMode } from './MobileConnectionMode';
import { useMobileGestures } from '@/hooks/useMobileGestures';
import { MessageSquare, StickyNote, Square, Trash2, Copy, Group, Ungroup, Plug } from 'lucide-react';
import { IntegrationsPanel } from './IntegrationsPanel';

// Enhanced Canvas Interactions
import { 
  useCanvasInteractions, 
  AlignmentGuides, 
  AutoLayoutToolbar,
  QuickActionsToolbar 
} from './CanvasInteractions';
import { NodeGroups } from './NodeGroups';
import { StickyNotes } from './StickyNotes';

// Define node and edge types as constants outside component
// All node types use CustomNode - React Flow will use 'default' as fallback for unregistered types
const NODE_TYPES: NodeTypes = {
  default: CustomNode, // Fallback for any unregistered node type
  text_input: CustomNode,
  file_loader: CustomNode,
  webhook_input: CustomNode,
  chunk: CustomNode,
  embed: CustomNode,
  vector_store: CustomNode,
  vector_search: CustomNode,
  chat: CustomNode,
  memory: CustomNode,
  langchain_agent: CustomNode,
  tool: CustomNode,
  crewai_agent: CustomNode,
  // Intelligence nodes
  smart_data_analyzer: CustomNode,
  auto_chart_generator: CustomNode,
  content_moderator: CustomNode,
  meeting_summarizer: CustomNode,
  lead_scorer: CustomNode,
  ai_web_search: CustomNode,
  // Business nodes
  stripe_analytics: CustomNode,
  cost_optimizer: CustomNode,
  social_analyzer: CustomNode,
  ab_test_analyzer: CustomNode,
  // Content nodes
  blog_generator: CustomNode,
  brand_generator: CustomNode,
  podcast_transcriber: CustomNode,
  social_scheduler: CustomNode,
  // Developer nodes
  bug_triager: CustomNode,
  docs_writer: CustomNode,
  performance_monitor: CustomNode,
  security_scanner: CustomNode,
  // Sales nodes
  call_summarizer: CustomNode,
  followup_writer: CustomNode,
  lead_enricher: CustomNode,
  proposal_generator: CustomNode,
  // Multi-modal nodes
  ocr: CustomNode,
  transcribe: CustomNode,
  video_frames: CustomNode,
  data_loader: CustomNode,
  data_to_text: CustomNode,
  vision: CustomNode,
  // Retrieval nodes
  rerank: CustomNode,
  hybrid_retrieval: CustomNode,
  bm25_search: CustomNode,
  // Storage nodes
  knowledge_graph: CustomNode,
  s3: CustomNode,
  database: CustomNode,
  azure_blob: CustomNode,
  // Communication nodes
  email: CustomNode,
  slack: CustomNode,
  // Storage nodes (OAuth)
  google_drive: CustomNode,
  google_sheets: CustomNode,
  airtable: CustomNode,
  // Integration nodes
  reddit: CustomNode,
  // Processing nodes
  advanced_nlp: CustomNode,
  // Training nodes
  finetune: CustomNode,
};

const EDGE_TYPES: EdgeTypes = {
  custom: CustomEdge,
};

export function WorkflowCanvas() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const [addNodeOpen, setAddNodeOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [connectionMode, setConnectionMode] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [selectedNodeIds, setSelectedNodeIds] = useState<string[]>([]);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId: string } | null>(null);
  const [integrationsOpen, setIntegrationsOpen] = useState(false);
  
  const { toggleChatInterface } = useUIStore();

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Mobile gestures (only enabled on mobile)
  const mobileGestures = useMobileGestures(
    isMobile ? {
      onDoubleTap: (x, y) => {
        if (reactFlowInstance) {
          const position = reactFlowInstance.project({ x, y });
          console.log('Double tap at:', position);
        }
      },
      onLongPress: (x, y) => {
        if (reactFlowInstance) {
          const position = reactFlowInstance.project({ x, y });
          console.log('Long press at:', position);
        }
      },
    } : {}
  );
  
  // Use constants directly - they're defined outside component so they're stable
  // React Flow will only warn if these are recreated on each render
  const nodeTypes = NODE_TYPES;
  const edgeTypes = EDGE_TYPES;
  
  const {
    nodes: storeNodes,
    edges: storeEdges,
    addNode,
    removeNode,
    updateNodePosition,
    addEdge: addEdgeToStore,
    removeEdge,
    selectNode,
    undo,
    redo,
    canUndo,
    canRedo,
  } = useWorkflowStore();

  // Initialize React Flow state from store
  const [nodes, setNodes, onNodesChange] = useNodesState(storeNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(storeEdges);

  // Enhanced Canvas Interactions
  const canvasInteractions = useCanvasInteractions({
    reactFlowInstance,
    nodes,
    edges,
    selectedNodes: selectedNodeIds
  });

  // Sync store nodes with React Flow nodes (only when store changes externally)
  // Use a ref to track previous store state to avoid infinite loops
  const prevStoreNodesRef = useRef(storeNodes);
  const prevStoreEdgesRef = useRef(storeEdges);

  useEffect(() => {
    // Check if nodes changed by comparing their JSON representation
    // This catches both ID changes (add/remove) and data/config changes
    const storeNodesStr = JSON.stringify(storeNodes);
    const prevStoreNodesStr = JSON.stringify(prevStoreNodesRef.current);
    
    if (storeNodesStr !== prevStoreNodesStr) {
      setNodes(storeNodes);
      prevStoreNodesRef.current = storeNodes;
    }
  }, [storeNodes, setNodes]);

  useEffect(() => {
    // Only sync if store edges changed externally (not from React Flow)
    const storeEdgeIds = storeEdges.map(e => e.id).join(',');
    const prevStoreEdgeIds = prevStoreEdgesRef.current.map(e => e.id).join(',');
    
    if (storeEdgeIds !== prevStoreEdgeIds) {
      setEdges(storeEdges);
      prevStoreEdgesRef.current = storeEdges;
    }
  }, [storeEdges, setEdges]);

  // Track node selection changes directly from nodes state
  useEffect(() => {
    const currentlySelected = nodes.filter(node => node.selected).map(node => node.id);
    setSelectedNodeIds(currentlySelected);
  }, [nodes]);

  // Close context menu when clicking outside
  useEffect(() => {
    if (!contextMenu) return;

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.node-context-menu')) {
        setContextMenu(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [contextMenu]);

  // Handle node drag start
  const onNodeDragStart = useCallback(() => {
    canvasInteractions.setIsDragging(true);
  }, [canvasInteractions]);

  // Handle node drag stop
  const onNodeDragStop = useCallback(() => {
    canvasInteractions.setIsDragging(false);
    // Clear alignment guides when drag ends
    canvasInteractions.setShowGuides(false);
    // Update group positions after dragging nodes
    canvasInteractions.updateGroupPositions();
  }, [canvasInteractions]);

  // Handle node changes
  const handleNodesChange = useCallback(
    (changes: any) => {
      // Process all changes normally
      const filteredChanges = changes;
      
      onNodesChange(filteredChanges);
      
      // Selection changes are now tracked via useEffect on nodes state
      
      // Update store for position changes with smart snapping
      filteredChanges.forEach((change: any) => {
        if (change.type === 'position' && change.position) {
          // Apply smart snapping if dragging
          if (canvasInteractions.isDragging) {
            const snappedPosition = canvasInteractions.calculateSnapPosition(change.id, change.position);
            // Update both store and ReactFlow node state with snapped position
            updateNodePosition(change.id, snappedPosition);
            // Update the node in ReactFlow state to reflect snapped position
            setNodes((nds) =>
              nds.map((node) =>
                node.id === change.id
                  ? { ...node, position: snappedPosition }
                  : node
              )
            );
            // Update group positions in real-time while dragging
            canvasInteractions.updateGroupPositions();
          } else {
            // Just update store when not dragging
            updateNodePosition(change.id, change.position);
            // Update group positions after position change
            canvasInteractions.updateGroupPositions();
          }
        } else if (change.type === 'remove') {
          removeNode(change.id);
        }
      });
    },
    [onNodesChange, updateNodePosition, removeNode, nodes, canvasInteractions, setNodes]
  );

  // Handle edge changes
  const handleEdgesChange = useCallback(
    (changes: any) => {
      onEdgesChange(changes);
      
      // Update store for edge removals
      changes.forEach((change: any) => {
        if (change.type === 'remove') {
          removeEdge(change.id);
        }
      });
    },
    [onEdgesChange, removeEdge]
  );

  // Handle new connections
  const onConnect = useCallback(
    (params: Connection) => {
      if (params.source && params.target) {
        const newEdge = {
          id: `e${params.source}-${params.target}`,
          source: params.source,
          target: params.target,
          sourceHandle: params.sourceHandle || undefined,
          targetHandle: params.targetHandle || undefined,
          type: 'custom',
        };
        
        addEdgeToStore(newEdge as Edge);
        setEdges((eds) => addEdge(params, eds));
      }
    },
    [addEdgeToStore, setEdges]
  );

  // Handle node click - support Ctrl/Cmd + left-click for multi-select
  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      // Don't handle click if clicking on textarea (for text_input nodes)
      if ((event.target as HTMLElement).closest('textarea')) {
        return;
      }
      
      // If Ctrl/Cmd is held, allow multi-select with left-click
      const isMultiSelect = event.ctrlKey || event.metaKey;
      if (isMultiSelect) {
        event.preventDefault();
        event.stopPropagation();
        
        // Toggle selection for this node, keep others selected
        setNodes((nds) =>
          nds.map((n) => {
            if (n.id === node.id) {
              return { ...n, selected: !n.selected };
            }
            return n; // Keep other nodes' selection state
          })
        );
        return;
      }
      
      // Normal left-click - node component handles preview modal
      // We don't need to do anything here for normal clicks
    },
    [setNodes]
  );

  // Handle right-click on nodes - toggle selection and show context menu
  const onNodeContextMenu = useCallback(
    (event: React.MouseEvent, node: Node) => {
      event.preventDefault(); // Prevent default context menu
      event.stopPropagation(); // Stop event bubbling
      
      const isMultiSelect = event.ctrlKey || event.metaKey;
      
      // Toggle node selection
      setNodes((nds) => {
        return nds.map((n) => {
          if (n.id === node.id) {
            // Toggle selection for the clicked node
            return { ...n, selected: !n.selected };
          }
          // If not holding Ctrl/Cmd, deselect all other nodes
          if (!isMultiSelect) {
            return { ...n, selected: false };
          }
          // If holding Ctrl/Cmd, keep other nodes' selection state unchanged
          return n;
        });
      });
      
      // Show context menu at mouse position
      setContextMenu({
        x: event.clientX,
        y: event.clientY,
        nodeId: node.id,
      });
    },
    [setNodes]
  );

  // Handle pane click (deselect all and close context menu)
  const onPaneClick = useCallback(() => {
    selectNode(null);
    // Also deselect all nodes
    setNodes((nds) => nds.map((n) => ({ ...n, selected: false })));
    setContextMenu(null); // Close context menu
    setSelectedNodeIds([]); // Clear selected node IDs
  }, [selectNode, setNodes]);

  // Handle pane context menu (prevent browser context menu on canvas)
  const onPaneContextMenu = useCallback((event: React.MouseEvent) => {
    event.preventDefault(); // Prevent browser context menu
    event.stopPropagation();
    // Optionally: Could show a canvas-level context menu here in the future
  }, []);

  // Handle drag over
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      event.stopPropagation();

      if (!reactFlowInstance) {
        console.warn('ReactFlow instance not available');
        return;
      }

      // Try to get data from application/reactflow first, then fallback to text/plain
      let data = event.dataTransfer.getData('application/reactflow');
      if (!data) {
        data = event.dataTransfer.getData('text/plain');
      }

      if (!data) {
        console.warn('No drag data found. Available types:', event.dataTransfer.types);
        return;
      }

      try {
        const { type, data: nodeData } = JSON.parse(data);
        
        // Get the position relative to the ReactFlow viewport
        const position = reactFlowInstance.screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });

        const newNode = {
          id: `${type}-${Date.now()}`,
          type: type,
          position,
          data: {
            ...nodeData,
            label: nodeData.label || type,
          },
        };

        addNode(newNode);
      } catch (error) {
        console.error('Error parsing dropped node:', error, data);
      }
    },
    [reactFlowInstance, addNode]
  );

  // Mobile toolbar handlers
  const handleMobileAddNode = useCallback(() => {
    setAddNodeOpen(true);
  }, []);

  const handleMobileSave = useCallback(() => {
    // Placeholder - integrate with save functionality from WorkflowHeader
    console.log('Mobile save triggered');
  }, []);

  const handleMobileRun = useCallback(() => {
    // Placeholder - integrate with execution functionality
    console.log('Mobile run triggered');
  }, []);

  const handleMobileConnection = useCallback(() => {
    setConnectionMode(!connectionMode);
  }, [connectionMode]);

  const handleNodeEdit = useCallback((node: Node) => {
    setSelectedNode(node);
  }, []);

  const handleNodeSave = useCallback((nodeData: any) => {
    if (selectedNode) {
      const updatedNode = { ...selectedNode, data: nodeData };
      setNodes(nodes => nodes.map(n => n.id === selectedNode.id ? updatedNode : n));
      setSelectedNode(null);
    }
  }, [selectedNode, setNodes]);

  const handleNodeDelete = useCallback(() => {
    if (selectedNode) {
      removeNode(selectedNode.id);
      setSelectedNode(null);
    }
  }, [selectedNode, removeNode]);

  const handleConnectionCreated = useCallback((sourceId: string, targetId: string) => {
    console.log('Connection created:', sourceId, '->', targetId);
    setConnectionMode(false);
  }, []);

  // Canvas interaction handlers
  const handleCanvasDoubleClick = useCallback((event: React.MouseEvent) => {
    if (!reactFlowInstance) return;
    
    const position = reactFlowInstance.screenToFlowPosition({
      x: event.clientX,
      y: event.clientY,
    });
    
    // Add sticky note on double-click
    canvasInteractions.addStickyNote(position);
  }, [reactFlowInstance, canvasInteractions]);

  const handleQuickActions = {
    align: canvasInteractions.alignSelectedNodes,
    distribute: canvasInteractions.distributeSelectedNodes,
    group: () => {
      if (selectedNodeIds.length > 1) {
        canvasInteractions.createGroup(selectedNodeIds, 'New Group');
      }
    },
    ungroup: () => {
      if (selectedNodeIds.length > 0) {
        canvasInteractions.ungroupSelectedNodes(selectedNodeIds);
      }
    },
    delete: () => {
      selectedNodeIds.forEach(nodeId => removeNode(nodeId));
      setSelectedNodeIds([]);
    },
    duplicate: () => {
      // Duplicate selected nodes
      selectedNodeIds.forEach(nodeId => {
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
          const newNode = {
            ...node,
            id: `${node.type}-${Date.now()}-copy`,
            position: {
              x: node.position.x + 50,
              y: node.position.y + 50,
            },
          };
          addNode(newNode);
        }
      });
    },
    disconnect: () => {
      // Remove all edges connected to selected nodes
      selectedNodeIds.forEach(nodeId => {
        const connectedEdges = edges.filter(
          edge => edge.source === nodeId || edge.target === nodeId
        );
        connectedEdges.forEach(edge => removeEdge(edge.id));
      });
    },
  };

  return (
    <div 
      className="w-full h-full canvas-dark flex flex-col" 
      ref={reactFlowWrapper}
    >
      {/* Ambient glow layer - creates living atmosphere */}
      <div className="canvas-ambient-glow" />
      
      <div 
        className="flex-1 relative"
        onDoubleClick={handleCanvasDoubleClick}
        onContextMenu={(e) => {
          // Prevent browser context menu on canvas area
          e.preventDefault();
          e.stopPropagation();
        }}
      >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onNodeContextMenu={onNodeContextMenu}
        onNodeDragStart={onNodeDragStart}
        onNodeDragStop={onNodeDragStop}
        onPaneClick={onPaneClick}
        onPaneContextMenu={onPaneContextMenu}
        onInit={(instance) => {
          setReactFlowInstance(instance);
        }}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultEdgeOptions={{
          type: 'custom',
          style: { strokeWidth: 2 },
        }}
        fitView
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        minZoom={0.1}
        maxZoom={2}
        panOnDrag={true} // Pan with left mouse on empty space, middle mouse anywhere
        panOnScroll
        zoomOnScroll
        zoomOnPinch
        zoomOnDoubleClick={false}
        nodesDraggable={true} // Explicitly enable node dragging
        nodesConnectable={true} // Enable node connections
        selectNodesOnDrag={false} // Don't select when dragging nodes
        selectionOnDrag={true} // Enable selection box (Shift + drag)
        className="react-flow-canvas"
      >
        {/* Grid is in CSS - no React Flow Background needed */}
        <Controls className="react-flow__controls mobile-optimized" />
        
        <MiniMap 
          position="bottom-left"
          className="react-flow__minimap hidden md:block m-4"
          maskColor="rgba(6, 8, 13, 0.6)"
          nodeColor={(node) => {
            const category = node.data?.category || 'default';
            return NODE_CATEGORY_COLORS[category as keyof typeof NODE_CATEGORY_COLORS] || '#64748b';
          }}
          nodeStrokeWidth={3}
          zoomable
          pannable
        />
        
        {/* Top Left Panel - Hidden on mobile */}
        <Panel position="top-left" className="hidden md:block">
          <div className="relative">
            <div className="glass rounded-lg p-2 md:p-4 flex items-center gap-3">
              <div className="text-xs md:text-sm text-slate-300">
                Nodes: {nodes.length} | Edges: {edges.length}
              </div>
              <div className="w-px h-4 bg-white/20" />
              <button
                onClick={() => setIntegrationsOpen(!integrationsOpen)}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs transition-all ${
                  integrationsOpen
                    ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                    : 'hover:bg-white/10 text-slate-300 hover:text-white'
                }`}
                title="MCP Integrations (Slack, Gmail, Airtable...)"
              >
                <Plug className="w-3.5 h-3.5" />
                <span>MCP</span>
              </button>
            </div>

            {/* Integrations Panel Dropdown */}
            <IntegrationsPanel
              isOpen={integrationsOpen}
              onClose={() => setIntegrationsOpen(false)}
              onOpenSettings={() => {
                setIntegrationsOpen(false);
                // Navigate to MCP settings - this would need to be connected to your routing
                window.dispatchEvent(new CustomEvent('open-settings', { detail: { tab: 'mcp' } }));
              }}
            />
          </div>
        </Panel>
        
        {/* Top Right Panel - Execution Status */}
        <Panel position="top-right" className="glass rounded-lg p-2 md:p-4">
          <ExecutionStatusIcon />
        </Panel>
        
        {/* Bottom Center Panel - Mobile responsive */}
        <Panel position="bottom-center" className="glass rounded-lg p-2 md:p-4 mb-16 md:mb-0">
          <ExecutionControls />
        </Panel>
        
        {/* Canvas Interaction Tools - Bottom Right */}
        <Panel position="bottom-right" className="flex flex-col gap-2 mb-16 md:mb-0">
          {/* Auto Layout Toolbar */}
          {!isMobile && (
            <AutoLayoutToolbar 
              onLayoutApply={canvasInteractions.applyAutoLayout}
              reactFlowInstance={reactFlowInstance}
            />
          )}
          
          {/* Add Sticky Note Button */}
          <button
            onClick={() => {
              const center = { x: 400, y: 300 };
              canvasInteractions.addStickyNote(center);
            }}
            className="glass p-2 rounded-lg hover:bg-white/10 transition-colors text-slate-300 hover:text-white"
            title="Add Sticky Note"
          >
            <StickyNote className="w-5 h-5" />
          </button>

          {/* Chat Button */}
          <button
            onClick={toggleChatInterface}
            className="flex items-center gap-1 md:gap-2 px-2 md:px-3 py-1.5 md:py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition-all duration-200 hover:scale-105"
            title="Open Chat Interface"
          >
            <MessageSquare className="w-4 md:w-5 h-4 md:h-5" />
            <span className="text-xs md:text-sm font-medium hidden sm:inline">Chat</span>
          </button>
        </Panel>
      </ReactFlow>
      
      {/* Canvas Interaction Overlays */}
      <AlignmentGuides 
        guides={canvasInteractions.alignmentGuides}
        showGuides={canvasInteractions.showGuides}
      />
      
      <NodeGroups 
        groups={canvasInteractions.nodeGroups}
        onUpdateGroup={canvasInteractions.updateGroup}
        onDeleteGroup={canvasInteractions.deleteGroup}
        nodes={nodes}
        onSelectNodes={(nodeIds) => {
          // Select all nodes in the group
          setNodes((nds) =>
            nds.map((n) => ({
              ...n,
              selected: nodeIds.includes(n.id),
            }))
          );
        }}
      />
      
      <StickyNotes 
        notes={canvasInteractions.stickyNotes}
        onUpdateNote={canvasInteractions.updateStickyNote}
        onDeleteNote={canvasInteractions.deleteStickyNote}
      />
      
      <QuickActionsToolbar
        selectedNodes={selectedNodeIds}
        onAlign={handleQuickActions.align}
        onDistribute={handleQuickActions.distribute}
        onGroup={handleQuickActions.group}
        onUngroup={handleQuickActions.ungroup}
        onDelete={handleQuickActions.delete}
        onDuplicate={handleQuickActions.duplicate}
        onDisconnect={handleQuickActions.disconnect}
      />
      
      {/* Node Context Menu - Right-click menu */}
      {contextMenu && (
        <div
          className="node-context-menu fixed z-50 glass border border-white/10 rounded-lg p-1 shadow-2xl bg-slate-900/95 backdrop-blur-xl min-w-[180px]"
          style={{
            left: `${contextMenu.x}px`,
            top: `${contextMenu.y}px`,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => {
              handleQuickActions.duplicate();
              setContextMenu(null);
            }}
            className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:text-white hover:bg-white/10 rounded flex items-center gap-2 transition-colors"
          >
            <Copy className="w-4 h-4" />
            Duplicate
          </button>
          
          {selectedNodeIds.length > 1 && (
            <button
              onClick={() => {
                handleQuickActions.group();
                setContextMenu(null);
              }}
              className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:text-white hover:bg-white/10 rounded flex items-center gap-2 transition-colors"
            >
              <Group className="w-4 h-4" />
              Group Nodes
            </button>
          )}
          
          <button
            onClick={() => {
              handleQuickActions.disconnect();
              setContextMenu(null);
            }}
            className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:text-white hover:bg-white/10 rounded flex items-center gap-2 transition-colors"
          >
            <Ungroup className="w-4 h-4" />
            Disconnect All
          </button>
          
          <div className="border-t border-white/10 my-1" />
          
          <button
            onClick={() => {
              handleQuickActions.delete();
              setContextMenu(null);
            }}
            className="w-full px-3 py-2 text-left text-sm text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded flex items-center gap-2 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      )}
      
      {/* Floating Add Node Button - Always visible and draggable */}
      <AddNodeButton />
      </div>
      
      {/* Execution Status Bar - Fixed at bottom */}
      <ExecutionStatusBar />
      
      {/* Mobile Toolbar - Only on mobile */}
      {isMobile && (
        <MobileToolbar
          onAddNode={handleMobileAddNode}
          onSave={handleMobileSave}
          onRun={handleMobileRun}
          onUndo={() => canUndo() && undo()}
          onRedo={() => canRedo() && redo()}
          onConnectionMode={handleMobileConnection}
          canUndo={canUndo()}
          canRedo={canRedo()}
          isSaving={false}
          isRunning={false}
          isConnectionMode={connectionMode}
        />
      )}

      {/* Mobile Node Palette - Bottom drawer */}
      {isMobile && addNodeOpen && (
        <NodePalettePopup
          isOpen={addNodeOpen}
          onClose={() => setAddNodeOpen(false)}
          position={{ x: 0, y: 0 }} // Not used for mobile
          isMobile={true}
        />
      )}

      {/* Mobile Node Editor */}
      {isMobile && selectedNode && (
        <MobileNodeEditor
          node={selectedNode}
          isOpen={!!selectedNode}
          onClose={() => setSelectedNode(null)}
          onSave={handleNodeSave}
          onDelete={handleNodeDelete}
        />
      )}

      {/* Mobile Connection Mode */}
      {isMobile && (
        <MobileConnectionMode
          isActive={connectionMode}
          onToggle={() => setConnectionMode(false)}
          onConnectionCreated={handleConnectionCreated}
        />
      )}
    </div>
  );
}

