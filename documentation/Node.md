 Node Types (MVP - Keep It Lean)
Input Nodes (3 total):
javascript1. Upload File Node
   - Accept: PDF, DOCX, TXT, MD
   - Config: Auto-parse toggle
   - Output: Raw text + metadata

2. Text Input Node
   - Manual text entry
   - For testing/quick demos
   - Output: Text string

3. API Fetch Node
   - Pull from external source
   - Config: URL, headers, auth
   - Output: Fetched content

Processing Nodes (4 total):
javascript1. Text Splitter Node
   Config:
   - Strategy: [Recursive | Semantic | Fixed Size]
   - Size: 512 tokens (slider)
   - Overlap: 50 tokens (slider)
   
   Visualization:
   Shows: X chunks created, avg tokens per chunk
   Test output: Preview first 3 chunks

2. PDF Parser Node
   Config:
   - Extract tables: [Yes/No]
   - OCR for images: [Yes/No]
   - Page range: [All | Custom]
   
   Shows: Pages processed, images found, tables found

3. Metadata Enricher Node
   Config:
   - Auto-extract dates: [Yes/No]
   - Add source filename: [Yes/No]
   - Custom fields: [Key-Value pairs]
   
   Shows: Metadata preview

4. Filter Node
   Config:
   - Condition: [Contains | RegEx | Length]
   - Value: [Input field]
   - Action: [Keep | Remove]
   
   Shows: Chunks before/after filtering

Embedding Nodes (3 total):
javascript1. OpenAI Embeddings Node
   Config:
   - Model: [text-embedding-3-large | -small]
   - Dimensions: [1536 | 3072] (auto-set)
   - Batch size: 100 (for optimization)
   
   Shows: 
   - Embeddings created: X
   - Cost: $X
   - Time: Xs

2. HuggingFace Node
   Config:
   - Model: [Dropdown of popular models]
   - Custom endpoint: [Optional]
   
   Shows: Embedding dimensions, processing speed

3. Cohere Node
   Config:
   - Model: [embed-english-v3.0 | multilingual]
   - Input type: [search_document | search_query]

Storage Nodes (3 total):
javascript1. Pinecone Node
   Config:
   - API Key: [Input | Env var]
   - Index name: [Dropdown of existing]
   - Namespace: [Optional]
   - Create index: [Yes/No]
   
   Shows:
   - Vectors upserted: X
   - Index stats: X vectors total
   - Cost estimate

2. FAISS Node (In-Memory)
   Config:
   - Index type: [Flat | IVF | HNSW]
   - Persist to disk: [Yes/No]
   - File path: [If persisting]
   
   Shows:
   - Vectors stored: X
   - Memory usage: XMB
   - Search speed estimate

3. Supabase Node
   Config:
   - Project URL: [Input]
   - API Key: [Input]
   - Table name: [Input]
   
   Shows: Connection status, vectors stored

Retrieval Nodes (3 total):
javascript1. Vector Search Node
   Config:
   - Top-K: 5 (slider 1-20)
   - Score threshold: 0.7 (slider 0-1)
   - Metadata filters: [Optional]
   
   Shows:
   - Query: [Text]
   - Results found: X
   - Top score: 0.XX
   - Preview: Top 3 chunks with scores

2. Hybrid Search Node
   Config:
   - Vector weight: 0.7 (slider)
   - Keyword weight: 0.3 (slider)
   - Top-K: 5
   
   Shows: 
   - Vector results: X
   - Keyword results: X
   - Combined & re-ranked: X

3. Reranker Node
   Config:
   - Model: [Cohere | Cross-Encoder]
   - Top-N: 3 (final results)
   
   Shows:
   - Input: X candidates
   - Output: Y reranked
   - Score improvements

LLM Nodes (3 total):
javascript1. OpenAI Chat Node
   Config:
   - Model: [GPT-4 | GPT-3.5-turbo]
   - Temperature: 0.7 (slider)
   - Max tokens: 500
   - System prompt: [Textarea]
   - User prompt template: [With {context} {query} variables]
   
   Shows:
   - Tokens used: Input X + Output Y
   - Cost: $X
   - Response preview

2. Anthropic Claude Node
   Config:
   - Model: [Claude 3.5 Sonnet | Opus]
   - Temperature: 0.7
   - System prompt: [Textarea]
   
   Shows: Similar to OpenAI

3. Prompt Template Node
   Config:
   - Template: [Textarea with {variables}]
   - Variables: Auto-detected from {}
   - Preview: [Shows rendered prompt]

