# 💾 Persistent Cost Tracking System

## Overview

Nodeflow now has **persistent cost tracking** that stores all cost data in the database, enabling historical cost analysis, daily/weekly/monthly statistics, and detailed breakdowns by category, provider, and model.

---

## 🎯 Features

### **1. Database Persistence**
- All cost records are stored in the `cost_records` table
- Automatic aggregation into daily/weekly/monthly summaries
- Detailed breakdowns by category, provider, and model

### **2. Historical Analytics**
- View costs for any time period (daily, weekly, monthly)
- Track cost trends over time
- Compare costs across workflows, users, or time periods

### **3. Detailed Breakdowns**
- **By Category**: LLM, Embedding, Rerank, Vector Search, Other
- **By Provider**: OpenAI, Anthropic, Gemini, Cohere, etc.
- **By Model**: gpt-4o-mini, claude-sonnet-4, etc.

### **4. Automatic Aggregation**
- Database triggers automatically update aggregations
- No manual aggregation needed
- Real-time cost summaries

---

## 📊 Database Schema

### **cost_records Table**
Stores individual node-level cost records:

```sql
- id: UUID (primary key)
- execution_id: TEXT
- workflow_id: UUID (foreign key to workflows)
- user_id: UUID (foreign key to profiles)
- node_id: TEXT
- node_type: TEXT (e.g., 'chat', 'embed', 'rerank')
- cost: DECIMAL(10, 6)
- tokens_used: JSONB ({input: int, output: int, total: int})
- duration_ms: INTEGER
- provider: TEXT (e.g., 'openai', 'anthropic')
- model: TEXT (e.g., 'gpt-4o-mini')
- category: TEXT ('llm', 'embedding', 'rerank', 'vector_search', 'other')
- config: JSONB (node configuration)
- metadata: JSONB (additional metadata)
- created_at: TIMESTAMP
```

### **cost_aggregations Table**
Stores pre-aggregated cost summaries:

```sql
- id: UUID (primary key)
- workflow_id: UUID (optional)
- user_id: UUID (optional)
- period_type: TEXT ('daily', 'weekly', 'monthly')
- period_start: TIMESTAMP
- period_end: TIMESTAMP
- total_cost: DECIMAL(10, 6)
- total_executions: INTEGER
- cost_by_category: JSONB
- cost_by_provider: JSONB
- cost_by_model: JSONB
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

---

## 🔧 API Endpoints

### **1. Get Cost Statistics**
```http
GET /api/v1/cost/stats?period=daily&days=30&workflow_id=<uuid>&user_id=<uuid>
```

**Response:**
```json
{
  "total_cost": 125.50,
  "total_executions": 150,
  "total_records": 450,
  "period": "daily",
  "start_date": "2025-01-01T00:00:00",
  "end_date": "2025-01-31T23:59:59",
  "breakdown_by_category": {
    "llm": {"cost": 100.00, "count": 200},
    "embedding": {"cost": 20.00, "count": 150},
    "rerank": {"cost": 5.50, "count": 100}
  },
  "breakdown_by_provider": {
    "openai": {"cost": 80.00, "count": 180},
    "anthropic": {"cost": 20.00, "count": 20}
  },
  "breakdown_by_model": {
    "gpt-4o-mini": {"cost": 60.00, "count": 150},
    "claude-sonnet-4": {"cost": 20.00, "count": 20}
  },
  "period_data": [
    {
      "period": "2025-01-01T00:00:00",
      "total_cost": 4.50,
      "executions": 5,
      "records": 15
    },
    ...
  ]
}
```

### **2. Get Cost History**
```http
GET /api/v1/cost/history?limit=100&offset=0&workflow_id=<uuid>&start_date=2025-01-01&end_date=2025-01-31
```

**Response:**
```json
{
  "records": [
    {
      "id": "uuid",
      "execution_id": "exec-123",
      "workflow_id": "workflow-uuid",
      "user_id": "user-uuid",
      "node_id": "node-1",
      "node_type": "chat",
      "cost": 0.05,
      "tokens_used": {"input": 100, "output": 50, "total": 150},
      "duration_ms": 1200,
      "provider": "openai",
      "model": "gpt-4o-mini",
      "category": "llm",
      "config": {...},
      "metadata": {...},
      "created_at": "2025-01-15T10:30:00"
    },
    ...
  ],
  "count": 100,
  "limit": 100,
  "offset": 0
}
```

### **3. Get Cost Breakdown**
```http
GET /api/v1/cost/breakdown?group_by=category&days=30&workflow_id=<uuid>
```

**Response:**
```json
{
  "group_by": "category",
  "breakdown": {
    "llm": {"cost": 100.00, "count": 200},
    "embedding": {"cost": 20.00, "count": 150},
    "rerank": {"cost": 5.50, "count": 100}
  },
  "total_cost": 125.50
}
```

---

## 🔄 How It Works

### **1. During Execution**
When a workflow executes:

1. **Node executes** and calculates cost
2. **Cost stored in NodeResult** (in-memory)
3. **Engine aggregates** costs for execution
4. **Costs persisted to database** via `record_cost()`
5. **Database trigger** automatically updates aggregations

### **2. Cost Recording Flow**

```python
# In backend/core/engine.py
async def _record_execution_costs(...):
    # Build cost records from node results
    cost_records = [...]
    
    # Store in-memory (for immediate access)
    cost_intelligence._cost_history[execution_id] = cost_records
    
    # Persist to database (for historical tracking)
    for cost_record in cost_records:
        record_cost(
            execution_id=execution_id,
            workflow_id=workflow_id,
            user_id=user_id,
            node_id=node_id,
            node_type=node_type,
            cost=cost_value,
            category=category,  # 'llm', 'embedding', etc.
            provider=provider,  # 'openai', 'anthropic', etc.
            model=model,  # 'gpt-4o-mini', etc.
            tokens_used=tokens_used,
            duration_ms=duration_ms,
            ...
        )
