"""
Airtable Node for NodeAI.

This node supports reading from and writing to Airtable.
Supports operations: read, create, update, upsert.
"""

from typing import Any, Dict, List, Optional
import httpx
from urllib.parse import quote

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.secret_resolver import resolve_api_key
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AirtableNode(BaseNode):
    """
    Airtable Node.
    
    Supports reading from and writing to Airtable.
    Operations: read, create, update, upsert.
    """

    node_type = "airtable"
    name = "Airtable"
    description = "Read from and write to Airtable with API key support."
    category = "storage"  # Can be both input and output

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the Airtable node.
        
        Supports operations: read, create, update, upsert.
        """
        node_id = config.get("_node_id", "airtable")
        operation = config.get("operation", "read")  # read, create, update, upsert
        
        await self.stream_progress(node_id, 0.1, f"Connecting to Airtable ({operation})...")
        
        # Get configuration
        base_id = config.get("base_id") or inputs.get("base_id")
        table_name = config.get("table_name") or inputs.get("table_name")
        table_id = config.get("table_id") or inputs.get("table_id")  # Optional: can use table ID instead of name
        
        # Resolve API key from vault if secret_id is provided, otherwise use direct value
        user_id = config.get("_user_id")
        api_key = resolve_api_key(
            config, "api_key", user_id=user_id
        ) or config.get("api_key") or inputs.get("api_key")
        
        if not base_id:
            raise ValueError("Airtable Base ID is required")
        if not table_name and not table_id:
            raise ValueError("Airtable Table name or Table ID is required")
        if not api_key:
            raise ValueError("Airtable API key is required")
        
        # Clean base_id - remove any path components if user pasted full URL
        if "/" in base_id:
            # Extract just the base ID part (app...)
            parts = base_id.split("/")
            for part in parts:
                if part.startswith("app"):
                    base_id = part
                    break
        
        # Use table_id if provided, otherwise use table_name
        table_identifier = table_id if table_id else table_name
        
        # Route to appropriate operation
        if operation == "read":
            return await self._execute_read(api_key, base_id, table_identifier, inputs, config, node_id)
        elif operation in ("create", "update", "upsert"):
            return await self._execute_write(api_key, base_id, table_identifier, inputs, config, node_id, operation)
        else:
            raise ValueError(f"Unsupported Airtable operation: {operation}")
    
    async def _execute_read(
        self,
        api_key: str,
        base_id: str,
        table_identifier: str,  # Can be table name or table ID
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Execute read operation."""
        # Optional parameters
        view = config.get("view")  # Optional view name
        filter_by_formula = config.get("filter_by_formula")  # Optional filter
        max_records = config.get("max_records")  # Optional limit
        
        await self.stream_progress(node_id, 0.3, f"Fetching records from table: {table_identifier}...")
        
        # Read data from Airtable API
        try:
            data, schema = await self._read_records(
                api_key=api_key,
                base_id=base_id,
                table_identifier=table_identifier,
                view=view,
                filter_by_formula=filter_by_formula,
                max_records=max_records,
                node_id=node_id,
            )
        except Exception as e:
            logger.error(f"Failed to read Airtable records: {e}", exc_info=True)
            raise ValueError(f"Failed to read Airtable records: {str(e)}")
        
        await self.stream_progress(
            node_id, 0.9, f"Loaded {len(data) if isinstance(data, list) else 1} records"
        )
        
        result = {
            "data": data,
            "schema": schema,
            "metadata": {
                "source": "airtable",
                "base_id": base_id,
                "table_name": table_identifier,  # Can be name or ID
                "view": view,
                "record_count": len(data) if isinstance(data, list) else 1,
            },
        }
        
        await self.stream_progress(
            node_id, 1.0, f"Data loaded: {len(data) if isinstance(data, list) else 1} records"
        )
        
        return result
    
    async def _execute_write(
        self,
        api_key: str,
        base_id: str,
        table_identifier: str,  # Can be table name or table ID
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
        operation: str,
    ) -> Dict[str, Any]:
        """Execute create/update/upsert operation."""
        # Get data from inputs (from previous nodes)
        data = (
            inputs.get("data") or
            inputs.get("results") or
            inputs.get("records") or
            []
        )
        
        if not data:
            raise ValueError(
                "No data to write. Connect a data source node (e.g., Data Loader, "
                "Airtable Read, Google Sheets Read, or processing node)."
            )
        
        # Validate data format
        if not isinstance(data, list):
            raise ValueError(f"Data must be a list, got {type(data).__name__}")
        
        if len(data) == 0:
            raise ValueError("Data list is empty. Nothing to write.")
        
        if not isinstance(data[0], dict):
            raise ValueError("Data must be a list of dictionaries")
        
        await self.stream_progress(node_id, 0.3, f"Converting {len(data)} records for Airtable...")
        
        # Convert list of dicts to Airtable records format
        records = self._convert_data_to_records(data, operation)
        
        await self.stream_progress(node_id, 0.5, f"Writing {len(records)} records to table: {table_identifier}...")
        
        # Write to Airtable
        try:
            result = await self._write_records(
                api_key=api_key,
                base_id=base_id,
                table_identifier=table_identifier,
                records=records,
                operation=operation,
                node_id=node_id,
            )
        except Exception as e:
            logger.error(f"Failed to write to Airtable: {e}", exc_info=True)
            raise ValueError(f"Failed to write to Airtable: {str(e)}")
        
        await self.stream_progress(node_id, 1.0, f"Successfully wrote {result.get('records_created', 0)} records")
        
        return {
            "success": True,
            "operation": operation,
            "records_created": result.get("records_created", 0),
            "records_updated": result.get("records_updated", 0),
            "total_records": len(data),
            "base_id": base_id,
            "table_name": table_identifier,  # Can be name or ID
            "errors": result.get("errors"),
        }
    
    async def _read_records(
        self,
        api_key: str,
        base_id: str,
        table_identifier: str,  # Can be table name or table ID
        view: Optional[str],
        filter_by_formula: Optional[str],
        max_records: Optional[int],
        node_id: str,
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Read records from Airtable using the Airtable API.
        
        Args:
            api_key: Airtable API key
            base_id: Airtable Base ID
            table_identifier: Table name or table ID (tbl...)
            view: Optional view name
            filter_by_formula: Optional filter formula
            max_records: Optional maximum records to fetch
            node_id: Node ID for progress updates
            
        Returns:
            Tuple of (data list, schema dict)
        """
        await self.stream_progress(node_id, 0.5, "Fetching data from Airtable API...")
        
        # Airtable API endpoint - URL encode table identifier to handle spaces and special characters
        # Table ID (tbl...) doesn't need encoding, but table names do
        encoded_table = quote(table_identifier, safe='') if not table_identifier.startswith('tbl') else table_identifier
        url = f"https://api.airtable.com/v0/{base_id}/{encoded_table}"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Build query parameters
        params = {}
        if view:
            params["view"] = view
        if filter_by_formula:
            params["filterByFormula"] = filter_by_formula
        if max_records:
            params["maxRecords"] = min(max_records, 100)  # Airtable max is 100 per request
        
        all_records = []
        offset = None
        total_fetched = 0
        
        # Paginate through all records
        while True:
            if offset:
                params["offset"] = offset
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params=params,
                )
                
                if response.status_code != 200:
                    # Try to parse error response
                    error_msg = "Unknown error"
                    try:
                        if response.content:
                            error_data = response.json()
                            # Handle both dict and string responses
                            if isinstance(error_data, dict):
                                error_msg = error_data.get("error", {}).get("message", str(error_data))
                            elif isinstance(error_data, str):
                                error_msg = error_data
                            else:
                                error_msg = str(error_data)
                        else:
                            error_msg = f"HTTP {response.status_code}: No response body"
                    except Exception as e:
                        # If JSON parsing fails, use response text
                        error_msg = response.text[:500] if response.text else f"HTTP {response.status_code}: Failed to parse error response"
                    
                    # Add helpful context for 404 errors
                    if response.status_code == 404:
                        error_msg = (
                            f"{error_msg}. "
                            f"Please verify: Base ID '{base_id}' and Table identifier '{table_identifier}' are correct. "
                            f"You can use either the table name (e.g., 'Leads') or table ID (e.g., 'tbl8ic7XsKDgVfrQq'). "
                            f"Table names with spaces or special characters are automatically URL-encoded."
                        )
                    
                    raise ValueError(f"Airtable API error ({response.status_code}): {error_msg}")
                
                data = response.json()
                records = data.get("records", [])
                all_records.extend(records)
                total_fetched += len(records)
                
                await self.stream_progress(
                    node_id, 0.5 + (total_fetched / (max_records or 1000)) * 0.3,
                    f"Fetched {total_fetched} records..."
                )
                
                # Check if there are more records
                offset = data.get("offset")
                if not offset:
                    break
                
                # Respect max_records limit
                if max_records and total_fetched >= max_records:
                    all_records = all_records[:max_records]
                    break
        
        await self.stream_progress(node_id, 0.8, f"Parsed {len(all_records)} records")
        
        if not all_records:
            # Return empty data
            return [], {
                "base_id": base_id,
                "table_name": table_identifier,  # Can be name or ID
                "field_names": [],
                "record_count": 0,
            }
        
        # Convert Airtable records to list of dictionaries (flatten fields)
        # Airtable format: {"id": "rec123", "fields": {"Name": "John", ...}}
        # Our format: {"id": "rec123", "Name": "John", ...}
        data_list = []
        all_field_names = set()
        
        for record in all_records:
            record_dict = {
                "id": record.get("id"),
            }
            fields = record.get("fields", {})
            record_dict.update(fields)  # Flatten fields
            data_list.append(record_dict)
            all_field_names.update(fields.keys())
        
        # Generate schema
        schema = {
            "base_id": base_id,
            "table_name": table_identifier,  # Can be name or ID
            "field_names": sorted(all_field_names),
            "record_count": len(data_list),
        }
        
        return data_list, schema
    
    def _convert_data_to_records(
        self,
        data: List[Dict[str, Any]],
        operation: str,
    ) -> List[Dict[str, Any]]:
        """
        Convert list of dictionaries to Airtable records format.
        
        Args:
            data: List of dictionaries (records)
            operation: Operation type (create, update, upsert)
            
        Returns:
            List of Airtable records
        """
        records = []
        
        for record in data:
            # Airtable expects {"fields": {...}} or {"id": "...", "fields": {...}}
            airtable_record = {}
            
            # For update/upsert, check if record has an "id" field
            if operation in ("update", "upsert") and "id" in record:
                airtable_record["id"] = record.pop("id")
            
            # All other fields go into "fields"
            airtable_record["fields"] = record
            
            records.append(airtable_record)
        
        return records
    
    async def _write_records(
        self,
        api_key: str,
        base_id: str,
        table_name: str,
        records: List[Dict[str, Any]],
        operation: str,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Write records to Airtable using the Airtable API.
        
        Args:
            api_key: Airtable API key
            base_id: Airtable Base ID
            table_name: Table name
            records: List of Airtable records
            operation: Operation type (create, update, upsert)
            node_id: Node ID for progress updates
            
        Returns:
            Result dictionary with counts and errors
        """
        await self.stream_progress(node_id, 0.7, f"Executing {operation} operation...")
        
        # Airtable API endpoint
        # URL encode table name to handle spaces and special characters
        encoded_table_name = quote(table_name, safe='')
        url = f"https://api.airtable.com/v0/{base_id}/{encoded_table_name}"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Airtable allows max 10 records per request
        batch_size = 10
        created_count = 0
        updated_count = 0
        errors = []
        
        # Process in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(records) + batch_size - 1) // batch_size
            
            await self.stream_progress(
                node_id,
                0.7 + (i / len(records)) * 0.25,
                f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)..."
            )
            
            # Prepare request body based on operation
            if operation == "create":
                body = {"records": batch}
                method = "POST"
            elif operation == "update":
                # Update requires records with IDs
                body = {"records": batch}
                method = "PATCH"
            elif operation == "upsert":
                # Upsert uses PATCH with typecast and performUpsert
                body = {
                    "records": batch,
                    "typecast": True,
                    "performUpsert": {
                        "fieldsToMergeOn": ["id"]  # Upsert on ID field if present
                    }
                }
                method = "PATCH"
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "POST":
                    response = await client.post(url, headers=headers, json=body)
                else:  # PATCH
                    response = await client.patch(url, headers=headers, json=body)
                
                if response.status_code in (200, 201):
                    response_data = response.json()
                    created_records = response_data.get("records", [])
                    created_count += len(created_records)
                    
                    # For update/upsert, count updated records
                    if operation in ("update", "upsert"):
                        updated_count += len(created_records)
                else:
                    # Try to parse error response
                    error_msg = "Unknown error"
                    error_data = {}
                    try:
                        if response.content:
                            error_data = response.json()
                            # Handle both dict and string responses
                            if isinstance(error_data, dict):
                                error_msg = error_data.get("error", {}).get("message", str(error_data))
                            elif isinstance(error_data, str):
                                error_msg = error_data
                            else:
                                error_msg = str(error_data)
                        else:
                            error_msg = f"HTTP {response.status_code}: No response body"
                    except Exception as e:
                        # If JSON parsing fails, use response text
                        error_msg = response.text[:500] if response.text else f"HTTP {response.status_code}: Failed to parse error response"
                        error_data = {"raw_error": error_msg}
                    
                    errors.append({
                        "batch": batch_num,
                        "error": error_msg,
                        "details": error_data,
                    })
                    logger.error(f"Airtable API error (batch {batch_num}): {error_msg}")
        
        await self.stream_progress(node_id, 0.95, f"Completed: {created_count} records processed")
        
        return {
            "records_created": created_count,
            "records_updated": updated_count if operation in ("update", "upsert") else 0,
            "errors": errors if errors else None,
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for Airtable configuration."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "title": "Operation",
                    "description": "Airtable operation to perform",
                    "enum": ["read", "create", "update", "upsert"],
                    "default": "read",
                },
                "base_id": {
                    "type": "string",
                    "title": "Base ID",
                    "description": "Airtable Base ID (from the URL: /app{baseId}/...). Example: 'appbXFBBjkOpCfek5'. If you paste the full URL, the base ID will be extracted automatically.",
                    "default": "",
                },
                "table_name": {
                    "type": "string",
                    "title": "Table Name",
                    "description": "Name of the table (e.g., 'Leads'). Alternatively, use Table ID below.",
                    "default": "",
                },
                "table_id": {
                    "type": "string",
                    "title": "Table ID (Optional)",
                    "description": "Table ID from the URL (e.g., 'tbl8ic7XsKDgVfrQq'). More reliable than table name. If provided, this takes precedence over table name.",
                    "default": "",
                },
                "api_key": {
                    "type": "string",
                    "title": "API Key",
                    "description": "Airtable API key (get from https://airtable.com/api)",
                    "default": "",
                },
                "view": {
                    "type": "string",
                    "title": "View (Optional)",
                    "description": "Name of the view to read from (only for read operation)",
                    "default": "",
                },
                "filter_by_formula": {
                    "type": "string",
                    "title": "Filter Formula (Optional)",
                    "description": "Airtable formula to filter records (only for read operation, e.g., \"{Status} = 'Active'\")",
                    "default": "",
                },
                "max_records": {
                    "type": "integer",
                    "title": "Max Records (Optional)",
                    "description": "Maximum number of records to fetch (only for read operation, leave empty for all)",
                    "default": None,
                    "minimum": 1,
                    "maximum": 10000,
                },
            },
            "required": ["base_id", "api_key"],
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "data": {
                "type": "array",
                "description": "Parsed data (list of records as dictionaries with flattened fields) - for read operation",
            },
            "schema": {
                "type": "object",
                "description": "Data schema (field names, record count, etc.) - for read operation",
            },
            "metadata": {
                "type": "object",
                "description": "Source metadata (base_id, table_name, view, etc.) - for read operation",
            },
            "success": {
                "type": "boolean",
                "description": "Whether the write operation succeeded - for write operations",
            },
            "operation": {
                "type": "string",
                "description": "Operation type that was performed",
            },
            "records_created": {
                "type": "integer",
                "description": "Number of records created - for write operations",
            },
            "records_updated": {
                "type": "integer",
                "description": "Number of records updated (for update/upsert operations)",
            },
            "total_records": {
                "type": "integer",
                "description": "Total number of records processed - for write operations",
            },
        }

    def get_metadata(self) -> NodeMetadata:
        """Return node metadata."""
        return NodeMetadata(
            type=self.node_type,
            name=self.name,
            description=self.description,
            category=self.category,
            icon="airtable",  # Use ProviderIcon with 'airtable'
            config_schema=self.get_schema(),
        )


# Register the node
NodeRegistry.register(
    AirtableNode.node_type,
    AirtableNode,
    AirtableNode().get_metadata(),
)
