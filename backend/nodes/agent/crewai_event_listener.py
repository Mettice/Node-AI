"""
CrewAI Event Listener for streaming agent activities.

This module provides a custom event listener that captures CrewAI events
and converts them to StreamEvents for real-time visualization in the frontend.
"""

import asyncio
from typing import Dict, Optional

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CrewAIStreamingListener:
    """
    Custom CrewAI event listener that streams agent activities to the frontend.
    
    This listener captures CrewAI events and converts them to StreamEvents
    for real-time visualization in the Agent Room.
    """
    
    def __init__(self, node_instance, node_id: str, execution_id: Optional[str] = None, main_event_loop=None):
        """
        Initialize the listener.
        
        Args:
            node_instance: The CrewAINode instance (for calling stream_event)
            node_id: The node ID for streaming
            execution_id: The execution ID (optional, can be set later)
            main_event_loop: The main asyncio event loop (for scheduling from worker threads)
        """
        self.node_instance = node_instance
        self.node_id = node_id
        self.execution_id = execution_id
        self.main_event_loop = main_event_loop
        self._listener_instance = None
        # Track task-to-agent mapping for events that don't include agent info
        self._task_to_agent: Dict[str, str] = {}
    
    def _schedule_stream_event(self, event_type: str, data: dict, agent: Optional[str] = None, task: Optional[str] = None):
        """
        Schedule a stream event to run on the main event loop.
        
        This is safe to call from any thread, including CrewAI's worker threads.
        """
        if not self.execution_id:
            return
        
        # Try to get the main event loop
        loop = self.main_event_loop
        if not loop:
            try:
                # Try to get the running loop (might work if we're in the main thread)
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop - try to get the event loop
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    # No event loop available - log and skip (this is normal in worker threads, event listener should handle it)
                    logger.debug(f"Cannot stream event {event_type}: no event loop available (worker thread)")
                    return
        
        # Schedule the coroutine on the main event loop
        try:
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.node_instance.stream_event(event_type, self.node_id, data, agent=agent, task=task),
                    loop
                )
            else:
                # If loop is not running, we can't schedule - log and skip
                logger.warning(f"Cannot stream event {event_type}: event loop is not running")
        except Exception as e:
            logger.warning(f"Error scheduling stream event {event_type}: {e}", exc_info=True)
    
    def set_execution_id(self, execution_id: str):
        """Update the execution ID."""
        self.execution_id = execution_id
        if self._listener_instance:
            self._listener_instance.execution_id = execution_id
    
    def setup_listeners(self, crewai_event_bus):
        """
        Set up event listeners for CrewAI events.
        
        This method is called by CrewAI's event system to register handlers.
        """
        try:
            from crewai.events import (
                # Crew events
                CrewKickoffStartedEvent,
                CrewKickoffCompletedEvent,
                CrewKickoffFailedEvent,
                # Agent events
                AgentExecutionStartedEvent,
                AgentExecutionCompletedEvent,
                AgentExecutionErrorEvent,
                # Task events
                TaskStartedEvent,
                TaskCompletedEvent,
                TaskFailedEvent,
                # Tool events
                ToolUsageStartedEvent,
                ToolUsageFinishedEvent,
                ToolUsageErrorEvent,
                # LLM events
                LLMCallStartedEvent,
                LLMCallCompletedEvent,
                LLMStreamChunkEvent,
            )
        except ImportError as e:
            logger.warning(f"Could not import CrewAI events: {e}")
            return
        
        # Crew lifecycle events
        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_crew_started(source, event: CrewKickoffStartedEvent):
            """Handle crew kickoff started."""
            if not self.execution_id:
                return
            
            try:
                self._schedule_stream_event(
                    "node_progress",
                    {"message": f"Crew '{getattr(event, 'crew_name', 'Crew')}' started execution"},
                )
            except Exception as e:
                logger.warning(f"Error streaming crew started event: {e}")
        
        @crewai_event_bus.on(CrewKickoffCompletedEvent)
        def on_crew_completed(source, event: CrewKickoffCompletedEvent):
            """Handle crew kickoff completed."""
            if not self.execution_id:
                return
            
            try:
                self._schedule_stream_event(
                    "node_progress",
                    {"message": f"Crew '{getattr(event, 'crew_name', 'Crew')}' completed execution"},
                )
            except Exception as e:
                logger.warning(f"Error streaming crew completed event: {e}")
        
        @crewai_event_bus.on(CrewKickoffFailedEvent)
        def on_crew_failed(source, event: CrewKickoffFailedEvent):
            """Handle crew kickoff failed."""
            if not self.execution_id:
                return
            
            try:
                self._schedule_stream_event(
                    "node_progress",
                    {"message": f"Crew '{getattr(event, 'crew_name', 'Crew')}' failed: {getattr(event, 'error', 'Unknown error')}"},
                )
            except Exception as e:
                logger.warning(f"Error streaming crew failed event: {e}")
        
        # Agent execution events
        @crewai_event_bus.on(AgentExecutionStartedEvent)
        def on_agent_started(source, event: AgentExecutionStartedEvent):
            """Handle agent execution started."""
            if not self.execution_id:
                return
            
            try:
                # Extract agent role
                agent_role = None
                if hasattr(event, 'agent') and event.agent:
                    agent_role = getattr(event.agent, 'role', None) or str(event.agent)
                elif hasattr(event, 'agent_role'):
                    agent_role = event.agent_role
                
                # Extract task info
                task_name = None
                if hasattr(event, 'task') and event.task:
                    task_name = getattr(event.task, 'description', None) or getattr(event.task, 'name', None)
                elif hasattr(event, 'task_name'):
                    task_name = event.task_name
                
                self._schedule_stream_event(
                    "agent_started",
                    {
                        "agent": agent_role,
                        "goal": getattr(event.agent, 'goal', None) if hasattr(event, 'agent') and event.agent else None,
                    },
                    agent=agent_role,
                    task=task_name,
                )
            except Exception as e:
                logger.warning(f"Error streaming agent started event: {e}", exc_info=True)
        
        @crewai_event_bus.on(AgentExecutionCompletedEvent)
        def on_agent_completed(source, event: AgentExecutionCompletedEvent):
            """Handle agent execution completed."""
            if not self.execution_id:
                return
            
            try:
                # Extract agent role
                agent_role = None
                if hasattr(event, 'agent') and event.agent:
                    agent_role = getattr(event.agent, 'role', None) or str(event.agent)
                elif hasattr(event, 'agent_role'):
                    agent_role = event.agent_role
                
                # Extract task info
                task_name = None
                if hasattr(event, 'task') and event.task:
                    task_name = getattr(event.task, 'description', None) or getattr(event.task, 'name', None)
                elif hasattr(event, 'task_name'):
                    task_name = event.task_name
                
                # Extract output - get full output, not truncated
                output = None
                if hasattr(event, 'output'):
                    output_obj = event.output
                    # Try to get the actual output text from TaskOutput
                    if hasattr(output_obj, 'raw'):
                        output = str(output_obj.raw)
                    elif hasattr(output_obj, 'description'):
                        output = str(output_obj.description)
                    elif hasattr(output_obj, 'summary'):
                        output = str(output_obj.summary)
                    else:
                        output = str(output_obj)
                    # Keep more content for display (1000 chars instead of 500)
                    if len(output) > 1000:
                        output = output[:1000] + "..."
                
                self._schedule_stream_event(
                    "agent_completed",
                    {
                        "agent": agent_role,
                        "output": output,
                        "task": task_name,
                    },
                    agent=agent_role,
                    task=task_name,
                )
            except Exception as e:
                logger.warning(f"Error streaming agent completed event: {e}", exc_info=True)
        
        @crewai_event_bus.on(AgentExecutionErrorEvent)
        def on_agent_error(source, event: AgentExecutionErrorEvent):
            """Handle agent execution error."""
            if not self.execution_id:
                return
            
            try:
                # Extract agent role
                agent_role = None
                if hasattr(event, 'agent') and event.agent:
                    agent_role = getattr(event.agent, 'role', None) or str(event.agent)
                elif hasattr(event, 'agent_role'):
                    agent_role = event.agent_role
                
                error_msg = str(getattr(event, 'error', 'Unknown error'))
                
                self._schedule_stream_event(
                    "error",
                    {
                        "agent": agent_role,
                        "message": f"Agent '{agent_role}' error: {error_msg}",
                    },
                    agent=agent_role,
                )
            except Exception as e:
                logger.warning(f"Error streaming agent error event: {e}", exc_info=True)
        
        # Task events
        @crewai_event_bus.on(TaskStartedEvent)
        def on_task_started(source, event: TaskStartedEvent):
            """Handle task started."""
            if not self.execution_id:
                return
            
            try:
                # Extract task name
                task_name = None
                if hasattr(event, 'task') and event.task:
                    task_name = getattr(event.task, 'description', None) or getattr(event.task, 'name', None)
                elif hasattr(event, 'task_name'):
                    task_name = event.task_name
                
                # Extract agent role
                agent_role = None
                if hasattr(event, 'agent') and event.agent:
                    agent_role = getattr(event.agent, 'role', None) or str(event.agent)
                elif hasattr(event, 'agent_role'):
                    agent_role = event.agent_role
                elif hasattr(event, 'task') and event.task and hasattr(event.task, 'agent'):
                    agent = event.task.agent
                    agent_role = getattr(agent, 'role', None) if agent else None
                
                # Store task-to-agent mapping for later use
                if task_name and agent_role:
                    self._task_to_agent[task_name] = agent_role
                
                # Log for debugging
                logger.info(f"[Event Listener] Task started: {task_name}, Agent: {agent_role}")
                
                self._schedule_stream_event(
                    "task_started",
                    {
                        "task": task_name,
                        "agent": agent_role,
                    },
                    agent=agent_role,
                    task=task_name,
                )
            except Exception as e:
                logger.warning(f"Error streaming task started event: {e}", exc_info=True)
        
        @crewai_event_bus.on(TaskCompletedEvent)
        def on_task_completed(source, event: TaskCompletedEvent):
            """Handle task completed."""
            if not self.execution_id:
                return
            
            try:
                # Extract task name
                task_name = None
                task_obj = None
                if hasattr(event, 'task') and event.task:
                    task_obj = event.task
                    task_name = getattr(event.task, 'description', None) or getattr(event.task, 'name', None)
                elif hasattr(event, 'task_name'):
                    task_name = event.task_name
                
                # Extract agent role - try multiple methods
                agent_role = None
                
                # Method 1: Direct agent on event
                if hasattr(event, 'agent') and event.agent:
                    agent_role = getattr(event.agent, 'role', None) or str(event.agent)
                
                # Method 2: agent_role attribute
                if not agent_role and hasattr(event, 'agent_role'):
                    agent_role = event.agent_role
                
                # Method 3: Get from task.agent (most reliable for CrewAI)
                if not agent_role and task_obj:
                    # Try task.agent directly
                    if hasattr(task_obj, 'agent') and task_obj.agent:
                        agent_obj = task_obj.agent
                        agent_role = getattr(agent_obj, 'role', None) if agent_obj else None
                    
                    # Try task.assigned_agent (some CrewAI versions use this)
                    if not agent_role and hasattr(task_obj, 'assigned_agent') and task_obj.assigned_agent:
                        agent_obj = task_obj.assigned_agent
                        agent_role = getattr(agent_obj, 'role', None) if agent_obj else None
                
                # Method 4: Try to get from output (TaskOutput might have agent info)
                if not agent_role and hasattr(event, 'output') and event.output:
                    output = event.output
                    if hasattr(output, 'agent') and output.agent:
                        agent_obj = output.agent
                        agent_role = getattr(agent_obj, 'role', None) if agent_obj else None
                
                # Method 5: Use cached task-to-agent mapping from task_started event
                if not agent_role and task_name and task_name in self._task_to_agent:
                    agent_role = self._task_to_agent[task_name]
                    logger.debug(f"[Event Listener] Using cached agent mapping for task: {task_name} -> {agent_role}")
                
                # Log for debugging (including what we found)
                logger.info(f"[Event Listener] Task completed: {task_name}, Agent: {agent_role}")
                
                self._schedule_stream_event(
                    "task_completed",
                    {
                        "task": task_name,
                        "agent": agent_role,
                    },
                    agent=agent_role,
                    task=task_name,
                )
            except Exception as e:
                logger.warning(f"Error streaming task completed event: {e}", exc_info=True)
        
        @crewai_event_bus.on(TaskFailedEvent)
        def on_task_failed(source, event: TaskFailedEvent):
            """Handle task failed."""
            if not self.execution_id:
                return
            
            try:
                # Extract task name
                task_name = None
                if hasattr(event, 'task') and event.task:
                    task_name = getattr(event.task, 'description', None) or getattr(event.task, 'name', None)
                elif hasattr(event, 'task_name'):
                    task_name = event.task_name
                
                error_msg = str(getattr(event, 'error', 'Unknown error'))
                
                self._schedule_stream_event(
                    "error",
                    {
                        "task": task_name,
                        "message": f"Task '{task_name}' failed: {error_msg}",
                    },
                    task=task_name,
                )
            except Exception as e:
                logger.warning(f"Error streaming task failed event: {e}", exc_info=True)
        
        # Tool usage events
        @crewai_event_bus.on(ToolUsageStartedEvent)
        def on_tool_started(source, event: ToolUsageStartedEvent):
            """Handle tool usage started."""
            if not self.execution_id:
                return
            
            try:
                # Extract tool name
                tool_name = getattr(event, 'tool_name', None) or 'unknown'
                
                # Extract agent role
                agent_role = None
                if hasattr(event, 'agent') and event.agent:
                    agent_role = getattr(event.agent, 'role', None) or str(event.agent)
                elif hasattr(event, 'agent_role'):
                    agent_role = event.agent_role
                
                # Extract tool args
                tool_args = getattr(event, 'tool_args', {})
                if isinstance(tool_args, str):
                    try:
                        import json
                        tool_args = json.loads(tool_args)
                    except:
                        tool_args = {"input": tool_args}
                
                self._schedule_stream_event(
                    "agent_tool_called",
                    {
                        "tool": tool_name,
                        "input": tool_args,
                    },
                    agent=agent_role,
                )
            except Exception as e:
                logger.warning(f"Error streaming tool started event: {e}", exc_info=True)
        
        @crewai_event_bus.on(ToolUsageFinishedEvent)
        def on_tool_finished(source, event: ToolUsageFinishedEvent):
            """Handle tool usage finished."""
            if not self.execution_id:
                return
            
            try:
                # Extract tool name
                tool_name = getattr(event, 'tool_name', None) or 'unknown'
                
                # Extract agent role
                agent_role = None
                if hasattr(event, 'agent') and event.agent:
                    agent_role = getattr(event.agent, 'role', None) or str(event.agent)
                elif hasattr(event, 'agent_role'):
                    agent_role = event.agent_role
                
                # Extract result
                result = getattr(event, 'result', None)
                if result:
                    result_str = str(result)
                    if len(result_str) > 200:
                        result_str = result_str[:200] + "..."
                else:
                    result_str = None
                
                self._schedule_stream_event(
                    "agent_output",
                    {
                        "tool": tool_name,
                        "result": result_str,
                    },
                    agent=agent_role,
                )
            except Exception as e:
                logger.warning(f"Error streaming tool finished event: {e}", exc_info=True)
        
        @crewai_event_bus.on(ToolUsageErrorEvent)
        def on_tool_error(source, event: ToolUsageErrorEvent):
            """Handle tool usage error."""
            if not self.execution_id:
                return
            
            try:
                # Extract tool name
                tool_name = getattr(event, 'tool_name', None) or 'unknown'
                
                # Extract agent role
                agent_role = None
                if hasattr(event, 'agent') and event.agent:
                    agent_role = getattr(event.agent, 'role', None) or str(event.agent)
                elif hasattr(event, 'agent_role'):
                    agent_role = event.agent_role
                
                error_msg = str(getattr(event, 'error', 'Unknown error'))
                
                self._schedule_stream_event(
                    "error",
                    {
                        "tool": tool_name,
                        "message": f"Tool '{tool_name}' error: {error_msg}",
                    },
                    agent=agent_role,
                )
            except Exception as e:
                logger.warning(f"Error streaming tool error event: {e}", exc_info=True)
        
        # LLM events (for thoughts/reasoning)
        @crewai_event_bus.on(LLMCallStartedEvent)
        def on_llm_started(source, event: LLMCallStartedEvent):
            """Handle LLM call started (agent thinking)."""
            if not self.execution_id:
                return
            
            try:
                # Extract agent role
                agent_role = None
                if hasattr(event, 'agent') and event.agent:
                    agent_role = getattr(event.agent, 'role', None) or str(event.agent)
                elif hasattr(event, 'agent_role'):
                    agent_role = event.agent_role
                
                # Extract prompt/thought
                prompt = getattr(event, 'prompt', None)
                if prompt:
                    thought = str(prompt)
                    if len(thought) > 500:
                        thought = thought[:500] + "..."
                else:
                    thought = None
                
                if agent_role:  # Only stream if we have agent info
                    self._schedule_stream_event(
                        "agent_thinking",
                        {
                            "thought": thought,
                        },
                        agent=agent_role,
                    )
            except Exception as e:
                logger.warning(f"Error streaming LLM started event: {e}", exc_info=True)
        
        @crewai_event_bus.on(LLMStreamChunkEvent)
        def on_llm_chunk(source, event: LLMCallCompletedEvent):
            """Handle LLM stream chunk (partial thoughts)."""
            if not self.execution_id:
                return
            
            try:
                # Extract agent role
                agent_role = None
                if hasattr(event, 'agent') and event.agent:
                    agent_role = getattr(event.agent, 'role', None) or str(event.agent)
                elif hasattr(event, 'agent_role'):
                    agent_role = event.agent_role
                
                # Extract chunk
                chunk = getattr(event, 'chunk', None)
                if chunk and agent_role:
                    self._schedule_stream_event(
                        "agent_thinking",
                        {
                            "thought": str(chunk),
                            "partial": True,
                        },
                        agent=agent_role,
                    )
            except Exception as e:
                logger.warning(f"Error streaming LLM chunk event: {e}", exc_info=True)
        
        @crewai_event_bus.on(LLMCallCompletedEvent)
        def on_llm_completed(source, event: LLMCallCompletedEvent):
            """Handle LLM call completed (agent finished thinking)."""
            if not self.execution_id:
                return
            
            try:
                # Extract agent role
                agent_role = None
                if hasattr(event, 'agent') and event.agent:
                    agent_role = getattr(event.agent, 'role', None) or str(event.agent)
                elif hasattr(event, 'agent_role'):
                    agent_role = event.agent_role
                
                # Extract response/thought
                response = getattr(event, 'response', None)
                if response:
                    thought = str(response)
                    if len(thought) > 500:
                        thought = thought[:500] + "..."
                else:
                    thought = None
                
                # Extract token usage if available
                tokens_used = {}
                if hasattr(event, 'usage_metadata') and event.usage_metadata:
                    usage = event.usage_metadata
                    tokens_used = {
                        "input_tokens": getattr(usage, 'input_tokens', None) or getattr(usage, 'prompt_tokens', None) or 0,
                        "output_tokens": getattr(usage, 'output_tokens', None) or getattr(usage, 'completion_tokens', None) or 0,
                        "total_tokens": getattr(usage, 'total_tokens', None) or 0,
                    }
                elif hasattr(event, 'tokens_used'):
                    tokens_used = event.tokens_used
                
                event_data = {
                    "thought": thought,
                    "completed": True,
                }
                
                # Include token information if available
                if tokens_used and (tokens_used.get("input_tokens") or tokens_used.get("output_tokens") or tokens_used.get("total_tokens")):
                    event_data["tokens_used"] = tokens_used
                    # Also add tokens at top level for easier access
                    event_data["input_tokens"] = tokens_used.get("input_tokens", 0)
                    event_data["output_tokens"] = tokens_used.get("output_tokens", 0)
                    event_data["total_tokens"] = tokens_used.get("total_tokens", 0)
                
                if agent_role and thought:  # Only stream if we have agent info and thought
                    self._schedule_stream_event(
                        "agent_thinking",
                        event_data,
                        agent=agent_role,
                    )
            except Exception as e:
                logger.warning(f"Error streaming LLM completed event: {e}", exc_info=True)
        
        logger.info("CrewAI event listeners registered successfully")


