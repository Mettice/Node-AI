# Phase 1: Core Engine & First Nodes

**Duration:** Week 2-3  
**Status:** 🔄 Not Started  
**Prerequisites:** [Phase 0: Foundation & Setup](./PHASE_0_FOUNDATION.md)

---

## 🎯 Goals

- Build workflow execution engine
- Implement base node architecture
- Create 5-6 essential nodes
- Test with simple workflows via API

---

## 📋 Tasks

### Backend: Core Engine

#### 1. Data Models (`backend/core/models.py`)

- [ ] **Workflow Model**
  ```python
  class Workflow(BaseModel):
      id: str
      name: str
      description: Optional[str]
      nodes: List[Node]
      edges: List[Edge]
      created_at: datetime
      updated_at: datetime
  ```

- [ ] **Node Model**
  ```python
  class Node(BaseModel):
      id: str
      type: str  # node type identifier
      position: Position  # x, y coordinates
      data: Dict[str, Any]  # node configuration
  ```

- [ ] **Edge Model**
  ```python
  class Edge(BaseModel):
      id: str
      source: str  # source node id
      target: str  # target node id
      sourceHandle: Optional[str]
      targetHandle: Optional[str]
  ```

- [ ] **Execution Model**
  ```python
  class Execution(BaseModel):
      id: str
      workflow_id: str
      status: ExecutionStatus  # pending, running, completed, failed
      started_at: datetime
      completed_at: Optional[datetime]
      total_cost: float
      results: Dict[str, NodeResult]
      trace: List[ExecutionStep]
  ```

- [ ] **NodeResult Model**
  ```python
  class NodeResult(BaseModel):
      node_id: str
      status: NodeStatus
      output: Optional[Dict[str, Any]]
      error: Optional[str]
      cost: float
      duration_ms: int
      started_at: datetime
      completed_at: datetime
  ```

- [ ] **ExecutionStep Model** (for tracing)
  ```python
  class ExecutionStep(BaseModel):
      node_id: str
      timestamp: datetime
      action: str  # started, completed, error
      data: Optional[Dict[str, Any]]
  ```

#### 2. Base Node Class (`backend/nodes/base.py`)

- [ ] Create abstract `BaseNode` class:
  ```python
  from abc import ABC, abstractmethod
  
  class BaseNode(ABC):
      node_type: str
      name: str
      description: str
      category: str
      
      @abstractmethod
      async def execute(
          self, 
          inputs: Dict[str, Any], 
          config: Dict[str, Any]
      ) -> Dict[str, Any]:
          """Execute the node logic"""
          pass
      
      @abstractmethod
      def get_schema(self) -> Dict[str, Any]:
          """Return JSON schema for node configuration"""
          pass
      
      def validate(self, config: Dict[str, Any]) -> bool:
          """Validate node configuration"""
          pass
      
      def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
          """Estimate cost before execution"""
          return 0.0
  ```

- [ ] Add error handling structure
- [ ] Add cost tracking hooks
- [ ] Add logging hooks

#### 3. Node Registry (`backend/core/node_registry.py`)

- [ ] Implement registry pattern:
  ```python
  class NodeRegistry:
      _nodes: Dict[str, Type[BaseNode]] = {}
      
      @classmethod
      def register(cls, node_type: str, node_class: Type[BaseNode]):
          """Register a node type"""
          
      @classmethod
      def get(cls, node_type: str) -> Type[BaseNode]:
          """Get node class by type"""
          
      @classmethod
      def list_all(cls) -> List[Dict[str, Any]]:
          """List all registered nodes with metadata"""
  ```

- [ ] Auto-discovery of nodes
  - Scan `backend/nodes/` directory
  - Auto-register all node classes
- [ ] Node metadata collection
  - Name, description, category
  - Input/output schemas
  - Configuration schema

#### 4. Workflow Engine (`backend/core/engine.py`)

- [ ] **Parse Workflow JSON**
  - Validate workflow structure
  - Validate nodes and edges
  - Check for circular dependencies

- [ ] **Build Execution Graph**
  - Create dependency graph from edges
  - Topological sort for execution order
  - Detect parallel execution opportunities

- [ ] **Execute Nodes**
  - Execute nodes in correct order
  - Handle dependencies (pass outputs as inputs)
  - Support parallel execution where possible
  - Track execution state

- [ ] **Collect Results**
  - Aggregate node results
  - Calculate total cost
  - Build execution trace
  - Handle errors gracefully

- [ ] **Error Propagation**
  - Stop execution on critical errors
  - Continue execution on non-critical errors (optional)
  - Collect all errors for reporting

#### 5. Cost Tracker (`backend/utils/cost_tracker.py`)

- [ ] Cost calculation for each node type:
  - OpenAI embeddings: tokens × price per token
  - OpenAI chat: input tokens + output tokens × price
  - Vector storage: per vector pricing (if applicable)
- [ ] Token counting utilities:
  - Use `tiktoken` for accurate token counting
  - Support different models
- [ ] Cost aggregation:
  - Sum costs across all nodes
  - Track costs by category
- [ ] Cost estimation:
  - Estimate before execution
  - Update during execution

