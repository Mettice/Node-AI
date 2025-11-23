/**
 * Main workflow canvas component using React Flow
 */

import { useCallback, useRef, useState, useEffect, useMemo } from 'react';
import ReactFlow, {
  Controls,
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
import { CustomNode } from './CustomNode';
import { CustomEdge } from './CustomEdge';
import { ExecutionStatusIcon } from './ExecutionStatusIcon';
import { ExecutionControls } from '@/components/Execution/ExecutionControls';
import { ExecutionStatusBar } from '@/components/Execution/ExecutionStatusBar';
import { AddNodeButton } from './AddNodeButton';
import { MobileToolbar } from './MobileToolbar';
import { MessageSquare } from 'lucide-react';

// Define node and edge types as constants outside component
const NODE_TYPES: NodeTypes = {
  default: CustomNode,
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
  const [isMobile, setIsMobile] = useState(false);
  
  const { toggleChatInterface } = useUIStore();

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
  // Memoize node and edge types to ensure stable references
  // Even though they're constants, ReactFlow needs stable references
  const nodeTypes = useMemo(() => NODE_TYPES, []);
  const edgeTypes = useMemo(() => EDGE_TYPES, []);
  
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

  // Handle node changes
  const handleNodesChange = useCallback(
    (changes: any) => {
      // Process all changes normally
      const filteredChanges = changes;
      
      onNodesChange(filteredChanges);
      
      // Update store for position changes
      filteredChanges.forEach((change: any) => {
        if (change.type === 'position' && change.position) {
          updateNodePosition(change.id, change.position);
        } else if (change.type === 'remove') {
          removeNode(change.id);
        }
      });
    },
    [onNodesChange, updateNodePosition, removeNode, nodes]
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
        };
        
        addEdgeToStore(newEdge as Edge);
        setEdges((eds) => addEdge(params, eds));
      }
    },
    [addEdgeToStore, setEdges]
  );

  // Handle node click (node handles its own preview modal)
  const onNodeClick = useCallback(
    (event: React.MouseEvent, _node: Node) => {
      // Don't handle click if clicking on textarea (for text_input nodes)
      if ((event.target as HTMLElement).closest('textarea')) {
        return;
      }
      // Node component handles click to show preview modal
      // We don't need to do anything here
    },
    []
  );

  // Handle pane click (deselect)
  const onPaneClick = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

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

  return (
    <div 
      className="w-full h-full canvas-dark flex flex-col" 
      ref={reactFlowWrapper}
    >
      <div className="flex-1 relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        onInit={(instance) => {
          setReactFlowInstance(instance);
        }}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        minZoom={0.1}
        maxZoom={2}
        panOnDrag
        panOnScroll
        zoomOnScroll
        zoomOnPinch
        zoomOnDoubleClick={false}
        selectNodesOnDrag={false}
      >
        {/* Grid is in CSS - no React Flow Background needed */}
        <Controls className="react-flow__controls mobile-optimized" />
        
        {/* Top Left Panel - Hidden on mobile */}
        <Panel position="top-left" className="glass rounded-lg p-2 md:p-4 hidden md:block">
          <div className="text-xs md:text-sm text-slate-300">
            Nodes: {nodes.length} | Edges: {edges.length}
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
        
        {/* Bottom Right Panel - Chat button, mobile optimized */}
        <Panel position="bottom-right" className="glass rounded-lg p-2 md:p-4 flex items-center gap-2 md:gap-3 mb-16 md:mb-0">
          <button
            onClick={toggleChatInterface}
            className="flex items-center gap-1 md:gap-2 px-2 md:px-3 py-1.5 md:py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-all duration-200 hover:scale-105"
            title="Open Chat Interface"
          >
            <MessageSquare className="w-4 md:w-5 h-4 md:h-5" />
            <span className="text-xs md:text-sm font-medium hidden sm:inline">Chat</span>
          </button>
        </Panel>
      </ReactFlow>
      </div>
      
      {/* Floating Add Node Button */}
      <AddNodeButton />
      
      {/* Execution Status Bar - Fixed at bottom */}
      <ExecutionStatusBar />
    </div>
  );
}

