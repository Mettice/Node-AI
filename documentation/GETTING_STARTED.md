# Getting Started with NodAI

Welcome to NodAI! This guide will help you get up and running with the visual AI workflow builder.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (for backend)
- **Node.js 18+** (for frontend)
- **API Keys** for the services you want to use:
  - OpenAI (for embeddings and chat)
  - Anthropic (for Claude models)
  - Google Gemini (optional)
  - Pinecone (optional, for vector storage)

### Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd Nodeflow
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GEMINI_API_KEY=your-gemini-key  # Optional

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS (for production, set your frontend domain)
CORS_ORIGINS_STR=http://localhost:5173,https://yourdomain.com

# Sentry (optional, for error tracking)
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=development

# JWT Secret (change in production!)
JWT_SECRET_KEY=your-secret-key-change-in-production
```

#### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### 5. Start Backend Server

```bash
cd backend

# Start with auto-reload
uvicorn backend.main:app --reload

# Or run directly
python -m backend.main
```

The backend will be available at `http://localhost:8000`  
The frontend will be available at `http://localhost:5173`

---

## 📖 Your First Workflow

### Step 1: Create a Simple RAG Workflow

1. **Open the Canvas**
   - Click the "+" button on the canvas to add nodes

2. **Add a Text Input Node**
   - Search for "Text Input" in the node palette
   - Drag it to the canvas
   - Enter a test query: "What is artificial intelligence?"

3. **Add a Chat Node**
   - Search for "Chat" in the node palette
   - Connect it to the Text Input node
   - Configure:
     - Provider: OpenAI
     - Model: gpt-3.5-turbo
     - Prompt: "Answer this question: {{text_input.text}}"

4. **Save the Workflow**
   - Click "Save" in the top toolbar
   - Give it a name: "My First Workflow"

5. **Run the Workflow**
   - Click the "Run" button
   - Watch the execution in real-time!

### Step 2: Build a Complete RAG Pipeline

1. **Add a File Loader Node**
   - Upload a PDF or text file
   - This will extract text from the file

2. **Add a Chunk Node**
   - Connect it to the File Loader
   - Set chunk size: 500
   - Set overlap: 50

3. **Add an Embed Node**
   - Connect it to the Chunk node
   - Choose provider: OpenAI
   - Model: text-embedding-3-small

4. **Add a Vector Store Node**
   - Connect it to the Embed node
   - Choose storage: FAISS
   - This stores your embeddings

5. **Add a Vector Search Node**
   - Connect it to the Vector Store
   - Set top_k: 5
   - This retrieves relevant chunks

6. **Add a Chat Node**
   - Connect it to the Vector Search
   - Use the retrieved context in your prompt:
     ```
     Context: {{vector_search.results}}
     Question: {{text_input.text}}
     
     Answer the question using the context above.
     ```

7. **Save and Run**
   - Save your workflow
   - Run it to see the complete RAG pipeline in action!

---

## 🎯 Common Workflows

### 1. Document Q&A

**Use Case:** Answer questions about uploaded documents

**Nodes:**
- File Loader → Chunk → Embed → Vector Store
- Text Input → Vector Search → Chat

**Configuration:**
- Chunk size: 500-1000 tokens
- Top K: 3-5 chunks
- Model: gpt-4 or claude-3-opus for best results

### 2. Content Summarization

**Use Case:** Summarize long documents

**Nodes:**
- File Loader → Chunk → Chat (with summarization prompt)

**Configuration:**
- Chunk size: 2000 tokens
- Prompt: "Summarize the following text in 3-5 bullet points: {{chunk.text}}"

### 3. Multi-Agent Workflow

**Use Case:** Complex tasks requiring multiple AI agents

**Nodes:**
- Text Input → CrewAI Agent → Chat

**Configuration:**
- Use CrewAI for agent coordination
- Define roles and tasks for each agent

---

## 🔧 Configuration Tips

### Node Configuration

