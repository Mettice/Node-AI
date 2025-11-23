/**
 * Workflow state management (Zustand)
 */

import { create } from 'zustand';
import type { Node as RFNode, Edge as RFEdge } from 'reactflow';
import type { Workflow } from '@/types/workflow';

// Use React Flow's Node and Edge types for internal state
type Node = RFNode;
type Edge = RFEdge;

interface WorkflowSnapshot {
  nodes: Node[];
  edges: Edge[];
  workflowName: string;
}

interface WorkflowState {
  // Workflow data
  nodes: Node[];
  edges: Edge[];
  workflowName: string;
  workflowId: string | null; // ID of saved workflow
  selectedNodeId: string | null;

  // History for undo/redo
  history: WorkflowSnapshot[];
  historyIndex: number;
  maxHistorySize: number;

  // Actions
  addNode: (node: Node) => void;
  removeNode: (nodeId: string) => void;
  updateNode: (nodeId: string, data: Partial<Node>) => void;
  updateNodePosition: (nodeId: string, position: { x: number; y: number }) => void;
  addEdge: (edge: Edge) => void;
  removeEdge: (edgeId: string) => void;
  selectNode: (nodeId: string | null) => void;
  setWorkflow: (workflow: Workflow) => void;
  clearWorkflow: () => void;
  setWorkflowName: (name: string) => void;
  setWorkflowId: (id: string | null) => void;
  
  // Undo/Redo actions
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
  _saveToHistory: () => void;
}

// Helper function to create a snapshot
const createSnapshot = (nodes: Node[], edges: Edge[], workflowName: string): WorkflowSnapshot => ({
  nodes: JSON.parse(JSON.stringify(nodes)), // Deep clone
  edges: JSON.parse(JSON.stringify(edges)), // Deep clone
  workflowName,
});

export const useWorkflowStore = create<WorkflowState>((set, get) => {
  const initialState: WorkflowSnapshot = {
    nodes: [],
    edges: [],
    workflowName: 'Untitled Workflow',
  };

  return {
    // Initial state
    nodes: [],
    edges: [],
    workflowName: 'Untitled Workflow',
    workflowId: null,
    selectedNodeId: null,
    history: [initialState],
    historyIndex: 0,
    maxHistorySize: 50,

    // Save current state to history
    _saveToHistory: () => {
      const state = get();
      const snapshot = createSnapshot(state.nodes, state.edges, state.workflowName);
      
      set((current) => {
        // Remove any history after current index (when we're in the middle of history)
        const newHistory = current.history.slice(0, current.historyIndex + 1);
        
        // Add new snapshot
        newHistory.push(snapshot);
        
        // Limit history size
        const trimmedHistory = newHistory.slice(-current.maxHistorySize);
        
        return {
          history: trimmedHistory,
          historyIndex: trimmedHistory.length - 1,
        };
      });
    },

    // Undo/Redo
    undo: () => {
      const state = get();
      if (state.historyIndex > 0) {
        const previousSnapshot = state.history[state.historyIndex - 1];
        set({
          nodes: previousSnapshot.nodes,
          edges: previousSnapshot.edges,
          workflowName: previousSnapshot.workflowName,
          historyIndex: state.historyIndex - 1,
        });
      }
    },

    redo: () => {
      const state = get();
      if (state.historyIndex < state.history.length - 1) {
        const nextSnapshot = state.history[state.historyIndex + 1];
        set({
          nodes: nextSnapshot.nodes,
          edges: nextSnapshot.edges,
          workflowName: nextSnapshot.workflowName,
          historyIndex: state.historyIndex + 1,
        });
      }
    },

    canUndo: () => {
      return get().historyIndex > 0;
    },

    canRedo: () => {
      const state = get();
      return state.historyIndex < state.history.length - 1;
    },

    // Actions that modify workflow state
    addNode: (node) => {
      const state = get();
      state._saveToHistory();
      set({
        nodes: [...state.nodes, node],
      });
    },

    removeNode: (nodeId) => {
      const state = get();
      state._saveToHistory();
      set({
        nodes: state.nodes.filter((n) => n.id !== nodeId),
        edges: state.edges.filter(
          (e) => e.source !== nodeId && e.target !== nodeId
        ),
        selectedNodeId: state.selectedNodeId === nodeId ? null : state.selectedNodeId,
      });
    },

    updateNode: (nodeId, data) => {
      const state = get();
      state._saveToHistory();
      set({
        nodes: state.nodes.map((n) =>
          n.id === nodeId ? { 
            ...n, 
            ...data,
            // Force React Flow to detect change by creating new data object reference
            // Deep clone to ensure React Flow detects the change
            data: data.data ? JSON.parse(JSON.stringify({ ...n.data, ...data.data })) : n.data
          } : n
        ),
      });
    },

    updateNodePosition: (nodeId, position) => {
      // Don't save position changes to history (too frequent)
      set((state) => ({
        nodes: state.nodes.map((n) =>
          n.id === nodeId ? { ...n, position } : n
        ),
      }));
    },

    addEdge: (edge) => {
      const state = get();
      state._saveToHistory();
      set({
        edges: [...state.edges, edge],
      });
    },

    removeEdge: (edgeId) => {
      const state = get();
      state._saveToHistory();
      set({
        edges: state.edges.filter((e) => e.id !== edgeId),
      });
    },

    selectNode: (nodeId) =>
      set({
        selectedNodeId: nodeId,
      }),

    setWorkflow: (workflow) => {
      const snapshot = createSnapshot(workflow.nodes, workflow.edges, workflow.name);
      set({
        nodes: workflow.nodes,
        edges: workflow.edges,
        workflowName: workflow.name,
        workflowId: workflow.id || null,
        history: [snapshot],
        historyIndex: 0,
      });
    },

    clearWorkflow: () => {
      const initialState: WorkflowSnapshot = {
        nodes: [],
        edges: [],
        workflowName: 'Untitled Workflow',
      };
      set({
        nodes: [],
        edges: [],
        workflowName: 'Untitled Workflow',
        workflowId: null,
        selectedNodeId: null,
        history: [initialState],
        historyIndex: 0,
      });
    },

    setWorkflowName: (name) => {
      const state = get();
      state._saveToHistory();
      set({
        workflowName: name,
      });
    },

    setWorkflowId: (id) =>
      set({
        workflowId: id,
      }),
  };
});

