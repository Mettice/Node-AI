"""
Data to Text Node for NodeAI.

This node converts structured data (CSV, Excel, JSON) to natural language text.
"""

from typing import Any, Dict, List

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class DataToTextNode(BaseNode):
    """
    Data to Text Node.
    
    Converts structured data to natural language text.
    Supports multiple output formats: table, list, narrative.
    """

    node_type = "data_to_text"
    name = "Data to Text"
    description = "Convert structured data (CSV, Excel, JSON) to natural language text for embedding."
    category = "processing"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the data to text node.
        
        Converts structured data to text.
        """
        node_id = config.get("_node_id", "data_to_text")
        
        await self.stream_progress(node_id, 0.1, "Preparing data conversion...")
        
        # Get data from inputs (from Data Loader node)
        data = inputs.get("data")
        schema = inputs.get("schema", {})
        
        if data is None:
            raise ValueError("data is required. Connect a Data Loader node.")
        
        await self.stream_progress(node_id, 0.3, "Converting data to text...")
        
        # Get format
        format_type = config.get("format", "table")
        max_records = config.get("max_records", 100)  # Limit records for large datasets
        include_schema = config.get("include_schema", False)
        
        await self.stream_progress(node_id, 0.5, f"Formatting as {format_type}...")
        
        # Convert to text based on format
        if format_type == "table":
            text = await self._format_as_table(data, schema, max_records, include_schema, node_id)
        elif format_type == "list":
            text = await self._format_as_list(data, schema, max_records, include_schema, node_id)
        elif format_type == "narrative":
            text = await self._format_as_narrative(data, schema, max_records, include_schema, node_id)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        await self.stream_progress(node_id, 0.9, f"Converted to text: {len(text)} characters")
        
        result = {
            "text": text,
            "metadata": {
                "source": "data_to_text",
                "format": format_type,
                "text_length": len(text),
                "records_processed": min(len(data) if isinstance(data, list) else 1, max_records),
            },
        }
        
        await self.stream_progress(node_id, 1.0, f"Data conversion completed: {len(text)} characters")
        
        return result
    
    async def _format_as_table(
        self, data: Any, schema: Dict[str, Any], max_records: int, include_schema: bool, node_id: str
    ) -> str:
        """Format data as a table."""
        lines = []
        
        if include_schema and schema:
            lines.append("Schema:")
            if "columns" in schema:
                lines.append(f"Columns: {', '.join(schema['columns'])}")
            if "row_count" in schema:
                lines.append(f"Total rows: {schema['row_count']}")
            lines.append("")
        
        if isinstance(data, list):
            if len(data) == 0:
                return "No data available."
            
            # Limit records
            records = data[:max_records]
            
            # Get column names from first record or schema
            if records and isinstance(records[0], dict):
                columns = list(records[0].keys())
            elif "columns" in schema:
                columns = schema["columns"]
            else:
                columns = []
            
            if not columns:
                return "No columns found in data."
            
            # Create header
            header = " | ".join(str(col) for col in columns)
            lines.append(header)
            lines.append("-" * len(header))
            
            # Add rows
            for i, record in enumerate(records):
                if isinstance(record, dict):
                    row = " | ".join(str(record.get(col, "")) for col in columns)
                    lines.append(row)
                else:
                    lines.append(str(record))
            
            if len(data) > max_records:
                lines.append(f"\n... ({len(data) - max_records} more records)")
        
        elif isinstance(data, dict):
            # Format as key-value pairs
            for key, value in data.items():
                lines.append(f"{key}: {value}")
        
        else:
            lines.append(str(data))
        
        return "\n".join(lines)
    
    async def _format_as_list(
        self, data: Any, schema: Dict[str, Any], max_records: int, include_schema: bool, node_id: str
    ) -> str:
        """Format data as a list."""
        lines = []
        
        if include_schema and schema:
            lines.append("Schema:")
            if "columns" in schema:
                lines.append(f"Columns: {', '.join(schema['columns'])}")
            lines.append("")
        
        if isinstance(data, list):
            if len(data) == 0:
                return "No data available."
            
            # Limit records
            records = data[:max_records]
            
            for i, record in enumerate(records, 1):
                if isinstance(record, dict):
                    record_text = ", ".join(f"{k}: {v}" for k, v in record.items())
                    lines.append(f"{i}. {record_text}")
                else:
                    lines.append(f"{i}. {record}")
            
            if len(data) > max_records:
                lines.append(f"\n... ({len(data) - max_records} more records)")
        
        elif isinstance(data, dict):
            for key, value in data.items():
                lines.append(f"- {key}: {value}")
        
        else:
            lines.append(f"- {data}")
        
        return "\n".join(lines)
    
    async def _format_as_narrative(
        self, data: Any, schema: Dict[str, Any], max_records: int, include_schema: bool, node_id: str
    ) -> str:
        """Format data as narrative text."""
        lines = []
        
        if include_schema and schema:
            if "columns" in schema:
                lines.append(f"This dataset contains {', '.join(schema['columns'])} columns.")
            if "row_count" in schema:
                lines.append(f"There are {schema['row_count']} records in total.")
            lines.append("")
        
        if isinstance(data, list):
            if len(data) == 0:
                return "No data available."
            
            # Limit records
            records = data[:max_records]
            
            lines.append("The data contains the following records:")
            lines.append("")
            
            for i, record in enumerate(records, 1):
                if isinstance(record, dict):
                    record_text = ", ".join(f"{k} is {v}" for k, v in record.items())
                    lines.append(f"Record {i}: {record_text}.")
                else:
                    lines.append(f"Record {i}: {record}.")
            
            if len(data) > max_records:
                lines.append(f"\nThere are {len(data) - max_records} additional records not shown here.")
        
        elif isinstance(data, dict):
            lines.append("The data contains the following information:")
            for key, value in data.items():
                lines.append(f"The {key} is {value}.")
        
        else:
            lines.append(f"The data value is {data}.")
        
        return "\n".join(lines)

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for data to text configuration."""
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "title": "Format",
                    "description": "Output text format",
                    "enum": ["table", "list", "narrative"],
                    "default": "table",
                },
                "max_records": {
                    "type": "integer",
                    "title": "Max Records",
                    "description": "Maximum number of records to include (to limit text length)",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 10000,
                },
                "include_schema": {
                    "type": "boolean",
                    "title": "Include Schema",
                    "description": "Include schema information in output",
                    "default": False,
                },
            },
            "required": [],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "text": {
                "type": "string",
                "description": "Converted text representation of data",
            },
            "metadata": {
                "type": "object",
                "description": "Conversion metadata",
            },
        }


# Register the node
NodeRegistry.register(
    DataToTextNode.node_type,
    DataToTextNode,
    DataToTextNode().get_metadata(),
)

