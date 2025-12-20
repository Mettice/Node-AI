/**
 * Application constants
 */

export const APP_NAME = 'NodeAI';
export const APP_VERSION = '0.1.0';

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_PREFIX = '/api/v1';

// Node Category Colors - "Living Intelligence" Design System
export const NODE_CATEGORY_COLORS = {
  input: '#22d3ee',       // Cool Cyan - Data entry points
  processing: '#fb923c',  // Orange - Transformation/chunking  
  embedding: '#a78bfa',   // Purple - Vector operations
  storage: '#34d399',     // Emerald - Database/persistence
  retrieval: '#60a5fa',   // Blue - Search/fetch operations
  llm: '#f0b429',         // Warm Amber - AI/Language models (signature color)
  agent: '#f472b6',       // Pink - Multi-agent systems
  memory: '#a78bfa',      // Purple - Memory operations
  tool: '#fb923c',        // Orange - Processing tools
  training: '#a78bfa',    // Purple - Training/fine-tuning
  data: '#34d399',        // Emerald - Data nodes
  // AI-Native Intelligence Categories
  intelligence: '#f59e0b', // Amber - AI Intelligence & Analytics
  business: '#10b981',     // Emerald - Business Intelligence & Insights
  content: '#ec4899',      // Pink - Content Creation & Marketing
  developer: '#6366f1',    // Indigo - Developer Tools & Automation
  sales: '#ef4444',        // Red - Sales & CRM Tools
  communication: '#8b5cf6', // Violet - Communication & Notifications
} as const;

// Node Category Icons (Lucide React icon names)
export const NODE_CATEGORY_ICONS = {
  input: 'FileText',
  processing: 'Scissors',
  embedding: 'Brain',
  storage: 'Database',
  retrieval: 'Search',
  llm: 'MessageSquare',
  agent: 'Bot',
  memory: 'BrainCircuit',
  tool: 'Wrench',
  training: 'GraduationCap',
  data: 'FileSpreadsheet',
  // AI-Native Intelligence Categories
  intelligence: 'Lightbulb',      // Intelligence & Analytics
  business: 'TrendingUp',         // Business Intelligence
  content: 'PenTool',             // Content Creation
  developer: 'Code',              // Developer Tools
  sales: 'Target',                // Sales & CRM
  communication: 'MessageCircle', // Communication
} as const;

