# Testing CrewAI Node - Quick Start Guide

## 🚀 Quick Test Options

### Option 1: Test via UI (Recommended)

1. **Start the Application**
   ```bash
   # Terminal 1: Backend
   cd backend
   python -m uvicorn main:app --reload
   
   # Terminal 2: Frontend
   cd frontend
   npm run dev
   ```

2. **Create a Simple Workflow**
   - Open the app in browser (usually `http://localhost:5173`)
   - Drag **Text Input** node to canvas
   - Drag **CrewAI Agent** node to canvas
   - Connect Text Input → CrewAI Agent

3. **Configure CrewAI Agent**
   - Click on CrewAI Agent node
   - Set Provider: **OpenAI**
   - Set Model: **GPT-4** (or GPT-3.5-turbo for faster/cheaper)
   - Click **"Add Agent"**:
     - Role: `Researcher`
     - Goal: `Research the topic thoroughly`
     - Backstory: `Expert researcher with 10 years experience`
   - Click **"Add Agent"** again:
     - Role: `Writer`
     - Goal: `Write a comprehensive report`
     - Backstory: `Skilled technical writer`
   - Click **"Add Task"**:
     - Description: `Research AI trends in 2024`
     - Assigned Agent: `Researcher`
   - Click **"Add Task"** again:
     - Description: `Write a report based on research`
     - Assigned Agent: `Writer`

4. **Configure Text Input**
   - Click on Text Input node
   - Enter: `Research the latest AI trends in 2024 and write a comprehensive report`

5. **Run the Workflow**
   - Click **"Run"** button (top right)
   - Watch execution logs in sidebar
   - See results when complete

---

### Option 2: Test via Python Script

1. **Run the test script**
   ```bash
   cd backend
   python test_crewai.py
   ```

2. **Expected Output:**
   ```
   ============================================================
   CrewAI Agent Node Test Suite
   ============================================================
   
   🧪 Testing CrewAI Agent Node...
   ============================================================
   
   📋 Configuration:
      Provider: openai
      Model: gpt-4
      Agents: 2
      Tasks: 2
   
   📝 Task: Research the latest AI trends in 2024...
   
   🚀 Executing CrewAI workflow...
   
   ============================================================
   ✅ SUCCESS!
   ============================================================
   
   📊 Output: [CrewAI results here]
   👥 Agents Used: ['Researcher', 'Writer']
   📋 Tasks Completed: [task descriptions]
   💰 Estimated Cost: $0.xxxx
   ```

---

### Option 3: Load Template Workflows

Template workflows are available in `backend/data/workflows/`:

1. **`crewai_test_template.json`** - Simple research & write workflow
2. **`crewai_with_tools_template.json`** - CrewAI with Calculator and Web Search tools

**To load a template:**
- Currently, templates need to be loaded manually or via API
- Copy the JSON structure into your workflow
- Or use the workflow import feature (if available)

---

## 📋 Test Scenarios

### Scenario 1: Basic Research & Write
**Goal:** Test two agents collaborating

**Setup:**
- Text Input: "Research quantum computing and write a summary"
- CrewAI Agent:
  - Agent 1: Researcher (research the topic)
  - Agent 2: Writer (write summary)
  - Task 1 → Researcher
  - Task 2 → Writer

**Expected:** Research findings + written summary

---

### Scenario 2: Single Agent with Tools
**Goal:** Test agent using tools

**Setup:**
- Text Input: "Calculate 15% of 1000, then search for investment strategies"
- Tool Node (Calculator) → CrewAI Agent
- Tool Node (Web Search) → CrewAI Agent
- CrewAI Agent:
  - Agent: Financial Analyst
  - Tasks: Use calculator, then search

**Expected:** Calculation result + search results

---

### Scenario 3: Complex Multi-Agent Workflow
**Goal:** Test multiple agents with different roles

**Setup:**
- Text Input: "Analyze market trends, create strategy, and write proposal"
- CrewAI Agent:
  - Agent 1: Analyst (analyze trends)
  - Agent 2: Strategist (create strategy)
  - Agent 3: Writer (write proposal)
  - Tasks assigned to each agent

**Expected:** Analysis + Strategy + Proposal

---

## ✅ Success Criteria

A successful test should show:

1. **Execution Logs:**
   - ✅ "Executing CrewAI crew with X agents and Y tasks"
   - ✅ Agent actions visible
   - ✅ Task completion indicators

2. **Output:**
   - ✅ Complete result from crew
   - ✅ Shows agent collaboration
   - ✅ Tasks completed successfully

3. **Cost Tracking:**
   - ✅ Cost displayed (if available)
   - ✅ Reasonable cost for task complexity

4. **No Errors:**
   - ✅ No API key errors
   - ✅ No configuration errors
   - ✅ No execution failures

---

## 🐛 Troubleshooting

### Error: "OpenAI API key is required"
**Fix:** Set `OPENAI_API_KEY` in `.env` file or environment

### Error: "At least one agent must be configured"
**Fix:** Add at least one agent with role and goal

### Error: "Task description is required"
**Fix:** Provide task in Text Input or CrewAI config

### Agents not working together
**Fix:** 
- Check task assignments match agent roles
- Ensure process type is "sequential"
- Verify agents have clear goals

### Tools not detected
**Fix:**
- Connect Tool nodes BEFORE CrewAI agent
- Ensure tools are properly configured
- Check tool outputs format

---

## 📊 Performance Tips

1. **Start Simple:** Test with 1 agent, 1 task first
2. **Model Selection:**
   - GPT-3.5-turbo: Faster, cheaper, good for simple tasks
   - GPT-4: Better quality, slower, more expensive
3. **Limit Iterations:** Set `max_iterations` to 3-5 for testing
4. **Monitor Costs:** CrewAI makes multiple LLM calls
5. **Use Appropriate Temperature:** 0.7 is good default

---

## 🎯 Next Steps After Testing

Once basic tests pass:

1. ✅ Test with different agent configurations
2. ✅ Test with various tools (Calculator, Web Search, etc.)
3. ✅ Test sequential vs hierarchical processes
4. ✅ Test with multiple CrewAI nodes in one workflow
5. ✅ Create custom workflows for your use cases

---

## 📝 Notes

- CrewAI execution can take 30-60 seconds (or more) depending on complexity
- Costs vary based on model, iterations, and task complexity
- Results may vary between runs (LLM non-determinism)
- For production, consider adding error handling and retries

