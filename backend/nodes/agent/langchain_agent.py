"""
LangChain Agent Node for NodeAI.

This node creates an AI agent using LangChain's ReAct framework.
The agent can use tools to perform actions and make decisions.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
import json

# For type hints when Tool might not be available
if TYPE_CHECKING:
    try:
        from langchain.tools import Tool
    except ImportError:
        try:
            from langchain_core.tools import Tool
        except ImportError:
            Tool = Any  # type: ignore
else:
    Tool = Any  # Will be set properly in the try/except below

from backend.nodes.base import BaseNode
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.config import settings
from backend.core.secret_resolver import resolve_api_key
from backend.utils.logger import get_logger
from backend.utils.model_pricing import (
    calculate_llm_cost,
    get_available_models,
    ModelType,
)

logger = get_logger(__name__)

# Import Tool first - try all possible locations
Tool = None
try:
    from langchain_core.tools import Tool
except ImportError:
    try:
        from langchain.tools import Tool
    except ImportError:
        Tool = Any  # Fallback for type hints

# Try old API first
try:
    from langchain.agents import initialize_agent, AgentType
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    # Ensure Tool is imported
    if Tool is None or Tool == Any:
        try:
            from langchain.tools import Tool
        except ImportError:
            pass
    LANGCHAIN_AVAILABLE = True
    LANGCHAIN_NEW_API = False
except ImportError:
    try:
        # Try newer API
        from langchain.agents import AgentExecutor, create_react_agent
        from langchain.prompts import PromptTemplate
        # Ensure Tool is imported
        if Tool is None or Tool == Any:
            try:
                from langchain_core.tools import Tool
            except ImportError:
                try:
                    from langchain.tools import Tool
                except ImportError:
                    Tool = Any
        LANGCHAIN_NEW_API = True
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        LANGCHAIN_NEW_API = False
        if Tool is None:
            Tool = Any
        logger.warning("LangChain not available. Install langchain and langchain-openai to use agent nodes.")


class LangChainAgentNode(BaseNode):
    """
    LangChain Agent Node.
    
    Creates an AI agent that can:
    - Use tools to perform actions
    - Make decisions based on reasoning
    - Show reasoning steps
    """

    node_type = "langchain_agent"
    name = "LangChain Agent"
    description = "AI agent with ReAct reasoning and tool capabilities"
    category = "agent"

    def __init__(self):
        """Initialize the agent node."""
        super().__init__()
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is required for agent nodes. "
                "Install with: pip install langchain langchain-openai langchain-anthropic"
            )

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the agent node.
        
        The agent receives a task/query and uses available tools to complete it.
        """
        if not LANGCHAIN_AVAILABLE:
            raise ValueError("LangChain is not available. Please install required packages.")

        provider = config.get("provider", "openai")
        model = config.get("openai_model") or config.get("anthropic_model") or "gpt-3.5-turbo"
        temperature = config.get("temperature", 0.7)
        max_iterations = config.get("max_iterations", 5)
        verbose = config.get("verbose", True)
        
        # Get task/query from inputs or config
        task = inputs.get("task") or inputs.get("query") or config.get("task") or config.get("query")
        if not task:
            raise ValueError("Task or query is required for agent execution")
        
        # Get node ID for streaming (from config, will be set by engine)
        # If not provided, use a default (engine should set this)
        node_id = config.get("_node_id", "langchain_agent")
        
        # Stream agent started
        await self.stream_event(
            "agent_started",
            node_id,
            {"task": task, "provider": provider, "model": model},
        )
        
        # Get tools from inputs (from Tool nodes) or create default tools
        tools = self._get_tools(inputs, config)
        
        # Stream tool information
        if tools:
            await self.stream_log(
                node_id,
                f"Agent has access to {len(tools)} tool(s): {', '.join([t.name for t in tools])}",
            )
        
        # Create LLM based on provider (pass config to allow API keys from node configuration)
        llm = self._create_llm(provider, model, temperature, config)
        
        # Create ReAct agent
        agent = self._create_agent(llm, tools, verbose)
        
        # Stream initial progress
        await self.stream_progress(node_id, 0.1, "Agent initialized, starting reasoning...")
        
        # Execute agent
        try:
            result = await self._run_agent(agent, task, max_iterations, verbose, node_id)
            
            # Extract token usage and calculate cost
            cost = 0.0
            tokens_used = {"input": 0, "output": 0, "total": 0}
            
            # Try to get token usage from result (set by _run_agent)
            if result.get("_token_usage"):
                tokens_used = result["_token_usage"]
                cost = self._calculate_cost(provider, model, tokens_used["input"], tokens_used["output"])
            else:
                # Fallback: Try to extract from llm_output
                if result.get("llm_output") and isinstance(result.get("llm_output"), dict):
                    llm_output = result.get("llm_output", {})
                    if "token_usage" in llm_output:
                        token_usage = llm_output["token_usage"]
                        tokens_used = {
                            "input": token_usage.get("prompt_tokens", 0),
                            "output": token_usage.get("completion_tokens", 0),
                            "total": token_usage.get("total_tokens", 0),
                        }
                        cost = self._calculate_cost(provider, model, tokens_used["input"], tokens_used["output"])
                else:
                    # Last resort: Estimate from input/output length
                    output_text = str(result.get("output", ""))
                    input_tokens = len(task) // 4  # Rough: 1 token ≈ 4 chars
                    output_tokens = len(output_text) // 4
                    tokens_used = {
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": input_tokens + output_tokens,
                    }
                    cost = self._calculate_cost(provider, model, input_tokens, output_tokens)
            
            return {
                "output": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "tool_calls": self._format_tool_calls(result.get("intermediate_steps", [])),
                "reasoning": result.get("reasoning", ""),
                "provider": provider,
                "model": model,
                "tokens_used": tokens_used,
                "cost": cost,
            }
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            raise ValueError(f"Agent execution failed: {str(e)}")

    def _create_llm(self, provider: str, model: str, temperature: float, config: Dict[str, Any] = None):
        """Create LLM instance based on provider."""
        config = config or {}
        
        user_id = config.get("_user_id")
        
        if provider == "openai":
            # Resolve API key from vault, config, or settings
            api_key = resolve_api_key(config, "openai_api_key", user_id=user_id)
            if not api_key:
                raise ValueError("OpenAI API key not found. Please configure it in the node settings or environment variables.")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key,
            )
        elif provider == "anthropic":
            # Resolve API key from vault, config, or settings
            api_key = resolve_api_key(config, "anthropic_api_key", user_id=user_id)
            if not api_key:
                raise ValueError("Anthropic API key not found. Please configure it in the node settings or environment variables.")
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                api_key=api_key,
            )
        elif provider == "gemini" or provider == "google":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                # Use API key from config if provided, otherwise fall back to environment variable
                api_key = config.get("gemini_api_key") or settings.gemini_api_key
                if not api_key:
                    raise ValueError("Gemini API key is required. Provide it in the node configuration or set GEMINI_API_KEY environment variable.")
                return ChatGoogleGenerativeAI(
                    model=model,
                    temperature=temperature,
                    google_api_key=api_key,
                )
            except ImportError:
                raise ValueError(
                    "langchain-google-genai not installed. Install with: pip install langchain-google-genai"
                )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _get_tools(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> List[Any]:
        """Get tools for the agent."""
        tools = []
        
        # Add graph query tools if Knowledge Graph node is connected
        graph_tools = self._get_graph_tools(inputs, config)
        if graph_tools:
            tools.extend(graph_tools)
            logger.info(f"Added {len(graph_tools)} graph query tool(s) from Knowledge Graph node")
        
        # Check if tools are provided in inputs (from connected Tool nodes)
        # Tool nodes output: {"tool_id": "...", "tool_name": "...", "tool_type": "...", ...}
        tool_outputs = []
        
        # Look for tool outputs in inputs (from connected Tool nodes)
        # Tool nodes output with keys like "tool_{tool_id}" and also at root level
        for key, value in inputs.items():
            if key.startswith("tool_") and isinstance(value, dict) and value.get("tool_id"):
                # This is a tool output from a Tool node (using unique key)
                tool_outputs.append(value)
            elif isinstance(value, dict) and value.get("tool_id") and key != "tool_id":
                # This is a tool output at root level
                tool_outputs.append(value)
            elif isinstance(value, list):
                # Handle list of tool outputs (if execution engine collects them)
                for item in value:
                    if isinstance(item, dict) and item.get("tool_id"):
                        tool_outputs.append(item)
        
        # Also check if the entire input dict itself is a tool output (backward compatibility)
        if isinstance(inputs, dict) and inputs.get("tool_id") and inputs not in tool_outputs:
            # Check if this is actually a tool output (has registered field or tool_name)
            if inputs.get("registered") or inputs.get("tool_name"):
                tool_outputs.append(inputs)
        
        # Convert tool outputs to LangChain Tool objects
        for tool_output in tool_outputs:
            # Import ToolNode to get tool definition
            try:
                from backend.nodes.tools.tool_node import ToolNode
                tool_id = tool_output.get("tool_id")
                if tool_id:
                    tool_def = ToolNode.get_tool_definition(tool_id)
                    
                    if tool_def:
                        langchain_tool = ToolNode.create_langchain_tool(tool_def)
                        if langchain_tool:
                            tools.append(langchain_tool)
                            logger.info(f"Added tool from Tool node: {tool_def.get('name')}")
            except ImportError:
                logger.warning("ToolNode not available")
            except Exception as e:
                logger.warning(f"Error loading tool: {e}")
        
        # If no tools from Tool nodes, check config
        if not tools:
            tools_data = config.get("tools", [])
            if tools_data:
                for tool_data in tools_data:
                    if isinstance(tool_data, dict):
                        tool = self._create_tool_from_dict(tool_data)
                        if tool:
                            tools.append(tool)
        
        # Always include calculator as fallback if no tools
        if not tools:
            tools.append(self._create_calculator_tool())
            logger.info("Using default calculator tool (no tools provided)")
        
        return tools

    def _create_tool_from_dict(self, tool_data: Dict[str, Any]) -> Optional[Any]:
        """Create a LangChain Tool from a dictionary."""
        if not LANGCHAIN_AVAILABLE or Tool is None:
            logger.warning("LangChain Tool not available")
            return None
            
        tool_type = tool_data.get("type")
        name = tool_data.get("name", "unknown")
        description = tool_data.get("description", "")
        
        if tool_type == "calculator":
            return self._create_calculator_tool()
        elif tool_type == "web_search":
            # Placeholder - would need actual search API
            return Tool(
                name="web_search",
                func=lambda query: f"Search results for: {query} (web search not implemented yet)",
                description="Search the web for information. Input should be a search query.",
            )
        elif tool_type == "custom":
            func_str = tool_data.get("function")
            if func_str:
                # For now, just return a placeholder
                return Tool(
                    name=name,
                    func=lambda x: f"Custom tool result for: {x}",
                    description=description,
                )
        
        return None

    def _create_calculator_tool(self) -> Any:
        """Create a calculator tool."""
        def calculator(expression: str) -> str:
            """Evaluate a mathematical expression safely."""
            try:
                # Only allow safe mathematical operations
                allowed_chars = set("0123456789+-*/()., ")
                if not all(c in allowed_chars for c in expression):
                    return "Error: Invalid characters in expression"
                
                result = eval(expression)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        if not LANGCHAIN_AVAILABLE or Tool is None:
            raise ValueError("LangChain Tool not available. Cannot create calculator tool.")
        return Tool(
            name="calculator",
            func=calculator,
            description="Evaluates mathematical expressions. Input should be a valid mathematical expression like '2+2' or '10*5'.",
        )

    def _create_agent(self, llm, tools: List[Any], verbose: bool):
        """Create a ReAct agent."""
        try:
            # Try new API first
            if 'LANGCHAIN_NEW_API' in globals() and LANGCHAIN_NEW_API:
                from langchain.agents import AgentExecutor, create_react_agent
                from langchain.prompts import PromptTemplate
                
                prompt = PromptTemplate.from_template("""
You are a helpful AI assistant that can use tools to answer questions.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
""")
                
                agent = create_react_agent(llm, tools, prompt)
                executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    verbose=verbose,
                    handle_parsing_errors=True,
                )
                return executor
        except:
            pass
        
        # Fallback to older API
        try:
            from langchain.agents import initialize_agent, AgentType
            agent = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=verbose,
                handle_parsing_errors=True,
            )
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise ValueError(f"Could not create agent. LangChain version may be incompatible: {e}")

    async def _run_agent(self, agent, task: str, max_iterations: int, verbose: bool, node_id: str) -> Dict[str, Any]:
        """Run the agent and return results with streaming support."""
        import asyncio
        
        # Track token usage
        token_usage = {"input": 0, "output": 0, "total": 0}
        step_count = 0
        events_to_stream = []  # Collect events to stream after execution
        
        def run_sync():
            nonlocal step_count, events_to_stream
            # Try new API (invoke) with streaming support
            if hasattr(agent, 'invoke'):
                result = agent.invoke({"input": task})
                
                # Collect intermediate steps for streaming
                if isinstance(result, dict) and 'intermediate_steps' in result:
                    intermediate_steps = result.get('intermediate_steps', [])
                    total_steps = len(intermediate_steps)
                    
                    for i, step in enumerate(intermediate_steps):
                        step_count += 1
                        progress = 0.2 + (i / max(total_steps, 1)) * 0.6  # 20% to 80%
                        
                        if len(step) >= 2:
                            action, observation = step[0], step[1]
                            
                            # Extract action details
                            tool_name = None
                            tool_input = None
                            if hasattr(action, 'tool'):
                                tool_name = action.tool
                                tool_input = getattr(action, 'tool_input', None)
                            elif isinstance(action, dict):
                                tool_name = action.get('tool')
                                tool_input = action.get('tool_input')
                            
                            # Collect tool call event
                            if tool_name:
                                events_to_stream.append((
                                    "agent_tool_called",
                                    {
                                        "tool": tool_name,
                                        "input": str(tool_input) if tool_input else "",
                                        "step": step_count,
                                    },
                                ))
                            
                            # Collect observation event
                            if observation:
                                events_to_stream.append((
                                    "log",
                                    {"message": f"Tool result: {str(observation)[:100]}..."},
                                ))
                        
                        # Collect progress event
                        events_to_stream.append((
                            "node_progress",
                            {
                                "progress": progress,
                                "message": f"Step {step_count}/{total_steps} completed",
                            },
                        ))
                
                # Try to extract token usage from result
                if isinstance(result, dict):
                    # Check for llm_output in result
                    if 'llm_output' in result and result['llm_output']:
                        llm_output = result['llm_output']
                        if 'token_usage' in llm_output:
                            usage = llm_output['token_usage']
                            token_usage['input'] = usage.get('prompt_tokens', 0)
                            token_usage['output'] = usage.get('completion_tokens', 0)
                            token_usage['total'] = usage.get('total_tokens', 0)
                    # Also check intermediate_steps for token usage
                    if 'intermediate_steps' in result:
                        for step in result.get('intermediate_steps', []):
                            if len(step) >= 2:
                                action_result = step[1]
                                if isinstance(action_result, dict) and 'llm_output' in action_result:
                                    llm_out = action_result['llm_output']
                                    if 'token_usage' in llm_out:
                                        usage = llm_out['token_usage']
                                        token_usage['input'] += usage.get('prompt_tokens', 0)
                                        token_usage['output'] += usage.get('completion_tokens', 0)
                                        token_usage['total'] += usage.get('total_tokens', 0)
                return result
            # Try old API (run)
            elif hasattr(agent, 'run'):
                output = agent.run(task)
                return {"output": output, "intermediate_steps": []}
            else:
                raise ValueError("Agent does not support invoke or run methods")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_sync)
        
        # Stream collected events
        for event_type, event_data in events_to_stream:
            if event_type == "node_progress":
                await self.stream_progress(node_id, event_data["progress"], event_data.get("message"))
            elif event_type == "log":
                await self.stream_log(node_id, event_data["message"])
            else:
                await self.stream_event(event_type, node_id, event_data)
        
        # Stream final output
        if isinstance(result, dict):
            output = result.get("output", "")
            if output:
                await self.stream_output(node_id, str(output)[:500], partial=False)
            
            # Stream completion
            await self.stream_progress(node_id, 0.9, "Agent reasoning complete")
            await self.stream_event(
                "agent_completed",
                node_id,
                {"steps": step_count, "output_length": len(str(output))},
            )
        
        # Add token usage to result if we found it
        if isinstance(result, dict) and any(token_usage.values()):
            result['_token_usage'] = token_usage
        
        return result

    def _format_tool_calls(self, intermediate_steps: List) -> List[Dict[str, Any]]:
        """Format tool calls for output."""
        formatted = []
        for step in intermediate_steps:
            if len(step) >= 2:
                action, observation = step[0], step[1]
                tool_name = action.tool if hasattr(action, 'tool') else (getattr(action, 'tool', None) or str(action))
                tool_input = action.tool_input if hasattr(action, 'tool_input') else (getattr(action, 'tool_input', None) or str(action))
                formatted.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "output": str(observation),
                })
        return formatted

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for agent configuration."""
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "enum": ["openai", "anthropic", "gemini"],
                    "default": "openai",
                    "title": "Provider",
                    "description": "LLM provider for the agent",
                },
                "openai_model": {
                    "type": "string",
                    "enum": self._get_openai_model_list(),
                    "default": "gpt-4o-mini",
                    "title": "OpenAI Model",
                    "description": "OpenAI model to use",
                },
                "anthropic_model": {
                    "type": "string",
                    "enum": self._get_anthropic_model_list(),
                    "default": "claude-sonnet-4-5-20250929",
                    "title": "Anthropic Model",
                    "description": "Anthropic model to use",
                },
                "gemini_model": {
                    "type": "string",
                    "enum": self._get_gemini_model_list(),
                    "default": "gemini-2.5-flash",
                    "title": "Gemini Model",
                    "description": "Google Gemini model to use",
                },
                "openai_api_key": {
                    "type": "string",
                    "title": "OpenAI API Key",
                    "description": "OpenAI API key (optional, uses environment variable if not provided)",
                },
                "anthropic_api_key": {
                    "type": "string",
                    "title": "Anthropic API Key",
                    "description": "Anthropic API key (optional, uses environment variable if not provided)",
                },
                "gemini_api_key": {
                    "type": "string",
                    "title": "Gemini API Key",
                    "description": "Google Gemini API key (optional, uses environment variable if not provided)",
                },
                "temperature": {
                    "type": "number",
                    "default": 0.7,
                    "minimum": 0.0,
                    "maximum": 2.0,
                    "title": "Temperature",
                    "description": "Sampling temperature",
                },
                "max_iterations": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                    "title": "Max Iterations",
                    "description": "Maximum number of reasoning steps",
                },
                "verbose": {
                    "type": "boolean",
                    "default": True,
                    "title": "Verbose",
                    "description": "Show reasoning steps",
                },
                "task": {
                    "type": "string",
                    "title": "Task",
                    "description": "Task or question for the agent",
                },
            },
            "required": ["provider"],
        }

    def _get_openai_model_list(self) -> List[str]:
        """Get list of available OpenAI LLM models from pricing system."""
        try:
            models = get_available_models(provider="openai", model_type=ModelType.LLM)
            return [model.model_id for model in models if not (model.metadata or {}).get("deprecated", False)]
        except Exception as e:
            logger.warning(f"Failed to get OpenAI models from pricing system: {e}")
            return ["gpt-5.1", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
    
    def _get_anthropic_model_list(self) -> List[str]:
        """Get list of available Anthropic Claude LLM models from pricing system."""
        try:
            models = get_available_models(provider="anthropic", model_type=ModelType.LLM)
            return [
                model.model_id for model in models 
                if not (model.metadata or {}).get("deprecated", False)
                and not (model.metadata or {}).get("is_alias", False)
            ]
        except Exception as e:
            logger.warning(f"Failed to get Anthropic models from pricing system: {e}")
            return ["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001", "claude-opus-4-1-20250805"]
    
    def _get_gemini_model_list(self) -> List[str]:
        """Get list of available Gemini LLM models from pricing system."""
        try:
            models = get_available_models(provider="gemini", model_type=ModelType.LLM)
            return [model.model_id for model in models if not (model.metadata or {}).get("deprecated", False)]
        except Exception as e:
            logger.warning(f"Failed to get Gemini models from pricing system: {e}")
            return ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]

    def _calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on provider and model using centralized pricing."""
        return calculate_llm_cost(provider, model, input_tokens, output_tokens)

    def estimate_cost(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> float:
        """Estimate cost based on provider and input size."""
        provider = config.get("provider", "openai")
        model = (
            config.get("openai_model") or 
            config.get("anthropic_model") or 
            config.get("gemini_model") or 
            "gpt-3.5-turbo"
        )
        
        # Rough estimation based on task length
        task = inputs.get("task") or inputs.get("query") or config.get("task") or config.get("query") or ""
        estimated_tokens = len(task) / 4  # Rough: 1 token ≈ 4 chars
        
        # Estimate output tokens (assume similar to input for agent reasoning)
        estimated_output = estimated_tokens * 0.5  # Agents typically use less output
        
        return self._calculate_cost(provider, model, int(estimated_tokens), int(estimated_output))


# Register the node (only if LangChain is available)
if LANGCHAIN_AVAILABLE:
    try:
        NodeRegistry.register(
            LangChainAgentNode.node_type,
            LangChainAgentNode,
            LangChainAgentNode().get_metadata(),
        )
        logger.info("LangChain agent node registered successfully")
    except Exception as e:
        logger.warning(f"Failed to register LangChain agent node: {e}")
        # Don't fail - node just won't be available
else:
    logger.debug("LangChain agent node not registered - LangChain not available")

