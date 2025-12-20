"""
Workflow validation and graph analysis module.

This module handles:
- Workflow structure validation
- Graph analysis (cycles, dependencies)
- Execution order building
"""

from collections import defaultdict, deque
from typing import Dict, List, Set

from backend.core.exceptions import (
    CircularDependencyError,
    WorkflowValidationError,
)
from backend.core.models import Node, Workflow
from backend.core.node_registry import NodeRegistry
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowValidator:
    """Validates workflows and builds execution order."""

    @staticmethod
    def validate_workflow(workflow: Workflow) -> None:
        """
        Validate workflow structure.
        
        Raises:
            WorkflowValidationError: If workflow is invalid
        """
        errors = []

        # Check nodes exist
        if not workflow.nodes:
            errors.append("Workflow must have at least one node")

        # Check node types are registered with helpful error messages
        missing_nodes = []
        for node in workflow.nodes:
            if not NodeRegistry.is_registered(node.type):
                missing_nodes.append(node.type)
        
        if missing_nodes:
            # Provide helpful suggestions for common missing node types
            suggestions = []
            for node_type in missing_nodes:
                if node_type in ['crewai_agent']:
                    suggestions.append(f"'{node_type}' requires CrewAI package: pip install crewai")
                elif node_type in ['knowledge_graph']:
                    suggestions.append(f"'{node_type}' requires Neo4j package: pip install neo4j")
                elif node_type in ['rerank']:
                    suggestions.append(f"'{node_type}' requires additional packages: pip install cohere sentence-transformers")
                else:
                    suggestions.append(f"'{node_type}' may require additional dependencies")
            
            error_msg = f"Node types not available: {', '.join(missing_nodes)}"
            if suggestions:
                error_msg += f". Installation hints: {' | '.join(suggestions)}"
            errors.append(error_msg)

        # Check edges reference valid nodes
        node_ids = {node.id for node in workflow.nodes}
        for edge in workflow.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge source node '{edge.source}' not found")
            if edge.target not in node_ids:
                errors.append(f"Edge target node '{edge.target}' not found")

        # Check for circular dependencies
        if WorkflowValidator.has_circular_dependency(workflow):
            cycle = WorkflowValidator.find_cycle(workflow)
            raise CircularDependencyError(cycle)

        if errors:
            raise WorkflowValidationError(
                "Workflow validation failed",
                errors=errors,
            )

    @staticmethod
    def build_execution_order(workflow: Workflow) -> List[str]:
        """
        Build execution order using topological sort.
        
        Returns:
            List of node IDs in execution order
        """
        # Build dependency graph
        graph: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = defaultdict(int)

        # Initialize all nodes
        for node in workflow.nodes:
            in_degree[node.id] = 0

        # Build graph from edges
        for edge in workflow.edges:
            graph[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        # Topological sort using Kahn's algorithm
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        execution_order = []

        while queue:
            node_id = queue.popleft()
            execution_order.append(node_id)

            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check if all nodes were processed
        if len(execution_order) != len(workflow.nodes):
            # There's a cycle (should have been caught in validation, but double-check)
            raise CircularDependencyError(
                WorkflowValidator.find_cycle(workflow) or ["unknown cycle"]
            )

        return execution_order

    @staticmethod
    def has_circular_dependency(workflow: Workflow) -> bool:
        """Check for circular dependencies using DFS."""
        graph: Dict[str, List[str]] = defaultdict(list)
        for edge in workflow.edges:
            graph[edge.source].append(edge.target)

        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in graph[node_id]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node in workflow.nodes:
            if node.id not in visited:
                if has_cycle(node.id):
                    return True

        return False

    @staticmethod
    def find_cycle(workflow: Workflow) -> List[str]:
        """Find a cycle in the workflow graph."""
        graph: Dict[str, List[str]] = defaultdict(list)
        for edge in workflow.edges:
            graph[edge.source].append(edge.target)

        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def find_cycle_dfs(node_id: str) -> List[str] | None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for neighbor in graph[node_id]:
                if neighbor not in visited:
                    result = find_cycle_dfs(neighbor)
                    if result:
                        return result
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            path.pop()
            rec_stack.remove(node_id)
            return None

        for node in workflow.nodes:
            if node.id not in visited:
                cycle = find_cycle_dfs(node.id)
                if cycle:
                    return cycle

        return []

    @staticmethod
    def get_node_by_id(workflow: Workflow, node_id: str) -> Node:
        """Get node by ID."""
        for node in workflow.nodes:
            if node.id == node_id:
                return node
        raise ValueError(f"Node {node_id} not found in workflow")