```

### **3. Automatic Aggregation**

Database trigger (`update_cost_aggregations()`) automatically:
- Updates daily aggregations
- Updates weekly aggregations
- Updates monthly aggregations
- Maintains breakdowns by category, provider, and model

---

## 📈 Usage Examples

### **Get Daily Costs for Last 7 Days**
```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/cost/stats",
    params={
        "period": "daily",
        "days": 7,
        "user_id": "user-uuid"
    }
)

stats = response.json()
print(f"Total cost: ${stats['total_cost']:.2f}")
print(f"Daily breakdown:")
for day in stats['period_data']:
    print(f"  {day['period']}: ${day['total_cost']:.2f}")
```

### **Get Cost Breakdown by Provider**
```python
response = requests.get(
    "http://localhost:8000/api/v1/cost/breakdown",
    params={
        "group_by": "provider",
        "days": 30
    }
)

breakdown = response.json()
for provider, data in breakdown['breakdown'].items():
    print(f"{provider}: ${data['cost']:.2f} ({data['count']} records)")
```

### **Get Cost History with Pagination**
```python
response = requests.get(
    "http://localhost:8000/api/v1/cost/history",
    params={
        "limit": 50,
        "offset": 0,
        "workflow_id": "workflow-uuid"
    }
)

history = response.json()
for record in history['records']:
    print(f"{record['created_at']}: ${record['cost']:.6f} ({record['node_type']})")
```

---

## 🚀 Migration

To enable persistent cost tracking:

1. **Run the migration:**
   ```bash
   psql -d your_database -f backend/migrations/004_add_cost_tracking.sql
   ```

2. **Verify tables created:**
   ```sql
   SELECT * FROM cost_records LIMIT 1;
   SELECT * FROM cost_aggregations LIMIT 1;
   ```

3. **Test cost recording:**
   - Execute a workflow
   - Check `cost_records` table for new entries
   - Check `cost_aggregations` table for automatic aggregations

---

## 🔍 Benefits

### **1. Historical Analysis**
- Track costs over time
- Identify cost trends
- Compare periods

### **2. Detailed Insights**
- See which workflows cost the most
- Identify expensive models
- Optimize based on data

### **3. Budget Management**
- Set budgets per workflow/user
- Get alerts when approaching limits
- Track spending patterns

### **4. Performance**
- Pre-aggregated summaries (fast queries)
- Indexed for efficient lookups
- Automatic updates via triggers

---

## 📝 Notes

- **Zero-cost records** are not stored (filtered out)
- **Database persistence** is optional (gracefully handles missing DB)
- **In-memory cache** still maintained for immediate access
- **Automatic aggregation** happens via database triggers
- **User ID** is optional (works without authentication)

---

## 🔮 Future Enhancements

- [ ] Cost alerts and notifications
- [ ] Budget management UI
- [ ] Cost forecasting based on trends
- [ ] Export cost data (CSV, JSON)
- [ ] Cost comparison across workflows
- [ ] Cost optimization recommendations

---

**Last Updated**: January 2025

