/**
 * Workflow type definitions
 */

export interface Node {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
}

export interface Edge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface Workflow {
  id?: string;
  name: string;
  nodes: Node[];
  edges: Edge[];
  metadata?: Record<string, any>;
}

