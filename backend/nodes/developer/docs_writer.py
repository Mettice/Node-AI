"""
Documentation Writer Node - Code → automatic README/docs
"""

from typing import Any, Dict
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeValidationError, NodeExecutionError
from backend.core.node_registry import NodeRegistry


class DocsWriterNode(BaseNode, LLMConfigMixin):
    node_type = "docs_writer"
    name = "Documentation Writer"
    description = "Automatically generates documentation from code"
    category = "developer"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute documentation generation with LLM support"""
        try:
            # Get inputs - accept multiple field names
            code_input = (
                inputs.get("code") or
                inputs.get("text") or
                inputs.get("content") or
                inputs.get("output") or
                ""
            )
            doc_type = config.get("doc_type", "readme")
            
            if not code_input:
                raise NodeValidationError("Code input is required. Connect a text_input node or provide code in config.")

            # Try to use LLM if available
            use_llm = False
            llm_config = None
            
            try:
                llm_config = self._resolve_llm_config(config)
                if llm_config.get("api_key"):
                    use_llm = True
            except Exception:
                use_llm = False

            if use_llm and llm_config:
                # Use LLM for better documentation generation
                try:
                    if doc_type == "readme":
                        documentation = await self._generate_llm_readme(code_input, llm_config)
                    elif doc_type == "api_docs":
                        documentation = await self._generate_llm_api_docs(code_input, llm_config)
                    else:
                        documentation = await self._generate_llm_general_docs(code_input, llm_config)
                    sections = await self._extract_doc_sections(documentation)
                except Exception as e:
                    # Fallback to pattern-based if LLM fails
                    await self.stream_log("docs_writer", f"LLM generation failed, using pattern matching: {e}", "warning")
                    if doc_type == "readme":
                        documentation = self._generate_readme(code_input)
                    elif doc_type == "api_docs":
                        documentation = self._generate_api_docs(code_input)
                    else:
                        documentation = self._generate_general_docs(code_input)
                    sections = ["Installation", "Usage", "API Reference", "Contributing"]
            else:
                # Use pattern-based fallback
                if doc_type == "readme":
                    documentation = self._generate_readme(code_input)
                elif doc_type == "api_docs":
                    documentation = self._generate_api_docs(code_input)
                else:
                    documentation = self._generate_general_docs(code_input)
                sections = ["Installation", "Usage", "API Reference", "Contributing"]

            return {
                "documentation": documentation,
                "doc_type": doc_type,
                "sections": sections
            }
        except Exception as e:
            raise NodeExecutionError(f"Documentation generation failed: {str(e)}")

    def _generate_readme(self, code: str) -> str:
        return f"""# Project Title

## Description
Generated documentation for the project.

## Installation
```bash
npm install
```

## Usage
```javascript
// Example usage based on code analysis
{code[:200]}...
```

## Contributing
Please read our contributing guidelines.
"""

    def _generate_api_docs(self, code: str) -> str:
        return "## API Documentation\n\nGenerated API documentation based on code analysis."

    def _generate_general_docs(self, code: str) -> str:
        return "# Documentation\n\nAutomatically generated documentation."

    async def _generate_llm_readme(self, code: str, llm_config: Dict[str, Any]) -> str:
        """Generate README using LLM"""
        # Truncate code if too long
        code_preview = code[:8000] if len(code) > 8000 else code
        if len(code) > 8000:
            code_preview += "\n\n[Code truncated for length...]"
        
        prompt = f"""Generate a comprehensive README.md file for this code.

Code:
```python
{code_preview}
```

Generate a complete README with:
1. Project title and description
2. Installation instructions
3. Usage examples
4. API/Function documentation
5. Contributing guidelines
6. License section (if applicable)

Make it professional, clear, and helpful for developers who want to use this code."""
        
        llm_response = await self._call_llm(prompt, llm_config, max_tokens=2000)
        return llm_response.strip()

    async def _generate_llm_api_docs(self, code: str, llm_config: Dict[str, Any]) -> str:
        """Generate API documentation using LLM"""
        code_preview = code[:8000] if len(code) > 8000 else code
        if len(code) > 8000:
            code_preview += "\n\n[Code truncated for length...]"
        
        prompt = f"""Generate comprehensive API documentation for this code.

Code:
```python
{code_preview}
```

Generate API documentation with:
1. Overview of the API
2. Function/Class documentation with:
   - Description
   - Parameters/Arguments
   - Return values
   - Example usage
3. Code examples
4. Error handling

Format it clearly with proper headings and code blocks."""
        
        llm_response = await self._call_llm(prompt, llm_config, max_tokens=2000)
        return llm_response.strip()

    async def _generate_llm_general_docs(self, code: str, llm_config: Dict[str, Any]) -> str:
        """Generate general documentation using LLM"""
        code_preview = code[:8000] if len(code) > 8000 else code
        if len(code) > 8000:
            code_preview += "\n\n[Code truncated for length...]"
        
        prompt = f"""Generate comprehensive documentation for this code.

Code:
```python
{code_preview}
```

Generate documentation that explains:
1. What the code does
2. How it works
3. Key components and their purposes
4. Usage examples
5. Important notes or considerations

Make it clear and easy to understand for developers."""
        
        llm_response = await self._call_llm(prompt, llm_config, max_tokens=2000)
        return llm_response.strip()

    async def _extract_doc_sections(self, documentation: str) -> list:
        """Extract section headings from documentation"""
        import re
        # Find markdown headings
        headings = re.findall(r'^#+\s+(.+)$', documentation, re.MULTILINE)
        return headings[:10]  # Limit to 10 sections

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "doc_type": {
                    "type": "string",
                    "title": "Documentation Type",
                    "description": "Type of documentation to generate",
                    "enum": ["readme", "api_docs", "general"],
                    "default": "readme"
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "code": {
                "type": "string",
                "title": "Source Code",
                "description": "Code to generate documentation for",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "documentation": {"type": "string", "description": "Generated documentation"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        code_input = inputs.get("code", "")
        return 0.01 + (len(code_input) / 1000 * 0.005)


# Register the node
NodeRegistry.register(
    "docs_writer",
    DocsWriterNode,
    DocsWriterNode().get_metadata(),
)