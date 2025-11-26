# 🎯 Node Mapping: Workflows & Use Cases

**Complete guide to which nodes are used for each workflow type and use case**

---

## 📋 Table of Contents

1. [Workflow Types - Node Mapping](#workflow-types---node-mapping)
2. [Use Cases - Node Mapping](#use-cases---node-mapping)
3. [Node Categories Reference](#node-categories-reference)
4. [Complete Node List](#complete-node-list)

---

## 🔧 Workflow Types - Node Mapping

### 1. **RAG (Retrieval-Augmented Generation) Workflows** 📚

#### **Setup Phase (One-Time)**
```
File Loader → Chunk → Embed → Vector Store
```

**Nodes Used**:
1. **File Loader** (`file_loader`)
   - Upload documents (PDF, DOCX, TXT, etc.)
   - Extract text content
   - Output: `text`, `file_id`, `metadata`

2. **Chunk** (`chunk`)
   - Split documents into smaller pieces
   - Config: `chunk_size`, `overlap`, `chunking_strategy`
   - Output: `chunks` (array of text chunks)

3. **Embed** (`embed`)
   - Create vector embeddings from chunks
   - Providers: OpenAI, HuggingFace, Cohere, Voyage AI
   - Output: `embeddings` (array of vectors)

4. **Vector Store** (`vector_store`)
   - Store embeddings in vector database
   - Providers: FAISS, Pinecone, Chroma
   - Output: `index_id`, `metadata`

#### **Query Phase (Per Request)**
```
Text Input → Embed → Vector Search → Rerank → Chat → Output
```

**Nodes Used**:
1. **Text Input** (`text_input`)
   - User query/question
   - Output: `text`

2. **Embed** (`embed`)
   - Create embedding for query
   - Same provider as setup phase
   - Output: `embedding`

3. **Vector Search** (`vector_search`)
   - Search vector store for similar chunks
   - Config: `top_k`, `index_id`
   - Output: `results` (array of similar chunks with scores)

4. **Rerank** (`rerank`) ⚠️ *Optional but recommended*
   - Improve search result relevance
   - Providers: Cohere, Cross-Encoder
   - Output: `reranked_results` (sorted by relevance)

5. **Chat** (`chat`)
   - Generate answer using retrieved context
   - Providers: OpenAI, Anthropic, Google Gemini, Groq
   - Prompt template: `"Context: {{vector_search.results}}\nQuestion: {{text_input.text}}\nAnswer:"`
   - Output: `text` (generated response)

---

### 2. **Multi-Agent Workflows** 🤖

#### **Basic Multi-Agent Flow**
```
Text Input → CrewAI Agent → Output
```

**Nodes Used**:
1. **Text Input** (`text_input`)
   - Task description or prompt
   - Output: `text`

2. **CrewAI Agent** (`crewai_agent`)
   - Coordinate multiple AI agents
   - Config:
     - `agents`: Array of agent definitions (role, goal, backstory)
     - `tasks`: Array of task definitions
     - `verbose`: Enable detailed logging
   - Output: `result` (final output from crew execution)

#### **Enhanced Multi-Agent Flow (With Tools)**
```
Text Input ──┐
             ├→ CrewAI Agent → Output
Tool Node ───┘
```

**Additional Nodes**:
3. **Tool Node** (`tool`)
   - Define tools for agents to use
   - Tool types:
     - `web_search` - Search the web
     - `calculator` - Mathematical calculations
     - `web_scraping` - Scrape web pages
     - `api_call` - Call external APIs
     - `database_query` - Query databases
     - `code_execution` - Execute Python code
     - `email` - Send emails
     - `rss_feed` - Read RSS feeds
     - `s3_storage` - Store/retrieve from S3
     - `custom` - Custom tool definitions
   - Output: `tool_definition` (registered for agents)

4. **Memory Node** (`memory`) ⚠️ *Optional*
   - Store conversation history
   - Maintain context across workflow runs
   - Output: `memory` (conversation context)

#### **Alternative: LangChain Agent**
```
Text Input → LangChain Agent → Output
```

**Nodes Used**:
1. **Text Input** (`text_input`)
2. **LangChain Agent** (`langchain_agent`)
   - Single agent with tool access
   - Config: `agent_type`, `tools`, `model`
   - Output: `result`

---

### 3. **Document Processing Workflows** 📄

#### **PDF/Text Document Processing**
```
File Loader → Chunk → Process → Output
```

**Nodes Used**:
1. **File Loader** (`file_loader`)
   - Upload PDF, DOCX, TXT files
   - Extract text content
   - Output: `text`, `file_id`

2. **Chunk** (`chunk`)
   - Split into manageable pieces
   - Output: `chunks`

3. **Chat** (`chat`) or **Advanced NLP** (`advanced_nlp`)
   - Summarize, extract, or analyze
   - Output: `text` (processed result)

#### **Image Processing (OCR)**
```
File Loader → OCR → Chunk → Process → Output
```

**Nodes Used**:
1. **File Loader** (`file_loader`)
   - Upload image files (JPG, PNG, WebP)
   - Output: `file_id`, `file_path`

2. **OCR** (`ocr`)
   - Extract text from images
   - Provider: Tesseract
   - Output: `text` (extracted text)

3. **Chunk** (`chunk`) ⚠️ *If needed*
   - Split extracted text
   - Output: `chunks`

4. **Chat** (`chat`) or **Advanced NLP** (`advanced_nlp`)
   - Process extracted text
   - Output: `text`

#### **Audio Processing (Transcription)**
```
File Loader → Transcribe → Chunk → Process → Output
```

**Nodes Used**:
1. **File Loader** (`file_loader`)
   - Upload audio files (MP3, WAV)
   - Output: `file_id`, `file_path`

2. **Transcribe** (`transcribe`)
   - Convert audio to text
   - Provider: OpenAI Whisper
   - Output: `text` (transcription)

3. **Chunk** (`chunk`) ⚠️ *If needed*
   - Split transcription
   - Output: `chunks`

4. **Chat** (`chat`) or **Advanced NLP** (`advanced_nlp`)
   - Summarize or analyze transcription
   - Output: `text`

#### **Video Processing**
```
File Loader → Video Frames → OCR → Process → Output
```

**Nodes Used**:
1. **File Loader** (`file_loader`)
   - Upload video files (MP4, AVI)
   - Output: `file_id`, `file_path`

2. **Video Frames** (`video_frames`)
   - Extract frames from video
   - Config: `frame_interval`, `max_frames`
   - Output: `frames` (array of frame images)

3. **OCR** (`ocr`)
   - Extract text from frames
   - Output: `text`

4. **Chat** (`chat`) or **Advanced NLP** (`advanced_nlp`)
   - Process extracted content
   - Output: `text`

#### **Vision Processing (Image Analysis)**
```
File Loader → Vision → Output
```

**Nodes Used**:
1. **File Loader** (`file_loader`)
   - Upload images
   - Output: `file_id`, `file_path`

2. **Vision** (`vision`)
   - Analyze images with vision models
   - Providers: OpenAI GPT-4 Vision, Google Gemini Vision
   - Config: `prompt`, `model`
   - Output: `text` (image description/analysis)

---

### 4. **Data Transformation Workflows** 🔄

#### **Structured Data Processing**
```
Data Loader → Data to Text → Chat → Output
```

**Nodes Used**:
1. **Data Loader** (`data_loader`)
   - Load structured data
   - Formats: CSV, Excel, JSON, Parquet
   - Output: `data` (structured data object)

2. **Data to Text** (`data_to_text`)
   - Convert structured data to natural language
   - Config: `format`, `include_headers`
   - Output: `text` (natural language representation)

3. **Chat** (`chat`) or **Advanced NLP** (`advanced_nlp`)
   - Analyze, summarize, or extract insights
   - Output: `text` (analysis/insights)

#### **Advanced Data Analysis**
```
Data Loader → Advanced NLP → Output
```

**Nodes Used**:
1. **Data Loader** (`data_loader`)
2. **Advanced NLP** (`advanced_nlp`)
   - Multiple NLP tasks:
     - `summarization` - Summarize data
     - `classification` - Classify data points
     - `extraction` - Extract specific information
     - `sentiment_analysis` - Analyze sentiment
     - `translation` - Translate content
   - Providers: HuggingFace, Azure, OpenAI, Anthropic
   - Output: `result` (task-specific output)

---

### 5. **Hybrid RAG Workflows** 🔗

#### **Hybrid RAG Flow**
```
Text Input ──┬→ Embed → Vector Search ──┐
             │                           ├→ Hybrid Retrieval → Chat → Output
             └→ Knowledge Graph ─────────┘
```

**Nodes Used**:
1. **Text Input** (`text_input`)
   - User query
   - Output: `text`

2. **Embed** (`embed`)
   - Create query embedding
   - Output: `embedding`

3. **Vector Search** (`vector_search`)
   - Semantic similarity search
   - Output: `results` (vector search results)

4. **Knowledge Graph** (`knowledge_graph`)
   - Query knowledge graph for relationships
   - Operations:
     - `create_node` - Create nodes
     - `create_relationship` - Create relationships
     - `query` - Query graph (Cypher queries)
   - Provider: Neo4j
   - Output: `results` (graph query results)

5. **Hybrid Retrieval** (`hybrid_retrieval`)
   - Combine vector search + knowledge graph results
   - Fusion methods: `reciprocal_rank`, `weighted`, `rrf`
   - Output: `combined_results` (merged and ranked)

6. **Chat** (`chat`)
   - Generate answer using hybrid results
   - Output: `text`

---

### 6. **Content Generation Workflows** ✍️

#### **Simple Content Generation**
```
Text Input → Chat → Output
```

**Nodes Used**:
1. **Text Input** (`text_input`)
   - Prompt or topic
   - Output: `text`

2. **Chat** (`chat`)
   - Generate content
   - Providers: OpenAI, Anthropic, Google Gemini
   - Config: `prompt`, `temperature`, `max_tokens`
   - Output: `text` (generated content)

#### **Enhanced Content Generation (With Memory)**
```
Text Input → Memory → Chat → Output
```

**Additional Nodes**:
3. **Memory Node** (`memory`)
   - Maintain conversation context
   - Store previous interactions
   - Output: `memory` (context)

#### **Multi-Stage Content Generation**
```
Text Input → Chat (Draft) → Chat (Refine) → Output
```

**Nodes Used**:
1. **Text Input** (`text_input`)
2. **Chat** (`chat`) - First stage (draft)
3. **Chat** (`chat`) - Second stage (refinement)
   - Uses output from first Chat node
   - Prompt: `"Refine this content: {{chat.text}}"`

---

## 🎯 Use Cases - Node Mapping
1. **Customer Support Chatbot** 💬

### 
#### **Setup Phase**
```
File Loader → Chunk → Embed → Vector Store
```

**Nodes**:
- **File Loader** - Upload support documents
- **Chunk** - Split documents (chunk_size: 500-1000)
- **Embed** - Create embeddings (OpenAI text-embedding-3-small)
- **Vector Store** - Store in FAISS or Pinecone

#### **Query Phase**
```
Text Input → Embed → Vector Search → Rerank → Chat → Output
```

**Nodes**:
- **Text Input** - Customer question
- **Embed** - Query embedding
- **Vector Search** - Find relevant chunks (top_k: 3-5)
- **Rerank** - Improve relevance (Cohere rerank)
- **Chat** - Generate answer (GPT-4 or Claude)

**Optional Enhancements**:
- **Memory Node** - Remember conversation history
- **Advanced NLP** - Sentiment analysis of customer queries

---

### 2. **Document Q&A System** 📚

#### **Setup Phase**
```
File Loader → OCR (if images) → Chunk → Embed → Vector Store
```

**Nodes**:
- **File Loader** - Upload documents (PDF, DOCX, images)
- **OCR** - Extract text from images (if needed)
- **Chunk** - Split documents
- **Embed** - Create embeddings
- **Vector Store** - Store embeddings

#### **Query Phase**
```
Text Input → Embed → Vector Search → Rerank → Chat → Output
```

**Nodes**:
- **Text Input** - User question
- **Embed** - Query embedding
- **Vector Search** - Retrieve relevant chunks
- **Rerank** - Improve results
- **Chat** - Generate answer with citations

**Optional Enhancements**:
- **Hybrid Retrieval** - Combine with knowledge graph for better results
- **Advanced NLP** - Extract specific information types

---

### 3. **Research Assistant** 🔬

#### **Hybrid RAG Setup**
```
File Loader → Chunk → Embed → Vector Store
Knowledge Graph → Create nodes/relationships
```

**Nodes**:
- **File Loader** - Upload research papers
- **Chunk** - Split papers
- **Embed** - Create embeddings
- **Vector Store** - Store embeddings
- **Knowledge Graph** - Create nodes (Papers, Authors) and relationships (CITES, AUTHORED)

#### **Query Phase**
```
Text Input → Embed → Vector Search ──┐
             ↓                        ├→ Hybrid Retrieval → Chat → Output
         Knowledge Graph ─────────────┘
```

**Nodes**:
- **Text Input** - Research question
- **Embed** - Query embedding
- **Vector Search** - Semantic search
- **Knowledge Graph** - Relationship queries (Cypher)
- **Hybrid Retrieval** - Combine both methods
- **Chat** - Generate comprehensive answer

**Optional Enhancements**:
- **Tool Node** (web_search) - Search external sources
- **CrewAI Agent** - Multi-agent research coordination

---

### 4. **Content Generation Pipeline** ✍️

#### **Multi-Agent Content Generation**
```
Text Input → Tool (Web Search) → CrewAI Agent → Chat → Output
```

**Nodes**:
- **Text Input** - Topic or brief
- **Tool Node** (web_search) - Research information
- **CrewAI Agent** - Coordinate agents:
  - Agent 1: Researcher (gathers info)
  - Agent 2: Writer (creates content)
  - Agent 3: Reviewer (checks quality)
- **Chat** - Final formatting/polish

**Alternative: Simple Generation**
```
Text Input → Chat → Output
```

**Nodes**:
- **Text Input** - Prompt
- **Chat** - Generate content

**Optional Enhancements**:
- **Memory Node** - Maintain style consistency
- **Advanced NLP** - Summarization, translation

---

### 5. **Data Analysis & Reporting** 📊

#### **Data Analysis Workflow**
```
Data Loader → Data to Text → Chat → Output
```

**Nodes**:
- **Data Loader** - Load CSV/Excel/JSON
- **Data to Text** - Convert to natural language
- **Chat** - Analyze and generate insights

**Advanced Analysis**
```
Data Loader → Advanced NLP → Output
```

**Nodes**:
- **Data Loader** - Load data
- **Advanced NLP** - Task: `summarization`, `classification`, `extraction`
  - Summarize large datasets
  - Classify data points
  - Extract specific information

**Optional Enhancements**:
- **Tool Node** (calculator) - Perform calculations
- **Chat** - Generate formatted reports

---

### 6. **Multi-Modal Document Processing** 🖼️

#### **Unified Processing Workflow**
```
File Loader → [OCR | Transcribe | Video Frames] → Chunk → Process → Output
```

**Nodes**:
- **File Loader** - Upload file (PDF, image, audio, video)
- **OCR** - If image, extract text
- **Transcribe** - If audio, convert to text
- **Video Frames** - If video, extract frames → OCR
- **Chunk** - Split content
- **Chat** or **Advanced NLP** - Process and analyze

**Specific Flows**:

**PDF Processing**:
```
File Loader → Chunk → Chat → Output
```

**Image Processing**:
```
File Loader → OCR → Chat → Output
```

**Audio Processing**:
```
File Loader → Transcribe → Chat → Output
```

**Video Processing**:
```
File Loader → Video Frames → OCR → Chat → Output
```

**Vision Analysis**:
```
File Loader → Vision → Output
```

---

## 📦 Node Categories Reference

### **Input Nodes** 📥
- **Text Input** (`text_input`) - Text entry
- **File Loader** (`file_loader`) - File upload (PDF, images, audio, video, etc.)
- **Data Loader** (`data_loader`) - Structured data (CSV, Excel, JSON, Parquet)
- **Webhook Input** (`webhook_input`) - Receive webhook data

### **Processing Nodes** ⚙️
- **Chunk** (`chunk`) - Split text into chunks
- **OCR** (`ocr`) - Extract text from images
- **Transcribe** (`transcribe`) - Convert audio to text
- **Video Frames** (`video_frames`) - Extract frames from video
- **Data to Text** (`data_to_text`) - Convert structured data to text
- **Advanced NLP** (`advanced_nlp`) - Advanced NLP tasks (summarization, NER, classification, etc.)

### **Embedding Nodes** 🔢
- **Embed** (`embed`) - Create vector embeddings (OpenAI, HuggingFace, Cohere, Voyage AI)

### **Storage Nodes** 💾
- **Vector Store** (`vector_store`) - Store embeddings (FAISS, Pinecone, Chroma)
- **Knowledge Graph** (`knowledge_graph`) - Neo4j graph database
- **Database** (`database`) - SQL database operations
- **S3** (`s3`) - AWS S3 storage
- **Azure Blob** (`azure_blob`) - Azure Blob Storage
- **Google Drive** (`google_drive`) - Google Drive integration

### **Retrieval Nodes** 🔍
- **Vector Search** (`vector_search`) - Semantic similarity search
- **Rerank** (`rerank`) - Improve search relevance (Cohere, Cross-Encoder)
- **Hybrid Retrieval** (`hybrid_retrieval`) - Combine vector + graph search

### **LLM Nodes** 🤖
- **Chat** (`chat`) - Text generation (OpenAI, Anthropic, Google Gemini, Groq)
- **Vision** (`vision`) - Image analysis (GPT-4 Vision, Gemini Vision)

### **Agent Nodes** 👥
- **CrewAI Agent** (`crewai_agent`) - Multi-agent coordination
- **LangChain Agent** (`langchain_agent`) - Single agent with tools

### **Tool Nodes** 🛠️
- **Tool** (`tool`) - Define tools for agents:
  - `web_search` - Web search
  - `calculator` - Math calculations
  - `web_scraping` - Scrape web pages
  - `api_call` - Call external APIs
  - `database_query` - Query databases
  - `code_execution` - Execute Python code
  - `email` - Send emails
  - `rss_feed` - Read RSS feeds
  - `s3_storage` - S3 operations
  - `custom` - Custom tools

### **Memory Nodes** 🧠
- **Memory** (`memory`) - Conversation history and context

### **Communication Nodes** 📧
- **Email** (`email`) - Send emails
- **Slack** (`slack`) - Send Slack messages

### **Integration Nodes** 🔌
- **Reddit** (`reddit`) - Reddit integration

### **Training Nodes** 🎓
- **Fine-Tune** (`finetune`) - Fine-tune LLM models

---

## 📋 Complete Node List

### **Core Nodes (Always Available)**
1. Text Input
2. File Loader
3. Chunk
4. Embed
5. Vector Store
6. Vector Search
7. Chat
8. Memory

### **Optional Nodes (Require Dependencies)**
9. Data Loader (requires pandas, openpyxl, pyarrow)
10. OCR (requires pytesseract, Pillow)
11. Transcribe (requires openai-whisper)
12. Video Frames (requires opencv-python)
13. Advanced NLP (requires transformers/OpenAI/Anthropic)
14. Knowledge Graph (requires neo4j)
15. Rerank (requires cohere or sentence-transformers)
16. Hybrid Retrieval
17. Vision (requires OpenAI or Google)
18. CrewAI Agent (requires crewai)
19. LangChain Agent (requires langchain)
20. Tool Node
21. Fine-Tune (requires OpenAI)
22. Email (requires email libraries)
23. Slack (requires slack-sdk)
24. S3 (requires boto3)
25. Azure Blob (requires azure-storage-blob)
26. Database (requires SQLAlchemy)
27. Google Drive (requires google-api-python-client)
28. Reddit (requires praw)
29. Webhook Input

---

## 🎯 Quick Reference: Common Workflow Patterns

### **Simple RAG**
```
File Loader → Chunk → Embed → Vector Store
Text Input → Embed → Vector Search → Chat
```

### **Advanced RAG**
```
File Loader → Chunk → Embed → Vector Store
Text Input → Embed → Vector Search → Rerank → Chat
```

### **Multi-Agent**
```
Text Input → Tool → CrewAI Agent → Chat
```

### **Document Processing**
```
File Loader → [OCR|Transcribe|Video Frames] → Chunk → Chat
```

### **Data Analysis**
```
Data Loader → Data to Text → Chat
```

### **Hybrid RAG**
```
Text Input → Embed → Vector Search ──┐
             ↓                        ├→ Hybrid Retrieval → Chat
         Knowledge Graph ─────────────┘
```

---

**This mapping shows exactly which nodes to use for each workflow type and use case!** 🎯

