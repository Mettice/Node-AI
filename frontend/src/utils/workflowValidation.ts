/**
 * Workflow validation utilities
 */

import type { Node, Edge } from 'reactflow';

interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export function validateWorkflow(workflow: { nodes: Node[]; edges: Edge[] }): ValidationResult {
  const errors: string[] = [];

  // Check for nodes
  if (workflow.nodes.length === 0) {
    errors.push('Workflow must have at least one node');
  }

  // Check for disconnected nodes (optional - can have standalone nodes)
  // Check for circular dependencies
  const visited = new Set<string>();
  const recStack = new Set<string>();

  function hasCycle(nodeId: string): boolean {
    if (recStack.has(nodeId)) {
      return true;
    }
    if (visited.has(nodeId)) {
      return false;
    }

    visited.add(nodeId);
    recStack.add(nodeId);

    const outgoingEdges = workflow.edges.filter((e) => e.source === nodeId);
    for (const edge of outgoingEdges) {
      if (hasCycle(edge.target)) {
        return true;
      }
    }

    recStack.delete(nodeId);
    return false;
  }

  // Check each node for cycles
  for (const node of workflow.nodes) {
    if (hasCycle(node.id)) {
      errors.push('Workflow contains circular dependencies');
      break;
    }
  }

  // Check for valid connections (source and target exist)
  for (const edge of workflow.edges) {
    const sourceExists = workflow.nodes.some((n) => n.id === edge.source);
    const targetExists = workflow.nodes.some((n) => n.id === edge.target);

    if (!sourceExists) {
      errors.push(`Edge references non-existent source node: ${edge.source}`);
    }
    if (!targetExists) {
      errors.push(`Edge references non-existent target node: ${edge.target}`);
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