Output Nodes (3 total):
javascript1. Chat Widget Node
   Config:
   - Widget style: [Embedded | Popup | Fullscreen]
   - Primary color: [Color picker]
   - Welcome message: [Text]
   - Generate embed code: [Button]
   
   Shows: Live preview of chat widget

2. API Endpoint Node
   Config:
   - Endpoint name: [Input]
   - Authentication: [None | API Key | OAuth]
   - Rate limit: [Requests/min]
   
   Shows:
   - Generated endpoint: https://api.ragflow.io/v1/{name}
   - Curl example
   - SDK snippets (Python, JS)

3. Webhook Node
   Config:
   - URL: [Input]
   - Method: [POST | PUT]
   - Headers: [Key-Value]
   - Payload template: [JSON]
   
   Shows: Test button, last response
```

---

## 🎨 Killer Features (The Differentiators)

### **1. Real-Time Cost Tracking**
```
Top Navigation Bar:

[💰 Session Cost: $2.47]
├─ Embeddings: $0.23
├─ Vector Storage: $0.01
├─ LLM Calls: $2.18
└─ Reranking: $0.05

[Breakdown ▼] [Set Budget Alert]
```

Every node execution shows cost in real-time

---

### **2. Execution Tracing (Like Datadog for RAG)**
```
Trace View:

Query: "What is the refund policy?"
Total: 2.3s | Cost: $0.052 | Success ✅

Timeline:
├─ 0ms     [🔍] Vector Search Started
├─ 234ms   [✅] Retrieved 5 chunks (scores: 0.89-0.76)
├─ 235ms   [🤖] LLM Call Started
│   └─ Context: 1,247 tokens
│   └─ Model: GPT-4
├─ 2.1s    [✅] Response Generated (312 tokens)
└─ 2.3s    [📤] Response Returned

[View Prompt] [View Retrieved Chunks] [View Full Response]
```

---

### **3. Node Testing (Debug Each Step)**
```
Click any node → "Test Node" button

Before Testing:
[🔨 Text Splitter Node]
Status: Not tested
[Test with Sample Input ▼]

After Testing:
[🔨 Text Splitter Node]
Status: ✅ Passed (456ms)
Input: 5,234 tokens
Output: 12 chunks
Avg chunk size: 436 tokens

[View Output ▼]
Chunk 1: "Our refund policy states that..."
Chunk 2: "For digital products, refunds are..."
...

[Copy Output] [Run Again]
```

---

### **4. Error Highlighting**
```
If a node fails:

[🤖 LLM Node] ❌
Error: Rate limit exceeded (429)

Suggestions:
- Add retry logic
- Switch to GPT-3.5-turbo (cheaper, faster)
- Reduce batch size
- Check API key quota

[View Error Logs] [Auto-fix] [Skip This Node]
```

---

### **5. Version Control**
```
Workflow Versions:

v1.0.0 (Current) ✅ Deployed
├─ Basic RAG with GPT-4
└─ Deployed: 2 days ago

v0.9.0 (Previous)
├─ Used GPT-3.5, lower accuracy
└─ [Rollback] [Compare]

[New Version] [Tag Release]
```

---

## 🚀 Multi-Agent Support (Phase 2)

### **CrewAI Integration:**
```
New Node Category: 🤖 Agents

Agent Node:
┌────────────────────────────────┐
│ 🤖 Research Agent              │
├────────────────────────────────┤
│ Role: Research Specialist      │
│ Goal: [Textarea]               │
│ Backstory: [Textarea]          │
│ Tools:                         │
│ ☑ Web Search                   │
│ ☑ RAG Search (from workflow)   │
│ ☐ Calculator                   │
│                                │
│ LLM: [GPT-4 ▼]                │
│ Max iterations: 5              │
└────────────────────────────────┘

Crew Node:
┌────────────────────────────────┐
│ 🎬 Content Creation Crew       │
├────────────────────────────────┤
│ Agents:                        │
│ • Research Agent (Connected)   │
│ • Writer Agent (Connected)     │
│ • Editor Agent (Connected)     │
│                                │
│ Process: Sequential            │
│ Verbose: Yes                   │
│                                │
│ [Preview Execution Flow]       │
└────────────────────────────────┘

Visual Crew Execution:
┌─────────────────────────────────────┐
│ 🤖 Research Agent                   │
│ Status: ✅ Complete (12.3s)         │
│ Output: Found 8 sources, 24 stats   │
│    ↓                                │
│ 🤖 Writer Agent                     │
│ Status: ⏳ Writing... (45% done)    │
│ Output: 678 / 1500 words            │
│    ↓                                │
│ 🤖 Editor Agent                     │
│ Status: ⏸️ Waiting...               │
└─────────────────────────────────────┘
