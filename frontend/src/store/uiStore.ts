/**
 * UI state management (Zustand)
 */

import { create } from 'zustand';

interface UIState {
  // Sidebar visibility
  nodePaletteOpen: boolean;
  sidebarTab: 'nodes' | 'models' | 'rag-eval' | 'prompt' | 'optimize'; // Active tab in sidebar (legacy, for backward compat)
  promptPlaygroundInitialPrompt?: string; // Initial prompt to load in playground
  propertiesPanelOpen: boolean;
  executionPanelOpen: boolean;
  executionLogsOpen: boolean;
  chatInterfaceOpen: boolean;
  insightsPanelOpen: boolean; // New: Expanded insights panel

  // Utility modals
  activeUtility: 'rag-eval' | 'prompt' | 'models' | 'optimize' | 'templates' | 'help' | 'settings' | 'dashboard' | 'knowledge-base' | null;

  // Canvas state
  canvasZoom: number;
  canvasPan: { x: number; y: number };

  // Actions
  toggleNodePalette: () => void;
  setSidebarTab: (tab: 'nodes' | 'models' | 'rag-eval' | 'prompt' | 'optimize', initialPrompt?: string) => void;
  setActiveUtility: (utility: 'rag-eval' | 'prompt' | 'models' | 'optimize' | 'templates' | 'help' | 'settings' | 'dashboard' | 'knowledge-base' | null) => void;
  togglePropertiesPanel: () => void;
  toggleExecutionPanel: () => void;
  toggleExecutionLogs: () => void;
  toggleChatInterface: () => void;
  toggleInsightsPanel: () => void;
  setExecutionPanelOpen: (open: boolean) => void;
  setExecutionLogsOpen: (open: boolean) => void;
  setInsightsPanelOpen: (open: boolean) => void;
  setCanvasZoom: (zoom: number) => void;
  setCanvasPan: (pan: { x: number; y: number }) => void;
}

export const useUIStore = create<UIState>((set) => ({
  // Initial state
  nodePaletteOpen: true,
  sidebarTab: 'nodes',
  promptPlaygroundInitialPrompt: undefined,
  propertiesPanelOpen: true,
  executionPanelOpen: false,
  executionLogsOpen: false,
  chatInterfaceOpen: false,
  insightsPanelOpen: false,
  activeUtility: null,
  canvasZoom: 1,
  canvasPan: { x: 0, y: 0 },

  // Actions
  toggleNodePalette: () =>
    set((state) => ({
      nodePaletteOpen: !state.nodePaletteOpen,
    })),

  setSidebarTab: (tab, initialPrompt) =>
    set({
      sidebarTab: tab,
      promptPlaygroundInitialPrompt: initialPrompt,
    }),

  setActiveUtility: (utility) =>
    set({
      activeUtility: utility,
    }),

  togglePropertiesPanel: () =>
    set((state) => ({
      propertiesPanelOpen: !state.propertiesPanelOpen,
    })),

  toggleExecutionPanel: () =>
    set((state) => ({
      executionPanelOpen: !state.executionPanelOpen,
    })),

  toggleExecutionLogs: () =>
    set((state) => ({
      executionLogsOpen: !state.executionLogsOpen,
    })),

  toggleChatInterface: () =>
    set((state) => ({
      chatInterfaceOpen: !state.chatInterfaceOpen,
    })),

  toggleInsightsPanel: () =>
    set((state) => ({
      insightsPanelOpen: !state.insightsPanelOpen,
    })),

  setExecutionPanelOpen: (open) =>
    set({
      executionPanelOpen: open,
    }),

  setExecutionLogsOpen: (open) =>
    set({
      executionLogsOpen: open,
    }),

  setInsightsPanelOpen: (open) =>
    set({
      insightsPanelOpen: open,
    }),

  setCanvasZoom: (zoom) =>
    set({
      canvasZoom: zoom,
    }),

  setCanvasPan: (pan) =>
    set({
      canvasPan: pan,
    }),
}));

