"""
Calculator tool implementation.
"""

import math
import re
from typing import Dict, Any, Callable


def get_calculator_schema() -> Dict[str, Any]:
    """Get schema fields for calculator tool."""
    return {
        "calculator_allowed_operations": {
            "type": "string",
            "default": "all",
            "title": "Allowed Operations",
            "description": "Mathematical operations allowed (all, basic, advanced)",
        },
    }


def create_calculator_tool(config: Dict[str, Any]) -> Callable[[str], str]:
    """Create calculator tool function."""
    def calculator_func(expression: str) -> str:
        """Evaluate a mathematical expression safely."""
        try:
            # Clean expression
            expression = expression.strip()
            
            # Allowed operations based on config
            allowed_ops = config.get("calculator_allowed_operations", "all")
            
            # Only allow safe mathematical operations
            if allowed_ops == "basic":
                allowed_chars = set("0123456789+-*/()., ")
            elif allowed_ops == "advanced":
                allowed_chars = set("0123456789+-*/()., ^sqrtlogsinco")
            else:  # all
                allowed_chars = set("0123456789+-*/()., ^sqrtlogsinco")
            
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression"
            
            # Replace common math functions
            expression = expression.replace("^", "**")
            expression = re.sub(r'sqrt\(([^)]+)\)', r'math.sqrt(\1)', expression)
            expression = re.sub(r'log\(([^)]+)\)', r'math.log(\1)', expression)
            expression = re.sub(r'sin\(([^)]+)\)', r'math.sin(\1)', expression)
            expression = re.sub(r'cos\(([^)]+)\)', r'math.cos(\1)', expression)
            
            # Safe evaluation with math module
            safe_dict = {"__builtins__": {}, "math": math}
            result = eval(expression, safe_dict)
            
            # Format result
            if isinstance(result, float):
                if result.is_integer():
                    return str(int(result))
                return f"{result:.6f}".rstrip('0').rstrip('.')
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    return calculator_func

