# LangChain Agent Guide

## Overview

Your LangChain Agent is a **single AI agent** that uses the **ReAct (Reasoning + Acting) framework** to solve tasks by reasoning through problems and using tools to take actions.

## How It Works

### 1. **ReAct Framework**

The agent follows this reasoning loop:

```
Question: "What is 2+2 and what's the weather in New York?"

Thought: I need to calculate 2+2 first, then get weather information
Action: calculator
Action Input: "2+2"
Observation: "4"

Thought: Now I need weather information for New York
Action: web_search
Action Input: "weather New York"
Observation: "72°F, sunny"

Thought: I now have both answers
Final Answer: 2+2 equals 4. The weather in New York is 72°F and sunny.
```

**Key Features:**
- **Reasoning**: The agent thinks about what to do before acting
- **Tool Use**: Can call tools (calculator, web search, custom tools) to get information
- **Iterative**: Can make multiple tool calls until it has enough information
- **Self-Correcting**: Can adjust its approach based on tool results

### 2. **Execution Flow**

```
1. Input: Task/Query
   ↓
2. Initialize Agent
   - Create LLM (OpenAI, Anthropic, or Gemini)
   - Load tools (from Tool nodes or config)
   - Create ReAct agent
   ↓
3. Agent Reasoning Loop
   - Thought: Agent thinks about the task
   - Action: Agent decides which tool to use
   - Action Input: Agent prepares input for tool
   - Observation: Tool executes and returns result
   - (Repeat until agent has final answer)
   ↓
4. Final Answer
   - Agent provides complete answer
   - Returns output with tool calls and reasoning
```

### 3. **Tool Integration**

The agent can use tools in three ways:

#### **A. Connected Tool Nodes** (Recommended)
```
[Tool Node] → [LangChain Agent]
```
- Tool nodes output tool definitions
- Agent automatically converts them to LangChain tools
- Tools are available during agent execution

#### **B. Knowledge Graph Tools**
```
[Knowledge Graph Node] → [LangChain Agent]
```
- Automatically adds graph query tools
- Agent can query the knowledge graph
- Useful for structured data retrieval

#### **C. Built-in Tools**
- **Calculator**: Mathematical expressions (`2+2`, `10*5`)
- **Web Search**: (placeholder - needs implementation)

#### **D. Config Tools**
You can define tools in the node configuration:
```json
{
  "tools": [
    {
      "type": "calculator",
      "name": "calculator",
      "description": "Evaluates math expressions"
    }
  ]
}
```

### 4. **Configuration Options**

```json
{
  "provider": "openai",           // LLM provider: openai, anthropic, gemini
  "openai_model": "gpt-4o-mini",  // Model to use
  "temperature": 0.7,             // Creativity (0.0-2.0)
  "max_iterations": 5,            // Max reasoning steps (1-20)
  "verbose": true,                // Show reasoning steps
  "task": "Your question here"    // Task/query for agent
}
```

**Supported Providers:**
- **OpenAI**: `gpt-5.1`, `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`
- **Anthropic**: `claude-sonnet-4-5-20250929`, `claude-haiku-4-5-20251001`
- **Gemini**: `gemini-2.5-pro`, `gemini-2.5-flash`

### 5. **Input/Output**

**Input:**
- `task` or `query`: The question/task for the agent
- Tool outputs from connected Tool nodes
- Knowledge Graph outputs

**Output:**
```json
{
  "output": "Final answer from agent",
  "intermediate_steps": [...],      // All reasoning steps
  "tool_calls": [                   // Formatted tool calls
    {
      "tool": "calculator",
      "input": "2+2",
      "output": "4"
    }
  ],
  "reasoning": "Agent's reasoning process",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "tokens_used": {
    "input": 150,
    "output": 200,
    "total": 350
  },
  "cost": 0.0003
}
```

## Example Workflows

### **Example 1: Simple Calculator Agent**

```
[Text Input] → [LangChain Agent]
```

**Text Input:** `"What is 15 * 23 + 100?"`

**Agent Process:**
1. Thought: "I need to calculate this math expression"
2. Action: `calculator`
3. Action Input: `"15 * 23 + 100"`
4. Observation: `"445"`
5. Final Answer: `"15 * 23 + 100 = 445"`

### **Example 2: Agent with Custom Tools**

```
[Tool Node (Web Search)] → [LangChain Agent]
[Text Input] → [LangChain Agent]
```

**Text Input:** `"What's the latest news about AI?"`

**Agent Process:**
1. Thought: "I need to search for recent AI news"
2. Action: `web_search`
3. Action Input: `"latest AI news 2024"`
4. Observation: `"[Search results...]"`
5. Final Answer: `"[Summary of AI news]"`

### **Example 3: Agent with Knowledge Graph**

```
[Knowledge Graph] → [LangChain Agent]
[Text Input] → [LangChain Agent]
```

**Text Input:** `"Who wrote the paper about transformers?"`

**Agent Process:**
1. Thought: "I need to query the knowledge graph"
2. Action: `graph_query`
3. Action Input: `"MATCH (p:Paper)-[:ABOUT]->(t:Topic {name: 'transformers'}) RETURN p"`
4. Observation: `"[Graph results...]"`
5. Final Answer: `"[Answer based on graph data]"`

## Key Differences from CrewAI Agent

| Feature | LangChain Agent | CrewAI Agent |
|---------|----------------|--------------|
| **Type** | Single agent | Multi-agent system |
| **Structure** | One agent + tools | Multiple agents + tasks |
| **Use Case** | Tool-based tasks | Coordinated workflows |
| **Visualization** | Standard node | Agent Room (multi-agent) |
| **Complexity** | Simpler | More complex |

## Best Practices

1. **Clear Tasks**: Provide specific, actionable tasks
   - ✅ Good: "Calculate 15 * 23 and explain the steps"
   - ❌ Bad: "Do math"

2. **Tool Selection**: Connect relevant Tool nodes
   - Use Tool nodes for custom functionality
   - Use Knowledge Graph for structured queries

3. **Max Iterations**: Start with 5, increase if needed
   - More iterations = more reasoning but higher cost
   - Watch for infinite loops

4. **Temperature**: Use 0.7 for balanced reasoning
   - Lower (0.3): More deterministic
   - Higher (1.0): More creative

5. **Cost Management**: Monitor token usage
   - Each reasoning step uses tokens
   - Tool calls add to cost
   - Use `gpt-4o-mini` for cost-effective tasks

## Troubleshooting

**Agent gets stuck:**
- Reduce `max_iterations`
- Check if tools are working correctly
- Verify task is clear and actionable

**No tools available:**
- Connect Tool nodes to the agent
- Check tool node outputs
- Agent will use default calculator if no tools

**High costs:**
- Use cheaper models (`gpt-4o-mini` instead of `gpt-4o`)
- Reduce `max_iterations`
- Simplify tasks

**Agent doesn't use tools:**
- Verify tools are properly connected
- Check tool descriptions are clear
- Ensure task requires tool use

## Advanced Features

### **Agent Lightning Integration** (Optional)

Enable automatic agent optimization:
```json
{
  "enable_agent_lightning": true
}
```

- Uses reinforcement learning to improve agent performance
- Automatically optimizes tool selection and reasoning
- Requires `agentlightning` package

### **Streaming**

The agent streams:
- Agent start/completion events
- Tool call events
- Progress updates
- Final output

All events are available in the execution panel for real-time monitoring.

---

**Your LangChain Agent is a powerful single-agent system perfect for tool-based tasks that require reasoning and action!** 🚀
