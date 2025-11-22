# NodAI User Guide

Complete guide to using NodAI's visual AI workflow builder.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Interface Guide](#interface-guide)
3. [Building Workflows](#building-workflows)
4. [Node Reference](#node-reference)
5. [Deployment](#deployment)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

NodAI is a visual workflow builder for creating AI-powered applications. Build complex RAG pipelines, multi-agent systems, and data processing workflows without writing code.

### Key Concepts

- **Workflows:** Collections of connected nodes that process data
- **Nodes:** Individual processing units (input, processing, LLM, storage, etc.)
- **Edges:** Connections between nodes that define data flow
- **Execution:** Running a workflow to process data
- **Deployment:** Making a workflow available via API

---

## Interface Guide

### Main Components

#### 1. **Canvas**
- **Center area** where you build workflows
- **Drag and drop** nodes from the palette
- **Connect nodes** by dragging from output to input handles
- **Pan and zoom** to navigate large workflows

#### 2. **Node Palette**
- **Floating "+" button** on canvas opens the palette
- **Search** for nodes by name
- **Categories:**
  - Input: Text, File, Data Loader
  - Processing: Chunk, OCR, Transcribe
  - Embedding: OpenAI, Local models
  - Storage: FAISS, Pinecone, Database
  - LLM: Chat, Vision models
  - Agents: CrewAI, LangChain
  - Tools: Web Scraping, Email, etc.

#### 3. **Properties Panel**
- **Right sidebar** shows node configuration
- **Edit node settings** when a node is selected
- **View node outputs** after execution

#### 4. **Top Toolbar**
- **Workflow name:** Click to rename
- **Save:** Save current workflow
- **Undo/Redo:** Navigate history
- **Export:** Download workflow JSON
- **Deploy:** Make workflow available via API

#### 5. **Left Sidebar**
- **Utility icons** at the bottom:
  - 📚 Knowledge Base
  - ✏️ Prompt Playground
  - 🤖 Models
  - 🎯 Auto-tune
  - 📋 Templates
  - ❓ Help
  - ⚙️ Settings

#### 6. **Dashboard**
- **Overview:** Quick stats and recent activity
- **Workflows:** Manage all workflows
- **Query:** Test deployed workflows
- **API Keys:** Manage API keys
- **Deployments:** View deployment versions
- **Metrics:** Performance analytics
- **Analytics:** Advanced analytics

---

## Building Workflows

### Step-by-Step: Creating a Workflow

#### 1. **Start with Input**
- Add a **Text Input** node for queries
- Or add a **File Loader** for document processing
- Configure the input node with your data

#### 2. **Add Processing Nodes**
- **Chunk:** Split documents into smaller pieces
- **Embed:** Convert text to vectors
- **Process:** OCR, transcription, etc.

#### 3. **Add Storage (for RAG)**
- **Vector Store:** Store embeddings
- **Database:** Store structured data
- **Knowledge Base:** Manage document collections

#### 4. **Add Retrieval (for RAG)**
- **Vector Search:** Find relevant chunks
- **Rerank:** Improve search results
- **Filter:** Apply metadata filters

#### 5. **Add LLM**
- **Chat:** Generate responses
- **Vision:** Process images
- **Configure prompt** with template variables

#### 6. **Connect Nodes**
- **Drag from output handle** to input handle
- **Multiple connections** are allowed
- **Check data flow** in execution logs

#### 7. **Configure Nodes**
- **Click a node** to open properties
- **Fill required fields**
- **Set optional parameters**
- **Save configuration**

#### 8. **Test Your Workflow**
- **Click "Run"** button
- **Watch execution** in real-time
- **Check results** in properties panel
- **View logs** in right sidebar

#### 9. **Save and Deploy**
- **Save workflow** with a descriptive name
- **Deploy** when ready for production
- **Get API endpoint** for integration

---

## Node Reference

### Input Nodes

#### Text Input
- **Purpose:** Accept text input from users
- **Configuration:**
  - Text: Default text value
- **Output:** `text` field

#### File Loader
- **Purpose:** Load and extract text from files
- **Supported Formats:** PDF, DOCX, TXT, MD, Images, Audio, Video
- **Configuration:**
  - File ID: Upload file first, then select
- **Output:** `text`, `file_path`, `file_type`

#### Data Loader
- **Purpose:** Load structured data (CSV, JSON, etc.)
- **Configuration:**
  - Source: File or URL
  - Format: CSV, JSON, Parquet
- **Output:** `data` (structured data)

### Processing Nodes

#### Chunk
- **Purpose:** Split text into smaller chunks
- **Configuration:**
  - Chunk size: Tokens per chunk (default: 500)
  - Overlap: Overlapping tokens (default: 50)
  - Method: Character, Token, Semantic
- **Output:** `chunks` (array of text chunks)

#### Embed
- **Purpose:** Convert text to vector embeddings
- **Configuration:**
  - Provider: OpenAI, Anthropic, Local
  - Model: Embedding model name
- **Output:** `embeddings` (array of vectors)

#### OCR
- **Purpose:** Extract text from images
- **Configuration:**
  - Language: OCR language
- **Output:** `text` (extracted text)

#### Transcribe
- **Purpose:** Convert audio to text
- **Configuration:**
  - Language: Audio language
  - Model: Whisper model
- **Output:** `text` (transcription)

### Storage Nodes

#### Vector Store
- **Purpose:** Store and retrieve vector embeddings
- **Configuration:**
  - Storage: FAISS, Pinecone, Gemini File Search
  - Index ID: Unique identifier
- **Output:** `index_id`, `stored_count`

#### Database
- **Purpose:** Store structured data
- **Configuration:**
  - Type: SQLite, PostgreSQL, MySQL
  - Connection string
- **Output:** `connection_status`

### Retrieval Nodes

#### Vector Search
- **Purpose:** Find similar vectors
- **Configuration:**
  - Index ID: Vector store to search
  - Top K: Number of results (default: 5)
  - Query: Search query (from previous node)
- **Output:** `results` (array of similar chunks)

#### Rerank
- **Purpose:** Improve search result relevance
- **Configuration:**
  - Provider: Cohere, Cross-Encoder
  - Model: Reranking model
  - Top N: Results to rerank
- **Output:** `reranked_results`

### LLM Nodes

#### Chat
- **Purpose:** Generate text using LLMs
- **Configuration:**
  - Provider: OpenAI, Anthropic, Google
  - Model: Model name (e.g., gpt-4, claude-3-opus)
  - Prompt: Template with variables (e.g., `{{input.text}}`)
  - Temperature: Creativity (0.0-2.0)
  - Max tokens: Response length
- **Output:** `text` (generated response)

#### Vision
- **Purpose:** Process images with vision models
- **Configuration:**
  - Provider: OpenAI, Google
  - Model: Vision model
  - Prompt: Image description request
- **Output:** `text` (image description)

### Agent Nodes

#### CrewAI Agent
- **Purpose:** Multi-agent coordination
- **Configuration:**
  - Agents: Define agent roles and tasks
  - Tools: Available tools for agents
- **Output:** `result` (agent output)

#### LangChain Agent
- **Purpose:** LangChain agent execution
- **Configuration:**
  - Agent type: ReAct, Plan-and-Execute
  - Tools: Available tools
- **Output:** `result` (agent output)

---

## Deployment

### Deploying a Workflow

1. **Build and test** your workflow
2. **Click "Deploy"** in top toolbar
3. **Wait for deployment** (processes vector stores)
4. **Get API endpoint:**
   ```
   POST /api/v1/workflows/{workflow_id}/query
   ```

### Deployment Features

- **Version Management:** Track deployment versions
- **Rollback:** Revert to previous versions
- **Health Monitoring:** Real-time health status
- **Metrics:** Track queries, costs, performance

### Querying Deployed Workflows

**Input Format:**
```json
{
  "input": {
    "query": "Your question",
    "file_id": "optional-file-id"
  }
}
```

**Response Format:**
```json
{
  "execution_id": "uuid",
  "status": "completed",
  "results": {
    "node_id": {
      "output": {...},
      "cost": 0.001,
      "duration_ms": 500
    }
  },
  "total_cost": 0.001,
  "duration_ms": 500
}
```

---

## Best Practices

### Workflow Design

1. **Start Simple:** Build basic workflows first, then add complexity
2. **Test Incrementally:** Test each node as you add it
3. **Use Descriptive Names:** Name workflows and nodes clearly
4. **Document Your Workflows:** Add descriptions to workflows
5. **Version Control:** Save different versions for experimentation

### Performance Optimization

1. **Chunk Size:** Balance between context and precision
   - Small chunks (200-500): Better precision
   - Large chunks (1000-2000): Better context

2. **Top K Selection:** Retrieve only what you need
   - Start with 5-10 results
   - Increase if needed

3. **Model Selection:** Choose based on use case
   - Fast/Cheap: gpt-3.5-turbo
   - Quality: gpt-4, claude-3-opus
   - Embeddings: text-embedding-3-small (cost-effective)

4. **Caching:** Deploy workflows to enable caching
   - Vector stores are cached after deployment
   - Reduces processing time for queries

### Cost Management

1. **Monitor Costs:** Use the metrics dashboard
2. **Set Limits:** Configure API key cost limits
3. **Optimize Models:** Use cheaper models when possible
4. **Cache Results:** Deploy workflows to enable caching
5. **Batch Processing:** Process multiple items together

### Security

1. **API Keys:** Store securely, rotate regularly
2. **Input Validation:** Validate user inputs
3. **Rate Limiting:** Set appropriate rate limits
4. **Access Control:** Use API keys for authentication
5. **Data Privacy:** Be mindful of sensitive data

---

## Troubleshooting

### Common Issues

#### Workflow Won't Run

**Problem:** Workflow execution fails immediately

**Solutions:**
- Check all nodes are connected properly
- Verify required fields are filled
- Check for circular dependencies
- Review execution logs for errors

#### Node Execution Fails

**Problem:** Specific node fails during execution

**Solutions:**
- Check API keys are configured
- Verify node configuration
- Check input data format
- Review node-specific error messages

#### Poor Results

**Problem:** Workflow produces low-quality results

**Solutions:**
- Adjust chunk size
- Increase top K for retrieval
- Improve prompts
- Try different models
- Add reranking

#### High Costs

**Problem:** Workflow costs are too high

**Solutions:**
- Use cheaper models (gpt-3.5-turbo vs gpt-4)
- Reduce chunk size
- Decrease top K
- Enable caching (deploy workflow)
- Set cost limits on API keys

#### Slow Performance

**Problem:** Workflow execution is slow

**Solutions:**
- Deploy workflow (enables caching)
- Use faster models
- Reduce chunk size
- Optimize node order
- Check network latency

### Getting Help

1. **Check Logs:** View execution logs in right sidebar
2. **Review Documentation:** Check node descriptions
3. **Test Incrementally:** Isolate problematic nodes
4. **Check API Status:** Verify external APIs are working
5. **Error Tracking:** Check Sentry (if configured)

---

## Advanced Topics

### Template Variables

Use template variables in prompts to reference node outputs:

```
Context: {{vector_search.results}}
Question: {{text_input.text}}
Answer: [Your answer here]
```

Available variables:
- `{{node_id.field}}` - Access any node's output field
- `{{node_id}}` - Access entire node output object

### Custom Tools

Create custom tools for agents:

1. **Define tool schema** (JSON Schema)
2. **Implement tool function**
3. **Add to agent configuration**
4. **Use in workflow**

### Knowledge Bases

Manage document collections:

1. **Create Knowledge Base** in sidebar
2. **Upload documents**
3. **Configure processing** (chunk size, embed model)
4. **Process documents**
5. **Use in workflows** via Vector Store node

### Webhooks

Trigger workflows via HTTP:

1. **Add Webhook Input node** to workflow
2. **Configure webhook** (name, method)
3. **Get webhook URL**
4. **Send HTTP requests** to trigger workflow

---

## Next Steps

1. **Explore Examples:** Check example workflows
2. **Build Your Own:** Create workflows for your use cases
3. **Deploy:** Make workflows available via API
4. **Monitor:** Track performance and costs
5. **Optimize:** Improve based on metrics

---

**Happy Building! 🚀**

