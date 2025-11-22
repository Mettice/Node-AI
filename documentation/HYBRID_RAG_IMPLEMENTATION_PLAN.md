# Hybrid RAG Implementation Plan

## Overview

Implementing Hybrid RAG system that combines:
- **Vector Search** (semantic similarity) - ✅ Already have
- **Knowledge Graph** (structured relationships) - 🆕 Need to add
- **LLM Orchestration** (intelligent routing) - ✅ Already have

---

## Phase 1: Neo4j Knowledge Graph Node (Week 1-2)

### 1.1 Neo4j Node - Foundation

**File**: `backend/nodes/storage/knowledge_graph.py`

**Features**:
- Connect to Neo4j database
- Create/read/update/delete nodes and relationships
- Execute Cypher queries
- Import/export graph data
- Graph schema management

**Schema**:
```python
{
  "operation": "create_node|create_relationship|query|import|export",
  "neo4j_uri": str,
  "neo4j_user": str,
  "neo4j_password": str,
  "cypher_query": str,  # For custom queries
  "node_labels": list,  # For node operations
  "relationship_type": str,  # For relationship operations
  "properties": dict,  # Node/relationship properties
}
```

**Operations**:
- `create_node`: Create a node with labels and properties
- `create_relationship`: Create relationship between nodes
- `query`: Execute custom Cypher query
- `import`: Import graph from JSON/CSV
- `export`: Export graph to JSON

---

## Phase 2: Hybrid Retrieval Node (Week 2-3)

### 2.1 Hybrid Retrieval Node

**File**: `backend/nodes/retrieval/hybrid_retrieval.py`

**Features**:
- Combine vector search + graph queries
- Intelligent routing (when to use which)
- Result fusion (merge results from both sources)
- Configurable weights

**Schema**:
```python
{
  "query": str,
  "vector_search_config": dict,  # Vector search settings
  "graph_query_config": dict,  # Graph query settings
  "fusion_method": "reciprocal_rank|weighted|rrf",  # Result fusion
  "vector_weight": float,  # Weight for vector results (default: 0.7)
  "graph_weight": float,  # Weight for graph results (default: 0.3)
  "top_k": int,  # Final number of results
}
```

**Workflow**:
1. User query comes in
2. Run vector search (semantic similarity)
3. Run graph query (relationship queries)
4. Fuse results using chosen method
5. Return combined results

---

## Phase 3: Relationship Query Tools (Week 3-4)

### 3.1 Pre-built Graph Query Tools

**File**: `backend/nodes/retrieval/graph_tools.py`

**Purpose**: Pre-built Cypher queries for common patterns

**Tools**:
1. **Find Related Entities**
   - Find all entities related to a given entity
   - Example: "Find all papers by this author"

2. **Find Paths**
   - Find paths between two entities
   - Example: "How is author A connected to author B?"

3. **Find Communities**
   - Find clusters/communities in graph
   - Example: "Find research groups"

4. **Find Influencers**
   - Find highly connected nodes
   - Example: "Find most cited authors"

5. **Find Similar Entities**
   - Find entities with similar relationships
   - Example: "Find authors with similar citation patterns"

---

## Phase 4: LLM Tool-Calling Integration (Week 4-5)

### 4.1 Intelligent Query Routing

**Integration**: Use existing LangChain/CrewAI agents

**How it works**:
1. User asks question
2. LLM analyzes query
3. LLM decides which tools to call:
   - Vector search tool (for semantic queries)
   - Graph query tools (for relationship queries)
   - Or both (for hybrid queries)
4. Execute selected tools
5. Combine results
6. Return answer

**Implementation**:
- Add graph tools to agent tool registry
- Create tool descriptions for LLM
- Integrate with existing agent nodes

---

## Phase 5: Frontend Integration (Week 5-6)

### 5.1 UI Components

**Neo4j Node UI**:
- Connection form (URI, user, password)
- Operation selector
- Cypher query editor
- Graph visualization (optional)

**Hybrid Retrieval Node UI**:
- Query input
- Vector search config
- Graph query config
- Fusion method selector
- Weight sliders
- Results display (showing source: vector/graph/both)

**Graph Tools UI**:
- Tool selector
- Parameter inputs
- Results visualization

---

## Phase 6: Documentation & Examples (Week 6)

### 6.1 Example Workflows

1. **Biomedical Research** (from LinkedIn post)
   - Vector search for semantic similarity
   - Graph query for author networks
   - Combine for comprehensive results

2. **Legal Documents**
   - Vector search for case similarity
   - Graph query for citation networks
   - Combine for precedent analysis

3. **Enterprise Knowledge**
   - Vector search for document similarity
   - Graph query for organizational relationships
   - Combine for knowledge discovery

---

## Implementation Order

1. ✅ **Neo4j Node** (Foundation)
2. ✅ **Hybrid Retrieval Node** (Core feature)
3. ✅ **Graph Query Tools** (Pre-built queries)
4. ✅ **LLM Integration** (Intelligent routing)
5. ✅ **Frontend UI** (User experience)
6. ✅ **Documentation** (Examples and guides)

---

## Dependencies

**New Python Packages**:
- `neo4j` - Neo4j Python driver
- `networkx` (optional) - Graph analysis

**Configuration**:
- Add Neo4j connection settings to `config.py`
- Add Neo4j credentials to environment variables

---

## Testing Strategy

1. **Unit Tests**: Test each node independently
2. **Integration Tests**: Test hybrid retrieval workflow
3. **Example Tests**: Test with real-world scenarios
4. **Performance Tests**: Measure latency and throughput

---

## Success Metrics

1. ✅ Can connect to Neo4j
2. ✅ Can execute graph queries
3. ✅ Can combine vector + graph results
4. ✅ LLM can intelligently route queries
5. ✅ Results are better than vector-only or graph-only

---

## Next Steps

1. Start with Neo4j node implementation
2. Test with sample graph data
3. Build hybrid retrieval node
4. Integrate with existing vector search
5. Add frontend UI
6. Create example workflows

**Let's begin!** 🚀

