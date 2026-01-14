"""
CrewAI Agent Node for NodeAI.

This node creates a multi-agent crew that can work together on tasks.
"""

from typing import Any, Dict, List, Optional
import json
import asyncio
import os
import threading

from backend.nodes.base import BaseNode

# Lock for thread-safe environment variable modification during CrewAI execution
# This prevents race conditions when multiple CrewAI nodes run concurrently
_crewai_env_lock = threading.Lock()
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.utils.logger import get_logger
from backend.config import settings
from backend.core.secret_resolver import resolve_api_key
from backend.core.agent_lightning import get_agent_lightning_wrapper, calculate_simple_reward
from backend.utils.model_pricing import (
    calculate_llm_cost,
    get_available_models,
    ModelType,
)
from backend.nodes.agent.crewai_event_listener import CrewAIStreamingEventListener

logger = get_logger(__name__)


class CrewAINode(BaseNode):
    """
    CrewAI Node for multi-agent coordination.
    
    Creates a crew of agents that work together on tasks.
    """

    node_type = "crewai_agent"
    name = "CrewAI Agent"
    description = "Multi-agent crew that coordinates multiple agents to work together on tasks"
    category = "agent"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the CrewAI node.
        
        Creates a crew of agents and executes tasks.
        """
        # Check if CrewAI is installed
        try:
            from crewai import Agent, Task, Crew, Process
        except ImportError:
            raise ValueError(
                "CrewAI not installed. Install with: pip install crewai[tools]"
            )

        # Get node ID for streaming (from config, set by engine)
        node_id = config.get("_node_id", "crewai_agent")
        
        provider = config.get("provider", "openai")
        # Handle provider-specific model selection
        if provider == "openai":
            model = config.get("openai_model") or config.get("model", "gpt-4")
        elif provider == "anthropic":
            model = config.get("anthropic_model") or config.get("model", "claude-3-sonnet-20240229")
        elif provider == "gemini" or provider == "google":
            model = config.get("gemini_model") or config.get("model", "gemini-2.5-flash")
        else:
            model = config.get("model", "gpt-4")
        
        temperature = config.get("temperature", 0.7)
        max_iterations = config.get("max_iterations", 3)
        verbose = config.get("verbose", False)
        
        # Get task description from inputs or config
        task_description = inputs.get("task") or inputs.get("text") or config.get("task", "")
        
        # Create LLM (pass config to allow API keys from node configuration)
        llm = self._create_llm(provider, model, temperature, config)
        
        # Get agents configuration - can be JSON string or array
        agents_config = config.get("agents", [])
        if isinstance(agents_config, str):
            try:
                agents_config = json.loads(agents_config)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in agents configuration")
        
        if not agents_config or len(agents_config) == 0:
            raise ValueError("At least one agent must be configured")
        
        # Create agents
        agents = []
        for agent_config in agents_config:
            agent = self._create_agent(agent_config, llm, inputs, config)
            agents.append(agent)
        
        # Create tasks - can be JSON string or array
        tasks_config = config.get("tasks", [])
        if isinstance(tasks_config, str):
            try:
                tasks_config = json.loads(tasks_config)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in tasks configuration")
        
        if not tasks_config or len(tasks_config) == 0:
            # Create a default task from the task description
            if not task_description:
                raise ValueError("Task description is required. Provide it in inputs, config, or define tasks.")
            tasks_config = [{
                "description": task_description,
                "agent": agents[0].role if agents else "agent",
            }]
        
        tasks = []
        for task_config in tasks_config:
            task = self._create_task(task_config, agents, inputs)
            tasks.append(task)
        
        # Prepare inputs for CrewAI - format all inputs as strings for interpolation
        crew_inputs = {}
        if inputs:
            for key, value in inputs.items():
                if isinstance(value, (str, int, float)):
                    crew_inputs[key] = str(value)
                elif isinstance(value, dict):
                    # Convert dict to JSON string
                    try:
                        crew_inputs[key] = json.dumps(value)
                    except:
                        crew_inputs[key] = str(value)
                elif isinstance(value, list):
                    # Convert list to comma-separated string or JSON
                    try:
                        crew_inputs[key] = json.dumps(value)
                    except:
                        crew_inputs[key] = ", ".join(str(v) for v in value)
        
        # Create crew with callbacks for streaming
        process = config.get("process", "sequential")
        
        # Create and register CrewAI event listener for streaming
        # This captures agent activities, thoughts, tool usage, etc.
        # The listener will auto-register when instantiated (via BaseEventListener.__init__)
        event_listener = None
        try:
            # Get the main event loop to pass to the listener
            # This allows the listener to schedule coroutines from worker threads
            main_loop = None
            try:
                main_loop = asyncio.get_running_loop()
            except RuntimeError:
                try:
                    main_loop = asyncio.get_event_loop()
                except RuntimeError:
                    logger.warning("No event loop available for event listener")
            
            event_listener = CrewAIStreamingEventListener(
                node_instance=self,
                node_id=node_id,
                execution_id=self.execution_id,
                main_event_loop=main_loop
            )
            logger.info(f"CrewAI event listener created for node {node_id}")
        except Exception as e:
            logger.warning(f"Failed to create event listener: {e}, falling back to callbacks", exc_info=True)
        
        # Define callbacks for streaming agent actions (fallback if event listener fails)
        # Note: CrewAI callbacks are synchronous, so we need to properly schedule async operations
        # Get the running event loop (asyncio already imported at top of file)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        # Create a mapping of task descriptions to agents for callback use
        task_to_agent = {}
        for task in tasks:
            # Get the agent assigned to this task
            agent = getattr(task, 'agent', None)
            if agent:
                task_to_agent[task.description] = agent.role if hasattr(agent, 'role') else str(agent)
            else:
                # If no agent assigned, use the first agent as fallback
                task_to_agent[task.description] = agents[0].role if agents else "agent"
        
        # Track task completion for progress updates
        completed_tasks = []
        total_tasks = len(tasks)
        
        def task_callback(task_output):
            """Callback when a task completes.
            
            Note: CrewAI passes TaskOutput object, not Task object.
            TaskOutput typically has: raw, description (sometimes), but not agent.
            We need to match it back to the original task to get agent info.
            """
            if not self.execution_id:
                return
                
            try:
                # Extract task description from output
                # TaskOutput might have description, or we can get it from raw
                task_description = None
                
                # Try different ways to get the task description
                if hasattr(task_output, 'description') and task_output.description:
                    task_description = task_output.description
                elif hasattr(task_output, 'task') and task_output.task:
                    task_description = task_output.task
                elif hasattr(task_output, 'raw'):
                    # Sometimes description is in raw
                    raw = task_output.raw
                    if isinstance(raw, str):
                        # Use first 100 chars as description
                        task_description = raw[:100] + "..." if len(raw) > 100 else raw
                    elif isinstance(raw, dict) and 'description' in raw:
                        task_description = raw['description']
                
                # Fallback: try to match by checking all tasks
                if not task_description:
                    # Try to find matching task by checking task outputs
                    for task in tasks:
                        # This is a best-effort match
                        task_description = task.description
                        break  # Use first task as fallback
                
                if not task_description:
                    task_description = "Unknown task"
                
                # Get agent role from our mapping
                agent_role = task_to_agent.get(task_description, None)
                
                # If not found in mapping, try to get from task_output (unlikely but try)
                if not agent_role:
                    # TaskOutput doesn't have agent, but we can try
                    if hasattr(task_output, 'agent'):
                        agent_obj = getattr(task_output, 'agent', None)
                        if agent_obj:
                            agent_role = agent_obj.role if hasattr(agent_obj, 'role') else str(agent_obj)
                
                # Final fallback
                if not agent_role:
                    agent_role = agents[0].role if agents else "agent"
                
                # Track completed task for progress
                completed_tasks.append(task_description)
                
                # Calculate progress: start at 20%, end at 90%, with tasks in between
                progress = 0.2 + (len(completed_tasks) / total_tasks) * 0.7
                
                # Schedule async operations on the event loop
                # CrewAI callbacks are sync, so we need to schedule coroutines properly
                # Use the main event loop if available (from event_listener)
                try:
                    # Try to get the main event loop (should be set when listener was created)
                    loop = None
                    if event_listener and hasattr(event_listener, 'listener') and hasattr(event_listener.listener, 'main_event_loop'):
                        loop = event_listener.listener.main_event_loop
                    
                    if not loop:
                        try:
                            loop = asyncio.get_running_loop()
                        except RuntimeError:
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                logger.debug("No event loop available for task_callback (event listener should handle this)")
                                return
                    
                    if loop and loop.is_running():
                        # Schedule the coroutines to run on the event loop
                        asyncio.run_coroutine_threadsafe(
                            self.stream_progress(
                                node_id,
                                progress,
                                f"Task {len(completed_tasks)}/{total_tasks} completed by {agent_role}"
                            ),
                            loop
                        )
                        asyncio.run_coroutine_threadsafe(
                            self.stream_event(
                                "task_completed",
                                node_id,
                                {"task": task_description, "agent": agent_role},
                                agent=agent_role,
                                task=task_description,
                            ),
                            loop
                        )
                except Exception as stream_error:
                    logger.debug(f"Error streaming progress from task_callback: {stream_error} (event listener should handle this)")
            except Exception as e:
                # Don't let callback errors break execution
                logger.warning(f"Error in task_callback: {e}", exc_info=True)
        
        def step_callback(step):
            """Callback for agent steps (thinking, tool calls, etc.)."""
            if not self.execution_id:
                return
            
            # Extract agent info from step
            agent_name = getattr(step, 'agent', None)
            if agent_name:
                agent_name = agent_name.role if hasattr(agent_name, 'role') else str(agent_name)
            
            # Stream agent thinking
            if hasattr(step, 'thought') or hasattr(step, 'reasoning'):
                thought = getattr(step, 'thought', None) or getattr(step, 'reasoning', None)
                if thought:
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.run_coroutine_threadsafe(
                                self.stream_event(
                                    "agent_thinking",
                                    node_id,
                                    {"thought": str(thought)},
                                    agent=agent_name,
                                ),
                                loop
                            )
                    except Exception:
                        pass
            
            # Stream tool calls
            if hasattr(step, 'tool') and step.tool:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            self.stream_event(
                                "agent_tool_called",
                                node_id,
                                {"tool": step.tool, "input": getattr(step, 'tool_input', {})},
                                agent=agent_name,
                            ),
                            loop
                        )
                except Exception:
                    pass
        
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential if process == "sequential" else Process.hierarchical,
            verbose=verbose,
            task_callback=task_callback,
            step_callback=step_callback,
        )
        
        # Stream agent started events
        for agent in agents:
            if self.execution_id:
                await self.stream_event(
                    "agent_started",
                    node_id,
                    {"agent": agent.role, "goal": agent.goal},
                    agent=agent.role,
                )
        
        # Execute crew
        logger.info(f"Executing CrewAI crew with {len(agents)} agents and {len(tasks)} tasks")
        
        # Stream initial progress
        await self.stream_progress(node_id, 0.1, "Starting CrewAI execution...")
        
        # Stream progress for crew setup
        await self.stream_progress(node_id, 0.2, f"Running {len(agents)} agents on {len(tasks)} tasks...")
        
        # Execute crew with progress monitoring
        # CrewAI execution is synchronous, so we run it in an executor to avoid blocking
        import warnings
        import concurrent.futures
        # asyncio already imported at top of file

        # Create executor for running CrewAI
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        # Capture API key info for thread-safe environment variable setting
        # CrewAI/LiteLLM internally looks for env vars, not the passed api_key
        api_key_for_env = getattr(self, '_current_api_key', None)
        env_var_name = getattr(self, '_current_env_var', None)

        def execute_crew():
            """Execute CrewAI in a separate thread with proper env var handling."""
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)

                # Set environment variable for CrewAI's internal LiteLLM calls
                # Use lock to prevent race conditions in multi-tenant environment
                if api_key_for_env and env_var_name:
                    with _crewai_env_lock:
                        # Store original value
                        original_value = os.environ.get(env_var_name)
                        try:
                            # Set the API key for this execution
                            os.environ[env_var_name] = api_key_for_env
                            logger.debug(f"Set {env_var_name} for CrewAI execution")
                            # Pass inputs to crew.kickoff() so CrewAI can interpolate them into task descriptions
                            return crew.kickoff(inputs=crew_inputs if crew_inputs else None)
                        finally:
                            # Restore original value
                            if original_value is not None:
                                os.environ[env_var_name] = original_value
                            elif env_var_name in os.environ:
                                del os.environ[env_var_name]
                            logger.debug(f"Restored {env_var_name} after CrewAI execution")
                else:
                    # Fallback: run without setting env var (will use existing env if any)
                    return crew.kickoff(inputs=crew_inputs if crew_inputs else None)

        # Submit the crew execution
        future = executor.submit(execute_crew)
        
        # Simulate progress updates while crew is running
        progress_steps = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9]
        step_messages = [
            "Agent analyzing task...",
            "Generating response...",
            "Processing information...",
            "Continuing execution...",
            "Working on tasks...",
            "Finalizing outputs...",
            "Almost done...",
            "Completing execution..."
        ]
        
        step_idx = 0
        while not future.done():
            # Stream progress update
            if step_idx < len(progress_steps):
                await self.stream_progress(
                    node_id, 
                    progress_steps[step_idx],
                    step_messages[step_idx]
                )
                step_idx += 1
            
            # IMPORTANT: Use asyncio.sleep instead of future.result(timeout)
            # This allows the event loop to process other tasks (like streaming)
            await asyncio.sleep(3.0)
        
        # Get the result
        result = future.result()
        
        # Cleanup executor
        executor.shutdown(wait=False)
        
        # Stream completion progress
        await self.stream_progress(node_id, 0.95, "Processing results...")
        
        # Extract token usage from CrewAI's usage_metrics
        tokens_used = {"input": 0, "output": 0, "total": 0}
        cost = 0.0
        per_agent_tokens = {}  # Initialize per-agent token tracking
        
        if hasattr(crew, 'usage_metrics') and crew.usage_metrics:
            usage = crew.usage_metrics
            logger.info(f"CrewAI usage_metrics: {usage}")
            
            # CrewAI usage_metrics is a Pydantic model, access attributes directly
            total_tokens = getattr(usage, 'total_tokens', None) or getattr(usage, 'total', 0) or 0
            prompt_tokens = getattr(usage, 'prompt_tokens', None) or getattr(usage, 'input_tokens', None) or getattr(usage, 'prompt', 0) or 0
            completion_tokens = getattr(usage, 'completion_tokens', None) or getattr(usage, 'output_tokens', None) or getattr(usage, 'completion', 0) or 0
            
            # If we have total but not breakdown, estimate 70/30 split
            if total_tokens > 0 and prompt_tokens == 0 and completion_tokens == 0:
                prompt_tokens = int(total_tokens * 0.7)
                completion_tokens = int(total_tokens * 0.3)
            
            tokens_used = {
                "input": prompt_tokens,
                "output": completion_tokens,
                "total": total_tokens or (prompt_tokens + completion_tokens),
            }
            logger.info(f"CrewAI token usage extracted: {tokens_used}")
            
            # Try to distribute tokens per agent if we have task outputs
            if hasattr(result, 'tasks_output') and result.tasks_output and total_tokens > 0:
                num_tasks = len(result.tasks_output)
                if num_tasks > 0:
                    for task_output in result.tasks_output:
                        agent_role = None
                        if hasattr(task_output, 'agent') and task_output.agent:
                            agent_obj = task_output.agent
                            agent_role = getattr(agent_obj, 'role', None) or str(agent_obj)
                        
                        if agent_role:
                            per_agent_tokens[agent_role] = {
                                "input": prompt_tokens // num_tasks,
                                "output": completion_tokens // num_tasks,
                                "total": total_tokens // num_tasks,
                            }
        
        # Calculate cost using actual token usage if available
        if tokens_used["total"] > 0:
            cost = self._calculate_cost_from_tokens(provider, model, tokens_used["input"], tokens_used["output"])
            logger.info(f"CrewAI cost calculated from tokens: ${cost:.4f}")
        else:
            # Fallback to estimation if no metrics available
            cost = self._calculate_cost(provider, model, result, max_iterations)
            logger.warning("No token usage metrics from CrewAI, using cost estimation")
            logger.info(f"CrewAI estimated cost: ${cost:.4f}")
        
        # Format the result nicely
        result_text = str(result)
        
        # Agent Lightning integration (optional)
        agl_wrapper = get_agent_lightning_wrapper(config)
        if agl_wrapper.enabled:
            try:
                # Calculate reward based on result quality
                result_dict = {
                    "output": result_text,
                    "tokens_used": tokens_used,
                    "cost": cost,
                }
                reward = calculate_simple_reward(result_dict)
                agl_wrapper.emit_reward(reward, {
                    "node_id": node_id,
                    "provider": provider,
                    "model": model,
                    "tokens_used": tokens_used,
                })
                logger.info(f"Agent Lightning reward emitted: {reward}")
            except Exception as e:
                logger.warning(f"Failed to emit Agent Lightning reward: {e}")
        
        # Stream the full output with token information
        # Also stream per-agent token information
        for agent_role, agent_tokens in per_agent_tokens.items():
            await self.stream_event(
                "agent_completed",
                node_id,
                {
                    "agent": agent_role,
                    "tokens_used": agent_tokens,
                    "input_tokens": agent_tokens.get("input", 0),
                    "output_tokens": agent_tokens.get("output", 0),
                    "total_tokens": agent_tokens.get("total", 0),
                },
                agent=agent_role,
            )
        
        # Extract individual agent outputs from CrewAI result BEFORE sending node_output event
        agent_outputs = {}
        if hasattr(result, 'tasks_output') and result.tasks_output:
            logger.info(f"Extracting agent outputs from {len(result.tasks_output)} task outputs")
            
            # Also try to get agent outputs from crew.tasks_output if available
            crew_tasks_output = None
            if hasattr(crew, 'tasks_output') and crew.tasks_output:
                crew_tasks_output = crew.tasks_output
                logger.info(f"Found crew.tasks_output with {len(crew_tasks_output)} tasks")
            
            # Use crew.tasks_output if available, otherwise use result.tasks_output
            tasks_to_process = crew_tasks_output if crew_tasks_output else result.tasks_output
            
            for idx, task_output in enumerate(tasks_to_process):
                agent_role = None
                task_desc = None
                output_text = None
                
                # Get agent role - try multiple methods with more fallbacks
                if hasattr(task_output, 'agent') and task_output.agent:
                    agent_obj = task_output.agent
                    if hasattr(agent_obj, 'role'):
                        agent_role = agent_obj.role
                    elif hasattr(agent_obj, 'name'):
                        agent_role = agent_obj.name
                    else:
                        agent_role = str(agent_obj)
                elif hasattr(task_output, 'agent_role'):
                    agent_role = task_output.agent_role
                elif hasattr(task_output, 'agent_name'):
                    agent_role = task_output.agent_name
                
                # If we still don't have agent_role, try to match from tasks
                if not agent_role and hasattr(task_output, 'task') and task_output.task:
                    task_obj = task_output.task
                    if hasattr(task_obj, 'agent') and task_obj.agent:
                        agent_obj = task_obj.agent
                        if hasattr(agent_obj, 'role'):
                            agent_role = agent_obj.role
                        elif hasattr(agent_obj, 'name'):
                            agent_role = agent_obj.name
                
                # Get task description
                if hasattr(task_output, 'task') and task_output.task:
                    task_obj = task_output.task
                    if hasattr(task_obj, 'description'):
                        task_desc = task_obj.description
                    elif hasattr(task_obj, 'name'):
                        task_desc = task_obj.name
                    else:
                        task_desc = str(task_obj)
                elif hasattr(task_output, 'task_description'):
                    task_desc = task_output.task_description
                elif hasattr(task_output, 'task_name'):
                    task_desc = task_output.task_name
                
                # Get output text - try multiple methods with more fallbacks
                if hasattr(task_output, 'raw') and task_output.raw:
                    output_text = str(task_output.raw)
                elif hasattr(task_output, 'output') and task_output.output:
                    output_text = str(task_output.output)
                elif hasattr(task_output, 'description') and task_output.description:
                    output_text = str(task_output.description)
                elif hasattr(task_output, 'summary') and task_output.summary:
                    output_text = str(task_output.summary)
                elif hasattr(task_output, 'result') and task_output.result:
                    output_text = str(task_output.result)
                elif hasattr(task_output, 'content') and task_output.content:
                    output_text = str(task_output.content)
                
                logger.info(f"Task output {idx}: agent={agent_role}, task={task_desc}, has_output={bool(output_text)}, output_length={len(output_text) if output_text else 0}")
                
                # Only add if we have both agent_role and output_text
                if agent_role and output_text:
                    if agent_role not in agent_outputs:
                        agent_outputs[agent_role] = []
                    agent_outputs[agent_role].append({
                        "task": task_desc or f"Task {idx + 1}",
                        "output": output_text,
                    })
                elif agent_role:
                    logger.warning(f"Task output {idx} has agent_role '{agent_role}' but no output text")
                elif output_text:
                    logger.warning(f"Task output {idx} has output text but no agent_role")
            
            logger.info(f"Extracted agent outputs for {len(agent_outputs)} agents: {list(agent_outputs.keys())}")
            for role, outputs in agent_outputs.items():
                logger.info(f"  - {role}: {len(outputs)} task(s)")
        
        # Fallback: If we have agents but no outputs for some, create empty entries
        # This ensures all agents are represented in the output
        if agents and len(agent_outputs) < len(agents):
            agent_roles_in_output = set(agent_outputs.keys())
            for agent in agents:
                agent_role = agent.role
                if agent_role not in agent_roles_in_output:
                    logger.warning(f"Agent '{agent_role}' has no outputs extracted, creating empty entry")
                    agent_outputs[agent_role] = []
        
        logger.info(f"Final agent outputs count: {len(agent_outputs)} agents")
        
        # Agent Lightning integration (optional)
        agl_wrapper = get_agent_lightning_wrapper(config)
        if agl_wrapper.enabled:
            try:
                # Calculate reward based on result quality
                result_dict = {
                    "output": result_text,
                    "tokens_used": tokens_used,
                    "cost": cost,
                }
                reward = calculate_simple_reward(result_dict)
                agl_wrapper.emit_reward(reward, {
                    "node_id": node_id,
                    "provider": provider,
                    "model": model,
                    "tokens_used": tokens_used,
                    "cost": cost,
                })
            except Exception as e:
                logger.warning(f"Agent Lightning reward calculation failed: {e}")
        
        # Stream node_output event WITH agent_outputs included
        await self.stream_event(
            "node_output",
            node_id,
            {
                "output": result_text,
                "partial": False,
                "tokens_used": tokens_used,
                "agent_outputs": agent_outputs,  # Include agent outputs in the event
                "agents": [agent.role for agent in agents],
                "tasks": [task.description for task in tasks],
                "per_agent_tokens": per_agent_tokens,
            },
        )
        await self.stream_progress(node_id, 1.0, "CrewAI execution completed")
        
        # Return structured output with the report
        return {
            "report": result_text,  # The main output - CrewAI report
            "output": result_text,  # Also keep 'output' for compatibility
            "agents": [agent.role for agent in agents],
            "tasks": [task.description for task in tasks],
            "agent_outputs": agent_outputs,  # Individual agent outputs
            "per_agent_tokens": per_agent_tokens,  # Token usage per agent
            "provider": provider,
            "model": model,
            "cost": cost,
            "tokens_used": tokens_used,
            "summary": f"CrewAI execution completed with {len(agents)} agents and {len(tasks)} tasks. Cost: ${cost:.4f}"
        }

    def _create_llm(self, provider: str, model: str, temperature: float, config: Dict[str, Any] = None):
        """Create LLM instance based on provider."""
        config = config or {}

        user_id = config.get("_user_id")

        # Store provider for later use in execute_crew
        self._current_provider = provider

        if provider == "openai":
            # Resolve API key from vault, config, or settings (in that order)
            # In production, users should configure via node settings or vault, not env vars
            api_key = resolve_api_key(config, "openai_api_key", user_id=user_id, fallback_to_settings=True)
            if not api_key:
                raise ValueError(
                    "OpenAI API key not found. Please configure it in the CrewAI node settings:\n"
                    "1. Open the CrewAI node properties\n"
                    "2. Enter your OpenAI API key in the 'OpenAI API Key' field, OR\n"
                    "3. Select a key from your Secrets Vault\n"
                    "Note: In production, API keys should be configured per-node or via vault, not environment variables."
                )
            # Store API key for CrewAI's internal LiteLLM calls
            self._current_api_key = api_key
            self._current_env_var = "OPENAI_API_KEY"
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                raise ValueError(
                    "langchain-openai not installed. Install with: pip install langchain-openai"
                )
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key,
            )
        elif provider == "anthropic":
            # Use API key from config if provided, otherwise fall back to environment variable
            api_key = resolve_api_key(config, "anthropic_api_key", user_id=user_id, fallback_to_settings=True)
            if not api_key:
                raise ValueError(
                    "Anthropic API key not found. Please configure it in the CrewAI node settings:\n"
                    "1. Open the CrewAI node properties\n"
                    "2. Enter your Anthropic API key in the 'Anthropic API Key' field, OR\n"
                    "3. Select a key from your Secrets Vault\n"
                    "Note: In production, API keys should be configured per-node or via vault, not environment variables."
                )
            # Store API key for CrewAI's internal LiteLLM calls
            self._current_api_key = api_key
            self._current_env_var = "ANTHROPIC_API_KEY"
            try:
                from langchain_anthropic import ChatAnthropic
            except ImportError:
                raise ValueError(
                    "langchain-anthropic not installed. Install with: pip install langchain-anthropic"
                )
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                api_key=api_key,
            )
        elif provider == "gemini" or provider == "google":
            # Use API key from config if provided, otherwise fall back to environment variable
            api_key = resolve_api_key(config, "gemini_api_key", user_id=user_id, fallback_to_settings=True)
            if not api_key:
                raise ValueError(
                    "Gemini API key not found. Please configure it in the CrewAI node settings:\n"
                    "1. Open the CrewAI node properties\n"
                    "2. Enter your Gemini API key in the 'Gemini API Key' field, OR\n"
                    "3. Select a key from your Secrets Vault\n"
                    "Note: In production, API keys should be configured per-node or via vault, not environment variables."
                )
            # Store API key for CrewAI's internal LiteLLM calls
            self._current_api_key = api_key
            self._current_env_var = "GEMINI_API_KEY"
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError:
                raise ValueError(
                    "langchain-google-genai not installed. Install with: pip install langchain-google-genai"
                )
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                google_api_key=api_key,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _create_agent(self, agent_config: Dict[str, Any], llm, inputs: Dict[str, Any], config: Dict[str, Any]):
        """Create a CrewAI Agent from configuration."""
        try:
            from crewai import Agent
            from backend.nodes.tools.tool_node import ToolNode
        except ImportError:
            raise ValueError("CrewAI or ToolNode not available")

        role = agent_config.get("role", "Agent")
        goal = agent_config.get("goal", "")
        backstory = agent_config.get("backstory", "")
        tools_config = agent_config.get("tools", [])
        
        # Get tools from connected Tool nodes
        tools = []
        
        # Note: CrewAI 1.5.0 has strict tool validation that doesn't support LangChain tools
        # For now, we'll skip external tool nodes and only use config-defined tools
        # TODO: Upgrade to CrewAI 2.x which has better LangChain compatibility
        
        has_external_tools = False
        
        # Check if graph tools are connected
        graph_tools = self._get_graph_tools(inputs, config)
        if graph_tools:
            has_external_tools = True
            logger.warning(
                f"Knowledge Graph tools detected but skipped. "
                f"CrewAI 1.5.0 doesn't support external tool integration. "
                f"Consider upgrading to CrewAI 2.x for full tool support."
            )
        
        # Check if Tool nodes are connected
        for key, value in inputs.items():
            if key.startswith("tool_") and isinstance(value, dict) and value.get("tool_id"):
                has_external_tools = True
                tool_id = value.get("tool_id")
                logger.warning(
                    f"External tool '{tool_id}' detected but skipped. "
                    f"CrewAI 1.5.0 doesn't support external tool integration. "
                    f"Consider upgrading to CrewAI 2.x for full tool support."
                )
        
        # Only load tools from config (these are CrewAI native tools)
        if tools_config:
            for tool_data in tools_config:
                if isinstance(tool_data, dict):
                    tool = self._create_tool_from_dict(tool_data)
                    if tool:
                        tools.append(tool)
        
        # CrewAI requires tools to be a list, not None
        # Pass empty list if no tools are available
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools if tools else [],  # Empty list instead of None
            llm=llm,
            verbose=True,
        )

    def _create_task(self, task_config: Dict[str, Any], agents: List, inputs: Dict[str, Any] = None):
        """Create a CrewAI Task from configuration."""
        try:
            from crewai import Task
        except ImportError:
            raise ValueError("CrewAI not available")

        description = task_config.get("description", "")
        agent_role = task_config.get("agent", "")
        expected_output = task_config.get("expected_output", "Complete the task successfully")
        
        # Substitute placeholders in description and expected_output with input values
        # Common placeholders: {research_topic}, {text}, {task}, {input}, {content_type}, {brand_info}, etc.
        if inputs:
            # Get the research topic/text from inputs (fallback chain)
            research_topic = (
                inputs.get("text") or 
                inputs.get("task") or 
                inputs.get("input") or 
                inputs.get("research_topic") or 
                ""
            )
            
            # Get specific inputs for common template placeholders
            content_type = inputs.get("content_type") or inputs.get("text_input_content_type") or ""
            brand_info = inputs.get("brand_info") or inputs.get("text_input_brand") or ""
            
            # Replace all placeholders using Python string formatting
            # This supports both {placeholder} and {placeholder:format} syntax
            # Exclude keys we're already passing explicitly to avoid conflicts
            explicit_keys = {"research_topic", "text", "task", "input", "content_type", "brand_info"}
            additional_inputs = {
                k: str(v) for k, v in inputs.items() 
                if isinstance(v, (str, int, float)) and k not in explicit_keys
            }
            
            try:
                # First, try to format with all available inputs
                description = description.format(
                    research_topic=research_topic,
                    text=research_topic,
                    task=research_topic,
                    input=research_topic,
                    content_type=content_type,
                    brand_info=brand_info,
                    **additional_inputs
                )
            except (KeyError, ValueError) as e:
                # If formatting fails, fall back to simple replacement for common placeholders
                logger.debug(f"String formatting failed, using simple replacement: {e}")
                description = description.replace("{research_topic}", research_topic)
                description = description.replace("{text}", research_topic)
                description = description.replace("{task}", research_topic)
                description = description.replace("{input}", research_topic)
                description = description.replace("{content_type}", content_type)
                description = description.replace("{brand_info}", brand_info)
            
            # Also replace in expected_output
            try:
                expected_output = expected_output.format(
                    research_topic=research_topic,
                    text=research_topic,
                    task=research_topic,
                    input=research_topic,
                    content_type=content_type,
                    brand_info=brand_info,
                    **additional_inputs
                )
            except (KeyError, ValueError) as e:
                # Fall back to simple replacement
                logger.debug(f"String formatting failed for expected_output, using simple replacement: {e}")
                expected_output = expected_output.replace("{research_topic}", research_topic)
                expected_output = expected_output.replace("{text}", research_topic)
                expected_output = expected_output.replace("{task}", research_topic)
                expected_output = expected_output.replace("{input}", research_topic)
                expected_output = expected_output.replace("{content_type}", content_type)
                expected_output = expected_output.replace("{brand_info}", brand_info)
        
        # Find agent by role
        assigned_agent = None
        for agent in agents:
            if agent.role == agent_role:
                assigned_agent = agent
                break
        
        if not assigned_agent and agents:
            assigned_agent = agents[0]  # Default to first agent
        
        if not assigned_agent:
            raise ValueError("No agent available for task assignment")
        
        return Task(
            description=description,
            agent=assigned_agent,
            expected_output=expected_output,
        )

    def _create_tool_from_dict(self, tool_data: Dict[str, Any]):
        """Create a LangChain Tool from a dictionary."""
        try:
            from langchain.tools import Tool
        except ImportError:
            return None

        tool_type = tool_data.get("type")
        name = tool_data.get("name", "unknown")
        description = tool_data.get("description", "")
        
        if tool_type == "calculator":
            def calculator_func(expression: str) -> str:
                try:
                    result = eval(expression)
                    return str(result)
                except Exception as e:
                    return f"Error: {str(e)}"
            
            return Tool(
                name=name,
                func=calculator_func,
                description=description,
            )
        
        return None

    def _get_openai_model_list(self) -> List[str]:
        """Get list of available OpenAI LLM models from pricing system."""
        try:
            models = get_available_models(provider="openai", model_type=ModelType.LLM)
            model_list = [model.model_id for model in models if not (model.metadata or {}).get("deprecated", False)]
            if not model_list:
                logger.warning("No OpenAI LLM models found in pricing system, using fallback list")
                return ["gpt-5.1", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
            logger.debug(f"Found {len(model_list)} OpenAI LLM models: {model_list[:5]}...")
            return model_list
        except Exception as e:
            logger.warning(f"Failed to get OpenAI models from pricing system: {e}", exc_info=True)
            return ["gpt-5.1", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
    
    def _get_anthropic_model_list(self) -> List[str]:
        """Get list of available Anthropic Claude LLM models from pricing system."""
        try:
            models = get_available_models(provider="anthropic", model_type=ModelType.LLM)
            model_list = [
                model.model_id for model in models 
                if not (model.metadata or {}).get("deprecated", False)
                and not (model.metadata or {}).get("is_alias", False)
            ]
            if not model_list:
                logger.warning("No Anthropic LLM models found in pricing system, using fallback list")
                return ["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001", "claude-opus-4-1-20250805"]
            logger.debug(f"Found {len(model_list)} Anthropic LLM models: {model_list[:5]}...")
            return model_list
        except Exception as e:
            logger.warning(f"Failed to get Anthropic models from pricing system: {e}", exc_info=True)
            return ["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001", "claude-opus-4-1-20250805"]
    
    def _get_gemini_model_list(self) -> List[str]:
        """Get list of available Gemini LLM models from pricing system."""
        try:
            models = get_available_models(provider="gemini", model_type=ModelType.LLM)
            model_list = [model.model_id for model in models if not (model.metadata or {}).get("deprecated", False)]
            if not model_list:
                logger.warning("No Gemini LLM models found in pricing system, using fallback list")
                return ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]
            logger.debug(f"Found {len(model_list)} Gemini LLM models: {model_list[:5]}...")
            return model_list
        except Exception as e:
            logger.warning(f"Failed to get Gemini models from pricing system: {e}", exc_info=True)
            return ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]

    def _calculate_cost_from_tokens(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost from actual token usage using centralized pricing."""
        return calculate_llm_cost(provider, model, input_tokens, output_tokens)

    def _calculate_cost(self, provider: str, model: str, result: Any, max_iterations: int) -> float:
        """Calculate execution cost."""
        # Estimate cost based on result length and iterations
        # This is a rough estimate - CrewAI doesn't expose token usage directly
        result_str = str(result)
        estimated_tokens = len(result_str.split()) * 1.3  # Rough token estimate
        
        # Estimate input/output split (70/30)
        input_tokens = int(estimated_tokens * 0.7 * max_iterations)
        output_tokens = int(estimated_tokens * 0.3 * max_iterations)
        
        return calculate_llm_cost(provider, model, input_tokens, output_tokens)

    def _get_graph_tools(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> List:
        """
        Get graph query tools if Knowledge Graph node is connected.
        
        Checks for Knowledge Graph node outputs in inputs and creates
        LangChain Tool wrappers for the graph query tools.
        """
        try:
            from backend.nodes.retrieval.graph_tools import GraphQueryTools
            from langchain.tools import Tool
            
            # Check if we have Knowledge Graph connection info
            neo4j_uri = config.get("neo4j_uri") or inputs.get("neo4j_uri")
            neo4j_user = config.get("neo4j_user") or inputs.get("neo4j_user")
            neo4j_password = config.get("neo4j_password") or inputs.get("neo4j_password")
            
            # Also check environment variables
            if not neo4j_uri:
                neo4j_uri = getattr(settings, "neo4j_uri", None)
            if not neo4j_user:
                neo4j_user = getattr(settings, "neo4j_user", None)
            if not neo4j_password:
                neo4j_password = getattr(settings, "neo4j_password", None)
            
            # If no Neo4j connection info, check if Knowledge Graph node is connected
            has_graph_connection = (
                "operation" in inputs and inputs.get("operation") == "query"
            ) or any(key.startswith("graph_") for key in inputs.keys())
            
            if not neo4j_uri and not has_graph_connection:
                # No graph connection available
                return []
            
            # Create graph query tools
            graph_tools = []
            tool_definitions = GraphQueryTools.get_all_tools()
            
            for tool_def in tool_definitions:
                tool_name = tool_def["name"]
                tool_description = tool_def["description"]
                
                # Create a wrapper function that executes the graph query
                def create_graph_tool_func(tool_name: str, neo4j_uri: Optional[str], 
                                         neo4j_user: Optional[str], neo4j_password: Optional[str]):
                    """Create a function that executes a graph query tool."""
                    def graph_tool_func(query_input: str) -> str:
                        """Execute graph query tool (sync version for CrewAI)."""
                        try:
                            import json
                            from neo4j import GraphDatabase
                            
                            # Parse input (should be JSON string with parameters)
                            try:
                                params = json.loads(query_input) if isinstance(query_input, str) else query_input
                            except json.JSONDecodeError:
                                # If not JSON, try to extract entity IDs from string
                                params = {"entity_id": int(query_input)} if query_input.isdigit() else {}
                            
                            # Get connection info
                            uri = neo4j_uri or getattr(settings, "neo4j_uri", None)
                            user = neo4j_user or getattr(settings, "neo4j_user", None)
                            password = neo4j_password or getattr(settings, "neo4j_password", None)
                            
                            if not uri:
                                return "Error: Neo4j connection not configured. Set NEO4J_URI environment variable or connect a Knowledge Graph node."
                            
                            # Create Neo4j driver
                            driver = GraphDatabase.driver(uri, auth=(user, password) if user and password else None)
                            
                            try:
                                # Get the tool query
                                if tool_name == "find_related_entities":
                                    query_info = GraphQueryTools.find_related_entities(
                                        entity_id=params.get("entity_id", 0),
                                        relationship_types=params.get("relationship_types"),
                                        max_depth=params.get("max_depth", 1),
                                        limit=params.get("limit", 10),
                                    )
                                elif tool_name == "find_paths":
                                    query_info = GraphQueryTools.find_paths(
                                        from_entity_id=params.get("from_entity_id", 0),
                                        to_entity_id=params.get("to_entity_id", 0),
                                        relationship_types=params.get("relationship_types"),
                                        max_depth=params.get("max_depth", 3),
                                        limit=params.get("limit", 5),
                                    )
                                elif tool_name == "find_communities":
                                    query_info = GraphQueryTools.find_communities(
                                        node_label=params.get("node_label", ""),
                                        relationship_type=params.get("relationship_type", ""),
                                        min_community_size=params.get("min_community_size", 3),
                                        limit=params.get("limit", 10),
                                    )
                                elif tool_name == "find_influencers":
                                    query_info = GraphQueryTools.find_influencers(
                                        node_label=params.get("node_label", ""),
                                        relationship_type=params.get("relationship_type", ""),
                                        metric=params.get("metric", "degree"),
                                        limit=params.get("limit", 10),
                                    )
                                elif tool_name == "find_similar_entities":
                                    query_info = GraphQueryTools.find_similar_entities(
                                        entity_id=params.get("entity_id", 0),
                                        node_label=params.get("node_label", ""),
                                        relationship_type=params.get("relationship_type", ""),
                                        similarity_metric=params.get("similarity_metric", "jaccard"),
                                        limit=params.get("limit", 10),
                                    )
                                else:
                                    return f"Error: Unknown graph tool: {tool_name}"
                                
                                # Execute query
                                cypher_query = query_info["cypher_query"]
                                query_params = query_info["parameters"]
                                
                                with driver.session() as session:
                                    result = session.run(cypher_query, **query_params)
                                    records = []
                                    for record in result:
                                        # Convert Neo4j types to Python types
                                        record_dict = {}
                                        for key in record.keys():
                                            value = record[key]
                                            if hasattr(value, "__class__") and value.__class__.__name__ in ["Node", "Relationship"]:
                                                record_dict[key] = {
                                                    "id": value.id,
                                                    "labels" if hasattr(value, "labels") else "type": (
                                                        list(value.labels) if hasattr(value, "labels") else value.type
                                                    ),
                                                    "properties": dict(value),
                                                }
                                            else:
                                                record_dict[key] = value
                                        records.append(record_dict)
                                
                                return json.dumps({
                                    "tool": tool_name,
                                    "results": records,
                                    "count": len(records),
                                }, indent=2)
                                
                            finally:
                                driver.close()
                                
                        except Exception as e:
                            logger.error(f"Graph tool {tool_name} error: {e}", exc_info=True)
                            return f"Error executing graph query: {str(e)}"
                    
                    return graph_tool_func
                
                # Create the tool function
                tool_func = create_graph_tool_func(tool_name, neo4j_uri, neo4j_user, neo4j_password)
                
                # Create LangChain Tool
                tool = Tool(
                    name=tool_name,
                    func=tool_func,
                    description=tool_description,
                )
                graph_tools.append(tool)
            
            return graph_tools
            
        except ImportError as e:
            logger.warning(f"Graph tools not available: {e}")
            return []
        except Exception as e:
            logger.warning(f"Error creating graph tools: {e}", exc_info=True)
            return []

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for CrewAI configuration."""
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "enum": ["openai", "anthropic", "gemini"],
                    "default": "openai",
                    "title": "Provider",
                    "description": "LLM provider to use",
                },
                "model": {
                    "type": "string",
                    "default": "gpt-4",
                    "title": "Model",
                    "description": "Model to use (fallback if provider-specific model not set)",
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
                    "minimum": 0,
                    "maximum": 2,
                    "title": "Temperature",
                    "description": "Sampling temperature",
                },
                "max_iterations": {
                    "type": "integer",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10,
                    "title": "Max Iterations",
                    "description": "Maximum number of iterations",
                },
                "process": {
                    "type": "string",
                    "enum": ["sequential", "hierarchical"],
                    "default": "sequential",
                    "title": "Process Type",
                    "description": "How agents coordinate (sequential or hierarchical)",
                },
                "verbose": {
                    "type": "boolean",
                    "default": False,
                    "title": "Verbose",
                    "description": "Enable verbose logging",
                },
                "enable_agent_lightning": {
                    "type": "boolean",
                    "default": False,
                    "title": "Enable Agent Lightning",
                    "description": "Enable Agent Lightning optimization (RL/APO) for automatic agent improvement. Requires agentlightning package.",
                },
                "task": {
                    "type": "string",
                    "title": "Task Description",
                    "description": "Main task description (can also be provided via inputs)",
                },
                "agents": {
                    "type": "array",
                    "title": "Agents",
                    "description": "List of agents in the crew",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {
                                "type": "string",
                                "title": "Role",
                                "description": "Agent role (e.g., 'Researcher', 'Writer')",
                            },
                            "goal": {
                                "type": "string",
                                "title": "Goal",
                                "description": "Agent's goal",
                            },
                            "backstory": {
                                "type": "string",
                                "title": "Backstory",
                                "description": "Agent's backstory",
                            },
                            "tools": {
                                "type": "array",
                                "title": "Tools",
                                "description": "Tools available to this agent",
                                "items": {
                                    "type": "object",
                                },
                            },
                        },
                        "required": ["role", "goal"],
                    },
                },
                "tasks": {
                    "type": "array",
                    "title": "Tasks",
                    "description": "List of tasks for the crew",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "title": "Description",
                                "description": "Task description",
                            },
                            "agent": {
                                "type": "string",
                                "title": "Assigned Agent",
                                "description": "Role of agent assigned to this task",
                            },
                            "expected_output": {
                                "type": "string",
                                "title": "Expected Output",
                                "description": "What the task should produce (optional, defaults to 'Complete the task successfully')",
                                "default": "Complete the task successfully",
                            },
                        },
                        "required": ["description"],
                    },
                },
            },
            "required": ["provider", "agents"],
        }


# Register the node with detailed diagnostics
try:
    # Check if CrewAI is available before registering
    try:
        import crewai
        crewai_version = getattr(crewai, '__version__', 'unknown')
        logger.info(f"CrewAI package found, version: {crewai_version}")
        
        # Try importing specific components
        from crewai import Agent, Task, Crew, Process
        logger.info("CrewAI core components imported successfully")
        
        CREWAI_AVAILABLE = True
        
    except ImportError as e:
        CREWAI_AVAILABLE = False
        logger.warning(f"CrewAI not available - ImportError: {e}")
        logger.warning("CrewAI node will not be available. Install with: pip install crewai[tools]")
    except Exception as e:
        CREWAI_AVAILABLE = False
        logger.error(f"Unexpected error importing CrewAI: {e}", exc_info=True)
    
    if CREWAI_AVAILABLE:
        try:
            NodeRegistry.register(
                CrewAINode.node_type,
                CrewAINode,
                CrewAINode().get_metadata(),
            )
            logger.info("✅ CrewAI node registered successfully")
        except Exception as e:
            logger.error(f"Failed to register CrewAI node after successful import: {e}", exc_info=True)
    else:
        logger.warning("❌ CrewAI node not registered - CrewAI package not available")
        
except Exception as e:
    logger.error(f"Unexpected error during CrewAI node registration: {e}", exc_info=True)

