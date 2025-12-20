"""
Base node class for NodeAI backend.

This module defines the abstract BaseNode class that all node implementations
must inherit from. It provides the common interface and shared functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.models import NodeMetadata
from backend.core.streaming import StreamableNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class BaseNode(ABC):
    """
    Abstract base class for all nodes in NodeAI.
    
    All node implementations must inherit from this class and implement
    the required abstract methods.
    
    Attributes:
        node_type: Unique identifier for the node type (e.g., 'text_input')
        name: Human-readable name for the node
        description: Description of what the node does
        category: Category of the node (input, processing, embedding, etc.)
    """

    # These should be overridden in subclasses
    node_type: str = ""
    name: str = ""
    description: str = ""
    category: str = ""

    def __init__(self):
        """Initialize the base node."""
        if not self.node_type:
            raise ValueError(f"Node class {self.__class__.__name__} must define node_type")
        # Initialize streaming support (all nodes can use streaming)
        self.execution_id: Optional[str] = None

    @abstractmethod
    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the node logic.
        
        This is the main method that performs the node's work. It should:
        1. Validate inputs and config
        2. Perform the node's operation
        3. Return output data
        
        Args:
            inputs: Input data from previous nodes (keyed by input name)
            config: Node configuration from the workflow
            
        Returns:
            Dictionary containing the node's output data
            
        Raises:
            NodeExecutionError: If execution fails
            NodeValidationError: If inputs or config are invalid
            
        Example:
            ```python
            async def execute(self, inputs, config):
                text = inputs.get("text", "")
                result = process_text(text)
                return {"output": result}
            ```
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for node configuration.
        
        This schema is used by the frontend to generate configuration forms.
        It should follow JSON Schema specification.
        
        Returns:
            JSON schema dictionary
            
        Example:
            ```python
            def get_schema(self):
                return {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "title": "Text Input",
                            "description": "Enter text to process"
                        }
                    },
                    "required": ["text"]
                }
            ```
        """
        pass

    def validate(self, config: Dict[str, Any]) -> bool:
        """
        Validate node configuration.
        
        This method checks if the provided configuration is valid.
        Override this method for custom validation logic.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            NodeValidationError: If validation fails (with details)
        """
        # Enhanced validation with type checking and value constraints
        schema = self.get_schema()
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        validation_errors = []
        
        # Apply schema defaults for missing fields BEFORE validation
        # This ensures nodes work with their default values even if not explicitly configured
        for field_name, field_schema in properties.items():
            if field_name not in config or config[field_name] is None:
                if "default" in field_schema:
                    config[field_name] = field_schema["default"]
        
        # Check required fields (after applying defaults)
        missing_fields = []
        for field in required:
            if field not in config or config[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            validation_errors.extend(missing_fields)
        
        # Type and value validation
        for field_name, field_schema in properties.items():
            if field_name in config:
                value = config[field_name]
                
                # Skip validation for None values if field is not required
                if value is None and field_name not in required:
                    continue
                
                # Type validation
                expected_type = field_schema.get("type", "any")
                if expected_type != "any" and not self._validate_type(value, expected_type):
                    validation_errors.append(f"Field '{field_name}' must be of type {expected_type}, got {type(value).__name__}")
                
                # Value constraints
                if "minimum" in field_schema and isinstance(value, (int, float)) and value < field_schema["minimum"]:
                    validation_errors.append(f"Field '{field_name}' must be >= {field_schema['minimum']}, got {value}")
                
                if "maximum" in field_schema and isinstance(value, (int, float)) and value > field_schema["maximum"]:
                    validation_errors.append(f"Field '{field_name}' must be <= {field_schema['maximum']}, got {value}")
                
                if "minLength" in field_schema and isinstance(value, str) and len(value) < field_schema["minLength"]:
                    validation_errors.append(f"Field '{field_name}' must be at least {field_schema['minLength']} characters")
                
                if "maxLength" in field_schema and isinstance(value, str) and len(value) > field_schema["maxLength"]:
                    validation_errors.append(f"Field '{field_name}' must be at most {field_schema['maxLength']} characters")
                
                if "enum" in field_schema and value not in field_schema["enum"]:
                    validation_errors.append(f"Field '{field_name}' must be one of {field_schema['enum']}, got {value}")

        if validation_errors:
            raise NodeValidationError(
                f"Configuration validation failed: {'; '.join(validation_errors)}",
                errors=validation_errors,
            )

        return True
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """
        Validate that a value matches the expected JSON Schema type.
        
        Args:
            value: Value to validate
            expected_type: JSON Schema type string
            
        Returns:
            True if value matches expected type
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        
        # Handle nullable types (e.g., ["string", "null"])
        if isinstance(expected_type, list):
            return any(self._validate_type(value, t) for t in expected_type)
        
        if expected_type in type_mapping:
            expected_python_type = type_mapping[expected_type]
            return isinstance(value, expected_python_type)
        
        # Default to True for unknown types
        return True

    def estimate_cost(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> float:
        """
        Estimate the cost of executing this node.
        
        Override this method for nodes that have associated costs
        (e.g., API calls to OpenAI, Anthropic, etc.).
        
        Args:
            inputs: Input data
            config: Node configuration
            
        Returns:
            Estimated cost in USD (default: 0.0)
        """
        return 0.0

    def get_metadata(self) -> NodeMetadata:
        """
        Get metadata about this node type.
        
        This method constructs NodeMetadata from the node's attributes
        and schema. Override if you need custom metadata.
        
        Returns:
            NodeMetadata object
        """
        from backend.core.models import NodeInputSchema, NodeOutputSchema
        
        # Convert input schema to NodeInputSchema objects
        input_schema = self.get_input_schema()
        inputs = []
        for name, schema_info in input_schema.items():
            # Handle nullable types (JSON schema uses ['string', 'null'] format)
            schema_type = schema_info.get('type', 'any')
            if isinstance(schema_type, list):
                # Extract the non-null type (first non-null value)
                schema_type = next((t for t in schema_type if t != 'null'), schema_type[0] if schema_type else 'any')
            
            inputs.append(NodeInputSchema(
                name=name,
                type=str(schema_type) if schema_type else 'any',
                description=schema_info.get('description') or schema_info.get('title'),
                required=schema_info.get('required', False),
            ))
        
        # Convert output schema to NodeOutputSchema objects
        output_schema = self.get_output_schema()
        outputs = []
        for name, schema_info in output_schema.items():
            # Handle nullable types (JSON schema uses ['string', 'null'] format)
            schema_type = schema_info.get('type', 'any')
            if isinstance(schema_type, list):
                # Extract the non-null type (first non-null value)
                schema_type = next((t for t in schema_type if t != 'null'), schema_type[0] if schema_type else 'any')
            
            outputs.append(NodeOutputSchema(
                name=name,
                type=str(schema_type) if schema_type else 'any',
                description=schema_info.get('description'),
            ))
        
        return NodeMetadata(
            type=self.node_type,
            name=self.name or self.node_type,
            description=self.description or f"{self.name} node",
            category=self.category or "misc",
            inputs=inputs,
            outputs=outputs,
            config_schema=self.get_schema(),
        )

    def get_input_schema(self) -> Dict[str, Any]:
        """
        Get schema for node inputs.
        
        Override this method to define what inputs the node expects.
        This is used for validation and frontend display.
        
        Returns:
            Dictionary describing input schema
        """
        return {}

    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get schema for node outputs.
        
        Override this method to define what outputs the node produces.
        This is used for validation and frontend display.
        
        Returns:
            Dictionary describing output schema
        """
        return {}

    async def stream_event(
        self,
        event_type: str,
        node_id: str,
        data: Dict[str, Any],
        agent: Optional[str] = None,
        task: Optional[str] = None,
    ) -> None:
        """Publish a streaming event (if execution_id is set)."""
        if not self.execution_id:
            return
        
        from backend.core.streaming import StreamEvent, StreamEventType, stream_manager
        
        # Convert string event type to enum
        try:
            event_type_enum = StreamEventType(event_type)
        except ValueError:
            # If event type is not valid, default to LOG
            logger.warning(f"Invalid event type '{event_type}', defaulting to LOG")
            event_type_enum = StreamEventType.LOG
        
        event = StreamEvent(
            event_type=event_type_enum,
            node_id=node_id,
            execution_id=self.execution_id,
            agent=agent,
            task=task,
            data=data,
        )
        await stream_manager.publish(event)
    
    async def stream_progress(
        self,
        node_id: str,
        progress: float,
        message: Optional[str] = None,
    ) -> None:
        """Stream progress update (0.0 to 1.0)."""
        await self.stream_event(
            "node_progress",
            node_id,
            {"progress": progress, "message": message},
        )
    
    async def stream_output(
        self,
        node_id: str,
        output: Any,
        partial: bool = False,
    ) -> None:
        """Stream output update."""
        await self.stream_event(
            "node_output",
            node_id,
            {"output": output, "partial": partial},
        )
    
    async def stream_log(
        self,
        node_id: str,
        message: str,
        level: str = "info",
    ) -> None:
        """Stream a log message."""
        await self.stream_event(
            "log",
            node_id,
            {"message": message, "level": level},
        )

    async def execute_safe(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the node with error handling.
        
        This is a wrapper around execute() that provides consistent
        error handling and logging.
        
        Args:
            inputs: Input data
            config: Node configuration
            
        Returns:
            Node output data
            
        Raises:
            NodeExecutionError: If execution fails
        """
        try:
            # Validate configuration
            self.validate(config)

            # Log execution start
            logger.debug(f"Executing node {self.node_type} with config: {config}")

            # Execute the node
            result = await self.execute(inputs, config)

            # Log execution success
            logger.debug(f"Node {self.node_type} executed successfully")

            return result

        except NodeValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            logger.error(f"Node {self.node_type} execution failed: {e}", exc_info=True)
            raise NodeExecutionError(
                f"Execution failed: {str(e)}",
                node_type=self.node_type,
                original_error=e,
            ) from e

    def __repr__(self) -> str:
        """String representation of the node."""
        return f"{self.__class__.__name__}(type={self.node_type}, name={self.name})"

