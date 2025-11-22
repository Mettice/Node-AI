# CrewAI Agent Node Integration Guide

## How CrewAI Agents Work with Other Nodes

CrewAI agents can be connected to other nodes in your workflow to create powerful multi-agent systems. Here's how:

### 1. **Input Nodes → CrewAI Agent**

**Text Input Node** → **CrewAI Agent**
- The text input provides the **initial task/context** to the crew
- The agent receives this as `inputs.get("text")` or `inputs.get("task")`
- Example: User types "Research AI trends and write a report"

**File Loader → CrewAI Agent**
- File content can be passed as context
- Agents can process documents and extract information

### 2. **Tool Nodes → CrewAI Agent**

**Tool Node** → **CrewAI Agent**
- Tool nodes provide **capabilities** to agents
- Each connected tool becomes available to all agents in the crew
- Agents automatically use tools when needed
- Example: Connect Calculator, Web Search, and API Call tools

**How it works:**
1. Tool nodes output: `{"tool_id": "...", "tool_name": "...", ...}`
2. CrewAI agent detects tools in `inputs` with keys like `tool_*`
3. Tools are automatically registered with agents
4. Agents can call tools during task execution

### 3. **CrewAI Agent → Output Nodes**

**CrewAI Agent** → **Chat Node**
- CrewAI output can be formatted and displayed in chat
- Use for conversational interfaces

**CrewAI Agent** → **Text Output**
- Direct output of crew results
- Can be saved or processed further

### 4. **Multiple CrewAI Agents**

You can create **multiple CrewAI agent nodes** in the same workflow:

```
Text Input → CrewAI Agent 1 (Research Team)
                ↓
            CrewAI Agent 2 (Writing Team)
                ↓
            Chat Node
```

**How they work together:**
- Each CrewAI node is independent
- Output from one can be input to another
- Different crews can specialize in different tasks

### 5. **Memory Node → CrewAI Agent**

**Memory Node** → **CrewAI Agent**
- Provides conversation history context
- Agents can reference past interactions
- Useful for maintaining context across workflow runs

## Example Workflows

### Example 1: Research and Write Workflow

```
Text Input: "Research quantum computing and write a report"
    ↓
Tool Node (Web Search) → CrewAI Agent
    ↓
CrewAI Agent:
  - Agent 1 (Researcher): role="Researcher", goal="Research thoroughly"
  - Agent 2 (Writer): role="Writer", goal="Write comprehensive report"
  - Task 1: "Research quantum computing" → Researcher
  - Task 2: "Write report" → Writer
    ↓
Chat Node (displays final report)
```

### Example 2: Multi-Stage Processing

```
Text Input: "Analyze market trends"
    ↓
CrewAI Agent 1 (Analysis Team):
  - Agent: Analyst
  - Task: "Analyze market data"
    ↓
CrewAI Agent 2 (Presentation Team):
  - Agent: Presenter
  - Task: "Create presentation from analysis"
    ↓
Output
```

### Example 3: Tool-Enhanced Agent

```
Text Input: "Calculate ROI and search for best practices"
    ↓
Tool Node (Calculator) → CrewAI Agent
Tool Node (Web Search) → CrewAI Agent
    ↓
CrewAI Agent:
  - Agent: Financial Analyst
  - Tools: Calculator, Web Search
  - Task: "Calculate ROI and find best practices"
    ↓
Output (with calculations and research)
```

## Key Points

✅ **Agents receive:**
- Text/context from input nodes
- Tools from connected Tool nodes
- Task descriptions from config or inputs

✅ **Agents output:**
- Results of crew execution
- Can be passed to other nodes
- Includes agent roles, tasks, and costs

✅ **Multiple agents:**
- Each CrewAI node is independent
- Can chain multiple crews
- Different crews can have different agents/tasks

✅ **Tool integration:**
- Tools are automatically detected
- All agents in a crew can use all tools
- Tools are called automatically when needed

## Configuration Tips

1. **Agent Roles**: Use clear, distinct roles (e.g., "Researcher", "Writer", "Analyst")
2. **Goals**: Be specific about what each agent should achieve
3. **Backstory**: Add context to help agents understand their expertise
4. **Tasks**: Assign tasks to agents by role name
5. **Tools**: Connect Tool nodes before the CrewAI agent to provide capabilities

## Best Practices

- **Start simple**: One agent, one task
- **Add complexity gradually**: Multiple agents, multiple tasks
- **Use tools**: Connect Tool nodes for enhanced capabilities
- **Chain crews**: Use multiple CrewAI nodes for complex workflows
- **Monitor costs**: CrewAI can make multiple LLM calls