---

### Backend: First Nodes (MVP Set)

#### 1. Text Input Node (`backend/nodes/input/text_input.py`)

- [ ] Implement node:
  - Accept text string in config
  - Output: `{"text": str}`
- [ ] Configuration schema:
  ```json
  {
    "type": "object",
    "properties": {
      "text": {
        "type": "string",
        "title": "Text Input",
        "description": "Enter text to process"
      }
    },
    "required": ["text"]
  }
  ```
- [ ] Unit tests

#### 2. Text Splitter Node (`backend/nodes/processing/chunk.py`)

- [ ] Implement recursive text splitting:
  - Use LangChain's RecursiveCharacterTextSplitter
  - Or implement custom splitter
- [ ] Configuration:
  - `chunk_size`: int (default: 512 tokens)
  - `chunk_overlap`: int (default: 50 tokens)
  - `separators`: List[str] (optional)
- [ ] Output: `{"chunks": List[str]}`
- [ ] Token counting for chunk size
- [ ] Unit tests

#### 3. OpenAI Embed Node (`backend/nodes/embedding/openai_embed.py`)

- [ ] Implement OpenAI embeddings API:
  - Use `openai.embeddings.create()`
  - Support batch processing
- [ ] Configuration:
  - `model`: str (default: "text-embedding-3-small")
  - `batch_size`: int (default: 100)
- [ ] Output: `{"embeddings": List[List[float]]}`
- [ ] Cost tracking:
  - Calculate cost based on tokens
  - Track API usage
- [ ] Error handling:
  - Rate limit handling
  - Retry logic
- [ ] Unit tests with mocks

#### 4. FAISS Store Node (`backend/nodes/storage/faiss_store.py`)

- [ ] Implement in-memory FAISS index:
  - Create FAISS index
  - Store vectors with metadata
  - Support different index types (Flat, IVF, HNSW)
- [ ] Configuration:
  - `index_type`: str (default: "Flat")
  - `dimension`: int (auto-detect from embeddings)
- [ ] Output: `{"index_id": str, "vectors_stored": int}`
- [ ] Store index in memory (use dict to track by index_id)
- [ ] Unit tests

#### 5. Vector Search Node (`backend/nodes/retrieval/search.py`)

- [ ] Implement FAISS search:
  - Load index by index_id
  - Embed query text
  - Search for top-k results
  - Return results with scores
- [ ] Configuration:
  - `query`: str (query text)
  - `top_k`: int (default: 5)
  - `score_threshold`: float (optional, default: 0.0)
  - `index_id`: str (from previous store node)
- [ ] Output: `{"results": List[{"text": str, "score": float, "metadata": dict}]}`
- [ ] Requires embedding node in workflow (for query embedding)
- [ ] Unit tests

#### 6. OpenAI Chat Node (`backend/nodes/llm/openai_chat.py`)

- [ ] Implement OpenAI chat completion:
  - Use `openai.chat.completions.create()`
  - Support system and user prompts
  - Template variable substitution
- [ ] Configuration:
  - `model`: str (default: "gpt-3.5-turbo")
  - `temperature`: float (default: 0.7)
  - `max_tokens`: int (default: 500)
  - `system_prompt`: str (optional)
  - `user_prompt_template`: str (with {variables})
- [ ] Template variable substitution:
  - Replace `{context}` with retrieved chunks
  - Replace `{query}` with user query
  - Support custom variables
- [ ] Output: `{"response": str, "tokens_used": int, "cost": float}`
- [ ] Cost tracking:
  - Track input and output tokens separately
  - Calculate cost based on model pricing
- [ ] Unit tests with mocks

---

### Backend: API Endpoints

#### 1. Workflow Execution (`backend/api/execution.py`)

- [ ] `POST /api/v1/workflows/execute`
  - Accept workflow JSON
  - Execute workflow
  - Return execution ID
  - Support async execution (return immediately)
  
- [ ] `GET /api/v1/executions/{execution_id}`
  - Get execution status and results
  - Return full execution data
  
- [ ] `GET /api/v1/executions/{execution_id}/trace`
  - Get detailed execution trace
  - Return step-by-step timeline

- [ ] `POST /api/v1/workflows/execute/sync` (optional)
  - Synchronous execution
  - Wait for completion
  - Return results directly

#### 2. Node Information (`backend/api/nodes.py`)

- [ ] `GET /api/v1/nodes`
  - List all available nodes
  - Return node metadata (name, description, category)
  
- [ ] `GET /api/v1/nodes/{node_type}`
  - Get node schema
  - Return configuration schema
  - Return input/output schemas

#### 3. Health & Info (`backend/api/health.py`)

- [ ] `GET /api/v1/health`
  - Check API health
  - Return status and version
  
- [ ] `GET /api/v1/info`
  - Get API information
  - Return available nodes, version, etc.

---

### Backend: Storage

#### 1. Workflow Store (`backend/storage/workflow_store.py`)

- [ ] Save workflow to JSON file:
  - Store in `data/workflows/` directory
  - Use workflow ID as filename
  - Include metadata (created_at, updated_at)
  
