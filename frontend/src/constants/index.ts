/**
 * Application constants
 */

export const APP_NAME = 'NodeAI';
export const APP_VERSION = '0.1.0';

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_PREFIX = '/api/v1';

// Node Category Colors (Muted, enterprise-friendly)
export const NODE_CATEGORY_COLORS = {
  input: '#7c3aed',      // Deep purple (was #a78bfa - more muted)
  processing: '#d97706',  // Deep amber (was #fb923c - less orange)
  embedding: '#0891b2',   // Deep cyan (was #22d3ee - darker)
  storage: '#059669',     // Deep emerald (was #34d399 - darker)
  retrieval: '#2563eb',   // Deep blue (was #60a5fa - darker)
  llm: '#db2777',         // Deep pink (was #f472b6 - darker)
  memory: '#7c3aed',      // Deep purple (for memory)
  agent: '#d97706',       // Deep amber (for agents)
  tool: '#059669',        // Deep emerald (for tools)
  training: '#7c3aed',    // Deep purple (for training/fine-tuning)
  data: '#059669',        // Deep emerald (for data nodes like product catalog, user profile)
} as const;

// Node Category Icons (Lucide React icon names)
export const NODE_CATEGORY_ICONS = {
  input: 'FileText',
  processing: 'Scissors',
  embedding: 'Brain',
  storage: 'Database',
  retrieval: 'Search',
  llm: 'MessageSquare',
} as const;

