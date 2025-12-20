# New Nodes Data Flow & LLM Integration Guide

## How Data Flows Between Nodes

### 1. Text Input Node Output
The `text_input` node outputs:
```python
{
    "text": "user entered text",
    "metadata": {...}
}
```

### 2. Workflow Engine Data Mapping
The workflow engine (`_collect_node_inputs`) automatically maps outputs to inputs:

**Direct mappings:**
- `text_input` → `inputs["text"]`
- `text_input` → `inputs["output"]` (extracted from nested structure)
- `text_input` → `inputs["query"]` (fallback)
- `text_input` → `inputs["content"]` (fallback)
- `text_input` → `inputs["body"]` (fallback)

**Node ID mapping:**
- If source is `text_input` node with ID `text_input_brand`, data is also available as `inputs["text_input_brand"]`

### 3. How New Nodes Should Receive Data

**Best Practice:** Accept multiple field names for flexibility:

```python
# ✅ GOOD - Flexible input handling
data = (
    inputs.get("data") or 
    inputs.get("text") or 
    inputs.get("content") or 
    inputs.get("output") or
    ""
)

# ❌ BAD - Only accepts one field name
data = inputs.get("data", "")
```

## LLM Provider & Vault Integration

### 1. Two Patterns for LLM Configuration

There are two patterns in the codebase, both using the same underlying `resolve_api_key()` function:

#### Pattern A: LLMConfigMixin (Recommended for Simple LLM Calls)
For nodes that make direct LLM API calls (like `smart_data_analyzer`, `blog_generator`):

```python
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin

class MyNode(BaseNode, LLMConfigMixin):
    async def execute(self, inputs, config):
        # Resolve LLM config (handles vault, API keys, provider selection)
        llm_config = self._resolve_llm_config(config)
        
        # Call LLM using direct SDK calls
        response = await self._call_llm(prompt, llm_config, max_tokens=2000)
        
        # Estimate cost
        cost = self._estimate_llm_cost(prompt, response, llm_config)
```

#### Pattern B: Direct resolve_api_key() (Used in CrewAI/Advanced NLP)
For nodes that use LangChain or other frameworks:

```python
from backend.core.secret_resolver import resolve_api_key

class MyNode(BaseNode):
    def _create_llm(self, provider, model, temperature, config):
        user_id = config.get("_user_id")
        
        if provider == "openai":
            api_key = resolve_api_key(config, "openai_api_key", user_id=user_id)
            if not api_key:
                raise ValueError("OpenAI API key not found")
            # Create LangChain LLM or other framework instance
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model, temperature=temperature, api_key=api_key)
```

**Both patterns use the same underlying system!** The difference is:
- **LLMConfigMixin**: Wraps everything in helper methods, uses direct SDK calls
- **Direct pattern**: More control, used for LangChain/agent frameworks

### 2. How API Key Resolution Works

**API Key Resolution Priority (same for both patterns):**
1. **Vault Secret** - If `openai_api_key_secret_id` is in config, retrieves from vault
2. **Direct Config** - If `openai_api_key` is in config, uses that value
3. **Environment Variable** - Falls back to `settings.openai_api_key`

The `resolve_api_key()` function automatically checks for `{key_name}_secret_id` first, then the direct key.

**Provider Selection:**
- Config: `provider: "openai" | "anthropic" | "gemini"`
- Model selection: `openai_model`, `anthropic_model`, `gemini_model` (or fallback `model` field)
- Temperature: `temperature` (default: 0.1 for mixin, 0.7 for CrewAI)

### 3. Required Config Schema

Include LLM config in your node's `get_schema()`:

```python
def get_schema(self):
    base_schema = {
        "type": "object",
        "properties": {
            # Your node-specific properties
            "analysis_type": {...},
            # ... other properties
        }
    }
    
    # Merge with LLM schema
    llm_schema = self._get_llm_schema_section()
    base_schema["properties"].update(llm_schema)
    
    return base_schema
```

### 4. User ID for Vault Access

The workflow engine automatically adds `_user_id` to config:
```python
# In engine.py
node_config["_user_id"] = self._user_id
```

So `_resolve_llm_config()` can access vault secrets for that user.

## Common Issues & Fixes

### Issue 1: "API key not found"
**Cause:** Node not using LLMConfigMixin or vault not configured
**Fix:** 
- Inherit from `LLMConfigMixin`
- Use `_resolve_llm_config(config)` instead of direct API key access
- Ensure `_user_id` is in config (engine adds this automatically)

### Issue 2: "Data input is required" when connected to text_input
**Cause:** Node expects specific field name (e.g., "data") but text_input provides "text"
**Fix:** Accept multiple field names:
```python
data = inputs.get("data") or inputs.get("text") or inputs.get("content") or ""
```

### Issue 3: Node not receiving data from connected nodes
**Cause:** Input field name mismatch
**Fix:** 
- Check what the source node outputs (see `get_output_schema()`)
- Accept multiple common field names
- Use intelligent routing if enabled

## Example: Complete Node with LLM

```python
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin

class MyLLMNode(BaseNode, LLMConfigMixin):
    node_type = "my_llm_node"
    name = "My LLM Node"
    category = "intelligence"
    
    async def execute(self, inputs, config):
        # 1. Get inputs flexibly
        text = (
            inputs.get("text") or 
            inputs.get("content") or 
            inputs.get("data") or
            inputs.get("output") or
            ""
        )
        
        if not text:
            raise NodeValidationError("Text input required")
        
        # 2. Resolve LLM config (handles vault, API keys)
        llm_config = self._resolve_llm_config(config)
        
        # 3. Create prompt
        prompt = f"Analyze this: {text}"
        
        # 4. Call LLM
        response = await self._call_llm(prompt, llm_config, max_tokens=2000)
        
        # 5. Return result
        return {
            "analysis": response,
            "metadata": {
                "model": llm_config["model"],
                "provider": llm_config["provider"]
            }
        }
    
    def get_schema(self):
        # Include LLM config in schema
        schema = {
            "type": "object",
            "properties": {
                # Your custom properties
                "custom_setting": {
                    "type": "string",
                    "title": "Custom Setting"
                }
            }
        }
        
        # Add LLM config
        llm_schema = self._get_llm_schema_section()
        schema["properties"].update(llm_schema)
        
        return schema
```

