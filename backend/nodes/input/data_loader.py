"""
Data Loader Node for NodeAI.

This node loads and parses structured data files (CSV, Excel, JSON, Parquet).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Upload directory (same as file_loader)
UPLOAD_DIR = Path("uploads")


class DataLoaderNode(BaseNode):
    """
    Data Loader Node.
    
    Loads and parses structured data files.
    Supports: CSV, Excel (XLSX), JSON, Parquet
    """

    node_type = "data_loader"
    name = "Data Loader"
    description = "Load and parse structured data files (CSV, Excel, JSON, Parquet)."
    category = "input"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the data loader node.
        
        Loads and parses structured data files.
        Can work standalone (with file_id) or connected to File Upload node (with data_path).
        """
        node_id = config.get("_node_id", "data_loader")
        
        await self.stream_progress(node_id, 0.1, "Locating data file...")
        
        # Get file_id from config (if standalone) or data_path from inputs (if from File Upload)
        file_id = config.get("file_id")
        data_path = inputs.get("data_path") or inputs.get("text")  # From File Upload node
        
        if not data_path and not file_id:
            raise ValueError("Either file_id (config) or data_path (from File Upload) is required")
        
        # If file_id provided, find the file
        if file_id and not data_path:
            data_extensions = [".csv", ".xlsx", ".json", ".parquet"]
            for ext in data_extensions:
                candidate = UPLOAD_DIR / f"{file_id}{ext}"
                if candidate.exists():
                    data_path = candidate
                    break
            
            if not data_path:
                raise ValueError(f"Data file with ID {file_id} not found")
        
        # Validate path exists
        if isinstance(data_path, str):
            data_path = Path(data_path)
        
        if not data_path.exists():
            raise ValueError(f"Data file not found: {data_path}")
        
        await self.stream_progress(node_id, 0.3, f"Found file: {data_path.name}")
        
        # Determine file type and parse
        ext = data_path.suffix.lower()
        await self.stream_progress(node_id, 0.5, f"Parsing {ext} file...")
        
        if ext == ".csv":
            data, schema = await self._load_csv(data_path, node_id, config)
        elif ext == ".xlsx":
            data, schema = await self._load_excel(data_path, node_id, config)
        elif ext == ".json":
            data, schema = await self._load_json(data_path, node_id)
        elif ext == ".parquet":
            data, schema = await self._load_parquet(data_path, node_id)
        else:
            raise ValueError(f"Unsupported data file type: {ext}")
        
        await self.stream_progress(node_id, 0.9, f"Loaded {len(data) if isinstance(data, list) else 1} records")
        
        result = {
            "data": data,
            "schema": schema,
            "metadata": {
                "source": "data_upload",
                "file_path": str(data_path),
                "file_type": ext,
                "file_category": "data",
                "record_count": len(data) if isinstance(data, list) else 1,
            },
        }
        
        await self.stream_progress(node_id, 1.0, f"Data loaded: {len(data) if isinstance(data, list) else 1} records")
        
        return result
    
    async def _load_csv(self, file_path: Path, node_id: str, config: Dict[str, Any]) -> tuple[Any, Dict[str, Any]]:
        """Load CSV file."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "CSV loading requires pandas. Install with: pip install pandas"
            )
        
        try:
            await self.stream_progress(node_id, 0.6, "Reading CSV file...")
            
            # CSV options
            delimiter = config.get("delimiter", ",")
            header = config.get("header", 0)  # 0 = first row, None = no header
            nrows = config.get("nrows", None)  # Limit rows
            
            df = pd.read_csv(
                file_path,
                delimiter=delimiter,
                header=header,
                nrows=nrows,
            )
            
            await self.stream_progress(node_id, 0.7, f"Parsed {len(df)} rows, {len(df.columns)} columns")
            
            # Convert to list of dicts
            data = df.to_dict(orient="records")
            
            # Generate schema
            schema = {
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "row_count": len(df),
                "column_count": len(df.columns),
            }
            
            return data, schema
            
        except Exception as e:
            logger.error(f"CSV loading failed: {e}")
            raise ValueError(f"Failed to load CSV: {str(e)}")
    
    async def _load_excel(self, file_path: Path, node_id: str, config: Dict[str, Any]) -> tuple[Any, Dict[str, Any]]:
        """Load Excel file."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Excel loading requires pandas and openpyxl. Install with: pip install pandas openpyxl")
        
        try:
            await self.stream_progress(node_id, 0.6, "Reading Excel file...")
            
            # Excel options
            sheet_name = config.get("sheet_name", 0)  # 0 = first sheet, None = all sheets
            header = config.get("header", 0)
            nrows = config.get("nrows", None)
            
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                header=header,
                nrows=nrows,
            )
            
            await self.stream_progress(node_id, 0.7, f"Parsed {len(df)} rows, {len(df.columns)} columns")
            
            # Convert to list of dicts
            data = df.to_dict(orient="records")
            
            # Generate schema
            schema = {
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "row_count": len(df),
                "column_count": len(df.columns),
                "sheet_name": sheet_name,
            }
            
            return data, schema
            
        except Exception as e:
            logger.error(f"Excel loading failed: {e}")
            raise ValueError(f"Failed to load Excel: {str(e)}")
    
    async def _load_json(self, file_path: Path, node_id: str) -> tuple[Any, Dict[str, Any]]:
        """Load JSON file."""
        try:
            await self.stream_progress(node_id, 0.6, "Reading JSON file...")
            
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            await self.stream_progress(node_id, 0.7, "Parsed JSON file")
            
            # Generate schema
            if isinstance(data, list):
                if len(data) > 0:
                    # Infer schema from first item
                    first_item = data[0]
                    schema = {
                        "type": "array",
                        "item_type": type(first_item).__name__,
                        "item_keys": list(first_item.keys()) if isinstance(first_item, dict) else None,
                        "length": len(data),
                    }
                else:
                    schema = {"type": "array", "length": 0}
            elif isinstance(data, dict):
                schema = {
                    "type": "object",
                    "keys": list(data.keys()),
                }
            else:
                schema = {
                    "type": type(data).__name__,
                }
            
            return data, schema
            
        except Exception as e:
            logger.error(f"JSON loading failed: {e}")
            raise ValueError(f"Failed to load JSON: {str(e)}")
    
    async def _load_parquet(self, file_path: Path, node_id: str) -> tuple[Any, Dict[str, Any]]:
        """Load Parquet file."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Parquet loading requires pandas and pyarrow. Install with: pip install pandas pyarrow")
        
        try:
            await self.stream_progress(node_id, 0.6, "Reading Parquet file...")
            
            df = pd.read_parquet(file_path)
            
            await self.stream_progress(node_id, 0.7, f"Parsed {len(df)} rows, {len(df.columns)} columns")
            
            # Convert to list of dicts
            data = df.to_dict(orient="records")
            
            # Generate schema
            schema = {
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "row_count": len(df),
                "column_count": len(df.columns),
            }
            
            return data, schema
            
        except Exception as e:
            logger.error(f"Parquet loading failed: {e}")
            raise ValueError(f"Failed to load Parquet: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for data loader configuration."""
        return {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "title": "File ID (Optional)",
                    "description": "ID of uploaded data file (if not using File Upload node)",
                    "default": "",
                },
                "delimiter": {
                    "type": "string",
                    "title": "Delimiter (CSV only)",
                    "description": "CSV delimiter character",
                    "default": ",",
                },
                "header": {
                    "type": "integer",
                    "title": "Header Row (CSV/Excel)",
                    "description": "Row number to use as header (0 = first row, -1 = no header)",
                    "default": 0,
                },
                "sheet_name": {
                    "type": "string",
                    "title": "Sheet Name (Excel only)",
                    "description": "Sheet name or index (0 = first sheet)",
                    "default": "0",
                },
                "nrows": {
                    "type": "integer",
                    "title": "Max Rows (Optional)",
                    "description": "Maximum number of rows to load (leave empty for all)",
                    "default": None,
                    "minimum": 1,
                },
            },
            "required": [],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "data": {
                "type": "array",
                "description": "Parsed data (list of records for CSV/Excel/Parquet, or JSON structure)",
            },
            "schema": {
                "type": "object",
                "description": "Data schema (columns, types, etc.)",
            },
            "metadata": {
                "type": "object",
                "description": "File metadata",
            },
        }


# Register the node
NodeRegistry.register(
    DataLoaderNode.node_type,
    DataLoaderNode,
    DataLoaderNode().get_metadata(),
)

