"""
Code execution tool implementation.
"""

import sys
import io
import math
from typing import Dict, Any, Callable


def get_code_execution_schema() -> Dict[str, Any]:
    """Get schema fields for code execution tool."""
    return {
        "code_execution_language": {
            "type": "string",
            "enum": ["python", "javascript"],
            "default": "python",
            "title": "Language",
            "description": "Programming language for code execution",
        },
        "code_execution_timeout": {
            "type": "integer",
            "default": 10,
            "minimum": 1,
            "maximum": 60,
            "title": "Timeout (seconds)",
            "description": "Maximum execution time in seconds",
        },
    }


def create_code_execution_tool(config: Dict[str, Any]) -> Callable[[str], str]:
    """Create code execution tool function."""
    def code_exec_func(code: str) -> str:
        """Execute code in a sandboxed environment."""
        language = config.get("code_execution_language", "python")
        timeout = config.get("code_execution_timeout", 10)
        
        if language == "python":
            try:
                # Restricted builtins for safety
                safe_builtins = {
                    'abs': abs, 'all': all, 'any': any, 'bool': bool,
                    'dict': dict, 'float': float, 'int': int, 'len': len,
                    'list': list, 'max': max, 'min': min, 'range': range,
                    'round': round, 'str': str, 'sum': sum, 'tuple': tuple,
                    'type': type, 'zip': zip, 'enumerate': enumerate,
                    'sorted': sorted, 'reversed': reversed,
                }
                
                # Safe globals with math module
                safe_globals = {
                    '__builtins__': safe_builtins,
                    'math': math,
                    '__name__': '__main__',
                }
                
                # Capture stdout
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                
                try:
                    # Execute code
                    exec(code, safe_globals)
                    output = buffer.getvalue()
                    return output if output else "Code executed successfully (no output)"
                finally:
                    sys.stdout = old_stdout
                    
            except Exception as e:
                return f"Error: {str(e)}"
        elif language == "javascript":
            # For JavaScript, we'd need Node.js subprocess
            # This is a placeholder - would need proper sandboxing
            return "Error: JavaScript execution not yet fully implemented. Use Python for now."
        else:
            return f"Error: Language {language} not yet supported"
    
    return code_exec_func

