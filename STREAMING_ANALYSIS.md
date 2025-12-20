# Streaming System Analysis - Agent Room Visualization

## Current State

### What's Working ✅
1. **Backend sends `agent_started` events** - Line 292-300 in `crewai_agent.py` sends events with `agent=agent.role`
2. **StreamEvent includes agent/task fields** - `StreamEvent.to_dict()` includes `agent` and `task` in the JSON
3. **Frontend receives events** - SSEProcessor receives events and stores them with agent/task info
4. **Interface is correct** - Both backend and frontend have `agent` and `task` fields

### What's NOT Working ❌
1. **Callbacks not firing** - `step_callback` and `task_callback` in CrewAI are defined but may not be called by CrewAI
2. **No agent activity events** - We're not getting `agent_thinking`, `agent_tool_called`, `agent_output` events
3. **No task events** - We're not getting `task_started`, `task_completed` events with task info
4. **Limited visibility** - Only seeing `agent_started` (4 events) and generic `node_progress` events

## Root Cause Analysis

### Problem 1: CrewAI Callbacks May Not Work
The current implementation uses CrewAI's `task_callback` and `step_callback`:
- These callbacks are **synchronous** and may not be called by CrewAI in all scenarios
- CrewAI's callback system might be deprecated or not fully functional
- The callbacks might only fire for certain process types (sequential vs hierarchical)

### Problem 2: CrewAI Has Its Own Event System
CrewAI has a built-in event listener system (`CrewAIEventsBus`) that provides:
- `AgentExecutionStartedEvent` - When an agent starts
- `AgentExecutionCompletedEvent` - When an agent finishes
- `ToolUsageStartedEvent` / `ToolUsageFinishedEvent` - Tool usage
- `LLMCallStartedEvent` / `LLMCallCompletedEvent` - LLM calls (thoughts)
- `TaskStartedEvent` / `TaskCompletedEvent` - Task lifecycle

**This is the proper way to capture CrewAI events!**

## Solution: Use CrewAI Event Listener System

### Implementation Plan

1. **Create a Custom Event Listener**
   - Subscribe to CrewAI's event bus
   - Convert CrewAI events to our StreamEvent format
   - Stream agent activities, thoughts, tool usage, task progress

2. **Event Mapping**
   ```
   CrewAI Event → Our StreamEvent
   ├─ AgentExecutionStartedEvent → agent_started (with agent_role)
   ├─ AgentExecutionCompletedEvent → agent_completed (with agent_role)
   ├─ ToolUsageStartedEvent → agent_tool_called (with agent_role, tool_name)
   ├─ LLMCallStartedEvent → agent_thinking (with agent_role, thought)
   ├─ TaskStartedEvent → task_started (with task_name, agent_role)
   └─ TaskCompletedEvent → task_completed (with task_name, agent_role)
   ```

3. **Benefits**
   - Real-time agent activity tracking
   - Actual thoughts and reasoning
   - Tool usage visibility
   - Task progress per agent
   - Proper agent identification

## Next Steps

1. **Add detailed logging** (DONE) - See what's actually in events
2. **Implement CrewAI event listener** - Subscribe to CrewAI's event bus
3. **Test with real execution** - Verify events are captured
4. **Update Agent Room** - Use the new event data for visualization

## Files to Modify

1. `backend/nodes/agent/crewai_agent.py`
   - Add CrewAI event listener setup
   - Convert CrewAI events to StreamEvents
   - Remove/replace callbacks if needed

2. `frontend/src/components/Canvas/AgentRoom.tsx`
   - Already updated to use agent/task fields
   - Will automatically work once backend sends proper events

3. `frontend/src/components/Execution/SSEProcessor.tsx`
   - Already updated with detailed logging
   - Will show what events are actually received

## Testing

After implementation, check console logs for:
- `agent_started` events with `agent` field populated
- `agent_thinking` events with `agent` and `data.thought`
- `agent_tool_called` events with `agent` and `data.tool`
- `task_started` / `task_completed` events with `task` and `agent`
- All events should have proper `agent` and `task` identification

