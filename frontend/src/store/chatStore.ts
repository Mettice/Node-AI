/**
 * Chat store - manages conversation state and message history
 */

import { create } from 'zustand';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  cost?: number;
  sources?: Array<{
    text: string;
    score: number;
    metadata?: Record<string, any>;
  }>;
}

interface ChatState {
  messages: ChatMessage[];
  isProcessing: boolean;
  currentQuery: string;
  vectorStoreReady: boolean;
  memoryEnabled: boolean;
  sessionId: string;
  
  // Actions
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  clearMessages: () => void;
  setProcessing: (processing: boolean) => void;
  setCurrentQuery: (query: string) => void;
  setVectorStoreReady: (ready: boolean) => void;
  setMemoryEnabled: (enabled: boolean) => void;
  setSessionId: (id: string) => void;
  updateLastMessage: (updates: Partial<ChatMessage>) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isProcessing: false,
  currentQuery: '',
  vectorStoreReady: false,
  memoryEnabled: false,
  sessionId: `session-${Date.now()}`,
  
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: `${message.role}-${Date.now()}`,
          timestamp: new Date().toISOString(),
        },
      ],
    })),
  
  clearMessages: () => set({ 
    messages: [], 
    vectorStoreReady: false,
    sessionId: `session-${Date.now()}`, // New session when clearing
  }),
  
  setProcessing: (processing) => set({ isProcessing: processing }),
  
  setCurrentQuery: (query) => set({ currentQuery: query }),
  
  setVectorStoreReady: (ready) => set({ vectorStoreReady: ready }),
  
  setMemoryEnabled: (enabled) => set({ memoryEnabled: enabled }),
  
  setSessionId: (id) => set({ sessionId: id }),
  
  updateLastMessage: (updates) =>
    set((state) => {
      const messages = [...state.messages];
      const lastIndex = messages.length - 1;
      if (lastIndex >= 0) {
        messages[lastIndex] = { ...messages[lastIndex], ...updates };
      }
      return { messages };
    }),
}));

