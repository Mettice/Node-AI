# 💰 Cost Tracking System - Complete Guide

## Overview

Nodeflow has a **unified cost tracking system** that automatically captures token usage and model pricing for all major providers, similar to LangChain's LangSmith cost tracking.

---

## 🎯 How Cost Tracking Works

### **1. Automatic Cost Calculation**

Costs are calculated **automatically** at the node level:

- **LLM Nodes** (Chat, Agents): Calculate cost based on input/output tokens
- **Embedding Nodes**: Calculate cost based on text length
- **Rerank Nodes**: Calculate cost based on query + document pairs
- **Vector Search**: Usually free (or minimal if using paid services)

### **2. Cost Storage**

Costs are stored at multiple levels:

1. **Node Level**: Each `NodeResult` includes `cost` field
2. **Execution Level**: `Execution.total_cost` aggregates all node costs
3. **Cost Intelligence**: Detailed breakdown by provider, model, category
4. **Usage Logs**: Database records for API key usage tracking

### **3. Cost Breakdown**

Costs are automatically categorized:

- **By Provider**: OpenAI, Anthropic, Gemini, Cohere, etc.
- **By Model**: gpt-4o-mini, claude-sonnet-4, gemini-2.5-flash, etc.
- **By Category**: LLM, Embedding, Reranking, Vector Search, Other

---

## 📊 Cost Tracking Architecture

```
Node Execution
    ↓
Calculate Cost (using model_pricing.py)
    ↓
Store in NodeResult.cost
    ↓
Aggregate in Execution.total_cost
    ↓
Record in Cost Intelligence API
    ↓
Display in UI (ExecutionSummary, CostIntelligence)
```

---

## 🔍 Where Costs Are Displayed

### **1. Execution Summary**

Shows:
- **Total Cost**: Aggregated cost for entire workflow
- **Per-Node Cost**: Individual node costs in breakdown

**Location**: `ExecutionSummary.tsx`

### **2. Cost Intelligence Dashboard**

Shows:
- **Cost Breakdown by Category**: LLM, Embedding, etc.
- **Cost Breakdown by Provider**: OpenAI, Anthropic, etc.
- **Cost Breakdown by Model**: Specific model costs
- **Top Cost Nodes**: Highest cost nodes
- **Optimization Suggestions**: Cost-saving recommendations

**Location**: `CostIntelligence.tsx`

### **3. Execution Logs**

Shows:
- **Per-Node Cost**: Cost displayed next to each node result

**Location**: `ExecutionLogs.tsx`

---

## 💡 Cost Calculation Details

### **LLM Costs**

```python
# Calculated using model_pricing.py
cost = calculate_llm_cost(
    provider="openai",
    model="gpt-4o-mini",
    input_tokens=100,
    output_tokens=50
)
# Returns: $0.00015 (based on pricing per 1K tokens)
```

### **Embedding Costs**

```python
# Calculated using model_pricing.py
cost = calculate_embedding_cost_from_texts(
    provider="openai",
    model="text-embedding-3-small",
    texts=["text1", "text2", ...]
)
# Returns: $0.00001 (based on pricing per 1K tokens)
```

### **Rerank Costs**

```python
# Calculated using model_pricing.py
cost = calculate_rerank_cost(
    provider="cohere",
    model="rerank-english-v3.0",
    query_tokens=10,
    document_tokens=1000
)
# Returns: $0.001 (based on pricing per 1K units)
```

---

## 📈 Cost Intelligence API

### **Endpoints:**

1. **`GET /api/v1/cost/analyze/{execution_id}`**
   - Analyzes cost breakdown
   - Returns: Cost by category, provider, model
   - Includes optimization suggestions

2. **`GET /api/v1/cost/forecast/{workflow_id}`**
   - Predicts future costs
   - Based on historical data
   - Returns: Cost predictions

3. **`GET /api/v1/cost/optimize/{execution_id}`**
   - Provides optimization suggestions
   - Model recommendations
   - Cost-saving tips

