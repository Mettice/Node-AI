"""
Knowledge Graph Node for NodeAI.

This node provides Neo4j knowledge graph integration for storing and querying
structured relationships. Part of the Hybrid RAG system that combines vector
search (semantic similarity) with knowledge graphs (structured relationships).
"""

from typing import Any, Dict, List, Optional
import json

from backend.config import settings
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeGraphNode(BaseNode):
    """
    Knowledge Graph Node for Neo4j integration.
    
    Supports creating nodes, relationships, and executing Cypher queries
    for relationship-based retrieval in Hybrid RAG systems.
    """

    node_type = "knowledge_graph"
    name = "Knowledge Graph"
    description = "Store and query structured relationships using Neo4j knowledge graph"
    category = "storage"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the knowledge graph node.
        
        Supports multiple operations:
        - create_node: Create a node with labels and properties
        - create_relationship: Create relationship between nodes
        - query: Execute custom Cypher query
        - import: Import graph from JSON
        - export: Export graph to JSON
        """
        node_id = config.get("_node_id", "knowledge_graph")
        operation = config.get("operation", "query")
        
        await self.stream_progress(node_id, 0.1, f"Executing {operation} operation...")
        
        # Validate operation
        valid_operations = ["create_node", "create_relationship", "query", "import", "export"]
        if operation not in valid_operations:
            raise ValueError(
                f"Invalid operation: '{operation}'. "
                f"Valid operations are: {', '.join(valid_operations)}"
            )
        
        # Get Neo4j connection details
        uri = config.get("neo4j_uri") or settings.neo4j_uri
        user = config.get("neo4j_user") or settings.neo4j_user
        password = config.get("neo4j_password") or settings.neo4j_password
        
        # Validate connection configuration
        if not uri:
            raise ValueError(
                "Neo4j connection not configured. "
                "Please provide one of the following:\n"
                "1. Set NEO4J_URI environment variable (and optionally NEO4J_USER, NEO4J_PASSWORD)\n"
                "2. Configure neo4j_uri in the node settings\n"
                "Example: bolt://localhost:7687"
            )
        
        # Validate URI format
        if not uri.startswith(("bolt://", "neo4j://", "bolt+s://", "neo4j+s://")):
            raise ValueError(
                f"Invalid Neo4j URI format: '{uri}'. "
                "URI should start with bolt://, neo4j://, bolt+s://, or neo4j+s://\n"
                "Example: bolt://localhost:7687"
            )
        
        try:
            from neo4j import GraphDatabase
        except ImportError:
            raise ValueError(
                "Neo4j Python driver is not installed.\n"
                "Install it with: pip install neo4j\n"
                "Or add 'neo4j' to your requirements.txt"
            )
        
        # Create driver and validate connection
        driver = None
        try:
            await self.stream_progress(node_id, 0.2, "Connecting to Neo4j...")
            driver = GraphDatabase.driver(uri, auth=(user, password) if user and password else None)
            
            # Test connection
            try:
                driver.verify_connectivity()
                await self.stream_progress(node_id, 0.3, "Connected to Neo4j successfully")
            except Exception as e:
                error_msg = str(e)
                if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                    raise ValueError(
                        f"Neo4j authentication failed for URI: {uri}\n"
                        "Please check your username and password.\n"
                        "If using default Neo4j installation, default credentials are: neo4j/neo4j"
                    )
                elif "connection" in error_msg.lower() or "refused" in error_msg.lower():
                    raise ValueError(
                        f"Cannot connect to Neo4j at {uri}\n"
                        "Please ensure:\n"
                        "1. Neo4j is running (check with: docker ps or neo4j status)\n"
                        "2. The URI is correct (default: bolt://localhost:7687)\n"
                        "3. Firewall/network allows the connection"
                    )
                else:
                    raise ValueError(
                        f"Failed to connect to Neo4j: {error_msg}\n"
                        f"URI: {uri}\n"
                        "Please verify your Neo4j connection settings."
                    )
            
            # Route to appropriate operation
            if operation == "create_node":
                result = await self._create_node(driver, inputs, config, node_id)
            elif operation == "create_relationship":
                result = await self._create_relationship(driver, inputs, config, node_id)
            elif operation == "query":
                result = await self._execute_query(driver, inputs, config, node_id)
            elif operation == "import":
                result = await self._import_graph(driver, inputs, config, node_id)
            elif operation == "export":
                result = await self._export_graph(driver, inputs, config, node_id)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            return result
        except ValueError:
            # Re-raise ValueError as-is (these are user-friendly errors)
            raise
        except Exception as e:
            # Wrap unexpected errors with helpful context
            error_type = type(e).__name__
            error_msg = str(e)
            raise ValueError(
                f"Knowledge Graph operation '{operation}' failed: {error_msg}\n"
                f"Error type: {error_type}\n"
                "Please check:\n"
                "1. Your Neo4j connection is working\n"
                "2. Your query/parameters are valid\n"
                "3. You have necessary permissions"
            ) from e
        finally:
            if driver:
                try:
                    driver.close()
                except Exception as e:
                    logger.warning(f"Error closing Neo4j driver: {e}")

    async def _create_node(
        self,
        driver,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Create a node in the graph."""
        labels = config.get("node_labels", [])
        properties = config.get("properties", {})
        
        # Allow properties from inputs to override config
        if "properties" in inputs:
            properties = {**properties, **inputs["properties"]}
        
        # Validate labels
        if labels and not isinstance(labels, list):
            raise ValueError(
                f"node_labels must be a list, got {type(labels).__name__}\n"
                "Example: ['Author', 'Person']"
            )
        
        # Validate properties
        if properties and not isinstance(properties, dict):
            raise ValueError(
                f"properties must be a dictionary, got {type(properties).__name__}\n"
                "Example: {'name': 'John', 'age': 30}"
            )
        
        await self.stream_progress(node_id, 0.3, f"Creating node with labels: {labels}")
        
        def create_node_tx(tx):
            labels_str = ":".join(labels) if labels else ""
            query = f"CREATE (n{':' + labels_str if labels_str else ''} $properties) RETURN id(n) as node_id, n"
            result = tx.run(query, properties=properties)
            record = result.single()
            return {
                "node_id": record["node_id"],
                "properties": dict(record["n"]),
            }
        
        with driver.session() as session:
            result = session.execute_write(create_node_tx)
        
        await self.stream_progress(node_id, 1.0, f"Node created: {result['node_id']}")
        await self.stream_output(node_id, result, partial=False)
        
        return {
            "operation": "create_node",
            "node_id": result["node_id"],
            "properties": result["properties"],
            "labels": labels,
        }

    async def _create_relationship(
        self,
        driver,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Create a relationship between two nodes."""
        from_node_id = config.get("from_node_id") or inputs.get("from_node_id")
        to_node_id = config.get("to_node_id") or inputs.get("to_node_id")
        relationship_type = config.get("relationship_type", "RELATES_TO")
        properties = config.get("properties", {})
        
        # Validate required fields
        if from_node_id is None:
            raise ValueError(
                "from_node_id is required for creating relationships.\n"
                "Provide the source node ID (integer)."
            )
        if to_node_id is None:
            raise ValueError(
                "to_node_id is required for creating relationships.\n"
                "Provide the target node ID (integer)."
            )
        
        # Validate node IDs are integers
        try:
            from_node_id = int(from_node_id)
            to_node_id = int(to_node_id)
        except (ValueError, TypeError):
            raise ValueError(
                f"Node IDs must be integers. Got from_node_id={from_node_id}, to_node_id={to_node_id}\n"
                "Node IDs are returned when you create nodes."
            )
        
        # Validate relationship type
        if not relationship_type or not isinstance(relationship_type, str):
            raise ValueError(
                f"relationship_type must be a non-empty string. Got: {relationship_type}\n"
                "Example: 'CITES', 'COLLABORATES_WITH', 'AUTHORED'"
            )
        
        # Validate properties
        if properties and not isinstance(properties, dict):
            raise ValueError(
                f"properties must be a dictionary. Got: {type(properties).__name__}"
            )
        
        await self.stream_progress(
            node_id, 0.3, f"Creating relationship: {from_node_id} -[{relationship_type}]-> {to_node_id}"
        )
        
        def create_relationship_tx(tx):
            # First check if both nodes exist
            check_query = (
                "MATCH (a), (b) "
                "WHERE id(a) = $from_id AND id(b) = $to_id "
                "RETURN count(a) as from_count, count(b) as to_count"
            )
            check_result = tx.run(check_query, from_id=from_node_id, to_id=to_node_id)
            check_record = check_result.single()
            
            if check_record["from_count"] == 0:
                raise ValueError(f"Source node with ID {from_node_id} does not exist")
            if check_record["to_count"] == 0:
                raise ValueError(f"Target node with ID {to_node_id} does not exist")
            
            # Create relationship
            query = (
                "MATCH (a), (b) "
                "WHERE id(a) = $from_id AND id(b) = $to_id "
                f"CREATE (a)-[r:{relationship_type} $properties]->(b) "
                "RETURN id(r) as rel_id, r"
            )
            result = tx.run(
                query,
                from_id=from_node_id,
                to_id=to_node_id,
                properties=properties,
            )
            record = result.single()
            if not record:
                raise ValueError("Failed to create relationship - no record returned")
            return {
                "relationship_id": record["rel_id"],
                "type": relationship_type,
                "properties": dict(record["r"]),
            }
        
        with driver.session() as session:
            try:
                result = session.execute_write(create_relationship_tx)
            except ValueError:
                # Re-raise validation errors as-is
                raise
            except Exception as e:
                error_msg = str(e)
                if "does not exist" in error_msg:
                    raise ValueError(error_msg)
                elif "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    raise ValueError(
                        f"Relationship already exists between nodes {from_node_id} and {to_node_id}\n"
                        f"Type: {relationship_type}"
                    )
                else:
                    raise ValueError(
                        f"Failed to create relationship: {error_msg}\n"
                        f"From node ID: {from_node_id}, To node ID: {to_node_id}, Type: {relationship_type}"
                    )
        
        await self.stream_progress(node_id, 1.0, f"Relationship created: {result['relationship_id']}")
        await self.stream_output(node_id, result, partial=False)
        
        return {
            "operation": "create_relationship",
            "relationship_id": result["relationship_id"],
            "type": relationship_type,
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "properties": result["properties"],
        }

    async def _execute_query(
        self,
        driver,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Execute a custom Cypher query."""
        query = config.get("cypher_query") or inputs.get("cypher_query")
        parameters = config.get("query_parameters", {}) or inputs.get("query_parameters", {})
        
        # Validate query
        if not query:
            raise ValueError(
                "Cypher query is required for query operation.\n"
                "Provide a valid Cypher query string.\n"
                "Example: MATCH (n) RETURN n LIMIT 10"
            )
        
        if not isinstance(query, str):
            raise ValueError(
                f"cypher_query must be a string. Got: {type(query).__name__}"
            )
        
        # Validate parameters
        if parameters and not isinstance(parameters, dict):
            raise ValueError(
                f"query_parameters must be a dictionary. Got: {type(parameters).__name__}\n"
                "Example: {'name': 'John', 'limit': 10}"
            )
        
        # Basic Cypher syntax validation (check for common issues)
        query_upper = query.upper().strip()
        if not any(query_upper.startswith(cmd) for cmd in ["MATCH", "CREATE", "MERGE", "DELETE", "SET", "RETURN", "WITH", "UNWIND", "CALL"]):
            logger.warning(
                f"Cypher query doesn't start with a common keyword. "
                f"This might be invalid. Query: {query[:100]}..."
            )
        
        await self.stream_progress(node_id, 0.3, "Executing Cypher query...")
        
        def execute_query_tx(tx):
            result = tx.run(query, **parameters)
            records = []
            for record in result:
                # Convert Neo4j types to Python types
                record_dict = {}
                for key in record.keys():
                    value = record[key]
                    # Handle Neo4j Node and Relationship objects
                    if hasattr(value, "__class__") and value.__class__.__name__ in ["Node", "Relationship"]:
                        record_dict[key] = {
                            "id": value.id,
                            "labels" if hasattr(value, "labels") else "type": (
                                list(value.labels) if hasattr(value, "labels") else value.type
                            ),
                            "properties": dict(value),
                        }
                    else:
                        record_dict[key] = value
                records.append(record_dict)
            return records
        
        with driver.session() as session:
            results = session.execute_read(execute_query_tx)
        
        await self.stream_progress(node_id, 1.0, f"Query executed: {len(results)} results")
        await self.stream_output(node_id, {"results": results, "count": len(results)}, partial=False)
        
        return {
            "operation": "query",
            "results": results,
            "count": len(results),
        }

    async def _import_graph(
        self,
        driver,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Import graph data from JSON."""
        graph_data = config.get("graph_data") or inputs.get("graph_data")
        
        if not graph_data:
            raise ValueError("Graph data is required for import")
        
        if isinstance(graph_data, str):
            graph_data = json.loads(graph_data)
        
        await self.stream_progress(node_id, 0.2, "Importing graph data...")
        
        nodes_created = 0
        relationships_created = 0
        
        def import_graph_tx(tx):
            nonlocal nodes_created, relationships_created
            
            # Import nodes
            nodes = graph_data.get("nodes", [])
            node_id_map = {}  # Map external IDs to Neo4j node IDs
            
            for node in nodes:
                labels = node.get("labels", [])
                properties = node.get("properties", {})
                external_id = node.get("id")
                
                labels_str = ":".join(labels) if labels else ""
                query = f"CREATE (n{':' + labels_str if labels_str else ''} $properties) RETURN id(n) as node_id"
                result = tx.run(query, properties=properties)
                neo4j_id = result.single()["node_id"]
                
                if external_id:
                    node_id_map[external_id] = neo4j_id
                nodes_created += 1
            
            # Import relationships
            relationships = graph_data.get("relationships", [])
            for rel in relationships:
                from_id = rel.get("from")
                to_id = rel.get("to")
                rel_type = rel.get("type", "RELATES_TO")
                properties = rel.get("properties", {})
                
                # Use mapped IDs if available
                from_neo4j_id = node_id_map.get(from_id, from_id)
                to_neo4j_id = node_id_map.get(to_id, to_id)
                
                query = (
                    "MATCH (a), (b) "
                    "WHERE id(a) = $from_id AND id(b) = $to_id "
                    f"CREATE (a)-[r:{rel_type} $properties]->(b)"
                )
                tx.run(query, from_id=from_neo4j_id, to_id=to_neo4j_id, properties=properties)
                relationships_created += 1
            
            return {"nodes": nodes_created, "relationships": relationships_created}
        
        with driver.session() as session:
            try:
                result = session.execute_write(import_graph_tx)
            except Exception as e:
                error_msg = str(e)
                raise ValueError(
                    f"Failed to import graph data: {error_msg}\n"
                    f"Nodes to import: {len(nodes)}, Relationships to import: {len(relationships)}\n"
                    "Please check:\n"
                    "1. Node/relationship data format is correct\n"
                    "2. Labels and relationship types are valid\n"
                    "3. Properties are valid Neo4j types"
                )
        
        await self.stream_progress(
            node_id, 1.0, f"Import complete: {result['nodes']} nodes, {result['relationships']} relationships"
        )
        await self.stream_output(node_id, result, partial=False)
        
        return {
            "operation": "import",
            "nodes_created": result["nodes"],
            "relationships_created": result["relationships"],
        }

    async def _export_graph(
        self,
        driver,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Export graph data to JSON."""
        node_labels = config.get("export_node_labels", [])
        relationship_types = config.get("export_relationship_types", [])
        
        await self.stream_progress(node_id, 0.3, "Exporting graph data...")
        
        def export_graph_tx(tx):
            # Build node query
            if node_labels:
                labels_filter = ":".join(node_labels)
                node_query = f"MATCH (n:{labels_filter}) RETURN n"
            else:
                node_query = "MATCH (n) RETURN n"
            
            # Build relationship query
            if relationship_types:
                rel_filter = "|".join(relationship_types)
                rel_query = f"MATCH (a)-[r:{rel_filter}]->(b) RETURN a, r, b"
            else:
                rel_query = "MATCH (a)-[r]->(b) RETURN a, r, b"
            
            # Export nodes
            nodes = []
            node_result = tx.run(node_query)
            for record in node_result:
                node = record["n"]
                nodes.append({
                    "id": node.id,
                    "labels": list(node.labels),
                    "properties": dict(node),
                })
            
            # Export relationships
            relationships = []
            rel_result = tx.run(rel_query)
            for record in rel_result:
                a = record["a"]
                r = record["r"]
                b = record["b"]
                relationships.append({
                    "from": a.id,
                    "to": b.id,
                    "type": r.type,
                    "properties": dict(r),
                })
            
            return {"nodes": nodes, "relationships": relationships}
        
        with driver.session() as session:
            result = session.execute_read(export_graph_tx)
        
        await self.stream_progress(
            node_id, 1.0, f"Export complete: {len(result['nodes'])} nodes, {len(result['relationships'])} relationships"
        )
        
        graph_json = json.dumps(result, indent=2)
        await self.stream_output(node_id, result, partial=False)
        
        return {
            "operation": "export",
            "nodes": result["nodes"],
            "relationships": result["relationships"],
            "json": graph_json,
            "node_count": len(result["nodes"]),
            "relationship_count": len(result["relationships"]),
        }

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for knowledge graph configuration."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "title": "Operation",
                    "description": "Operation to perform",
                    "enum": ["create_node", "create_relationship", "query", "import", "export"],
                    "default": "query",
                },
                "neo4j_uri": {
                    "type": "string",
                    "title": "Neo4j URI",
                    "description": "Neo4j database URI (e.g., bolt://localhost:7687). Leave empty to use environment variable.",
                    "default": "",
                },
                "neo4j_user": {
                    "type": "string",
                    "title": "Neo4j Username",
                    "description": "Neo4j database username. Leave empty to use environment variable.",
                    "default": "",
                },
                "neo4j_password": {
                    "type": "string",
                    "title": "Neo4j Password",
                    "description": "Neo4j database password. Leave empty to use environment variable.",
                    "default": "",
                },
                "node_labels": {
                    "type": "array",
                    "title": "Node Labels",
                    "description": "Labels for the node (e.g., ['Author', 'Person'])",
                    "items": {"type": "string"},
                    "default": [],
                },
                "properties": {
                    "type": "object",
                    "title": "Properties",
                    "description": "Properties for the node or relationship",
                    "default": {},
                },
                "from_node_id": {
                    "type": "integer",
                    "title": "From Node ID",
                    "description": "Source node ID for relationship creation",
                },
                "to_node_id": {
                    "type": "integer",
                    "title": "To Node ID",
                    "description": "Target node ID for relationship creation",
                },
                "relationship_type": {
                    "type": "string",
                    "title": "Relationship Type",
                    "description": "Type of relationship (e.g., 'CITES', 'COLLABORATES_WITH')",
                    "default": "RELATES_TO",
                },
                "cypher_query": {
                    "type": "string",
                    "title": "Cypher Query",
                    "description": "Custom Cypher query to execute",
                    "default": "MATCH (n) RETURN n LIMIT 10",
                },
                "query_parameters": {
                    "type": "object",
                    "title": "Query Parameters",
                    "description": "Parameters for the Cypher query",
                    "default": {},
                },
                "graph_data": {
                    "type": "string",
                    "title": "Graph Data (JSON)",
                    "description": "JSON string containing nodes and relationships to import",
                },
                "export_node_labels": {
                    "type": "array",
                    "title": "Export Node Labels Filter",
                    "description": "Only export nodes with these labels (empty = all)",
                    "items": {"type": "string"},
                    "default": [],
                },
                "export_relationship_types": {
                    "type": "array",
                    "title": "Export Relationship Types Filter",
                    "description": "Only export relationships of these types (empty = all)",
                    "items": {"type": "string"},
                    "default": [],
                },
            },
            "required": ["operation"],
        }

    def estimate_cost(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> float:
        """Estimate cost for knowledge graph operations."""
        # Neo4j operations are typically free (self-hosted) or based on instance size (cloud)
        # For now, return 0.0 as cost estimation
        # In production, you might want to track compute costs
        return 0.0


# Register the node
try:
    NodeRegistry.register(
        "knowledge_graph",
        KnowledgeGraphNode,
        KnowledgeGraphNode().get_metadata(),
    )
except Exception as e:
    logger.warning(f"Failed to register Knowledge Graph node: {e}")