- [ ] Load workflow from JSON:
  - Load by workflow ID
  - Validate structure
  - Return workflow object
  
- [ ] List workflows:
  - List all saved workflows
  - Return metadata only (not full workflow)

#### 2. Execution Store (`backend/storage/execution_store.py`)

- [ ] Save execution trace:
  - Store in `data/executions/` directory
  - Use execution ID as filename
  - Include full trace data
  
- [ ] Load execution history:
  - Load by execution ID
  - List executions for a workflow
  - Support pagination

---

### Testing

#### 1. Unit Tests

- [ ] Test each node individually:
  - `test_text_input_node.py`
  - `test_chunk_node.py`
  - `test_openai_embed_node.py`
  - `test_faiss_store_node.py`
  - `test_vector_search_node.py`
  - `test_openai_chat_node.py`

- [ ] Test core engine:
  - `test_engine.py` - Workflow execution
  - `test_node_registry.py` - Node registration
  - `test_cost_tracker.py` - Cost calculations

#### 2. Integration Tests

- [ ] Test API endpoints:
  - `test_execution_api.py`
  - `test_nodes_api.py`
  - `test_health_api.py`

- [ ] Test workflow execution:
  - Simple linear workflow
  - Workflow with dependencies
  - Error handling

#### 3. End-to-End Test

- [ ] Simple RAG workflow test:
  ```python
  async def test_simple_rag_workflow():
      workflow = {
          "nodes": [
              {"id": "1", "type": "text_input", "data": {"text": "Hello world"}},
              {"id": "2", "type": "chunk", "data": {"chunk_size": 100}},
              {"id": "3", "type": "openai_embed", "data": {"model": "text-embedding-3-small"}},
              {"id": "4", "type": "faiss_store", "data": {}},
              {"id": "5", "type": "vector_search", "data": {"query": "hello", "top_k": 3}},
              {"id": "6", "type": "openai_chat", "data": {"model": "gpt-3.5-turbo"}}
          ],
          "edges": [
              {"source": "1", "target": "2"},
              {"source": "2", "target": "3"},
              {"source": "3", "target": "4"},
              {"source": "4", "target": "5"},
              {"source": "5", "target": "6"}
          ]
      }
      
      result = await engine.execute(workflow)
      assert result.status == "completed"
      assert result.total_cost > 0
  ```

---

## ✅ Deliverables Checklist

- [ ] Workflow engine executes simple workflows
- [ ] 5-6 core nodes working
- [ ] API endpoints functional
- [ ] Can test with curl/Postman
- [ ] Cost tracking working
- [ ] Execution traces saved
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] E2E test passing

---

## 🧪 Example Test Workflow

```json
{
  "nodes": [
    {
      "id": "1",
      "type": "text_input",
      "data": {
        "text": "The quick brown fox jumps over the lazy dog. This is a test document for RAG workflow."
      }
    },
    {
      "id": "2",
      "type": "chunk",
      "data": {
        "chunk_size": 50,
        "chunk_overlap": 10
      }
    },
    {
      "id": "3",
      "type": "openai_embed",
      "data": {
        "model": "text-embedding-3-small"
      }
    },
    {
      "id": "4",
      "type": "faiss_store",
      "data": {
        "index_type": "Flat"
      }
    },
    {
      "id": "5",
      "type": "vector_search",
      "data": {
        "query": "What is the document about?",
        "top_k": 3
      }
    },
    {
      "id": "6",
      "type": "openai_chat",
      "data": {
        "model": "gpt-3.5-turbo",
        "system_prompt": "You are a helpful assistant.",
        "user_prompt_template": "Context: {context}\n\nQuestion: {query}\n\nAnswer:"
      }
    }
  ],
  "edges": [
    {"source": "1", "target": "2"},
    {"source": "2", "target": "3"},
    {"source": "3", "target": "4"},
    {"source": "4", "target": "5"},
    {"source": "5", "target": "6"}
  ]
}
```

---

## 🧪 Testing with curl

```bash
# Execute a workflow
curl -X POST http://localhost:8000/api/v1/workflows/execute \
  -H "Content-Type: application/json" \
  -d @examples/simple_rag.json

# Get execution status
curl http://localhost:8000/api/v1/executions/{execution_id}

# Get execution trace
curl http://localhost:8000/api/v1/executions/{execution_id}/trace

# List available nodes
curl http://localhost:8000/api/v1/nodes

# Get node schema
curl http://localhost:8000/api/v1/nodes/text_input
```

---

## 📝 Notes

- Start with simple nodes, add complexity later
- Mock external APIs in tests
- Use async/await for all I/O operations
- Handle errors gracefully
- Log execution steps for debugging
- Track costs accurately

---

## 🔗 Related Files

- `backend/core/engine.py` - Workflow execution engine
- `backend/core/models.py` - Data models
- `backend/nodes/base.py` - Base node class
- `backend/core/node_registry.py` - Node registry
- `backend/utils/cost_tracker.py` - Cost tracking

---

## ➡️ Next Phase

Once Phase 1 is complete, proceed to [Phase 2: Frontend Canvas](./PHASE_2_FRONTEND_CANVAS.md)

