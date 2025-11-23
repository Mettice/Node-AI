"""
Database query tool implementation.
"""

from typing import Dict, Any, Callable


def get_database_query_schema() -> Dict[str, Any]:
    """Get schema fields for database query tool."""
    return {
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
            "description": "Database connection string",
        },
    }


def create_database_query_tool(config: Dict[str, Any]) -> Callable[[str], str]:
    """Create database query tool function."""
    def db_query_func(query: str) -> str:
        """Execute a database query."""
        db_type = config.get("database_type", "sqlite")
        connection_string = config.get("database_connection_string", "")
        
        try:
            if db_type == "sqlite":
                import sqlite3
                if not connection_string:
                    return "Error: Connection string required for SQLite database"
                conn = sqlite3.connect(connection_string)
                cursor = conn.cursor()
                cursor.execute(query)
                
                if query.strip().upper().startswith("SELECT"):
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    conn.close()
                    
                    if not results:
                        return "Query executed successfully. No results returned."
                    
                    # Format results
                    formatted = f"Columns: {', '.join(columns)}\n\n"
                    formatted += "\n".join([str(row) for row in results[:100]])  # Limit to 100 rows
                    if len(results) > 100:
                        formatted += f"\n... ({len(results) - 100} more rows)"
                    return formatted
                else:
                    conn.commit()
                    conn.close()
                    return f"Query executed successfully. {cursor.rowcount} row(s) affected."
            
            elif db_type == "postgresql":
                try:
                    import psycopg2
                    if not connection_string:
                        return "Error: Connection string required for PostgreSQL database"
                    conn = psycopg2.connect(connection_string)
                    cursor = conn.cursor()
                    cursor.execute(query)
                    
                    if query.strip().upper().startswith("SELECT"):
                        results = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description] if cursor.description else []
                        conn.close()
                        
                        if not results:
                            return "Query executed successfully. No results returned."
                        
                        formatted = f"Columns: {', '.join(columns)}\n\n"
                        formatted += "\n".join([str(row) for row in results[:100]])
                        if len(results) > 100:
                            formatted += f"\n... ({len(results) - 100} more rows)"
                        return formatted
                    else:
                        conn.commit()
                        conn.close()
                        return f"Query executed successfully. {cursor.rowcount} row(s) affected."
                except ImportError:
                    return "Error: psycopg2 package not installed. Install with: pip install psycopg2-binary"
            
            elif db_type == "mysql":
                try:
                    import mysql.connector
                    if not connection_string:
                        return "Error: Connection string required for MySQL database"
                    # Parse connection string or use as-is
                    conn = mysql.connector.connect(connection_string)
                    cursor = conn.cursor()
                    cursor.execute(query)
                    
                    if query.strip().upper().startswith("SELECT"):
                        results = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description] if cursor.description else []
                        conn.close()
                        
                        if not results:
                            return "Query executed successfully. No results returned."
                        
                        formatted = f"Columns: {', '.join(columns)}\n\n"
                        formatted += "\n".join([str(row) for row in results[:100]])
                        if len(results) > 100:
                            formatted += f"\n... ({len(results) - 100} more rows)"
                        return formatted
                    else:
                        conn.commit()
                        conn.close()
                        return f"Query executed successfully. {cursor.rowcount} row(s) affected."
                except ImportError:
                    return "Error: mysql-connector-python package not installed. Install with: pip install mysql-connector-python"
            
            return f"Error: Unknown database type: {db_type}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    return db_query_func