- **Provider Selection:** Choose based on your needs:
  - OpenAI: Fast, reliable, good for most use cases
  - Anthropic: Better for complex reasoning
  - Google Gemini: Good for multimodal tasks

- **Model Selection:**
  - **Embeddings:** `text-embedding-3-small` (cost-effective) or `text-embedding-3-large` (better quality)
  - **Chat:** `gpt-3.5-turbo` (fast, cheap) or `gpt-4` (better quality)
  - **Vision:** `gpt-4-vision-preview` for image understanding

### Chunking Strategy

- **Small chunks (200-500 tokens):** Better precision, more chunks
- **Large chunks (1000-2000 tokens):** Better context, fewer chunks
- **Overlap (10-20%):** Prevents information loss at boundaries

### Vector Storage

- **FAISS (Local):** Fast, free, good for development
- **Pinecone:** Managed, scalable, good for production
- **Gemini File Search:** Automatic chunking and indexing

---

## 🚀 Deployment

### Deploy a Workflow

1. **Build your workflow** on the canvas
2. **Test it** using the Run button
3. **Click "Deploy"** in the top toolbar
4. **Get your API endpoint:**
   ```
   POST /api/v1/workflows/{workflow_id}/query
   ```

### Query a Deployed Workflow

**Using cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "input": {
      "query": "Your question here"
    }
  }'
```

**Using Python SDK:**
```python
from nodai import NodAI

client = NodAI(api_key="your-api-key")
result = client.query_workflow(
    workflow_id="your-workflow-id",
    input={"query": "Your question here"}
)
print(result)
```

**Using JavaScript SDK:**
```javascript
import { NodAI } from '@nodai/sdk';

const client = new NodAI({ apiKey: 'your-api-key' });
const result = await client.queryWorkflow('workflow-id', {
  input: { query: 'Your question here' }
});
console.log(result);
```

---

## 📊 Monitoring & Analytics

### View Metrics

1. **Open Dashboard** (click the dashboard icon in sidebar)
2. **Select "Metrics" tab**
3. **Choose a workflow** to see:
   - Total queries
   - Success rate
   - Average response time
   - Total cost

### Deployment Management

1. **Open Dashboard**
2. **Select "Deployments" tab**
3. **View deployment versions:**
   - Version history
   - Health status
   - Rollback to previous versions

---

## 🔐 API Keys

### Create an API Key

1. **Open Dashboard**
2. **Select "API Keys" tab**
3. **Click "Create API Key"**
4. **Configure:**
   - Name: Descriptive name
   - Rate limit: Requests per hour
   - Cost limit: Maximum cost per hour
5. **Copy the key** (shown only once!)

### Use API Keys

Include the API key in requests:

```bash
curl -H "X-API-Key: your-api-key" ...
```

---

## 🐛 Troubleshooting

### Common Issues

**1. "Node execution failed"**
- Check API keys are configured
- Verify node configuration
- Check execution logs in the right sidebar

**2. "Workflow validation failed"**
- Ensure all nodes are connected properly
- Check for circular dependencies
- Verify required fields are filled

**3. "Rate limit exceeded"**
- Check your API key rate limits
- Wait before retrying
- Consider upgrading your plan

**4. "File upload failed"**
- Check file size (max 50MB)
- Verify file type is supported
- Check file isn't corrupted

### Getting Help

- **Documentation:** Check the `/documentation` folder
- **Logs:** View execution logs in the right sidebar
- **Error Tracking:** Check Sentry (if configured)

---

## 📚 Next Steps

1. **Explore Node Types:** Try different node types and configurations
2. **Build Complex Workflows:** Combine multiple nodes for advanced use cases
3. **Deploy to Production:** Deploy workflows and integrate with your applications
4. **Monitor Performance:** Use the metrics dashboard to optimize costs and performance

---

## 🎓 Learning Resources

- **Example Workflows:** Check the `data/workflows/` folder
- **API Documentation:** Visit `/docs` when backend is running
- **Node Documentation:** Hover over nodes to see descriptions
- **Video Tutorials:** Coming soon!

---

**Happy Building! 🚀**

