# CrewAI Node Testing Guide

## Quick Test Workflows

### Test 1: Simple Research & Write Workflow

**Workflow:** `crewai_test_template.json`

**Description:** Two agents collaborate:
- **Researcher Agent**: Researches the topic
- **Writer Agent**: Writes a comprehensive report

**How to Test:**
1. Load the template workflow
2. Click "Run" to execute
3. The CrewAI agent will:
   - Receive the task from Text Input
   - Researcher agent researches the topic
   - Writer agent creates the report
   - Output is displayed in execution logs

**Expected Output:**
- A comprehensive report on AI trends in 2024
- Includes research findings and written content
- Shows agent collaboration

---

### Test 2: CrewAI with Tools

**Workflow:** `crewai_with_tools_template.json`

**Description:** A Financial Analyst agent uses:
- **Calculator Tool**: For ROI calculations
- **Web Search Tool**: For research

**How to Test:**
1. Load the template workflow
2. Ensure you have:
   - OpenAI API key set (for CrewAI)
   - DuckDuckGo search available (for web search tool)
3. Click "Run" to execute
4. The agent will:
   - Use calculator to compute ROI
   - Use web search to find best practices
   - Combine results into a comprehensive answer

**Expected Output:**
- ROI calculation results
- Best practices from web search
- Combined analysis and recommendations

---

## Manual Testing Steps

### Step 1: Create a Simple Workflow

1. **Add Text Input Node**
   - Drag "Text Input" to canvas
   - Set text: "Research quantum computing and write a summary"

2. **Add CrewAI Agent Node**
   - Drag "CrewAI Agent" to canvas
   - Configure:
     - Provider: OpenAI
     - Model: GPT-4
     - Add Agent 1:
       - Role: "Researcher"
       - Goal: "Research quantum computing thoroughly"
       - Backstory: "Expert researcher in quantum computing"
     - Add Agent 2:
       - Role: "Writer"
       - Goal: "Write a clear summary"
       - Backstory: "Skilled technical writer"
     - Add Task 1:
       - Description: "Research quantum computing"
       - Agent: "Researcher"
     - Add Task 2:
       - Description: "Write a summary"
       - Agent: "Writer"

3. **Connect Nodes**
   - Connect Text Input → CrewAI Agent

4. **Run Workflow**
   - Click "Run" button
   - Watch execution logs
   - See results in sidebar

---

### Step 2: Add Tools to CrewAI

1. **Add Tool Nodes**
   - Add "Tool" node (Calculator)
   - Add "Tool" node (Web Search)

2. **Configure Tools**
   - Calculator: No config needed
   - Web Search: Select provider (DuckDuckGo)

3. **Connect Tools**
   - Connect Calculator → CrewAI Agent
   - Connect Web Search → CrewAI Agent

4. **Update CrewAI Task**
   - Modify task to use tools:
     - "Calculate 15% of 1000, then search for investment strategies"

5. **Run Workflow**
   - Agent will automatically use connected tools
   - Results will show tool usage

---

## Testing Checklist

### Basic Functionality
- [ ] CrewAI node appears in palette
- [ ] Can configure agents (role, goal, backstory)
- [ ] Can configure tasks
- [ ] Can select provider (OpenAI/Anthropic)
- [ ] Can select model
- [ ] Workflow executes successfully

### Agent Collaboration
- [ ] Multiple agents work together
- [ ] Tasks are assigned correctly
- [ ] Agents share information
- [ ] Sequential process works
- [ ] Hierarchical process works (if tested)

### Tool Integration
- [ ] Tools are detected from connected nodes
- [ ] Agents can use calculator
- [ ] Agents can use web search
- [ ] Tool outputs are used correctly

### Input/Output
- [ ] Text input provides task to CrewAI
- [ ] CrewAI receives input correctly
- [ ] Output is displayed in logs
- [ ] Results are formatted correctly

### Error Handling
- [ ] Missing API key shows clear error
- [ ] Invalid agent config shows error
- [ ] Missing task shows error
- [ ] Tool errors are handled gracefully

---

## Expected Results

### Successful Execution Should Show:
1. **Execution Logs:**
   - "Executing CrewAI crew with X agents and Y tasks"
   - Agent actions and decisions
   - Tool calls (if tools are used)
   - Final output

2. **Output:**
   - Complete result from crew execution
   - Agent roles used
   - Tasks completed
   - Cost information

3. **Timeline:**
   - Node execution order
   - Time taken for each step
   - Success indicators

---

## Troubleshooting

### Issue: "OpenAI API key is required"
**Solution:** Set `OPENAI_API_KEY` environment variable

### Issue: "At least one agent must be configured"
**Solution:** Add at least one agent with role and goal

### Issue: "Task description is required"
**Solution:** Provide task in Text Input or CrewAI config

### Issue: Tools not working
**Solution:** 
- Ensure Tool nodes are connected BEFORE CrewAI agent
- Check tool configuration
- Verify tool outputs are correct format

### Issue: Agents not collaborating
**Solution:**
- Check task assignments match agent roles
- Ensure process type is set correctly
- Verify agents have clear goals

---

## Performance Tips

1. **Start Simple**: Test with 1 agent, 1 task first
2. **Add Complexity**: Gradually add more agents and tasks
3. **Monitor Costs**: CrewAI can make multiple LLM calls
4. **Use Appropriate Models**: GPT-3.5 for simple tasks, GPT-4 for complex
5. **Limit Iterations**: Set `max_iterations` appropriately

---

## Next Steps

After testing:
1. Try different agent configurations
2. Experiment with different tasks
3. Test with various tools
4. Create custom workflows
5. Share successful workflows as templates