---

## 🆚 Comparison with LangChain LangSmith

| Feature | Nodeflow | LangSmith |
|---------|----------|-----------|
| **Automatic Tracking** | ✅ Yes | ✅ Yes |
| **Provider Support** | ✅ OpenAI, Anthropic, Gemini, Cohere, Voyage | ✅ All major providers |
| **Model Pricing** | ✅ Centralized in `model_pricing.py` | ✅ Built-in pricing |
| **Cost Breakdown** | ✅ By category, provider, model | ✅ By provider, model |
| **Cost Forecasting** | ✅ Yes (based on history) | ✅ Yes |
| **Optimization Suggestions** | ✅ Yes | ✅ Yes |
| **Custom Cost Data** | ⚠️ Limited | ✅ Full support |
| **UI Dashboard** | ✅ Cost Intelligence component | ✅ LangSmith UI |

---

## ✅ What We're Doing Right

1. **✅ Unified Cost Calculation**: All costs calculated using `model_pricing.py`
2. **✅ Automatic Tracking**: Costs tracked automatically during execution
3. **✅ Multi-Level Storage**: Node → Execution → Intelligence → Database
4. **✅ Cost Breakdown**: By category, provider, and model
5. **✅ Cost Forecasting**: Predictive cost analysis
6. **✅ Optimization Suggestions**: Cost-saving recommendations

---

## 🔧 Areas for Improvement

### **1. Custom Cost Data Support**

**Current**: Limited support for custom pricing
**LangChain**: Full support for custom cost data on any run

**Recommendation**: Add support for custom cost overrides per workflow/node

### **2. Cost Tracking UI**

**Current**: Cost Intelligence component exists but could be more prominent
**LangChain**: Dedicated LangSmith dashboard

**Recommendation**: Add cost tracking to main dashboard

### **3. Historical Cost Analysis**

**Current**: Cost history stored in-memory
**LangChain**: Persistent database storage

**Recommendation**: Store cost history in database for long-term analysis

---

## 📝 Cost Tracking Flow

### **During Execution:**

```python
# 1. Node executes
node_result = await node.execute(inputs, config)

# 2. Cost calculated automatically
cost = calculate_cost(provider, model, tokens)

# 3. Stored in NodeResult
node_result.cost = cost

# 4. Aggregated in Execution
execution.total_cost += cost

# 5. Recorded in Cost Intelligence
await record_execution_costs(execution_id, cost_records)
```

### **After Execution:**

```python
# 1. Cost Intelligence API analyzes costs
analysis = await analyze_execution_cost(execution_id)

# 2. Returns breakdown:
# - cost_by_category: {"llm": 0.05, "embedding": 0.001}
# - cost_by_provider: {"openai": 0.04, "anthropic": 0.01}
# - cost_by_model: {"gpt-4o-mini": 0.03, "claude-sonnet": 0.01}

# 3. UI displays breakdown
<CostIntelligence analysis={analysis} />
```

---

## 🎯 Summary

### **What We Have:**

✅ **Unified cost tracking** - All costs calculated consistently  
✅ **Automatic calculation** - No manual cost entry needed  
✅ **Multi-provider support** - OpenAI, Anthropic, Gemini, Cohere, Voyage  
✅ **Cost breakdown** - By category, provider, model  
✅ **Cost forecasting** - Predictive cost analysis  
✅ **Optimization suggestions** - Cost-saving recommendations  

### **What We Could Improve:**

⚠️ **Custom cost data** - Add support for custom pricing  
⚠️ **Persistent storage** - Store cost history in database  
⚠️ **Dashboard integration** - Make cost tracking more prominent  

### **Verdict:**

**We're doing well!** Our cost tracking system is similar to LangChain's LangSmith, with automatic tracking, multi-provider support, and cost breakdown. The main difference is LangSmith has a dedicated UI dashboard, while we integrate cost tracking into our execution views.

---

**Last Updated**: December 2025

