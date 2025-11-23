"""
Pre-built Graph Query Tools for Knowledge Graph Node.

These tools provide common Cypher query patterns for relationship-based queries
in Hybrid RAG systems. The LLM can call these tools instead of generating
Cypher queries directly (which is more reliable).
"""

from typing import Any, Dict, List, Optional

logger = None
try:
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
except:
    import logging
    logger = logging.getLogger(__name__)


class GraphQueryTools:
    """
    Pre-built Cypher query tools for common graph patterns.
    
    These tools encapsulate reliable Cypher queries that the LLM can call
    via tool-calling, rather than generating Cypher directly.
    """
    
    @staticmethod
    def find_related_entities(
        entity_id: int,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Find all entities related to a given entity.
        
        Example: "Find all papers by this author"
        
        Args:
            entity_id: ID of the entity to find relations for
            relationship_types: Filter by relationship types (None = all)
            max_depth: Maximum depth to traverse (1 = direct, 2 = 2 hops, etc.)
            limit: Maximum number of results
        
        Returns:
            Dictionary with Cypher query and parameters
        """
        if max_depth == 1:
            if relationship_types:
                rel_filter = "|".join(relationship_types)
                query = (
                    f"MATCH (a)-[r:{rel_filter}]->(b) "
                    "WHERE id(a) = $entity_id "
                    "RETURN b, type(r) as relationship_type, r, id(b) as entity_id "
                    f"LIMIT {limit}"
                )
            else:
                query = (
                    "MATCH (a)-[r]->(b) "
                    "WHERE id(a) = $entity_id "
                    "RETURN b, type(r) as relationship_type, r, id(b) as entity_id "
                    f"LIMIT {limit}"
                )
        else:
            # Multi-hop traversal
            if relationship_types:
                rel_filter = "|".join(relationship_types)
                query = (
                    f"MATCH path = (a)-[r:{rel_filter}*1..{max_depth}]->(b) "
                    "WHERE id(a) = $entity_id "
                    "RETURN b, relationships(path) as relationships, length(path) as depth, id(b) as entity_id "
                    f"LIMIT {limit}"
                )
            else:
                query = (
                    f"MATCH path = (a)-[r*1..{max_depth}]->(b) "
                    "WHERE id(a) = $entity_id "
                    "RETURN b, relationships(path) as relationships, length(path) as depth, id(b) as entity_id "
                    f"LIMIT {limit}"
                )
        
        return {
            "cypher_query": query,
            "parameters": {"entity_id": entity_id},
            "description": f"Find entities related to entity {entity_id}",
        }
    
    @staticmethod
    def find_paths(
        from_entity_id: int,
        to_entity_id: int,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 3,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Find paths between two entities.
        
        Example: "How is author A connected to author B?"
        
        Args:
            from_entity_id: Source entity ID
            to_entity_id: Target entity ID
            relationship_types: Filter by relationship types (None = all)
            max_depth: Maximum path length
            limit: Maximum number of paths
        
        Returns:
            Dictionary with Cypher query and parameters
        """
        if relationship_types:
            rel_filter = "|".join(relationship_types)
            query = (
                f"MATCH path = shortestPath((a)-[r:{rel_filter}*1..{max_depth}]->(b)) "
                "WHERE id(a) = $from_id AND id(b) = $to_id "
                "RETURN path, relationships(path) as relationships, length(path) as path_length "
                f"LIMIT {limit}"
            )
        else:
            query = (
                f"MATCH path = shortestPath((a)-[r*1..{max_depth}]->(b)) "
                "WHERE id(a) = $from_id AND id(b) = $to_id "
                "RETURN path, relationships(path) as relationships, length(path) as path_length "
                f"LIMIT {limit}"
            )
        
        return {
            "cypher_query": query,
            "parameters": {"from_id": from_entity_id, "to_id": to_entity_id},
            "description": f"Find paths from entity {from_entity_id} to entity {to_entity_id}",
        }
    
    @staticmethod
    def find_communities(
        node_label: str,
        relationship_type: str,
        min_community_size: int = 3,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Find communities/clusters in the graph.
        
        Example: "Find research groups" or "Find author collaboration networks"
        
        Uses a simple community detection algorithm (connected components).
        
        Args:
            node_label: Label of nodes to analyze (e.g., 'Author', 'Paper')
            relationship_type: Type of relationship to use (e.g., 'COLLABORATES_WITH')
            min_community_size: Minimum size of community to return
            limit: Maximum number of communities
        
        Returns:
            Dictionary with Cypher query and parameters
        """
        query = (
            f"MATCH (a:{node_label})-[r:{relationship_type}]-(b:{node_label}) "
            f"WITH a, collect(DISTINCT b) as neighbors "
            f"WHERE size(neighbors) >= {min_community_size - 1} "
            f"RETURN a, neighbors, size(neighbors) as community_size "
            f"ORDER BY community_size DESC "
            f"LIMIT {limit}"
        )
        
        return {
            "cypher_query": query,
            "parameters": {},
            "description": f"Find communities of {node_label} nodes connected by {relationship_type}",
        }
    
    @staticmethod
    def find_influencers(
        node_label: str,
        relationship_type: str,
        metric: str = "degree",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Find highly connected nodes (influencers).
        
        Example: "Find most cited authors" or "Find most connected papers"
        
        Args:
            node_label: Label of nodes to analyze
            relationship_type: Type of relationship to count
            metric: Ranking metric ('degree', 'in_degree', 'out_degree')
            limit: Maximum number of results
        
        Returns:
            Dictionary with Cypher query and parameters
        """
        if metric == "in_degree":
            # Count incoming relationships
            query = (
                f"MATCH (a:{node_label})<-[r:{relationship_type}]-(b) "
                f"WITH a, count(r) as in_degree "
                f"RETURN a, in_degree "
                f"ORDER BY in_degree DESC "
                f"LIMIT {limit}"
            )
        elif metric == "out_degree":
            # Count outgoing relationships
            query = (
                f"MATCH (a:{node_label})-[r:{relationship_type}]->(b) "
                f"WITH a, count(r) as out_degree "
                f"RETURN a, out_degree "
                f"ORDER BY out_degree DESC "
                f"LIMIT {limit}"
            )
        else:  # degree (total)
            # Count all relationships
            query = (
                f"MATCH (a:{node_label})-[r:{relationship_type}]-(b) "
                f"WITH a, count(r) as degree "
                f"RETURN a, degree "
                f"ORDER BY degree DESC "
                f"LIMIT {limit}"
            )
        
        return {
            "cypher_query": query,
            "parameters": {},
            "description": f"Find {node_label} nodes with highest {metric} for {relationship_type}",
        }
    
    @staticmethod
    def find_similar_entities(
        entity_id: int,
        node_label: str,
        relationship_type: str,
        similarity_metric: str = "jaccard",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Find entities with similar relationship patterns.
        
        Example: "Find authors with similar citation patterns"
        
        Uses Jaccard similarity on relationship sets.
        
        Args:
            entity_id: ID of the entity to find similar entities for
            node_label: Label of nodes to compare
            relationship_type: Type of relationship to use for similarity
            similarity_metric: Similarity metric ('jaccard')
            limit: Maximum number of results
        
        Returns:
            Dictionary with Cypher query and parameters
        """
        # Jaccard similarity: |A ∩ B| / |A ∪ B|
        # This query finds entities that share many common relationships
        query = (
            f"MATCH (a:{node_label})-[r1:{relationship_type}]->(common)<-[r2:{relationship_type}]-(b:{node_label}) "
            "WHERE id(a) = $entity_id AND id(a) <> id(b) "
            f"WITH a, b, count(DISTINCT common) as common_count "
            f"MATCH (a)-[r3:{relationship_type}]->(all_a) "
            f"WITH a, b, common_count, count(DISTINCT all_a) as a_total "
            f"MATCH (b)-[r4:{relationship_type}]->(all_b) "
            f"WITH a, b, common_count, a_total, count(DISTINCT all_b) as b_total "
            f"WITH a, b, common_count, a_total, b_total, "
            f"     toFloat(common_count) / (a_total + b_total - common_count) as jaccard_similarity "
            f"RETURN b, jaccard_similarity, common_count, a_total, b_total "
            f"ORDER BY jaccard_similarity DESC "
            f"LIMIT {limit}"
        )
        
        return {
            "cypher_query": query,
            "parameters": {"entity_id": entity_id},
            "description": f"Find {node_label} entities similar to entity {entity_id} based on {relationship_type}",
        }
    
    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        """
        Get all available graph query tools as LangChain tool definitions.
        
        Returns:
            List of tool definitions for LLM tool-calling
        """
        return [
            {
                "name": "find_related_entities",
                "description": "Find all entities related to a given entity. Use for queries like 'find all papers by this author' or 'find all collaborators'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "integer", "description": "ID of the entity"},
                        "relationship_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by relationship types (optional)",
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "Maximum depth to traverse (1 = direct, 2 = 2 hops)",
                            "default": 1,
                        },
                        "limit": {"type": "integer", "description": "Maximum number of results", "default": 10},
                    },
                    "required": ["entity_id"],
                },
            },
            {
                "name": "find_paths",
                "description": "Find paths between two entities. Use for queries like 'how is A connected to B' or 'find connection between X and Y'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_entity_id": {"type": "integer", "description": "Source entity ID"},
                        "to_entity_id": {"type": "integer", "description": "Target entity ID"},
                        "relationship_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by relationship types (optional)",
                        },
                        "max_depth": {"type": "integer", "description": "Maximum path length", "default": 3},
                        "limit": {"type": "integer", "description": "Maximum number of paths", "default": 5},
                    },
                    "required": ["from_entity_id", "to_entity_id"],
                },
            },
            {
                "name": "find_communities",
                "description": "Find communities/clusters in the graph. Use for queries like 'find research groups' or 'find collaboration networks'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "node_label": {"type": "string", "description": "Label of nodes to analyze (e.g., 'Author', 'Paper')"},
                        "relationship_type": {"type": "string", "description": "Type of relationship (e.g., 'COLLABORATES_WITH')"},
                        "min_community_size": {"type": "integer", "description": "Minimum community size", "default": 3},
                        "limit": {"type": "integer", "description": "Maximum number of communities", "default": 10},
                    },
                    "required": ["node_label", "relationship_type"],
                },
            },
            {
                "name": "find_influencers",
                "description": "Find highly connected nodes (influencers). Use for queries like 'find most cited authors' or 'find most connected papers'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "node_label": {"type": "string", "description": "Label of nodes to analyze"},
                        "relationship_type": {"type": "string", "description": "Type of relationship to count"},
                        "metric": {
                            "type": "string",
                            "enum": ["degree", "in_degree", "out_degree"],
                            "description": "Ranking metric",
                            "default": "degree",
                        },
                        "limit": {"type": "integer", "description": "Maximum number of results", "default": 10},
                    },
                    "required": ["node_label", "relationship_type"],
                },
            },
            {
                "name": "find_similar_entities",
                "description": "Find entities with similar relationship patterns. Use for queries like 'find authors with similar citation patterns'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "integer", "description": "ID of the entity to find similar entities for"},
                        "node_label": {"type": "string", "description": "Label of nodes to compare"},
                        "relationship_type": {"type": "string", "description": "Type of relationship to use for similarity"},
                        "similarity_metric": {"type": "string", "description": "Similarity metric", "default": "jaccard"},
                        "limit": {"type": "integer", "description": "Maximum number of results", "default": 10},
                    },
                    "required": ["entity_id", "node_label", "relationship_type"],
                },
            },
        ]

