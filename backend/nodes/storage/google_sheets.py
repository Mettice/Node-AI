"""
Google Sheets Node for NodeAI.

This node supports reading from and writing to Google Sheets.
Supports operations: read, write, append, update.
"""

from typing import Any, Dict, List, Optional
import httpx

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.oauth import OAuthManager
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleSheetsNode(BaseNode):
    """
    Google Sheets Node.
    
    Supports reading from and writing to Google Sheets.
    Operations: read, write, append, update.
    """

    node_type = "google_sheets"
    name = "Google Sheets"
    description = "Read from and write to Google Sheets with OAuth support."
    category = "storage"  # Can be both input and output

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the Google Sheets node.
        
        Supports operations: read, write, append, update.
        """
        node_id = config.get("_node_id", "google_sheets")
        operation = config.get("operation", "read")  # read, write, append, update
        
        await self.stream_progress(node_id, 0.1, f"Connecting to Google Sheets ({operation})...")
        
        # Get OAuth token
        token_id = config.get("oauth_token_id")
        if not token_id:
            raise ValueError(
                "Google Sheets OAuth token ID is required. "
                "Please connect your Google account first."
            )
        
        token_data = OAuthManager.get_token(token_id)
        if not token_data:
            raise ValueError(
                "Google OAuth token not found. Please reconnect your Google account."
            )
        
        # Check if token is valid
        if not OAuthManager.is_token_valid(token_data):
            raise ValueError(
                "Google OAuth token has expired. Please reconnect your Google account."
            )
        
        access_token = token_data["access_token"]
        
        # Route to appropriate operation
        if operation == "read":
            return await self._execute_read(access_token, inputs, config, node_id)
        elif operation in ("write", "append", "update"):
            return await self._execute_write(access_token, inputs, config, node_id, operation)
        else:
            raise ValueError(f"Unsupported Google Sheets operation: {operation}")
    
    async def _execute_read(
        self,
        access_token: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Execute read operation."""
        # Get configuration
        spreadsheet_id = config.get("spreadsheet_id") or inputs.get("spreadsheet_id")
        sheet_name = config.get("sheet_name", "Sheet1")
        range_name = config.get("range")  # Optional, e.g., "A1:C100"
        has_header = config.get("has_header", True)
        
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID is required")
        
        await self.stream_progress(node_id, 0.3, f"Reading sheet: {sheet_name}...")
        
        # Build range string
        if range_name:
            range_str = f"{sheet_name}!{range_name}"
        else:
            range_str = sheet_name
        
        # Read data from Google Sheets API
        try:
            data, schema = await self._read_sheet(
                access_token=access_token,
                spreadsheet_id=spreadsheet_id,
                range_str=range_str,
                has_header=has_header,
                node_id=node_id,
            )
        except Exception as e:
            logger.error(f"Failed to read Google Sheet: {e}", exc_info=True)
            raise ValueError(f"Failed to read Google Sheet: {str(e)}")
        
        await self.stream_progress(
            node_id, 0.9, f"Loaded {len(data) if isinstance(data, list) else 1} records"
        )
        
        result = {
            "data": data,
            "schema": schema,
            "metadata": {
                "source": "google_sheets",
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": sheet_name,
                "range": range_name,
                "record_count": len(data) if isinstance(data, list) else 1,
            },
        }
        
        await self.stream_progress(
            node_id, 1.0, f"Data loaded: {len(data) if isinstance(data, list) else 1} records"
        )
        
        return result
    
    async def _execute_write(
        self,
        access_token: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
        operation: str,
    ) -> Dict[str, Any]:
        """Execute write/append/update operation."""
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
                "Google Sheets Read, or processing node)."
            )
        
        # Validate data format
        if not isinstance(data, list):
            raise ValueError(f"Data must be a list, got {type(data).__name__}")
        
        if len(data) == 0:
            raise ValueError("Data list is empty. Nothing to write.")
        
        if not isinstance(data[0], dict):
            raise ValueError("Data must be a list of dictionaries")
        
        # Get configuration
        spreadsheet_id = config.get("spreadsheet_id") or inputs.get("spreadsheet_id")
        sheet_name = config.get("sheet_name", "Sheet1")
        range_name = config.get("range")  # Optional, e.g., "A1"
        clear_existing = config.get("clear_existing", False)
        include_header = config.get("include_header", True)
        
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID is required")
        
        await self.stream_progress(node_id, 0.3, f"Converting {len(data)} records to rows...")
        
        # Convert list of dicts to rows
        rows = self._convert_data_to_rows(data, include_header)
        
        await self.stream_progress(node_id, 0.5, f"Writing {len(rows)} rows to sheet: {sheet_name}...")
        
        # Write to Google Sheets
        try:
            result = await self._write_to_sheet(
                access_token=access_token,
                spreadsheet_id=spreadsheet_id,
                sheet_name=sheet_name,
                range_name=range_name,
                rows=rows,
                operation=operation,
                clear_existing=clear_existing,
                node_id=node_id,
            )
        except Exception as e:
            logger.error(f"Failed to write to Google Sheet: {e}", exc_info=True)
            raise ValueError(f"Failed to write to Google Sheet: {str(e)}")
        
        await self.stream_progress(node_id, 1.0, f"Successfully wrote {len(data)} records")
        
        return {
            "success": True,
            "operation": operation,
            "rows_written": len(data),
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name,
            "range": result.get("range"),
            "updated_range": result.get("updatedRange"),
            "updated_cells": result.get("updatedCells"),
        }
    
    async def _read_sheet(
        self,
        access_token: str,
        spreadsheet_id: str,
        range_str: str,
        has_header: bool,
        node_id: str,
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Read data from Google Sheets using the Sheets API v4.
        
        Args:
            access_token: OAuth access token
            spreadsheet_id: Google Sheets spreadsheet ID
            range_str: Range string (e.g., "Sheet1!A1:C100")
            has_header: Whether the first row contains headers
            node_id: Node ID for progress updates
            
        Returns:
            Tuple of (data list, schema dict)
        """
        await self.stream_progress(node_id, 0.5, "Fetching data from Google Sheets API...")
        
        # Google Sheets API v4 endpoint
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_str}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                params={
                    "valueRenderOption": "UNFORMATTED_VALUE",  # Get raw values
                    "dateTimeRenderOption": "FORMATTED_STRING",  # Format dates as strings
                },
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                raise ValueError(f"Google Sheets API error: {error_msg}")
            
            data = response.json()
            values = data.get("values", [])
        
        await self.stream_progress(node_id, 0.7, f"Parsed {len(values)} rows")
        
        if not values:
            # Return empty data
            return [], {
                "columns": [],
                "row_count": 0,
                "column_count": 0,
                "has_header": has_header,
            }
        
        # Extract headers if present
        if has_header and len(values) > 0:
            headers = [str(cell).strip() if cell else f"Column{i+1}" for i, cell in enumerate(values[0])]
            data_rows = values[1:]
        else:
            # Generate column names
            max_cols = max(len(row) for row in values) if values else 0
            headers = [f"Column{i+1}" for i in range(max_cols)]
            data_rows = values
        
        # Convert to list of dictionaries
        records = []
        for row in data_rows:
            record = {}
            for i, header in enumerate(headers):
                # Pad row if needed
                value = row[i] if i < len(row) else None
                # Convert None to empty string for consistency
                record[header] = value if value is not None else ""
            records.append(record)
        
        # Generate schema
        schema = {
            "columns": headers,
            "row_count": len(records),
            "column_count": len(headers),
            "has_header": has_header,
        }
        
        return records, schema
    
    def _convert_data_to_rows(
        self,
        data: List[Dict[str, Any]],
        include_header: bool = True,
    ) -> List[List[Any]]:
        """
        Convert list of dictionaries to rows for Google Sheets.
        
        Args:
            data: List of dictionaries (records)
            include_header: Whether to include header row
            
        Returns:
            List of rows (each row is a list of values)
        """
        if not data:
            return []
        
        # Get all unique keys from all records (columns)
        all_keys = set()
        for record in data:
            all_keys.update(record.keys())
        
        # Sort keys for consistent column order
        columns = sorted(all_keys)
        
        rows = []
        
        # Add header row if requested
        if include_header:
            rows.append(columns)
        
        # Add data rows
        for record in data:
            row = [record.get(col, "") for col in columns]
            rows.append(row)
        
        return rows
    
    async def _write_to_sheet(
        self,
        access_token: str,
        spreadsheet_id: str,
        sheet_name: str,
        range_name: Optional[str],
        rows: List[List[Any]],
        operation: str,
        clear_existing: bool,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Write rows to Google Sheets using the Sheets API v4.
        
        Args:
            access_token: OAuth access token
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet
            range_name: Optional range (e.g., "A1")
            rows: List of rows to write
            operation: Operation type (write, append, update)
            clear_existing: Whether to clear existing data before writing
            node_id: Node ID for progress updates
            
        Returns:
            API response dictionary
        """
        await self.stream_progress(node_id, 0.7, f"Executing {operation} operation...")
        
        # Build range string
        if range_name:
            # If range is provided, use it directly
            if "!" in range_name:
                # Already includes sheet name
                range_str = range_name
            else:
                # Add sheet name
                range_str = f"{sheet_name}!{range_name}"
        else:
            # Default to starting at A1
            range_str = f"{sheet_name}!A1"
        
        # Prepare request body
        body = {
            "values": rows,
        }
        
        # Determine endpoint and method based on operation
        if operation == "append":
            # Append to end of sheet
            url = (
                f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/"
                f"{sheet_name}!A:Z:append"
            )
            params = {
                "valueInputOption": "USER_ENTERED",  # Preserve formatting
                "insertDataOption": "INSERT_ROWS",
            }
            method = "POST"
        elif operation == "update":
            # Update specific range
            url = (
                f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/"
                f"{range_str}"
            )
            params = {
                "valueInputOption": "USER_ENTERED",
            }
            method = "PUT"
        else:  # write (default)
            # Write/overwrite range
            url = (
                f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/"
                f"{range_str}"
            )
            params = {
                "valueInputOption": "USER_ENTERED",
            }
            if clear_existing:
                # Clear existing data first
                await self._clear_range(
                    access_token, spreadsheet_id, range_str, node_id
                )
            method = "PUT"
        
        await self.stream_progress(node_id, 0.8, "Sending request to Google Sheets API...")
        
        # Make API request
        async with httpx.AsyncClient() as client:
            if method == "POST":
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    params=params,
                    json=body,
                )
            else:  # PUT
                response = await client.put(
                    url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    params=params,
                    json=body,
                )
            
            if response.status_code not in (200, 201):
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                raise ValueError(f"Google Sheets API error: {error_msg}")
            
            return response.json()
    
    async def _clear_range(
        self,
        access_token: str,
        spreadsheet_id: str,
        range_str: str,
        node_id: str,
    ) -> None:
        """Clear a range in Google Sheets."""
        url = (
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/"
            f"{range_str}:clear"
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to clear range: {response.text}")
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for Google Sheets configuration."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "title": "Operation",
                    "description": "Google Sheets operation to perform",
                    "enum": ["read", "write", "append", "update"],
                    "default": "read",
                },
                "spreadsheet_id": {
                    "type": "string",
                    "title": "Spreadsheet ID",
                    "description": "Google Sheets spreadsheet ID (from the URL: /spreadsheets/d/{ID}/edit)",
                    "default": "",
                },
                "sheet_name": {
                    "type": "string",
                    "title": "Sheet Name",
                    "description": "Name of the sheet (default: 'Sheet1')",
                    "default": "Sheet1",
                },
                "range": {
                    "type": "string",
                    "title": "Range (Optional)",
                    "description": "Specific range (e.g., 'A1:C100' for read, 'A1' for write). Leave empty for entire sheet (read) or start at A1 (write).",
                    "default": "",
                },
                "has_header": {
                    "type": "boolean",
                    "title": "Has Header Row",
                    "description": "Whether the first row contains column headers (for read operation)",
                    "default": True,
                },
                "clear_existing": {
                    "type": "boolean",
                    "title": "Clear Existing Data",
                    "description": "Clear existing data in range before writing (only for 'write' operation)",
                    "default": False,
                },
                "include_header": {
                    "type": "boolean",
                    "title": "Include Header Row",
                    "description": "Include column headers as first row (for write operations)",
                    "default": True,
                },
                "oauth_token_id": {
                    "type": "string",
                    "title": "OAuth Token ID",
                    "description": "OAuth token ID for Google Sheets access (connect Google account first)",
                    "default": "",
                },
            },
            "required": ["spreadsheet_id", "oauth_token_id"],
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "data": {
                "type": "array",
                "description": "Parsed data (list of records as dictionaries) - for read operation",
            },
            "schema": {
                "type": "object",
                "description": "Data schema (columns, types, etc.) - for read operation",
            },
            "metadata": {
                "type": "object",
                "description": "Source metadata (spreadsheet_id, sheet_name, etc.) - for read operation",
            },
            "success": {
                "type": "boolean",
                "description": "Whether the write operation succeeded - for write operations",
            },
            "operation": {
                "type": "string",
                "description": "Operation type that was performed",
            },
            "rows_written": {
                "type": "integer",
                "description": "Number of records written - for write operations",
            },
        }

    def get_metadata(self) -> NodeMetadata:
        """Return node metadata."""
        return NodeMetadata(
            type=self.node_type,
            name=self.name,
            description=self.description,
            category=self.category,
            icon="googlesheets",  # Use ProviderIcon with 'googlesheets' or 'googledrive'
            config_schema=self.get_schema(),
        )


# Register the node
NodeRegistry.register(
    GoogleSheetsNode.node_type,
    GoogleSheetsNode,
    GoogleSheetsNode().get_metadata(),
)
