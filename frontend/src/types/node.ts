/**
 * Node type definitions
 */

export interface NodeMetadata {
  type: string;
  name: string;
  description: string;
  category: string;
  config_schema: Record<string, any>;
}

export interface NodeSchema {
  type: 'object';
  properties: Record<string, any>;
  required?: string[];
}

export type NodeCategory = 
  | 'input' 
  | 'processing' 
  | 'embedding' 
  | 'storage' 
  | 'retrieval' 
  | 'llm';

export type NodeStatus = 
  | 'idle' 
  | 'running' 
  | 'completed' 
  | 'failed';