# Create a BaseEventListener wrapper for CrewAI's event system
class CrewAIStreamingEventListener:
    """
    Wrapper that implements BaseEventListener interface for CrewAI.
    
    This class creates and manages the actual listener instance.
    When instantiated, it automatically registers with CrewAI's event bus.
    """
    
    def __init__(self, node_instance, node_id: str, execution_id: Optional[str] = None, main_event_loop=None):
        """Initialize the event listener wrapper."""
        try:
            from crewai.events import BaseEventListener
            # Create the actual listener that will handle events
            self.listener = CrewAIStreamingListener(node_instance, node_id, execution_id, main_event_loop=main_event_loop)
            self.node_instance = node_instance
            self.node_id = node_id
            self.execution_id = execution_id
            
            # Create a BaseEventListener subclass that will auto-register
            # We need to capture the listener in a closure
            listener_ref = self.listener
            
            class AutoRegisterListener(BaseEventListener):
                def __init__(self, listener):
                    self.listener = listener
                    super().__init__()
                
                def setup_listeners(self, crewai_event_bus):
                    # Delegate to our listener
                    self.listener.setup_listeners(crewai_event_bus)
            
            # Create instance - this will auto-register via BaseEventListener.__init__
            self._listener_instance = AutoRegisterListener(listener_ref)
            logger.info(f"CrewAI streaming event listener created and registered for node {node_id} (main_event_loop: {main_event_loop is not None})")
            
        except ImportError as e:
            logger.warning(f"Could not import CrewAI BaseEventListener: {e}")
            self._listener_instance = None
        except Exception as e:
            logger.warning(f"Failed to create event listener: {e}", exc_info=True)
            self._listener_instance = None
    
    def set_execution_id(self, execution_id: str):
        """Update execution ID."""
        self.execution_id = execution_id
        if hasattr(self, 'listener'):
            self.listener.set_execution_id(execution_id)

