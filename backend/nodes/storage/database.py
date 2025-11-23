"""
Enhanced Database Node for NodeAI.

This node provides a dedicated interface for database operations with better UX
than the generic tool node. Supports SQLite, PostgreSQL, MySQL with query builder.
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.nodes.base import BaseNode
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseNode(BaseNode):
    """
    Enhanced Database Node.
    
    Provides a dedicated interface for database operations with better UX
    than the generic tool node.
    """

    node_type = "database"
    name = "Database"
    description = "Execute database queries with support for SQLite, PostgreSQL, and MySQL"
    category = "storage"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute database query.
        
        Supports: SQLite, PostgreSQL, MySQL
        """
        node_id = config.get("_node_id", "database")
        db_type = config.get("database_type", "sqlite")
        connection_string = config.get("database_connection_string", "")
        query = config.get("database_query") or inputs.get("query") or inputs.get("sql")
        
        if not connection_string:
            raise ValueError("Database connection string is required")
        if not query:
            raise ValueError("Database query is required")
        
        await self.stream_progress(node_id, 0.1, f"Connecting to {db_type} database...")
        
        start_time = time.time()
        
        try:
            if db_type == "sqlite":
                result = await self._execute_sqlite(connection_string, query, node_id)
            elif db_type == "postgresql":
                result = await self._execute_postgresql(connection_string, query, node_id)
            elif db_type == "mysql":
                result = await self._execute_mysql(connection_string, query, node_id)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            execution_time = time.time() - start_time
            result["execution_time"] = execution_time
            
            await self.stream_progress(node_id, 1.0, f"Query executed successfully in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Database query failed: {e}", exc_info=True)
            raise ValueError(f"Database query failed: {str(e)}")

    async def _execute_sqlite(
        self,
        connection_string: str,
        query: str,
        node_id: str,
    ) -> Dict[str, Any]:
        """Execute query on SQLite database."""
        try:
            import sqlite3
        except ImportError:
            raise ImportError("sqlite3 module not available (should be built-in)")
        
        await self.stream_progress(node_id, 0.3, "Executing SQLite query...")
        
        conn = sqlite3.connect(connection_string)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        try:
            cursor.execute(query)
            
            query_upper = query.strip().upper()
            is_select = query_upper.startswith("SELECT")
            
            if is_select:
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Convert rows to dictionaries
                results = [dict(row) for row in rows]
                
                return {
                    "output": {
                        "status": "success",
                        "query_type": "SELECT",
                        "row_count": len(results),
                        "columns": columns,
                        "results": results,
                    },
                    "results": results,
                    "columns": columns,
                    "row_count": len(results),
                    "query_type": "SELECT",
                }
            else:
                conn.commit()
                rowcount = cursor.rowcount
                
                return {
                    "output": {
                        "status": "success",
                        "query_type": query_upper.split()[0] if query_upper else "UNKNOWN",
                        "rows_affected": rowcount,
                    },
                    "rows_affected": rowcount,
                    "query_type": query_upper.split()[0] if query_upper else "UNKNOWN",
                }
        finally:
            cursor.close()
            conn.close()

    async def _execute_postgresql(
        self,
        connection_string: str,
        query: str,
        node_id: str,
    ) -> Dict[str, Any]:
        """Execute query on PostgreSQL database."""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError:
            raise ImportError("psycopg2 package not installed. Install with: pip install psycopg2-binary")
        
        await self.stream_progress(node_id, 0.3, "Executing PostgreSQL query...")
        
        conn = psycopg2.connect(connection_string)
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                
                query_upper = query.strip().upper()
                is_select = query_upper.startswith("SELECT")
                
                if is_select:
                    rows = cursor.fetchall()
                    columns = list(rows[0].keys()) if rows else []
                    
                    # Convert rows to dictionaries
                    results = [dict(row) for row in rows]
                    
                    return {
                        "output": {
                            "status": "success",
                            "query_type": "SELECT",
                            "row_count": len(results),
                            "columns": columns,
                            "results": results,
                        },
                        "results": results,
                        "columns": columns,
                        "row_count": len(results),
                        "query_type": "SELECT",
                    }
                else:
                    conn.commit()
                    rowcount = cursor.rowcount
                    
                    return {
                        "output": {
                            "status": "success",
                            "query_type": query_upper.split()[0] if query_upper else "UNKNOWN",
                            "rows_affected": rowcount,
                        },
                        "rows_affected": rowcount,
                        "query_type": query_upper.split()[0] if query_upper else "UNKNOWN",
                    }
        finally:
            conn.close()

    async def _execute_mysql(
        self,
        connection_string: str,
        query: str,
        node_id: str,
    ) -> Dict[str, Any]:
        """Execute query on MySQL database."""
        try:
            import mysql.connector
        except ImportError:
            raise ImportError("mysql-connector-python package not installed. Install with: pip install mysql-connector-python")
        
        await self.stream_progress(node_id, 0.3, "Executing MySQL query...")
        
        # MySQL connection string can be a dict or connection string
        # Try to parse as dict first, otherwise use as connection string
        try:
            conn_params = json.loads(connection_string) if connection_string.startswith('{') else connection_string
        except:
            conn_params = connection_string
        
        if isinstance(conn_params, dict):
            conn = mysql.connector.connect(**conn_params)
        else:
            # For connection string format, MySQL connector needs it parsed
            # This is a simplified version - in production, you'd want proper parsing
            conn = mysql.connector.connect(connection_string)
        
        try:
            cursor = conn.cursor(dictionary=True)  # Return results as dictionaries
            cursor.execute(query)
            
            query_upper = query.strip().upper()
            is_select = query_upper.startswith("SELECT")
            
            if is_select:
                rows = cursor.fetchall()
                columns = list(rows[0].keys()) if rows else []
                
                return {
                    "output": {
                        "status": "success",
                        "query_type": "SELECT",
                        "row_count": len(rows),
                        "columns": columns,
                        "results": rows,
                    },
                    "results": rows,
                    "columns": columns,
                    "row_count": len(rows),
                    "query_type": "SELECT",
                }
            else:
                conn.commit()
                rowcount = cursor.rowcount
                
                return {
                    "output": {
                        "status": "success",
                        "query_type": query_upper.split()[0] if query_upper else "UNKNOWN",
                        "rows_affected": rowcount,
                    },
                    "rows_affected": rowcount,
                    "query_type": query_upper.split()[0] if query_upper else "UNKNOWN",
                }
        finally:
            cursor.close()
            conn.close()

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for Database node configuration."""
        return {
            "type": "object",
            "properties": {
                "database_type": {
                    "type": "string",
                    "enum": ["sqlite", "postgresql", "mysql"],
                    "default": "sqlite",
                    "title": "Database Type",
                    "description": "Type of database",
                },
                "database_connection_string": {
                    "type": "string",
                    "title": "Connection String",
                    "description": "Database connection string (e.g., 'database.db' for SQLite, 'postgresql://user:pass@host:port/db' for PostgreSQL)",
                },
                "database_query": {
                    "type": "string",
                    "title": "SQL Query",
                    "description": "SQL query to execute (can also come from previous node)",
                },
                "query_type": {
                    "type": "string",
                    "enum": ["SELECT", "INSERT", "UPDATE", "DELETE", "CUSTOM"],
                    "default": "SELECT",
                    "title": "Query Type",
                    "description": "Type of query (for query builder - use CUSTOM for raw SQL)",
                },
            },
            "required": ["database_type", "database_connection_string", "database_query"],
        }


# Register the node
NodeRegistry.register(
    DatabaseNode.node_type,
    DatabaseNode,
    DatabaseNode().get_metadata(),
)

